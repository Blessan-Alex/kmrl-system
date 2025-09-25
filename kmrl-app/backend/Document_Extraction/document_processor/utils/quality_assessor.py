"""
Quality assessment utilities for documents
"""
import os
from pathlib import Path
from typing import Optional, List
import cv2
import numpy as np
from PIL import Image, ImageStat
from loguru import logger

from config import MAX_FILE_SIZE_MB, IMAGE_QUALITY_THRESHOLD, TEXT_DENSITY_THRESHOLD
from document_processor.models import QualityAssessment, QualityDecision


class QualityAssessor:
    """Assesses document quality and makes processing decisions"""
    
    def __init__(self):
        self.max_file_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        self.image_quality_threshold = IMAGE_QUALITY_THRESHOLD
        self.text_density_threshold = TEXT_DENSITY_THRESHOLD
    
    def assess_quality(self, file_path: str, file_type: str) -> QualityAssessment:
        """
        Perform comprehensive quality assessment
        
        Args:
            file_path: Path to the file
            file_type: Detected file type
            
        Returns:
            QualityAssessment object with results
        """
        try:
            file_path = Path(file_path)
            
            # Basic file size check
            file_size_valid = self._check_file_size(file_path)
            
            # Initialize assessment
            assessment = QualityAssessment(
                file_size_valid=file_size_valid,
                overall_quality_score=0.0,
                decision=QualityDecision.REJECT
            )
            
            if not file_size_valid:
                assessment.issues.append(f"File size exceeds {MAX_FILE_SIZE_MB}MB limit")
                assessment.recommendations.append("Compress or split the file")
                return assessment
            
            # Type-specific quality checks
            if file_type in ['image', 'pdf']:
                image_quality = self._assess_image_quality(file_path)
                assessment.image_quality_score = image_quality
                
                if image_quality < self.image_quality_threshold:
                    assessment.issues.append(f"Low image quality: {image_quality:.2f}")
                    assessment.recommendations.append("Apply image enhancement")
            
            # Text density check for all document types
            text_density = self._assess_text_density(file_path, file_type)
            assessment.text_density = text_density
            
            if text_density < self.text_density_threshold:
                assessment.issues.append(f"Low text density: {text_density:.2f}")
                assessment.recommendations.append("Check if document contains readable text")
            
            # Calculate overall quality score
            assessment.overall_quality_score = self._calculate_overall_score(
                file_size_valid, assessment.image_quality_score, text_density
            )
            
            # Make processing decision
            assessment.decision = self._make_processing_decision(assessment)
            
            logger.info(f"Quality assessment for {file_path.name}: {assessment.decision} (score: {assessment.overall_quality_score:.2f})")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing quality for {file_path}: {str(e)}")
            return QualityAssessment(
                file_size_valid=False,
                overall_quality_score=0.0,
                decision=QualityDecision.REJECT,
                issues=[f"Quality assessment failed: {str(e)}"]
            )
    
    def _check_file_size(self, file_path: Path) -> bool:
        """Check if file size is within limits"""
        try:
            file_size = file_path.stat().st_size
            return file_size <= self.max_file_size_bytes
        except Exception as e:
            logger.warning(f"Could not check file size for {file_path}: {str(e)}")
            return False
    
    def _assess_image_quality(self, file_path: Path) -> float:
        """Assess image quality using multiple metrics"""
        try:
            # Load image
            image = cv2.imread(str(file_path))
            if image is None:
                return 0.0
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate quality metrics
            metrics = []
            
            # 1. Laplacian variance (sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 1000, 1.0)  # Normalize
            metrics.append(sharpness_score)
            
            # 2. Contrast (standard deviation)
            contrast_score = min(np.std(gray) / 128, 1.0)  # Normalize
            metrics.append(contrast_score)
            
            # 3. Brightness (mean intensity)
            brightness = np.mean(gray)
            brightness_score = 1.0 - abs(brightness - 127) / 127  # Closer to 127 is better
            metrics.append(brightness_score)
            
            # 4. Noise level (using high-frequency content)
            noise_score = self._assess_noise_level(gray)
            metrics.append(noise_score)
            
            # 5. Resolution adequacy
            height, width = gray.shape
            resolution_score = min((height * width) / (1920 * 1080), 1.0)  # Compare to HD
            metrics.append(resolution_score)
            
            # Calculate weighted average
            weights = [0.3, 0.2, 0.2, 0.2, 0.1]  # Sharpness, contrast, brightness, noise, resolution
            overall_quality = sum(w * m for w, m in zip(weights, metrics))
            
            return min(overall_quality, 1.0)
            
        except Exception as e:
            logger.warning(f"Image quality assessment failed for {file_path}: {str(e)}")
            return 0.0
    
    def _assess_noise_level(self, gray_image: np.ndarray) -> float:
        """Assess noise level in grayscale image"""
        try:
            # Use Laplacian to detect edges and noise
            laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
            
            # Calculate noise level as ratio of high-frequency content
            noise_level = np.var(laplacian)
            
            # Normalize (lower noise is better)
            noise_score = max(0, 1.0 - (noise_level / 10000))
            return min(noise_score, 1.0)
            
        except Exception:
            return 0.5  # Default moderate score
    
    def _assess_text_density(self, file_path: Path, file_type: str) -> float:
        """Assess text density in document"""
        try:
            if file_type == 'image':
                return self._assess_image_text_density(file_path)
            elif file_type in ['pdf', 'office', 'text']:
                return self._assess_document_text_density(file_path, file_type)
            else:
                return 0.5  # Default for unknown types
            
        except Exception as e:
            logger.warning(f"Text density assessment failed for {file_path}: {str(e)}")
            return 0.0
    
    def _assess_image_text_density(self, file_path: Path) -> float:
        """Assess text density in image using OCR preprocessing"""
        try:
            # Load image
            image = cv2.imread(str(file_path))
            if image is None:
                return 0.0
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive threshold to detect text regions
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Find contours (potential text regions)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Calculate text area ratio
            total_area = gray.shape[0] * gray.shape[1]
            text_area = sum(cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 100)
            
            text_density = text_area / total_area if total_area > 0 else 0.0
            return min(text_density * 10, 1.0)  # Scale up and cap at 1.0
            
        except Exception:
            return 0.0
    
    def _assess_document_text_density(self, file_path: Path, file_type: str) -> float:
        """Assess text density in document files"""
        try:
            # This is a simplified version - in production, you'd use proper text extraction
            file_size = file_path.stat().st_size
            
            # Estimate text density based on file size and type
            if file_type == 'text':
                # For text files, assume high text density
                return 0.8
            elif file_type == 'pdf':
                # For PDFs, estimate based on file size (very rough)
                if file_size < 100000:  # < 100KB
                    return 0.3
                elif file_size < 1000000:  # < 1MB
                    return 0.6
                else:
                    return 0.8
            elif file_type == 'office':
                # For office docs, assume moderate to high text density
                return 0.7
            else:
                return 0.5
                
        except Exception:
            return 0.0
    
    def _calculate_overall_score(self, file_size_valid: bool, image_quality: Optional[float], 
                               text_density: Optional[float]) -> float:
        """Calculate overall quality score"""
        if not file_size_valid:
            return 0.0
        
        scores = []
        
        # File size score (binary)
        scores.append(1.0)
        
        # Image quality score
        if image_quality is not None:
            scores.append(image_quality)
        else:
            scores.append(0.8)  # Default for non-image files
        
        # Text density score
        if text_density is not None:
            scores.append(text_density)
        else:
            scores.append(0.8)  # Default
        
        return sum(scores) / len(scores)
    
    def _make_processing_decision(self, assessment: QualityAssessment) -> QualityDecision:
        """Make processing decision based on assessment"""
        if not assessment.file_size_valid:
            return QualityDecision.REJECT
        
        if assessment.overall_quality_score >= 0.8:
            return QualityDecision.PROCESS
        elif assessment.overall_quality_score >= 0.5:
            return QualityDecision.ENHANCE
        else:
            return QualityDecision.REJECT
