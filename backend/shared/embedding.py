"""
Embedding Service
优先使用 sentence-transformers，回退到 scikit-learn TF-IDF（轻量模式）
"""
import os
import logging
import hashlib
import json
from typing import List

import numpy as np

logger = logging.getLogger(__name__)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ========== 尝试加载 sentence-transformers ==========
_MODEL = None
# 优先用中文模型，回退到多语言模型
_MODEL_CANDIDATES = [
    os.getenv("EMBEDDING_MODEL", ""),  # 用户自定义
    "BAAI/bge-base-zh-v1.5",           # 中文专用，768维
    "moka-ai/m3e-base",                # 中文专用，768维
    "all-MiniLM-L6-v2",                # 多语言回退，384维
]
_MODEL_NAME = ""
_USE_ST = False
EMBEDDING_DIM = 384  # 默认维度，加载模型后更新

def _try_load_st():
    global _MODEL, _MODEL_NAME, _USE_ST, EMBEDDING_DIM
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.info("sentence-transformers not installed, using TF-IDF fallback")
        return False
    for model_name in _MODEL_CANDIDATES:
        if not model_name:
            continue
        try:
            _MODEL = SentenceTransformer(model_name)
            _MODEL_NAME = model_name
            _USE_ST = True
            # 获取实际维度
            test_vec = _MODEL.encode(["test"], show_progress_bar=False)
            EMBEDDING_DIM = len(test_vec[0])
            logger.info(f"Loaded embedding model: {model_name} (dim={EMBEDDING_DIM})")
            return True
        except Exception as e:
            logger.info(f"Failed to load {model_name}: {e}")
            continue
    logger.info("No sentence-transformers model available, using TF-IDF fallback")
    return False

# ========== TF-IDF 回退方案 ==========
_TFIDF_VECTORIZER = None
_SVD = None
_VOCAB_SIZE = 384  # 匹配 pgvector 维度

def _get_tfidf_model():
    global _TFIDF_VECTORIZER, _SVD
    if _TFIDF_VECTORIZER is None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        _TFIDF_VECTORIZER = TfidfVectorizer(
            max_features=10000,
            analyzer='char_wb',
            ngram_range=(2, 4),
            sublinear_tf=True,
        )
        _SVD = TruncatedSVD(n_components=_VOCAB_SIZE, random_state=42)
        # 预训练一些中文机械工程语料
        _pretrain_tfidf()
    return _TFIDF_VECTORIZER, _SVD

def _pretrain_tfidf():
    """用一些机械工程常见文本预训练 TF-IDF"""
    corpus = [
        "渐开线齿轮模数压力角齿数分度圆直径",
        "轴承选型径向载荷轴向载荷额定动载荷",
        "材料力学弯曲应力剪应力弹性模量泊松比",
        "液压系统压力流量泵阀缸马达",
        "机械设计公差配合表面粗糙度形位公差",
        "淬火回火正火退火表面处理热处理工艺",
        "铸造锻造焊接切削加工数控机床",
        "减速器齿轮传动蜗轮蜗杆传动比",
        "联轴器离合器制动器传动装置",
        "密封件O型圈油封机械密封",
        "疲劳强度寿命安全系数可靠性",
        "振动分析频谱故障诊断轴承齿轮",
        "有限元分析应力应变变形刚度",
        "机械原理自由度机构运动学动力学",
        "工程材料钢铁铝合金铜合金塑料",
        "CAD CAM CAE SolidWorks AutoCAD",
        "45号钢 40Cr 20CrMnTi Q235 不锈钢",
        "键连接螺栓连接焊接连接过盈配合",
        "滑动轴承滚动轴承润滑摩擦磨损",
        "带传动链传动齿轮传动螺旋传动",
    ]
    try:
        vec, svd = _get_tfidf_model()
        vec.fit(corpus)
        svd.fit(vec.transform(corpus))
        logger.info("TF-IDF model pretrained with mechanical engineering corpus")
    except Exception as e:
        logger.warning(f"TF-IDF pretraining failed: {e}")


def embed_texts_tfidf(texts: List[str]) -> List[List[float]]:
    """使用 TF-IDF + SVD 生成文本向量"""
    vec, svd = _get_tfidf_model()
    # 如果还没 fit，先 fit
    if not hasattr(vec, 'vocabulary_') or vec.vocabulary_ is None:
        _pretrain_tfidf()
    try:
        tfidf_matrix = vec.transform(texts)
        embeddings = svd.transform(tfidf_matrix)
        # 归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-8)
        embeddings = embeddings / norms
        return embeddings.tolist()
    except Exception as e:
        logger.warning(f"TF-IDF embedding failed: {e}, using hash fallback")
        return [embed_text_hash(t) for t in texts]


def embed_text_hash(text: str, dim: int = 384) -> List[float]:
    """哈希嵌入 — 最终回退方案，基于字符哈希生成确定性向量"""
    vec = [0.0] * dim
    # 字符级哈希
    for i, char in enumerate(text):
        h = hashlib.md5(f"{char}_{i}".encode()).hexdigest()
        idx = int(h[:8], 16) % dim
        sign = 1 if int(h[8:9], 16) % 2 == 0 else -1
        vec[idx] += sign * (1.0 / (1 + i * 0.1))
    # N-gram 哈希
    for n in [2, 3, 4]:
        for i in range(len(text) - n + 1):
            gram = text[i:i+n]
            h = hashlib.md5(gram.encode()).hexdigest()
            idx = int(h[:8], 16) % dim
            sign = 1 if int(h[8:9], 16) % 2 == 0 else -1
            vec[idx] += sign * (0.5 / (1 + i * 0.05))
    # 归一化
    norm = sum(x*x for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


# ========== 统一接口 ==========

def embed_texts(texts: List[str]) -> List[List[float]]:
    """批量生成文本向量"""
    global _USE_ST
    if _USE_ST and _MODEL is not None:
        try:
            embeddings = _MODEL.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return embeddings.tolist()
        except Exception:
            pass

    # 尝试加载 sentence-transformers（首次）
    if not _USE_ST:
        if _try_load_st() and _MODEL is not None:
            embeddings = _MODEL.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return embeddings.tolist()

    # 回退到 TF-IDF
    return embed_texts_tfidf(texts)


def embed_query(query: str) -> List[float]:
    """生成查询向量"""
    return embed_texts([query])[0]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算余弦相似度"""
    a_np = np.array(a)
    b_np = np.array(b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np) + 1e-8))
