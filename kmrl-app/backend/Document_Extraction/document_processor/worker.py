"""
Document processing worker - main entry point
"""
import os
import sys
from pathlib import Path
from loguru import logger

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import LOG_LEVEL, LOG_FILE
from celery_app import celery_app


def setup_logging():
    """Setup logging configuration"""
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file logger
    logger.add(
        LOG_FILE,
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days"
    )


def main():
    """Main worker entry point"""
    setup_logging()
    
    logger.info("Starting KMRL Document Processing Worker")
    logger.info(f"Log level: {LOG_LEVEL}")
    logger.info(f"Log file: {LOG_FILE}")
    
    # Start Celery worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--queues=document_processing,image_processing,ocr_processing',
        '--concurrency=4',
        '--hostname=kmrl-doc-worker@%h'
    ])


if __name__ == '__main__':
    main()
