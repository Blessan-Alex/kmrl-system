"""
SharePoint Connector for KMRL Corporate Documents
Handles document libraries, policies, and corporate communications
"""

import requests
from typing import List, Dict, Any
import structlog
from datetime import datetime
from ..base.base_connector import BaseConnector, Document

logger = structlog.get_logger()

class SharePointConnector(BaseConnector):
    """SharePoint connector for KMRL corporate documents"""
    
    def __init__(self, site_url: str):
        super().__init__("sharepoint", "http://localhost:3000")
        self.site_url = site_url
        self.access_token = None
    
    def authenticate(self, credentials: Dict[str, str]) -> str:
        """Get OAuth2 access token for SharePoint"""
        auth_url = f"{self.site_url}/_api/contextinfo"
        response = requests.post(auth_url, 
                               data={
                                   "client_id": credentials["client_id"],
                                   "client_secret": credentials["client_secret"]
                               })
        
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            return self.access_token
        else:
            raise Exception(f"SharePoint authentication failed: {response.text}")
    
    def fetch_documents(self, credentials: Dict[str, str], 
                       options: Dict[str, Any] = None) -> List[Document]:
        """Fetch documents modified since last sync"""
        options = options or {}
        
        try:
            # Authenticate if needed
            if not self.access_token:
                self.authenticate(credentials)
            
            # Query SharePoint REST API with enhanced parameters
            query_url = f"{self.site_url}/_api/web/lists/getbytitle('Documents')/items"
            last_sync = self.get_last_sync_time()
            
            params = {
                "$filter": f"Modified gt datetime'{last_sync.isoformat()}'",
                "$select": "Title,Modified,FileRef,FileLeafRef,FileSystemObjectType,Author,Created,File_x0020_Size,ContentType",
                "$orderby": "Modified desc",
                "$top": 1000  # Limit results
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json;odata=verbose"
            }
            
            response = requests.get(query_url, params=params, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"SharePoint API request failed: {response.status_code} - {response.text}")
            
            items = response.json().get("d", {}).get("results", [])
            documents = []
            
            for item in items:
                if item.get("FileSystemObjectType") == 0:  # File
                    # Check if already processed
                    doc_id = f"sharepoint_{item['FileRef']}"
                    if self.is_document_processed(doc_id):
                        continue
                    
                    try:
                        # Download the actual file
                        file_url = f"{self.site_url}/_api/web/GetFileByServerRelativeUrl('{item['FileRef']}')/$value"
                        file_response = requests.get(file_url, headers=headers, timeout=60)
                        
                        if file_response.status_code == 200:
                            # Get file extension for content type detection
                            filename = item["FileLeafRef"]
                            file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
                            
                            # Determine content type
                            content_type = self.get_content_type(file_extension, item.get("ContentType", ""))
                            
                            document = Document(
                                source="sharepoint",
                                filename=filename,
                                content=file_response.content,
                                content_type=content_type,
                                metadata={
                                    "title": item["Title"],
                                    "modified": item["Modified"],
                                    "created": item.get("Created", ""),
                                    "file_path": item["FileRef"],
                                    "file_size": item.get("File_x0020_Size", 0),
                                    "author": item.get("Author", {}).get("Title", ""),
                                    "library": "Documents",
                                    "content_type": item.get("ContentType", ""),
                                    "department": self.classify_department(item["Title"])
                                },
                                document_id=doc_id,
                                uploaded_at=datetime.now(),
                                language="english"  # SharePoint typically in English
                            )
                            
                            documents.append(document)
                        else:
                            logger.warning(f"Failed to download file {item['FileRef']}: {file_response.status_code}")
                            
                    except requests.exceptions.Timeout:
                        logger.warning(f"Timeout downloading file {item['FileRef']}")
                    except Exception as e:
                        logger.warning(f"Error downloading file {item['FileRef']}: {e}")
            
            logger.info("SharePoint documents fetched", count=len(documents))
            return documents
            
        except Exception as e:
            logger.error("SharePoint connector error", error=str(e))
            raise Exception(f"SharePoint connector failed: {str(e)}")
    
    def get_content_type(self, file_extension: str, sharepoint_content_type: str) -> str:
        """Determine content type based on file extension"""
        content_type_map = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ppt': 'application/vnd.ms-powerpoint',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'txt': 'text/plain',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'tiff': 'image/tiff',
            'tif': 'image/tiff'
        }
        
        if file_extension in content_type_map:
            return content_type_map[file_extension]
        elif sharepoint_content_type:
            return sharepoint_content_type
        else:
            return "application/octet-stream"
    
    def classify_department(self, title: str) -> str:
        """Classify document by department based on title"""
        title_lower = title.lower()
        if any(word in title_lower for word in ["board", "meeting", "minutes", "policy"]):
            return "executive"
        elif any(word in title_lower for word in ["hr", "personnel", "training", "recruitment"]):
            return "hr"
        elif any(word in title_lower for word in ["finance", "budget", "invoice", "payment"]):
            return "finance"
        elif any(word in title_lower for word in ["safety", "compliance", "regulatory"]):
            return "safety"
        else:
            return "general"
