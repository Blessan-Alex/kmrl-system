"""
Pydantic Schemas for KMRL Gateway
Data validation and serialization for API requests/responses
Based on doc_processor implementation with KMRL-specific enhancements
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from .document import DocumentStatus

class DocumentBase(BaseModel):
    """Base document schema with common fields"""
    original_filename: str
    source: str
    content_type: str
    file_size: int

class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    s3_key: str
    document_metadata: Optional[Dict[str, Any]] = None
    department: Optional[str] = "general"
    language: Optional[str] = "unknown"
    uploaded_by: Optional[str] = None

class DocumentUpdate(BaseModel):
    """Schema for updating document fields"""
    status: Optional[DocumentStatus] = None
    extracted_text: Optional[str] = None
    confidence_score: Optional[float] = None
    language: Optional[str] = None
    department: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None

class Document(DocumentBase):
    """Complete document schema for API responses"""
    id: int
    s3_key: str
    upload_time: datetime
    status: DocumentStatus
    extracted_text: Optional[str] = None
    confidence_score: Optional[float] = None
    language: Optional[str] = None
    department: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentList(BaseModel):
    """Schema for document listing with pagination"""
    documents: list[Document]
    total: int
    page: int
    per_page: int
    total_pages: int

class ProcessingLogCreate(BaseModel):
    """Schema for creating processing log entries"""
    document_id: int
    status: str
    message: str
    processing_time: Optional[float] = None
    error_details: Optional[str] = None

class ProcessingLog(BaseModel):
    """Schema for processing log entries"""
    id: int
    document_id: int
    status: str
    message: str
    timestamp: datetime
    processing_time: Optional[float] = None
    error_details: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentStatistics(BaseModel):
    """Schema for document statistics"""
    total_documents: int
    by_status: Dict[str, int]
    by_source: Dict[str, int]
    by_department: Dict[str, int]
    total_size: int
    average_processing_time: Optional[float] = None

class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str
    document_id: Optional[int] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
