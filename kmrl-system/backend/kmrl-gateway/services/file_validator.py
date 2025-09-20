"""
File Validator for KMRL Documents
Validates file types, sizes, and security for KMRL document processing
"""

import magic
from typing import Dict, Any
import structlog
from fastapi import UploadFile

logger = structlog.get_logger()

class FileValidator:
    """File validator for KMRL document types"""
    
    def __init__(self):
        self.max_file_size = 200 * 1024 * 1024  # 200MB
        self.allowed_extensions = [
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
            '.dwg', '.dxf', '.step', '.stp', '.iges', '.igs',
            '.txt', '.md', '.rst', '.html', '.xml', '.json', '.csv'
        ]
        self.blocked_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif']
    
    async def validate_kmrl_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate file for KMRL document processing"""
        try:
            # Check file size
            if file.size > self.max_file_size:
                return {
                    "valid": False,
                    "error": f"File size {file.size} exceeds maximum allowed size of {self.max_file_size} bytes"
                }
            
            # Check file extension
            if file.filename:
                file_ext = '.' + file.filename.split('.')[-1].lower()
                if file_ext in self.blocked_extensions:
                    return {
                        "valid": False,
                        "error": f"File type {file_ext} is not allowed for security reasons"
                    }
                
                if file_ext not in self.allowed_extensions:
                    return {
                        "valid": False,
                        "error": f"File type {file_ext} is not supported. Allowed types: {', '.join(self.allowed_extensions)}"
                    }
            
            # Read file content for MIME type validation
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Validate MIME type
            mime_type = magic.from_buffer(content, mime=True)
            if not self.is_valid_mime_type(mime_type):
                return {
                    "valid": False,
                    "error": f"MIME type {mime_type} is not supported"
                }
            
            return {"valid": True, "mime_type": mime_type}
            
        except Exception as e:
            logger.error("File validation error", error=str(e))
            return {
                "valid": False,
                "error": f"File validation failed: {str(e)}"
            }
    
    def is_valid_mime_type(self, mime_type: str) -> bool:
        """Check if MIME type is valid for KMRL documents"""
        valid_mime_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/tiff',
            'image/webp',
            'text/plain',
            'text/html',
            'text/xml',
            'application/json',
            'text/csv',
            'application/octet-stream'  # For CAD files
        ]
        return mime_type in valid_mime_types
