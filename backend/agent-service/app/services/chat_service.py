from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.exceptions import NotFoundException

from app.models.chat import Conversation, Message
from app.schemas.chat import ConversationCreate
from app.services.llm_client import llm_client

# RAG 服务
from shared.rag import rag_service


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(self, user_id: int, data: ConversationCreate = None) -> Conversation:
        conv = Conversation(
            user_id=user_id,
            title=data.title if data and data.title else "New Chat",
        )
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def get_conversation(self, conv_id: int) -> Conversation:
        result = await self.db.execute(select(Conversation).where(Conversation.id == conv_id))
        conv = result.scalar_one_or_none()
        if not conv:
            raise NotFoundException("Conversation not found")
        return conv

    async def list_conversations(self, user_id: int, skip: int = 0, limit: int = 50) -> List[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_history(self, conv_id: int, limit: int = 20) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def save_message(self, conv_id: int, role: str, content: str) -> Message:
        msg = Message(conversation_id=conv_id, role=role, content=content)
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def chat(self, user_id: int, message: str, conversation_id: Optional[int] = None) -> dict:
        """非流式对话（带 RAG 检索）"""
        # Get or create conversation
        if conversation_id:
            conv = await self.get_conversation(conversation_id)
        else:
            conv = await self.create_conversation(user_id)

        # Save user message
        await self.save_message(conv.id, "user", message)

        # Build history
        history_msgs = await self.get_history(conv.id, limit=20)
        history = [{"role": m.role, "content": m.content} for m in history_msgs[:-1]]

        # RAG: 从知识库检索相关上下文
        context = None
        try:
            context = await rag_service.get_context(message, top_k=3, user_id=user_id)
        except Exception as e:
            import logging
            logging.warning(f"RAG retrieval failed (non-fatal): {e}")

        # Call LLM with context
        messages = llm_client.build_messages(message, history=history, context=context)
        reply = await llm_client.chat(messages)

        # Save assistant message
        assistant_msg = await self.save_message(conv.id, "assistant", reply)

        return {
            "reply": reply,
            "conversation_id": conv.id,
            "message_id": assistant_msg.id,
            "has_context": context is not None,
        }
