"""
KMRL Connectors Package
======================

Automatic document ingestion from multiple data sources for KMRL Knowledge Hub.

This package provides connectors for:
- Email (IMAP)
- Maximo (Work Orders)
- SharePoint (Corporate Documents)
- WhatsApp (Field Reports)

Usage:
    from kmrl_connectors import EmailConnector, MaximoConnector
    from kmrl_connectors.scheduler import celery_app
"""

__version__ = "1.0.0"
__author__ = "KMRL Development Team"
__email__ = "dev@kmrl.com"

# Import main connectors for easy access
from .connectors.email_connector import EmailConnector
from .connectors.maximo_connector import MaximoConnector
from .connectors.sharepoint_connector import SharePointConnector
from .connectors.whatsapp_connector import WhatsAppConnector

# Import base connector
from .base.base_connector import BaseConnector, Document

# Import scheduler
from .scheduler import celery_app

# Import utilities
from .utils.credentials_manager import CredentialsManager

__all__ = [
    # Connectors
    'EmailConnector',
    'MaximoConnector', 
    'SharePointConnector',
    'WhatsAppConnector',
    
    # Base classes
    'BaseConnector',
    'Document',
    
    # Scheduler
    'celery_app',
    
    # Utilities
    'CredentialsManager',
]
