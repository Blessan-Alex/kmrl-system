"""
Complete Unit 4.pdf test with our document processing system
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from document_processor.utils.file_detector import FileTypeDetector
from document_processor.utils.quality_assessor import QualityAssessor
from document_processor.processors.image_processor import ImageProcessor
from document_processor.models import FileType


def test_unit4_complete():
    """Complete test of Unit 4.pdf with our system"""
    print("🔍 Complete Unit 4.pdf Processing Test")
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
    
    # Step 3: Convert PDF to images and process with OCR
    print("⚙️  Step 3: PDF to Image + OCR Processing")
    print("-" * 30)
    
    try:
        import pdfplumber
        import pytesseract
        from PIL import Image
        
        with pdfplumber.open(pdf_file) as pdf:
            num_pages = len(pdf.pages)
            print(f"✅ Pages: {num_pages}")
            
            text_parts = []
            successful_pages = 0
            total_processing_time = 0
            
            for page_num in range(num_pages):
                try:
                    page = pdf.pages[page_num]
                    
                    # Convert page to image
                    page_image = page.to_image(resolution=300)
                    pil_image = page_image.original
                    
                    # Save temporary image for processing
                    temp_image_path = f"temp_page_{page_num + 1}.png"
                    pil_image.save(temp_image_path)
                    
                    # Process with our ImageProcessor
                    processor = ImageProcessor()
                    result = processor.process(temp_image_path, FileType.IMAGE, file_id=f"unit4_page_{page_num + 1}")
                    
                    if result.success and result.extracted_text:
                        text_parts.append(f"--- Page {page_num + 1} ---\n{result.extracted_text}")
                        successful_pages += 1
                        total_processing_time += result.processing_time
                        print(f"✅ Page {page_num + 1}: {len(result.extracted_text)} chars (OCR)")
                    else:
                        print(f"⚠️  Page {page_num + 1}: No text extracted")
                    
                    # Clean up temp file
                    Path(temp_image_path).unlink()
                    
                except Exception as e:
                    print(f"❌ Page {page_num + 1}: Error - {str(e)}")
                    continue
            
            combined_text = '\n\n'.join(text_parts)
            
            print(f"✅ Successful pages: {successful_pages}/{num_pages}")
            print(f"✅ Total text: {len(combined_text)} characters")
            print(f"✅ Total processing time: {total_processing_time:.2f}s")
            
            if combined_text:
                # Save extracted text
                output_file = "unit4_complete_text.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(combined_text)
                print(f"💾 Text saved to: {output_file}")
                
                # Show preview
                print("\n📝 Text Preview (first 1000 chars):")
                print("-" * 30)
                preview = combined_text[:1000] + "..." if len(combined_text) > 1000 else combined_text
                print(preview)
                
                return True
            else:
                print("❌ No text could be extracted")
                return False
                
    except Exception as e:
        print(f"❌ Processing failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🚀 KMRL Document Processing System - Complete Unit 4.pdf Test")
    print("=" * 80)
    print("Testing image-based PDF with OCR processing")
    print()
    
    success = test_unit4_complete()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ Unit 4.pdf complete processing successful!")
        print("📁 Check 'unit4_complete_text.txt' for extracted content")
        print("🎯 This demonstrates our system's ability to handle image-based PDFs!")
    else:
        print("❌ Unit 4.pdf complete processing failed!")
        print("Check the errors above for details.")


if __name__ == "__main__":
    main()

