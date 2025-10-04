"""
Processing Status Model for KMRL Gateway
Tracks document processing status and progress
"""

import os
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

logger = structlog.get_logger()

class ProcessingStage(Enum):
    """Document processing stages"""
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    STORED = "stored"
    QUEUED = "queued"
    PROCESSING = "processing"
    OCR_COMPLETE = "ocr_complete"
    LANGUAGE_DETECTED = "language_detected"
    DEPARTMENT_CLASSIFIED = "department_classified"
    RAG_READY = "rag_ready"
    NOTIFICATIONS_SENT = "notifications_sent"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"

@dataclass
class ProcessingStatus:
    """Processing status model"""
    document_id: str
    current_stage: ProcessingStage
    progress_percentage: float
    started_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    processing_metadata: Dict[str, Any] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.processing_metadata is None:
            self.processing_metadata = {}
    
    @classmethod
    async def create(cls, document_id: str, current_stage: ProcessingStage = ProcessingStage.UPLOADED) -> 'ProcessingStatus':
        """Create new processing status"""
        now = datetime.now()
        status = cls(
            document_id=document_id,
            current_stage=current_stage,
            progress_percentage=0.0,
            started_at=now,
            updated_at=now,
            estimated_completion=now + timedelta(minutes=5)  # Default 5 minutes
        )
        
        await status.save()
        return status
    
    async def save(self):
        """Save processing status to Redis"""
        try:
            redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
            
            # Convert to dict for Redis storage
            status_data = asdict(self)
            status_data['current_stage'] = self.current_stage.value
            status_data['started_at'] = self.started_at.isoformat()
            status_data['updated_at'] = self.updated_at.isoformat()
            if self.estimated_completion:
                status_data['estimated_completion'] = self.estimated_completion.isoformat()
            
            # Store in Redis
            redis_client.hset(
                f"processing_status:{self.document_id}",
                mapping=status_data
            )
            
            # Set expiration (24 hours)
            redis_client.expire(f"processing_status:{self.document_id}", 86400)
            
            logger.info(f"Processing status saved for document {self.document_id}")
            
        except Exception as e:
            logger.error(f"Failed to save processing status: {e}")
            raise
    
    @classmethod
    async def get_by_document_id(cls, document_id: str) -> Optional['ProcessingStatus']:
        """Get processing status by document ID"""
        try:
            redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
            
            # Get status data from Redis
            status_data = redis_client.hgetall(f"processing_status:{document_id}")
            
            if not status_data:
                return None
            
            # Convert back to ProcessingStatus object
            status_data['current_stage'] = ProcessingStage(status_data['current_stage'])
            status_data['started_at'] = datetime.fromisoformat(status_data['started_at'])
            status_data['updated_at'] = datetime.fromisoformat(status_data['updated_at'])
            
            if status_data.get('estimated_completion'):
                status_data['estimated_completion'] = datetime.fromisoformat(status_data['estimated_completion'])
            else:
                status_data['estimated_completion'] = None
            
            # Parse processing_metadata if it's a string
            if isinstance(status_data.get('processing_metadata'), str):
                status_data['processing_metadata'] = json.loads(status_data['processing_metadata'])
            
            return cls(**status_data)
            
        except Exception as e:
            logger.error(f"Failed to get processing status: {e}")
            return None
    
    async def update_stage(self, new_stage: ProcessingStage, progress_percentage: float = None, 
                          error_message: str = None, metadata: Dict[str, Any] = None):
        """Update processing stage"""
        self.current_stage = new_stage
        self.updated_at = datetime.now()
        
        if progress_percentage is not None:
            self.progress_percentage = progress_percentage
        
        if error_message:
            self.error_message = error_message
        
        if metadata:
            self.processing_metadata.update(metadata)
        
        # Update estimated completion based on stage
        self._update_estimated_completion()
        
        await self.save()
        
        logger.info(f"Processing stage updated for document {self.document_id}: {new_stage.value}")
    
    def _update_estimated_completion(self):
        """Update estimated completion time based on current stage"""
        stage_times = {
            ProcessingStage.UPLOADED: 0,
            ProcessingStage.VALIDATED: 1,
            ProcessingStage.STORED: 2,
            ProcessingStage.QUEUED: 3,
            ProcessingStage.PROCESSING: 4,
            ProcessingStage.OCR_COMPLETE: 5,
            ProcessingStage.LANGUAGE_DETECTED: 6,
            ProcessingStage.DEPARTMENT_CLASSIFIED: 7,
            ProcessingStage.RAG_READY: 8,
            ProcessingStage.NOTIFICATIONS_SENT: 9,
            ProcessingStage.COMPLETED: 10
        }
        
        current_time = stage_times.get(self.current_stage, 0)
        total_stages = len(stage_times)
        
        if current_time > 0:
            remaining_stages = total_stages - current_time
            estimated_minutes = remaining_stages * 0.5  # 30 seconds per stage
            self.estimated_completion = datetime.now() + timedelta(minutes=estimated_minutes)
    
    async def mark_failed(self, error_message: str):
        """Mark processing as failed"""
        await self.update_stage(
            ProcessingStage.FAILED,
            progress_percentage=100.0,
            error_message=error_message
        )
        
        logger.error(f"Processing failed for document {self.document_id}: {error_message}")
    
    async def mark_completed(self):
        """Mark processing as completed"""
        await self.update_stage(
            ProcessingStage.COMPLETED,
            progress_percentage=100.0
        )
        
        logger.info(f"Processing completed for document {self.document_id}")
    
    async def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
        self.updated_at = datetime.now()
        await self.save()
        
        logger.warning(f"Retry count incremented for document {self.document_id}: {self.retry_count}/{self.max_retries}")
    
    def can_retry(self) -> bool:
        """Check if processing can be retried"""
        return self.retry_count < self.max_retries and self.current_stage != ProcessingStage.COMPLETED
    
    async def get_processing_history(self) -> List[Dict[str, Any]]:
        """Get processing history for this document"""
        try:
            redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
            
            # Get processing history from Redis
            history_key = f"processing_history:{self.document_id}"
            history_data = redis_client.lrange(history_key, 0, -1)
            
            history = []
            for entry in history_data:
                try:
                    history.append(json.loads(entry))
                except json.JSONDecodeError:
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get processing history: {e}")
            return []
    
    async def add_history_entry(self, stage: ProcessingStage, message: str, metadata: Dict[str, Any] = None):
        """Add entry to processing history"""
        try:
            redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
            
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'stage': stage.value,
                'message': message,
                'metadata': metadata or {}
            }
            
            # Add to history list
            history_key = f"processing_history:{self.document_id}"
            redis_client.lpush(history_key, json.dumps(history_entry))
            
            # Keep only last 50 entries
            redis_client.ltrim(history_key, 0, 49)
            
            # Set expiration (7 days)
            redis_client.expire(history_key, 604800)
            
        except Exception as e:
            logger.error(f"Failed to add history entry: {e}")
    
    @classmethod
    async def get_failed_documents(cls, hours: int = 24) -> List['ProcessingStatus']:
        """Get documents that failed processing in the last N hours"""
        try:
            redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
            
            # Get all processing status keys
            pattern = "processing_status:*"
            keys = redis_client.keys(pattern)
            
            failed_documents = []
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for key in keys:
                try:
                    status_data = redis_client.hgetall(key)
                    if status_data.get('current_stage') == ProcessingStage.FAILED.value:
                        # Check if it failed within the time window
                        updated_at = datetime.fromisoformat(status_data['updated_at'])
                        if updated_at >= cutoff_time:
                            document_id = key.split(':')[1]
                            status = await cls.get_by_document_id(document_id)
                            if status:
                                failed_documents.append(status)
                except Exception:
                    continue
            
            return failed_documents
            
        except Exception as e:
            logger.error(f"Failed to get failed documents: {e}")
            return []
    
    @classmethod
    async def get_processing_statistics(cls) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
            
            # Get all processing status keys
            pattern = "processing_status:*"
            keys = redis_client.keys(pattern)
            
            stats = {
                'total_documents': len(keys),
                'by_stage': {},
                'by_status': {
                    'completed': 0,
                    'processing': 0,
                    'failed': 0,
                    'queued': 0
                },
                'average_processing_time': 0,
                'retry_rate': 0
            }
            
            total_processing_time = 0
            completed_count = 0
            retry_count = 0
            
            for key in keys:
                try:
                    status_data = redis_client.hgetall(key)
                    stage = status_data.get('current_stage', 'unknown')
                    
                    # Count by stage
                    stats['by_stage'][stage] = stats['by_stage'].get(stage, 0) + 1
                    
                    # Count by status
                    if stage == ProcessingStage.COMPLETED.value:
                        stats['by_status']['completed'] += 1
                        completed_count += 1
                    elif stage == ProcessingStage.FAILED.value:
                        stats['by_status']['failed'] += 1
                    elif stage in [ProcessingStage.PROCESSING.value, ProcessingStage.OCR_COMPLETE.value]:
                        stats['by_status']['processing'] += 1
                    elif stage == ProcessingStage.QUEUED.value:
                        stats['by_status']['queued'] += 1
                    
                    # Calculate processing time
                    if stage == ProcessingStage.COMPLETED.value:
                        started_at = datetime.fromisoformat(status_data['started_at'])
                        updated_at = datetime.fromisoformat(status_data['updated_at'])
                        processing_time = (updated_at - started_at).total_seconds()
                        total_processing_time += processing_time
                    
                    # Count retries
                    retry_count += int(status_data.get('retry_count', 0))
                    
                except Exception:
                    continue
            
            # Calculate averages
            if completed_count > 0:
                stats['average_processing_time'] = total_processing_time / completed_count
            
            if stats['total_documents'] > 0:
                stats['retry_rate'] = retry_count / stats['total_documents']
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get processing statistics: {e}")
            return {}

if __name__ == '__main__':
    # Test processing status
    import asyncio
    
    async def test_processing_status():
        # Create a test processing status
        status = await ProcessingStatus.create("test_doc_123", ProcessingStage.UPLOADED)
        print(f"Created status: {status}")
        
        # Update stage
        await status.update_stage(ProcessingStage.PROCESSING, progress_percentage=50.0)
        print(f"Updated status: {status}")
        
        # Get statistics
        stats = await ProcessingStatus.get_processing_statistics()
        print(f"Statistics: {stats}")
    
    asyncio.run(test_processing_status())
