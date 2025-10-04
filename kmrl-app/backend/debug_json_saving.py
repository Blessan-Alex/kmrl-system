#!/usr/bin/env python3
"""
Debug JSON Saving Issue
Test the JSON saving functionality step by step
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append('.')

from models.database import SessionLocal
from models.document import Document

def test_json_saving():
    """Test JSON saving functionality"""
    print("🔍 Debugging JSON Saving Issue")
    print("=" * 50)
    
    # Test 1: Check if we can create output folder
    output_folder = Path("debug_json_test")
    output_folder.mkdir(exist_ok=True)
    print(f"✅ Output folder created: {output_folder.absolute()}")
    
    # Test 2: Check if we can write a simple JSON file
    test_json_path = output_folder / "test.json"
    test_data = {
        "test": "data",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        with open(test_json_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Test JSON file created: {test_json_path}")
    except Exception as e:
        print(f"❌ Failed to create test JSON: {e}")
        return
    
    # Test 3: Check database connection and get a document
    try:
        db = SessionLocal()
        # Get any document (processed or queued)
        doc = db.query(Document).first()
        if doc:
            print(f"✅ Found document: {doc.original_filename} (ID: {doc.id}, Status: {doc.status})")
            
            # Test 4: Create JSON structure like the processor does
            json_data = {
                "document_info": {
                    "id": doc.id,
                    "original_filename": doc.original_filename,
                    "s3_key": doc.s3_key,
                    "source": doc.source,
                    "status": doc.status
                },
                "processing_info": {
                    "processed_at": datetime.now().isoformat(),
                    "status": True,
                    "file_type_detected": "test",
                    "language": "en",
                    "confidence_score": 0.9
                },
                "extracted_content": {
                    "text": "This is test extracted text",
                    "text_length": 30
                }
            }
            
            # Test 5: Save document JSON
            safe_filename = "".join(c for c in doc.original_filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_filename = safe_filename.replace(' ', '_')
            json_filename = f"{doc.id:06d}_{safe_filename}_test.json"
            doc_json_path = output_folder / json_filename
            
            with open(doc_json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Document JSON created: {doc_json_path}")
            
            # Test 6: List files in output folder
            files = list(output_folder.glob("*.json"))
            print(f"✅ Files in output folder ({len(files)}):")
            for file in files:
                print(f"   - {file.name}")
                
        else:
            print("❌ No documents found in database")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_json_saving()
