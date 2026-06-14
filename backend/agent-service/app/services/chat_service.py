from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.exceptions import NotFoundException

from app.models.chat import Conversation, Message
from app.schemas.chat import ConversationCreate
from app.services.llm_client import llm_client

# Import RAG service
try:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    from shared.rag import rag_service
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(self, user_id: int, title: str = None) -> Conversation:
        conv = Conversation(
            user_id=user_id,
            title=title or "新对话",
        )
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def get_or_create_conversation(self, conversation_id: Optional[int], user_id: int) -> Conversation:
        """获取已有对话或创建新对话"""
        if conversation_id:
            conv = await self.get_conversation(conversation_id)
            if conv.user_id != user_id:
                raise NotFoundException("Conversation not found")
            return conv
        return await self.create_conversation(user_id)

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
        # Update conversation timestamp
        conv = await self.get_conversation(conv_id)
        # Auto-generate title from first user message
        if role == "user" and conv.title == "新对话":
            conv.title = content[:30] + ("..." if len(content) > 30 else "")
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def delete_conversation(self, conv_id: int, user_id: int):
        """删除对话及其所有消息"""
        conv = await self.get_conversation(conv_id)
        if conv.user_id != user_id:
            raise NotFoundException("Conversation not found")
        # 批量删除消息
        from sqlalchemy import delete as sql_delete
        await self.db.execute(sql_delete(Message).where(Message.conversation_id == conv_id))
        await self.db.delete(conv)
        await self.db.commit()

    async def chat(self, user_id: int, message: str, conversation_id: Optional[int] = None,
                   model_key: str = "deepseek") -> dict:
        """非流式对话"""
        conv = await self.get_or_create_conversation(conversation_id, user_id)
        await self.save_message(conv.id, "user", message)

        # Build history
        history_msgs = await self.get_history(conv.id, limit=20)
        history = [{"role": m.role, "content": m.content} for m in history_msgs[:-1]]

        # RAG context
        context = None
        if RAG_AVAILABLE:
            try:
                context = await rag_service.get_context(message, top_k=3)
            except Exception:
                pass

        messages = llm_client.build_messages(message, history=history, context=context)
        reply = await llm_client.chat(messages, model_key=model_key)

        assistant_msg = await self.save_message(conv.id, "assistant", reply)

        return {
            "reply": reply,
            "conversation_id": conv.id,
            "message_id": assistant_msg.id,
        }
