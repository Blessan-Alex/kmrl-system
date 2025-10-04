#!/usr/bin/env python3
"""
Direct Document Processor for KMRL
Processes queued documents directly without Celery (for immediate processing)
"""

import os
import sys
import tempfile
import boto3
import json
from datetime import datetime
from pathlib import Path
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

class DirectDocumentProcessor:
    """Direct document processor (no Celery) for KMRL system"""
    
    def __init__(self, output_folder: str = "processed_documents_output"):
        self.minio_client = self._get_minio_client()
        self.file_detector = FileTypeDetector()
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
        self.quality_assessor = QualityAssessor()
        
        # Create output folder for JSON files
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        print(f"📁 Output folder: {self.output_folder.absolute()}")
    
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
    
    def save_json_output(self, doc: Document, result: Dict[str, Any]):
        """Save processing result to JSON file"""
        try:
            # Create JSON data
            json_data = {
                "document_info": {
                    "id": doc.id,
                    "original_filename": doc.original_filename,
                    "s3_key": doc.s3_key,
                    "source": doc.source,
                    "file_size": doc.file_size
                },
                "processing_result": {
                    "success": result.get('success', False),
                    "error": result.get('error'),
                    "file_type_detected": result.get('file_type_detected'),
                    "language": result.get('language'),
                    "confidence_score": result.get('confidence_score'),
                    "quality_score": result.get('quality_score'),
                    "quality_decision": result.get('quality_decision')
                },
                "extracted_content": {
                    "text": result.get('extracted_text', ''),
                    "text_length": len(result.get('extracted_text', ''))
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Create filename
            safe_filename = "".join(c for c in doc.original_filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_filename = safe_filename.replace(' ', '_')
            json_filename = f"{doc.id:06d}_{safe_filename}.json"
            json_path = self.output_folder / json_filename
            
            # Save JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 JSON saved: {json_path}")
            
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")
    
    
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
            # Save JSON output
            self.save_json_output(doc, result)
            
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
    
    def process_batch(self, limit: int = 10) -> Dict[str, int]:
        """Process a batch of queued documents directly"""
        db = SessionLocal()
        stats = {'processed': 0, 'failed': 0, 'total': 0}
        
        try:
            # Get queued documents
            queued_docs = db.query(Document).filter(Document.status == 'queued').limit(limit).all()
            stats['total'] = len(queued_docs)
            
            print(f"🚀 Starting direct processing of {stats['total']} documents...")
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
    
    def create_processing_summary(self, stats: Dict[str, int]) -> str:
        """Create a summary JSON file of the processing session"""
        try:
            summary_data = {
                "processing_session": {
                    "timestamp": datetime.now().isoformat(),
                    "processor": "DirectDocumentProcessor",
                    "version": "1.0",
                    "output_folder": str(self.output_folder.absolute())
                },
                "statistics": {
                    "processed": stats['processed'],
                    "failed": stats['failed'],
                    "total": stats['total'],
                    "success_rate": f"{(stats['processed'] / stats['total'] * 100):.1f}%" if stats['total'] > 0 else "0%"
                },
                "output_files": {
                    "json_files_created": stats['processed'] + stats['failed'],
                    "folder_location": str(self.output_folder.absolute())
                }
            }
            
            summary_filename = f"processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            summary_path = self.output_folder / summary_filename
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            print(f"📋 Processing summary saved: {summary_path}")
            return str(summary_path)
            
        except Exception as e:
            print(f"❌ Failed to create processing summary: {e}")
            return ""

def main():
    """Main function for direct document processing"""
    processor = DirectDocumentProcessor()
    
    # Process documents in batches
    batch_size = 5  # Process 5 documents at a time
    total_processed = 0
    total_failed = 0
    
    while True:
        stats = processor.process_batch(limit=batch_size)
        total_processed += stats['processed']
        total_failed += stats['failed']
        
        if stats['total'] == 0:
            print("\n🎉 All queued documents have been processed!")
            break
        
        print(f"\n📈 Overall Progress: {total_processed} processed, {total_failed} failed")
        
        # Create processing summary
        overall_stats = {'processed': total_processed, 'failed': total_failed, 'total': total_processed + total_failed}
        summary_path = processor.create_processing_summary(overall_stats)
        
        # Show current status
        db = SessionLocal()
        try:
            from sqlalchemy import func
            status_counts = db.query(Document.status, func.count(Document.id)).group_by(Document.status).all()
            print("\n📊 Current Document Status:")
            for status, count in status_counts:
                print(f"   {status.upper()}: {count}")
            
            print(f"\n📁 All JSON outputs saved in: {processor.output_folder.absolute()}")
            if summary_path:
                print(f"📋 Processing summary: {summary_path}")
        finally:
            db.close()

if __name__ == "__main__":
    main()
