from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentCreate(BaseModel):
    title: str = Field(..., max_length=300)
    category: Optional[str] = None
    tags: List[str] = []
    description: Optional[str] = None
    is_public: bool = False


class DocumentResponse(BaseModel):
    id: int
    title: str
    file_type: str
    file_size: int
    category: Optional[str]
    tags: List[str]
    description: Optional[str]
    user_id: int
    is_public: bool
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)
    category: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[dict]
    query: str
    total: int
