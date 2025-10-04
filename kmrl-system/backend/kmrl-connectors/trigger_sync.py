#!/usr/bin/env python3
"""
Trigger Manual Sync
Test the system by running a manual sync
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def trigger_manual_sync():
    """Trigger a manual Gmail sync"""
    print("🔄 Triggering manual Gmail sync...")
    
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
        
        # Run sync
        credentials = {
            'credentials_file': connector.credentials_file,
            'token_file': connector.token_file
        }
        
        print("📥 Running Gmail sync...")
        result = connector.sync_incremental(credentials)
        
        print(f"📊 Sync completed: {result}")
        
        # Check downloads
        downloads_dir = "downloads"
        if os.path.exists(downloads_dir):
            files = os.listdir(downloads_dir)
            print(f"📁 Downloads folder now has {len(files)} files:")
            for file in files:
                print(f"  📄 {file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    trigger_manual_sync()
