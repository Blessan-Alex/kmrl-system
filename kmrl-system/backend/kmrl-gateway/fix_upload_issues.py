#!/usr/bin/env python3
"""
Fix Upload Issues Script for KMRL Gateway
Identifies and fixes common upload issues
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_server_running():
    """Check if the server is running"""
    try:
        import requests
        response = requests.get("http://localhost:3000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def fix_enhanced_storage_service():
    """Fix issues in enhanced storage service"""
    print("🔧 Fixing enhanced storage service...")
    
    file_path = "services/enhanced_storage_service.py"
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Remove DocumentStatus import if it exists
    if "from models.database_models import Document, DocumentStatus" in content:
        content = content.replace(
            "from models.database_models import Document, DocumentStatus",
            "from models.database_models import Document"
        )
        print("✅ Removed DocumentStatus import")
    
    # Fix 2: Replace any DocumentStatus.QUEUED with "queued"
    if "DocumentStatus.QUEUED" in content:
        content = content.replace("DocumentStatus.QUEUED", '"queued"')
        print("✅ Replaced DocumentStatus.QUEUED with 'queued'")
    
    # Fix 3: Replace any DocumentStatus.PROCESSING with "processing"
    if "DocumentStatus.PROCESSING" in content:
        content = content.replace("DocumentStatus.PROCESSING", '"processing"')
        print("✅ Replaced DocumentStatus.PROCESSING with 'processing'")
    
    # Fix 4: Replace any DocumentStatus.PROCESSED with "processed"
    if "DocumentStatus.PROCESSED" in content:
        content = content.replace("DocumentStatus.PROCESSED", '"processed"')
        print("✅ Replaced DocumentStatus.PROCESSED with 'processed'")
    
    # Fix 5: Replace any DocumentStatus.FAILED with "failed"
    if "DocumentStatus.FAILED" in content:
        content = content.replace("DocumentStatus.FAILED", '"failed"')
        print("✅ Replaced DocumentStatus.FAILED with 'failed'")
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Enhanced storage service fixed")

def fix_document_processor():
    """Fix issues in document processor"""
    print("🔧 Fixing document processor...")
    
    file_path = "services/document_processor.py"
    
    if not os.path.exists(file_path):
        print("⚠️ Document processor not found, skipping")
        return
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix DocumentStatus enum usage
    fixes = [
        ("DocumentStatus.PROCESSING", '"processing"'),
        ("DocumentStatus.PROCESSED", '"processed"'),
        ("DocumentStatus.FAILED", '"failed"'),
        ("DocumentStatus.QUEUED", '"queued"')
    ]
    
    for old, new in fixes:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Replaced {old} with {new}")
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Document processor fixed")

def check_database_connection():
    """Check database connection"""
    print("🔍 Checking database connection...")
    
    try:
        # Try to import and test database connection
        from models.database import engine, create_tables
        
        # Test connection
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Create tables if they don't exist
        create_tables()
        print("✅ Database tables created/verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_redis_connection():
    """Check Redis connection"""
    print("🔍 Checking Redis connection...")
    
    try:
        import redis
        r = redis.Redis.from_url('redis://localhost:6379')
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def check_minio_connection():
    """Check MinIO connection"""
    print("🔍 Checking MinIO connection...")
    
    try:
        from minio import Minio
        client = Minio(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        
        # Try to list buckets
        buckets = client.list_buckets()
        print("✅ MinIO connection successful")
        return True
    except Exception as e:
        print(f"❌ MinIO connection failed: {e}")
        print("⚠️ MinIO not available, will use local storage fallback")
        return False

def run_tests():
    """Run the test scripts"""
    print("🧪 Running tests...")
    
    # Run simple upload test
    print("\n1️⃣ Running simple upload test...")
    try:
        result = subprocess.run([sys.executable, "test_simple_upload.py"], 
                               capture_output=True, text=True, timeout=60)
        print("Simple upload test output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Simple upload test timed out")
        return False
    except Exception as e:
        print(f"❌ Simple upload test failed: {e}")
        return False

def main():
    """Main fix function"""
    print("🔧 KMRL Gateway Upload Issues Fix Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("services/enhanced_storage_service.py"):
        print("❌ Not in the correct directory. Please run from kmrl-gateway directory.")
        sys.exit(1)
    
    # Fix code issues
    fix_enhanced_storage_service()
    fix_document_processor()
    
    # Check connections
    db_ok = check_database_connection()
    redis_ok = check_redis_connection()
    minio_ok = check_minio_connection()
    
    print(f"\n📊 Connection Status:")
    print(f"Database: {'✅' if db_ok else '❌'}")
    print(f"Redis: {'✅' if redis_ok else '❌'}")
    print(f"MinIO: {'✅' if minio_ok else '❌'}")
    
    if not db_ok:
        print("\n❌ Database connection failed. Please check PostgreSQL.")
        print("Try: sudo service postgresql start")
        sys.exit(1)
    
    if not redis_ok:
        print("\n❌ Redis connection failed. Please check Redis.")
        print("Try: sudo service redis-server start")
        sys.exit(1)
    
    # Check if server is running
    if not check_server_running():
        print("\n⚠️ Server not running. Please start the server first:")
        print("python3 -m uvicorn app_enhanced:app --host 0.0.0.0 --port 3000 --log-level info")
        return
    
    # Run tests
    print("\n🧪 Running upload tests...")
    test_success = run_tests()
    
    if test_success:
        print("\n🎉 All fixes applied and tests passed!")
    else:
        print("\n❌ Tests failed. Check the output above for issues.")
    
    print("\n📋 Next steps:")
    print("1. If server is not running, start it with the command above")
    print("2. Run: python3 test_simple_upload.py")
    print("3. Run: python3 test_upload_api.py (for comprehensive testing)")

if __name__ == "__main__":
    main()
