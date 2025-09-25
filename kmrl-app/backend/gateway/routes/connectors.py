"""
Connector API Routes
Handles connector-specific upload and status endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
import structlog
import json

from models.database import get_db
from services.auth.api_key_auth import APIKeyAuth

# Initialize API key auth
api_key_auth = APIKeyAuth()
from services.processing.file_validator import FileValidator
from services.storage.minio_service import EnhancedStorageService
from services.queue.celery_service import QueueService
from services.monitoring.websocket_manager import websocket_manager

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/connectors", tags=["connectors"])

# Initialize services
file_validator = FileValidator()
storage_service = EnhancedStorageService()
queue_service = QueueService()

@router.post("/upload")
async def connector_upload(
    file: UploadFile = File(...),
    source: str = Form(...),
    metadata: str = Form("{}"),
    api_key: str = Depends(api_key_auth.verify_api_key),
    db: Session = Depends(get_db)
):
    """Direct connector upload endpoint"""
    try:
        # Parse metadata safely
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            metadata_dict = {}
        
        # Add detailed logging
        logger.info("Starting connector upload", 
                   filename=file.filename, 
                   source=source, 
                   content_type=file.content_type)
        
        # Validate file
        validation_result = await file_validator.validate_kmrl_file(file)
        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        # Store file
        result = await storage_service.store_file(
            file=file,
            source=source,
            metadata=metadata_dict,
            db=db
        )
        document = result['document']
        
        # Queue for processing
        task_id = await queue_service.queue_document_processing(document)
        
        # Broadcast update
        await websocket_manager.broadcast_document_update(document.id, "queued")
        
        logger.info("Connector upload successful", document_id=document.id)
        
        return {
            "document_id": document.id,
            "status": "queued",
            "task_id": task_id,
            "message": "Document uploaded and queued for processing"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Connector upload failed: {e}", exc_info=True)
        # Return more specific error details
        error_detail = f"Upload failed: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/status")
async def connector_status(
    api_key: str = Depends(api_key_auth.verify_api_key)
):
    """Get connector status and health"""
    try:
        # Check connector health
        import redis
        redis_client = redis.Redis.from_url("redis://localhost:6379")
        
        health_data = redis_client.hget('connector_health', 'status')
        if health_data:
            import json
            connector_status = json.loads(health_data)
        else:
            connector_status = {"error": "No health data available"}
        
        return {
            "connectors": connector_status,
            "timestamp": "2025-01-01T00:00:00Z",
            "overall_status": "healthy" if "error" not in connector_status else "degraded"
        }
        
    except Exception as e:
        logger.error(f"Connector status failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")
