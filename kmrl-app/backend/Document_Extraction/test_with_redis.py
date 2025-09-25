"""
Test with Redis and Celery (when Redis is running)
"""
import sys
from pathlib import Path
import time

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from document_processor.tasks import process_document, health_check


def test_with_redis():
    """Test the system with Redis and Celery"""
    print("🚀 Testing with Redis and Celery")
    print("=" * 50)
    
    # Test health check first
    print("🔍 Testing health check...")
    try:
        health_result = health_check.delay()
        print(f"✅ Health check task submitted: {health_result.id}")
        
        # Wait for result
        result = health_result.get(timeout=10)
        print(f"✅ Health check result: {result}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print("💡 Make sure Redis is running: redis-server")
        return False
    
    # Test document processing
    print("\n📄 Testing document processing...")
    pdf_file = "genral_cv-8.pdf"
    
    if not Path(pdf_file).exists():
        print(f"❌ PDF file {pdf_file} not found!")
        return False
    
    try:
        # Submit document processing task
        print(f"📤 Submitting task for: {pdf_file}")
        task = process_document.delay(pdf_file, "redis_test_001")
        print(f"✅ Task submitted: {task.id}")
        
        # Wait for result
        print("⏳ Waiting for processing to complete...")
        result = task.get(timeout=60)  # 60 second timeout
        
        print("\n📊 Processing Result:")
        print("-" * 30)
        print(f"✅ Success: {result.get('success', False)}")
        print(f"✅ File ID: {result.get('file_id', 'Unknown')}")
        print(f"✅ Status: {result.get('status', 'Unknown')}")
        
        if result.get('success'):
            processing_result = result.get('processing_result', {})
            print(f"✅ Text length: {len(processing_result.get('extracted_text', ''))}")
            print(f"✅ Processing time: {processing_result.get('processing_time', 0):.2f}s")
            print(f"✅ Language: {processing_result.get('metadata', {}).get('language', 'Unknown')}")
            
            # Save result to file
            if processing_result.get('extracted_text'):
                output_file = "redis_extracted_text.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(processing_result['extracted_text'])
                print(f"💾 Text saved to: {output_file}")
        else:
            print(f"❌ Processing failed: {result.get('errors', 'Unknown error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        return False


def main():
    """Main test function"""
    print("🔧 KMRL Document Processing System - Redis Test")
    print("=" * 60)
    print("This test requires Redis to be running")
    print("Start Redis with: redis-server")
    print()
    
    success = test_with_redis()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Redis test completed successfully!")
        print("✅ Your system is ready for production use!")
    else:
        print("❌ Redis test failed!")
        print("💡 Make sure Redis is running: redis-server")
        print("💡 Then start the worker: python3 document_processor/worker.py")


if __name__ == "__main__":
    main()

