"""
Document Model for KMRL Gateway
Handles document metadata and processing status
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class DocumentModel(BaseModel):
    """Document model for KMRL processing"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    source: str
    content_type: str
    file_size: int
    storage_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"
    confidence_score: Optional[float] = None
    language: str = "unknown"
    department: str = "general"
    uploaded_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @classmethod
    async def get_by_id(cls, document_id: str) -> Optional['DocumentModel']:
        """Get document by ID (placeholder for database integration)"""
        # This would typically query a database
        # For now, return None as placeholder
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "source": self.source,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "storage_path": self.storage_path,
            "metadata": self.metadata,
            "status": self.status,
            "confidence_score": self.confidence_score,
            "language": self.language,
            "department": self.department,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
