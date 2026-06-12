from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import json

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.database import get_db
from shared.rag import rag_service

from app.schemas.chat import ChatRequest, ChatResponse, ConversationCreate, ConversationResponse, MessageResponse
from app.services.chat_service import ChatService
from app.services.llm_client import llm_client

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """非流式对话（带 RAG）"""
    svc = ChatService(db)
    result = await svc.chat(user_id=1, message=req.message, conversation_id=req.conversation_id)
    return result


@router.post("/stream")
async def chat_stream(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """SSE 流式对话（带 RAG 检索）"""
    svc = ChatService(db)

    # Get or create conversation
    if req.conversation_id:
        conv = await svc.get_conversation(req.conversation_id)
    else:
        conv = await svc.create_conversation(user_id=1)

    # Save user message
    await svc.save_message(conv.id, "user", req.message)

    # Build history
    history_msgs = await svc.get_history(conv.id, limit=20)
    history = [{"role": m.role, "content": m.content} for m in history_msgs[:-1]]

    # RAG: 检索知识库
    context = None
    sources = []
    try:
        results = await rag_service.search(req.message, top_k=3, user_id=1)
        if results:
            sources = [{"doc_id": r["document_id"], "score": r["score"], "content": r["content"][:200]} for r in results]
            context = "\n\n---\n\n".join([f"[来源 {i+1}: 文档#{r['document_id']}]\n{r['content']}" for i, r in enumerate(results)])
    except Exception as e:
        import logging
        logging.warning(f"RAG retrieval failed: {e}")

    # Build messages with RAG context
    messages = llm_client.build_messages(req.message, history=history, context=context)

    async def generate():
        # 先发送检索到的来源信息
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        # 流式输出 LLM 回答
        full_reply = []
        async for chunk in llm_client.chat_stream(messages):
            full_reply.append(chunk)
            yield f"data: {json.dumps({'type': 'content', 'content': chunk, 'conversation_id': conv.id})}\n\n"

        # Save complete reply
        await svc.save_message(conv.id, "assistant", "".join(full_reply))
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    svc = ChatService(db)
    return await svc.list_conversations(user_id=1, skip=skip, limit=limit)


@router.get("/conversations/{conv_id}", response_model=ConversationResponse)
async def get_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    svc = ChatService(db)
    conv = await svc.get_conversation(conv_id)
    messages = await svc.get_history(conv_id, limit=100)
    return ConversationResponse(
        id=conv.id, title=conv.title, user_id=conv.user_id,
        created_at=conv.created_at, messages=messages
    )


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    # TODO: implement delete
    return {"message": "Conversation deleted"}
