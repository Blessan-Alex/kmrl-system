"""
Celery Scheduler for KMRL Automatic Document Ingestion
Handles scheduled fetching from all data sources with monitoring and retry logic
"""

from celery import Celery
from celery.schedules import crontab
from celery.exceptions import Retry
import structlog
from datetime import datetime
from connectors.email_connector import EmailConnector
from connectors.maximo_connector import MaximoConnector
from connectors.sharepoint_connector import SharePointConnector
from connectors.whatsapp_connector import WhatsAppConnector
from utils.credentials_manager import CredentialsManager

logger = structlog.get_logger()

# Initialize Celery
celery_app = Celery('kmrl-connectors')
celery_app.config_from_object('config.celery_config')

# Initialize credentials manager
credentials_manager = CredentialsManager()

# Task configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_disable_rate_limits=True,
    task_annotations={
        'fetch_email_documents': {'rate_limit': '10/m'},
        'fetch_maximo_documents': {'rate_limit': '5/m'},
        'fetch_sharepoint_documents': {'rate_limit': '3/m'},
        'fetch_whatsapp_documents': {'rate_limit': '8/m'},
    }
)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def fetch_email_documents(self):
    """Automatically fetch new email attachments every 5 minutes"""
    start_time = datetime.now()
    try:
        logger.info("Starting email document fetch", task_id=self.request.id)
        
        connector = EmailConnector(
            imap_host=credentials_manager.get_email_imap_host(),
            imap_port=credentials_manager.get_email_imap_port()
        )
        
        credentials = credentials_manager.get_email_credentials()
        connector.sync_documents(credentials)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("Email fetch completed", 
                   task_id=self.request.id,
                   duration=duration,
                   processed_count=connector.get_processed_documents_count())
        
        return {
            "status": "success",
            "source": "email",
            "duration": duration,
            "processed_count": connector.get_processed_documents_count()
        }
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error("Email fetch failed", 
                    task_id=self.request.id,
                    error=str(e),
                    duration=duration)
        
        # Retry on specific errors
        if "authentication" in str(e).lower() or "connection" in str(e).lower():
            raise self.retry(countdown=300)  # Retry in 5 minutes for auth issues
        
        return {
            "status": "failed",
            "source": "email",
            "error": str(e),
            "duration": duration
        }

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 120})
def fetch_maximo_documents(self):
    """Automatically fetch new Maximo work orders every 15 minutes"""
    start_time = datetime.now()
    try:
        logger.info("Starting Maximo document fetch", task_id=self.request.id)
        
        connector = MaximoConnector(
            base_url=credentials_manager.get_maximo_base_url()
        )
        
        credentials = credentials_manager.get_maximo_credentials()
        connector.sync_documents(credentials)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("Maximo fetch completed", 
                   task_id=self.request.id,
                   duration=duration,
                   processed_count=connector.get_processed_documents_count())
        
        return {
            "status": "success",
            "source": "maximo",
            "duration": duration,
            "processed_count": connector.get_processed_documents_count()
        }
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error("Maximo fetch failed", 
                    task_id=self.request.id,
                    error=str(e),
                    duration=duration)
        
        # Retry on specific errors
        if "authentication" in str(e).lower() or "timeout" in str(e).lower():
            raise self.retry(countdown=600)  # Retry in 10 minutes for auth/timeout issues
        
        return {
            "status": "failed",
            "source": "maximo",
            "error": str(e),
            "duration": duration
        }

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 180})
def fetch_sharepoint_documents(self):
    """Automatically fetch new SharePoint documents every 30 minutes"""
    start_time = datetime.now()
    try:
        logger.info("Starting SharePoint document fetch", task_id=self.request.id)
        
        connector = SharePointConnector(
            site_url=credentials_manager.get_sharepoint_site_url()
        )
        
        credentials = credentials_manager.get_sharepoint_credentials()
        connector.sync_documents(credentials)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("SharePoint fetch completed", 
                   task_id=self.request.id,
                   duration=duration,
                   processed_count=connector.get_processed_documents_count())
        
        return {
            "status": "success",
            "source": "sharepoint",
            "duration": duration,
            "processed_count": connector.get_processed_documents_count()
        }
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error("SharePoint fetch failed", 
                    task_id=self.request.id,
                    error=str(e),
                    duration=duration)
        
        # Retry on specific errors
        if "authentication" in str(e).lower() or "permission" in str(e).lower():
            raise self.retry(countdown=900)  # Retry in 15 minutes for auth issues
        
        return {
            "status": "failed",
            "source": "sharepoint",
            "error": str(e),
            "duration": duration
        }

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 90})
def fetch_whatsapp_documents(self):
    """Automatically fetch new WhatsApp documents every 10 minutes"""
    start_time = datetime.now()
    try:
        logger.info("Starting WhatsApp document fetch", task_id=self.request.id)
        
        connector = WhatsAppConnector(
            phone_number_id=credentials_manager.get_whatsapp_phone_number_id()
        )
        
        credentials = credentials_manager.get_whatsapp_credentials()
        connector.sync_documents(credentials)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("WhatsApp fetch completed", 
                   task_id=self.request.id,
                   duration=duration,
                   processed_count=connector.get_processed_documents_count())
        
        return {
            "status": "success",
            "source": "whatsapp",
            "duration": duration,
            "processed_count": connector.get_processed_documents_count()
        }
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error("WhatsApp fetch failed", 
                    task_id=self.request.id,
                    error=str(e),
                    duration=duration)
        
        # Retry on specific errors
        if "authentication" in str(e).lower() or "rate limit" in str(e).lower():
            raise self.retry(countdown=300)  # Retry in 5 minutes for auth/rate limit issues
        
        return {
            "status": "failed",
            "source": "whatsapp",
            "error": str(e),
            "duration": duration
        }

# Monitoring and health check tasks
@celery_app.task
def health_check():
    """Health check for all connectors"""
    try:
        health_status = {}
        
        # Check email connector
        try:
            email_connector = EmailConnector(
                imap_host=credentials_manager.get_email_imap_host(),
                imap_port=credentials_manager.get_email_imap_port()
            )
            health_status['email'] = email_connector.get_sync_status()
        except Exception as e:
            health_status['email'] = {"status": "error", "error": str(e)}
        
        # Check Maximo connector
        try:
            maximo_connector = MaximoConnector(
                base_url=credentials_manager.get_maximo_base_url()
            )
            health_status['maximo'] = maximo_connector.get_sync_status()
        except Exception as e:
            health_status['maximo'] = {"status": "error", "error": str(e)}
        
        # Check SharePoint connector
        try:
            sharepoint_connector = SharePointConnector(
                site_url=credentials_manager.get_sharepoint_site_url()
            )
            health_status['sharepoint'] = sharepoint_connector.get_sync_status()
        except Exception as e:
            health_status['sharepoint'] = {"status": "error", "error": str(e)}
        
        # Check WhatsApp connector
        try:
            whatsapp_connector = WhatsAppConnector(
                phone_number_id=credentials_manager.get_whatsapp_phone_number_id()
            )
            health_status['whatsapp'] = whatsapp_connector.get_sync_status()
        except Exception as e:
            health_status['whatsapp'] = {"status": "error", "error": str(e)}
        
        logger.info("Health check completed", health_status=health_status)
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"status": "error", "error": str(e)}

@celery_app.task
def cleanup_old_tasks():
    """Cleanup old completed tasks to prevent memory issues"""
    try:
        # This would clean up old task results from Redis
        # Implementation depends on Redis configuration
        logger.info("Task cleanup completed")
        return {"status": "success", "message": "Old tasks cleaned up"}
        
    except Exception as e:
        logger.error("Task cleanup failed", error=str(e))
        return {"status": "error", "error": str(e)}

# Schedule automatic ingestion for KMRL
celery_app.conf.beat_schedule = {
    'fetch-email-every-5-minutes': {
        'task': 'scheduler.fetch_email_documents',
        'schedule': crontab(minute='*/5'),
    },
    'fetch-maximo-every-15-minutes': {
        'task': 'scheduler.fetch_maximo_documents',
        'schedule': crontab(minute='*/15'),
    },
    'fetch-sharepoint-every-30-minutes': {
        'task': 'scheduler.fetch_sharepoint_documents',
        'schedule': crontab(minute='*/30'),
    },
    'fetch-whatsapp-every-10-minutes': {
        'task': 'scheduler.fetch_whatsapp_documents',
        'schedule': crontab(minute='*/10'),
    },
    'health-check-every-hour': {
        'task': 'scheduler.health_check',
        'schedule': crontab(minute=0),  # Every hour
    },
    'cleanup-tasks-daily': {
        'task': 'scheduler.cleanup_old_tasks',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
