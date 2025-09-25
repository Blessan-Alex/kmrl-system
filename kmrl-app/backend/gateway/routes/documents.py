"""
Document API Routes
Handles document upload, download, and management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import structlog
import io
import redis

from models.database import get_db
from models.schemas import Document as DocumentSchema, DocumentCreate, DocumentList
from models.document import Document
from services.auth.api_key_auth import APIKeyAuth

# Initialize API key auth
api_key_auth = APIKeyAuth()
from services.processing.file_validator import FileValidator
from services.storage.minio_service import EnhancedStorageService
from services.queue.celery_service import QueueService
from services.monitoring.websocket_manager import websocket_manager

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Initialize services
file_validator = FileValidator()
storage_service = EnhancedStorageService()
queue_service = QueueService()

# Upload endpoint moved to main app.py
# Use /api/v1/documents/upload from main gateway
# This prevents endpoint duplication conflicts

@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    api_key: str = Depends(api_key_auth.verify_api_key),
    db: Session = Depends(get_db)
):
    """Download a document"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get file content
        file_content = await storage_service.download_file(document)
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=document.content_type,
            headers={"Content-Disposition": f"attachment; filename={document.original_filename}"}
        )
        
    except Exception as e:
        logger.error(f"Document download failed: {e}")
        raise HTTPException(status_code=500, detail="Download failed")


@router.post("/test-upload")
async def test_upload(
    file: UploadFile = File(...),
    api_key: str = Depends(api_key_auth.verify_api_key)
):
    """Simple test upload endpoint"""
    try:
        # Just return success without complex processing
        return {
            "status": "success",
            "filename": file.filename,
            "size": file.size if hasattr(file, 'size') else 'unknown',
            "message": "Test upload successful"
        }
    except Exception as e:
        logger.error(f"Test upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test upload failed: {str(e)}")


@router.get("/")
async def list_documents(
    limit: int = 10,
    offset: int = 0,
    status: Optional[str] = None,
    source: Optional[str] = None,
    api_key: str = Depends(api_key_auth.verify_api_key),
    db: Session = Depends(get_db)
):
    """List documents with filtering"""
    try:
        query = db.query(Document)
        
        if status:
            query = query.filter(Document.status == status)
        if source:
            query = query.filter(Document.source == source)
        
        documents = query.offset(offset).limit(limit).all()
        total = query.count()
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        current_page = (offset // limit) + 1 if limit > 0 else 1
        
        return DocumentList(
            documents=documents,
            total=total,
            page=current_page,
            per_page=limit,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Document list failed: {e}")
        raise HTTPException(status_code=500, detail="List failed")

@router.get("/statistics")
async def get_document_statistics(
    api_key: str = Depends(api_key_auth.verify_api_key),
    db: Session = Depends(get_db)
):
    """Get document statistics"""
    try:
        total_documents = db.query(Document).count()
        
        # Status breakdown
        status_counts = db.query(
            Document.status,
            func.count(Document.id)
        ).group_by(Document.status).all()
        
        # Source breakdown
        source_counts = db.query(
            Document.source,
            func.count(Document.id)
        ).group_by(Document.source).all()
        
        return {
            "total_documents": total_documents,
            "by_status": dict(status_counts),
            "by_source": dict(source_counts)
        }
        
    except Exception as e:
        logger.error(f"Statistics failed: {e}")
        raise HTTPException(status_code=500, detail="Statistics failed")

@router.get("/validation-errors")
async def get_validation_errors(
    api_key: str = Depends(api_key_auth.verify_api_key),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get file validation errors for frontend display"""
    try:
        # Connect to Redis to get validation errors
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
        # Get recent validation errors
        error_keys = redis_client.keys("kmrl:validation_errors:*")
        recent_errors = []
        
        for key in error_keys[-50:]:  # Get last 50 errors
            error_data = redis_client.hgetall(key)
            if error_data:
                recent_errors.append({
                    "filename": error_data.get(b'filename', b'').decode('utf-8'),
                    "file_type": error_data.get(b'file_type', b'').decode('utf-8'),
                    "error_reason": error_data.get(b'error_reason', b'').decode('utf-8'),
                    "timestamp": error_data.get(b'timestamp', b'').decode('utf-8'),
                    "source": error_data.get(b'source', b'').decode('utf-8')
                })
        
        # Get supported file types
        supported_types = [
            ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp",
            ".dwg", ".dxf", ".step", ".stp", ".iges", ".igs",
            ".txt", ".md", ".rst", ".html", ".xml", ".json", ".csv"
        ]
        
        return {
            "recent_errors": recent_errors,
            "supported_file_types": supported_types,
            "total_errors": len(recent_errors)
        }
        
    except Exception as e:
        logger.error(f"Validation errors fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch validation errors")
