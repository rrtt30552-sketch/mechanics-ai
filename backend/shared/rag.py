"""
RAG Service - 检索增强生成
支持两种后端：
  - PostgreSQL + pgvector（生产环境）
  - JSON 文件存储（本地开发/测试）
"""
from typing import List, Optional
import os
import json
import logging

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.embedding import embed_query, embed_texts, EMBEDDING_DIM

logger = logging.getLogger(__name__)

# 向量存储文件路径（本地模式）
VECTORS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'vectors.json')


async def init_vector_extension(engine):
    """启用 pgvector 扩展并创建向量表（仅 PostgreSQL）"""
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector({EMBEDDING_DIM}),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
            ON document_embeddings
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_doc_id
            ON document_embeddings (document_id)
        """))


class FileVectorStore:
    """
    JSON 文件向量存储 — 本地开发用
    数据保存在 vectors.json，重启不丢失
    """

    def __init__(self):
        self._vectors: List[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(VECTORS_FILE):
            try:
                with open(VECTORS_FILE, 'r', encoding='utf-8') as f:
                    self._vectors = json.load(f)
                logger.info(f"Loaded {len(self._vectors)} vectors from {VECTORS_FILE}")
            except Exception as e:
                logger.warning(f"Failed to load vectors file: {e}")
                self._vectors = []
        else:
            self._vectors = []

    def _save(self):
        try:
            with open(VECTORS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._vectors, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save vectors file: {e}")

    async def add_vectors(self, doc_id: int, chunks: List[tuple]):
        """chunks: [(chunk_index, content, vector), ...]"""
        import numpy as np
        for chunk_index, content, vector in chunks:
            self._vectors.append({
                "doc_id": doc_id,
                "chunk_id": chunk_index,
                "content": content,
                "vector": vector if isinstance(vector, list) else vector.tolist(),
            })
        self._save()
        logger.info(f"Added {len(chunks)} vectors for doc {doc_id}, total: {len(self._vectors)}")

    async def search(self, query_vector: List[float], top_k: int = 5,
                     doc_ids: Optional[List[int]] = None) -> List[dict]:
        import numpy as np
        q = np.array(query_vector)
        results = []
        for v in self._vectors:
            if doc_ids and v["doc_id"] not in doc_ids:
                continue
            vec = np.array(v["vector"])
            score = float(np.dot(q, vec) / (np.linalg.norm(q) * np.linalg.norm(vec) + 1e-8))
            results.append({
                "doc_id": v["doc_id"],
                "chunk_id": v["chunk_id"],
                "content": v["content"],
                "score": score,
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def remove_doc(self, doc_id: int):
        self._vectors = [v for v in self._vectors if v["doc_id"] != doc_id]
        self._save()

    async def count(self) -> int:
        return len(self._vectors)


class PgVectorStore:
    """
    PostgreSQL + pgvector 向量存储（生产环境）
    """

    async def add_vectors(self, doc_id: int, chunks: List[tuple]):
        from shared.database import async_session
        from sqlalchemy import text
        async with async_session() as session:
            for chunk_index, content, vector in chunks:
                vec_str = "[" + ",".join(str(v) for v in vector) + "]"
                await session.execute(
                    text("""
                        INSERT INTO document_embeddings (document_id, chunk_index, content, embedding)
                        VALUES (:doc_id, :idx, :content, :embedding::vector)
                    """),
                    {"doc_id": doc_id, "idx": chunk_index, "content": content, "embedding": vec_str}
                )
            await session.commit()

    async def search(self, query_vector: List[float], top_k: int = 5,
                     doc_ids: Optional[List[int]] = None) -> List[dict]:
        from shared.database import async_session
        from sqlalchemy import text
        vec_str = "[" + ",".join(str(v) for v in query_vector) + "]"

        async with async_session() as session:
            if doc_ids:
                # 使用参数化查询防止 SQL 注入
                id_params = {f"doc_id_{i}": v for i, v in enumerate(doc_ids)}
                placeholders = ", ".join(f":doc_id_{i}" for i in range(len(doc_ids)))
                sql = text(f"""
                    SELECT document_id, chunk_index, content,
                           1 - (embedding <=> :query::vector) AS score
                    FROM document_embeddings
                    WHERE document_id IN ({placeholders})
                    ORDER BY embedding <=> :query::vector
                    LIMIT :top_k
                """)
                params = {"query": vec_str, "top_k": top_k, **id_params}
            else:
                sql = text("""
                    SELECT document_id, chunk_index, content,
                           1 - (embedding <=> :query::vector) AS score
                    FROM document_embeddings
                    ORDER BY embedding <=> :query::vector
                    LIMIT :top_k
                """)
                params = {"query": vec_str, "top_k": top_k}
            result = await session.execute(sql, params)
            rows = result.fetchall()
            return [
                {"doc_id": r[0], "chunk_id": r[1], "content": r[2], "score": float(r[3])}
                for r in rows
            ]

    async def remove_doc(self, doc_id: int):
        from shared.database import async_session
        from sqlalchemy import text
        async with async_session() as session:
            await session.execute(
                text("DELETE FROM document_embeddings WHERE document_id = :doc_id"),
                {"doc_id": doc_id}
            )
            await session.commit()

    async def count(self) -> int:
        from shared.database import async_session
        from sqlalchemy import text
        async with async_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM document_embeddings"))
            return result.scalar() or 0


# 根据环境选择存储后端
def _is_postgres() -> bool:
    db_url = os.getenv("DATABASE_URL", "")
    return bool(db_url) and "postgresql" in db_url

if _is_postgres():
    vector_store = PgVectorStore()
    logger.info("Using PostgreSQL + pgvector for vector storage")
else:
    vector_store = FileVectorStore()
    logger.info("Using JSON file for vector storage (local dev mode)")


class RAGService:
    """RAG 检索服务"""

    async def index_document(self, doc_id: int, chunks: List[str]):
        """将文档切片向量化并存入向量库"""
        if not chunks:
            return
        vectors = embed_texts(chunks)
        data = list(enumerate(zip(chunks, vectors)))
        chunk_data = [(i, content, vec) for i, (content, vec) in data]
        await vector_store.add_vectors(doc_id, chunk_data)

    async def search(self, query: str, top_k: int = 5,
                     doc_ids: Optional[List[int]] = None) -> List[dict]:
        """语义检索"""
        query_vector = embed_query(query)
        return await vector_store.search(query_vector, top_k, doc_ids)

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

    async def remove_document(self, doc_id: int):
        """删除文档的所有向量索引"""
        await vector_store.remove_doc(doc_id)


# 全局实例
rag_service = RAGService()
