"""
Document Processor for KMRL
Handles text extraction from various document types
"""

import os
import mimetypes
from typing import Dict, Any, Optional
import structlog
import pytesseract
from PIL import Image
import markitdown
import PyPDF2
import docx
import pandas as pd

logger = structlog.get_logger()

class DocumentProcessor:
    """Document processor for KMRL documents"""
    
    def __init__(self):
        self.tesseract_path = os.getenv('TESSERACT_PATH', '/usr/bin/tesseract')
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
    
    def extract_text(self, file_path: str, content_type: str) -> str:
        """Extract text from document based on content type"""
        try:
            if content_type.startswith('image/'):
                return self._extract_from_image(file_path)
            elif content_type == 'application/pdf':
                return self._extract_from_pdf(file_path)
            elif content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return self._extract_from_word(file_path)
            elif content_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                return self._extract_from_excel(file_path)
            else:
                return self._extract_generic(file_path)
                
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""
    
    def _extract_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            # Try Malayalam first, then English
            image = Image.open(file_path)
            
            # Malayalam OCR
            malayalam_text = pytesseract.image_to_string(image, lang='mal+eng')
            
            return malayalam_text.strip()
            
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
                
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""
    
    def _extract_from_word(self, file_path: str) -> str:
        """Extract text from Word document"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
            
        except Exception as e:
            logger.error(f"Word extraction failed: {e}")
            return ""
    
    def _extract_from_excel(self, file_path: str) -> str:
        """Extract text from Excel document"""
        try:
            df = pd.read_excel(file_path)
            text = df.to_string()
            return text.strip()
            
        except Exception as e:
            logger.error(f"Excel extraction failed: {e}")
            return ""
    
    def _extract_generic(self, file_path: str) -> str:
        """Generic text extraction using markitdown"""
        try:
            result = markitdown.convert(file_path)
            return result.text_content if hasattr(result, 'text_content') else str(result)
            
        except Exception as e:
            logger.error(f"Generic extraction failed: {e}")
            return ""
    
    def calculate_confidence(self, text_content: str, content_type: str) -> float:
        """Calculate confidence score for extracted text"""
        try:
            if not text_content or len(text_content.strip()) < 10:
                return 0.0
            
            # Base confidence on text length and content type
            base_confidence = 0.5
            
            # Adjust based on text length
            if len(text_content) > 100:
                base_confidence += 0.2
            if len(text_content) > 500:
                base_confidence += 0.2
            
            # Adjust based on content type
            if content_type.startswith('text/'):
                base_confidence += 0.1
            elif content_type == 'application/pdf':
                base_confidence += 0.1
            
            return min(base_confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.0
