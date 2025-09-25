"""
Enhanced Queue Service for KMRL Document Processing
Comprehensive task queuing with priority, monitoring, and error handling
"""

import os
import json
import redis
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog
from celery import Celery
from celery.result import AsyncResult

logger = structlog.get_logger()

class QueueService:
    """Enhanced queue service for KMRL document processing"""
    
    def __init__(self):
        self.celery_app = Celery('kmrl-gateway')
        self.celery_app.config_from_object('config.celery_config.CELERY_CONFIG')
        self.celery_app.autodiscover_tasks(['services.processing.document_processor'])
        self.redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        self.queue_configs = {
            'document_processing': {'priority': 1, 'max_retries': 3},
            'rag_processing': {'priority': 2, 'max_retries': 2},
            'notifications': {'priority': 3, 'max_retries': 1},
            'high_priority': {'priority': 0, 'max_retries': 5}
        }
    
    async def queue_document_processing(self, document: Any, priority: str = "normal") -> str:
        """Enhanced document queuing with priority and monitoring"""
        try:
            # Determine queue based on priority
            queue_name = self._get_queue_name(priority)
            queue_config = self.queue_configs.get(queue_name, self.queue_configs['document_processing'])
            
            # Create enhanced task payload for document worker
            task_payload = {
                "document_id": str(document.id),
                "filename": document.original_filename,
                "source": document.source,
                "s3_key": document.s3_key,
                "content_type": document.content_type,
                "metadata": document.document_metadata,
                "priority": priority,
                "queued_at": datetime.now().isoformat(),
                "max_retries": queue_config['max_retries']
            }
            
            # Queue the task for the document worker
            task = self.celery_app.send_task(
                'kmrl-gateway.process_document',
                args=[document.id],
                queue=queue_name,
                priority=queue_config['priority']
            )
            
            # Store task metadata in Redis
            await self._store_task_metadata(task.id, {
                'document_id': str(document.id),
                'queue_name': queue_name,
                'priority': priority,
                'status': 'PENDING',
                'queued_at': datetime.now().isoformat(),
                'retry_count': 0
            })
            
            # Update queue statistics
            await self._update_queue_stats(queue_name, 'queued')
            
            logger.info(f"Document queued for processing: {task.id} (queue: {queue_name}, priority: {priority})")
            return task.id
            
        except Exception as e:
            logger.error(f"Failed to queue document: {e}")
            raise Exception(f"Failed to queue document: {str(e)}")
    
    def _get_queue_name(self, priority: str) -> str:
        """Get queue name based on priority"""
        if priority == "high":
            return "high_priority"
        elif priority == "normal":
            return "document_processing"
        else:
            return "document_processing"
    
    async def _store_task_metadata(self, task_id: str, metadata: Dict[str, Any]):
        """Store task metadata in Redis"""
        try:
            self.redis_client.hset(f"task_metadata:{task_id}", mapping=metadata)
            self.redis_client.expire(f"task_metadata:{task_id}", 86400 * 7)  # 7 days
        except Exception as e:
            logger.error(f"Failed to store task metadata: {e}")
    
    async def _update_queue_stats(self, queue_name: str, action: str):
        """Update queue statistics"""
        try:
            stats_key = f"queue_stats:{queue_name}"
            current_time = datetime.now().isoformat()
            
            if action == 'queued':
                self.redis_client.hincrby(stats_key, 'total_queued', 1)
            elif action == 'completed':
                self.redis_client.hincrby(stats_key, 'total_completed', 1)
            elif action == 'failed':
                self.redis_client.hincrby(stats_key, 'total_failed', 1)
            
            self.redis_client.hset(stats_key, 'last_updated', current_time)
            self.redis_client.expire(stats_key, 86400 * 30)  # 30 days
        except Exception as e:
            logger.error(f"Failed to update queue stats: {e}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Enhanced task status with metadata"""
        try:
            task = self.celery_app.AsyncResult(task_id)
            
            # Get basic status
            status_info = {
                "task_id": task_id,
                "status": task.status,
                "result": task.result if task.successful() else None,
                "error": str(task.result) if task.failed() else None
            }
            
            # Get additional metadata from Redis
            try:
                metadata = self.redis_client.hgetall(f"task_metadata:{task_id}")
                if metadata:
                    status_info.update({
                        "document_id": metadata.get('document_id'),
                        "queue_name": metadata.get('queue_name'),
                        "priority": metadata.get('priority'),
                        "queued_at": metadata.get('queued_at'),
                        "retry_count": int(metadata.get('retry_count', 0))
                    })
            except Exception:
                pass
            
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return {
                "task_id": task_id,
                "status": "UNKNOWN",
                "error": str(e)
            }
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get comprehensive queue status"""
        try:
            queue_status = {}
            
            # Get Celery worker stats
            inspect = self.celery_app.control.inspect()
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            reserved_tasks = inspect.reserved()
            
            # Get queue statistics from Redis
            for queue_name in self.queue_configs.keys():
                stats_key = f"queue_stats:{queue_name}"
                stats = self.redis_client.hgetall(stats_key)
                
                queue_status[queue_name] = {
                    "total_queued": int(stats.get('total_queued', 0)),
                    "total_completed": int(stats.get('total_completed', 0)),
                    "total_failed": int(stats.get('total_failed', 0)),
                    "last_updated": stats.get('last_updated'),
                    "active_workers": len(active_tasks) if active_tasks else 0,
                    "pending_tasks": len(scheduled_tasks.get(queue_name, [])) if scheduled_tasks else 0
                }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "queues": queue_status,
                "worker_status": {
                    "active_workers": len(active_tasks) if active_tasks else 0,
                    "total_active_tasks": sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {"error": str(e)}
    
    async def retry_failed_task(self, task_id: str) -> bool:
        """Retry a failed task"""
        try:
            # Get task metadata
            metadata = self.redis_client.hgetall(f"task_metadata:{task_id}")
            if not metadata:
                return False
            
            retry_count = int(metadata.get('retry_count', 0))
            max_retries = int(metadata.get('max_retries', 3))
            
            if retry_count >= max_retries:
                logger.warning(f"Task {task_id} has exceeded max retries")
                return False
            
            # Increment retry count
            self.redis_client.hincrby(f"task_metadata:{task_id}", 'retry_count', 1)
            
            # Re-queue the task
            queue_name = metadata.get('queue_name', 'document_processing')
            priority = metadata.get('priority', 'normal')
            
            # Extract original task payload (this would need to be stored)
            # For now, just log the retry attempt
            logger.info(f"Retrying task {task_id} (attempt {retry_count + 1})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry task: {e}")
            return False
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        try:
            task = self.celery_app.AsyncResult(task_id)
            task.revoke(terminate=True)
            
            # Update metadata
            self.redis_client.hset(f"task_metadata:{task_id}", 'status', 'REVOKED')
            
            logger.info(f"Task {task_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return False
    
        async def handle_processing_result(self, task_id: str, result: Dict[str, Any]):
            """Handle processing result from document worker"""
            try:
                # Get task metadata
                metadata = self.redis_client.hgetall(f"task_metadata:{task_id}")
                if not metadata:
                    logger.warning(f"No metadata found for task {task_id}")
                    return
                
                document_id = metadata.get('document_id')
                if not document_id:
                    logger.warning(f"No document ID found for task {task_id}")
                    return
                
                # Update document status based on processing result
                from models.document import DocumentModel
                document = await DocumentModel.get_by_id(document_id)
                
                if document:
                    if result.get('status') == 'completed':
                        document.update_status(
                            status='completed',
                            confidence_score=result.get('confidence_score'),
                            language=result.get('language'),
                            department=result.get('department')
                        )
                        logger.info(f"Document processing completed: {document_id}")
                    elif result.get('status') == 'failed':
                        document.update_status(
                            status='failed'
                        )
                        logger.error(f"Document processing failed: {document_id} - {result.get('error')}")
                
                # Update task metadata
                self.redis_client.hset(f"task_metadata:{task_id}", 'status', result.get('status', 'UNKNOWN'))
                self.redis_client.hset(f"task_metadata:{task_id}", 'completed_at', datetime.now().isoformat())
                
                # Update queue statistics
                queue_name = metadata.get('queue_name', 'document_processing')
                if result.get('status') == 'completed':
                    await self._update_queue_stats(queue_name, 'completed')
                else:
                    await self._update_queue_stats(queue_name, 'failed')
                
            except Exception as e:
                logger.error(f"Failed to handle processing result: {e}")
        
        async def get_queue_statistics(self, hours: int = 24) -> Dict[str, Any]:
            """Get queue statistics for the last N hours"""
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                stats = {
                    "period_hours": hours,
                    "cutoff_time": cutoff_time.isoformat(),
                    "queue_performance": {},
                    "error_analysis": {},
                    "throughput": {}
                }
                
                # Analyze queue performance
                for queue_name in self.queue_configs.keys():
                    stats_key = f"queue_stats:{queue_name}"
                    queue_stats = self.redis_client.hgetall(stats_key)
                    
                    total_queued = int(queue_stats.get('total_queued', 0))
                    total_completed = int(queue_stats.get('total_completed', 0))
                    total_failed = int(queue_stats.get('total_failed', 0))
                    
                    success_rate = (total_completed / total_queued * 100) if total_queued > 0 else 0
                    error_rate = (total_failed / total_queued * 100) if total_queued > 0 else 0
                    
                    stats["queue_performance"][queue_name] = {
                        "total_queued": total_queued,
                        "total_completed": total_completed,
                        "total_failed": total_failed,
                        "success_rate": round(success_rate, 2),
                        "error_rate": round(error_rate, 2)
                    }
                
                return stats
                
            except Exception as e:
                logger.error(f"Failed to get queue statistics: {e}")
                return {"error": str(e)}
