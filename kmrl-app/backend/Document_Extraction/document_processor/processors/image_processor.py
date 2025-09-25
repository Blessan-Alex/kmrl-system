"""
Image document processor with OCR capabilities
"""
import time
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract not available. Install with: pip install pytesseract")

from config import TESSERACT_CMD, TESSERACT_LANGUAGES
from document_processor.models import FileType, ProcessingResult, OCRResult
from document_processor.processors.base_processor import BaseProcessor
from document_processor.utils.language_detector import LanguageDetector


class ImageProcessor(BaseProcessor):
    """Processor for image documents with OCR capabilities"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [FileType.IMAGE]
        self.language_detector = LanguageDetector()
        
        if TESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    
    def can_process(self, file_type: FileType) -> bool:
        """Check if processor can handle file type"""
        return file_type in self.supported_types
    
    def process(self, file_path: str, file_type: FileType, **kwargs) -> ProcessingResult:
        """Process image document with OCR"""
        start_time = time.time()
        file_id = kwargs.get('file_id', Path(file_path).stem)
        output_dir = kwargs.get('output_dir')
        
        try:
            if not self.validate_file(file_path):
                return self.create_error_result(
                    file_id, f"Invalid file: {file_path}",
                    self.get_processing_time(start_time, time.time())
                )
            
            # Preprocess image for better OCR
            processed_image_path = self._preprocess_image(file_path, output_dir)
            
            # Perform OCR
            ocr_result = self._perform_ocr(processed_image_path or file_path)
            
            # Detect language
            language = self.language_detector.detect_language(ocr_result.text)
            
            # Prepare metadata
            metadata = {
                'processor': 'image_ocr',
                'file_type': 'image',
                'ocr_confidence': ocr_result.confidence,
                'language': language,
                'needs_translation': self.language_detector.needs_translation(language),
                'image_dimensions': self._get_image_dimensions(file_path),
                'preprocessing_applied': processed_image_path is not None,
                'enhanced_image_path': processed_image_path
            }
            
            processing_time = self.get_processing_time(start_time, time.time())
            
            # Don't clean up enhanced images - keep them in output directory
            
            return self.create_success_result(
                file_id, ocr_result.text, metadata, processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {str(e)}")
            return self.create_error_result(
                file_id, f"Image processing failed: {str(e)}",
                self.get_processing_time(start_time, time.time())
            )
    
    def _preprocess_image(self, file_path: str, output_dir: Optional[str] = None) -> Optional[str]:
        """Preprocess image for better OCR results"""
        try:
            # Load image
            image = cv2.imread(file_path)
            if image is None:
                logger.warning(f"Could not load image: {file_path}")
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply preprocessing techniques
            processed = self._enhance_image_for_ocr(gray)
            
            # Save processed image in output directory if provided
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                filename = Path(file_path).stem + '.enhanced.jpg'
                processed_path = str(output_path / filename)
            else:
                processed_path = str(Path(file_path).with_suffix('.processed.jpg'))
            
            cv2.imwrite(processed_path, processed)
            
            logger.info(f"Image preprocessed and saved to: {processed_path}")
            return processed_path
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed for {file_path}: {str(e)}")
            return None
    
    def _enhance_image_for_ocr(self, gray_image: np.ndarray) -> np.ndarray:
        """Apply image enhancement techniques for better OCR"""
        try:
            # 1. Noise reduction
            denoised = cv2.medianBlur(gray_image, 3)
            
            # 2. Contrast enhancement using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # 3. Sharpening
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            # 4. Adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            return thresh
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {str(e)}")
            return gray_image
    
    def _perform_ocr(self, image_path: str) -> OCRResult:
        """Perform OCR on image"""
        if not TESSERACT_AVAILABLE:
            return OCRResult(
                text="",
                confidence=0.0,
                language="unknown",
                processing_time=0.0
            )
        
        try:
            start_time = time.time()
            
            # Load image with PIL
            image = Image.open(image_path)
            
            # Configure Tesseract for multiple languages
            custom_config = f'--oem 3 --psm 6 -l {TESSERACT_LANGUAGES}'
            
            # Perform OCR
            text = pytesseract.image_to_string(image, config=custom_config)
            
            # Get confidence data
            data = pytesseract.image_to_data(image, config=custom_config, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Get bounding boxes
            bounding_boxes = []
            for i, conf in enumerate(data['conf']):
                if int(conf) > 0:
                    bbox = {
                        'text': data['text'][i],
                        'confidence': int(conf),
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    }
                    bounding_boxes.append(bbox)
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence / 100.0,  # Convert to 0-1 scale
                language="mixed",  # Will be detected separately
                processing_time=processing_time,
                bounding_boxes=bounding_boxes
            )
            
        except Exception as e:
            logger.error(f"OCR processing failed for {image_path}: {str(e)}")
            return OCRResult(
                text="",
                confidence=0.0,
                language="unknown",
                processing_time=0.0
            )
    
    def _get_image_dimensions(self, file_path: str) -> Dict[str, int]:
        """Get image dimensions"""
        try:
            image = cv2.imread(file_path)
            if image is not None:
                height, width = image.shape[:2]
                return {'width': width, 'height': height}
            return {'width': 0, 'height': 0}
        except Exception:
            return {'width': 0, 'height': 0}
    
    def enhance_image(self, file_path: str, output_path: str) -> Dict[str, Any]:
        """
        Enhance image quality for better processing
        
        Args:
            file_path: Input image path
            output_path: Enhanced image output path
            
        Returns:
            Enhancement results
        """
        try:
            start_time = time.time()
            
            # Load image
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError(f"Could not load image: {file_path}")
            
            # Apply enhancement techniques
            enhanced = self._apply_image_enhancement(image)
            
            # Save enhanced image
            cv2.imwrite(output_path, enhanced)
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'enhanced_image_path': output_path,
                'processing_time': processing_time,
                'enhancement_applied': [
                    'denoising',
                    'contrast_enhancement',
                    'sharpening',
                    'adaptive_thresholding'
                ]
            }
            
        except Exception as e:
            logger.error(f"Image enhancement failed for {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': 0.0
            }
    
    def _apply_image_enhancement(self, image: np.ndarray) -> np.ndarray:
        """Apply comprehensive image enhancement"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 1. Denoising
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # 2. Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # 3. Sharpening
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            # 4. Gamma correction
            gamma = 1.2
            gamma_corrected = np.power(sharpened / 255.0, gamma) * 255.0
            gamma_corrected = np.uint8(gamma_corrected)
            
            return gamma_corrected
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {str(e)}")
            return image
