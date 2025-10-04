#!/usr/bin/env python3
"""
Automated Document Processor for KMRL
Processes queued documents using Document_Extraction module and updates database
"""

import os
import sys
import tempfile
import boto3
from botocore.config import Config
from typing import Dict, Any, Optional

# Add current directory to path
sys.path.append('.')

from models.database import SessionLocal
from models.document import Document
from Document_Extraction.document_processor.utils.file_detector import FileTypeDetector
from Document_Extraction.document_processor.processors.text_processor import TextProcessor
from Document_Extraction.document_processor.processors.image_processor import ImageProcessor
from Document_Extraction.document_processor.utils.quality_assessor import QualityAssessor
from Document_Extraction.document_processor.models import FileType

class AutomatedDocumentProcessor:
    """Automated document processor for KMRL system"""
    
    def __init__(self):
        self.minio_client = self._get_minio_client()
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
            print(f"Failed to download file from MinIO: {e}")
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
            print(f"🔄 Processing document: {doc.original_filename} (ID: {doc.id})")
            
            # Step 1: Download file from MinIO
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc.original_filename}")
            temp_file_path = temp_file.name
            temp_file.close()
            
            if not self.download_from_minio(doc.s3_key, temp_file_path):
                raise Exception(f"Failed to download file from MinIO: {doc.s3_key}")
            
            print(f"📥 Downloaded file to: {temp_file_path} ({os.path.getsize(temp_file_path)} bytes)")
            
            # Step 2: Detect file type
            file_type, mime_type, confidence = self.file_detector.detect_file_type(temp_file_path)
            print(f"🔍 Detected file type: {file_type.value} (confidence: {confidence:.2f})")
            
            # Step 3: Quality assessment
            quality_assessment = self.quality_assessor.assess_quality(temp_file_path, file_type.value)
            print(f"📊 Quality assessment: {quality_assessment.decision.value} (score: {quality_assessment.overall_quality_score:.2f})")
            
            # Step 4: Process based on file type and quality
            if quality_assessment.decision.value == 'reject':
                print("❌ Document rejected due to quality issues")
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
            
            print(f"📝 Extracted text length: {len(text_content)} characters")
            print(f"🌐 Language: {language}")
            print(f"🎯 Confidence: {confidence_score:.2f}")
            
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
            
            print(f"✅ Document processed successfully: {doc.original_filename}")
            
        except Exception as e:
            print(f"❌ Error processing document {doc.id}: {e}")
            result['error'] = str(e)
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    print(f"🗑️  Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    print(f"⚠️  Failed to cleanup temporary file {temp_file_path}: {e}")
        
        return result
    
    def update_document_in_db(self, doc: Document, result: Dict[str, Any]) -> bool:
        """Update document in database with processing results"""
        try:
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
            
            return True
        except Exception as e:
            print(f"❌ Failed to update document in database: {e}")
            return False
    
    def process_queued_documents(self, limit: int = 10) -> Dict[str, int]:
        """Process multiple queued documents"""
        db = SessionLocal()
        stats = {'processed': 0, 'failed': 0, 'total': 0}
        
        try:
            # Get queued documents
            queued_docs = db.query(Document).filter(Document.status == 'queued').limit(limit).all()
            stats['total'] = len(queued_docs)
            
            print(f"🚀 Starting automated processing of {stats['total']} documents...")
            print("=" * 60)
            
            for i, doc in enumerate(queued_docs, 1):
                print(f"\n📄 [{i}/{stats['total']}] Processing: {doc.original_filename}")
                
                # Process document
                result = self.process_document(doc)
                
                # Update database
                if self.update_document_in_db(doc, result):
                    if result['success']:
                        stats['processed'] += 1
                        print(f"✅ Successfully processed document {doc.id}")
                    else:
                        stats['failed'] += 1
                        print(f"❌ Failed to process document {doc.id}: {result['error']}")
                else:
                    stats['failed'] += 1
                    print(f"❌ Failed to update database for document {doc.id}")
                
                # Commit changes for each document
                db.commit()
            
            print("\n" + "=" * 60)
            print(f"📊 Processing Summary:")
            print(f"   ✅ Successfully processed: {stats['processed']}")
            print(f"   ❌ Failed: {stats['failed']}")
            print(f"   📈 Total: {stats['total']}")
            
        except Exception as e:
            print(f"❌ Error in batch processing: {e}")
        finally:
            db.close()
        
        return stats

def main():
    """Main function for automated document processing"""
    processor = AutomatedDocumentProcessor()
    
    # Process documents in batches
    batch_size = 5  # Process 5 documents at a time
    total_processed = 0
    total_failed = 0
    
    while True:
        stats = processor.process_queued_documents(limit=batch_size)
        total_processed += stats['processed']
        total_failed += stats['failed']
        
        if stats['total'] == 0:
            print("\n🎉 All queued documents have been processed!")
            break
        
        print(f"\n📈 Overall Progress: {total_processed} processed, {total_failed} failed")
        
        # Show current status
        db = SessionLocal()
        try:
            from sqlalchemy import func
            status_counts = db.query(Document.status, func.count(Document.id)).group_by(Document.status).all()
            print("\n📊 Current Document Status:")
            for status, count in status_counts:
                print(f"   {status.upper()}: {count}")
        finally:
            db.close()

if __name__ == "__main__":
    main()
