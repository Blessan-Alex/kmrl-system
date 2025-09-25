"""
Unified Celery Configuration for KMRL System
Single configuration for all Celery apps to prevent conflicts
"""

import os
from celery.schedules import crontab

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Celery Configuration
CELERY_CONFIG = {
    # Broker and Backend with key prefix to avoid conflicts
    'broker_url': REDIS_URL,
    'result_backend': REDIS_URL,
    'result_backend_transport_options': {'global_keyprefix': 'kmrl:'},
    'broker_transport_options': {'global_keyprefix': 'kmrl:'},
    
    # Serialization
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    
    # Timezone
    'timezone': 'UTC',
    'enable_utc': True,
    
    # Task Settings
    'task_track_started': True,
    'task_time_limit': 300,  # 5 minutes
    'task_soft_time_limit': 240,  # 4 minutes
    'worker_prefetch_multiplier': 1,
    'task_acks_late': True,
    'worker_disable_rate_limits': True,
    
    # Fix deprecation warning
    'broker_connection_retry_on_startup': True,
    
    # Task Discovery
    'include': [
        'connectors.tasks.sync_tasks',
        'services.processing.document_processor',
        'workers.document_worker.worker',
        'workers.rag_worker.worker',
        'workers.notification_worker.worker',
    ],
    
    # Beat Schedule - Only Active Connectors (Gmail, Google Drive)
    'beat_schedule': {
        'sync-gmail-incremental': {
            'task': 'connectors.tasks.sync_tasks.sync_gmail_incremental',
            'schedule': 120.0,  # Every 2 minutes
        },
        'sync-google-drive-incremental': {
            'task': 'connectors.tasks.sync_tasks.sync_google_drive_incremental',
            'schedule': 120.0,  # Every 2 minutes
        },
        'sync-gmail-historical': {
            'task': 'connectors.tasks.sync_tasks.sync_gmail_historical',
            'schedule': 120.0,  # Every 2 minutes
            'args': [365],  # 1 year of history
        },
        'sync-google-drive-historical': {
            'task': 'connectors.tasks.sync_tasks.sync_google_drive_historical',
            'schedule': 120.0,  # Every 2 minutes
            'args': [365],  # 1 year of history
        },
        'health-check-connectors': {
            'task': 'connectors.tasks.sync_tasks.health_check_connectors',
            'schedule': 60.0,  # Every minute
        },
        # Disabled connectors - commented out to prevent startup issues
        # 'sync-maximo-incremental': {
        #     'task': 'connectors.tasks.sync_tasks.sync_maximo_incremental',
        #     'schedule': 120.0,  # Every 2 minutes
        # },
        # 'sync-whatsapp-incremental': {
        #     'task': 'connectors.tasks.sync_tasks.sync_whatsapp_incremental',
        #     'schedule': 120.0,  # Every 2 minutes
        # },
    },
    
    # Task Routes with namespaced queues
    'task_routes': {
        'connectors.tasks.sync_tasks.*': {'queue': 'kmrl:connectors'},
        'services.processing.document_processor.*': {'queue': 'kmrl:documents'},
        'workers.document_worker.*': {'queue': 'kmrl:documents'},
        'workers.rag_worker.*': {'queue': 'kmrl:rag'},
        'workers.notification_worker.*': {'queue': 'kmrl:notifications'},
    },
    
    # Queue Configuration with namespace to avoid Redis key conflicts
    'task_default_queue': 'kmrl:default',
    'task_queues': {
        'kmrl:default': {
            'exchange': 'kmrl:default',
            'routing_key': 'kmrl:default',
        },
        'kmrl:connectors': {
            'exchange': 'kmrl:connectors',
            'routing_key': 'kmrl:connectors',
        },
        'kmrl:documents': {
            'exchange': 'kmrl:documents',
            'routing_key': 'kmrl:documents',
        },
        'kmrl:rag': {
            'exchange': 'kmrl:rag',
            'routing_key': 'kmrl:rag',
        },
        'kmrl:notifications': {
            'exchange': 'kmrl:notifications',
            'routing_key': 'kmrl:notifications',
        },
    },
    
    # Worker Settings
    'worker_hijack_root_logger': False,
    'worker_log_color': True,
    'worker_log_format': '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    'worker_task_log_format': '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
}
