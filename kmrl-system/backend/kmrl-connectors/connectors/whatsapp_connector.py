"""
WhatsApp Business Connector for KMRL Field Reports
Handles mobile document uploads and field worker communications
"""

import requests
from typing import List, Dict, Any
import structlog
from datetime import datetime
from base.base_connector import BaseConnector, Document

logger = structlog.get_logger()

class WhatsAppConnector(BaseConnector):
    """WhatsApp Business API connector for KMRL field reports"""
    
    def __init__(self, phone_number_id: str):
        super().__init__("whatsapp", "http://localhost:3000")
        self.phone_number_id = phone_number_id
    
    def fetch_documents(self, credentials: Dict[str, str], 
                       options: Dict[str, Any] = None) -> List[Document]:
        """Fetch WhatsApp Business messages with documents"""
        options = options or {}
        
        try:
            headers = {"Authorization": f"Bearer {credentials['access_token']}"}
            
            # Get messages since last sync
            last_sync = self.get_last_sync_time()
            params = {
                "fields": "id,from,type,timestamp,media,text,context",
                "since": int(last_sync.timestamp()),
                "limit": 100  # Limit results
            }
            
            response = requests.get(
                f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"WhatsApp API request failed: {response.status_code} - {response.text}")
            
            messages = response.json().get("data", [])
            documents = []
            
            for message in messages:
                if message.get("type") == "document" and message.get("media"):
                    media_id = message["media"]["id"]
                    
                    # Check if already processed
                    if self.is_document_processed(media_id):
                        continue
                    
                    try:
                        # Get media URL with enhanced fields
                        media_response = requests.get(
                            f"https://graph.facebook.com/v18.0/{media_id}",
                            headers=headers,
                            params={"fields": "url,mime_type,file_size,sha256"},
                            timeout=30
                        )
                        
                        if media_response.status_code == 200:
                            media_data = media_response.json()
                            
                            # Download file
                            file_response = requests.get(
                                media_data["url"], 
                                headers=headers,
                                timeout=60
                            )
                            
                            if file_response.status_code == 200:
                                # Extract filename from media data or use default
                                filename = self.extract_filename(media_data, media_id)
                                
                                # Detect language from message text
                                message_text = message.get("text", "")
                                language = self.detect_language(message_text)
                                
                                # Classify department based on message content
                                department = self.classify_department(message_text, message.get("from", ""))
                                
                                document = Document(
                                    source="whatsapp",
                                    filename=filename,
                                    content=file_response.content,
                                    content_type=media_data.get("mime_type", "application/octet-stream"),
                                    metadata={
                                        "message_id": message["id"],
                                        "from": message["from"],
                                        "timestamp": message["timestamp"],
                                        "media_id": media_id,
                                        "message_text": message_text,
                                        "file_size": media_data.get("file_size", 0),
                                        "sha256": media_data.get("sha256", ""),
                                        "context": message.get("context", {}),
                                        "department": department
                                    },
                                    document_id=media_id,
                                    uploaded_at=datetime.now(),
                                    language=language
                                )
                                
                                documents.append(document)
                            else:
                                logger.warning(f"Failed to download media {media_id}: {file_response.status_code}")
                                
                        else:
                            logger.warning(f"Failed to get media info {media_id}: {media_response.status_code}")
                            
                    except requests.exceptions.Timeout:
                        logger.warning(f"Timeout processing media {media_id}")
                    except Exception as e:
                        logger.warning(f"Error processing media {media_id}: {e}")
            
            logger.info("WhatsApp documents fetched", count=len(documents))
            return documents
            
        except Exception as e:
            logger.error("WhatsApp connector error", error=str(e))
            raise Exception(f"WhatsApp connector failed: {str(e)}")
    
    def extract_filename(self, media_data: Dict[str, Any], media_id: str) -> str:
        """Extract filename from media data"""
        # Try to get filename from URL or use media_id
        url = media_data.get("url", "")
        if url and "/" in url:
            filename = url.split("/")[-1]
            if "." in filename:
                return filename
        
        # Use media_id as fallback
        return f"whatsapp_{media_id}"
    
    def detect_language(self, text: str) -> str:
        """Detect language from message text"""
        if not text:
            return "unknown"
        
        # Malayalam Unicode range
        malayalam_chars = "അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹളഴറ"
        
        malayalam_count = sum(1 for char in text if char in malayalam_chars)
        english_count = sum(1 for char in text if char.isalpha() and char not in malayalam_chars)
        
        if malayalam_count > 0 and english_count > 0:
            return "mixed"
        elif malayalam_count > 0:
            return "malayalam"
        elif english_count > 0:
            return "english"
        else:
            return "unknown"
    
    def classify_department(self, message_text: str, sender: str) -> str:
        """Classify department based on message content and sender"""
        text_lower = message_text.lower()
        
        # Field operations keywords
        field_keywords = [
            "field", "site", "station", "platform", "track", "train",
            "passenger", "service", "delay", "incident", "report"
        ]
        
        # Safety keywords
        safety_keywords = [
            "safety", "emergency", "accident", "incident", "hazard",
            "evacuation", "fire", "smoke", "alarm"
        ]
        
        # Operations keywords
        operations_keywords = [
            "schedule", "timetable", "service", "operation", "control",
            "dispatch", "signal", "power", "communication"
        ]
        
        if any(keyword in text_lower for keyword in safety_keywords):
            return "safety"
        elif any(keyword in text_lower for keyword in operations_keywords):
            return "operations"
        elif any(keyword in text_lower for keyword in field_keywords):
            return "field_operations"
        else:
            return "field_operations"  # Default for WhatsApp
