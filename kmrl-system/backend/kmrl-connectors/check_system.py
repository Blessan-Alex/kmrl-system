#!/usr/bin/env python3
"""
Check Unified System Status
"""

import os
import time
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_system_status():
    """Check if the unified system is running and processing"""
    print("🔍 Checking Unified System Status...")
    
    try:
        # Check Redis connection
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        client = redis.Redis.from_url(redis_url)
        client.ping()
        print("✅ Redis is running")
        
        # Check for active Celery tasks
        try:
            from tasks import celery_app
            
            # Get active tasks
            active_tasks = celery_app.control.inspect().active()
            if active_tasks:
                print(f"✅ Celery has {len(active_tasks)} active workers")
                for worker, tasks in active_tasks.items():
                    print(f"  📊 Worker {worker}: {len(tasks)} tasks")
            else:
                print("⚠️  No active Celery workers found")
            
            # Check scheduled tasks
            scheduled_tasks = celery_app.control.inspect().scheduled()
            if scheduled_tasks:
                print(f"📅 Scheduled tasks: {len(scheduled_tasks)}")
            else:
                print("📅 No scheduled tasks found")
                
        except Exception as e:
            print(f"⚠️  Celery check failed: {e}")
        
        # Check downloads directory
        downloads_dir = "downloads"
        if os.path.exists(downloads_dir):
            files = os.listdir(downloads_dir)
            print(f"📁 Downloads directory: {len(files)} files")
            for file in files:
                print(f"  📄 {file}")
        else:
            print("❌ Downloads directory not found")
        
        # Test manual sync
        print("\n🔍 Testing manual Gmail sync...")
        from connectors.gmail_connector import GmailConnector
        
        connector = GmailConnector("http://localhost:3000")
        if connector._authenticate_gmail():
            print("✅ Gmail authentication working")
            
            credentials = {
                'credentials_file': connector.credentials_file,
                'token_file': connector.token_file
            }
            
            result = connector.sync_incremental(credentials)
            print(f"📊 Sync result: {result}")
        else:
            print("❌ Gmail authentication failed")
        
        return True
        
    except Exception as e:
        print(f"❌ System check failed: {e}")
        return False

if __name__ == "__main__":
    check_system_status()
