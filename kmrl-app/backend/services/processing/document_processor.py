"""
Enhanced Document Processing Service for KMRL Gateway
Advanced document processing with text extraction and workflow management
Based on doc_processor implementation with KMRL-specific enhancements
"""

import os
import fitz  # PyMuPDF
import io
import boto3
from datetime import datetime
from typing import Optional, Dict, Any
from celery import Celery
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError
from botocore.client import Config as BotocoreConfig
import structlog

from models.document import Document, DocumentStatus, ProcessingLog
from models.database import SessionLocal

logger = structlog.get_logger()

# Celery app configuration
celery_app = Celery('kmrl-gateway')
celery_app.config_from_object('config.celery_config.CELERY_CONFIG')

# Autodiscover tasks to ensure all are registered
celery_app.autodiscover_tasks(['services.processing.document_processor'])

# MinIO configuration
BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'kmrl-documents')

def get_minio_client():
    """Get MinIO client for file operations"""
    endpoint = os.getenv('MINIO_ENDPOINT', 'localhost').strip()
    user = os.getenv('MINIO_ACCESS_KEY', 'minioadmin').strip()
    password = os.getenv('MINIO_SECRET_KEY', 'minioadmin').strip()
    endpoint_url = f"http://{endpoint}:9000"
    
    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=user,
        aws_secret_access_key=password,
        config=BotocoreConfig(s3={'addressing_style': 'path'}, signature_version='s3v4')
    )

@celery_app.task(name="kmrl-gateway.process_document")
def process_document(document_id: int):
    """
    Enhanced document processing task with text extraction and status management
    """
    db = SessionLocal()
    doc = None
    start_time = datetime.now()
    
    try:
        # Get document from database
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return {"status": "error", "message": "Document not found"}

        # Update status to processing
        doc.status = "processing"
        doc.updated_at = datetime.now()
        db.commit()
        
        logger.info(f"Processing document: {doc.original_filename} (ID: {doc.id})")
        
        # Create processing log entry
        log_entry = ProcessingLog(
            document_id=doc.id,
            status="processing",
            message="Started document processing",
            timestamp=datetime.now()
        )
        db.add(log_entry)
        db.commit()

        # Download file from MinIO
        minio_client = get_minio_client()
        try:
            response = minio_client.get_object(Bucket=BUCKET_NAME, Key=doc.s3_key)
            file_content = response["Body"].read()
            logger.info(f"Downloaded {doc.s3_key} from MinIO ({len(file_content)} bytes)")
        except ClientError as e:
            logger.error(f"Failed to download file from MinIO: {e}")
            raise Exception(f"Failed to download file: {e}")

        # Extract text based on file type
        extracted_text = ""
        processing_notes = []
        
        try:
            if doc.original_filename.lower().endswith('.pdf'):
                logger.info("Extracting text from PDF...")
                with fitz.open(stream=io.BytesIO(file_content)) as pdf_doc:
                    extracted_text = "".join(page.get_text() for page in pdf_doc)
                    processing_notes.append(f"Extracted text from {len(pdf_doc)} pages")
                    
            elif doc.original_filename.lower().endswith('.txt'):
                logger.info("Extracting text from TXT file...")
                extracted_text = file_content.decode('utf-8', errors='ignore')
                processing_notes.append("Extracted text from plain text file")
                
            elif doc.original_filename.lower().endswith(('.docx', '.doc')):
                logger.info("Processing DOCX/DOC file...")
                # For now, mark as unsupported but could add python-docx support
                extracted_text = "DOCX/DOC file processing not yet implemented"
                processing_notes.append("DOCX/DOC processing not implemented")
                
            else:
                logger.info("Unsupported file type for text extraction")
                extracted_text = f"File type {doc.original_filename.split('.')[-1]} not supported for text extraction"
                processing_notes.append(f"Unsupported file type: {doc.original_filename.split('.')[-1]}")

            # Calculate confidence score based on text length and quality
            confidence_score = calculate_confidence_score(extracted_text, doc.original_filename)
            
            # Update document with extracted text
            doc.extracted_text = extracted_text
            doc.confidence_score = confidence_score
            doc.status = "processed"
            doc.updated_at = datetime.now()
            
            # Create success log entry
            processing_time = (datetime.now() - start_time).total_seconds()
            log_entry = ProcessingLog(
                document_id=doc.id,
                status="processed",
                message=f"Successfully processed document. {', '.join(processing_notes)}",
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            db.add(log_entry)
            db.commit()
            
            logger.info(f"Successfully processed document: {doc.original_filename}")
            logger.info(f"Extracted {len(extracted_text)} characters with confidence {confidence_score:.2f}")
            
            return {
                "status": "success",
                "document_id": doc.id,
                "extracted_text_length": len(extracted_text),
                "confidence_score": confidence_score,
                "processing_time": processing_time
            }

        except Exception as extraction_error:
            logger.error(f"Error during text extraction: {extraction_error}")
            doc.extracted_text = f"Failed to extract text: {extraction_error}"
            doc.status = "failed"
            doc.updated_at = datetime.now()
            
            # Create error log entry
            processing_time = (datetime.now() - start_time).total_seconds()
            log_entry = ProcessingLog(
                document_id=doc.id,
                status="failed",
                message=f"Text extraction failed: {str(extraction_error)}",
                processing_time=processing_time,
                error_details=str(extraction_error),
                timestamp=datetime.now()
            )
            db.add(log_entry)
            db.commit()
            
            return {
                "status": "error",
                "document_id": doc.id,
                "error": str(extraction_error)
            }

    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}")
        if doc:
            doc.status = "failed"
            doc.updated_at = datetime.now()
            
            # Create error log entry
            processing_time = (datetime.now() - start_time).total_seconds()
            log_entry = ProcessingLog(
                document_id=doc.id,
                status="failed",
                message=f"Document processing failed: {str(e)}",
                processing_time=processing_time,
                error_details=str(e),
                timestamp=datetime.now()
            )
            db.add(log_entry)
            db.commit()
            
        return {
            "status": "error",
            "document_id": document_id,
            "error": str(e)
        }
    finally:
        if db.is_active:
            db.commit()
        db.close()
        logger.info(f"Database session closed for document {document_id}")

def calculate_confidence_score(extracted_text: str, filename: str) -> float:
    """
    Calculate confidence score for extracted text
    Based on text length, quality indicators, and file type
    """
    if not extracted_text or extracted_text.startswith("Failed to extract"):
        return 0.0
    
    # Base score
    score = 0.5
    
    # Length factor (longer text generally better)
    text_length = len(extracted_text.strip())
    if text_length > 1000:
        score += 0.2
    elif text_length > 500:
        score += 0.1
    elif text_length > 100:
        score += 0.05
    
    # Quality indicators
    if any(char.isalpha() for char in extracted_text):
        score += 0.1  # Contains letters
    
    if any(char.isdigit() for char in extracted_text):
        score += 0.05  # Contains numbers
    
    # File type factor
    if filename.lower().endswith('.txt'):
        score += 0.1  # Plain text files are more reliable
    elif filename.lower().endswith('.pdf'):
        score += 0.05  # PDFs can be more complex
    
    # Normalize to 0-1 range
    return min(max(score, 0.0), 1.0)

@celery_app.task(name="kmrl-gateway.cleanup_old_logs")
def cleanup_old_logs(days_to_keep: int = 30):
    """
    Cleanup old processing logs to maintain database performance
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = db.query(ProcessingLog).filter(
            ProcessingLog.timestamp < cutoff_date
        ).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted_count} old processing logs")
        return {"deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {e}")
        return {"error": str(e)}
    finally:
        db.close()
