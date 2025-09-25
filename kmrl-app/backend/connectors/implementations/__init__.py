"""
Unified Connectors Package for KMRL Document Ingestion
======================================================

Data source connectors implementing the enhanced base connector architecture.
All connectors support incremental sync, historical processing, and unified document handling.

This package provides connectors for:
- Gmail: Gmail API-based email attachment processing
- Google Drive: Google Drive API-based file processing
- Maximo: Maximo API-based work order document processing
- WhatsApp: WhatsApp Cloud API-based message processing

Usage:
    from kmrl_connectors.connectors import GmailConnector, GoogleDriveConnector, MaximoConnector, WhatsAppConnector
    
    # Initialize connectors
    api_endpoint = "http://localhost:3000"
    gmail_connector = GmailConnector(api_endpoint)
    gdrive_connector = GoogleDriveConnector(api_endpoint)
    maximo_connector = MaximoConnector(api_endpoint)
    whatsapp_connector = WhatsAppConnector(api_endpoint)
    
    # Perform incremental sync
    gmail_connector.sync_incremental(credentials)
    
    # Perform historical sync
    gmail_connector.sync_historical(credentials, days_back=30)
"""

from .gmail_connector import GmailConnector
from .gdrive_connector import GoogleDriveConnector
from .maximo_connector import MaximoConnector
from .whatsapp_connector import WhatsAppConnector

# Legacy imports for backward compatibility
from .email_connector import EmailConnector
from .google_drive_connector import GoogleDriveConnector as LegacyGoogleDriveConnector

__all__ = [
    'GmailConnector',
    'GoogleDriveConnector', 
    'MaximoConnector',
    'WhatsAppConnector',
    # Legacy exports
    'EmailConnector',
    'LegacyGoogleDriveConnector',
]
