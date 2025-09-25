#!/usr/bin/env python3
"""
KMRL System Complete Data Cleanup Script
Clears all data from PostgreSQL, Redis, MinIO, and local storage
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Add backend to path
sys.path.append('.')

def clear_postgresql():
    """Clear all documents and processing logs from PostgreSQL"""
    print("🗑️  CLEARING POSTGRESQL DATABASE...")
    
    try:
        from models.database import get_db
        from models.document import Document, ProcessingLog
        from sqlalchemy import text
        
        # Get database session
        db = next(get_db())
        
        # Check current state
        total_docs = db.query(Document).count()
        print(f"  Current documents in database: {total_docs}")
        
        if total_docs > 0:
            # Clear all documents
            print("  Deleting all documents...")
            db.query(Document).delete()
            db.query(ProcessingLog).delete()
            
            # Commit changes
            db.commit()
            
            # Verify cleanup
            remaining_docs = db.query(Document).count()
            print(f"  Documents remaining after cleanup: {remaining_docs}")
        else:
            print("  Database is already clean")
        
        print("  ✅ PostgreSQL database cleared successfully!")
        db.close()
        
    except Exception as e:
        print(f"  ❌ Error clearing PostgreSQL: {e}")
        return False
    
    return True

def clear_redis():
    """Clear all data from Redis cache"""
    print("🗑️  CLEARING REDIS CACHE...")
    
    try:
        import redis
        
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Check current state
        redis_keys = r.dbsize()
        print(f"  Current Redis keys: {redis_keys}")
        
        if redis_keys > 0:
            # Clear all keys
            r.flushdb()
            print("  ✅ Redis cache cleared successfully!")
        else:
            print("  Redis is already clean")
        
    except Exception as e:
        print(f"  ❌ Error clearing Redis: {e}")
        return False
    
    return True

def clear_minio_data():
    """Clear all user data from MinIO data directory"""
    print("🗑️  CLEARING MINIO DATA...")
    
    try:
        minio_data_path = Path("minio-data")
        
        if minio_data_path.exists():
            # Count files before cleanup
            file_count = len(list(minio_data_path.rglob("*")))
            print(f"  Current files in MinIO data: {file_count}")
            
            if file_count > 0:
                # Remove all user data (keep .minio.sys for MinIO to function)
                for item in minio_data_path.iterdir():
                    if item.name != ".minio.sys":
                        if item.is_dir():
                            shutil.rmtree(item)
                            print(f"    Removed directory: {item.name}")
                        else:
                            item.unlink()
                            print(f"    Removed file: {item.name}")
                
                # Verify cleanup
                remaining_files = len(list(minio_data_path.rglob("*")))
                print(f"  Files remaining after cleanup: {remaining_files}")
                print("  ✅ MinIO data cleared successfully!")
            else:
                print("  MinIO data is already clean")
        else:
            print("  MinIO data directory does not exist")
        
    except Exception as e:
        print(f"  ❌ Error clearing MinIO data: {e}")
        return False
    
    return True

def clear_local_storage():
    """Clear all files from local storage directories"""
    print("🗑️  CLEARING LOCAL STORAGE...")
    
    try:
        storage_path = Path("storage")
        
        if storage_path.exists():
            # Count files before cleanup
            file_count = len(list(storage_path.rglob("*")))
            print(f"  Current files in local storage: {file_count}")
            
            if file_count > 0:
                # Remove all storage directories
                for item in storage_path.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                        print(f"    Removed directory: {item.name}")
                    else:
                        item.unlink()
                        print(f"    Removed file: {item.name}")
                
                # Verify cleanup
                remaining_files = len(list(storage_path.rglob("*")))
                print(f"  Files remaining after cleanup: {remaining_files}")
                print("  ✅ Local storage cleared successfully!")
            else:
                print("  Local storage is already clean")
        else:
            print("  Local storage directory does not exist")
        
    except Exception as e:
        print(f"  ❌ Error clearing local storage: {e}")
        return False
    
    return True

def verify_clean_state():
    """Verify that all data has been cleared"""
    print("🔍 VERIFYING CLEAN STATE...")
    
    try:
        # Check PostgreSQL
        from models.database import get_db
        from models.document import Document
        from sqlalchemy import func
        
        db = next(get_db())
        total_docs = db.query(func.count(Document.id)).scalar()
        print(f"  📊 PostgreSQL Documents: {total_docs}")
        db.close()
        
        # Check Redis
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        redis_keys = r.dbsize()
        print(f"  📊 Redis Keys: {redis_keys}")
        
        # Check local storage
        storage_path = Path("storage")
        if storage_path.exists():
            storage_files = len(list(storage_path.rglob("*")))
            print(f"  📁 Local Storage Files: {storage_files}")
        else:
            print(f"  📁 Local Storage: Directory does not exist (clean)")
        
        # Check MinIO data
        minio_path = Path("minio-data")
        if minio_path.exists():
            minio_files = len(list(minio_path.rglob("*")))
            print(f"  📁 MinIO Data Files: {minio_files}")
        else:
            print(f"  📁 MinIO Data: Directory does not exist (clean)")
        
        print()
        print("  ✅ CLEANUP VERIFICATION COMPLETE!")
        print("  🎯 System is ready for fresh testing!")
        
    except Exception as e:
        print(f"  ❌ Error during verification: {e}")
        return False
    
    return True

def main():
    """Main cleanup function"""
    print("🧹 KMRL SYSTEM COMPLETE DATA CLEANUP")
    print("=" * 50)
    print()
    
    # Track success of each cleanup step
    success_count = 0
    total_steps = 5
    
    # Step 1: Clear PostgreSQL
    if clear_postgresql():
        success_count += 1
    print()
    
    # Step 2: Clear Redis
    if clear_redis():
        success_count += 1
    print()
    
    # Step 3: Clear MinIO data
    if clear_minio_data():
        success_count += 1
    print()
    
    # Step 4: Clear local storage
    if clear_local_storage():
        success_count += 1
    print()
    
    # Step 5: Verify clean state
    if verify_clean_state():
        success_count += 1
    print()
    
    # Final summary
    print("=" * 50)
    if success_count == total_steps:
        print("🎉 ALL CLEANUP STEPS COMPLETED SUCCESSFULLY!")
        print("🚀 System is ready for fresh testing!")
        print()
        print("Next steps:")
        print("1. Restart the KMRL system")
        print("2. Monitor logs for fresh processing")
        print("3. Test file uploads and connectors")
    else:
        print(f"⚠️  {success_count}/{total_steps} cleanup steps completed")
        print("Some cleanup steps may have failed - check the logs above")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
