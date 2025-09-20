"""
Queue Service for KMRL Document Processing
Handles task queuing using Celery and Redis
"""

import os
import json
from typing import Any
import structlog
from celery import Celery

logger = structlog.get_logger()

class QueueService:
    """Queue service for KMRL document processing"""
    
    def __init__(self):
        self.celery_app = Celery('kmrl-gateway')
        self.celery_app.config_from_object('config.celery_config')
    
    async def queue_document_processing(self, document: Any) -> str:
        """Queue document for processing"""
        try:
            # Create task payload
            task_payload = {
                "document_id": str(document.id),
                "filename": document.filename,
                "source": document.source,
                "storage_path": document.storage_path,
                "content_type": document.content_type,
                "metadata": document.metadata
            }
            
            # Queue the task
            task = self.celery_app.send_task(
                'document_processing.process_document',
                args=[task_payload],
                queue='document_processing'
            )
            
            logger.info(f"Document queued for processing: {task.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"Failed to queue document: {e}")
            raise Exception(f"Failed to queue document: {str(e)}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        try:
            task = self.celery_app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": task.status,
                "result": task.result if task.successful() else None,
                "error": str(task.result) if task.failed() else None
            }
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return {
                "task_id": task_id,
                "status": "UNKNOWN",
                "error": str(e)
            }
