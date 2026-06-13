"""
RAG Service - 检索增强生成
使用 PostgreSQL + pgvector 进行持久化向量存储与检索
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, delete

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.embedding import embed_query, embed_texts
from shared.config import get_settings

settings = get_settings()

# Embedding 维度 (all-MiniLM-L6-v2 = 384)
EMBEDDING_DIM = 384


async def init_vector_extension(engine):
    """启用 pgvector 扩展并创建向量表"""
    async with engine.begin() as conn:
        # 启用 pgvector 扩展
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # 创建文档向量表（如果不存在）
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

        # 创建 HNSW 索引加速检索（如果不存在）
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
            ON document_embeddings
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """))

        # 创建 document_id 索引
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_doc_id
            ON document_embeddings (document_id)
        """))


class VectorStore:
    """
    PostgreSQL + pgvector 向量存储
    数据持久化，支持高效的余弦相似度检索
    """

    async def add_vectors(self, doc_id: int, chunks: List[tuple]):
        """
        添加向量到数据库
        chunks: [(chunk_index, content, embedding_vector), ...]
        """
        from shared.database import async_session
        async with async_session() as session:
            for chunk_index, content, vector in chunks:
                # 将 list 转为 pgvector 格式字符串
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
        """向量检索，使用 pgvector 的余弦距离运算符 <=>"""
        from shared.database import async_session
        vec_str = "[" + ",".join(str(v) for v in query_vector) + "]"

        async with async_session() as session:
            if doc_ids:
                # 指定文档范围内检索
                placeholders = ",".join(str(i) for i in doc_ids)
                sql = text(f"""
                    SELECT document_id, chunk_index, content,
                           1 - (embedding <=> :query::vector) AS score
                    FROM document_embeddings
                    WHERE document_id IN ({placeholders})
                    ORDER BY embedding <=> :query::vector
                    LIMIT :top_k
                """)
            else:
                sql = text("""
                    SELECT document_id, chunk_index, content,
                           1 - (embedding <=> :query::vector) AS score
                    FROM document_embeddings
                    ORDER BY embedding <=> :query::vector
                    LIMIT :top_k
                """)

            result = await session.execute(sql, {"query": vec_str, "top_k": top_k})
            rows = result.fetchall()

            return [
                {
                    "doc_id": row[0],
                    "chunk_id": row[1],
                    "content": row[2],
                    "score": float(row[3]),
                }
                for row in rows
            ]

    async def remove_doc(self, doc_id: int):
        """删除某文档的所有向量"""
        from shared.database import async_session
        async with async_session() as session:
            await session.execute(
                text("DELETE FROM document_embeddings WHERE document_id = :doc_id"),
                {"doc_id": doc_id}
            )
            await session.commit()

    async def count(self) -> int:
        """获取向量总数"""
        from shared.database import async_session
        async with async_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM document_embeddings"))
            return result.scalar() or 0


# 全局向量存储实例
vector_store = VectorStore()


class RAGService:
    """RAG 检索服务"""

    async def index_document(self, doc_id: int, chunks: List[str]):
        """将文档切片向量化并存入向量库"""
        if not chunks:
            return

        vectors = embed_texts(chunks)
        chunk_data = list(enumerate(zip(chunks, vectors)))
        # [(chunk_index, content, vector), ...]
        data = [(i, content, vec) for i, (content, vec) in chunk_data]
        await vector_store.add_vectors(doc_id, data)

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
