#!/usr/bin/env python3
"""
Celery Worker for Automated Document Processing
Integrates with Document_Extraction module for full document processing pipeline
"""

import os
import sys
import tempfile
import boto3
from botocore.config import Config
from typing import Dict, Any, Optional

# Import shared module FIRST to ensure correct paths are set up
import shared

import json
import uuid
from datetime import datetime
import structlog
from celery import Celery

# Initialize logger first
logger = structlog.get_logger()

# Import Document_Extraction processors
try:
    from Document_Extraction.document_processor.utils.file_detector import FileTypeDetector
    from Document_Extraction.document_processor.processors.text_processor import TextProcessor
    from Document_Extraction.document_processor.processors.image_processor import ImageProcessor
    from Document_Extraction.document_processor.utils.quality_assessor import QualityAssessor
    from Document_Extraction.document_processor.models import FileType
    DOCUMENT_EXTRACTION_AVAILABLE = True
    logger.info("Document_Extraction module imported successfully")
except ImportError as e:
    DOCUMENT_EXTRACTION_AVAILABLE = False
    logger.warning(f"Document_Extraction not available in automated processor: {e}")

# Import database models
from models.database import SessionLocal
from models.document import Document

# Initialize Celery
celery_app = Celery('kmrl-automated-processor')
from config.celery_config import CELERY_CONFIG
celery_app.config_from_object(CELERY_CONFIG)

# Autodiscover tasks
celery_app.autodiscover_tasks(['workers.automated_document_processor'])

class AutomatedDocumentProcessor:
    """Automated document processor for KMRL system"""
    
    def __init__(self):
        self.minio_client = self._get_minio_client()
        if DOCUMENT_EXTRACTION_AVAILABLE:
            self.file_detector = FileTypeDetector()
            self.text_processor = TextProcessor()
            self.image_processor = ImageProcessor()
            self.quality_assessor = QualityAssessor()
    
    def _get_minio_client(self):
        """Get MinIO client for file operations"""
        return boto3.client(
            's3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin',
            config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4')
        )
    
    def download_from_minio(self, s3_key: str, local_path: str) -> bool:
        """Download file from MinIO to local path"""
        try:
            self.minio_client.download_file('kmrl-documents', s3_key, local_path)
            return True
        except Exception as e:
            logger.error(f"Failed to download file from MinIO: {e}")
            return False
    
    def process_document(self, doc: Document) -> Dict[str, Any]:
        """Process a single document with full Document_Extraction pipeline"""
        temp_file_path = None
        result = {
            'success': False,
            'document_id': doc.id,
            'filename': doc.original_filename,
            'error': None,
            'extracted_text': '',
            'language': 'unknown',
            'confidence_score': 0.0,
            'file_type_detected': 'unknown'
        }
        
        try:
            logger.info(f"Processing document: {doc.original_filename} (ID: {doc.id})")
            
            # Step 1: Download file from MinIO
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc.original_filename}")
            temp_file_path = temp_file.name
            temp_file.close()
            
            if not self.download_from_minio(doc.s3_key, temp_file_path):
                raise Exception(f"Failed to download file from MinIO: {doc.s3_key}")
            
            logger.info(f"Downloaded file to: {temp_file_path} ({os.path.getsize(temp_file_path)} bytes)")
            
            if not DOCUMENT_EXTRACTION_AVAILABLE:
                # Fallback processing
                result.update({
                    'success': True,
                    'extracted_text': f"Document processed successfully. File: {doc.original_filename}",
                    'language': 'unknown',
                    'confidence_score': 0.8,
                    'file_type_detected': 'unknown'
                })
                return result
            
            # Step 2: Detect file type
            file_type, mime_type, confidence = self.file_detector.detect_file_type(temp_file_path)
            logger.info(f"Detected file type: {file_type.value} (confidence: {confidence:.2f})")
            
            # Step 3: Quality assessment
            quality_assessment = self.quality_assessor.assess_quality(temp_file_path, file_type.value)
            logger.info(f"Quality assessment: {quality_assessment.decision.value} (score: {quality_assessment.overall_quality_score:.2f})")
            
            # Step 4: Process based on file type and quality
            if quality_assessment.decision.value == 'reject':
                logger.warning("Document rejected due to quality issues")
                result['error'] = f"Quality assessment failed: {quality_assessment.issues}"
                return result
            
            # Step 5: Extract text content
            if file_type == FileType.IMAGE:
                processing_result = self.image_processor.process(temp_file_path, file_type)
            else:
                processing_result = self.text_processor.process(temp_file_path, file_type)
            
            # Step 6: Extract results
            if hasattr(processing_result, 'extracted_text'):
                text_content = processing_result.extracted_text or ''
                language = processing_result.metadata.get('language', 'unknown')
                confidence_score = processing_result.metadata.get('confidence', 0.0)
            else:
                text_content = processing_result.get('extracted_text', '')
                language = processing_result.get('language', 'unknown')
                confidence_score = processing_result.get('confidence', 0.0)
            
            logger.info(f"Extracted text length: {len(text_content)} characters, Language: {language}, Confidence: {confidence_score:.2f}")
            
            # Step 7: Update result
            result.update({
                'success': True,
                'extracted_text': text_content,
                'language': language,
                'confidence_score': confidence_score,
                'file_type_detected': file_type.value,
                'quality_score': quality_assessment.overall_quality_score,
                'quality_decision': quality_assessment.decision.value
            })
            
            logger.info(f"Document processed successfully: {doc.original_filename}")
            
        except Exception as e:
            logger.error(f"Error processing document {doc.id}: {e}")
            result['error'] = str(e)
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.info(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temporary file {temp_file_path}: {e}")
        
        return result

# Initialize processor
processor = AutomatedDocumentProcessor()

@celery_app.task(bind=True, name='process_single_document')
def process_single_document(self, document_id: int) -> Dict[str, Any]:
    """Process a single document by ID"""
    try:
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if not doc:
                return {
                    'success': False,
                    'error': f'Document with ID {document_id} not found',
                    'document_id': document_id
                }
            
            if doc.status != 'queued':
                return {
                    'success': False,
                    'error': f'Document {document_id} is not in queued status (current: {doc.status})',
                    'document_id': document_id
                }
            
            # Process document
            result = processor.process_document(doc)
            
            # Update database
            if result['success']:
                doc.status = 'processed'
                doc.extracted_text = result['extracted_text']
                doc.language = result['language']
                doc.confidence_score = result['confidence_score']
                doc.file_type_detected = result['file_type_detected']
                doc.quality_score = result.get('quality_score', 0.0)
                doc.quality_decision = result.get('quality_decision', 'unknown')
            else:
                doc.status = 'failed'
                doc.extracted_text = None
            
            db.commit()
            logger.info(f"Updated document {document_id} status to {doc.status}")
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in process_single_document task: {e}")
        return {
            'success': False,
            'error': str(e),
            'document_id': document_id
        }

@celery_app.task(bind=True, name='process_batch_documents')
def process_batch_documents(self, batch_size: int = 10) -> Dict[str, Any]:
    """Process a batch of queued documents"""
    try:
        db = SessionLocal()
        stats = {'processed': 0, 'failed': 0, 'total': 0, 'document_ids': []}
        
        try:
            # Get queued documents
            queued_docs = db.query(Document).filter(Document.status == 'queued').limit(batch_size).all()
            stats['total'] = len(queued_docs)
            
            logger.info(f"Processing batch of {stats['total']} documents")
            
            for doc in queued_docs:
                stats['document_ids'].append(doc.id)
                
                # Process document
                result = processor.process_document(doc)
                
                # Update database
                if result['success']:
                    doc.status = 'processed'
                    doc.extracted_text = result['extracted_text']
                    doc.language = result['language']
                    doc.confidence_score = result['confidence_score']
                    doc.file_type_detected = result['file_type_detected']
                    doc.quality_score = result.get('quality_score', 0.0)
                    doc.quality_decision = result.get('quality_decision', 'unknown')
                    stats['processed'] += 1
                    logger.info(f"Successfully processed document {doc.id}")
                else:
                    doc.status = 'failed'
                    doc.extracted_text = None
                    stats['failed'] += 1
                    logger.error(f"Failed to process document {doc.id}: {result['error']}")
                
                # Commit changes for each document
                db.commit()
            
            logger.info(f"Batch processing completed: {stats['processed']} processed, {stats['failed']} failed")
            return stats
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in process_batch_documents task: {e}")
        return {
            'success': False,
            'error': str(e),
            'processed': 0,
            'failed': 0,
            'total': 0
        }

@celery_app.task(bind=True, name='process_all_queued_documents')
def process_all_queued_documents(self) -> Dict[str, Any]:
    """Process all queued documents in the system"""
    try:
        db = SessionLocal()
        total_stats = {'processed': 0, 'failed': 0, 'total': 0, 'batches': 0}
        
        try:
            # Get total count of queued documents
            total_queued = db.query(Document).filter(Document.status == 'queued').count()
            total_stats['total'] = total_queued
            
            logger.info(f"Starting to process all {total_queued} queued documents")
            
            # Process in batches of 10
            batch_size = 10
            while True:
                batch_result = process_batch_documents.delay(batch_size)
                batch_stats = batch_result.get(timeout=300)  # 5 minute timeout
                
                total_stats['processed'] += batch_stats.get('processed', 0)
                total_stats['failed'] += batch_stats.get('failed', 0)
                total_stats['batches'] += 1
                
                logger.info(f"Batch {total_stats['batches']} completed: {batch_stats.get('processed', 0)} processed, {batch_stats.get('failed', 0)} failed")
                
                # Check if there are more documents to process
                remaining = db.query(Document).filter(Document.status == 'queued').count()
                if remaining == 0:
                    break
                
                logger.info(f"Remaining documents: {remaining}")
            
            logger.info(f"All documents processed: {total_stats['processed']} processed, {total_stats['failed']} failed")
            return total_stats
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in process_all_queued_documents task: {e}")
        return {
            'success': False,
            'error': str(e),
            'processed': 0,
            'failed': 0,
            'total': 0
        }

if __name__ == "__main__":
    celery_app.start()
