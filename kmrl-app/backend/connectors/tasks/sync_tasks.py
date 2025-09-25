"""
Celery Tasks for KMRL Connector Synchronization
Implements scheduled sync tasks for all connectors with incremental and historical processing
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import structlog
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Celery with unified configuration
celery_app = Celery('kmrl_connectors')
celery_app.config_from_object('config.celery_config.CELERY_CONFIG')

# Autodiscover tasks to ensure all are registered
celery_app.autodiscover_tasks(['connectors.tasks.sync_tasks'])

logger = structlog.get_logger()

@celery_app.task(bind=True, name='connectors.tasks.sync_tasks.sync_gmail_incremental')
def sync_gmail_incremental(self):
    """Sync Gmail attachments incrementally"""
    try:
        from connectors.implementations.gmail_connector import GmailConnector
        
        api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        connector = GmailConnector(api_endpoint)
        
        # Get credentials from environment (following reference implementation)
        credentials = {
            'credentials_file': connector.credentials_file,
            'token_file': connector.token_file
        }
        
        # Perform incremental sync
        result = connector.sync_incremental(credentials)
        
        logger.info("Gmail incremental sync completed", **result)
        return result
        
    except Exception as e:
        logger.error(f"Gmail incremental sync failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name='connectors.tasks.sync_tasks.sync_google_drive_incremental')
def sync_google_drive_incremental(self):
    """Sync Google Drive files incrementally"""
    try:
        from connectors.implementations.google_drive_connector import GoogleDriveConnector
        
        api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        connector = GoogleDriveConnector(api_endpoint)
        
        # Get credentials from environment (following reference implementation)
        credentials = {
            'credentials_file': connector.credentials_file,
            'token_file': connector.token_file
        }
        
        # Perform incremental sync
        result = connector.sync_incremental(credentials)
        
        logger.info("Google Drive incremental sync completed", **result)
        return result
        
    except Exception as e:
        logger.error(f"Google Drive incremental sync failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name='connectors.tasks.sync_tasks.sync_maximo_incremental')
def sync_maximo_incremental(self):
    """Sync Maximo work orders incrementally"""
    try:
        from connectors.implementations.maximo_connector import MaximoConnector
        
        api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        connector = MaximoConnector(api_endpoint)
        
        # Get credentials from environment
        credentials = {
            'maximo_base_url': connector.maximo_base_url,
            'maximo_username': connector.maximo_username,
            'maximo_password': connector.maximo_password
        }
        
        # Perform incremental sync
        result = connector.sync_incremental(credentials)
        
        logger.info("Maximo incremental sync completed", **result)
        return result
        
    except Exception as e:
        logger.error(f"Maximo incremental sync failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name='connectors.tasks.sync_tasks.sync_whatsapp_incremental')
def sync_whatsapp_incremental(self):
    """Sync WhatsApp messages incrementally"""
    try:
        from connectors.implementations.whatsapp_connector import WhatsAppConnector
        
        api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        connector = WhatsAppConnector(api_endpoint)
        
        # Get credentials from environment
        credentials = {
            'whatsapp_phone_number_id': connector.whatsapp_phone_number_id,
            'whatsapp_access_token': connector.whatsapp_access_token
        }
        
        # Perform incremental sync
        result = connector.sync_incremental(credentials)
        
        logger.info("WhatsApp incremental sync completed", **result)
        return result
        
    except Exception as e:
        logger.error(f"WhatsApp incremental sync failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name='connectors.tasks.sync_tasks.sync_gmail_historical')
def sync_gmail_historical(self, days_back: int = 30):
    """Sync Gmail attachments historically"""
    try:
        from connectors.implementations.gmail_connector import GmailConnector
        
        api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        connector = GmailConnector(api_endpoint)
        
        # Get credentials from environment (following reference implementation)
        credentials = {
            'credentials_file': connector.credentials_file,
            'token_file': connector.token_file
        }
        
        # Perform historical sync
        result = connector.sync_historical(credentials, days_back=days_back)
        
        logger.info("Gmail historical sync completed", **result)
        return result
        
    except Exception as e:
        logger.error(f"Gmail historical sync failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@celery_app.task(bind=True, name='connectors.tasks.sync_tasks.sync_google_drive_historical')
def sync_google_drive_historical(self, days_back: int = 30):
    """Sync Google Drive files historically"""
    try:
        from connectors.implementations.google_drive_connector import GoogleDriveConnector
        
        api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        connector = GoogleDriveConnector(api_endpoint)
        
        # Get credentials from environment (following reference implementation)
        credentials = {
            'credentials_file': connector.credentials_file,
            'token_file': connector.token_file
        }
        
        # Perform historical sync
        result = connector.sync_historical(credentials, days_back=days_back)
        
        logger.info("Google Drive historical sync completed", **result)
        return result
        
    except Exception as e:
        logger.error(f"Google Drive historical sync failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@celery_app.task(bind=True, name='connectors.tasks.sync_tasks.sync_maximo_historical')
def sync_maximo_historical(self, days_back: int = 30):
    """Sync Maximo work orders historically"""
    try:
        from connectors.implementations.maximo_connector import MaximoConnector
        
        api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        connector = MaximoConnector(api_endpoint)
        
        # Get credentials from environment
        credentials = {
            'maximo_base_url': connector.maximo_base_url,
            'maximo_username': connector.maximo_username,
            'maximo_password': connector.maximo_password
        }
        
        # Perform historical sync
        result = connector.sync_historical(credentials, days_back=days_back)
        
        logger.info("Maximo historical sync completed", **result)
        return result
        
    except Exception as e:
        logger.error(f"Maximo historical sync failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@celery_app.task(bind=True, name='connectors.tasks.sync_tasks.sync_all_historical')
def sync_all_historical(self, days_back: int = 30):
    """Sync all connectors historically"""
    try:
        logger.info("Starting historical sync for all connectors", days_back=days_back)
        
        # Schedule historical sync tasks for all connectors
        gmail_task = sync_gmail_historical.delay(days_back)
        gdrive_task = sync_google_drive_historical.delay(days_back)
        maximo_task = sync_maximo_historical.delay(days_back)
        
        # Wait for completion (with timeout)
        results = {}
        try:
            results['gmail'] = gmail_task.get(timeout=1800)  # 30 minutes
        except Exception as e:
            results['gmail'] = {'error': str(e)}
        
        try:
            results['google_drive'] = gdrive_task.get(timeout=1800)  # 30 minutes
        except Exception as e:
            results['google_drive'] = {'error': str(e)}
        
        try:
            results['maximo'] = maximo_task.get(timeout=1800)  # 30 minutes
        except Exception as e:
            results['maximo'] = {'error': str(e)}
        
        logger.info("All connectors historical sync completed", results=results)
        return results
        
    except Exception as e:
        logger.error(f"All connectors historical sync failed: {e}")
        raise self.retry(exc=e, countdown=600, max_retries=2)

@celery_app.task(bind=True, name='connectors.tasks.sync_tasks.health_check_connectors')
def health_check_connectors(self):
    """Health check for active connectors only (Gmail, Google Drive)"""
    try:
        from connectors.implementations.gmail_connector import GmailConnector
        from connectors.implementations.google_drive_connector import GoogleDriveConnector
        
        api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        
        health_status = {}
        
        # Check Gmail connector (active)
        try:
            gmail_connector = GmailConnector(api_endpoint)
            health_status['gmail'] = gmail_connector.get_sync_status()
        except Exception as e:
            health_status['gmail'] = {'error': str(e), 'status': 'error'}
        
        # Check Google Drive connector (active)
        try:
            gdrive_connector = GoogleDriveConnector(api_endpoint)
            health_status['google_drive'] = gdrive_connector.get_sync_status()
        except Exception as e:
            health_status['google_drive'] = {'error': str(e), 'status': 'error'}
        
        # Mark inactive connectors as inactive instead of failing
        health_status['maximo'] = {'status': 'inactive', 'message': 'Maximo connector not configured'}
        health_status['whatsapp'] = {'status': 'inactive', 'message': 'WhatsApp connector not configured'}
        
        # Store health status in Redis
        import redis
        redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        redis_client.hset('connector_health', mapping={
            'timestamp': datetime.now().isoformat(),
            'status': json.dumps(health_status)
        })
        
        logger.info("Connector health check completed", status=health_status)
        return health_status
        
    except Exception as e:
        logger.error(f"Connector health check failed: {e}")
        return {'error': str(e)}

@celery_app.task(bind=True, name='connectors.tasks.sync_tasks.process_whatsapp_webhook')
def process_whatsapp_webhook(self, webhook_data: Dict[str, Any]):
    """Process WhatsApp webhook message"""
    try:
        from connectors.implementations.whatsapp_connector import WhatsAppConnector
        
        api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        connector = WhatsAppConnector(api_endpoint)
        
        # Process webhook message
        documents = connector.process_webhook_message(webhook_data)
        
        # Upload documents to API
        uploaded_count = 0
        for document in documents:
            try:
                result = connector.upload_to_api(document)
                connector.mark_document_processed(document)
                uploaded_count += 1
            except Exception as e:
                logger.error(f"Failed to upload WhatsApp document: {e}")
                continue
        
        logger.info("WhatsApp webhook processed", 
                   documents_received=len(documents),
                   documents_uploaded=uploaded_count)
        
        return {
            'documents_received': len(documents),
            'documents_uploaded': uploaded_count
        }
        
    except Exception as e:
        logger.error(f"WhatsApp webhook processing failed: {e}")
        raise self.retry(exc=e, countdown=30, max_retries=3)

# Utility functions
def start_connector_sync():
    """Start all connector sync tasks"""
    logger.info("Starting connector sync tasks")
    
    # Start incremental sync tasks
    sync_gmail_incremental.delay()
    sync_google_drive_incremental.delay()
    sync_maximo_incremental.delay()
    sync_whatsapp_incremental.delay()
    
    # Start health check
    health_check_connectors.delay()
    
    logger.info("All connector sync tasks started")

def stop_connector_sync():
    """Stop all connector sync tasks"""
    logger.info("Stopping connector sync tasks")
    
    # Revoke all scheduled tasks
    celery_app.control.purge()
    
    logger.info("All connector sync tasks stopped")

if __name__ == '__main__':
    # For testing
    celery_app.start()
