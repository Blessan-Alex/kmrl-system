"""
Enhanced Base Connector Architecture for KMRL Document Ingestion
Implements unified data ingestion pipeline with incremental sync
"""

from abc import ABC, abstractmethod
import redis
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Generator
import structlog
from dataclasses import dataclass, field
from enum import Enum
import time

logger = structlog.get_logger()

class SyncStatus(Enum):
    """Sync status enumeration"""
    IDLE = "idle"
    SYNCING = "syncing"
    ERROR = "error"
    PAUSED = "paused"

@dataclass
class Document:
    """Unified document model for all KMRL sources"""
    source: str
    filename: str
    content: bytes
    content_type: str
    metadata: Dict[str, Any]
    document_id: Optional[str] = None
    uploaded_at: datetime = field(default_factory=datetime.now)
    language: str = "unknown"
    size: int = 0
    checksum: Optional[str] = None
    original_path: Optional[str] = None
    
    def __post_init__(self):
        """Calculate checksum and size after initialization"""
        if self.content:
            self.size = len(self.content)
            self.checksum = hashlib.md5(self.content).hexdigest()
        
        if not self.document_id:
            # Generate unique document ID based on source, filename, and checksum
            self.document_id = f"{self.source}_{self.filename}_{self.checksum}"

@dataclass
class SyncState:
    """Sync state for incremental processing"""
    last_sync_time: datetime
    last_document_id: Optional[str] = None
    sync_cursor: Optional[str] = None
    total_processed: int = 0
    error_count: int = 0
    status: SyncStatus = SyncStatus.IDLE

class EnhancedBaseConnector(ABC):
    """Enhanced base class for all KMRL data source connectors"""
    
    def __init__(self, source_name: str, api_endpoint: str, sync_interval_minutes: int = 2):
        self.source_name = source_name.lower()
        self.api_endpoint = api_endpoint
        self.sync_interval = timedelta(minutes=sync_interval_minutes)
        
        # Redis keys for state management
        self.state_key = f"connector_state:{self.source_name}"
        self.processed_key = f"processed_docs:{self.source_name}"
        self.checksums_key = f"document_checksums:{self.source_name}"
        self.sync_status_key = f"sync_status:{self.source_name}"
        self.error_log_key = f"sync_errors:{self.source_name}"
        
        # Connect to Redis
        self.redis_client = self._connect_redis()
        
        logger.info(f"Initialized {source_name} connector", 
                   sync_interval=sync_interval_minutes)
    
    def _connect_redis(self) -> redis.Redis:
        """Connect to Redis with retry logic"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        for attempt in range(3):
            try:
                client = redis.Redis.from_url(redis_url, decode_responses=True)
                client.ping()
                logger.info(f"Connected to Redis at {redis_url}")
                return client
            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(1)
                else:
                    raise Exception(f"Redis connection required but failed: {e}")
    
    def get_sync_state(self) -> SyncState:
        """Get current sync state from Redis"""
        try:
            state_data = self.redis_client.hgetall(self.state_key)
            if state_data:
                return SyncState(
                    last_sync_time=datetime.fromisoformat(state_data.get('last_sync_time', datetime.min.isoformat())),
                    last_document_id=state_data.get('last_document_id'),
                    sync_cursor=state_data.get('sync_cursor'),
                    total_processed=int(state_data.get('total_processed', 0)),
                    error_count=int(state_data.get('error_count', 0)),
                    status=SyncStatus(state_data.get('status', SyncStatus.IDLE.value))
                )
        except Exception as e:
            logger.warning(f"Failed to get sync state: {e}")
        
        return SyncState(last_sync_time=datetime.min)
    
    def update_sync_state(self, state: SyncState):
        """Update sync state in Redis"""
        try:
            state_data = {
                'last_sync_time': state.last_sync_time.isoformat(),
                'last_document_id': state.last_document_id or '',
                'sync_cursor': state.sync_cursor or '',
                'total_processed': str(state.total_processed),
                'error_count': str(state.error_count),
                'status': state.status.value
            }
            self.redis_client.hset(self.state_key, mapping=state_data)
        except Exception as e:
            logger.error(f"Failed to update sync state: {e}")
    
    def is_document_processed(self, document_id: str) -> bool:
        """Check if document was already processed using checksum"""
        return self.redis_client.sismember(self.processed_key, document_id)
    
    def mark_document_processed(self, document: Document):
        """Mark document as processed"""
        try:
            self.redis_client.sadd(self.processed_key, document.document_id)
            if document.checksum:
                self.redis_client.hset(self.checksums_key, document.checksum, document.document_id)
        except Exception as e:
            logger.error(f"Failed to mark document as processed: {e}")
    
    def should_sync(self) -> bool:
        """Check if it's time to sync based on interval"""
        state = self.get_sync_state()
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        # Ensure last_sync_time is timezone-aware
        if state.last_sync_time.tzinfo is None:
            last_sync = state.last_sync_time.replace(tzinfo=timezone.utc)
        else:
            last_sync = state.last_sync_time
            
        time_since_last = now - last_sync
        return time_since_last >= self.sync_interval
    
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
                        'uploaded_by': 'connector_system',
                        'language': document.language,
                        'checksum': document.checksum,
                        'size': str(document.size),
                        'document_id': document.document_id
                    }
                    
                    headers = {
                        'X-API-Key': self.get_api_key(),
                        'X-Connector-Source': self.source_name
                    }
                    
                    response = requests.post(
                        f"{self.api_endpoint}/api/v1/documents/upload",
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info("Document uploaded successfully", 
                                   source=document.source, 
                                   filename=document.filename,
                                   document_id=document.document_id)
                        return result
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
        api_key = os.getenv('API_KEY')
        if not api_key:
            # Fallback to Redis
            api_key = self.redis_client.get("kmrl_api_key")
            if api_key:
                return api_key
        
        return api_key or "kmrl-api-key-2024"
    
    def log_sync_error(self, error: str, context: Dict[str, Any] = None):
        """Log sync error with context"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': error,
            'context': context or {}
        }
        self.redis_client.lpush(self.error_log_key, json.dumps(error_entry))
        # Keep only last 100 errors
        self.redis_client.ltrim(self.error_log_key, 0, 99)
    
    def get_recent_errors(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent sync errors"""
        try:
            errors = self.redis_client.lrange(self.error_log_key, 0, count - 1)
            return [json.loads(error) for error in errors]
        except Exception as e:
            logger.error(f"Failed to get recent errors: {e}")
            return []
    
    def clear_errors(self):
        """Clear error log"""
        self.redis_client.delete(self.error_log_key)
    
    @abstractmethod
    def fetch_documents_incremental(self, credentials: Dict[str, str], 
                                   state: SyncState,
                                   batch_size: int = 50) -> Generator[List[Document], None, None]:
        """Fetch documents incrementally with pagination"""
        pass
    
    @abstractmethod
    def fetch_documents_historical(self, credentials: Dict[str, str], 
                                  start_date: datetime,
                                  batch_size: int = 100) -> Generator[List[Document], None, None]:
        """Fetch historical documents in chunks"""
        pass
    
    def sync_incremental(self, credentials: Dict[str, str], force: bool = False) -> Dict[str, Any]:
        """Perform incremental sync"""
        if not force and not self.should_sync():
            return {"status": "skipped", "reason": "not_time_for_sync"}
        
        state = self.get_sync_state()
        state.status = SyncStatus.SYNCING
        self.update_sync_state(state)
        
        try:
            logger.info(f"Starting incremental sync for {self.source_name}")
            
            total_documents = 0
            batch_count = 0
            
            for document_batch in self.fetch_documents_incremental(credentials, state):
                batch_count += 1
                processed_in_batch = 0
                
                for document in document_batch:
                    if not self.is_document_processed(document.document_id):
                        try:
                            self.upload_to_api(document)
                            self.mark_document_processed(document)
                            processed_in_batch += 1
                            total_documents += 1
                        except Exception as e:
                            logger.error(f"Failed to process document {document.document_id}: {e}")
                            state.error_count += 1
                            self.log_sync_error(str(e), {
                                'document_id': document.document_id,
                                'filename': document.filename
                            })
                
                # Update state after each batch
                state.last_sync_time = datetime.now()
                state.total_processed += processed_in_batch
                self.update_sync_state(state)
                
                logger.info(f"Processed batch {batch_count}", 
                           batch_size=len(document_batch),
                           processed=processed_in_batch)
            
            state.status = SyncStatus.IDLE
            self.update_sync_state(state)
            
            result = {
                "status": "completed",
                "total_documents": total_documents,
                "batches_processed": batch_count,
                "errors": state.error_count
            }
            
            logger.info(f"Incremental sync completed for {self.source_name}", **result)
            return result
            
        except Exception as e:
            state.status = SyncStatus.ERROR
            self.update_sync_state(state)
            self.log_sync_error(str(e))
            
            logger.error(f"Incremental sync failed for {self.source_name}: {e}")
            raise
    
    def sync_historical(self, credentials: Dict[str, str], 
                       days_back: int = 30,
                       batch_size: int = 100) -> Dict[str, Any]:
        """Perform historical sync in chunks"""
        state = self.get_sync_state()
        state.status = SyncStatus.SYNCING
        self.update_sync_state(state)
        
        from datetime import timezone
        start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        try:
            logger.info(f"Starting historical sync for {self.source_name}", 
                       days_back=days_back, start_date=start_date.isoformat())
            
            total_documents = 0
            batch_count = 0
            
            for document_batch in self.fetch_documents_historical(credentials, start_date, batch_size):
                batch_count += 1
                processed_in_batch = 0
                
                for document in document_batch:
                    if not self.is_document_processed(document.document_id):
                        try:
                            self.upload_to_api(document)
                            self.mark_document_processed(document)
                            processed_in_batch += 1
                            total_documents += 1
                        except Exception as e:
                            logger.error(f"Failed to process document {document.document_id}: {e}")
                            state.error_count += 1
                
                # Update state after each batch
                state.total_processed += processed_in_batch
                self.update_sync_state(state)
                
                logger.info(f"Historical batch {batch_count} processed", 
                           batch_size=len(document_batch),
                           processed=processed_in_batch)
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.1)
            
            state.status = SyncStatus.IDLE
            state.last_sync_time = datetime.now()
            self.update_sync_state(state)
            
            result = {
                "status": "completed",
                "total_documents": total_documents,
                "batches_processed": batch_count,
                "days_processed": days_back,
                "errors": state.error_count
            }
            
            logger.info(f"Historical sync completed for {self.source_name}", **result)
            return result
            
        except Exception as e:
            state.status = SyncStatus.ERROR
            self.update_sync_state(state)
            self.log_sync_error(str(e))
            
            logger.error(f"Historical sync failed for {self.source_name}: {e}")
            raise
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get comprehensive sync status"""
        state = self.get_sync_state()
        recent_errors = self.get_recent_errors(5)
        
        return {
            "source": self.source_name,
            "status": state.status.value,
            "last_sync": state.last_sync_time.isoformat(),
            "total_processed": state.total_processed,
            "error_count": state.error_count,
            "sync_interval_minutes": self.sync_interval.total_seconds() / 60,
            "next_sync_in": max(0, self.sync_interval.total_seconds() - 
                               (datetime.now() - state.last_sync_time).total_seconds()),
            "recent_errors": recent_errors,
            "api_endpoint": self.api_endpoint
        }
    
    def reset_sync_state(self):
        """Reset sync state (for testing or manual intervention)"""
        self.redis_client.delete(self.state_key)
        logger.info(f"Reset sync state for {self.source_name}")
    
    def pause_sync(self):
        """Pause automatic sync"""
        state = self.get_sync_state()
        state.status = SyncStatus.PAUSED
        self.update_sync_state(state)
        logger.info(f"Paused sync for {self.source_name}")
    
    def resume_sync(self):
        """Resume automatic sync"""
        state = self.get_sync_state()
        state.status = SyncStatus.IDLE
        self.update_sync_state(state)
        logger.info(f"Resumed sync for {self.source_name}")
