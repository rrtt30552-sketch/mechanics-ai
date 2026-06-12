"""
Embedding Service - 使用 DeepSeek API 生成文本向量
替换原有的 sentence-transformers 本地方案
"""
import httpx
from typing import List
import numpy as np

from .config import get_settings

settings = get_settings()


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    批量文本向量化 — 调用 DeepSeek Embedding API
    
    DeepSeek embedding 模型: deepseek-embedding
    输出维度: 1536
    """
    if not texts:
        return []

    # DeepSeek embedding API 单次最多处理多条，分批处理防限流
    batch_size = 32
    all_embeddings = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = await client.post(
                f"{settings.DEEPSEEK_BASE_URL}/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.EMBEDDING_MODEL,
                    "input": batch,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            # 按 index 排序保证顺序一致
            sorted_embs = sorted(data["data"], key=lambda x: x["index"])
            all_embeddings.extend([item["embedding"] for item in sorted_embs])

    return all_embeddings


async def embed_query(query: str) -> List[float]:
    """单条查询向量化"""
    results = await embed_texts([query])
    return results[0]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算余弦相似度"""
    a_np = np.array(a)
    b_np = np.array(b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np) + 1e-8))
