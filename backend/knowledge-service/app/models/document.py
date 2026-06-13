from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, xlsx, pptx, dwg
    file_path = Column(String(500), nullable=False)  # MinIO path
    file_size = Column(Integer, default=0)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, index=True, nullable=False)
    is_public = Column(Boolean, default=False)
    chunk_count = Column(Integer, default=0)  # number of vector chunks
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    vector_id = Column(String(100), nullable=True)  # Milvus vector ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
