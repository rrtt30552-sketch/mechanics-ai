from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
import json

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.database import get_db
from shared.security import get_current_user
from app.services.chat_service import ChatService
from app.services.llm_client import llm_client

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


@router.post("/")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """普通对话（非流式）"""
    service = ChatService(db)
    result = await service.chat(user.id, req.message, req.conversation_id)
    return result


@router.post("/stream")
async def chat_stream(req: ChatRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """流式对话（SSE）"""
    service = ChatService(db)

    # Get or create conversation, save user message
    conv = await service.get_or_create_conversation(req.conversation_id, user.id)
    await service.save_message(conv.id, "user", req.message)

    # Build history
    history_msgs = await service.get_history(conv.id, limit=20)
    history = [{"role": m.role, "content": m.content} for m in history_msgs[:-1]]

    # RAG context
    context = None
    try:
        from app.services.rag_bridge import get_rag_context
        context = await get_rag_context(req.message)
    except Exception:
        pass

    # Build messages for LLM
    messages = llm_client.build_messages(req.message, history=history, context=context)

    async def event_generator():
        full_reply = []
        async for chunk in llm_client.chat_stream(messages):
            full_reply.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk, 'conversation_id': conv.id}, ensure_ascii=False)}\n\n"

        # Save complete reply
        complete_text = "".join(full_reply)
        msg = await service.save_message(conv.id, "assistant", complete_text)
        yield f"data: {json.dumps({'done': True, 'message_id': msg.id, 'conversation_id': conv.id}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/conversations")
async def list_conversations(
    skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    """获取用户的对话列表"""
    service = ChatService(db)
    convs = await service.list_conversations(user.id, skip=skip, limit=limit)
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": str(c.created_at),
            "updated_at": str(c.updated_at),
        }
        for c in convs
    ]


@router.get("/conversations/{conv_id}/messages")
async def get_messages(
    conv_id: int, limit: int = 100,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    """获取某次对话的全部消息"""
    service = ChatService(db)
    conv = await service.get_conversation(conv_id)
    if conv.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    messages = await service.get_history(conv_id, limit=limit)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": str(m.created_at),
        }
        for m in messages
    ]


@router.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: int,
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    """删除对话"""
    service = ChatService(db)
    await service.delete_conversation(conv_id, user.id)
    return {"ok": True}
