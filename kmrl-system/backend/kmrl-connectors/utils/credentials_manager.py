"""
Credentials Manager for KMRL Connectors
Handles secure credential storage and retrieval
"""

import os
from typing import Dict, str

class CredentialsManager:
    """Manages credentials for all KMRL data sources"""
    
    def get_email_credentials(self) -> Dict[str, str]:
        """Get email credentials from environment"""
        return {
            "email": os.getenv("EMAIL_USER"),
            "password": os.getenv("EMAIL_PASSWORD")
        }
    
    def get_email_imap_host(self) -> str:
        """Get email IMAP host"""
        return os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com")
    
    def get_email_imap_port(self) -> int:
        """Get email IMAP port"""
        return int(os.getenv("EMAIL_IMAP_PORT", "993"))
    
    def get_maximo_credentials(self) -> Dict[str, str]:
        """Get Maximo credentials"""
        return {
            "username": os.getenv("MAXIMO_USERNAME"),
            "password": os.getenv("MAXIMO_PASSWORD")
        }
    
    def get_maximo_base_url(self) -> str:
        """Get Maximo base URL"""
        return os.getenv("MAXIMO_BASE_URL")
    
    def get_sharepoint_credentials(self) -> Dict[str, str]:
        """Get SharePoint credentials"""
        return {
            "client_id": os.getenv("SHAREPOINT_CLIENT_ID"),
            "client_secret": os.getenv("SHAREPOINT_CLIENT_SECRET")
        }
    
    def get_sharepoint_site_url(self) -> str:
        """Get SharePoint site URL"""
        return os.getenv("SHAREPOINT_SITE_URL")
    
    def get_whatsapp_credentials(self) -> Dict[str, str]:
        """Get WhatsApp credentials"""
        return {
            "access_token": os.getenv("WHATSAPP_ACCESS_TOKEN")
        }
    
    def get_whatsapp_phone_number_id(self) -> str:
        """Get WhatsApp phone number ID"""
        return os.getenv("WHATSAPP_PHONE_NUMBER_ID")
