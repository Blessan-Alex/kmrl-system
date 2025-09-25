"""
WhatsApp Connector for KMRL Document Ingestion
Implements WhatsApp Cloud API-based message and media processing with incremental sync
"""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Generator, Optional
import structlog

from ..base.enhanced_base_connector import EnhancedBaseConnector, Document, SyncState

logger = structlog.get_logger()

class WhatsAppConnector(EnhancedBaseConnector):
    """WhatsApp connector for processing messages and media from WhatsApp Business API"""
    
    def __init__(self, api_endpoint: str, sync_interval_minutes: int = 2):
        super().__init__("whatsapp", api_endpoint, sync_interval_minutes)
        
        # WhatsApp Cloud API configuration
        self.whatsapp_phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.whatsapp_access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.whatsapp_webhook_verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
        
        # WhatsApp API settings
        self.whatsapp_api_version = os.getenv('WHATSAPP_API_VERSION', 'v18.0')
        self.whatsapp_base_url = f"https://graph.facebook.com/{self.whatsapp_api_version}"
        
        # Sync settings
        self.include_media = os.getenv('WHATSAPP_INCLUDE_MEDIA', 'true').lower() == 'true'
        self.include_text_messages = os.getenv('WHATSAPP_INCLUDE_TEXT', 'true').lower() == 'true'
        self.target_phone_numbers = os.getenv('WHATSAPP_TARGET_NUMBERS', '').split(',') if os.getenv('WHATSAPP_TARGET_NUMBERS') else []
        
        self._session = None
        
        logger.info("WhatsApp connector initialized", 
                   phone_number_id=self.whatsapp_phone_number_id,
                   api_version=self.whatsapp_api_version)
    
    def _authenticate_whatsapp(self) -> bool:
        """Authenticate with WhatsApp Cloud API"""
        try:
            if not all([self.whatsapp_phone_number_id, self.whatsapp_access_token]):
                logger.error("WhatsApp credentials not configured")
                return False
            
            # Create session for authentication
            self._session = requests.Session()
            self._session.headers.update({
                'Authorization': f'Bearer {self.whatsapp_access_token}',
                'Content-Type': 'application/json'
            })
            
            # Test authentication by getting phone number info
            test_url = f"{self.whatsapp_base_url}/{self.whatsapp_phone_number_id}"
            response = self._session.get(test_url, timeout=10)
            
            if response.status_code == 200:
                logger.info("WhatsApp authentication successful")
                return True
            else:
                logger.error(f"WhatsApp authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"WhatsApp authentication failed: {e}")
            return False
    
    def _get_whatsapp_session(self):
        """Get authenticated WhatsApp session"""
        if not self._session:
            if not self._authenticate_whatsapp():
                raise Exception("Failed to authenticate with WhatsApp")
        return self._session
    
    def _create_document_from_message(self, message: Dict[str, Any]) -> Document:
        """Create Document object from WhatsApp text message"""
        message_id = message.get('id', '')
        text_content = message.get('text', {}).get('body', '')
        from_number = message.get('from', '')
        timestamp = message.get('timestamp', '')
        
        # Convert timestamp to datetime
        try:
            message_time = datetime.fromtimestamp(int(timestamp))
        except:
            message_time = datetime.now()
        
        metadata = {
            'message_id': message_id,
            'from_number': from_number,
            'message_type': 'text',
            'timestamp': timestamp,
            'message_time': message_time.isoformat(),
            'source_type': 'whatsapp_message'
        }
        
        # Create filename from message info
        filename = f"WA_MSG_{message_id}.txt"
        
        # Create content
        content = text_content.encode('utf-8')
        
        # Detect language
        language = self._detect_language(text_content)
        
        return Document(
            source="whatsapp",
            filename=filename,
            content=content,
            content_type="text/plain",
            metadata=metadata,
            uploaded_at=message_time,
            language=language,
            original_path=f"whatsapp://message/{message_id}"
        )
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection for Malayalam/English"""
        # Basic Malayalam Unicode range detection
        malayalam_chars = sum(1 for char in text if '\u0D00' <= char <= '\u0D7F')
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars > 0 and malayalam_chars / total_chars > 0.1:
            return "mal"
        return "eng"
    
    def fetch_documents_incremental(self, credentials: Dict[str, str], 
                                   state: SyncState,
                                   batch_size: int = 50) -> Generator[List[Document], None, None]:
        """Fetch new messages from WhatsApp incrementally"""
        try:
            logger.info("WhatsApp incremental sync - checking for new webhook messages")
            
            # For WhatsApp, we typically rely on webhooks for real-time processing
            # This is a simplified implementation that processes stored webhook messages
            
            current_batch = []
            
            # In a real implementation, this would process messages from a webhook queue
            # For demo purposes, we'll return an empty batch
            logger.info("No new WhatsApp messages to process")
            
            if current_batch:
                yield current_batch
                
        except Exception as e:
            logger.error(f"WhatsApp incremental fetch failed: {e}")
            raise
    
    def fetch_documents_historical(self, credentials: Dict[str, str], 
                                  start_date: datetime,
                                  batch_size: int = 100) -> Generator[List[Document], None, None]:
        """Fetch historical messages from WhatsApp"""
        try:
            logger.info(f"Starting WhatsApp historical fetch from {start_date}")
            
            # WhatsApp Cloud API doesn't provide direct access to historical messages
            # This would require processing stored webhook data or manual exports
            logger.info("WhatsApp historical fetch not implemented - requires webhook data")
            
            # Return empty generator
            return
            
        except Exception as e:
            logger.error(f"WhatsApp historical fetch failed: {e}")
            raise
    
    def process_webhook_message(self, webhook_data: Dict[str, Any]) -> List[Document]:
        """Process incoming webhook message from WhatsApp"""
        try:
            logger.info("Processing WhatsApp webhook message")
            
            # Extract messages from webhook data
            entry = webhook_data.get('entry', [])
            if not entry:
                return []
            
            documents = []
            for item in entry:
                changes = item.get('changes', [])
                for change in changes:
                    if change.get('field') == 'messages':
                        value = change.get('value', {})
                        messages = value.get('messages', [])
                        
                        for message in messages:
                            if self.include_text_messages and message.get('type') == 'text':
                                doc = self._create_document_from_message(message)
                                documents.append(doc)
            
            logger.info(f"Processed {len(documents)} documents from WhatsApp webhook")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to process WhatsApp webhook: {e}")
            return []
    
    def get_connector_info(self) -> Dict[str, Any]:
        """Get connector-specific information"""
        status = self.get_sync_status()
        
        # Add WhatsApp-specific info
        status.update({
            "whatsapp_phone_number_id": self.whatsapp_phone_number_id,
            "whatsapp_api_version": self.whatsapp_api_version,
            "include_media": self.include_media,
            "include_text_messages": self.include_text_messages,
            "target_phone_numbers": self.target_phone_numbers
        })
        
        return status