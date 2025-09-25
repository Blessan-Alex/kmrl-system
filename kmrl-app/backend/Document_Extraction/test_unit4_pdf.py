"""
Test Unit 4.pdf processing
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


def test_unit4_pdf():
    """Test Unit 4.pdf processing"""
    print("🔍 Testing Unit 4.pdf Processing")
    print("=" * 60)
    
    pdf_file = "Unit 4.pdf"
    
    if not Path(pdf_file).exists():
        print(f"❌ PDF file {pdf_file} not found!")
        return
    
    file_size_mb = Path(pdf_file).stat().st_size / (1024 * 1024)
    print(f"📄 Processing file: {pdf_file}")
    print(f"📊 File size: {file_size_mb:.1f} MB")
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
    result = processor.process(pdf_file, file_type, file_id="unit4_test")
    
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
    
    # Step 4: Show Extracted Text Preview
    if result.success and result.extracted_text:
        print("📝 Step 4: Extracted Text Preview")
        print("-" * 30)
        text_preview = result.extracted_text[:1000] + "..." if len(result.extracted_text) > 1000 else result.extracted_text
        print(text_preview)
        print()
        
        # Save full text to file
        output_file = "unit4_extracted_text.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.extracted_text)
        print(f"💾 Full text saved to: {output_file}")
        print()
        
        # Show text statistics
        lines = result.extracted_text.split('\n')
        words = result.extracted_text.split()
        print(f"📊 Text Statistics:")
        print(f"   - Characters: {len(result.extracted_text):,}")
        print(f"   - Words: {len(words):,}")
        print(f"   - Lines: {len(lines):,}")
        print()
    
    # Step 5: Summary
    print("📋 Step 5: Processing Summary")
    print("-" * 30)
    print(f"📄 File: {pdf_file}")
    print(f"📊 Size: {file_size_mb:.1f} MB")
    print(f"🔍 Type: {file_type.value} (confidence: {confidence:.2f})")
    print(f"📊 Quality: {assessment.decision.value} (score: {assessment.overall_quality_score:.2f})")
    print(f"⚙️  Processor: {result.metadata.get('processor', 'Unknown')}")
    print(f"⏱️  Time: {result.processing_time:.2f}s")
    print(f"📝 Text: {len(result.extracted_text) if result.extracted_text else 0:,} chars")
    print(f"🌐 Language: {result.metadata.get('language', 'Unknown')}")
    
    if result.success:
        print("\n🎉 Unit 4.pdf processing completed successfully!")
    else:
        print("\n❌ Unit 4.pdf processing failed!")
    
    return result


def main():
    """Main test function"""
    print("🚀 KMRL Document Processing System - Unit 4.pdf Test")
    print("=" * 70)
    print("Testing large PDF file (4.0MB)")
    print()
    
    result = test_unit4_pdf()
    
    print("\n" + "=" * 70)
    if result and result.success:
        print("✅ Unit 4.pdf test completed successfully!")
        print("📁 Check 'unit4_extracted_text.txt' for full extracted content")
    else:
        print("❌ Unit 4.pdf test failed!")
        print("Check the errors above for details.")


if __name__ == "__main__":
    main()

