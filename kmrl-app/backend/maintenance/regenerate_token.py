#!/usr/bin/env python3
"""
Regenerate OAuth2 token with correct scopes for Gmail and Google Drive
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Required scopes for both Gmail and Google Drive
REQUIRED_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file'
]

def regenerate_token():
    """Regenerate OAuth2 token with correct scopes"""
    print("🔄 Regenerating OAuth2 token with correct scopes...")
    
    credentials_file = 'credentials.json'
    token_file = 'token.json'
    
    # Check if credentials file exists
    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file not found: {credentials_file}")
        return False
    
    try:
        # Delete existing token to force re-authentication
        if os.path.exists(token_file):
            os.remove(token_file)
            print("🗑️  Removed existing token file")
        
        # Start OAuth2 flow
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file, 
            REQUIRED_SCOPES
        )
        
        print("🌐 Starting OAuth2 flow...")
        print("📋 Requested scopes:")
        for scope in REQUIRED_SCOPES:
            print(f"   - {scope}")
        
        # Run local server for OAuth2
        creds = flow.run_local_server(port=8081)
        
        # Save the new token
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        
        print("✅ Token regenerated successfully!")
        
        # Verify the token has correct scopes
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        token_scopes = token_data.get('scopes', [])
        print(f"📄 Token scopes: {token_scopes}")
        
        # Check if all required scopes are present
        missing_scopes = [scope for scope in REQUIRED_SCOPES if scope not in token_scopes]
        if missing_scopes:
            print(f"⚠️  Missing scopes: {missing_scopes}")
            return False
        else:
            print("✅ All required scopes present in token")
            return True
        
    except Exception as e:
        print(f"❌ Token regeneration failed: {e}")
        return False

def test_authentication():
    """Test authentication with the new token"""
    print("🧪 Testing authentication...")
    
    try:
        # Test Gmail authentication
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        
        creds = Credentials.from_authorized_user_file('token.json', REQUIRED_SCOPES)
        
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
        
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
        print(f"❌ Authentication test failed: {e}")
        return False

def main():
    """Main function"""
    print("🔧 OAuth2 Token Regeneration Tool")
    print("=" * 50)
    print("This will regenerate the OAuth2 token with correct scopes")
    print("for both Gmail and Google Drive APIs.")
    print("=" * 50)
    
    # Regenerate token
    if regenerate_token():
        print("\n🧪 Testing authentication...")
        if test_authentication():
            print("\n🎉 Token regeneration and authentication successful!")
            print("The connectors should now work correctly.")
        else:
            print("\n⚠️  Token regeneration succeeded but authentication test failed.")
    else:
        print("\n❌ Token regeneration failed.")

if __name__ == "__main__":
    main()
