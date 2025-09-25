# KMRL Document Processing System - Phase 2

This is the implementation of Phase 2: Document Processing for the KMRL Document Processing System. The system processes documents from a queue, detects file types, assesses quality, and routes them to appropriate processors.

## Features

### Core Processing Pipeline
- **File Type Detection**: Multi-method detection using extensions, MIME types, and magic numbers
- **Quality Assessment**: Comprehensive quality checks including file size, image quality, and text density
- **Intelligent Routing**: Routes documents to specialized processors based on type and quality
- **Async Processing**: Celery-based task queue for scalable document processing

### Supported File Types
- **Technical Drawings**: `.dwg`, `.dxf`, `.step`, `.stp`, `.iges`, `.igs`
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`
- **PDFs**: Text, image, and mixed content PDFs
- **Office Documents**: `.docx`, `.doc`, `.xlsx`, `.xls`, `.pptx`, `.ppt`
- **Text Files**: `.txt`, `.md`, `.rst`, `.html`, `.xml`, `.json`, `.csv`

### Specialized Processors
- **Text Processor**: Handles office documents and PDFs using MarkItDown
- **Image Processor**: OCR processing with Tesseract (Malayalam + English)
- **CAD Processor**: Metadata extraction and placeholder text for technical drawings
- **Quality Assessment**: File size, image quality, and text density analysis

## Installation

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Install System Dependencies**:
```bash
# Install Tesseract OCR
sudo apt-get install tesseract-ocr tesseract-ocr-mal

# Install Redis (for Celery)
sudo apt-get install redis-server
```

3. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Running the Worker

Start the Celery worker to process documents:

```bash
python document_processor/worker.py
```

### Processing Documents

#### Using Celery Tasks (Recommended)
```python
from document_processor.tasks import process_document

# Submit document for processing
task = process_document.delay('path/to/document.pdf', 'file_id_123')

# Get result (blocking)
result = task.get(timeout=30)
print(result)
```

#### Direct Processing
```python
from document_processor.processors.text_processor import TextProcessor

processor = TextProcessor()
result = processor.process('document.pdf', 'pdf', file_id='test_001')
print(result.extracted_text)
```

### Example Usage

Run the example script to see the system in action:

```bash
python example_usage.py
```

## Architecture

### File Type Detection
The system uses a multi-layered approach:
1. **Extension-based**: Fast detection using file extensions
2. **MIME-type**: Using python-magic for MIME type detection
3. **Magic numbers**: Binary signature detection
4. **Weighted combination**: Combines all methods with confidence scoring

### Quality Assessment
Comprehensive quality checks:
- **File size validation**: 50MB limit (configurable)
- **Image quality analysis**: Sharpness, contrast, brightness, noise, resolution
- **Text density assessment**: OCR preprocessing for images, heuristics for documents
- **Decision making**: Process, Enhance, or Reject based on quality scores

### Processing Pipeline
1. **Queue Pickup**: Worker picks task from Redis queue
2. **File Type Detection**: Multi-method detection with confidence scoring
3. **Quality Assessment**: Comprehensive quality analysis
4. **Processor Routing**: Route to appropriate specialized processor
5. **Text Extraction**: Extract text using appropriate method
6. **Language Detection**: Detect language (Malayalam/English)
7. **Result Storage**: Store extracted text and metadata

## Configuration

Key configuration options in `config.py`:

```python
# File processing limits
MAX_FILE_SIZE_MB = 50
IMAGE_QUALITY_THRESHOLD = 0.7
TEXT_DENSITY_THRESHOLD = 0.1

# OCR configuration
TESSERACT_CMD = "/usr/bin/tesseract"
TESSERACT_LANGUAGES = "eng+mal"

# Redis configuration
REDIS_URL = "redis://localhost:6379/0"
```

## API Reference

### FileTypeDetector
```python
detector = FileTypeDetector()
file_type, mime_type, confidence = detector.detect_file_type('document.pdf')
```

### QualityAssessor
```python
assessor = QualityAssessor()
assessment = assessor.assess_quality('document.pdf', 'pdf')
```

### TextProcessor
```python
processor = TextProcessor()
result = processor.process('document.pdf', FileType.PDF, file_id='test')
```

### ImageProcessor
```python
processor = ImageProcessor()
result = processor.process('image.jpg', FileType.IMAGE, file_id='test')
```

### CADProcessor
```python
processor = CADProcessor()
result = processor.process('drawing.dwg', FileType.CAD, file_id='test')
```

## Monitoring and Logging

The system includes comprehensive logging:
- **Console output**: Real-time processing status
- **File logging**: Detailed logs saved to `logs/document_processor.log`
- **Task monitoring**: Celery task status and progress updates

## Error Handling

Robust error handling throughout:
- **File validation**: Checks file existence and readability
- **Graceful degradation**: Fallback methods when primary processing fails
- **Detailed error reporting**: Comprehensive error messages and stack traces
- **Recovery mechanisms**: Automatic retry for transient failures

## Performance Considerations

- **Async processing**: Non-blocking document processing
- **Resource management**: Automatic cleanup of temporary files
- **Memory efficiency**: Streaming processing for large files
- **Concurrent processing**: Multiple workers for parallel processing

## Future Enhancements

- **Translation integration**: Automatic Malayalam to English translation
- **Advanced OCR**: Support for more languages and document types
- **Machine learning**: Quality assessment using ML models
- **Cloud integration**: Support for cloud storage backends
- **Real-time monitoring**: Web dashboard for processing status

## Troubleshooting

### Common Issues

1. **Tesseract not found**: Ensure Tesseract is installed and path is correct
2. **Redis connection failed**: Check Redis server is running
3. **File processing errors**: Check file permissions and format support
4. **Memory issues**: Reduce concurrency or increase system memory

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is part of the KMRL Document Processing System.
# KM
