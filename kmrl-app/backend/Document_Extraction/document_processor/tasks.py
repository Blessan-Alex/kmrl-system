"""
Celery tasks for document processing
"""
import time
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from celery_app import celery_app
from document_processor.models import (
    FileType, ProcessingStatus, QualityDecision, 
    DocumentMetadata, ProcessingResult
)
from document_processor.utils.file_detector import FileTypeDetector
from document_processor.utils.quality_assessor import QualityAssessor
from document_processor.processors.text_processor import TextProcessor
from document_processor.processors.image_processor import ImageProcessor
from document_processor.processors.cad_processor import CADProcessor


@celery_app.task(bind=True, name='process_document')
def process_document(self, file_path: str, file_id: str, **kwargs) -> Dict[str, Any]:
    """
    Main document processing task
    
    Args:
        file_path: Path to the file to process
        file_id: Unique identifier for the file
        **kwargs: Additional processing parameters
        
    Returns:
        Processing result dictionary
    """
    task_id = self.request.id
    logger.info(f"Starting document processing task {task_id} for file: {file_path}")
    
    try:
        # Initialize processors
        file_detector = FileTypeDetector()
        quality_assessor = QualityAssessor()
        
        # Step 1: File Type Detection
        logger.info(f"Step 1: Detecting file type for {file_path}")
        file_type, mime_type, confidence = file_detector.detect_file_type(file_path)
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'step': 'file_type_detection', 'file_type': file_type.value, 'confidence': confidence}
        )
        
        # Step 2: Quality Assessment
        logger.info(f"Step 2: Assessing quality for {file_path}")
        quality_assessment = quality_assessor.assess_quality(file_path, file_type.value)
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={
                'step': 'quality_assessment',
                'quality_score': quality_assessment.overall_quality_score,
                'decision': quality_assessment.decision.value
            }
        )
        
        # Step 3: Route to appropriate processor based on quality decision
        if quality_assessment.decision == QualityDecision.REJECT:
            logger.warning(f"File {file_path} rejected due to quality issues: {quality_assessment.issues}")
            return {
                'success': False,
                'file_id': file_id,
                'status': ProcessingStatus.REJECTED.value,
                'reason': 'Quality assessment failed',
                'issues': quality_assessment.issues,
                'recommendations': quality_assessment.recommendations
            }
        
        elif quality_assessment.decision == QualityDecision.ENHANCE:
            logger.info(f"File {file_path} requires enhancement before processing")
            enhancement_needed = True
            # Auto-enhance images before processing
            if file_type == FileType.IMAGE:
                try:
                    processor = ImageProcessor()
                    enhanced_path = str(Path(file_path).with_suffix('.enhanced.jpg'))
                    enh_result = processor.enhance_image(file_path, enhanced_path)
                    if enh_result.get('success'):
                        logger.info(f"Enhanced image saved to {enhanced_path}")
                        file_path = enhanced_path
                    else:
                        logger.warning(f"Image enhancement failed, continuing with original: {enh_result.get('error')}")
                except Exception as e:
                    logger.warning(f"Image enhancement step failed: {e}")
        else:
            enhancement_needed = False
        
        # Step 4: Process document with appropriate processor
        logger.info(f"Step 3: Processing {file_type.value} document: {file_path}")
        self.update_state(
            state='PROGRESS',
            meta={'step': 'document_processing', 'file_type': file_type.value}
        )
        
        processing_result = _route_to_processor(file_path, file_type, file_id, **kwargs)
        
        # Step 5: Post-processing
        if processing_result.success:
            logger.info(f"Document processing completed successfully for {file_path}")
            
            # Add quality assessment info to result
            processing_result.metadata.update({
                'quality_score': quality_assessment.overall_quality_score,
                'quality_decision': quality_assessment.decision.value,
                'enhancement_needed': enhancement_needed,
                'file_type_detected': file_type.value,
                'mime_type': mime_type,
                'detection_confidence': confidence
            })

            # Confidence assessment and human review flagging
            # Prefer OCR confidence when available; fallback to quality score
            result_confidence = processing_result.metadata.get('ocr_confidence')
            if isinstance(result_confidence, (int, float)):
                confidence_score = float(result_confidence)
            else:
                confidence_score = float(quality_assessment.overall_quality_score)
            human_review_required = confidence_score < 0.7
            processing_result.metadata['confidence_score'] = confidence_score
            processing_result.metadata['human_review_required'] = human_review_required
            
            return {
                'success': True,
                'file_id': file_id,
                'status': ProcessingStatus.COMPLETED.value,
                'processing_result': processing_result.dict(),
                'quality_assessment': quality_assessment.dict(),
                'human_review_required': human_review_required,
                'confidence_score': confidence_score
            }
        else:
            logger.error(f"Document processing failed for {file_path}: {processing_result.errors}")
            return {
                'success': False,
                'file_id': file_id,
                'status': ProcessingStatus.FAILED.value,
                'errors': processing_result.errors,
                'processing_result': processing_result.dict()
            }
            
    except Exception as e:
        logger.error(f"Unexpected error in document processing task {task_id}: {str(e)}")
        return {
            'success': False,
            'file_id': file_id,
            'status': ProcessingStatus.FAILED.value,
            'error': str(e)
        }


def _route_to_processor(file_path: str, file_type: FileType, file_id: str, **kwargs) -> ProcessingResult:
    """Route document to appropriate processor"""
    try:
        # Initialize processors
        processors = {
            FileType.TEXT: TextProcessor(),
            FileType.OFFICE: TextProcessor(),
            FileType.PDF: TextProcessor(),
            FileType.IMAGE: ImageProcessor(),
            FileType.CAD: CADProcessor()
        }
        
        processor = processors.get(file_type)
        if not processor:
            return ProcessingResult(
                file_id=file_id,
                success=False,
                processing_time=0.0,
                errors=[f"No processor available for file type: {file_type}"]
            )
        
        if not processor.can_process(file_type):
            return ProcessingResult(
                file_id=file_id,
                success=False,
                processing_time=0.0,
                errors=[f"Processor cannot handle file type: {file_type}"]
            )
        
        # Process the document
        return processor.process(file_path, file_type, file_id=file_id, **kwargs)
        
    except Exception as e:
        logger.error(f"Error routing to processor for {file_path}: {str(e)}")
        return ProcessingResult(
            file_id=file_id,
            success=False,
            processing_time=0.0,
            errors=[f"Processor routing failed: {str(e)}"]
        )


@celery_app.task(bind=True, name='enhance_image')
def enhance_image(self, file_path: str, output_path: str, **kwargs) -> Dict[str, Any]:
    """
    Image enhancement task
    
    Args:
        file_path: Path to the input image
        output_path: Path to save enhanced image
        **kwargs: Additional parameters
        
    Returns:
        Enhancement result dictionary
    """
    task_id = self.request.id
    logger.info(f"Starting image enhancement task {task_id} for: {file_path}")
    
    try:
        processor = ImageProcessor()
        result = processor.enhance_image(file_path, output_path)
        
        if result['success']:
            logger.info(f"Image enhancement completed for {file_path}")
            return {
                'success': True,
                'task_id': task_id,
                'enhanced_image_path': result['enhanced_image_path'],
                'processing_time': result['processing_time'],
                'enhancement_applied': result['enhancement_applied']
            }
        else:
            logger.error(f"Image enhancement failed for {file_path}: {result.get('error', 'Unknown error')}")
            return {
                'success': False,
                'task_id': task_id,
                'error': result.get('error', 'Unknown error')
            }
            
    except Exception as e:
        logger.error(f"Unexpected error in image enhancement task {task_id}: {str(e)}")
        return {
            'success': False,
            'task_id': task_id,
            'error': str(e)
        }


@celery_app.task(bind=True, name='ocr_process')
def ocr_process(self, image_path: str, file_id: str, **kwargs) -> Dict[str, Any]:
    """
    OCR processing task
    
    Args:
        image_path: Path to the image file
        file_id: Unique identifier for the file
        **kwargs: Additional parameters
        
    Returns:
        OCR result dictionary
    """
    task_id = self.request.id
    logger.info(f"Starting OCR task {task_id} for: {image_path}")
    
    try:
        processor = ImageProcessor()
        result = processor.process(image_path, FileType.IMAGE, file_id=file_id, **kwargs)
        
        if result.success:
            logger.info(f"OCR processing completed for {image_path}")
            return {
                'success': True,
                'task_id': task_id,
                'file_id': file_id,
                'extracted_text': result.extracted_text,
                'confidence': result.metadata.get('ocr_confidence', 0.0),
                'language': result.metadata.get('language', 'unknown'),
                'processing_time': result.processing_time
            }
        else:
            logger.error(f"OCR processing failed for {image_path}: {result.errors}")
            return {
                'success': False,
                'task_id': task_id,
                'file_id': file_id,
                'errors': result.errors
            }
            
    except Exception as e:
        logger.error(f"Unexpected error in OCR task {task_id}: {str(e)}")
        return {
            'success': False,
            'task_id': task_id,
            'file_id': file_id,
            'error': str(e)
        }


@celery_app.task(name='health_check')
def health_check() -> Dict[str, Any]:
    """Health check task for monitoring"""
    return {
        'status': 'healthy',
        'timestamp': time.time(),
        'workers': 'active'
    }
