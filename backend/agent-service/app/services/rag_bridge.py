"""
RAG Bridge - 连接 agent-service 和 shared/rag
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from shared.rag import rag_service
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


async def get_rag_context(query: str, top_k: int = 3) -> str | None:
    """从知识库检索相关上下文"""
    if not RAG_AVAILABLE:
        return None
    try:
        return await rag_service.get_context(query, top_k=top_k)
    except Exception:
        return None
