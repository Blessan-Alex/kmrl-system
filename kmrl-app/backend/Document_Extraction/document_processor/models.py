"""
Data models for document processing
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class FileType(str, Enum):
    """Supported file types"""
    CAD = "cad"
    IMAGE = "image"
    PDF = "pdf"
    OFFICE = "office"
    TEXT = "text"
    UNKNOWN = "unknown"


class QualityDecision(str, Enum):
    """Quality assessment decisions"""
    PROCESS = "process"
    ENHANCE = "enhance"
    REJECT = "reject"


class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ENHANCED = "enhanced"
    REJECTED = "rejected"


class DocumentMetadata(BaseModel):
    """Document metadata model"""
    file_id: str
    original_filename: str
    file_size: int
    file_type: FileType
    mime_type: str
    upload_timestamp: datetime
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    quality_score: Optional[float] = None
    quality_decision: Optional[QualityDecision] = None
    extracted_text: Optional[str] = None
    language: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_errors: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QualityAssessment(BaseModel):
    """Quality assessment results"""
    file_size_valid: bool
    image_quality_score: Optional[float] = None
    text_density: Optional[float] = None
    overall_quality_score: float
    decision: QualityDecision
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class ProcessingResult(BaseModel):
    """Document processing result"""
    file_id: str
    success: bool
    extracted_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class OCRResult(BaseModel):
    """OCR processing result"""
    text: str
    confidence: float
    language: str
    processing_time: float
    bounding_boxes: Optional[List[Dict[str, Any]]] = None


class ImageEnhancementResult(BaseModel):
    """Image enhancement result"""
    enhanced_image_path: str
    enhancement_applied: List[str]
    quality_improvement: float
    processing_time: float
