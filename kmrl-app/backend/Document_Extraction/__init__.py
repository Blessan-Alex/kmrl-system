"""
Document_Extraction Module for KMRL
Comprehensive document processing system with multi-format support
"""

__version__ = "1.0.0"
__author__ = "KMRL Development Team"

# Make key components easily importable (with error handling)
try:
    from .document_processor.tasks import process_document
    from .document_processor.utils.file_detector import FileTypeDetector
    from .document_processor.utils.quality_assessor import QualityAssessor
    
    __all__ = [
        'process_document',
        'FileTypeDetector', 
        'QualityAssessor'
    ]
except ImportError as e:
    # If imports fail, just define the module without the components
    __all__ = []
