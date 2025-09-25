"""
Example usage of KMRL Document Processing System
"""
import time
from pathlib import Path
from loguru import logger

from document_processor.tasks import process_document, enhance_image, ocr_process
from document_processor.utils.file_detector import FileTypeDetector
from document_processor.utils.quality_assessor import QualityAssessor
from document_processor.processors.text_processor import TextProcessor
from document_processor.processors.image_processor import ImageProcessor
from document_processor.processors.cad_processor import CADProcessor


def example_file_type_detection():
    """Example of file type detection"""
    print("\n=== File Type Detection Example ===")
    
    detector = FileTypeDetector()
    
    # Test files (you would replace these with actual files)
    test_files = [
        "sample.pdf",
        "document.docx", 
        "image.jpg",
        "drawing.dwg",
        "data.xlsx"
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            file_type, mime_type, confidence = detector.detect_file_type(file_path)
            print(f"File: {file_path}")
            print(f"  Type: {file_type.value}")
            print(f"  MIME: {mime_type}")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Supported: {detector.is_supported_file(file_path)}")
            print()


def example_quality_assessment():
    """Example of quality assessment"""
    print("\n=== Quality Assessment Example ===")
    
    assessor = QualityAssessor()
    
    # Test with a sample file
    test_file = "genral_cv-8.pdf"  # Using the existing PDF in the directory
    
    if Path(test_file).exists():
        assessment = assessor.assess_quality(test_file, "pdf")
        
        print(f"File: {test_file}")
        print(f"File size valid: {assessment.file_size_valid}")
        print(f"Image quality: {assessment.image_quality_score}")
        print(f"Text density: {assessment.text_density}")
        print(f"Overall quality: {assessment.overall_quality_score:.2f}")
        print(f"Decision: {assessment.decision.value}")
        print(f"Issues: {assessment.issues}")
        print(f"Recommendations: {assessment.recommendations}")
    else:
        print(f"Test file {test_file} not found")


def example_document_processing():
    """Example of document processing"""
    print("\n=== Document Processing Example ===")
    
    # Test with the existing PDF
    test_file = "genral_cv-8.pdf"
    
    if Path(test_file).exists():
        print(f"Processing file: {test_file}")
        
        # Process using TextProcessor
        processor = TextProcessor()
        result = processor.process(test_file, "pdf", file_id="test_001")
        
        print(f"Success: {result.success}")
        print(f"Processing time: {result.processing_time:.2f}s")
        print(f"Text length: {len(result.extracted_text) if result.extracted_text else 0}")
        print(f"Metadata: {result.metadata}")
        
        if result.errors:
            print(f"Errors: {result.errors}")
        
        if result.warnings:
            print(f"Warnings: {result.warnings}")
    else:
        print(f"Test file {test_file} not found")


def example_celery_task():
    """Example of using Celery tasks"""
    print("\n=== Celery Task Example ===")
    
    test_file = "genral_cv-8.pdf"
    
    if Path(test_file).exists():
        print(f"Submitting task for: {test_file}")
        
        # Submit task to Celery
        task = process_document.delay(test_file, "celery_test_001")
        
        print(f"Task ID: {task.id}")
        print("Task submitted to queue...")
        print("Note: This requires a running Celery worker to process")
        
        # In a real scenario, you would wait for the task to complete
        # result = task.get(timeout=30)
        # print(f"Task result: {result}")
    else:
        print(f"Test file {test_file} not found")


def example_processor_routing():
    """Example of processor routing"""
    print("\n=== Processor Routing Example ===")
    
    processors = {
        "text": TextProcessor(),
        "image": ImageProcessor(),
        "cad": CADProcessor()
    }
    
    test_cases = [
        ("document.pdf", "pdf"),
        ("image.jpg", "image"),
        ("drawing.dwg", "cad"),
        ("spreadsheet.xlsx", "office")
    ]
    
    for file_name, file_type in test_cases:
        print(f"\nFile: {file_name} (Type: {file_type})")
        
        for processor_name, processor in processors.items():
            can_process = processor.can_process(file_type)
            print(f"  {processor_name} processor: {'✓' if can_process else '✗'}")


def main():
    """Run all examples"""
    print("KMRL Document Processing System - Examples")
    print("=" * 50)
    
    # Run examples
    example_file_type_detection()
    example_quality_assessment()
    example_document_processing()
    example_processor_routing()
    example_celery_task()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo run the worker:")
    print("  python document_processor/worker.py")
    print("\nTo process documents via Celery:")
    print("  from document_processor.tasks import process_document")
    print("  task = process_document.delay('path/to/file.pdf', 'file_id')")


if __name__ == "__main__":
    main()
