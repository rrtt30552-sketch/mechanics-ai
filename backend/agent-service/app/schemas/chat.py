from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[int] = None
    stream: bool = False


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    message_id: int


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Chat"


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    title: str
    user_id: int
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True
