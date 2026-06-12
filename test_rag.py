#!/usr/bin/env python3
"""
RAG 端到端测试脚本
测试：文本向量化 → 向量存储 → 语义检索
"""
import sys
import os

# Add backend to path but avoid importing shared/__init__.py (which needs DB)
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

# Manually register shared package with empty __init__ to avoid DB import
import types
shared_pkg = types.ModuleType('shared')
shared_pkg.__path__ = [os.path.join(backend_dir, 'shared')]
sys.modules['shared'] = shared_pkg

# Now safe to import
from shared.embedding import embed_texts, embed_query, cosine_similarity
from shared.rag import VectorStore, RAGService


def test_embedding():
    """测试 embedding 功能"""
    print("=" * 50)
    print("1. 测试文本向量化")
    print("=" * 50)

    texts = [
        "45号钢是优质碳素结构钢，含碳量约0.45%，具有较高的强度和良好的切削加工性。",
        "40Cr是合金结构钢，含有铬元素，淬透性好，常用于制造承受重载的零件。",
        "渐开线齿轮的模数是齿轮几何尺寸计算的基本参数，模数越大，齿轮越大。",
        "液压系统压力不足可能是由于液压泵磨损、溢流阀设定不当或系统泄漏引起的。",
        "淬火是将钢加热到临界温度以上，保温后快速冷却的热处理工艺。",
    ]

    vectors = embed_texts(texts)
    print(f"  ✅ 成功生成 {len(vectors)} 个向量")
    print(f"  📐 向量维度: {len(vectors[0])}")

    # Test similarity
    q = "45号钢和40Cr哪个好？"
    q_vec = embed_query(q)
    print(f"\n  查询: {q}")
    for i, (text, vec) in enumerate(zip(texts, vectors)):
        score = cosine_similarity(q_vec, vec)
        print(f"  [{score:.4f}] {text[:50]}...")

    return texts, vectors


def test_vector_store(texts, vectors):
    """测试向量存储与检索"""
    print("\n" + "=" * 50)
    print("2. 测试向量存储与检索")
    print("=" * 50)

    store = VectorStore()
    chunks = [(i, text, vec) for i, (text, vec) in enumerate(zip(texts, vectors))]
    store.add_vectors(doc_id=1, chunks=chunks)
    print(f"  ✅ 存入 {store.count} 条向量")

    # Search
    q = "齿轮模数怎么选？"
    q_vec = embed_query(q)
    results = store.search(q_vec, top_k=3)
    print(f"\n  查询: {q}")
    for r in results:
        print(f"  [{r['score']:.4f}] {r['content'][:60]}...")

    return store


def test_rag_service():
    """测试 RAG 服务（异步）"""
    print("\n" + "=" * 50)
    print("3. 测试 RAG 检索上下文生成")
    print("=" * 50)

    import asyncio

    async def run():
        svc = RAGService()

        docs = [
            "45号钢含碳量约0.45%，抗拉强度≥600MPa，屈服强度≥355MPa。常用于制造轴、齿轮、连杆等零件。",
            "40Cr钢含碳0.37-0.44%，铬0.80-1.10%。经调质处理后具有良好的综合力学性能，常用于制造齿轮轴、连杆螺栓等。",
            "渐开线齿轮标准模数系列：1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10... 模数m = d/z，d为分度圆直径，z为齿数。",
            "液压系统常见故障：压力不足（泵磨损、溢流阀故障）、油温过高（散热不良）、执行机构爬行（空气混入）。",
        ]
        await svc.index_document(doc_id=1, chunks=docs)
        print(f"  ✅ 索引了 {len(docs)} 个文档片段")

        q = "40Cr钢的成分和用途是什么？"
        context = await svc.get_context(q, top_k=2)
        print(f"\n  查询: {q}")
        print(f"  检索到的上下文:")
        for line in context.split('\n')[:6]:
            print(f"    {line}")

        q2 = "液压系统压力不够怎么办？"
        context2 = await svc.get_context(q2, top_k=2)
        print(f"\n  查询: {q2}")
        print(f"  检索到的上下文:")
        for line in context2.split('\n')[:6]:
            print(f"    {line}")

    asyncio.run(run())


if __name__ == "__main__":
    print("🚀 MechAI RAG Pipeline 测试\n")
    texts, vectors = test_embedding()
    test_vector_store(texts, vectors)
    test_rag_service()
    print("\n" + "=" * 50)
    print("✅ RAG 链路全部测试通过！")
    print("=" * 50)
