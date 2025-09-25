"""
Direct PDF processing test without Redis/Celery
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from document_processor.utils.file_detector import FileTypeDetector
from document_processor.utils.quality_assessor import QualityAssessor
from document_processor.processors.text_processor import TextProcessor
from document_processor.models import FileType


def test_pdf_processing():
    """Test PDF processing directly without Celery"""
    print("🔍 Testing PDF Processing with genral_cv-8.pdf")
    print("=" * 60)
    
    pdf_file = "genral_cv-8.pdf"
    
    if not Path(pdf_file).exists():
        print(f"❌ PDF file {pdf_file} not found!")
        return
    
    print(f"📄 Processing file: {pdf_file}")
    print(f"📊 File size: {Path(pdf_file).stat().st_size / 1024:.1f} KB")
    print()
    
    # Step 1: File Type Detection
    print("🔍 Step 1: File Type Detection")
    print("-" * 30)
    detector = FileTypeDetector()
    file_type, mime_type, confidence = detector.detect_file_type(pdf_file)
    
    print(f"✅ Detected Type: {file_type.value}")
    print(f"✅ MIME Type: {mime_type}")
    print(f"✅ Confidence: {confidence:.2f}")
    print(f"✅ Supported: {detector.is_supported_file(pdf_file)}")
    print()
    
    # Step 2: Quality Assessment
    print("📊 Step 2: Quality Assessment")
    print("-" * 30)
    assessor = QualityAssessor()
    assessment = assessor.assess_quality(pdf_file, file_type.value)
    
    print(f"✅ File size valid: {assessment.file_size_valid}")
    print(f"✅ Image quality: {assessment.image_quality_score}")
    print(f"✅ Text density: {assessment.text_density}")
    print(f"✅ Overall quality: {assessment.overall_quality_score:.2f}")
    print(f"✅ Decision: {assessment.decision.value}")
    
    if assessment.issues:
        print(f"⚠️  Issues: {', '.join(assessment.issues)}")
    if assessment.recommendations:
        print(f"💡 Recommendations: {', '.join(assessment.recommendations)}")
    print()
    
    # Step 3: Document Processing
    print("⚙️  Step 3: Document Processing")
    print("-" * 30)
    processor = TextProcessor()
    result = processor.process(pdf_file, file_type, file_id="test_001")
    
    print(f"✅ Success: {result.success}")
    print(f"✅ Processing time: {result.processing_time:.2f}s")
    print(f"✅ Text length: {len(result.extracted_text) if result.extracted_text else 0} characters")
    print(f"✅ Language: {result.metadata.get('language', 'Unknown')}")
    print(f"✅ Needs translation: {result.metadata.get('needs_translation', False)}")
    
    if result.errors:
        print(f"❌ Errors: {', '.join(result.errors)}")
    if result.warnings:
        print(f"⚠️  Warnings: {', '.join(result.warnings)}")
    print()
    
    # Step 4: Show Extracted Text
    if result.success and result.extracted_text:
        print("📝 Step 4: Extracted Text Preview")
        print("-" * 30)
        text_preview = result.extracted_text[:500] + "..." if len(result.extracted_text) > 500 else result.extracted_text
        print(text_preview)
        print()
        
        # Save full text to file
        output_file = "extracted_text.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.extracted_text)
        print(f"💾 Full text saved to: {output_file}")
        print()
    
    # Step 5: Summary
    print("📋 Step 5: Processing Summary")
    print("-" * 30)
    print(f"📄 File: {pdf_file}")
    print(f"🔍 Type: {file_type.value} (confidence: {confidence:.2f})")
    print(f"📊 Quality: {assessment.decision.value} (score: {assessment.overall_quality_score:.2f})")
    print(f"⚙️  Processor: {result.metadata.get('processor', 'Unknown')}")
    print(f"⏱️  Time: {result.processing_time:.2f}s")
    print(f"📝 Text: {len(result.extracted_text) if result.extracted_text else 0} chars")
    print(f"🌐 Language: {result.metadata.get('language', 'Unknown')}")
    
    if result.success:
        print("\n🎉 PDF processing completed successfully!")
    else:
        print("\n❌ PDF processing failed!")
    
    return result


def test_different_processors():
    """Test different processors with the PDF"""
    print("\n" + "=" * 60)
    print("🔧 Testing Different Processors")
    print("=" * 60)
    
    pdf_file = "genral_cv-8.pdf"
    
    # Test Text Processor
    print("\n📝 Text Processor Test:")
    print("-" * 20)
    text_processor = TextProcessor()
    result = text_processor.process(pdf_file, FileType.PDF, file_id="text_test")
    print(f"✅ Can process PDF: {text_processor.can_process(FileType.PDF)}")
    print(f"✅ Success: {result.success}")
    print(f"✅ Text length: {len(result.extracted_text) if result.extracted_text else 0}")
    
    # Test Image Processor (should not process PDFs)
    print("\n🖼️  Image Processor Test:")
    print("-" * 20)
    from document_processor.processors.image_processor import ImageProcessor
    image_processor = ImageProcessor()
    print(f"❌ Can process PDF: {image_processor.can_process(FileType.PDF)}")
    
    # Test CAD Processor (should not process PDFs)
    print("\n🔧 CAD Processor Test:")
    print("-" * 20)
    from document_processor.processors.cad_processor import CADProcessor
    cad_processor = CADProcessor()
    print(f"❌ Can process PDF: {cad_processor.can_process(FileType.PDF)}")


def main():
    """Main test function"""
    print("🚀 KMRL Document Processing System - Direct PDF Test")
    print("=" * 60)
    print("Testing without Redis/Celery - Direct processing only")
    print()
    
    # Test PDF processing
    result = test_pdf_processing()
    
    # Test different processors
    test_different_processors()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    
    if result and result.success:
        print("\n🎯 Next steps:")
        print("1. Start Redis: redis-server")
        print("2. Start worker: python3 document_processor/worker.py")
        print("3. Use Celery tasks for production processing")
    else:
        print("\n❌ Some tests failed. Check the errors above.")


if __name__ == "__main__":
    main()

