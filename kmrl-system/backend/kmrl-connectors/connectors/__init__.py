"""
Connectors Package
==================

Data source connectors for KMRL document ingestion.

This package provides connectors for:
- Email: IMAP-based email attachment processing
- Maximo: Work order document processing
- SharePoint: Corporate document library integration
- WhatsApp: Field report and mobile document processing

Usage:
    from kmrl_connectors.connectors import EmailConnector, MaximoConnector
"""

from .email_connector import EmailConnector
from .maximo_connector import MaximoConnector
from .sharepoint_connector import SharePointConnector
from .whatsapp_connector import WhatsAppConnector

__all__ = [
    'EmailConnector',
    'MaximoConnector',
    'SharePointConnector',
    'WhatsAppConnector',
]
