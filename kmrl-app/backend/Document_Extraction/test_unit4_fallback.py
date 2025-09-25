"""
Test Unit 4.pdf with fallback methods
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import PyPDF2
import time


def test_unit4_fallback():
    """Test Unit 4.pdf with PyPDF2 fallback"""
    print("🔍 Testing Unit 4.pdf with Fallback Methods")
    print("=" * 60)
    
    pdf_file = "Unit 4.pdf"
    
    if not Path(pdf_file).exists():
        print(f"❌ PDF file {pdf_file} not found!")
        return
    
    file_size_mb = Path(pdf_file).stat().st_size / (1024 * 1024)
    print(f"📄 Processing file: {pdf_file}")
    print(f"📊 File size: {file_size_mb:.1f} MB")
    print()
    
    # Method 1: PyPDF2
    print("📖 Method 1: PyPDF2 Processing")
    print("-" * 30)
    try:
        start_time = time.time()
        
        with open(pdf_file, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"✅ Pages: {num_pages}")
            
            text_parts = []
            successful_pages = 0
            
            for page_num in range(min(num_pages, 10)):  # Process first 10 pages
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text.strip():
                        text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
                        successful_pages += 1
                        print(f"✅ Page {page_num + 1}: {len(page_text)} chars")
                    else:
                        print(f"⚠️  Page {page_num + 1}: No text extracted")
                        
                except Exception as e:
                    print(f"❌ Page {page_num + 1}: Error - {str(e)}")
                    continue
            
            combined_text = '\n\n'.join(text_parts)
            processing_time = time.time() - start_time
            
            print(f"✅ Successful pages: {successful_pages}/{min(num_pages, 10)}")
            print(f"✅ Total text: {len(combined_text)} characters")
            print(f"✅ Processing time: {processing_time:.2f}s")
            
            if combined_text:
                # Save extracted text
                output_file = "unit4_fallback_text.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(combined_text)
                print(f"💾 Text saved to: {output_file}")
                
                # Show preview
                print("\n📝 Text Preview (first 500 chars):")
                print("-" * 30)
                preview = combined_text[:500] + "..." if len(combined_text) > 500 else combined_text
                print(preview)
                
                return True
            else:
                print("❌ No text could be extracted")
                return False
                
    except Exception as e:
        print(f"❌ PyPDF2 processing failed: {str(e)}")
        return False


def test_pdf_info():
    """Get basic PDF information"""
    print("\n📊 PDF Information")
    print("-" * 30)
    
    try:
        with open("Unit 4.pdf", 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"✅ Pages: {len(pdf_reader.pages)}")
            print(f"✅ Encrypted: {pdf_reader.is_encrypted}")
            
            if hasattr(pdf_reader, 'metadata') and pdf_reader.metadata:
                print(f"✅ Title: {pdf_reader.metadata.get('/Title', 'Unknown')}")
                print(f"✅ Author: {pdf_reader.metadata.get('/Author', 'Unknown')}")
                print(f"✅ Creator: {pdf_reader.metadata.get('/Creator', 'Unknown')}")
            
            # Check first page
            if len(pdf_reader.pages) > 0:
                first_page = pdf_reader.pages[0]
                print(f"✅ First page rotation: {first_page.rotation}")
                print(f"✅ First page media box: {first_page.mediabox}")
                
    except Exception as e:
        print(f"❌ Error getting PDF info: {str(e)}")


def main():
    """Main test function"""
    print("🚀 Unit 4.pdf Fallback Processing Test")
    print("=" * 70)
    print("Testing with PyPDF2 fallback method")
    print()
    
    # Get PDF info first
    test_pdf_info()
    
    # Try fallback processing
    success = test_unit4_fallback()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Unit 4.pdf fallback processing completed!")
        print("📁 Check 'unit4_fallback_text.txt' for extracted content")
    else:
        print("❌ Unit 4.pdf fallback processing failed!")
        print("💡 The PDF may be corrupted or have complex formatting")


if __name__ == "__main__":
    main()

