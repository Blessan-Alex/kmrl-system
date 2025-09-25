"""
Unified Configuration for KMRL System
Centralized configuration management
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class UnifiedConfig:
    """Unified configuration for all KMRL services"""
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://kmrl_user:kmrl_password@localhost:5432/kmrl_db')
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    DATABASE_PORT = int(os.getenv('DATABASE_PORT', '5432'))
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'kmrl_db')
    DATABASE_USER = os.getenv('DATABASE_USER', 'kmrl_user')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'kmrl_password')
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    
    # MinIO Configuration
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'kmrl-documents')
    MINIO_SECURE = os.getenv('MINIO_SECURE', 'False').lower() == 'true'
    
    # Gateway Configuration
    GATEWAY_HOST = os.getenv('GATEWAY_HOST', '0.0.0.0')
    GATEWAY_PORT = int(os.getenv('GATEWAY_PORT', '3000'))
    GATEWAY_DEBUG = os.getenv('GATEWAY_DEBUG', 'False').lower() == 'true'
    
    # Connector Configuration
    CONNECTOR_SYNC_INTERVAL = int(os.getenv('CONNECTOR_SYNC_INTERVAL', '120'))  # 2 minutes
    CONNECTOR_MAX_RETRIES = int(os.getenv('CONNECTOR_MAX_RETRIES', '3'))
    CONNECTOR_TIMEOUT = int(os.getenv('CONNECTOR_TIMEOUT', '300'))  # 5 minutes
    
    # Celery Configuration
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    
    # Security Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    
    # API Keys
    API_KEYS = {
        'gmail': os.getenv('GMAIL_API_KEY', 'connector-email'),
        'google_drive': os.getenv('GOOGLE_DRIVE_API_KEY', 'connector-google-drive'),
        'maximo': os.getenv('MAXIMO_API_KEY', 'connector-maximo'),
        'whatsapp': os.getenv('WHATSAPP_API_KEY', 'connector-whatsapp'),
        'sharepoint': os.getenv('SHAREPOINT_API_KEY', 'connector-sharepoint'),
        'email': os.getenv('EMAIL_API_KEY', 'connector-email')
    }
    
    # File Processing Configuration
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '209715200'))  # 200MB
    ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', '.pdf,.docx,.xlsx,.txt,.jpg,.png').split(',')
    BLOCKED_EXTENSIONS = os.getenv('BLOCKED_EXTENSIONS', '.exe,.bat,.sh,.ps1').split(',')
    
    # Monitoring Configuration
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))  # 1 minute
    METRICS_COLLECTION_INTERVAL = int(os.getenv('METRICS_COLLECTION_INTERVAL', '30'))  # 30 seconds
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/kmrl.log')
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'url': cls.DATABASE_URL,
            'host': cls.DATABASE_HOST,
            'port': cls.DATABASE_PORT,
            'name': cls.DATABASE_NAME,
            'user': cls.DATABASE_USER,
            'password': cls.DATABASE_PASSWORD
        }
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Get Redis configuration"""
        return {
            'url': cls.REDIS_URL,
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'db': cls.REDIS_DB
        }
    
    @classmethod
    def get_minio_config(cls) -> Dict[str, Any]:
        """Get MinIO configuration"""
        return {
            'endpoint': cls.MINIO_ENDPOINT,
            'access_key': cls.MINIO_ACCESS_KEY,
            'secret_key': cls.MINIO_SECRET_KEY,
            'bucket': cls.MINIO_BUCKET,
            'secure': cls.MINIO_SECURE
        }
    
    @classmethod
    def get_celery_config(cls) -> Dict[str, Any]:
        """Get Celery configuration"""
        return {
            'broker_url': cls.CELERY_BROKER_URL,
            'result_backend': cls.CELERY_RESULT_BACKEND,
            'task_serializer': cls.CELERY_TASK_SERIALIZER,
            'accept_content': cls.CELERY_ACCEPT_CONTENT,
            'result_serializer': cls.CELERY_RESULT_SERIALIZER,
            'timezone': cls.CELERY_TIMEZONE,
            'enable_utc': cls.CELERY_ENABLE_UTC
        }
