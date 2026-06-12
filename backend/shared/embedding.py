"""
Embedding Service - 使用 sentence-transformers 生成文本向量
"""
import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

# 全局模型实例（懒加载）
_model = None
_model_name = "all-MiniLM-L6-v2"


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_model_name)
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """批量生成文本向量"""
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """生成查询向量"""
    model = get_model()
    embedding = model.encode([query], normalize_embeddings=True)
    return embedding[0].tolist()


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算余弦相似度"""
    a_np = np.array(a)
    b_np = np.array(b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np) + 1e-8))
