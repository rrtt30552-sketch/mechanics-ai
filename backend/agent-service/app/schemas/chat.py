from pydantic import BaseModel
from typing import Optional


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class MessageCreate(BaseModel):
    role: str
    content: str
