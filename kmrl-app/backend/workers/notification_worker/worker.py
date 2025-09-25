"""
Smart Notification Worker for KMRL
Handles intelligent notifications based on document content and stakeholder roles
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
import structlog
from celery import Celery
# Note: sentence_transformers and shared modules need to be installed/implemented
# from sentence_transformers import SentenceTransformer
# from shared.notification_engine import NotificationEngine
# from shared.stakeholder_manager import StakeholderManager
# from shared.similarity_calculator import SimilarityCalculator

logger = structlog.get_logger()

# Initialize Celery
celery_app = Celery('kmrl-notification-worker')
celery_app.config_from_object('config.celery_config.CELERY_CONFIG')

# Autodiscover tasks to ensure all are registered
celery_app.autodiscover_tasks(['workers.notification_worker.worker'])

# Initialize processors (commented out until dependencies are installed)
# notification_engine = NotificationEngine()
# stakeholder_manager = StakeholderManager()
# similarity_calculator = SimilarityCalculator()

# Notification templates and thresholds
NOTIFICATION_TEMPLATES = {
    "urgent_maintenance": {
        "threshold": 0.85,
        "keywords": ["urgent", "critical", "emergency", "breakdown", "failure"],
        "recipients": ["engineering", "operations", "maintenance"]
    },
    "safety_incident": {
        "threshold": 0.90,
        "keywords": ["accident", "injury", "safety", "incident", "hazard"],
        "recipients": ["safety", "operations", "executive"]
    },
    "compliance_violation": {
        "threshold": 0.80,
        "keywords": ["violation", "non-compliance", "regulatory", "audit"],
        "recipients": ["compliance", "executive", "legal"]
    },
    "deadline_approaching": {
        "threshold": 0.75,
        "keywords": ["deadline", "due date", "urgent", "expiring"],
        "recipients": ["all"]
    },
    "budget_exceeded": {
        "threshold": 0.80,
        "keywords": ["budget", "cost", "expense", "overrun"],
        "recipients": ["finance", "executive"]
    }
}

@celery_app.task
def generate_smart_notifications(document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate smart notifications based on document content"""
    try:
        document_id = document_data.get('document_id')
        text_content = document_data.get('text_content')
        department = document_data.get('department')
        language = document_data.get('language')
        
        logger.info(f"Generating smart notifications for document: {document_id}")
        
        notifications = []
        
        # Check each notification type
        for notification_type, config in NOTIFICATION_TEMPLATES.items():
            # Calculate similarity with keywords
            similarity_score = similarity_calculator.calculate_similarity(
                text_content, config['keywords']
            )
            
            if similarity_score >= config['threshold']:
                # Get stakeholders for this notification type
                stakeholders = stakeholder_manager.get_stakeholders(
                    config['recipients'], department
                )
                
                # Generate notification
                notification = {
                    "id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "notification_type": notification_type,
                    "title": f"KMRL Alert: {notification_type.replace('_', ' ').title()}",
                    "message": f"Document requires attention: {notification_type} (Score: {similarity_score:.2f})",
                    "priority": "high" if similarity_score >= 0.90 else "medium",
                    "recipients": stakeholders,
                    "similarity_score": similarity_score,
                    "created_at": datetime.now().isoformat()
                }
                
                notifications.append(notification)
                
                # Send notification to each stakeholder
                for stakeholder in stakeholders:
                    send_notification.delay(notification, stakeholder)
        
        logger.info(f"Generated {len(notifications)} notifications for document: {document_id}")
        return notifications
        
    except Exception as e:
        logger.error(f"Smart notification generation failed: {e}")
        return []

@celery_app.task
def send_notification(notification: Dict[str, Any], stakeholder: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification to stakeholder"""
    try:
        stakeholder_id = stakeholder.get('id')
        notification_type = notification.get('notification_type')
        priority = notification.get('priority')
        
        # Send via appropriate channel (email, SMS, in-app)
        result = notification_engine.send_notification(
            stakeholder_id=stakeholder_id,
            notification_type=notification_type,
            title=notification.get('title'),
            message=notification.get('message'),
            priority=priority
        )
        
        logger.info(f"Notification sent to stakeholder: {stakeholder_id}")
        return result
        
    except Exception as e:
        logger.error(f"Notification sending failed: {e}")
        return {"status": "failed", "error": str(e)}

@celery_app.task
def process_notification_queue() -> Dict[str, Any]:
    """Process pending notifications in queue"""
    try:
        # Get pending notifications from queue
        pending_notifications = notification_engine.get_pending_notifications()
        
        processed_count = 0
        for notification in pending_notifications:
            # Process each notification
            result = send_notification.delay(notification, notification.get('stakeholder'))
            if result.get():
                processed_count += 1
        
        logger.info(f"Processed {processed_count} notifications from queue")
        return {"processed_count": processed_count}
        
    except Exception as e:
        logger.error(f"Notification queue processing failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    celery_app.start()
