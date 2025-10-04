#!/usr/bin/env python3
"""
Simple Historical Gmail Sync
Bypass datetime issues and download attachments directly
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def simple_historical_sync():
    """Simple historical sync that bypasses datetime issues"""
    print("🔄 Running simple historical Gmail sync...")
    
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
        
        # Get Gmail service
        service = connector._get_gmail_service()
        if not service:
            print("❌ Failed to get Gmail service")
            return False
        
        print("✅ Gmail service connected")
        
        # Search for emails with attachments (last 30 days)
        print("📧 Searching for emails with attachments...")
        
        # Calculate date 30 days ago
        thirty_days_ago = datetime.now() - timedelta(days=30)
        date_str = thirty_days_ago.strftime('%Y/%m/%d')
        
        # Search query
        query = f"has:attachment after:{date_str}"
        print(f"🔍 Search query: {query}")
        
        # Search for messages
        results = service.users().messages().list(userId='me', q=query, maxResults=50).execute()
        messages = results.get('messages', [])
        
        print(f"📊 Found {len(messages)} emails with attachments")
        
        if not messages:
            print("❌ No emails with attachments found")
            return False
        
        # Process first few messages to avoid too many API calls
        processed = 0
        downloaded = 0
        
        for i, message in enumerate(messages[:10]):  # Process first 10 messages
            try:
                print(f"📧 Processing email {i+1}/10...")
                
                # Get message details
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                
                # Get attachments
                payload = msg.get('payload', {})
                parts = payload.get('parts', [])
                
                if not parts:
                    continue
                
                # Process each part
                for part in parts:
                    if part.get('filename'):
                        filename = part.get('filename')
                        print(f"  📎 Found attachment: {filename}")
                        
                        # Get attachment data
                        attachment_id = part.get('body', {}).get('attachmentId')
                        if attachment_id:
                            try:
                                attachment = service.users().messages().attachments().get(
                                    userId='me', 
                                    messageId=message['id'], 
                                    id=attachment_id
                                ).execute()
                                
                                # Decode attachment data
                                import base64
                                data = attachment.get('data')
                                if data:
                                    file_data = base64.urlsafe_b64decode(data)
                                    
                                    # Save to downloads folder
                                    downloads_dir = "downloads"
                                    os.makedirs(downloads_dir, exist_ok=True)
                                    
                                    file_path = os.path.join(downloads_dir, filename)
                                    with open(file_path, 'wb') as f:
                                        f.write(file_data)
                                    
                                    print(f"  ✅ Downloaded: {filename} ({len(file_data)} bytes)")
                                    downloaded += 1
                                    
                            except Exception as e:
                                print(f"  ❌ Failed to download {filename}: {e}")
                
                processed += 1
                
            except Exception as e:
                print(f"  ❌ Failed to process email {i+1}: {e}")
                continue
        
        print(f"\n📊 Summary:")
        print(f"  📧 Emails processed: {processed}")
        print(f"  📎 Attachments downloaded: {downloaded}")
        
        # Check downloads folder
        downloads_dir = "downloads"
        if os.path.exists(downloads_dir):
            files = os.listdir(downloads_dir)
            print(f"  📁 Total files in downloads: {len(files)}")
            for file in files:
                file_path = os.path.join(downloads_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"    📄 {file} ({file_size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple historical sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    simple_historical_sync()
