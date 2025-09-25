"""
Base processor class for document processing
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

from document_processor.models import ProcessingResult, FileType


class BaseProcessor(ABC):
    """Base class for all document processors"""
    
    def __init__(self):
        self.supported_types = []
    
    @abstractmethod
    def process(self, file_path: str, file_type: FileType, **kwargs) -> ProcessingResult:
        """
        Process a document file
        
        Args:
            file_path: Path to the file to process
            file_type: Detected file type
            **kwargs: Additional processing parameters
            
        Returns:
            ProcessingResult with extracted text and metadata
        """
        pass
    
    @abstractmethod
    def can_process(self, file_type: FileType) -> bool:
        """
        Check if this processor can handle the file type
        
        Args:
            file_type: File type to check
            
        Returns:
            True if processor can handle this file type
        """
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate that the file exists and is readable
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is valid
        """
        try:
            path = Path(file_path)
            return path.exists() and path.is_file() and path.stat().st_size > 0
        except Exception as e:
            logger.error(f"File validation failed for {file_path}: {str(e)}")
            return False
    
    def get_processing_time(self, start_time: float, end_time: float) -> float:
        """Calculate processing time in seconds"""
        return end_time - start_time
    
    def create_error_result(self, file_id: str, error_message: str, 
                          processing_time: float = 0.0) -> ProcessingResult:
        """Create a ProcessingResult for error cases"""
        return ProcessingResult(
            file_id=file_id,
            success=False,
            processing_time=processing_time,
            errors=[error_message]
        )
    
    def create_success_result(self, file_id: str, extracted_text: str, 
                            metadata: Dict[str, Any], processing_time: float) -> ProcessingResult:
        """Create a ProcessingResult for successful processing"""
        return ProcessingResult(
            file_id=file_id,
            success=True,
            extracted_text=extracted_text,
            metadata=metadata,
            processing_time=processing_time
        )
