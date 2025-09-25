"""
Enhanced Storage Service for KMRL Documents
Comprehensive file storage with backup, versioning, and security
"""

import os
import uuid
import hashlib
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import structlog
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
import redis
import json

logger = structlog.get_logger()

class StorageService:
    """Enhanced storage service for KMRL documents"""
    
    def __init__(self):
        self.minio_client = Minio(
            os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )
        self.bucket_name = "kmrl-documents"
        self.backup_bucket = "kmrl-documents-backup"
        self.redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        self.local_storage_path = Path(os.getenv("LOCAL_STORAGE_PATH", "./storage"))
        self._ensure_bucket_exists()
        self._ensure_local_storage()
    
    def _ensure_bucket_exists(self):
        """Ensure the buckets exist"""
        try:
            # Create main bucket
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            
            # Create backup bucket
            if not self.minio_client.bucket_exists(self.backup_bucket):
                self.minio_client.make_bucket(self.backup_bucket)
                logger.info(f"Created backup bucket: {self.backup_bucket}")
                
        except Exception as e:
            logger.warning(f"MinIO not available, using local storage only: {e}")
            # Don't raise the exception, just log a warning
            # The system can work without MinIO for testing
    
    def _ensure_local_storage(self):
        """Ensure local storage directory exists"""
        try:
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Local storage path: {self.local_storage_path}")
        except Exception as e:
            logger.error(f"Failed to create local storage: {e}")
            raise
    
    async def store_file(self, file: UploadFile, source: str) -> Dict[str, Any]:
        """Enhanced file storage with backup and metadata"""
        try:
            # Generate unique file path
            file_id = str(uuid.uuid4())
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            object_name = f"{source}/{datetime.now().strftime('%Y/%m/%d')}/{file_id}.{file_extension}"
            
            # Read file content
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Check for duplicate files
            duplicate_info = await self._check_duplicate_file(file_hash)
            if duplicate_info:
                logger.info(f"Duplicate file detected: {duplicate_info['path']}")
                return duplicate_info
            
            # Try to store in MinIO, fall back to local storage if not available
            import io
            content_stream = io.BytesIO(content)
            
            try:
                self.minio_client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name,
                    data=content_stream,
                    length=len(content),
                    content_type=file.content_type,
                    metadata={
                        'original_filename': file.filename,
                        'source': source,
                        'file_hash': file_hash,
                        'uploaded_at': datetime.now().isoformat()
                    }
                )
                
                # Create backup
                await self._create_backup(object_name, content_stream, file.content_type)
                logger.info(f"File stored in MinIO: {object_name}")
                
            except Exception as e:
                logger.warning(f"MinIO storage failed, using local storage only: {e}")
                # Continue with local storage only
            
            # Store locally for processing
            local_path = self.local_storage_path / object_name
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(content)
            
            # Store metadata in Redis
            await self._store_file_metadata(file_id, {
                'object_name': object_name,
                'bucket': self.bucket_name,
                'file_hash': file_hash,
                'size': len(content),
                'content_type': file.content_type,
                'source': source,
                'local_path': str(local_path),
                'uploaded_at': datetime.now().isoformat()
            })
            
            logger.info(f"File stored successfully: {object_name}")
            
            return {
                "path": object_name,
                "bucket": self.bucket_name if hasattr(self, 'minio_client') else "local",
                "file_id": file_id,
                "size": len(content),
                "file_hash": file_hash,
                "local_path": str(local_path),
                "storage_type": "minio" if hasattr(self, 'minio_client') else "local"
            }
            
        except Exception as e:
            logger.error(f"Failed to store file: {e}")
            raise Exception(f"File storage failed: {str(e)}")
    
    async def _check_duplicate_file(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Check if file already exists based on hash"""
        try:
            # Check Redis for existing file hash
            existing_file = self.redis_client.get(f"file_hash:{file_hash}")
            if existing_file:
                return json.loads(existing_file)
            return None
        except Exception as e:
            logger.error(f"Failed to check duplicate file: {e}")
            return None
    
    async def _create_backup(self, object_name: str, content_stream, content_type: str):
        """Create backup of file"""
        try:
            backup_name = f"backup/{object_name}"
            # Reset stream position for backup
            content_stream.seek(0)
            self.minio_client.put_object(
                bucket_name=self.backup_bucket,
                object_name=backup_name,
                data=content_stream,
                length=content_stream.getbuffer().nbytes,
                content_type=content_type
            )
            logger.info(f"Backup created: {backup_name}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    async def _store_file_metadata(self, file_id: str, metadata: Dict[str, Any]):
        """Store file metadata in Redis"""
        try:
            # Store file metadata
            self.redis_client.hset(f"file_metadata:{file_id}", mapping=metadata)
            
            # Store file hash mapping
            self.redis_client.set(f"file_hash:{metadata['file_hash']}", json.dumps(metadata))
            
            # Set expiration (30 days)
            self.redis_client.expire(f"file_metadata:{file_id}", 86400 * 30)
            self.redis_client.expire(f"file_hash:{metadata['file_hash']}", 86400 * 30)
            
        except Exception as e:
            logger.error(f"Failed to store file metadata: {e}")
    
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
    
    async def get_file(self, object_name: str) -> bytes:
        """Get file content from storage"""
        try:
            response = self.minio_client.get_object(self.bucket_name, object_name)
            return response.read()
        except Exception as e:
            logger.error(f"Failed to get file: {e}")
            raise Exception(f"Failed to get file: {str(e)}")
    
    async def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from Redis"""
        try:
            metadata = self.redis_client.hgetall(f"file_metadata:{file_id}")
            if metadata:
                return metadata
            return None
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None
    
    def delete_file(self, object_name: str) -> bool:
        """Delete file from storage"""
        try:
            # Delete from main bucket
            self.minio_client.remove_object(self.bucket_name, object_name)
            
            # Delete from backup bucket
            backup_name = f"backup/{object_name}"
            try:
                self.minio_client.remove_object(self.backup_bucket, backup_name)
            except S3Error:
                pass  # Backup might not exist
            
            # Delete local file
            local_path = self.local_storage_path / object_name
            if local_path.exists():
                local_path.unlink()
            
            logger.info(f"File deleted: {object_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            # Get bucket statistics
            main_bucket_stats = self._get_bucket_statistics(self.bucket_name)
            backup_bucket_stats = self._get_bucket_statistics(self.backup_bucket)
            
            # Get local storage statistics
            local_stats = self._get_local_storage_statistics()
            
            return {
                "main_bucket": main_bucket_stats,
                "backup_bucket": backup_bucket_stats,
                "local_storage": local_stats,
                "total_files": main_bucket_stats["file_count"] + backup_bucket_stats["file_count"],
                "total_size_bytes": main_bucket_stats["total_size"] + backup_bucket_stats["total_size"]
            }
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {"error": str(e)}
    
    def _get_bucket_statistics(self, bucket_name: str) -> Dict[str, Any]:
        """Get statistics for a bucket"""
        try:
            objects = list(self.minio_client.list_objects(bucket_name, recursive=True))
            total_size = 0
            file_count = len(objects)
            
            for obj in objects:
                total_size += obj.size
            
            return {
                "bucket_name": bucket_name,
                "file_count": file_count,
                "total_size": total_size,
                "average_size": total_size / file_count if file_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to get bucket statistics: {e}")
            return {"bucket_name": bucket_name, "file_count": 0, "total_size": 0, "average_size": 0}
    
    def _get_local_storage_statistics(self) -> Dict[str, Any]:
        """Get local storage statistics"""
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.local_storage_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                "path": str(self.local_storage_path),
                "file_count": file_count,
                "total_size": total_size,
                "average_size": total_size / file_count if file_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to get local storage statistics: {e}")
            return {"path": str(self.local_storage_path), "file_count": 0, "total_size": 0, "average_size": 0}
    
    async def cleanup_old_files(self, days: int = 30) -> Dict[str, Any]:
        """Clean up old files from local storage"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_files = 0
            freed_space = 0
            
            for file_path in self.local_storage_path.rglob('*'):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_files += 1
                        freed_space += file_size
            
            logger.info(f"Cleaned up {cleaned_files} files, freed {freed_space} bytes")
            
            return {
                "cleaned_files": cleaned_files,
                "freed_space_bytes": freed_space,
                "cutoff_date": cutoff_date.isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return {"error": str(e)}
