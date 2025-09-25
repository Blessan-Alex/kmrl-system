"""
Enhanced File Validator for KMRL Documents
Comprehensive file validation with security scanning and quality assessment
"""

import os
import magic
import hashlib
from typing import Dict, Any, List, Optional
import structlog
from fastapi import UploadFile
from PIL import Image
import json

logger = structlog.get_logger()

class FileValidator:
    """Enhanced file validator for KMRL document types"""
    
    def __init__(self):
        self.max_file_size = 200 * 1024 * 1024  # 200MB
        self.max_image_size = 50 * 1024 * 1024  # 50MB for images
        self.allowed_extensions = [
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
            '.dwg', '.dxf', '.step', '.stp', '.iges', '.igs',
            '.txt', '.md', '.rst', '.html', '.xml', '.json', '.csv'
        ]
        self.blocked_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.sh', '.ps1']
        self.suspicious_patterns = [
            b'<script', b'javascript:', b'data:text/html', b'eval(', b'exec(',
            b'../', b'..\\', b'cmd.exe', b'powershell', b'bash'
        ]
    
    def validate_file(self, file_path: str) -> bool:
        """Basic file validation for general use"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error("File does not exist", file_path=file_path)
                return False
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error("File size exceeds limit", 
                           file_size=file_size, 
                           max_size=self.max_file_size)
                return False
            
            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in self.blocked_extensions:
                logger.error("File type blocked for security", extension=file_ext)
                return False
            
            if file_ext not in self.allowed_extensions:
                logger.error("File type not supported", 
                           extension=file_ext,
                           allowed_types=self.allowed_extensions)
                return False
            
            # Basic MIME type validation
            try:
                mime_type = magic.from_file(file_path, mime=True)
                if not self.is_valid_mime_type(mime_type):
                    logger.error("Invalid MIME type", mime_type=mime_type)
                    return False
            except Exception as e:
                logger.warning("Could not validate MIME type", error=str(e))
            
            logger.info("File validation passed", file_path=file_path)
            return True
            
        except Exception as e:
            logger.error("File validation failed", error=str(e), file_path=file_path)
            return False
    
    async def validate_kmrl_file(self, file: UploadFile) -> Dict[str, Any]:
        """Enhanced validation for KMRL document processing"""
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
            
            # Read file content for comprehensive validation
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Security scan
            security_result = await self._security_scan(content)
            if not security_result["safe"]:
                return {
                    "valid": False,
                    "error": f"Security scan failed: {security_result['reason']}"
                }
            
            # Validate MIME type
            mime_type = magic.from_buffer(content, mime=True)
            if not self.is_valid_mime_type(mime_type):
                return {
                    "valid": False,
                    "error": f"MIME type {mime_type} is not supported"
                }
            
            # Quality assessment
            quality_result = await self._assess_file_quality(content, mime_type, file.filename)
            
            # Generate file hash
            file_hash = hashlib.sha256(content).hexdigest()
            
            return {
                "valid": True,
                "mime_type": mime_type,
                "file_hash": file_hash,
                "quality_score": quality_result["score"],
                "quality_issues": quality_result["issues"],
                "processing_recommendations": quality_result["recommendations"]
            }
            
        except Exception as e:
            logger.error("File validation error", error=str(e))
            return {
                "valid": False,
                "error": f"File validation failed: {str(e)}"
            }
    
    async def _security_scan(self, content: bytes) -> Dict[str, Any]:
        """Scan file content for security threats"""
        try:
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                if pattern in content:
                    return {
                        "safe": False,
                        "reason": f"Suspicious pattern detected: {pattern.decode('utf-8', errors='ignore')}"
                    }
            
            # Check for embedded executables
            if b'MZ' in content[:2]:  # PE executable signature
                return {
                    "safe": False,
                    "reason": "Executable file detected"
                }
            
            # Check for macro content in Office documents
            if b'VBA' in content or b'macro' in content.lower():
                return {
                    "safe": False,
                    "reason": "Macro content detected"
                }
            
            return {"safe": True, "reason": "No security threats detected"}
            
        except Exception as e:
            logger.error(f"Security scan error: {e}")
            return {"safe": False, "reason": f"Security scan failed: {str(e)}"}
    
    async def _assess_file_quality(self, content: bytes, mime_type: str, filename: str) -> Dict[str, Any]:
        """Assess file quality and provide processing recommendations"""
        try:
            quality_score = 1.0
            issues = []
            recommendations = []
            
            # Check file size appropriateness
            if len(content) < 1024:  # Less than 1KB
                quality_score -= 0.2
                issues.append("File size very small")
                recommendations.append("Verify file content")
            
            # Image quality assessment
            if mime_type.startswith('image/'):
                try:
                    image = Image.open(io.BytesIO(content))
                    width, height = image.size
                    
                    if width < 100 or height < 100:
                        quality_score -= 0.3
                        issues.append("Image resolution too low")
                        recommendations.append("Consider image enhancement")
                    
                    if width > 4000 or height > 4000:
                        quality_score -= 0.1
                        issues.append("Image resolution very high")
                        recommendations.append("Consider image compression")
                    
                except Exception:
                    quality_score -= 0.5
                    issues.append("Image format corrupted")
                    recommendations.append("File may need manual review")
            
            # PDF quality assessment
            elif mime_type == 'application/pdf':
                if b'%PDF' not in content[:10]:
                    quality_score -= 0.5
                    issues.append("Invalid PDF header")
                    recommendations.append("File may be corrupted")
            
            # Text file assessment
            elif mime_type.startswith('text/'):
                try:
                    text_content = content.decode('utf-8')
                    if len(text_content.strip()) < 10:
                        quality_score -= 0.3
                        issues.append("Text content very short")
                        recommendations.append("Verify text content")
                except UnicodeDecodeError:
                    quality_score -= 0.4
                    issues.append("Text encoding issues")
                    recommendations.append("File may need encoding conversion")
            
            # Office document assessment
            elif mime_type.startswith('application/vnd.'):
                if len(content) < 1024:
                    quality_score -= 0.2
                    issues.append("Office document size very small")
                    recommendations.append("Verify document content")
            
            return {
                "score": max(0.0, min(1.0, quality_score)),
                "issues": issues,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Quality assessment error: {e}")
            return {
                "score": 0.5,
                "issues": ["Quality assessment failed"],
                "recommendations": ["Manual review recommended"]
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
    
    async def get_file_statistics(self) -> Dict[str, Any]:
        """Get file validation statistics"""
        try:
            # This would typically query a database for statistics
            # For now, return placeholder data
            return {
                "total_validated": 0,
                "validation_success_rate": 0.0,
                "common_issues": [],
                "security_threats_blocked": 0
            }
        except Exception as e:
            logger.error(f"Failed to get file statistics: {e}")
            return {"error": str(e)}
