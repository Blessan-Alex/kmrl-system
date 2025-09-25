#!/usr/bin/env python3
"""
Create a proper OAuth2 token with refresh_token
"""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Required scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file'
]

def create_proper_token():
    """Create a proper OAuth2 token with refresh_token"""
    print("🔧 Creating proper OAuth2 token with refresh_token...")
    
    credentials_file = 'credentials.json'
    token_file = 'token.json'
    
    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file not found: {credentials_file}")
        return False
    
    try:
        # Delete existing token
        if os.path.exists(token_file):
            os.remove(token_file)
            print("🗑️  Removed existing token")
        
        # Create OAuth2 flow with offline access
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file, 
            SCOPES
        )
        
        # Configure for offline access to get refresh token
        flow.redirect_uri = 'http://localhost:8081/'
        
        print("🌐 Starting OAuth2 flow with offline access...")
        print("📋 This will open a browser window for authorization")
        print("📋 Make sure to grant all requested permissions")
        print("📋 The app needs offline access to get a refresh token")
        
        # Run the flow
        creds = flow.run_local_server(port=8081, access_type='offline', prompt='consent')
        
        # Save the credentials
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        
        print("✅ Token created successfully!")
        
        # Verify the token has refresh_token
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        if 'refresh_token' in token_data:
            print("✅ Refresh token present in token")
        else:
            print("❌ Refresh token missing from token")
            return False
        
        print(f"📄 Token scopes: {token_data.get('scopes', [])}")
        print(f"⏰ Token expires: {token_data.get('expiry', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Token creation failed: {e}")
        return False

def test_token():
    """Test the created token"""
    print("🧪 Testing created token...")
    
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        
        # Load credentials
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # Refresh if needed
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired token...")
                creds.refresh(Request())
            else:
                print("❌ Token is invalid and cannot be refreshed")
                return False
        
        # Test Gmail API
        gmail_service = build('gmail', 'v1', credentials=creds)
        profile = gmail_service.users().getProfile(userId='me').execute()
        print(f"✅ Gmail API test successful - User: {profile.get('emailAddress')}")
        
        # Test Google Drive API
        drive_service = build('drive', 'v3', credentials=creds)
        about = drive_service.about().get(fields='user').execute()
        print(f"✅ Google Drive API test successful - User: {about.get('user', {}).get('displayName')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Token test failed: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Proper OAuth2 Token Creation")
    print("=" * 50)
    print("This will create a proper OAuth2 token with refresh_token")
    print("You will need to authorize the application in your browser")
    print("=" * 50)
    
    if create_proper_token():
        print("\n🧪 Testing token...")
        if test_token():
            print("\n🎉 Token creation and testing successful!")
            print("The connectors should now work correctly.")
        else:
            print("\n⚠️  Token creation succeeded but testing failed.")
    else:
        print("\n❌ Token creation failed.")

if __name__ == "__main__":
    main()
