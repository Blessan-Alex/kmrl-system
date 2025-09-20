"""
FastAPI Gateway for KMRL Document Ingestion
Unified API for document processing and management
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog
from auth.jwt_handler import JWTHandler
from auth.api_key_auth import APIKeyAuth
from middleware.rate_limiter import RateLimiter
from services.file_validator import FileValidator
from services.storage_service import StorageService
from services.queue_service import QueueService
from models.document import DocumentModel
import json

logger = structlog.get_logger()

app = FastAPI(
    title="KMRL Document Gateway",
    description="Unified API for KMRL document ingestion and processing",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Initialize services
jwt_handler = JWTHandler()
api_key_auth = APIKeyAuth()
rate_limiter = RateLimiter()
file_validator = FileValidator()
storage_service = StorageService()
queue_service = QueueService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "kmrl-gateway"}

@app.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form(...),
    metadata: str = Form(...),
    api_key: str = Depends(api_key_auth.verify_api_key)
):
    """Unified document upload endpoint for KMRL"""
    try:
        # Rate limiting
        await rate_limiter.check_rate_limit(api_key)
        
        # File validation for KMRL document types
        validation_result = await file_validator.validate_kmrl_file(file)
        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata format")
        
        # Store file
        storage_result = await storage_service.store_file(file, source)
        
        # Create database record
        document = DocumentModel(
            filename=file.filename,
            source=source,
            content_type=file.content_type,
            file_size=file.size,
            storage_path=storage_result["path"],
            metadata=metadata_dict,
            status="pending"
        )
        
        # Queue processing task
        task_id = await queue_service.queue_document_processing(document)
        
        logger.info("KMRL document uploaded successfully", 
                   filename=file.filename, 
                   source=source,
                   task_id=task_id)
        
        return {
            "status": "success",
            "document_id": document.id,
            "task_id": task_id,
            "message": "Document queued for processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Document upload failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    api_key: str = Depends(api_key_auth.verify_api_key)
):
    """Get document processing status"""
    try:
        document = await DocumentModel.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "document_id": document.id,
            "status": document.status,
            "filename": document.filename,
            "source": document.source,
            "confidence_score": document.confidence_score,
            "language": document.language,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get document status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
