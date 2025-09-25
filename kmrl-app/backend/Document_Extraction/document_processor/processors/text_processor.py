"""
Text document processor for office documents and text files
"""
import time
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False
    logger.warning("MarkItDown not available. Install with: pip install markitdown")

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from document_processor.models import FileType, ProcessingResult
from document_processor.processors.base_processor import BaseProcessor
from document_processor.utils.language_detector import LanguageDetector
from config import TESSERACT_LANGUAGES, TESSERACT_CMD

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class TextProcessor(BaseProcessor):
    """Processor for text documents, office documents, and PDFs"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [FileType.OFFICE, FileType.TEXT, FileType.PDF]
        self.markitdown = MarkItDown() if MARKITDOWN_AVAILABLE else None
        self.language_detector = LanguageDetector()
    
    def can_process(self, file_type: FileType) -> bool:
        """Check if processor can handle file type"""
        return file_type in self.supported_types
    
    def process(self, file_path: str, file_type: FileType, **kwargs) -> ProcessingResult:
        """Process text document"""
        start_time = time.time()
        file_id = kwargs.get('file_id', Path(file_path).stem)
        
        try:
            if not self.validate_file(file_path):
                return self.create_error_result(
                    file_id, f"Invalid file: {file_path}", 
                    self.get_processing_time(start_time, time.time())
                )
            
            # Route to appropriate processor based on file type
            if file_type == FileType.OFFICE:
                result = self._process_office_document(file_path, file_id, start_time)
            elif file_type == FileType.TEXT:
                result = self._process_text_file(file_path, file_id, start_time)
            elif file_type == FileType.PDF:
                result = self._process_pdf_document(file_path, file_id, start_time)
            else:
                return self.create_error_result(
                    file_id, f"Unsupported file type: {file_type}",
                    self.get_processing_time(start_time, time.time())
                )
            
            # Detect language if text was extracted
            if result.success and result.extracted_text:
                language = self.language_detector.detect_language(result.extracted_text)
                result.metadata['language'] = language
                
                # If Malayalam, add translation flag
                if language == 'ml':
                    result.metadata['needs_translation'] = True
                    result.warnings.append("Document contains Malayalam text - translation required")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing text document {file_path}: {str(e)}")
            return self.create_error_result(
                file_id, f"Processing failed: {str(e)}",
                self.get_processing_time(start_time, time.time())
            )
    
    def _process_office_document(self, file_path: str, file_id: str, start_time: float) -> ProcessingResult:
        """Process office documents (Word, Excel, PowerPoint)"""
        try:
            if self.markitdown:
                # Use MarkItDown for comprehensive office document processing
                result = self.markitdown.convert(file_path)
                extracted_text = result.text_content
                metadata = {
                    'processor': 'markitdown',
                    'file_type': 'office',
                    'conversion_method': 'markitdown'
                }
            else:
                # Fallback to basic processing
                extracted_text, metadata = self._process_office_fallback(file_path)
            
            processing_time = self.get_processing_time(start_time, time.time())
            
            return self.create_success_result(
                file_id, extracted_text, metadata, processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing office document {file_path}: {str(e)}")
            return self.create_error_result(
                file_id, f"Office document processing failed: {str(e)}",
                self.get_processing_time(start_time, time.time())
            )
    
    def _process_office_fallback(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Fallback office document processing"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        try:
            if extension == '.docx' and DOCX_AVAILABLE:
                # Process Word document
                doc = DocxDocument(file_path)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                metadata = {'processor': 'python-docx', 'file_type': 'docx'}
                
            elif extension in ['.xlsx', '.xls'] and PANDAS_AVAILABLE:
                # Process Excel document
                df = pd.read_excel(file_path, sheet_name=None)
                text_parts = []
                for sheet_name, sheet_df in df.items():
                    text_parts.append(f"Sheet: {sheet_name}")
                    text_parts.append(sheet_df.to_string())
                text = '\n'.join(text_parts)
                metadata = {'processor': 'pandas', 'file_type': 'excel'}
                
            else:
                # Generic text extraction
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                metadata = {'processor': 'text_fallback', 'file_type': extension[1:]}
            
            return text, metadata
            
        except Exception as e:
            logger.warning(f"Fallback processing failed for {file_path}: {str(e)}")
            return "", {'processor': 'failed', 'error': str(e)}
    
    def _process_text_file(self, file_path: str, file_id: str, start_time: float) -> ProcessingResult:
        """Process plain text files"""
        try:
            file_path = Path(file_path)
            
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            text = ""
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if not text:
                return self.create_error_result(
                    file_id, "Could not decode text file with any supported encoding",
                    self.get_processing_time(start_time, time.time())
                )
            
            metadata = {
                'processor': 'text_file',
                'file_type': file_path.suffix[1:],
                'encoding': used_encoding,
                'file_size': file_path.stat().st_size
            }
            
            processing_time = self.get_processing_time(start_time, time.time())
            
            return self.create_success_result(
                file_id, text, metadata, processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            return self.create_error_result(
                file_id, f"Text file processing failed: {str(e)}",
                self.get_processing_time(start_time, time.time())
            )
    
    def _process_pdf_document(self, file_path: str, file_id: str, start_time: float) -> ProcessingResult:
        """Process PDF documents"""
        try:
            if self.markitdown:
                # Use MarkItDown for PDF processing
                result = self.markitdown.convert(file_path)
                extracted_text = result.text_content or ""
                metadata = {
                    'processor': 'markitdown',
                    'file_type': 'pdf',
                    'conversion_method': 'markitdown'
                }
            else:
                # Fallback PDF processing
                extracted_text, metadata = self._process_pdf_fallback(file_path)

            # Always attempt mixed-content OCR extraction to capture image text (e.g., Malayalam)
            if PDFPLUMBER_AVAILABLE and OCR_AVAILABLE:
                ocr_text, ocr_meta = self._extract_pdf_images_with_ocr(file_path)
                if ocr_text and ocr_text.strip():
                    # Combine MarkItDown/PDF text with OCR text
                    combined = (extracted_text.strip() + "\n\n" + ocr_text.strip()).strip() if extracted_text else ocr_text.strip()
                    extracted_text = combined
                    metadata.update({'mixed_content_ocr': True, **ocr_meta})
            
            processing_time = self.get_processing_time(start_time, time.time())
            
            return self.create_success_result(
                file_id, extracted_text, metadata, processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return self.create_error_result(
                file_id, f"PDF processing failed: {str(e)}",
                self.get_processing_time(start_time, time.time())
            )
    
    def _process_pdf_fallback(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Fallback PDF processing using PyPDF2"""
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_parts.append(f"Page {page_num + 1}:\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                        continue
                
                text = '\n\n'.join(text_parts)
                metadata = {
                    'processor': 'PyPDF2',
                    'file_type': 'pdf',
                    'pages': len(pdf_reader.pages)
                }
                
                return text, metadata
                
        except Exception as e:
            logger.warning(f"PDF fallback processing failed for {file_path}: {str(e)}")
            return "", {'processor': 'failed', 'error': str(e)}

    def _extract_pdf_images_with_ocr(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract images from PDF pages and OCR them; return combined text and metadata."""
        if not (PDFPLUMBER_AVAILABLE and OCR_AVAILABLE):
            return "", {'ocr_attempted': False}

        ocr_text_parts = []
        pages_ocrd = 0
        try:
            # Ensure tesseract binary is configured
            try:
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
            except Exception:
                pass
            custom_config = f"--oem 3 --psm 6 -l {TESSERACT_LANGUAGES}"
            mal_only_config = "--oem 3 --psm 6 -l mal"
            with pdfplumber.open(file_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    try:
                        img = page.to_image(resolution=300).original  # PIL.Image
                        # Run OCR with default config
                        text_default = pytesseract.image_to_string(img, config=custom_config) or ""
                        # Run Malayalam-only OCR
                        text_mal = pytesseract.image_to_string(img, config=mal_only_config) or ""

                        # Decide which text to keep: prefer Malayalam-dominant
                        def _ml_ratio(s: str) -> float:
                            total = sum(1 for c in s if c.isalpha())
                            ml = sum(1 for c in s if '\u0D00' <= c <= '\u0D7F')
                            return (ml / total) if total else 0.0

                        ml_ratio_default = _ml_ratio(text_default)
                        ml_ratio_mal = _ml_ratio(text_mal)

                        chosen = text_mal if (ml_ratio_mal >= max(0.3, ml_ratio_default) and text_mal.strip()) else text_default

                        # Filter lines to reduce non-Malayalam noise when Malayalam dominates
                        if _ml_ratio(chosen) >= 0.3:
                            lines = []
                            for line in chosen.splitlines():
                                if _ml_ratio(line) >= 0.2 or (not line.strip()):
                                    lines.append(line)
                            chosen = "\n".join(lines)

                        if chosen and chosen.strip():
                            ocr_text_parts.append(f"--- Page {idx + 1} (OCR) ---\n{chosen.strip()}")
                            pages_ocrd += 1
                    except Exception as e:
                        logger.warning(f"OCR failed on PDF page {idx+1}: {e}")
                        continue
        except Exception as e:
            logger.warning(f"pdfplumber failed to open {file_path}: {e}")
            return "", {'ocr_attempted': True, 'pages_ocrd': 0}

        combined = "\n\n".join(ocr_text_parts)
        meta = {
            'ocr_attempted': True,
            'pages_ocrd': pages_ocrd,
            'ocr_text_chars': len(combined)
        }
        return combined, meta
