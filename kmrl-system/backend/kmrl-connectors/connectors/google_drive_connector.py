"""
Google Drive Connector for KMRL Document Ingestion
Fetches documents from Google Drive using Google Drive API
"""

import os
import io
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import structlog
import requests

# Real Google API imports - no mocks!
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = structlog.get_logger()

class GoogleDriveConnector:
    """Connector for Google Drive document ingestion"""
    
    def __init__(self, folder_id: str = None, credentials_path: str = None):
        """
        Initialize Google Drive connector
        
        Args:
            folder_id: Google Drive folder ID to monitor
            credentials_path: Path to OAuth2 credentials JSON file
        """
        self.folder_id = folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.credentials_path = credentials_path or 'client_secret_581583075277-rm2ea74nlbkmfqt5ouktf6ou0o8bov9l.apps.googleusercontent.com.json'
        self.service = None
        self.credentials = None
        
        # KMRL document file extensions
        self.kmrl_extensions = [
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
            '.jpg', '.jpeg', '.png', '.tiff', '.dwg', '.dxf',
            '.step', '.stp', '.iges', '.igs', '.txt', '.rtf'
        ]
        
        # Department keywords for classification
        self.department_keywords = {
            'engineering': [
                'maintenance', 'repair', 'technical', 'equipment', 'machinery',
                'installation', 'calibration', 'inspection', 'troubleshooting',
                'schematic', 'blueprint', 'design', 'specification'
            ],
            'finance': [
                'invoice', 'payment', 'budget', 'cost', 'expense', 'financial',
                'accounting', 'billing', 'purchase', 'procurement', 'quote',
                'tender', 'contract', 'agreement'
            ],
            'safety': [
                'safety', 'incident', 'accident', 'hazard', 'risk', 'emergency',
                'evacuation', 'fire', 'security', 'compliance', 'audit',
                'training', 'certification', 'ppe'
            ],
            'operations': [
                'operation', 'schedule', 'planning', 'logistics', 'transport',
                'delivery', 'supply', 'inventory', 'stock', 'warehouse',
                'distribution', 'shipping', 'receiving'
            ],
            'field_operations': [
                'field', 'site', 'location', 'on-site', 'remote', 'mobile',
                'inspection', 'survey', 'measurement', 'reading', 'check',
                'verification', 'confirmation'
            ],
            'general': [
                'meeting', 'minutes', 'report', 'update', 'notification',
                'announcement', 'communication', 'correspondence', 'memo'
            ]
        }
    
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API using real OAuth2"""
        try:
            # Load credentials from file
            if not os.path.exists(self.credentials_path):
                logger.error(f"Credentials file not found: {self.credentials_path}")
                return False
                
            with open(self.credentials_path, 'r') as f:
                creds_data = json.load(f)
            
            # Create OAuth2 flow
            flow = Flow.from_client_config(
                creds_data,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            # Check for existing token
            token_file = 'token.json'
            if os.path.exists(token_file):
                self.credentials = Credentials.from_authorized_user_file(token_file)
            
            # Refresh or get new credentials
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    # Get authorization URL for real OAuth2 flow
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    print(f"Please visit this URL to authorize: {auth_url}")
                    auth_code = input("Enter the authorization code: ")
                    flow.fetch_token(code=auth_code)
                    self.credentials = flow.credentials
                
                # Save credentials for future use
                with open(token_file, 'w') as f:
                    f.write(self.credentials.to_json())
            
            logger.info("Google Drive authentication successful")
            return True
                
        except Exception as e:
            logger.error(f"Google Drive authentication failed: {e}")
            return False
    
    def get_service(self):
        """Get Google Drive service instance"""
        if not self.service:
            if self.authenticate():
                # Create real Google Drive service
                self.service = build('drive', 'v3', credentials=self.credentials)
                logger.info("Google Drive service initialized with real API")
            else:
                raise Exception("Failed to authenticate with Google Drive")
        
        return self.service
    
    def fetch_documents(self, credentials: Dict[str, str], options: Dict[str, Any] = None) -> List[Dict]:
        """
        Fetch documents from Google Drive
        
        Args:
            credentials: Authentication credentials
            options: Additional options for document fetching
            
        Returns:
            List of document dictionaries
        """
        try:
            service = self.get_service()
            documents = []
            
            # Get documents modified since last sync
            last_sync = self.get_last_sync_time()
            query = f"modifiedTime > '{last_sync.isoformat()}'"
            
            if self.folder_id:
                query += f" and '{self.folder_id}' in parents"
            
            # Search for documents
            results = service.files().list(
                q=query,
                fields="files(id,name,mimeType,modifiedTime,size,webViewLink)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} files in Google Drive")
            
            for file_info in files:
                # Check if it's a KMRL document
                if self.is_kmrl_document(file_info['name']):
                    # Download file content
                    file_content = self.download_file(file_info['id'])
                    
                    if file_content:
                        # Create document object
                        document = {
                            'source': 'google_drive',
                            'filename': file_info['name'],
                            'content': file_content,
                            'content_type': file_info.get('mimeType', 'application/octet-stream'),
                            'metadata': {
                                'file_id': file_info['id'],
                                'modified_time': file_info.get('modifiedTime'),
                                'size': file_info.get('size'),
                                'web_view_link': file_info.get('webViewLink'),
                                'folder_id': self.folder_id
                            },
                            'document_id': f"gdrive_{file_info['id']}",
                            'uploaded_at': datetime.now(),
                            'language': self.detect_language(file_info['name']),
                            'department': self.classify_department(file_info['name'])
                        }
                        
                        documents.append(document)
                        logger.info(f"Processed document: {file_info['name']}")
            
            # Update last sync time
            self.update_sync_time(datetime.now())
            
            logger.info(f"Google Drive fetch completed: {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Google Drive fetch failed: {e}")
            raise Exception(f"Google Drive connector failed: {str(e)}")
    
    def download_file(self, file_id: str) -> Optional[bytes]:
        """Download file content from Google Drive"""
        try:
            service = self.get_service()
            request = service.files().get_media(fileId=file_id)
            file_content = request.execute()
            return file_content
        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {e}")
            return None
    
    def is_kmrl_document(self, filename: str) -> bool:
        """Check if file is a KMRL document based on extension"""
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in self.kmrl_extensions)
    
    def detect_language(self, text: str) -> str:
        """Detect language of document (English, Malayalam, or Mixed)"""
        # Malayalam Unicode range
        malayalam_chars = "അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹളഴറ"
        
        malayalam_count = sum(1 for char in text if char in malayalam_chars)
        english_count = sum(1 for char in text if char.isalpha() and char not in malayalam_chars)
        
        if malayalam_count > 0 and english_count > 0:
            return 'mixed'
        elif malayalam_count > 0:
            return 'malayalam'
        else:
            return 'english'
    
    def classify_department(self, filename: str) -> str:
        """Classify document department based on filename"""
        filename_lower = filename.lower()
        
        # Check for department keywords
        for department, keywords in self.department_keywords.items():
            if any(keyword in filename_lower for keyword in keywords):
                return department
        
        return 'general'
    
    def get_content_type(self, filename: str, mime_type: str = None) -> str:
        """Get content type for file"""
        if mime_type:
            return mime_type
        
        # Map file extensions to MIME types
        extension = os.path.splitext(filename)[1].lower()
        mime_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.txt': 'text/plain'
        }
        
        return mime_map.get(extension, 'application/octet-stream')
    
    def get_last_sync_time(self) -> datetime:
        """Get last successful sync time from Redis"""
        try:
            import redis
            r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
            last_sync = r.get('connector_state:googledriveconnector')
            if last_sync:
                return datetime.fromisoformat(last_sync.decode())
        except Exception as e:
            logger.error(f"Failed to get last sync time: {e}")
        
        return datetime.min
    
    def update_sync_time(self, sync_time: datetime):
        """Update last successful sync time in Redis"""
        try:
            import redis
            r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
            r.set('connector_state:googledriveconnector', sync_time.isoformat())
        except Exception as e:
            logger.error(f"Failed to update sync time: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get connector sync status"""
        try:
            import redis
            r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
            
            last_sync = r.get('connector_state:googledriveconnector')
            processed_count = r.scard('processed_docs:googledriveconnector')
            
            return {
                'connector': 'GoogleDriveConnector',
                'last_sync': last_sync.decode() if last_sync else 'Never',
                'processed_documents': processed_count,
                'status': 'active' if last_sync else 'inactive'
            }
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {'connector': 'GoogleDriveConnector', 'status': 'error', 'error': str(e)}


# Real Google Drive API - no mocks!
