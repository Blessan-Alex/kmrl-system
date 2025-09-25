"""
File type detection utilities
"""
import magic
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from loguru import logger

from config import SUPPORTED_EXTENSIONS, FILE_TYPE_PRIORITIES
from document_processor.models import FileType


class FileTypeDetector:
    """Detects file types using multiple methods"""
    
    def __init__(self):
        self.magic = magic.Magic(mime=True)
        self.magic_file = magic.Magic()
    
    def detect_file_type(self, file_path: str) -> Tuple[FileType, str, float]:
        """
        Detect file type using multiple methods
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (file_type, mime_type, confidence)
        """
        try:
            file_path = Path(file_path)
            
            # Method 1: Extension-based detection
            ext_type, ext_confidence = self._detect_by_extension(file_path)
            
            # Method 2: MIME type detection
            mime_type, mime_confidence = self._detect_by_mime(file_path)
            
            # Method 3: Magic number detection
            magic_type, magic_confidence = self._detect_by_magic(file_path)
            
            # Combine results with weighted confidence
            final_type, final_confidence = self._combine_detection_results(
                ext_type, ext_confidence,
                mime_type, mime_confidence,
                magic_type, magic_confidence
            )
            
            logger.info(f"File type detection for {file_path.name}: {final_type} (confidence: {final_confidence:.2f})")
            
            return final_type, mime_type, final_confidence
            
        except Exception as e:
            logger.error(f"Error detecting file type for {file_path}: {str(e)}")
            return FileType.UNKNOWN, "application/octet-stream", 0.0
    
    def _detect_by_extension(self, file_path: Path) -> Tuple[FileType, float]:
        """Detect file type by extension"""
        extension = file_path.suffix.lower()
        
        for file_type, extensions in SUPPORTED_EXTENSIONS.items():
            if extension in extensions:
                return FileType(file_type), 0.8  # High confidence for known extensions
        
        return FileType.UNKNOWN, 0.0
    
    def _detect_by_mime(self, file_path: Path) -> Tuple[str, float]:
        """Detect MIME type using python-magic"""
        try:
            mime_type = self.magic.from_file(str(file_path))
            confidence = 0.9 if mime_type != "application/octet-stream" else 0.3
            return mime_type, confidence
        except Exception as e:
            logger.warning(f"MIME detection failed for {file_path}: {str(e)}")
            return "application/octet-stream", 0.0
    
    def _detect_by_magic(self, file_path: Path) -> Tuple[FileType, float]:
        """Detect file type using magic numbers"""
        try:
            magic_info = self.magic_file.from_file(str(file_path))
            mime_type = self.magic.from_file(str(file_path))
            
            # Map MIME types to our file types
            mime_to_type = {
                'application/pdf': FileType.PDF,
                'image/jpeg': FileType.IMAGE,
                'image/png': FileType.IMAGE,
                'image/gif': FileType.IMAGE,
                'image/bmp': FileType.IMAGE,
                'image/tiff': FileType.IMAGE,
                'image/webp': FileType.IMAGE,
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileType.OFFICE,
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': FileType.OFFICE,
                'application/vnd.openxmlformats-officedocument.presentationml.presentation': FileType.OFFICE,
                'application/msword': FileType.OFFICE,
                'application/vnd.ms-excel': FileType.OFFICE,
                'application/vnd.ms-powerpoint': FileType.OFFICE,
                'text/plain': FileType.TEXT,
                'text/html': FileType.TEXT,
                'text/markdown': FileType.TEXT,
                'application/json': FileType.TEXT,
                'text/csv': FileType.TEXT,
                'application/xml': FileType.TEXT,
                'text/xml': FileType.TEXT,
            }
            
            file_type = mime_to_type.get(mime_type, FileType.UNKNOWN)
            confidence = 0.9 if file_type != FileType.UNKNOWN else 0.1
            
            return file_type, confidence
            
        except Exception as e:
            logger.warning(f"Magic detection failed for {file_path}: {str(e)}")
            return FileType.UNKNOWN, 0.0
    
    def _combine_detection_results(self, ext_type: FileType, ext_conf: float,
                                 mime_type: str, mime_conf: float,
                                 magic_type: FileType, magic_conf: float) -> Tuple[FileType, float]:
        """Combine detection results with weighted confidence"""
        
        # Weight the different detection methods
        weights = {'extension': 0.4, 'mime': 0.3, 'magic': 0.3}
        
        # Collect votes for each file type
        votes = {}
        
        # Extension vote
        votes[ext_type] = votes.get(ext_type, 0) + ext_conf * weights['extension']
        
        # MIME type vote (map to our file types)
        mime_to_type = {
            'application/pdf': FileType.PDF,
            'image/': FileType.IMAGE,
            'text/': FileType.TEXT,
            'application/vnd.openxmlformats': FileType.OFFICE,
            'application/msword': FileType.OFFICE,
            'application/vnd.ms-': FileType.OFFICE,
        }
        
        mime_file_type = FileType.UNKNOWN
        for mime_prefix, file_type in mime_to_type.items():
            if mime_type.startswith(mime_prefix):
                mime_file_type = file_type
                break
        
        votes[mime_file_type] = votes.get(mime_file_type, 0) + mime_conf * weights['mime']
        
        # Magic vote
        votes[magic_type] = votes.get(magic_type, 0) + magic_conf * weights['magic']
        
        # Find the file type with highest confidence
        if not votes:
            return FileType.UNKNOWN, 0.0
        
        best_type = max(votes.keys(), key=lambda k: votes[k])
        best_confidence = votes[best_type]
        
        # Apply priority ordering for ties
        if best_confidence < 0.5:  # Low confidence, use priority order
            for priority_type in FILE_TYPE_PRIORITIES:
                if FileType(priority_type) in votes and votes[FileType(priority_type)] > 0:
                    return FileType(priority_type), votes[FileType(priority_type)]
        
        return best_type, min(best_confidence, 1.0)
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if file type is supported"""
        file_type, _, confidence = self.detect_file_type(file_path)
        return file_type != FileType.UNKNOWN and confidence > 0.3
    
    def get_file_category(self, file_type: FileType) -> str:
        """Get processing category for file type"""
        category_map = {
            FileType.CAD: "technical_drawing",
            FileType.IMAGE: "image",
            FileType.PDF: "pdf",
            FileType.OFFICE: "office",
            FileType.TEXT: "text",
            FileType.UNKNOWN: "unknown"
        }
        return category_map.get(file_type, "unknown")
