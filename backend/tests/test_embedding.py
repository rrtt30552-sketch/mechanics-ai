"""
Tests for shared/embedding.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.embedding import embed_texts, embed_query, cosine_similarity


def test_embed_texts():
    """文本向量化"""
    texts = [
        "45号钢含碳量约0.45%",
        "渐开线齿轮模数计算",
    ]
    vectors = embed_texts(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) > 0
    # 两个向量维度应该相同
    assert len(vectors[0]) == len(vectors[1])


def test_embed_query():
    """查询向量化"""
    vec = embed_query("液压系统压力不足")
    assert len(vec) > 0
    assert all(isinstance(v, float) for v in vec)


def test_cosine_similarity():
    """余弦相似度"""
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    c = [0.0, 1.0, 0.0]

    # 相同向量相似度为 1
    assert abs(cosine_similarity(a, b) - 1.0) < 1e-6
    # 正交向量相似度为 0
    assert abs(cosine_similarity(a, c)) < 1e-6


def test_semantic_similarity():
    """语义相似性 — 相关文本应该比不相关文本相似度更高"""
    texts = [
        "45号钢是优质碳素结构钢",
        "45号钢含碳量约0.45%",
        "液压系统压力不足",
    ]
    query = "45号钢的化学成分"
    q_vec = embed_query(query)

    scores = [cosine_similarity(q_vec, embed_query(t)) for t in texts]

    # 前两个关于45号钢的应该比液压系统的分数高
    assert scores[0] > scores[2] or scores[1] > scores[2]


if __name__ == "__main__":
    test_embed_texts()
    test_embed_query()
    test_cosine_similarity()
    test_semantic_similarity()
    print("✅ All embedding tests passed!")
