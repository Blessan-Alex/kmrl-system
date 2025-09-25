"""
Google Drive Connector for KMRL Document Ingestion
Implements Google Drive API-based file processing with incremental sync
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Generator, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import structlog

from ..base.enhanced_base_connector import EnhancedBaseConnector, Document, SyncState

logger = structlog.get_logger()

# Google Drive API scopes
GDRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file"
]

class GoogleDriveConnector(EnhancedBaseConnector):
    """Google Drive connector for processing files and documents"""
    
    def __init__(self, api_endpoint: str, sync_interval_minutes: int = 2):
        super().__init__("google_drive", api_endpoint, sync_interval_minutes)
        
        # Use hardcoded paths like reference implementation
        self.credentials_file = os.path.join(os.path.dirname(__file__), "..", "..", "credentials.json")
        self.token_file = os.path.join(os.path.dirname(__file__), "..", "..", "token.json")
        self.oauth2_port = int(os.getenv('OAUTH2_REDIRECT_PORT', '8080'))
        
        # Google Drive specific settings
        self.target_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.skip_google_docs = os.getenv('SKIP_GOOGLE_DOCS', 'true').lower() == 'true'
        
        self._drive_service = None
        
        # KMRL document file extensions (from reference)
        self.kmrl_extensions = [
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
            '.jpg', '.jpeg', '.png', '.tiff', '.dwg', '.dxf',
            '.step', '.stp', '.iges', '.igs', '.txt', '.rtf'
        ]
        
        # Department keywords for classification (from reference)
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
        
        logger.info("Google Drive connector initialized", 
                   target_folder_id=self.target_folder_id,
                   credentials_file=self.credentials_file)
    
    def _authenticate_drive(self) -> bool:
        """Authenticate with Google Drive API"""
        try:
            creds = None
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, GDRIVE_SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error("Google Drive credentials file not found", file=self.credentials_file)
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, GDRIVE_SCOPES
                    )
                    creds = flow.run_local_server(port=self.oauth2_port)
                
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())
            
            self._drive_service = build("drive", "v3", credentials=creds)
            logger.info("Google Drive authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Google Drive authentication failed: {e}")
            return False
    
    def _get_drive_service(self):
        """Get authenticated Google Drive service"""
        if not self._drive_service:
            if not self._authenticate_drive():
                raise Exception("Failed to authenticate with Google Drive")
        return self._drive_service
    
    def _list_files(self, query: str = None, page_size: int = 100, 
                   page_token: str = None) -> Dict[str, Any]:
        """List files from Google Drive with optional query"""
        try:
            service = self._get_drive_service()
            
            params = {
                'pageSize': page_size,
                'fields': 'nextPageToken, files(id, name, mimeType, size, modifiedTime, createdTime, parents, owners)',
                'orderBy': 'modifiedTime desc'
            }
            
            if query:
                params['q'] = query
            
            if page_token:
                params['pageToken'] = page_token
            
            results = service.files().list(**params).execute()
            
            files = results.get('files', [])
            next_token = results.get('nextPageToken')
            
            logger.debug(f"Retrieved {len(files)} files from Google Drive")
            return {
                'files': files,
                'next_page_token': next_token
            }
            
        except HttpError as error:
            logger.error(f"Google Drive list files failed: {error}")
            raise
    
    def _download_file(self, file_id: str, file_name: str) -> Optional[bytes]:
        """Download file content from Google Drive"""
        try:
            service = self._get_drive_service()
            
            # Get file metadata first
            file_metadata = service.files().get(fileId=file_id).execute()
            mime_type = file_metadata.get('mimeType', '')
            
            # Skip Google Docs/Sheets/Slides if configured
            if self.skip_google_docs and mime_type.startswith('application/vnd.google-apps'):
                logger.info(f"Skipping Google Docs file: {file_name} ({mime_type})")
                return None
            
            # Download file content
            request = service.files().get_media(fileId=file_id)
            file_content = request.execute()
            
            logger.debug(f"Downloaded file: {file_name} ({len(file_content)} bytes)")
            return file_content
            
        except HttpError as error:
            logger.error(f"Failed to download file {file_id} ({file_name}): {error}")
            return None
    
    def _create_document_from_file(self, file_info: Dict[str, Any], 
                                  file_content: bytes) -> Document:
        """Create Document object from Google Drive file"""
        # Parse dates
        try:
            modified_time = datetime.fromisoformat(file_info['modifiedTime'].replace('Z', '+00:00'))
        except:
            modified_time = datetime.now()
        
        try:
            created_time = datetime.fromisoformat(file_info['createdTime'].replace('Z', '+00:00'))
        except:
            created_time = modified_time
        
        # Get owner information
        owners = file_info.get('owners', [])
        owner_email = owners[0].get('emailAddress', 'unknown') if owners else 'unknown'
        
        metadata = {
            'file_id': file_info['id'],
            'file_name': file_info['name'],
            'mime_type': file_info.get('mimeType', ''),
            'file_size': file_info.get('size', len(file_content)),
            'modified_time': modified_time.isoformat(),
            'created_time': created_time.isoformat(),
            'owner_email': owner_email,
            'parents': file_info.get('parents', []),
            'source_type': 'google_drive_file'
        }
        
        # Detect language from filename
        language = self._detect_language(file_info['name'])
        
        return Document(
            source="google_drive",
            filename=file_info['name'],
            content=file_content,
            content_type=file_info.get('mimeType', 'application/octet-stream'),
            metadata=metadata,
            uploaded_at=modified_time,
            language=language,
            original_path=f"gdrive://{file_info['id']}"
        )
    
    def _detect_language(self, filename: str) -> str:
        """Simple language detection for Malayalam/English"""
        # Basic Malayalam Unicode range detection
        malayalam_chars = sum(1 for char in filename if '\u0D00' <= char <= '\u0D7F')
        total_chars = len([c for c in filename if c.isalpha()])
        
        if total_chars > 0 and malayalam_chars / total_chars > 0.1:
            return "mal"
        return "eng"
    
    def _build_query(self, state: SyncState, incremental: bool = True) -> str:
        """Build Google Drive query for file filtering"""
        query_parts = []
        
        # Filter by folder if specified
        if self.target_folder_id:
            query_parts.append(f"'{self.target_folder_id}' in parents")
        
        # Exclude Google Docs if configured
        if self.skip_google_docs:
            query_parts.append("mimeType != 'application/vnd.google-apps.document'")
            query_parts.append("mimeType != 'application/vnd.google-apps.spreadsheet'")
            query_parts.append("mimeType != 'application/vnd.google-apps.presentation'")
            query_parts.append("mimeType != 'application/vnd.google-apps.form'")
            query_parts.append("mimeType != 'application/vnd.google-apps.drawing'")
        
        # Add incremental sync filter
        if incremental and state.last_sync_time > datetime.min:
            # Convert to RFC 3339 format for Google Drive API
            time_filter = state.last_sync_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            query_parts.append(f"modifiedTime > '{time_filter}'")
        
        # Exclude trashed files
        query_parts.append("trashed = false")
        
        return " and ".join(query_parts)
    
    def fetch_documents_incremental(self, credentials: Dict[str, str], 
                                   state: SyncState,
                                   batch_size: int = 50) -> Generator[List[Document], None, None]:
        """Fetch new/modified files from Google Drive incrementally"""
        try:
            query = self._build_query(state, incremental=True)
            logger.info(f"Google Drive incremental query: {query}")
            
            current_batch = []
            page_token = None
            
            while True:
                # Get files from Google Drive
                result = self._list_files(query=query, page_size=batch_size, page_token=page_token)
                files = result['files']
                page_token = result['next_page_token']
                
                if not files:
                    logger.info("No new/modified files found in Google Drive")
                    break
                
                for file_info in files:
                    try:
                        # Download file content
                        file_content = self._download_file(file_info['id'], file_info['name'])
                        
                        if file_content is not None:
                            document = self._create_document_from_file(file_info, file_content)
                            current_batch.append(document)
                            
                            if len(current_batch) >= batch_size:
                                yield current_batch
                                current_batch = []
                    
                    except Exception as e:
                        logger.error(f"Failed to process file {file_info.get('name', 'unknown')}: {e}")
                        continue
                
                # Yield remaining documents
                if current_batch:
                    yield current_batch
                    current_batch = []
                
                # Check if we should continue
                if not page_token:
                    break
                
                # Small delay to prevent rate limiting
                import time
                time.sleep(0.1)
            
            logger.info("Google Drive incremental fetch completed")
                
        except Exception as e:
            logger.error(f"Google Drive incremental fetch failed: {e}")
            raise
    
    def fetch_documents_historical(self, credentials: Dict[str, str], 
                                  start_date: datetime,
                                  batch_size: int = 100) -> Generator[List[Document], None, None]:
        """Fetch historical files from Google Drive"""
        try:
            logger.info(f"Starting Google Drive historical fetch from {start_date}")
            
            # Build query for historical sync (no time filter)
            query = self._build_query(SyncState(last_sync_time=datetime.min), incremental=False)
            
            current_batch = []
            page_token = None
            processed_count = 0
            max_historical = 2000  # Limit historical processing
            
            while processed_count < max_historical:
                try:
                    # Get files from Google Drive
                    result = self._list_files(query=query, page_size=batch_size, page_token=page_token)
                    files = result['files']
                    page_token = result['next_page_token']
                    
                    if not files:
                        logger.info("No more historical files found")
                        break
                    
                    for file_info in files:
                        try:
                            # Check if file is newer than start_date
                            modified_time = datetime.fromisoformat(
                                file_info['modifiedTime'].replace('Z', '+00:00')
                            )
                            
                            if modified_time < start_date:
                                continue
                            
                            # Download file content
                            file_content = self._download_file(file_info['id'], file_info['name'])
                            
                            if file_content is not None:
                                document = self._create_document_from_file(file_info, file_content)
                                current_batch.append(document)
                                processed_count += 1
                                
                                if processed_count >= max_historical:
                                    break
                                
                                if len(current_batch) >= batch_size:
                                    yield current_batch
                                    current_batch = []
                        
                        except Exception as e:
                            logger.error(f"Failed to process historical file {file_info.get('name', 'unknown')}: {e}")
                            continue
                    
                    # Yield remaining documents
                    if current_batch:
                        yield current_batch
                        current_batch = []
                    
                    # Check if we should continue
                    if not page_token or processed_count >= max_historical:
                        break
                    
                    # Add delay to prevent rate limiting
                    import time
                    time.sleep(0.1)
                
                except Exception as e:
                    logger.error(f"Google Drive historical batch failed: {e}")
                    break
            
            logger.info(f"Google Drive historical fetch completed: {processed_count} documents")
            
        except Exception as e:
            logger.error(f"Google Drive historical fetch failed: {e}")
            raise
    
    def get_connector_info(self) -> Dict[str, Any]:
        """Get connector-specific information"""
        status = self.get_sync_status()
        
        # Add Google Drive-specific info
        try:
            service = self._get_drive_service()
            about = service.about().get(fields="user").execute()
            user = about.get("user", {})
            
            status.update({
                "drive_user": user.get('displayName'),
                "drive_email": user.get('emailAddress'),
                "target_folder_id": self.target_folder_id,
                "skip_google_docs": self.skip_google_docs,
                "credentials_file": self.credentials_file,
                "token_file": self.token_file
            })
        except Exception as e:
            logger.warning(f"Failed to get Google Drive info: {e}")
            status["drive_error"] = str(e)
        
        return status
