#!/usr/bin/env python3
"""
Script to process all queued documents in the database
"""

import os
import sys
import tempfile
import boto3
from botocore.config import Config

# Add current directory to path
sys.path.append('.')

from models.database import SessionLocal
from models.document import Document
# Import Document_Extraction components
try:
    from Document_Extraction.document_processor.utils.file_detector import FileTypeDetector
    from Document_Extraction.document_processor.processors.text_processor import TextProcessor
    from Document_Extraction.document_processor.processors.image_processor import ImageProcessor
    DOCUMENT_EXTRACTION_AVAILABLE = True
except ImportError as e:
    print(f"Document_Extraction not available: {e}")
    DOCUMENT_EXTRACTION_AVAILABLE = False

def get_minio_client():
    """Get MinIO client for file operations"""
    return boto3.client(
        's3',
        endpoint_url='http://localhost:9000',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
        config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4')
    )

def download_from_minio(s3_key: str, local_path: str) -> bool:
    """Download file from MinIO to local path"""
    try:
        client = get_minio_client()
        client.download_file('kmrl-documents', s3_key, local_path)
        return True
    except Exception as e:
        print(f"Failed to download file from MinIO: {e}")
        return False

def process_document(doc: Document) -> bool:
    """Process a single document"""
    if not DOCUMENT_EXTRACTION_AVAILABLE:
        print("Document_Extraction not available, skipping processing")
        doc.status = 'failed'
        return False
        
    temp_file_path = None
    try:
        print(f"Processing document: {doc.original_filename} (ID: {doc.id})")
        
        # Download file from MinIO
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc.original_filename}")
        temp_file_path = temp_file.name
        temp_file.close()
        
        if not download_from_minio(doc.s3_key, temp_file_path):
            print(f"Failed to download file: {doc.s3_key}")
            return False
        
        print(f"Downloaded file to: {temp_file_path}")
        
        # Detect file type
        file_detector = FileTypeDetector()
        file_type, mime_type, confidence = file_detector.detect_file_type(temp_file_path)
        print(f"Detected file type: {file_type.value} (confidence: {confidence:.2f})")
        
        # Process based on file type
        if file_type.value == "image":
            processor = ImageProcessor()
            result = processor.process(temp_file_path, file_type)
        else:
            processor = TextProcessor()
            result = processor.process(temp_file_path, file_type)
        
        # Extract results
        if hasattr(result, 'extracted_text'):
            text_content = result.extracted_text or ''
            language = result.metadata.get('language', 'unknown')
            confidence_score = result.metadata.get('confidence', 0.0)
        else:
            text_content = result.get('extracted_text', '')
            language = result.get('language', 'unknown')
            confidence_score = result.get('confidence', 0.0)
        
        print(f"Extracted text length: {len(text_content)} characters")
        print(f"Language: {language}")
        print(f"Confidence: {confidence_score}")
        
        # Update document in database
        doc.status = 'processed'
        doc.extracted_text = text_content
        doc.language = language
        doc.confidence_score = confidence_score
        doc.file_type_detected = file_type.value
        
        return True
        
    except Exception as e:
        print(f"Error processing document {doc.id}: {e}")
        doc.status = 'failed'
        return False
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                print(f"Failed to cleanup temporary file {temp_file_path}: {e}")

def main():
    """Process all queued documents"""
    db = SessionLocal()
    try:
        # Get queued documents
        queued_docs = db.query(Document).filter(Document.status == 'queued').limit(5).all()
        print(f"Found {len(queued_docs)} queued documents to process")
        
        processed_count = 0
        for doc in queued_docs:
            if process_document(doc):
                processed_count += 1
            
            # Commit changes for each document
            db.commit()
        
        print(f"\nProcessed {processed_count} out of {len(queued_docs)} documents")
        
        # Show final status
        from sqlalchemy import func
        status_counts = db.query(Document.status, func.count(Document.id)).group_by(Document.status).all()
        print("\nFinal document status breakdown:")
        for status, count in status_counts:
            print(f"  {status}: {count}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
