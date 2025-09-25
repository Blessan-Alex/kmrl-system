"""
Enhanced Storage Service for KMRL Gateway
PostgreSQL-integrated file storage with MinIO and Redis caching
"""

import os
import uuid
import hashlib
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile
from botocore.exceptions import ClientError
from botocore.client import Config as BotocoreConfig
import structlog

from models.document import Document
from services.monitoring.websocket_manager import websocket_manager

logger = structlog.get_logger()

class EnhancedStorageService:
    """Enhanced storage service with PostgreSQL integration"""
    
    def __init__(self):
        self.bucket_name = os.getenv('MINIO_BUCKET_NAME', 'kmrl-documents')
        self.backup_bucket = f"{self.bucket_name}-backup"
        self.local_storage_path = Path(os.getenv("LOCAL_STORAGE_PATH", "./storage"))
        self._ensure_local_storage()
    
    def _ensure_local_storage(self):
        """Ensure local storage directory exists"""
        try:
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Local storage path: {self.local_storage_path}")
        except Exception as e:
            logger.error(f"Failed to create local storage: {e}")
            raise
    
    def get_minio_client(self):
        """Get MinIO client for file operations with improved error handling"""
        try:
            endpoint = os.getenv('MINIO_ENDPOINT', 'localhost').strip()
            user = os.getenv('MINIO_ACCESS_KEY', 'minioadmin').strip()
            password = os.getenv('MINIO_SECRET_KEY', 'minioadmin').strip()
            endpoint_url = f"http://{endpoint}:9000"
            
            client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=user,
                aws_secret_access_key=password,
                config=BotocoreConfig(s3={'addressing_style': 'path'}, signature_version='s3v4')
            )
            
            # Test connection
            try:
                client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"MinIO connection successful: {endpoint_url}")
                return client
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    # Bucket doesn't exist, try to create it
                    try:
                        client.create_bucket(Bucket=self.bucket_name)
                        logger.info(f"Created MinIO bucket: {self.bucket_name}")
                        return client
                    except ClientError as create_error:
                        logger.error(f"Failed to create MinIO bucket: {create_error}")
                        raise Exception(f"MinIO bucket creation failed: {create_error}")
                else:
                    logger.error(f"MinIO connection failed: {e}")
                    raise Exception(f"MinIO connection failed: {e}")
                    
        except Exception as e:
            logger.error(f"MinIO client creation failed: {e}")
            raise Exception(f"MinIO client creation failed: {e}")
    
    async def store_file(self, file: UploadFile, source: str, metadata: Dict[str, Any] = None, db: Session = None) -> Dict[str, Any]:
        """Store file with basic functionality"""
        try:
            # Generate unique file path
            file_id = str(uuid.uuid4())
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            object_name = f"{source}/{datetime.now().strftime('%Y/%m/%d')}/{file_id}.{file_extension}"
            
            # Read file content
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Store in MinIO
            try:
                client = self.get_minio_client()
                client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=content,
                    ContentType=file.content_type,
                    Metadata={
                        'original_filename': file.filename,
                        'source': source,
                        'file_hash': file_hash,
                        'uploaded_at': datetime.now().isoformat()
                    }
                )
                logger.info(f"File stored in MinIO: {object_name}")
            except Exception as e:
                logger.warning(f"MinIO storage failed: {e}")
                # Continue with local storage only
            
            # Store locally for processing
            local_path = self.local_storage_path / object_name
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(content)
            
            # Create database record if db is provided
            document = None
            if db:
                document = Document(
                    original_filename=file.filename,
                    s3_key=object_name,
                    source=source,
                    content_type=file.content_type,
                    file_size=len(content),
                    status="queued",
                    document_metadata=metadata or {},
                    uploaded_by="system"
                )
                db.add(document)
                db.commit()
                db.refresh(document)
                logger.info(f"Document created in database: {document.id}")
            
            return {
                'object_name': object_name,
                'file_id': file_id,
                'file_hash': file_hash,
                'local_path': str(local_path),
                'size': len(content),
                'document': document
            }
            
        except Exception as e:
            logger.error(f"File storage failed: {e}")
            raise
    
    async def store_file_with_db(self, file: UploadFile, source: str, db: Session, metadata: Dict[str, Any] = None, uploaded_by: str = None) -> Document:
        """Store file with database integration"""
        try:
            # Store file first
            storage_result = await self.store_file(file, source, metadata, db)
            
            # Create database record
            document = Document(
                original_filename=file.filename,
                s3_key=storage_result['object_name'],
                source=source,
                content_type=file.content_type,
                file_size=storage_result['size'],
                status="queued",
                document_metadata=metadata or {},
                uploaded_by=uploaded_by or "system"
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            logger.info(f"Document created in database: {document.id}")
            return document
            
        except Exception as e:
            logger.error(f"Database storage failed: {e}")
            db.rollback()
            raise
    
    async def download_file(self, document: Document) -> bytes:
        """Download file content"""
        try:
            client = self.get_minio_client()
            response = client.get_object(Bucket=self.bucket_name, Key=document.s3_key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"File download failed: {e}")
            # Fallback to local storage
            local_path = self.local_storage_path / document.s3_key
            if local_path.exists():
                return local_path.read_bytes()
            else:
                raise Exception(f"File not found: {document.s3_key}")