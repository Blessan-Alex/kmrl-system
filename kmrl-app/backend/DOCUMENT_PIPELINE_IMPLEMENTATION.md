# Document Pipeline Implementation Plan

## Overview

This document describes how to safely integrate the `@Document_Extraction` pipeline into the existing KMRL backend codebase, focusing on `connectors/` and `gateway/` components. The integration will enhance the current document processing capabilities with advanced OCR, quality assessment, and multi-format support while maintaining backward compatibility.

---

## Current Backend Structure

### Gateway (`gateway/`)
- **`app.py`** - FastAPI application with document upload endpoints
- **`routes/documents.py`** - Document management API routes
- **`routes/connectors.py`** - Connector management endpoints
- **Current processing**: Basic PDF text extraction using PyMuPDF
- **Storage**: MinIO integration with PostgreSQL metadata
- **Queue**: Celery-based async processing

### Connectors (`connectors/`)
- **`base/base_connector.py`** - Base connector architecture
- **`implementations/`** - Gmail, Google Drive, Maximo, SharePoint, WhatsApp connectors
- **`tasks/sync_tasks.py`** - Celery tasks for connector synchronization
- **Current flow**: Fetch documents → Upload to API → Queue for processing

### Services (`services/`)
- **`processing/document_processor.py`** - Current basic document processing
- **`processing/file_validator.py`** - File validation and security scanning
- **`storage/minio_service.py`** - MinIO storage operations
- **`queue/celery_service.py`** - Celery queue management

### Models (`models/`)
- **`document.py`** - SQLAlchemy models for documents and processing logs
- **`schemas.py`** - Pydantic schemas for API validation
- **Current fields**: Basic document metadata, extracted text, confidence score

---

## Mapping from Document_Extraction Audit

### Core Integration Points

#### 1. **File Type Detection** → `services/processing/file_validator.py`
- **Current**: Basic extension and MIME type validation
- **Enhancement**: Integrate `Document_Extraction/utils/file_detector.py`
- **Benefits**: Multi-method detection (extension + MIME + magic numbers), confidence scoring

#### 2. **Quality Assessment** → `services/processing/document_processor.py`
- **Current**: Basic confidence scoring based on text length
- **Enhancement**: Integrate `Document_Extraction/utils/quality_assessor.py`
- **Benefits**: Image quality analysis, text density assessment, intelligent routing

#### 3. **Document Processing** → `services/processing/document_processor.py`
- **Current**: PDF-only text extraction with PyMuPDF
- **Enhancement**: Integrate `Document_Extraction/processors/` modules
- **Benefits**: Multi-format support (Office, Images, CAD), OCR with Malayalam support

#### 4. **Language Detection** → `models/document.py`
- **Current**: No language detection
- **Enhancement**: Integrate `Document_Extraction/utils/language_detector.py`
- **Benefits**: Malayalam/English detection, translation flags

#### 5. **Enhanced Processing** → `workers/document_worker/worker.py`
- **Current**: Basic text extraction
- **Enhancement**: Integrate `Document_Extraction/document_processor/` pipeline
- **Benefits**: Quality-based routing, image enhancement, OCR processing

---

## Required Changes

### 1. **Gateway Enhancements**

#### Update `gateway/app.py`
```python
# Add new processing capabilities
from Document_Extraction.document_processor.tasks import process_document as enhanced_process_document
from Document_Extraction.document_processor.utils.file_detector import FileTypeDetector
from Document_Extraction.document_processor.utils.quality_assessor import QualityAssessor

# Enhanced upload endpoint with quality assessment
@app.post("/api/v1/documents/upload-enhanced")
async def upload_document_enhanced(
    file: UploadFile = File(...),
    source: str = Form(...),
    metadata: str = Form(...),
    api_key: str = Depends(api_key_auth.verify_api_key),
    db: Session = Depends(get_db)
):
    # File type detection
    detector = FileTypeDetector()
    file_type, mime_type, confidence = detector.detect_file_type(file.filename)
    
    # Quality assessment
    assessor = QualityAssessor()
    quality_assessment = assessor.assess_quality(file.filename, file_type.value)
    
    # Route to appropriate processor based on quality
    if quality_assessment.decision == "process":
        # Use enhanced processing
        task = enhanced_process_document.delay(file_path, file_id)
    elif quality_assessment.decision == "enhance":
        # Apply enhancement before processing
        # Implementation needed
    else:
        # Reject or flag for review
        # Implementation needed
```

#### Update `gateway/routes/documents.py`
```python
# Add new endpoints for enhanced processing
@router.post("/process-enhanced/{document_id}")
async def process_document_enhanced(
    document_id: int,
    api_key: str = Depends(api_key_auth.verify_api_key),
    db: Session = Depends(get_db)
):
    """Process document with enhanced pipeline"""
    # Implementation using Document_Extraction pipeline
```

### 2. **Connector Enhancements**

#### Update `connectors/base/base_connector.py`
```python
# Add enhanced processing hooks
from Document_Extraction.document_processor.utils.file_detector import FileTypeDetector
from Document_Extraction.document_processor.utils.quality_assessor import QualityAssessor

class BaseConnector(ABC):
    def __init__(self, source_name: str, api_endpoint: str):
        # ... existing code ...
        self.file_detector = FileTypeDetector()
        self.quality_assessor = QualityAssessor()
    
    def upload_to_api_enhanced(self, document: Document) -> Dict[str, Any]:
        """Enhanced upload with quality assessment"""
        # Detect file type
        file_type, mime_type, confidence = self.file_detector.detect_file_type(document.filename)
        
        # Assess quality
        quality_assessment = self.quality_assessor.assess_quality(document.filename, file_type.value)
        
        # Add quality metadata to upload
        document.metadata.update({
            'file_type': file_type.value,
            'quality_score': quality_assessment.overall_quality_score,
            'quality_decision': quality_assessment.decision.value,
            'detection_confidence': confidence
        })
        
        return self.upload_to_api(document)
```

### 3. **Service Layer Integration**

#### Update `services/processing/document_processor.py`
```python
# Replace current processing with Document_Extraction pipeline
from Document_Extraction.document_processor.processors.text_processor import TextProcessor
from Document_Extraction.document_processor.processors.image_processor import ImageProcessor
from Document_Extraction.document_processor.processors.cad_processor import CADProcessor
from Document_Extraction.document_processor.utils.language_detector import LanguageDetector

@celery_app.task(name="kmrl-gateway.process_document_enhanced")
def process_document_enhanced(document_id: int):
    """Enhanced document processing with Document_Extraction pipeline"""
    # Implementation using Document_Extraction processors
    # Route to appropriate processor based on file type
    # Apply quality assessment and enhancement
    # Detect language and add translation flags
```

#### Update `services/processing/file_validator.py`
```python
# Integrate Document_Extraction file detection
from Document_Extraction.document_processor.utils.file_detector import FileTypeDetector
from Document_Extraction.document_processor.utils.quality_assessor import QualityAssessor

class FileValidator:
    def __init__(self):
        # ... existing code ...
        self.file_detector = FileTypeDetector()
        self.quality_assessor = QualityAssessor()
    
    async def validate_kmrl_file_enhanced(self, file: UploadFile) -> Dict[str, Any]:
        """Enhanced validation with Document_Extraction capabilities"""
        # Use Document_Extraction file detection
        # Apply quality assessment
        # Return enhanced validation results
```

### 4. **Model Enhancements**

#### Update `models/document.py`
```python
# Add new fields for enhanced processing
class Document(Base):
    # ... existing fields ...
    
    # Enhanced processing fields
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

#### Update `models/schemas.py`
```python
# Add new schemas for enhanced processing
class DocumentEnhanced(Document):
    """Enhanced document schema with Document_Extraction fields"""
    file_type_detected: Optional[str] = None
    quality_score: Optional[float] = None
    quality_decision: Optional[str] = None
    detection_confidence: Optional[float] = None
    language_detected: Optional[str] = None
    needs_translation: Optional[bool] = None
    processing_metadata: Optional[Dict[str, Any]] = None
    enhancement_applied: Optional[bool] = None
    human_review_required: Optional[bool] = None

class QualityAssessment(BaseModel):
    """Quality assessment schema"""
    file_size_valid: bool
    image_quality_score: Optional[float] = None
    text_density: Optional[float] = None
    overall_quality_score: float
    decision: str
    issues: List[str] = []
    recommendations: List[str] = []
```

### 5. **Worker Integration**

#### Update `workers/document_worker/worker.py`
```python
# Integrate Document_Extraction worker
from Document_Extraction.document_processor.worker import main as document_extraction_worker
from Document_Extraction.document_processor.tasks import process_document as enhanced_process_document

@celery_app.task
def process_document_enhanced(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced document processing using Document_Extraction pipeline"""
    # Use Document_Extraction processing pipeline
    # Apply quality assessment and routing
    # Handle different file types appropriately
    # Return enhanced results with metadata
```

---

## Dependencies

### New Python Packages
```python
# Add to requirements.txt
# From Document_Extraction/requirements.txt
celery>=5.3.0
redis>=4.5.0
pydantic>=2.0.0
loguru>=0.7.0
python-dotenv>=1.0.0

# Image Processing & OCR
opencv-python>=4.8.0
pytesseract>=0.3.10
Pillow>=10.0.0
numpy>=1.24.0

# Document Processing
markitdown>=0.0.1a0
PyPDF2>=3.0.0
pdfplumber>=0.10.0
python-docx>=0.8.11
pandas>=2.0.0
openpyxl>=3.1.0

# File Detection
python-magic>=0.4.27
python-magic-bin>=0.4.14  # Windows alternative

# Language Detection
langdetect>=1.0.9

# CAD Processing
ezdxf>=1.1.0
```

### System Dependencies
```bash
# Install system dependencies
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-mal
sudo apt install -y libmagic1 libmagic-dev
sudo apt install -y redis-server
```

### Configuration Updates
```python
# Update config/unified_config.py
class UnifiedConfig:
    # ... existing config ...
    
    # Document_Extraction specific config
    DOCUMENT_EXTRACTION_ENABLED = os.getenv('DOCUMENT_EXTRACTION_ENABLED', 'True').lower() == 'true'
    TESSERACT_CMD = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')
    TESSERACT_LANGUAGES = os.getenv('TESSERACT_LANGUAGES', 'mal+eng')
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
    IMAGE_QUALITY_THRESHOLD = float(os.getenv('IMAGE_QUALITY_THRESHOLD', '0.7'))
    TEXT_DENSITY_THRESHOLD = float(os.getenv('TEXT_DENSITY_THRESHOLD', '0.1'))
```

---

## Safety & Migration Strategy

### 1. **Feature Flag Implementation**
```python
# Add feature flag for gradual rollout
ENHANCED_PROCESSING_ENABLED = os.getenv('ENHANCED_PROCESSING_ENABLED', 'False').lower() == 'true'

# In document processing
if ENHANCED_PROCESSING_ENABLED:
    # Use Document_Extraction pipeline
    result = enhanced_process_document.delay(file_path, file_id)
else:
    # Use existing processing
    result = process_document.delay(document_id)
```

### 2. **Staged Rollout Plan**

#### Phase 1: Infrastructure Setup (Week 1)
- [ ] Install Document_Extraction dependencies
- [ ] Update database schema with new fields
- [ ] Add feature flags to configuration
- [ ] Create integration tests

#### Phase 2: Basic Integration (Week 2)
- [ ] Integrate file type detection
- [ ] Add quality assessment
- [ ] Update file validator
- [ ] Test with PDF files only

#### Phase 3: Enhanced Processing (Week 3)
- [ ] Integrate text processor for Office documents
- [ ] Add image processor for OCR
- [ ] Implement language detection
- [ ] Test with mixed file types

#### Phase 4: Full Integration (Week 4)
- [ ] Integrate CAD processor
- [ ] Add enhancement capabilities
- [ ] Implement human review workflow
- [ ] Full system testing

#### Phase 5: Production Rollout (Week 5)
- [ ] Enable feature flag for staging
- [ ] Monitor performance and quality
- [ ] Gradual rollout to production
- [ ] Monitor and optimize

### 3. **Backward Compatibility**
- Maintain existing API endpoints
- Keep current processing as fallback
- Gradual migration of existing documents
- Comprehensive logging and monitoring

### 4. **Testing Strategy**
```python
# Add comprehensive tests
# tests/integration/test_document_extraction_integration.py
# tests/unit/test_enhanced_processing.py
# tests/e2e/test_full_pipeline.py
```

---

## Next Steps

### 1. **Immediate Actions**
1. **Create integration branch**: `git checkout -b feature/document-extraction-integration`
2. **Copy Document_Extraction module**: Move to `services/document_extraction/`
3. **Update dependencies**: Add new packages to `requirements.txt`
4. **Database migration**: Add new fields to document model

### 2. **Development Tasks**
1. **Create integration stubs** in `services/processing/`
2. **Update API endpoints** in `gateway/routes/`
3. **Add test coverage** in `tests/`
4. **Update configuration** in `config/`

### 3. **Deployment Tasks**
1. **Update Docker configuration** for new dependencies
2. **Add environment variables** for Document_Extraction config
3. **Update startup scripts** to include new workers
4. **Create monitoring dashboards** for enhanced processing

### 4. **Monitoring & Maintenance**
1. **Add metrics** for enhanced processing performance
2. **Create alerts** for processing failures
3. **Implement health checks** for new components
4. **Document operational procedures**

---

## Expected Benefits

### **Enhanced Capabilities**
- **Multi-format support**: PDF, Office, Images, CAD files
- **OCR processing**: Malayalam and English text extraction
- **Quality assessment**: Intelligent routing based on file quality
- **Language detection**: Automatic language identification
- **Image enhancement**: Preprocessing for better OCR results

### **Improved Performance**
- **Intelligent routing**: Process files based on quality and type
- **Parallel processing**: Multiple workers for different file types
- **Caching**: Reuse processing results for similar files
- **Monitoring**: Real-time processing status and metrics

### **Better User Experience**
- **Real-time updates**: WebSocket notifications for processing status
- **Quality feedback**: Users know if files need enhancement
- **Language support**: Automatic Malayalam/English detection
- **Error handling**: Clear error messages and recovery options

---

## Risk Mitigation

### **Technical Risks**
- **Dependency conflicts**: Test all new packages thoroughly
- **Performance impact**: Monitor processing times and resource usage
- **Memory usage**: Implement proper cleanup and resource management
- **Error handling**: Comprehensive error recovery and fallback mechanisms

### **Operational Risks**
- **Data migration**: Careful migration of existing documents
- **Service disruption**: Gradual rollout with rollback capability
- **Monitoring**: Enhanced monitoring and alerting for new components
- **Documentation**: Comprehensive documentation for new features

### **Business Risks**
- **User adoption**: Clear communication about new capabilities
- **Training**: User training for new features and workflows
- **Support**: Enhanced support for new processing capabilities
- **Compliance**: Ensure new processing meets regulatory requirements

---

## Conclusion

The integration of `@Document_Extraction` into the existing KMRL backend will significantly enhance document processing capabilities while maintaining system stability and backward compatibility. The phased approach ensures minimal disruption while providing maximum benefit from the advanced processing pipeline.

**Key Success Factors:**
- Gradual rollout with feature flags
- Comprehensive testing at each phase
- Monitoring and performance optimization
- User training and documentation
- Robust error handling and recovery

**Expected Timeline:** 5 weeks for full integration
**Resource Requirements:** 2-3 developers, 1 DevOps engineer
**Risk Level:** Medium (mitigated by phased approach)
**Business Impact:** High (significant improvement in document processing capabilities)
