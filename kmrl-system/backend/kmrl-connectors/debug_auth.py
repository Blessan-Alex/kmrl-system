#!/usr/bin/env python3
"""
Debug Gmail Authentication
"""

import os
import json
from google.oauth2.credentials import Credentials

# Gmail API scopes
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]

def debug_auth():
    """Debug authentication issue"""
    print("🔍 Debugging Gmail authentication...")
    
    token_file = "token.json"
    
    if not os.path.exists(token_file):
        print(f"❌ Token file not found: {token_file}")
        return
    
    print(f"📁 Token file exists: {token_file}")
    
    # Read token file
    with open(token_file, 'r') as f:
        token_data = json.load(f)
    
    print(f"📄 Token data keys: {list(token_data.keys())}")
    
    # Check for required fields
    required_fields = ['token', 'refresh_token', 'client_id', 'client_secret']
    missing_fields = [field for field in required_fields if field not in token_data]
    
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
    else:
        print("✅ All required fields present")
    
    # Try to create credentials
    try:
        creds = Credentials.from_authorized_user_file(token_file, GMAIL_SCOPES)
        print("✅ Credentials created successfully")
        print(f"📊 Credentials valid: {creds.valid}")
        print(f"📊 Credentials expired: {creds.expired}")
        print(f"📊 Has refresh token: {bool(creds.refresh_token)}")
        
        if creds.expired and creds.refresh_token:
            print("🔄 Token is expired but has refresh token - should be able to refresh")
        elif not creds.valid:
            print("❌ Credentials are not valid")
        else:
            print("✅ Credentials are valid and ready to use")
            
    except Exception as e:
        print(f"❌ Failed to create credentials: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_auth()
