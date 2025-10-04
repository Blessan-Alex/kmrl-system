# Document_Extraction Integration Plan

## Overview

This document provides a detailed plan for integrating `@Document_Extraction` into the current KMRL pipeline without breaking existing functionality. The integration will enhance document processing capabilities while maintaining backward compatibility.

---

## Current Workflow Analysis

### Current Pipeline Flow

```
1. Gateway receives file (Gmail/GDrive/Manual upload)
   ↓
2. File validation (FileValidator)
   ↓
3. File stored in MinIO
   ↓
4. Metadata saved to PostgreSQL (Document model)
   ↓
5. Job queued in Redis (QueueService.queue_document_processing)
   ↓
6. Celery worker picks job (process_document task)
   ↓
7. Basic text extraction (PyMuPDF for PDFs only)
   ↓
8. Results stored back to PostgreSQL
```

### Current Worker Implementation

**File**: `services/processing/document_processor.py:49-204`

```python
@celery_app.task(name="kmrl-gateway.process_document")
def process_document(document_id: int):
    # Current implementation:
    # 1. Download file from MinIO
    # 2. Basic PDF text extraction with PyMuPDF
    # 3. Simple confidence scoring
    # 4. Store results in PostgreSQL
```

**Limitations**:
- Only supports PDF files
- Basic text extraction
- No quality assessment
- No OCR capabilities
- No multi-format support

---

## Proposed Integration Workflow

### Enhanced Pipeline Flow

```
1. Gateway receives file (Gmail/GDrive/Manual upload)
   ↓
2. Enhanced file validation (FileValidator + Document_Extraction)
   ↓
3. File stored in MinIO
   ↓
4. Enhanced metadata saved to PostgreSQL (Document model + new fields)
   ↓
5. Job queued in Redis (QueueService.queue_document_processing)
   ↓
6. Enhanced Celery worker picks job (process_document_enhanced task)
   ↓
7. Document_Extraction pipeline processing:
   - File type detection
   - Quality assessment
   - Multi-format processing (PDF, Office, Images, CAD)
   - OCR with Malayalam support
   - Language detection
   ↓
8. Enhanced results stored back to PostgreSQL
```

---

## Technical Integration Steps

### Step 1: Database Schema Updates

**File**: `models/document.py`

```python
# Add new fields to Document model
class Document(Base):
    # ... existing fields ...
    
    # Document_Extraction enhanced fields
    file_type_detected = Column(String)  # cad, image, pdf, office, text
    quality_score = Column(Float)
    quality_decision = Column(String)  # process, enhance, reject
    detection_confidence = Column(Float)
    language_detected = Column(String)
    needs_translation = Column(Boolean, default=False)
    processing_metadata = Column(JSON)  # Store Document_Extraction metadata
    enhancement_applied = Column(Boolean, default=False)
    human_review_required = Column(Boolean, default=False)
```

### Step 2: Enhanced Worker Implementation

**File**: `services/processing/document_processor.py`

```python
# Add Document_Extraction imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Document_Extraction'))

from Document_Extraction.document_processor.tasks import process_document as de_process_document
from Document_Extraction.document_processor.utils.file_detector import FileTypeDetector
from Document_Extraction.document_processor.utils.quality_assessor import QualityAssessor

@celery_app.task(name="kmrl-gateway.process_document_enhanced")
def process_document_enhanced(document_id: int):
    """
    Enhanced document processing with Document_Extraction integration
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
        
        logger.info(f"Processing document with Document_Extraction: {doc.original_filename}")
        
        # Download file from MinIO
        minio_client = get_minio_client()
        try:
            response = minio_client.get_object(Bucket=BUCKET_NAME, Key=doc.s3_key)
            file_content = response["Body"].read()
            
            # Create temporary file for Document_Extraction
            temp_file_path = f"/tmp/{doc.s3_key}"
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
            with open(temp_file_path, 'wb') as f:
                f.write(file_content)
                
        except ClientError as e:
            logger.error(f"Failed to download file from MinIO: {e}")
            raise Exception(f"Failed to download file: {e}")

        # Call Document_Extraction pipeline
        try:
            # Use Document_Extraction process_document task
            de_result = de_process_document(
                file_path=temp_file_path,
                file_id=str(doc.id),
                source=doc.source,
                filename=doc.original_filename
            )
            
            if de_result.get('success'):
                # Extract results from Document_Extraction
                processing_result = de_result.get('processing_result', {})
                quality_assessment = de_result.get('quality_assessment', {})
                
                # Update document with enhanced results
                doc.extracted_text = processing_result.get('extracted_text', '')
                doc.confidence_score = de_result.get('confidence_score', 0.0)
                doc.file_type_detected = processing_result.get('metadata', {}).get('file_type_detected')
                doc.quality_score = quality_assessment.get('overall_quality_score', 0.0)
                doc.quality_decision = quality_assessment.get('decision', 'process')
                doc.language_detected = processing_result.get('metadata', {}).get('language', 'unknown')
                doc.processing_metadata = processing_result.get('metadata', {})
                doc.human_review_required = de_result.get('human_review_required', False)
                doc.status = "processed"
                doc.updated_at = datetime.now()
                
                # Create success log entry
                processing_time = (datetime.now() - start_time).total_seconds()
                log_entry = ProcessingLog(
                    document_id=doc.id,
                    status="processed",
                    message=f"Successfully processed with Document_Extraction. Quality: {doc.quality_score:.2f}, Language: {doc.language_detected}",
                    processing_time=processing_time,
                    timestamp=datetime.now()
                )
                db.add(log_entry)
                db.commit()
                
                logger.info(f"Document_Extraction processing completed: {doc.original_filename}")
                
                return {
                    "status": "success",
                    "document_id": doc.id,
                    "extracted_text_length": len(doc.extracted_text),
                    "confidence_score": doc.confidence_score,
                    "quality_score": doc.quality_score,
                    "language_detected": doc.language_detected,
                    "file_type_detected": doc.file_type_detected,
                    "processing_time": processing_time
                }
            else:
                # Document_Extraction failed, fall back to basic processing
                logger.warning(f"Document_Extraction failed, falling back to basic processing: {de_result.get('error')}")
                return _fallback_to_basic_processing(doc, file_content, db, start_time)
                
        except Exception as de_error:
            logger.error(f"Document_Extraction processing failed: {de_error}")
            # Fall back to basic processing
            return _fallback_to_basic_processing(doc, file_content, db, start_time)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}")
        if doc:
            doc.status = "failed"
            doc.updated_at = datetime.now()
            db.commit()
        return {"status": "error", "document_id": document_id, "error": str(e)}
    finally:
        if db.is_active:
            db.commit()
        db.close()

def _fallback_to_basic_processing(doc, file_content, db, start_time):
    """Fallback to basic processing if Document_Extraction fails"""
    try:
        # Use existing basic processing logic
        extracted_text = ""
        if doc.original_filename.lower().endswith('.pdf'):
            with fitz.open(stream=io.BytesIO(file_content)) as pdf_doc:
                extracted_text = "".join(page.get_text() for page in pdf_doc)
        elif doc.original_filename.lower().endswith('.txt'):
            extracted_text = file_content.decode('utf-8', errors='ignore')
        
        doc.extracted_text = extracted_text
        doc.confidence_score = calculate_confidence_score(extracted_text, doc.original_filename)
        doc.status = "processed"
        doc.updated_at = datetime.now()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        log_entry = ProcessingLog(
            document_id=doc.id,
            status="processed",
            message="Processed with basic fallback method",
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        db.add(log_entry)
        db.commit()
        
        return {
            "status": "success",
            "document_id": doc.id,
            "extracted_text_length": len(extracted_text),
            "confidence_score": doc.confidence_score,
            "processing_time": processing_time,
            "fallback": True
        }
    except Exception as e:
        logger.error(f"Fallback processing failed: {e}")
        return {"status": "error", "document_id": doc.id, "error": str(e)}
```

### Step 3: Queue Service Updates

**File**: `services/queue/celery_service.py`

```python
async def queue_document_processing(self, document: Any, priority: str = "normal") -> str:
    """Enhanced document queuing with Document_Extraction integration"""
    try:
        # Determine queue based on priority
        queue_name = self._get_queue_name(priority)
        queue_config = self.queue_configs.get(queue_name, self.queue_configs['document_processing'])
        
        # Create enhanced task payload
        task_payload = {
            "document_id": str(document.id),
            "filename": document.original_filename,
            "source": document.source,
            "s3_key": document.s3_key,
            "content_type": document.content_type,
            "metadata": document.document_metadata,
            "priority": priority,
            "queued_at": datetime.now().isoformat(),
            "max_retries": queue_config['max_retries']
        }
        
        # Queue the enhanced task
        task = self.celery_app.send_task(
            'kmrl-gateway.process_document_enhanced',  # Use enhanced task
            args=[document.id],
            queue=queue_name,
            priority=queue_config['priority']
        )
        
        # Store task metadata in Redis
        await self._store_task_metadata(task.id, {
            'document_id': str(document.id),
            'queue_name': queue_name,
            'priority': priority,
            'status': 'PENDING',
            'queued_at': datetime.now().isoformat(),
            'retry_count': 0,
            'enhanced_processing': True
        })
        
        logger.info(f"Enhanced document queued for processing: {task.id}")
        return task.id
        
    except Exception as e:
        logger.error(f"Failed to queue enhanced document: {e}")
        raise Exception(f"Failed to queue document: {str(e)}")
```

### Step 4: Gateway Integration (Optional Enhancement)

**File**: `gateway/app.py`

```python
# Add Document_Extraction imports for enhanced validation
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Document_Extraction'))

from Document_Extraction.document_processor.utils.file_detector import FileTypeDetector
from Document_Extraction.document_processor.utils.quality_assessor import QualityAssessor

@app.post("/api/v1/documents/upload-enhanced", response_model=DocumentSchema)
async def upload_document_enhanced(
    request: Request,
    file: UploadFile = File(...),
    source: str = Form(...),
    metadata: str = Form(...),
    api_key: str = Depends(api_key_auth.verify_api_key),
    db: Session = Depends(get_db)
):
    """Enhanced document upload with Document_Extraction preprocessing"""
    try:
        # Enhanced file type detection
        detector = FileTypeDetector()
        file_type, mime_type, confidence = detector.detect_file_type(file.filename)
        
        # Quality assessment
        assessor = QualityAssessor()
        quality_assessment = assessor.assess_quality(file.filename, file_type.value)
        
        # Store file with enhanced metadata
        db_document = await enhanced_storage_service.store_file_with_db(
            file, source, db, metadata_dict, uploaded_by=api_key
        )
        
        # Add enhanced metadata
        db_document.file_type_detected = file_type.value
        db_document.quality_score = quality_assessment.overall_quality_score
        db_document.quality_decision = quality_assessment.decision.value
        db_document.detection_confidence = confidence
        db.commit()
        
        # Queue for enhanced processing
        task_id = await queue_service.queue_document_processing(db_document, "normal")
        
        return db_document
        
    except Exception as e:
        logger.error(f"Enhanced upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Implementation Strategy

### Phase 1: Database Migration (Week 1)

1. **Create migration script**:
   ```sql
   ALTER TABLE documents ADD COLUMN file_type_detected VARCHAR(50);
   ALTER TABLE documents ADD COLUMN quality_score FLOAT;
   ALTER TABLE documents ADD COLUMN quality_decision VARCHAR(20);
   ALTER TABLE documents ADD COLUMN detection_confidence FLOAT;
   ALTER TABLE documents ADD COLUMN language_detected VARCHAR(10);
   ALTER TABLE documents ADD COLUMN needs_translation BOOLEAN DEFAULT FALSE;
   ALTER TABLE documents ADD COLUMN processing_metadata JSON;
   ALTER TABLE documents ADD COLUMN enhancement_applied BOOLEAN DEFAULT FALSE;
   ALTER TABLE documents ADD COLUMN human_review_required BOOLEAN DEFAULT FALSE;
   ```

2. **Update Document model** with new fields
3. **Test migration** on development database

### Phase 2: Worker Integration (Week 2)

1. **Copy Document_Extraction module** to `services/document_extraction/`
2. **Update worker** with enhanced processing logic
3. **Add fallback mechanism** for backward compatibility
4. **Test with sample documents**

### Phase 3: Queue Integration (Week 3)

1. **Update QueueService** to use enhanced tasks
2. **Add enhanced task metadata** to Redis
3. **Test queue processing** with different file types
4. **Monitor performance** and error rates

### Phase 4: Gateway Enhancement (Week 4)

1. **Add enhanced upload endpoint** (optional)
2. **Update file validation** to support more file types
3. **Add quality assessment** at upload time
4. **Test end-to-end workflow**

### Phase 5: Production Rollout (Week 5)

1. **Deploy to staging** environment
2. **Monitor processing** performance and quality
3. **Gradual rollout** to production
4. **Monitor and optimize**

---

## Risk Mitigation & Safeguards

### 1. Backward Compatibility

- **Fallback mechanism**: If Document_Extraction fails, fall back to basic processing
- **Existing endpoints**: Keep current `/api/v1/documents/upload` working
- **Database compatibility**: New fields are nullable, won't break existing queries

### 2. Error Handling

```python
try:
    # Document_Extraction processing
    de_result = de_process_document(...)
    if de_result.get('success'):
        # Use enhanced results
        pass
    else:
        # Fall back to basic processing
        return _fallback_to_basic_processing(...)
except Exception as e:
    logger.error(f"Document_Extraction failed: {e}")
    # Fall back to basic processing
    return _fallback_to_basic_processing(...)
```

### 3. Performance Monitoring

- **Processing time tracking**: Monitor enhanced vs basic processing times
- **Success rate monitoring**: Track Document_Extraction success rates
- **Resource usage**: Monitor CPU/memory usage for enhanced processing
- **Queue monitoring**: Track queue lengths and processing rates

### 4. Gradual Rollout

- **Feature flag**: Control enhanced processing via environment variable
- **A/B testing**: Route some documents to enhanced processing
- **Monitoring**: Track performance and quality metrics
- **Rollback plan**: Ability to disable enhanced processing if issues arise

---

## Expected Benefits

### Enhanced Capabilities

- **Multi-format support**: PDF, Office, Images, CAD files
- **OCR processing**: Malayalam and English text extraction
- **Quality assessment**: Intelligent routing based on file quality
- **Language detection**: Automatic language identification
- **Image enhancement**: Preprocessing for better OCR results

### Improved Performance

- **Intelligent routing**: Process files based on quality and type
- **Parallel processing**: Multiple workers for different file types
- **Caching**: Reuse processing results for similar files
- **Monitoring**: Real-time processing status and metrics

### Better User Experience

- **Real-time updates**: WebSocket notifications for processing status
- **Quality feedback**: Users know if files need enhancement
- **Language support**: Automatic Malayalam/English detection
- **Error handling**: Clear error messages and recovery options

---

## Conclusion

This integration plan provides a safe, gradual approach to enhancing the KMRL document processing pipeline with Document_Extraction capabilities. The key is maintaining backward compatibility while adding enhanced processing capabilities.

**Key Success Factors**:
- Gradual rollout with feature flags
- Comprehensive error handling and fallback mechanisms
- Performance monitoring and optimization
- User training and documentation
- Robust testing at each phase

**Expected Timeline**: 5 weeks for full integration
**Resource Requirements**: 2-3 developers, 1 DevOps engineer
**Risk Level**: Low (mitigated by fallback mechanisms and gradual rollout)
**Business Impact**: High (significant improvement in document processing capabilities)
