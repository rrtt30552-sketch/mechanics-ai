"""
RAG Service - 检索增强生成
使用 Milvus 向量数据库进行语义检索
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pymilvus import (
    connections, Collection, CollectionSchema,
    FieldSchema, DataType, utility
)
import logging

from .embedding import embed_query, embed_texts, cosine_similarity
from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Milvus Collection 名称
COLLECTION_NAME = "doc_embeddings"
VECTOR_DIM = 1536  # DeepSeek embedding 维度


def get_milvus_collection() -> Collection:
    """获取或创建 Milvus Collection"""
    # 连接 Milvus
    if not connections.has_connection("default"):
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
        )

    # 如果 Collection 不存在则创建
    if not utility.has_collection(COLLECTION_NAME):
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
            FieldSchema(name="document_id", dtype=DataType.INT64),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="user_id", dtype=DataType.INT64),
            FieldSchema(name="file_type", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
        ]
        schema = CollectionSchema(fields, description="机械知识库文档向量")
        collection = Collection(COLLECTION_NAME, schema)

        # 创建向量索引
        index_params = {
            "index_type": "IVF_SQ8",
            "metric_type": "COSINE",
            "params": {"nlist": 1024},
        }
        collection.create_index("embedding", index_params)
        logger.info(f"Created Milvus collection: {COLLECTION_NAME}")
    else:
        collection = Collection(COLLECTION_NAME)

    collection.load()
    return collection


class RAGService:
    """RAG 检索服务 — Milvus 版"""

    async def index_document(
        self,
        doc_id: int,
        chunks: List[str],
        user_id: int = 0,
        file_type: str = "",
        category: str = "",
    ):
        """
        将文档切片向量化并存入 Milvus
        """
        if not chunks:
            return

        # 批量向量化
        vectors = await embed_texts(chunks)
        if not vectors:
            return

        collection = get_milvus_collection()

        # 构建插入数据
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        doc_ids = [doc_id] * len(chunks)
        chunk_indices = list(range(len(chunks)))
        contents = chunks
        user_ids = [user_id] * len(chunks)
        file_types = [file_type] * len(chunks)
        categories = [category] * len(chunks)

        # 截断 content 到 8192 字符（Milvus VARCHAR 限制）
        contents = [c[:8192] for c in contents]

        collection.insert([
            ids, doc_ids, chunk_indices, contents,
            user_ids, file_types, categories, vectors
        ])
        collection.flush()
        logger.info(f"Indexed document {doc_id}: {len(chunks)} chunks into Milvus")

    async def remove_document(self, doc_id: int):
        """删除某文档的所有向量"""
        collection = get_milvus_collection()
        collection.delete(f'document_id == {doc_id}')
        collection.flush()
        logger.info(f"Removed document {doc_id} vectors from Milvus")

    async def search(
        self,
        query: str,
        top_k: int = 5,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        score_threshold: float = 0.5,
    ) -> List[dict]:
        """
        语义检索:
        1. 对 query 向量化
        2. Milvus 相似度检索
        3. 过滤低分结果
        """
        query_vector = await embed_query(query)
        if not query_vector:
            return []

        collection = get_milvus_collection()

        # 构建过滤表达式
        filters = []
        if user_id is not None:
            filters.append(f'user_id == {user_id}')
        if category:
            filters.append(f'category == "{category}"')
        filter_expr = " && ".join(filters) if filters else None

        # 向量检索
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 32}}
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k * 2,  # 多检索一些，后续过滤
            expr=filter_expr,
            output_fields=["document_id", "content", "chunk_index", "file_type", "category"],
        )

        # 整理结果，过滤低分
        formatted = []
        for hit in results[0]:
            score = hit.score
            if score >= score_threshold:
                formatted.append({
                    "document_id": hit.entity.get("document_id"),
                    "chunk_index": hit.entity.get("chunk_index"),
                    "content": hit.entity.get("content"),
                    "file_type": hit.entity.get("file_type"),
                    "category": hit.entity.get("category"),
                    "score": round(score, 4),
                })

        return formatted[:top_k]

    async def get_context(self, query: str, top_k: int = 3, user_id: Optional[int] = None) -> Optional[str]:
        """
        检索并拼接上下文字符串，直接注入到 LLM prompt 中
        """
        results = await self.search(query, top_k=top_k, user_id=user_id)
        if not results:
            return None

        context_parts = []
        for i, r in enumerate(results, 1):
            source = f"[来源 {i}: 文档#{r['document_id']}]"
            context_parts.append(f"{source}\n{r['content']}")

        return "\n\n---\n\n".join(context_parts)


# 全局实例
rag_service = RAGService()
