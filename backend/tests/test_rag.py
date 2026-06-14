"""
Tests for shared/rag.py — FileVectorStore
"""
import os
import sys
import asyncio
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Force file mode (no postgres)
os.environ.pop("DATABASE_URL", None)

from shared.embedding import embed_texts, embed_query
from shared.rag import FileVectorStore


def test_file_vector_store():
    """FileVectorStore 基本功能"""
    import json

    async def run():
        # 使用临时文件避免污染项目目录
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name
            json.dump([], f)

        # Monkey-patch VECTORS_FILE
        import shared.rag as rag_module
        original = rag_module.VECTORS_FILE
        rag_module.VECTORS_FILE = tmp_path

        try:
            store = FileVectorStore()

            # 测试数据
            texts = [
                "45号钢含碳量约0.45%",
                "渐开线齿轮模数计算",
                "液压系统常见故障",
            ]
            vectors = embed_texts(texts)
            chunks = [(i, text, vec) for i, (text, vec) in enumerate(zip(texts, vectors))]

            # 添加向量
            await store.add_vectors(doc_id=1, chunks=chunks)
            count = await store.count()
            assert count == 3, f"Expected 3, got {count}"

            # 搜索
            q_vec = embed_query("齿轮模数怎么选")
            results = await store.search(q_vec, top_k=2)
            assert len(results) == 2
            assert results[0]["score"] >= results[1]["score"]

            # 删除文档
            await store.remove_doc(1)
            count = await store.count()
            assert count == 0

        finally:
            rag_module.VECTORS_FILE = original
            os.unlink(tmp_path)

    asyncio.run(run())


if __name__ == "__main__":
    test_file_vector_store()
    print("✅ All RAG tests passed!")
