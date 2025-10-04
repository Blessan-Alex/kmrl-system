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

from models.database_models import Document
from services.websocket_manager import websocket_manager

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
        """Get MinIO client for file operations"""
        endpoint = os.getenv('MINIO_ENDPOINT', 'localhost').strip()
        user = os.getenv('MINIO_ACCESS_KEY', 'minioadmin').strip()
        password = os.getenv('MINIO_SECRET_KEY', 'minioadmin').strip()
        endpoint_url = f"http://{endpoint}:9000"
        
        return boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=user,
            aws_secret_access_key=password,
            config=BotocoreConfig(s3={'addressing_style': 'path'}, signature_version='s3v4')
        )
    
    async def store_file_with_db(self, file: UploadFile, source: str, db: Session, 
                                metadata: Dict[str, Any] = None, uploaded_by: str = None) -> Document:
        """
        Store file in MinIO and create PostgreSQL record
        """
        try:
            # Generate unique S3 key
            file_extension = os.path.splitext(file.filename)[1] if '.' in file.filename else ''
            s3_key = f"{uuid.uuid4()}{file_extension}"
            
            # Read file content
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Check for duplicate files
            duplicate_doc = db.query(Document).filter(Document.s3_key == s3_key).first()
            if duplicate_doc:
                logger.info(f"Duplicate file detected: {duplicate_doc.s3_key}")
                return duplicate_doc
            
            # Upload to MinIO
            minio_client = self.get_minio_client()
            try:
                # Ensure bucket exists
                try:
                    minio_client.head_bucket(Bucket=self.bucket_name)
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        minio_client.create_bucket(Bucket=self.bucket_name)
                        logger.info(f"Created bucket: {self.bucket_name}")
                
                # Upload file
                minio_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=content,
                    ContentType=file.content_type,
                    Metadata={
                        'original_filename': file.filename,
                        'source': source,
                        'file_hash': file_hash,
                        'uploaded_at': datetime.now().isoformat()
                    }
                )
                logger.info(f"Successfully uploaded '{file.filename}' to MinIO as '{s3_key}'")
                
            except Exception as e:
                logger.warning(f"MinIO upload failed, using local storage: {e}")
                # Fallback to local storage
                local_path = self.local_storage_path / source / datetime.now().strftime('%Y/%m/%d')
                local_path.mkdir(parents=True, exist_ok=True)
                local_file_path = local_path / f"{s3_key}"
                
                with open(local_file_path, 'wb') as f:
                    f.write(content)
                
                s3_key = str(local_file_path.relative_to(self.local_storage_path))
                logger.info(f"Stored file locally: {s3_key}")
            
            # Create PostgreSQL record
            db_document = Document(
                original_filename=file.filename,
                s3_key=s3_key,
                source=source,
                content_type=file.content_type,
                file_size=len(content),
                status="queued",
                document_metadata=metadata or {},
                uploaded_by=uploaded_by
            )
            
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            
            logger.info(f"Document stored in PostgreSQL: {db_document.id}")
            
            # Broadcast real-time update
            await websocket_manager.broadcast_document_update(
                db_document.id, "queued", 0, "Document uploaded and queued for processing"
            )
            
            return db_document
            
        except Exception as e:
            logger.error(f"Failed to store file with database: {e}")
            db.rollback()
            raise
    
    async def download_file(self, document: Document) -> bytes:
        """
        Download file content from MinIO or local storage
        """
        try:
            # First try MinIO (files stored with UUID names)
            try:
                minio_client = self.get_minio_client()
                response = minio_client.get_object(Bucket=self.bucket_name, Key=document.s3_key)
                return response['Body'].read()
            except Exception as minio_error:
                logger.warning(f"MinIO download failed for {document.s3_key}: {minio_error}")
                
                # Fallback to local storage
                local_file_path = self.local_storage_path / document.s3_key
                if local_file_path.exists():
                    with open(local_file_path, 'rb') as f:
                        return f.read()
                else:
                    raise FileNotFoundError(f"File not found in MinIO or local storage: {document.s3_key}")
                    
        except Exception as e:
            logger.error(f"Failed to download file {document.s3_key}: {e}")
            raise
    
    async def delete_file(self, document: Document, db: Session) -> bool:
        """
        Delete file from storage and database
        """
        try:
            # Delete from MinIO or local storage
            if not document.s3_key.startswith('/') and '/' in document.s3_key:
                # MinIO file
                minio_client = self.get_minio_client()
                try:
                    minio_client.delete_object(Bucket=self.bucket_name, Key=document.s3_key)
                    logger.info(f"Deleted file from MinIO: {document.s3_key}")
                except ClientError as e:
                    logger.warning(f"Failed to delete from MinIO: {e}")
            else:
                # Local file
                local_file_path = self.local_storage_path / document.s3_key
                if local_file_path.exists():
                    local_file_path.unlink()
                    logger.info(f"Deleted local file: {local_file_path}")
            
            # Delete from database
            db.delete(document)
            db.commit()
            
            logger.info(f"Deleted document from database: {document.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            db.rollback()
            return False
    
    async def get_file_info(self, document: Document) -> Dict[str, Any]:
        """
        Get file information and metadata
        """
        try:
            file_info = {
                "id": document.id,
                "filename": document.original_filename,
                "s3_key": document.s3_key,
                "source": document.source,
                "content_type": document.content_type,
                "file_size": document.file_size,
                "status": document.status.value,
                "upload_time": document.upload_time.isoformat(),
                "metadata": document.metadata
            }
            
            # Add MinIO-specific info if available
            if not document.s3_key.startswith('/') and '/' in document.s3_key:
                try:
                    minio_client = self.get_minio_client()
                    response = minio_client.head_object(Bucket=self.bucket_name, Key=document.s3_key)
                    file_info.update({
                        "last_modified": response['LastModified'].isoformat(),
                        "etag": response['ETag'],
                        "storage_class": response.get('StorageClass', 'STANDARD')
                    })
                except ClientError:
                    pass  # File might not exist in MinIO
            
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {}
    
    async def create_backup(self, document: Document) -> bool:
        """
        Create backup of document in backup bucket
        """
        try:
            minio_client = self.get_minio_client()
            
            # Download original file
            file_content = await self.download_file(document)
            
            # Upload to backup bucket
            backup_key = f"backup/{datetime.now().strftime('%Y/%m/%d')}/{document.s3_key}"
            minio_client.put_object(
                Bucket=self.backup_bucket,
                Key=backup_key,
                Body=file_content,
                ContentType=document.content_type,
                Metadata={
                    'original_filename': document.original_filename,
                    'source': document.source,
                    'backup_created_at': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Created backup: {backup_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
