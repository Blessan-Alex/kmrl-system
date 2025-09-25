"""
Base Connector Architecture for KMRL Document Ingestion
Solves the problem of scattered documents across multiple sources
"""

from abc import ABC, abstractmethod
import redis
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import structlog
from dataclasses import dataclass

# Real Redis client - no mocks!

logger = structlog.get_logger()

@dataclass
class Document:
    """Unified document model for all KMRL sources"""
    source: str
    filename: str
    content: bytes
    content_type: str
    metadata: Dict[str, Any]
    document_id: Optional[str] = None
    uploaded_at: datetime = None
    language: str = "unknown"  # For Malayalam/English detection

class BaseConnector(ABC):
    """Base class for all KMRL data source connectors"""
    
    def __init__(self, source_name: str, api_endpoint: str):
        self.source_name = source_name
        self.api_endpoint = api_endpoint
        self.redis_client = None
        self.state_key = f"connector_state:{source_name.lower()}"
        self.processed_key = f"processed_docs:{source_name.lower()}"
        
        # Connect to real Redis - no fallbacks!
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis_client = redis.Redis.from_url(redis_url)
            self.redis_client.ping()  # Test connection
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise Exception(f"Redis connection required but failed: {e}")
    
    def get_last_sync_time(self) -> datetime:
        """Get last successful sync time from Redis"""
        last_sync = self.redis_client.get(self.state_key)
        if last_sync:
            return datetime.fromisoformat(last_sync.decode())
        return datetime.min
    
    def update_sync_time(self, sync_time: datetime):
        """Update last successful sync time"""
        self.redis_client.set(self.state_key, sync_time.isoformat())
    
    def mark_document_processed(self, document_id: str):
        """Mark document as processed to avoid duplicates"""
        self.redis_client.sadd(self.processed_key, document_id)
    
    def is_document_processed(self, document_id: str) -> bool:
        """Check if document was already processed"""
        return self.redis_client.sismember(self.processed_key, document_id)
    
    def upload_to_api(self, document: Document) -> Dict[str, Any]:
        """Upload document to unified KMRL API"""
        import requests
        import tempfile
        import os
        
        try:
            # Create a temporary file from the document content
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{document.filename}") as temp_file:
                temp_file.write(document.content)
                temp_file_path = temp_file.name
            
            try:
                # Open the temporary file for upload
                with open(temp_file_path, 'rb') as file_obj:
                    files = {
                        'file': (document.filename, file_obj, document.content_type)
                    }
                    
                    data = {
                        'source': document.source,
                        'metadata': json.dumps(document.metadata),
                        'uploaded_by': 'system',
                        'language': document.language
                    }
                    
                    response = requests.post(
                        f"{self.api_endpoint}/api/v1/documents/upload",
                        files=files,
                        data=data,
                        headers={'X-API-Key': self.get_api_key()}
                    )
                    
                    if response.status_code == 200:
                        logger.info("Document uploaded successfully", 
                                   source=document.source, 
                                   filename=document.filename)
                        return response.json()
                    else:
                        logger.error("Document upload failed", 
                                    status=response.status_code,
                                    response=response.text)
                        raise Exception(f"Upload failed: {response.text}")
                        
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Upload error: {e}")
            raise
    
    def get_api_key(self) -> str:
        """Get API key for authentication"""
        api_key = self.redis_client.get("kmrl_api_key")
        if api_key:
            return api_key.decode()
        return "kmrl-api-key-2024"  # Default fallback
    
    @abstractmethod
    def fetch_documents(self, credentials: Dict[str, str], 
                       options: Dict[str, Any] = None) -> List[Document]:
        """Fetch documents from source system"""
        pass
    
    def sync_documents(self, credentials: Dict[str, str], 
                      options: Dict[str, Any] = None):
        """Main sync method - runs periodically"""
        try:
            logger.info(f"Starting sync for {self.source_name}")
            
            # Fetch new documents
            documents = self.fetch_documents(credentials, options)
            
            # Upload each document
            for doc in documents:
                if not self.is_document_processed(doc.document_id):
                    self.upload_to_api(doc)
                    self.mark_document_processed(doc.document_id)
            
            # Update sync time
            self.update_sync_time(datetime.now())
            
            logger.info(f"Sync completed for {self.source_name}", 
                      documents_count=len(documents))
            
        except Exception as e:
            logger.error(f"Sync failed for {self.source_name}", error=str(e))
            raise
    
    def get_processed_documents_count(self) -> int:
        """Get count of processed documents"""
        return self.redis_client.scard(self.processed_key)
    
    def clear_processed_documents(self):
        """Clear processed documents (for testing)"""
        self.redis_client.delete(self.processed_key)
        logger.info(f"Cleared processed documents for {self.source_name}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status information"""
        return {
            "source": self.source_name,
            "last_sync": self.get_last_sync_time().isoformat(),
            "processed_count": self.get_processed_documents_count(),
            "api_endpoint": self.api_endpoint
        }
