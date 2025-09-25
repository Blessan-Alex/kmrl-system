"""
Enhanced FastAPI Gateway for KMRL Document Ingestion
PostgreSQL-integrated API gateway with advanced security, monitoring, and real-time processing
"""

import os
import time
import json
import io
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import structlog
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Import enhanced services
from services.auth.jwt_handler import JWTHandler
from services.auth.api_key_auth import APIKeyAuth
from middleware.rate_limiter import RateLimiter
from middleware.security_middleware import SecurityMiddleware
from services.processing.file_validator import FileValidator
from services.storage.minio_service import EnhancedStorageService
from services.queue.celery_service import QueueService
from services.monitoring.health_service import HealthService
from services.monitoring.metrics_service import MetricsService
from services.monitoring.websocket_manager import websocket_manager
from services.processing.document_processor import process_document

# Import PostgreSQL models and schemas
from models.database import get_db, create_tables
from models.document import Document, DocumentStatus, ProcessingLog
from models.schemas import (
    Document as DocumentSchema, 
    DocumentCreate, 
    DocumentUpdate, 
    DocumentList,
    DocumentStatistics,
    WebSocketMessage
)

# Import routes
from gateway.routes.documents import router as documents_router
from gateway.routes.connectors import router as connectors_router
from gateway.routes.health import router as health_router
from gateway.routes.websocket import router as websocket_router

logger = structlog.get_logger()

# Enhanced FastAPI application
app = FastAPI(
    title="KMRL Document Gateway Enhanced",
    description="PostgreSQL-integrated API for KMRL document ingestion and processing with real-time updates",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enhanced middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Initialize enhanced services
jwt_handler = JWTHandler()
api_key_auth = APIKeyAuth()
rate_limiter = RateLimiter()
file_validator = FileValidator()
enhanced_storage_service = EnhancedStorageService()
queue_service = QueueService()
health_service = HealthService()
metrics_service = MetricsService()

# Include routers
app.include_router(documents_router)
app.include_router(connectors_router)
app.include_router(health_router)
app.include_router(websocket_router)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    try:
        create_tables()
        logger.info("Database tables created successfully")
        await websocket_manager.broadcast_system_status("startup", "KMRL Gateway Enhanced started")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Record metrics
    metrics_service.record_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration=process_time
    )
    
    return response

# Enhanced health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_status = await health_service.comprehensive_health_check()
        return health_status
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    try:
        metrics = await metrics_service.get_metrics()
        return Response(content=metrics, media_type="text/plain")
    except Exception as e:
        logger.error("Metrics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail="Metrics unavailable")

@app.get("/api/v1/status")
async def get_system_status():
    """Get comprehensive system status"""
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "service": "kmrl-gateway",
            "version": "2.0.0",
            "health": await health_service.comprehensive_health_check(),
            "metrics": await metrics_service.get_system_metrics(),
            "uptime": time.time() - metrics_service.start_time
        }
        return status
    except Exception as e:
        logger.error("Status check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Status unavailable")

# WebSocket endpoints for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client messages if needed
            try:
                message = json.loads(data)
                if message.get("type") == "subscribe_document":
                    document_id = message.get("document_id")
                    if document_id:
                        await websocket_manager.subscribe_to_document(websocket, document_id)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)

@app.websocket("/ws/{user_id}")
async def websocket_user_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for user-specific updates"""
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle user-specific messages
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, user_id)

# Enhanced document upload endpoint
@app.post("/api/v1/documents/upload", response_model=DocumentSchema)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    source: str = Form(...),
    metadata: str = Form(...),
    api_key: str = Depends(api_key_auth.verify_api_key),
    db: Session = Depends(get_db)
):
    """Enhanced document upload with PostgreSQL integration and real-time updates"""
    start_time = time.time()
    
    try:
        # Add detailed logging for debugging
        logger.info("Starting document upload", 
                   filename=file.filename,
                   source=source,
                   content_type=file.content_type,
                   file_size=file.size if hasattr(file, 'size') else 'unknown',
                   api_key=api_key[:8] + "..." if api_key else 'none')
        
        # Rate limiting
        await rate_limiter.check_rate_limit(request, "document_upload", user_id=api_key)
        
        # File validation
        validation_result = await file_validator.validate_kmrl_file(file)
        if not validation_result["valid"]:
            metrics_service.record_error("validation_failed")
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        # Parse metadata with improved error handling
        try:
            if metadata and metadata.strip():
                metadata_dict = json.loads(metadata)
                logger.info("Metadata parsed successfully", metadata_keys=list(metadata_dict.keys()))
            else:
                metadata_dict = {}
                logger.info("No metadata provided, using empty dict")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON metadata: {e}, using empty dict")
            metadata_dict = {}
        except Exception as e:
            logger.error(f"Metadata parsing error: {e}, using empty dict")
            metadata_dict = {}
        
        # Store file with PostgreSQL integration
        db_document = await enhanced_storage_service.store_file_with_db(
            file, source, db, metadata_dict, uploaded_by=api_key
        )
        
        # Queue for processing
        task_id = await queue_service.queue_document_processing(db_document, "normal")
        
        # Broadcast real-time update
        await websocket_manager.broadcast_document_update(
            db_document.id, "queued", 0, "Document uploaded and queued for processing"
        )
        
        duration = time.time() - start_time
        logger.info(f"Document uploaded and queued: {db_document.id}", 
                   duration=duration, filename=file.filename, source=source, task_id=task_id)
        
        return db_document
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ClientError as e:
        logger.error(f"MinIO storage failed: {e}")
        raise HTTPException(status_code=503, detail="Storage service unavailable")
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        # Return more specific error details
        error_detail = f"Upload failed: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)

# Document listing endpoint
@app.get("/api/v1/documents/", response_model=DocumentList)
def list_documents(
    skip: int = 0, 
    limit: int = 100, 
    source: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List documents with filtering and pagination"""
    try:
        query = db.query(Document)
        
        # Apply filters
        if source:
            query = query.filter(Document.source == source)
        if status:
            query = query.filter(Document.status == status)
        if department:
            query = query.filter(Document.department == department)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        documents = query.offset(skip).limit(limit).all()
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        current_page = (skip // limit) + 1
        
        return DocumentList(
            documents=documents,
            total=total,
            page=current_page,
            per_page=limit,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document status endpoint
@app.get("/api/v1/documents/{document_id}/status", response_model=DocumentSchema)
def get_document_status(document_id: int, db: Session = Depends(get_db)):
    """Get document status and details"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document download endpoint
@app.get("/api/v1/documents/{document_id}/download")
async def download_document(document_id: int, db: Session = Depends(get_db)):
    """Download original document file"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Download file content
        file_content = await enhanced_storage_service.download_file(document)
        
        # Prepare headers for download
        headers = {
            'Content-Disposition': f'attachment; filename="{document.original_filename}"',
            'Content-Type': document.content_type
        }
        
        return StreamingResponse(
            io.BytesIO(file_content), 
            media_type=document.content_type, 
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document statistics endpoint
@app.get("/api/v1/documents/statistics", response_model=DocumentStatistics)
def get_document_statistics(db: Session = Depends(get_db)):
    """Get document processing statistics"""
    try:
        # Get total documents
        total_documents = db.query(Document).count()
        
        # Get statistics by status
        status_stats = {}
        status_values = ["queued", "processing", "processed", "failed"]
        for status in status_values:
            count = db.query(Document).filter(Document.status == status).count()
            status_stats[status] = count
        
        # Get statistics by source
        source_stats = {}
        sources = db.query(Document.source).distinct().all()
        for (source,) in sources:
            count = db.query(Document).filter(Document.source == source).count()
            source_stats[source] = count
        
        # Get statistics by department
        department_stats = {}
        departments = db.query(Document.department).distinct().all()
        for (department,) in departments:
            count = db.query(Document).filter(Document.department == department).count()
            department_stats[department] = count
        
        # Get total size
        total_size = db.query(Document.file_size).all()
        total_size = sum(size[0] for size in total_size if size[0])
        
        # Get average processing time
        processing_logs = db.query(ProcessingLog.processing_time).filter(
            ProcessingLog.processing_time.isnot(None)
        ).all()
        avg_processing_time = None
        if processing_logs:
            times = [log[0] for log in processing_logs if log[0]]
            if times:
                avg_processing_time = sum(times) / len(times)
        
        return DocumentStatistics(
            total_documents=total_documents,
            by_status=status_stats,
            by_source=source_stats,
            by_department=department_stats,
            total_size=total_size,
            average_processing_time=avg_processing_time
        )
        
    except Exception as e:
        logger.error(f"Failed to get document statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Processing callback endpoint
@app.post("/api/v1/processing/callback/{task_id}")
async def processing_callback(task_id: str, result: dict):
    """Handle processing results from Celery workers"""
    try:
        # Update document status based on processing result
        document_id = result.get("document_id")
        status = result.get("status")
        
        if document_id and status:
            # Broadcast real-time update
            await websocket_manager.broadcast_document_update(
                document_id, status, 100, f"Processing completed with status: {status}"
            )
        
        logger.info(f"Processing callback received for task {task_id}: {result}")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Processing callback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket connection info endpoint
@app.get("/api/v1/websocket/info")
def get_websocket_info():
    """Get WebSocket connection information"""
    return {
        "total_connections": websocket_manager.get_connection_count(),
        "websocket_url": "/ws",
        "user_websocket_url": "/ws/{user_id}"
    }

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "KMRL Document Gateway Enhanced",
        "version": "3.0.0",
        "features": [
            "PostgreSQL Integration",
            "Real-time WebSocket Updates", 
            "Advanced Document Processing",
            "MinIO Storage",
            "Security & Authentication"
        ],
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
