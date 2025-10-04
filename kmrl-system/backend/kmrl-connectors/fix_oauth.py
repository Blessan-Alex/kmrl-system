#!/usr/bin/env python3
"""
Fix OAuth Token Issue
Re-authenticate with proper offline access to get refresh_token
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]

def fix_oauth_token():
    """Fix OAuth token with proper offline access"""
    print("🔧 Fixing OAuth token with offline access...")
    
    # Paths
    credentials_file = "credentials.json"
    token_file = "token.json"
    
    # Load credentials
    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file not found: {credentials_file}")
        return False
    
    try:
        # Create flow with offline access
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file, 
            GMAIL_SCOPES
        )
        
        # Set redirect URI
        flow.redirect_uri = "http://localhost:8080"
        
        print("🌐 Starting OAuth flow with offline access...")
        print("📱 This will open your browser for authorization...")
        
        # Run the flow
        creds = flow.run_local_server(port=8080, access_type='offline', prompt='consent')
        
        # Save the credentials
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        
        print("✅ OAuth token fixed successfully!")
        print(f"📁 Token saved to: {token_file}")
        
        # Verify the token has refresh_token
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        if 'refresh_token' in token_data:
            print("✅ Refresh token is present")
            return True
        else:
            print("❌ Refresh token is missing")
            return False
            
    except Exception as e:
        print(f"❌ OAuth flow failed: {e}")
        return False

if __name__ == "__main__":
    fix_oauth_token()
