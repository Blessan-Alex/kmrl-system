"""
Storage Service for KMRL Documents
Handles file storage using MinIO/S3
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any
import structlog
from minio import Minio
from fastapi import UploadFile

logger = structlog.get_logger()

class StorageService:
    """Storage service for KMRL documents"""
    
    def __init__(self):
        self.minio_client = Minio(
            os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=False
        )
        self.bucket_name = "kmrl-documents"
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists"""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to create bucket: {e}")
            raise
    
    async def store_file(self, file: UploadFile, source: str) -> Dict[str, Any]:
        """Store file in MinIO and return storage info"""
        try:
            # Generate unique file path
            file_id = str(uuid.uuid4())
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            object_name = f"{source}/{datetime.now().strftime('%Y/%m/%d')}/{file_id}.{file_extension}"
            
            # Read file content
            content = await file.read()
            
            # Upload to MinIO
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=content,
                length=len(content),
                content_type=file.content_type
            )
            
            logger.info(f"File stored successfully: {object_name}")
            
            return {
                "path": object_name,
                "bucket": self.bucket_name,
                "file_id": file_id,
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"Failed to store file: {e}")
            raise Exception(f"File storage failed: {str(e)}")
    
    def get_file_url(self, object_name: str, expires_in_seconds: int = 3600) -> str:
        """Get presigned URL for file access"""
        try:
            return self.minio_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires_in_seconds
            )
        except Exception as e:
            logger.error(f"Failed to generate file URL: {e}")
            raise Exception(f"Failed to generate file URL: {str(e)}")
    
    def delete_file(self, object_name: str) -> bool:
        """Delete file from storage"""
        try:
            self.minio_client.remove_object(self.bucket_name, object_name)
            logger.info(f"File deleted: {object_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
