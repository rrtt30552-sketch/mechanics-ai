from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.exceptions import NotFoundException, BadRequestException

from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentCreate


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(self, data: DocumentCreate, user_id: int, file_path: str,
                               file_type: str, file_size: int, chunk_count: int = 0) -> Document:
        doc = Document(
            title=data.title,
            file_type=file_type,
            file_path=file_path,
            file_size=file_size,
            category=data.category,
            tags=data.tags,
            description=data.description,
            user_id=user_id,
            is_public=data.is_public,
            chunk_count=chunk_count,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def get_document(self, doc_id: int) -> Document:
        result = await self.db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise NotFoundException("Document not found")
        return doc

    async def list_documents(self, user_id: Optional[int] = None, category: Optional[str] = None,
                              skip: int = 0, limit: int = 20) -> List[Document]:
        query = select(Document)
        if user_id:
            query = query.where(Document.user_id == user_id)
        if category:
            query = query.where(Document.category == category)
        query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_document(self, doc_id: int) -> None:
        doc = await self.get_document(doc_id)
        # Delete chunks
        chunks = await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == doc_id)
        )
        for chunk in chunks.scalars().all():
            await self.db.delete(chunk)
        await self.db.delete(doc)
        await self.db.commit()

    async def save_chunks(self, document_id: int, chunks: List[str]) -> List[DocumentChunk]:
        db_chunks = []
        for i, content in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=content,
            )
            self.db.add(chunk)
            db_chunks.append(chunk)
        await self.db.commit()
        for c in db_chunks:
            await self.db.refresh(c)
        return db_chunks

    async def get_document_chunks(self, document_id: int) -> List[DocumentChunk]:
        result = await self.db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())
