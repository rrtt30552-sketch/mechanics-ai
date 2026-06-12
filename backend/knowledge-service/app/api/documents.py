from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.database import get_db
from shared.exceptions import BadRequestException

from app.schemas.document import DocumentCreate, DocumentResponse, SearchRequest, SearchResponse
from app.services.knowledge_service import KnowledgeService
from app.services.document_parser import parse_document, chunk_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    category: Optional[str] = Form(None),
    tags: str = Form(""),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise BadRequestException("No file provided")

    # Read file content
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # Parse document text
    text = parse_document(file_bytes, file.filename)

    # Chunk text
    chunks = chunk_text(text)
    if not chunks:
        raise BadRequestException("Document is empty or could not be parsed")

    # Determine file type
    import os as _os
    file_type = _os.path.splitext(file.filename)[1].lstrip(".")

    # TODO: Upload to MinIO
    file_path = f"documents/{file.filename}"

    # Create document record
    svc = KnowledgeService(db)
    doc = await svc.create_document(
        data=DocumentCreate(
            title=title or file.filename,
            category=category,
            tags=[t.strip() for t in tags.split(",") if t.strip()] if tags else [],
            description=description,
            is_public=is_public,
        ),
        user_id=1,  # TODO: get from auth
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        chunk_count=len(chunks),
    )

    # Save chunks to PostgreSQL
    await svc.save_chunks(doc.id, chunks)

    # Generate embeddings and store in Milvus
    try:
        from shared.rag import rag_service
        await rag_service.index_document(
            doc_id=doc.id,
            chunks=chunks,
            user_id=1,  # TODO: get from auth
            file_type=file_type,
            category=category or "",
        )
        logger.info(f"Document {doc.id} indexed: {len(chunks)} chunks")
    except Exception as e:
        logger.warning(f"Embedding indexing failed (non-fatal): {e}")

    return doc


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    user_id: Optional[int] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    svc = KnowledgeService(db)
    return await svc.list_documents(user_id, category, skip, limit)


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    svc = KnowledgeService(db)
    return await svc.get_document(doc_id)


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    svc = KnowledgeService(db)

    # 删除 Milvus 向量
    try:
        from shared.rag import rag_service
        await rag_service.remove_document(doc_id)
    except Exception as e:
        logger.warning(f"Failed to remove vectors from Milvus: {e}")

    # 删除 PostgreSQL 记录
    await svc.delete_document(doc_id)
    return {"message": "Document deleted"}


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    req: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """语义搜索知识库"""
    from shared.rag import rag_service
    results = await rag_service.search(
        query=req.query,
        top_k=req.top_k,
        user_id=1,  # TODO: get from auth
        category=req.category,
    )
    return SearchResponse(results=results, query=req.query, total=len(results))
