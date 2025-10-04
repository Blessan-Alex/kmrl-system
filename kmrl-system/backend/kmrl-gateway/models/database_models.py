"""
Enhanced Database Models for KMRL Gateway
SQLAlchemy ORM models for PostgreSQL integration
Based on doc_processor implementation with KMRL-specific enhancements
"""

import enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, CheckConstraint
from sqlalchemy.sql import func
from .database import Base

class DocumentStatus(enum.Enum):
    """Document processing status enumeration"""
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class Document(Base):
    """Enhanced document model for KMRL processing with PostgreSQL integration"""
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'processing', 'processed', 'failed')",
            name='ck_document_status'
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, index=True)
    s3_key = Column(String, index=True)
    source = Column(String, index=True)  # gmail, maximo, whatsapp, etc.
    content_type = Column(String)
    file_size = Column(Integer)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="queued", nullable=False)
    extracted_text = Column(Text)
    confidence_score = Column(Float)
    language = Column(String, default="unknown")
    department = Column(String, default="general")
    document_metadata = Column(JSON)  # Store additional metadata
    uploaded_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ProcessingLog(Base):
    """Processing log for document workflow tracking"""
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    status = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processing_time = Column(Float)  # Processing time in seconds
    error_details = Column(Text)

class DocumentVersion(Base):
    """Document version control for updates and revisions"""
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    version_number = Column(Integer)
    s3_key = Column(String)
    file_size = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String)
    change_summary = Column(Text)
