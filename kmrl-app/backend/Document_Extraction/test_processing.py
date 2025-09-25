"""
Test script for KMRL Document Processing System
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from document_processor.models import FileType, ProcessingStatus, QualityDecision
        print("✓ Models imported successfully")
    except ImportError as e:
        print(f"✗ Models import failed: {e}")
        return False
    
    try:
        from document_processor.utils.file_detector import FileTypeDetector
        print("✓ File detector imported successfully")
    except ImportError as e:
        print(f"✗ File detector import failed: {e}")
        return False
    
    try:
        from document_processor.utils.quality_assessor import QualityAssessor
        print("✓ Quality assessor imported successfully")
    except ImportError as e:
        print(f"✗ Quality assessor import failed: {e}")
        return False
    
    try:
        from document_processor.processors.text_processor import TextProcessor
        print("✓ Text processor imported successfully")
    except ImportError as e:
        print(f"✗ Text processor import failed: {e}")
        return False
    
    try:
        from document_processor.processors.image_processor import ImageProcessor
        print("✓ Image processor imported successfully")
    except ImportError as e:
        print(f"✗ Image processor import failed: {e}")
        return False
    
    try:
        from document_processor.processors.cad_processor import CADProcessor
        print("✓ CAD processor imported successfully")
    except ImportError as e:
        print(f"✗ CAD processor import failed: {e}")
        return False
    
    return True


def test_file_detection():
    """Test file type detection"""
    print("\nTesting file type detection...")
    
    try:
        from document_processor.utils.file_detector import FileTypeDetector
        detector = FileTypeDetector()
        
        # Test with the existing PDF
        test_file = "Unit 4.pdf"
        if Path(test_file).exists():
            file_type, mime_type, confidence = detector.detect_file_type(test_file)
            print(f"✓ File detection: {test_file} -> {file_type.value} (confidence: {confidence:.2f})")
            return True
        else:
            print(f"✗ Test file {test_file} not found")
            return False
    except Exception as e:
        print(f"✗ File detection test failed: {e}")
        return False


def test_quality_assessment():
    """Test quality assessment"""
    print("\nTesting quality assessment...")
    
    try:
        from document_processor.utils.quality_assessor import QualityAssessor
        assessor = QualityAssessor()
        
        test_file = "genral_cv-8.pdf"
        if Path(test_file).exists():
            assessment = assessor.assess_quality(test_file, "pdf")
            print(f"✓ Quality assessment: {assessment.decision.value} (score: {assessment.overall_quality_score:.2f})")
            return True
        else:
            print(f"✗ Test file {test_file} not found")
            return False
    except Exception as e:
        print(f"✗ Quality assessment test failed: {e}")
        return False


def test_text_processing():
    """Test text processing"""
    print("\nTesting text processing...")
    
    try:
        from document_processor.processors.text_processor import TextProcessor
        from document_processor.models import FileType
        
        processor = TextProcessor()
        test_file = "genral_cv-8.pdf"
        
        if Path(test_file).exists():
            result = processor.process(test_file, FileType.PDF, file_id="test_001")
            if result.success:
                print(f"✓ Text processing: Success (text length: {len(result.extracted_text) if result.extracted_text else 0})")
                return True
            else:
                print(f"✗ Text processing failed: {result.errors}")
                return False
        else:
            print(f"✗ Test file {test_file} not found")
            return False
    except Exception as e:
        print(f"✗ Text processing test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("KMRL Document Processing System - Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_file_detection,
        test_quality_assessment,
        test_text_processing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! System is ready to use.")
    else:
        print("✗ Some tests failed. Check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
