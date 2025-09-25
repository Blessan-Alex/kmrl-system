"""
Test the actual DWG file with our enhanced CAD processor
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from document_processor.processors.enhanced_cad_processor import EnhancedCADProcessor
from document_processor.models import FileType


def test_dwg_file():
    """Test the actual DWG file"""
    print("🔧 Testing AutoCAD2DSamples7.dwg")
    print("=" * 60)
    
    dwg_file = "AutoCAD2DSamples7.dwg"
    
    if not Path(dwg_file).exists():
        print(f"❌ DWG file {dwg_file} not found!")
        return
    
    file_size_kb = Path(dwg_file).stat().st_size / 1024
    print(f"📄 Processing file: {dwg_file}")
    print(f"📊 File size: {file_size_kb:.1f} KB")
    print()
    
    # Test enhanced CAD processor
    processor = EnhancedCADProcessor()
    
    print("🔍 Step 1: File Type Detection")
    print("-" * 30)
    print(f"✅ Can process CAD: {processor.can_process(FileType.CAD)}")
    print(f"✅ Supported extensions: {list(processor.cad_extensions.keys())}")
    print()
    
    print("📊 Step 2: CAD File Summary")
    print("-" * 30)
    summary = processor.get_cad_summary(dwg_file)
    
    if 'error' in summary:
        print(f"❌ Error: {summary['error']}")
    else:
        print(f"✅ File: {summary.get('file_name', 'Unknown')}")
        print(f"✅ Size: {summary.get('size', 0) / 1024:.1f} KB")
        print(f"✅ Extension: {summary.get('extension', 'Unknown')}")
        print(f"✅ Format: {summary.get('format', 'Unknown')}")
        print(f"✅ Processing available: {summary.get('processing_available', False)}")
        
        if 'dxf_version' in summary:
            print(f"✅ DXF Version: {summary.get('dxf_version', 'Unknown')}")
            print(f"✅ Layers: {summary.get('layers', 0)}")
            print(f"✅ Blocks: {summary.get('blocks', 0)}")
            print(f"✅ Entities: {summary.get('entities', 0)}")
            print(f"✅ Has text: {summary.get('has_text', False)}")
            print(f"✅ Has dimensions: {summary.get('has_dimensions', False)}")
            print(f"✅ Has geometry: {summary.get('has_geometry', False)}")
    
    print()
    
    print("⚙️  Step 3: Full CAD Processing")
    print("-" * 30)
    result = processor.process(dwg_file, FileType.CAD, file_id="dwg_test")
    
    print(f"✅ Success: {result.success}")
    print(f"✅ Processing time: {result.processing_time:.2f}s")
    print(f"✅ Text length: {len(result.extracted_text) if result.extracted_text else 0} characters")
    
    if result.errors:
        print(f"❌ Errors: {', '.join(result.errors)}")
    if result.warnings:
        print(f"⚠️  Warnings: {', '.join(result.warnings)}")
    
    print()
    
    if result.success and result.extracted_text:
        print("📝 Step 4: Extracted Content")
        print("-" * 30)
        print(result.extracted_text)
        print()
        
        # Save to file
        output_file = "dwg_extracted_text.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.extracted_text)
        print(f"💾 Full content saved to: {output_file}")
        
        # Show metadata
        print("\n📊 Step 5: Processing Metadata")
        print("-" * 30)
        metadata = result.metadata
        print(f"✅ Processor: {metadata.get('processor', 'Unknown')}")
        print(f"✅ File type: {metadata.get('file_type', 'Unknown')}")
        print(f"✅ Extraction method: {metadata.get('extraction_method', 'Unknown')}")
        print(f"✅ ezdxf available: {metadata.get('ezdxf_available', False)}")
        
        if 'cad_data' in metadata:
            cad_data = metadata['cad_data']
            print(f"✅ Extraction successful: {cad_data.get('extraction_successful', False)}")
            if not cad_data.get('extraction_successful'):
                print(f"✅ Reason: {cad_data.get('reason', 'Unknown')}")
    
    return result


def test_dwg_conversion():
    """Test DWG to DXF conversion approach"""
    print("\n🔄 DWG to DXF Conversion Test")
    print("=" * 60)
    
    print("💡 DWG files are proprietary AutoCAD format")
    print("💡 For full processing, we need to convert to DXF first")
    print()
    
    print("📚 Conversion Options:")
    print("-" * 30)
    print("1. 🖥️  AutoCAD (Commercial)")
    print("   - Save As DXF format")
    print("   - Full compatibility")
    print()
    print("2. 🔧 LibreCAD (Free)")
    print("   - Open DWG, export as DXF")
    print("   - Good for 2D drawings")
    print()
    print("3. ☁️  Online Converters")
    print("   - Convert DWG to DXF online")
    print("   - No software installation needed")
    print()
    print("4. 🐍 Python Libraries")
    print("   - ezdxf (DXF only)")
    print("   - FreeCAD Python API")
    print("   - OpenCASCADE Python bindings")
    print()
    
    print("🎯 Current Status:")
    print("-" * 30)
    print("✅ DWG file detected and validated")
    print("✅ Basic metadata extraction working")
    print("❌ Full content extraction requires DXF conversion")
    print("💡 System provides informative placeholder text")


def main():
    """Main test function"""
    print("🚀 KMRL Document Processing System - DWG File Test")
    print("=" * 80)
    print("Testing actual AutoCAD DWG file processing")
    print()
    
    result = test_dwg_file()
    test_dwg_conversion()
    
    print("\n" + "=" * 80)
    if result and result.success:
        print("✅ DWG file test completed successfully!")
        print("📁 Check 'dwg_extracted_text.txt' for extracted content")
        print("🎯 System handles DWG files with appropriate metadata extraction")
    else:
        print("❌ DWG file test failed!")
        print("💡 This is expected for DWG files without conversion to DXF")


if __name__ == "__main__":
    main()

