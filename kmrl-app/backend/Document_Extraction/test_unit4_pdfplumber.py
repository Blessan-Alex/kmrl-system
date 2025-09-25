"""
Test Unit 4.pdf with pdfplumber
"""
import sys
from pathlib import Path
import time

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pdfplumber


def test_unit4_pdfplumber():
    """Test Unit 4.pdf with pdfplumber"""
    print("🔍 Testing Unit 4.pdf with pdfplumber")
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
            
            # Process first 10 pages
            for page_num in range(min(num_pages, 10)):
                try:
                    page = pdf.pages[page_num]
                    
                    # Try different extraction methods
                    text = page.extract_text()
                    
                    if text and text.strip():
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
                        successful_pages += 1
                        print(f"✅ Page {page_num + 1}: {len(text)} chars")
                    else:
                        # Try extracting text from tables
                        tables = page.extract_tables()
                        if tables:
                            table_text = ""
                            for table in tables:
                                for row in table:
                                    if row:
                                        table_text += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"
                            
                            if table_text.strip():
                                text_parts.append(f"--- Page {page_num + 1} (Tables) ---\n{table_text}")
                                successful_pages += 1
                                print(f"✅ Page {page_num + 1}: {len(table_text)} chars (tables)")
                            else:
                                print(f"⚠️  Page {page_num + 1}: No text or tables found")
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
                output_file = "unit4_pdfplumber_text.txt"
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
                print("❌ No text could be extracted with pdfplumber")
                return False
                
    except Exception as e:
        print(f"❌ pdfplumber processing failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🚀 Unit 4.pdf pdfplumber Test")
    print("=" * 70)
    print("Testing with pdfplumber library")
    print()
    
    success = test_unit4_pdfplumber()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Unit 4.pdf pdfplumber processing completed!")
        print("📁 Check 'unit4_pdfplumber_text.txt' for extracted content")
    else:
        print("❌ Unit 4.pdf pdfplumber processing failed!")
        print("💡 The PDF may be corrupted or have complex formatting")


if __name__ == "__main__":
    main()

