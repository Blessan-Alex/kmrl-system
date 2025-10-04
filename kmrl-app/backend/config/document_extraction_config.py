"""
Document_Extraction Integration Configuration
Configuration settings for Document_Extraction integration with KMRL pipeline
"""

import os
from typing import Dict, Any

class DocumentExtractionConfig:
    """Configuration for Document_Extraction integration"""
    
    # Feature flags
    DOCUMENT_EXTRACTION_ENABLED = os.getenv('DOCUMENT_EXTRACTION_ENABLED', 'True').lower() == 'true'
    ENHANCED_PROCESSING_ENABLED = os.getenv('ENHANCED_PROCESSING_ENABLED', 'True').lower() == 'true'
    
    # Document_Extraction specific settings
    TESSERACT_CMD = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')
    TESSERACT_LANGUAGES = os.getenv('TESSERACT_LANGUAGES', 'mal+eng')
    
    # File processing limits
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
    IMAGE_QUALITY_THRESHOLD = float(os.getenv('IMAGE_QUALITY_THRESHOLD', '0.7'))
    TEXT_DENSITY_THRESHOLD = float(os.getenv('TEXT_DENSITY_THRESHOLD', '0.1'))
    
    # Processing timeouts
    PROCESSING_TIMEOUT_SECONDS = int(os.getenv('PROCESSING_TIMEOUT_SECONDS', '300'))
    OCR_TIMEOUT_SECONDS = int(os.getenv('OCR_TIMEOUT_SECONDS', '60'))
    
    # Quality assessment settings
    QUALITY_THRESHOLD_PROCESS = float(os.getenv('QUALITY_THRESHOLD_PROCESS', '0.7'))
    QUALITY_THRESHOLD_ENHANCE = float(os.getenv('QUALITY_THRESHOLD_ENHANCE', '0.4'))
    QUALITY_THRESHOLD_REJECT = float(os.getenv('QUALITY_THRESHOLD_REJECT', '0.2'))
    
    # Language detection settings
    LANGUAGE_DETECTION_ENABLED = os.getenv('LANGUAGE_DETECTION_ENABLED', 'True').lower() == 'true'
    SUPPORTED_LANGUAGES = ['mal', 'eng', 'hin', 'tam', 'tel', 'kan', 'guj', 'mar', 'ben', 'ori', 'pun', 'asm']
    
    # File type support
    SUPPORTED_FILE_TYPES = {
        'pdf': ['pdf'],
        'office': ['docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt'],
        'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp'],
        'cad': ['dwg', 'dxf', 'step', 'stp', 'iges', 'igs'],
        'text': ['txt', 'md', 'rst', 'html', 'xml', 'json', 'csv']
    }
    
    # Processing priorities
    PROCESSING_PRIORITIES = {
        'high': 0,
        'normal': 1,
        'low': 2
    }
    
    # Error handling
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY_SECONDS = int(os.getenv('RETRY_DELAY_SECONDS', '5'))
    
    # Monitoring and logging
    ENABLE_DETAILED_LOGGING = os.getenv('ENABLE_DETAILED_LOGGING', 'True').lower() == 'true'
    LOG_PROCESSING_METRICS = os.getenv('LOG_PROCESSING_METRICS', 'True').lower() == 'true'
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            'document_extraction_enabled': cls.DOCUMENT_EXTRACTION_ENABLED,
            'enhanced_processing_enabled': cls.ENHANCED_PROCESSING_ENABLED,
            'tesseract_cmd': cls.TESSERACT_CMD,
            'tesseract_languages': cls.TESSERACT_LANGUAGES,
            'max_file_size_mb': cls.MAX_FILE_SIZE_MB,
            'image_quality_threshold': cls.IMAGE_QUALITY_THRESHOLD,
            'text_density_threshold': cls.TEXT_DENSITY_THRESHOLD,
            'processing_timeout_seconds': cls.PROCESSING_TIMEOUT_SECONDS,
            'ocr_timeout_seconds': cls.OCR_TIMEOUT_SECONDS,
            'quality_threshold_process': cls.QUALITY_THRESHOLD_PROCESS,
            'quality_threshold_enhance': cls.QUALITY_THRESHOLD_ENHANCE,
            'quality_threshold_reject': cls.QUALITY_THRESHOLD_REJECT,
            'language_detection_enabled': cls.LANGUAGE_DETECTION_ENABLED,
            'supported_languages': cls.SUPPORTED_LANGUAGES,
            'supported_file_types': cls.SUPPORTED_FILE_TYPES,
            'processing_priorities': cls.PROCESSING_PRIORITIES,
            'max_retries': cls.MAX_RETRIES,
            'retry_delay_seconds': cls.RETRY_DELAY_SECONDS,
            'enable_detailed_logging': cls.ENABLE_DETAILED_LOGGING,
            'log_processing_metrics': cls.LOG_PROCESSING_METRICS
        }
    
    @classmethod
    def is_file_type_supported(cls, file_extension: str) -> bool:
        """Check if file type is supported by Document_Extraction"""
        file_extension = file_extension.lower().lstrip('.')
        for category, extensions in cls.SUPPORTED_FILE_TYPES.items():
            if file_extension in extensions:
                return True
        return False
    
    @classmethod
    def get_file_category(cls, file_extension: str) -> str:
        """Get file category for given extension"""
        file_extension = file_extension.lower().lstrip('.')
        for category, extensions in cls.SUPPORTED_FILE_TYPES.items():
            if file_extension in extensions:
                return category
        return 'unknown'
