"""
RAG Service - 检索增强生成
从知识库中检索相关文档片段，注入到 LLM 上下文中
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.embedding import embed_query, cosine_similarity
from shared.config import get_settings

settings = get_settings()


class VectorStore:
    """
    简易向量存储（开发阶段用内存 + PostgreSQL，生产换 Milvus）
    """

    def __init__(self):
        self._vectors: List[Tuple[int, int, str, List[float]]] = []  # (doc_id, chunk_id, content, vector)

    def add_vectors(self, doc_id: int, chunks: List[Tuple[int, str, List[float]]]):
        """添加向量: chunks = [(chunk_id, content, vector), ...]"""
        for chunk_id, content, vector in chunks:
            self._vectors.append((doc_id, chunk_id, content, vector))

    def search(self, query_vector: List[float], top_k: int = 5,
               doc_ids: Optional[List[int]] = None) -> List[dict]:
        """向量检索，返回 top_k 最相关片段"""
        results = []
        for doc_id, chunk_id, content, vec in self._vectors:
            if doc_ids and doc_id not in doc_ids:
                continue
            score = cosine_similarity(query_vector, vec)
            results.append({
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "content": content,
                "score": score,
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def remove_doc(self, doc_id: int):
        """删除某文档的所有向量"""
        self._vectors = [(d, c, t, v) for d, c, t, v in self._vectors if d != doc_id]

    @property
    def count(self) -> int:
        return len(self._vectors)


# 全局向量存储实例
vector_store = VectorStore()


class RAGService:
    """RAG 检索服务"""

    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def index_document(self, doc_id: int, chunks: List[str]):
        """将文档切片向量化并存入向量库"""
        if not chunks:
            return

        from shared.embedding import embed_texts
        vectors = embed_texts(chunks)

        chunk_data = [(i, content, vec) for i, (content, vec) in enumerate(zip(chunks, vectors))]
        vector_store.add_vectors(doc_id, chunk_data)

    async def search(self, query: str, top_k: int = 5,
                     doc_ids: Optional[List[int]] = None) -> List[dict]:
        """语义检索"""
        query_vector = embed_query(query)
        return vector_store.search(query_vector, top_k, doc_ids)

    async def get_context(self, query: str, top_k: int = 3,
                          doc_ids: Optional[List[int]] = None) -> str:
        """检索并拼接上下文，用于注入 LLM prompt"""
        results = await self.search(query, top_k, doc_ids)
        if not results:
            return ""

        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(f"[参考片段 {i}] (相关度: {r['score']:.2f})\n{r['content']}")

        return "\n\n".join(context_parts)


# 全局实例
rag_service = RAGService()
