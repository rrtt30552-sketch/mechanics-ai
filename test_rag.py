#!/usr/bin/env python3
"""
RAG 端到端测试脚本
测试：DeepSeek Embedding → Milvus 存储 → 语义检索
"""
import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

# Register shared package
import types
shared_pkg = types.ModuleType('shared')
shared_pkg.__path__ = [os.path.join(backend_dir, 'shared')]
sys.modules['shared'] = shared_pkg

from shared.embedding import embed_texts, embed_query, cosine_similarity
from shared.rag import RAGService


async def test_embedding():
    """测试 DeepSeek Embedding API"""
    print("=" * 50)
    print("1. 测试 DeepSeek 文本向量化")
    print("=" * 50)

    texts = [
        "45号钢是优质碳素结构钢，含碳量约0.45%，具有较高的强度和良好的切削加工性。",
        "40Cr是合金结构钢，含有铬元素，淬透性好，常用于制造承受重载的零件。",
        "渐开线齿轮的模数是齿轮几何尺寸计算的基本参数，模数越大，齿轮越大。",
        "液压系统压力不足可能是由于液压泵磨损、溢流阀设定不当或系统泄漏引起的。",
        "淬火是将钢加热到临界温度以上，保温后快速冷却的热处理工艺。",
    ]

    vectors = await embed_texts(texts)
    print(f"  ✅ 成功生成 {len(vectors)} 个向量")
    print(f"  📐 向量维度: {len(vectors[0])}")

    # Test similarity
    q = "45号钢和40Cr哪个好？"
    q_vec = await embed_query(q)
    print(f"\n  查询: {q}")
    for i, (text, vec) in enumerate(zip(texts, vectors)):
        score = cosine_similarity(q_vec, vec)
        print(f"  [{score:.4f}] {text[:50]}...")

    return texts, vectors


async def test_rag_search():
    """测试 RAG 检索（需要 Milvus 运行）"""
    print("\n" + "=" * 50)
    print("2. 测试 RAG 检索")
    print("=" * 50)

    rag = RAGService()

    # 先索引一些测试文档
    test_chunks = [
        "45号钢是优质碳素结构钢，含碳量约0.45%，具有较高的强度和良好的切削加工性。",
        "40Cr是合金结构钢，含有铬元素，淬透性好，常用于制造承受重载的零件。",
        "渐开线齿轮的模数是齿轮几何尺寸计算的基本参数，模数越大，齿轮越大。",
        "液压系统压力不足可能是由于液压泵磨损、溢流阀设定不当或系统泄漏引起的。",
        "淬火是将钢加热到临界温度以上，保温后快速冷却的热处理工艺。",
    ]

    try:
        await rag.index_document(doc_id=999, chunks=test_chunks, user_id=0, file_type="txt", category="测试")
        print(f"  ✅ 索引 {len(test_chunks)} 条测试文档")
    except Exception as e:
        print(f"  ❌ 索引失败: {e}")
        print("  (请确保 Milvus 已启动)")
        return

    # 搜索测试
    queries = [
        "齿轮模数怎么选？",
        "钢材的热处理方法",
        "液压系统故障",
    ]

    for q in queries:
        print(f"\n  查询: {q}")
        results = await rag.search(q, top_k=3)
        if results:
            for r in results:
                print(f"  [{r['score']:.4f}] {r['content'][:60]}...")
        else:
            print("  (无结果)")

    # 清理测试数据
    try:
        await rag.remove_document(999)
        print("\n  ✅ 测试数据已清理")
    except Exception:
        pass


async def main():
    print("🔧 MechAI RAG 测试 (DeepSeek Embedding + Milvus)\n")

    try:
        await test_embedding()
    except Exception as e:
        print(f"  ❌ Embedding 测试失败: {e}")
        print("  (请检查 DEEPSEEK_API_KEY 和 DEEPSEEK_BASE_URL)")

    try:
        await test_rag_search()
    except Exception as e:
        print(f"  ❌ RAG 测试失败: {e}")
        print("  (请检查 Milvus 是否已启动)")


if __name__ == "__main__":
    asyncio.run(main())
