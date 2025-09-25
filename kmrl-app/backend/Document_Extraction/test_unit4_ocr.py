"""
Test Unit 4.pdf with OCR processing
"""
import sys
from pathlib import Path
import time

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pdfplumber
import pytesseract
from PIL import Image
import io


def test_unit4_ocr():
    """Test Unit 4.pdf with OCR processing"""
    print("🔍 Testing Unit 4.pdf with OCR Processing")
    print("=" * 60)
    
    pdf_file = "Unit 4.pdf"
    
    if not Path(pdf_file).exists():
        print(f"❌ PDF file {pdf_file} not found!")
        return
    
    file_size_mb = Path(pdf_file).stat().st_size / (1024 * 1024)
    print(f"📄 Processing file: {pdf_file}")
    print(f"📊 File size: {file_size_mb:.1f} MB")
    print()
    
    try:
        start_time = time.time()
        
        with pdfplumber.open(pdf_file) as pdf:
            num_pages = len(pdf.pages)
            print(f"✅ Pages: {num_pages}")
            
            text_parts = []
            successful_pages = 0
            
            # Process each page
            for page_num in range(num_pages):
                try:
                    page = pdf.pages[page_num]
                    print(f"🔍 Processing page {page_num + 1}...")
                    
                    # Convert page to image
                    page_image = page.to_image(resolution=300)
                    pil_image = page_image.original
                    
                    # Perform OCR
                    ocr_text = pytesseract.image_to_string(pil_image, lang='eng')
                    
                    if ocr_text and ocr_text.strip():
                        text_parts.append(f"--- Page {page_num + 1} (OCR) ---\n{ocr_text}")
                        successful_pages += 1
                        print(f"✅ Page {page_num + 1}: {len(ocr_text)} chars (OCR)")
                    else:
                        print(f"⚠️  Page {page_num + 1}: No text found with OCR")
                        
                except Exception as e:
                    print(f"❌ Page {page_num + 1}: OCR Error - {str(e)}")
                    continue
            
            combined_text = '\n\n'.join(text_parts)
            processing_time = time.time() - start_time
            
            print(f"✅ Successful pages: {successful_pages}/{num_pages}")
            print(f"✅ Total text: {len(combined_text)} characters")
            print(f"✅ Processing time: {processing_time:.2f}s")
            
            if combined_text:
                # Save extracted text
                output_file = "unit4_ocr_text.txt"
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
                print("❌ No text could be extracted with OCR")
                return False
                
    except Exception as e:
        print(f"❌ OCR processing failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🚀 Unit 4.pdf OCR Test")
    print("=" * 70)
    print("Testing with OCR processing for image-based PDF")
    print()
    
    success = test_unit4_ocr()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Unit 4.pdf OCR processing completed!")
        print("📁 Check 'unit4_ocr_text.txt' for extracted content")
    else:
        print("❌ Unit 4.pdf OCR processing failed!")
        print("💡 The PDF may not contain readable text or images")


if __name__ == "__main__":
    main()

