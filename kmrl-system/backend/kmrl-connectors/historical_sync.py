#!/usr/bin/env python3
"""
Historical Gmail Sync
Download older emails with attachments
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_historical_sync(days_back=30):
    """Run historical sync for Gmail"""
    print(f"🔄 Running historical Gmail sync for last {days_back} days...")
    
    try:
        from connectors.gmail_connector import GmailConnector
        
        # Create connector
        api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        connector = GmailConnector(api_endpoint)
        
        # Test authentication
        if not connector._authenticate_gmail():
            print("❌ Authentication failed")
            return False
        
        print("✅ Authentication successful")
        
        # Run historical sync
        credentials = {
            'credentials_file': connector.credentials_file,
            'token_file': connector.token_file
        }
        
        print(f"📥 Running historical sync for {days_back} days...")
        result = connector.sync_historical(credentials, days_back=days_back)
        
        print(f"📊 Historical sync completed: {result}")
        
        # Check downloads
        downloads_dir = "downloads"
        if os.path.exists(downloads_dir):
            files = os.listdir(downloads_dir)
            print(f"📁 Downloads folder now has {len(files)} files:")
            for file in files:
                file_path = os.path.join(downloads_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"  📄 {file} ({file_size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Historical sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_historical_sync():
    """Run historical sync for all connectors"""
    print("🔄 Running historical sync for all connectors...")
    
    try:
        from tasks import sync_all_historical
        
        # Run historical sync for all connectors
        result = sync_all_historical.delay(30)  # 30 days back
        
        print("📊 Historical sync task queued...")
        print(f"📋 Task ID: {result.id}")
        
        # Wait for completion
        print("⏳ Waiting for completion...")
        try:
            final_result = result.get(timeout=1800)  # 30 minutes timeout
            print(f"✅ Historical sync completed: {final_result}")
        except Exception as e:
            print(f"⚠️  Task completed with issues: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Historical sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Historical Gmail Sync Options:")
    print("1. Gmail only (last 30 days)")
    print("2. Gmail only (last 7 days)")
    print("3. Gmail only (last 90 days)")
    print("4. All connectors (last 30 days)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        run_historical_sync(30)
    elif choice == "2":
        run_historical_sync(7)
    elif choice == "3":
        run_historical_sync(90)
    elif choice == "4":
        run_all_historical_sync()
    else:
        print("❌ Invalid choice, running default (30 days)")
        run_historical_sync(30)
