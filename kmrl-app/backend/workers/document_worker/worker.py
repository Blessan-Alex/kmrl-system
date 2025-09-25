"""
Document Processing Worker for KMRL
Handles document processing pipeline with OCR, text extraction, and language detection
"""

import os
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
import structlog
from celery import Celery
import pytesseract
from PIL import Image
import markitdown
# Note: These shared modules need to be implemented or replaced with existing services
# from shared.document_processor import DocumentProcessor
# from shared.language_detector import LanguageDetector
# from shared.department_classifier import DepartmentClassifier

logger = structlog.get_logger()

# Initialize Celery
celery_app = Celery('kmrl-document-worker')
celery_app.config_from_object('config.celery_config.CELERY_CONFIG')

# Autodiscover tasks to ensure all are registered
celery_app.autodiscover_tasks(['workers.document_worker.worker'])

# Initialize processors (commented out until shared modules are implemented)
# document_processor = DocumentProcessor()
# language_detector = LanguageDetector()
# department_classifier = DepartmentClassifier()

@celery_app.task
def process_document(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process document through KMRL pipeline"""
    try:
        document_id = document_data.get('document_id')
        filename = document_data.get('filename')
        source = document_data.get('source')
        storage_path = document_data.get('storage_path')
        content_type = document_data.get('content_type')
        
        logger.info(f"Processing document: {filename}")
        
        # Step 1: Extract text content
        text_content = document_processor.extract_text(storage_path, content_type)
        
        # Step 2: Detect language
        language = language_detector.detect_language(text_content)
        
        # Step 3: Classify department
        department = department_classifier.classify_department(text_content, source)
        
        # Step 4: Generate confidence score
        confidence_score = document_processor.calculate_confidence(text_content, content_type)
        
        # Step 5: Update document status
        result = {
            "document_id": document_id,
            "status": "completed",
            "language": language,
            "department": department,
            "confidence_score": confidence_score,
            "text_content": text_content,
            "processed_at": datetime.now().isoformat()
        }
        
        logger.info(f"Document processed successfully: {filename}")
        return result
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        return {
            "document_id": document_data.get('document_id'),
            "status": "failed",
            "error": str(e),
            "processed_at": datetime.now().isoformat()
        }

@celery_app.task
def batch_process_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process multiple documents in batch"""
    results = []
    for doc in documents:
        result = process_document.delay(doc)
        results.append(result.get())
    return results

if __name__ == "__main__":
    celery_app.start()
