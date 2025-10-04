#!/usr/bin/env python3
"""
Start Automated Document Processing
Processes all queued documents using Celery workers
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

from workers.automated_document_processor import (
    process_single_document, 
    process_batch_documents, 
    process_all_queued_documents
)

def main():
    """Start automated document processing"""
    print("🚀 Starting Automated Document Processing")
    print("=" * 50)
    
    # Option 1: Process all queued documents
    print("📋 Processing all queued documents...")
    try:
        result = process_all_queued_documents.delay()
        print(f"✅ Task submitted successfully! Task ID: {result.id}")
        print("⏳ Processing in background...")
        
        # Wait for result (optional - you can remove this to run in background)
        print("🔄 Waiting for completion...")
        final_result = result.get(timeout=1800)  # 30 minute timeout
        
        print("\n📊 Final Results:")
        print(f"   ✅ Successfully processed: {final_result.get('processed', 0)}")
        print(f"   ❌ Failed: {final_result.get('failed', 0)}")
        print(f"   📈 Total documents: {final_result.get('total', 0)}")
        print(f"   🔄 Batches completed: {final_result.get('batches', 0)}")
        
    except Exception as e:
        print(f"❌ Error starting automated processing: {e}")

if __name__ == "__main__":
    main()
