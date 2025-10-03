I'll improve the plan.md by focusing on the core implementation without Docker for now, ensuring it follows the problem statement and detailed flow. Let me create a comprehensive implementation plan that addresses KMRL's specific needs.


[3 tools called]

Now I'll create an improved implementation plan that directly addresses KMRL's specific challenges and follows the detailed flow:

# **KMRL Knowledge Hub Implementation Plan**
## **Solving KMRL's Document Management Crisis**

### **Problem Context**
KMRL faces a **silent productivity tax** from thousands of daily documents across multiple channels (email, Maximo, SharePoint, WhatsApp) in English, Malayalam, and bilingual formats. The system must provide **rapid, trustworthy snapshots** while preserving traceability to original sources.

---

## **Phase 1: Core Infrastructure Setup (Week 1-2)**

### **1.1 Project Structure**
```
kmrl-knowledge-hub/
├── backend/
│   ├── kmrl-gateway/                 # FastAPI Gateway
│   ├── kmrl-connectors/              # Data Source Connectors  
│   ├── kmrl-webapp/                  # Django Backend
│   └── shared/                       # Common Libraries
├── frontend/
│   ├── kmrl-web/                     # React Dashboard
│   └── kmrl-mobile/                  # React Native Mobile
├── infrastructure/
│   ├── postgresql/                   # Database setup
│   ├── redis/                        # Cache & queues
│   ├── minio/                        # Object storage
│   └── opensearch/                   # Vector database
└── scripts/
    ├── setup.sh                      # Automated setup
    ├── start-dev.sh                  # Start all services
    └── stop-dev.sh                   # Stop all services
```

### **1.2 Environment Setup**
```bash
# Prerequisites Installation
sudo apt update
sudo apt install python3.9 python3-pip postgresql redis-server nginx
sudo apt install tesseract-ocr tesseract-ocr-mal  # Malayalam support
sudo apt install openjdk-11-jdk  # For OpenSearch

# Python Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **1.3 Database Setup**
```sql
-- PostgreSQL Setup
CREATE DATABASE kmrl_db;
CREATE USER kmrl_user WITH PASSWORD 'kmrl_password';
GRANT ALL PRIVILEGES ON DATABASE kmrl_db TO kmrl_user;

-- Create tables for document tracking
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,
    content_type VARCHAR(100),
    file_size BIGINT,
    storage_path TEXT,
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    confidence_score FLOAT,
    language VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## **Phase 2: Data Source Connectors (Week 3-4)**

### **2.1 Base Connector Architecture**
```python
# backend/kmrl-connectors/base/base_connector.py
from abc import ABC, abstractmethod
import redis
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()

@dataclass
class Document:
    """Unified document model for all KMRL sources"""
    source: str
    filename: str
    content: bytes
    content_type: str
    metadata: Dict[str, Any]
    document_id: Optional[str] = None
    uploaded_at: datetime = None
    language: str = "unknown"  # For Malayalam/English detection

class BaseConnector(ABC):
    """Base class for all KMRL data source connectors"""
    
    def __init__(self, source_name: str, api_endpoint: str):
        self.source_name = source_name
        self.api_endpoint = api_endpoint
        self.redis_client = redis.Redis.from_url("redis://localhost:6379")
        self.state_key = f"connector_state:{source_name.lower()}"
        self.processed_key = f"processed_docs:{source_name.lower()}"
    
    def get_last_sync_time(self) -> datetime:
        """Get last successful sync time from Redis"""
        last_sync = self.redis_client.get(self.state_key)
        if last_sync:
            return datetime.fromisoformat(last_sync.decode())
        return datetime.min
    
    def update_sync_time(self, sync_time: datetime):
        """Update last successful sync time"""
        self.redis_client.set(self.state_key, sync_time.isoformat())
    
    def mark_document_processed(self, document_id: str):
        """Mark document as processed to avoid duplicates"""
        self.redis_client.sadd(self.processed_key, document_id)
    
    def is_document_processed(self, document_id: str) -> bool:
        """Check if document was already processed"""
        return self.redis_client.sismember(self.processed_key, document_id)
    
    def upload_to_api(self, document: Document) -> Dict[str, Any]:
        """Upload document to unified KMRL API"""
        import requests
        
        files = {
            'file': (document.filename, document.content, document.content_type)
        }
        
        data = {
            'source': document.source,
            'metadata': json.dumps(document.metadata),
            'uploaded_by': 'system',
            'language': document.language
        }
        
        response = requests.post(
            f"{self.api_endpoint}/api/v1/documents/upload",
            files=files,
            data=data,
            headers={'X-API-Key': self.get_api_key()}
        )
        
        if response.status_code == 200:
            logger.info("Document uploaded successfully", 
                       source=document.source, 
                       filename=document.filename)
            return response.json()
        else:
            logger.error("Document upload failed", 
                        status=response.status_code,
                        response=response.text)
            raise Exception(f"Upload failed: {response.text}")
    
    def get_api_key(self) -> str:
        """Get API key for authentication"""
        return self.redis_client.get("kmrl_api_key").decode()
    
    @abstractmethod
    def fetch_documents(self, credentials: Dict[str, str], 
                       options: Dict[str, Any] = None) -> List[Document]:
        """Fetch documents from source system"""
        pass
    
    def sync_documents(self, credentials: Dict[str, str], 
                      options: Dict[str, Any] = None):
        """Main sync method - runs periodically"""
        try:
            logger.info(f"Starting sync for {self.source_name}")
            
            # Fetch new documents
            documents = self.fetch_documents(credentials, options)
            
            # Upload each document
            for doc in documents:
                if not self.is_document_processed(doc.document_id):
                    self.upload_to_api(doc)
                    self.mark_document_processed(doc.document_id)
            
            # Update sync time
            self.update_sync_time(datetime.now())
            
            logger.info(f"Sync completed for {self.source_name}", 
                      documents_count=len(documents))
            
        except Exception as e:
            logger.error(f"Sync failed for {self.source_name}", error=str(e))
            raise
```

### **2.2 Email Connector for KMRL Documents**
```python
# backend/kmrl-connectors/connectors/email_connector.py
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any
import structlog
from datetime import datetime
from base.base_connector import BaseConnector, Document

logger = structlog.get_logger()

class EmailConnector(BaseConnector):
    """Email connector for KMRL document ingestion"""
    
    def __init__(self, imap_host: str, imap_port: int = 993):
        super().__init__("email", "http://localhost:3000")
        self.imap_host = imap_host
        self.imap_port = imap_port
    
    def fetch_documents(self, credentials: Dict[str, str], 
                       options: Dict[str, Any] = None) -> List[Document]:
        """Fetch email attachments since last sync"""
        options = options or {}
        
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(credentials["email"], credentials["password"])
            mail.select("INBOX")
            
            # Search for emails since last sync
            last_sync = self.get_last_sync_time()
            search_criteria = f'SINCE "{last_sync.strftime("%d-%b-%Y")}"'
            
            status, messages = mail.search(None, search_criteria)
            email_ids = messages[0].split()
            
            documents = []
            for email_id in email_ids:
                # Fetch email
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract attachments
                for part in email_message.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        if filename and self.is_kmrl_document(filename):
                            # Decode filename if needed
                            if filename.startswith('=?UTF-8?'):
                                filename = decode_header(filename)[0][0].decode()
                            
                            # Check if already processed
                            doc_id = f"{email_id.decode()}_{filename}"
                            if self.is_document_processed(doc_id):
                                continue
                            
                            content = part.get_payload(decode=True)
                            
                            # Detect language from email content
                            language = self.detect_language(email_message)
                            
                            document = Document(
                                source="email",
                                filename=filename,
                                content=content,
                                content_type=part.get_content_type(),
                                metadata={
                                    "from": email_message.get("From"),
                                    "subject": email_message.get("Subject"),
                                    "date": email_message.get("Date"),
                                    "message_id": email_id.decode(),
                                    "email_id": email_id.decode(),
                                    "department": self.classify_department(email_message.get("Subject", ""))
                                },
                                document_id=doc_id,
                                uploaded_at=datetime.now(),
                                language=language
                            )
                            
                            documents.append(document)
            
            mail.close()
            mail.logout()
            
            logger.info("Email documents fetched", count=len(documents))
            return documents
            
        except Exception as e:
            logger.error("Email connector error", error=str(e))
            raise Exception(f"Email connector failed: {str(e)}")
    
    def is_kmrl_document(self, filename: str) -> bool:
        """Check if file is a KMRL document type"""
        kmrl_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.pptx', 
                          '.jpg', '.jpeg', '.png', '.tiff', '.dwg', '.dxf',
                          '.step', '.stp', '.iges', '.igs']
        return any(filename.lower().endswith(ext) for ext in kmrl_extensions)
    
    def detect_language(self, email_message) -> str:
        """Detect if email contains Malayalam content"""
        subject = email_message.get("Subject", "")
        # Simple language detection - can be enhanced with proper NLP
        if any(char in subject for char in "അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹളഴറ"):
            return "malayalam"
        return "english"
    
    def classify_department(self, subject: str) -> str:
        """Classify email by department based on subject"""
        subject_lower = subject.lower()
        if any(word in subject_lower for word in ["maintenance", "repair", "technical"]):
            return "engineering"
        elif any(word in subject_lower for word in ["finance", "invoice", "payment", "budget"]):
            return "finance"
        elif any(word in subject_lower for word in ["safety", "incident", "accident"]):
            return "safety"
        elif any(word in subject_lower for word in ["hr", "personnel", "training"]):
            return "hr"
        else:
            return "general"
```

### **2.3 Maximo Connector for Maintenance Documents**
```python
# backend/kmrl-connectors/connectors/maximo_connector.py
import requests
from typing import List, Dict, Any
import structlog
from datetime import datetime
from base.base_connector import BaseConnector, Document

logger = structlog.get_logger()

class MaximoConnector(BaseConnector):
    """Maximo connector for KMRL maintenance work orders"""
    
    def __init__(self, base_url: str):
        super().__init__("maximo", "http://localhost:3000")
        self.base_url = base_url
        self.token = None
    
    def authenticate(self, credentials: Dict[str, str]) -> str:
        """Authenticate with Maximo and get token"""
        auth_response = requests.post(
            f"{self.base_url}/maximo/oslc/login",
            json={
                "username": credentials["username"],
                "password": credentials["password"]
            }
        )
        
        if auth_response.status_code == 200:
            self.token = auth_response.json()["token"]
            return self.token
        else:
            raise Exception(f"Maximo authentication failed: {auth_response.text}")
    
    def fetch_documents(self, credentials: Dict[str, str], 
                       options: Dict[str, Any] = None) -> List[Document]:
        """Fetch work order attachments since last sync"""
        options = options or {}
        
        try:
            # Authenticate if needed
            if not self.token:
                self.authenticate(credentials)
            
            # Get work orders modified since last sync
            last_sync = self.get_last_sync_time()
            headers = {"Authorization": f"Bearer {self.token}"}
            
            params = {
                "oslc.select": "wonum,description,status,attachments,changedate,location",
                "oslc.where": f"changedate>='{last_sync.strftime('%Y-%m-%dT%H:%M:%S')}'"
            }
            
            response = requests.get(
                f"{self.base_url}/maximo/oslc/os/mxwo",
                headers=headers,
                params=params
            )
            
            work_orders = response.json()
            documents = []
            
            for work_order in work_orders.get("data", []):
                if work_order.get("attachments"):
                    for attachment in work_order["attachments"]:
                        # Check if already processed
                        doc_id = f"{work_order['wonum']}_{attachment['id']}"
                        if self.is_document_processed(doc_id):
                            continue
                        
                        # Download attachment
                        file_response = requests.get(
                            f"{self.base_url}/maximo/oslc/os/mxattachment/{attachment['id']}/content",
                            headers=headers
                        )
                        
                        document = Document(
                            source="maximo",
                            filename=attachment["filename"],
                            content=file_response.content,
                            content_type=attachment.get("contentType", "application/octet-stream"),
                            metadata={
                                "work_order_id": work_order["wonum"],
                                "description": work_order["description"],
                                "status": work_order["status"],
                                "location": work_order.get("location", ""),
                                "attachment_id": attachment["id"],
                                "change_date": work_order["changedate"],
                                "department": "engineering"  # Maximo is primarily engineering
                            },
                            document_id=doc_id,
                            uploaded_at=datetime.now(),
                            language="english"  # Maximo typically in English
                        )
                        
                        documents.append(document)
            
            logger.info("Maximo documents fetched", count=len(documents))
            return documents
            
        except Exception as e:
            logger.error("Maximo connector error", error=str(e))
            raise Exception(f"Maximo connector failed: {str(e)}")
```

### **2.4 SharePoint Connector for Corporate Documents**
```python
# backend/kmrl-connectors/connectors/sharepoint_connector.py
import requests
from typing import List, Dict, Any
import structlog
from datetime import datetime
from base.base_connector import BaseConnector, Document

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
            
            # Query SharePoint REST API
            query_url = f"{self.site_url}/_api/web/lists/getbytitle('Documents')/items"
            last_sync = self.get_last_sync_time()
            
            params = {
                "$filter": f"Modified gt datetime'{last_sync.isoformat()}'",
                "$select": "Title,Modified,FileRef,FileLeafRef,FileSystemObjectType,Author"
            }
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = requests.get(query_url, params=params, headers=headers)
            items = response.json()["value"]
            
            documents = []
            for item in items:
                if item.get("FileSystemObjectType") == 0:  # File
                    # Check if already processed
                    doc_id = f"sharepoint_{item['FileRef']}"
                    if self.is_document_processed(doc_id):
                        continue
                    
                    # Download the actual file
                    file_url = f"{self.site_url}/_api/web/GetFileByServerRelativeUrl('{item['FileRef']}')/$value"
                    file_response = requests.get(file_url, headers=headers)
                    
                    if file_response.status_code == 200:
                        document = Document(
                            source="sharepoint",
                            filename=item["FileLeafRef"],
                            content=file_response.content,
                            content_type="application/octet-stream",
                            metadata={
                                "title": item["Title"],
                                "modified": item["Modified"],
                                "file_path": item["FileRef"],
                                "author": item.get("Author", {}).get("Title", ""),
                                "library": "Documents",
                                "department": self.classify_department(item["Title"])
                            },
                            document_id=doc_id,
                            uploaded_at=datetime.now(),
                            language="english"  # SharePoint typically in English
                        )
                        
                        documents.append(document)
            
            logger.info("SharePoint documents fetched", count=len(documents))
            return documents
            
        except Exception as e:
            logger.error("SharePoint connector error", error=str(e))
            raise Exception(f"SharePoint connector failed: {str(e)}")
    
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
```

### **2.5 WhatsApp Business Connector for Field Reports**
```python
# backend/kmrl-connectors/connectors/whatsapp_connector.py
import requests
from typing import List, Dict, Any
import structlog
from datetime import datetime
from base.base_connector import BaseConnector, Document

logger = structlog.get_logger()

class WhatsAppConnector(BaseConnector):
    """WhatsApp Business API connector for KMRL field reports"""
    
    def __init__(self, phone_number_id: str):
        super().__init__("whatsapp", "http://localhost:3000")
        self.phone_number_id = phone_number_id
    
    def fetch_documents(self, credentials: Dict[str, str], 
                       options: Dict[str, Any] = None) -> List[Document]:
        """Fetch WhatsApp Business messages with documents"""
        options = options or {}
        
        try:
            headers = {"Authorization": f"Bearer {credentials['access_token']}"}
            
            # Get messages since last sync
            last_sync = self.get_last_sync_time()
            params = {
                "fields": "id,from,type,timestamp,media",
                "since": int(last_sync.timestamp())
            }
            
            response = requests.get(
                f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages",
                headers=headers,
                params=params
            )
            
            messages = response.json().get("data", [])
            documents = []
            
            for message in messages:
                if message.get("type") == "document" and message.get("media"):
                    media_id = message["media"]["id"]
                    
                    # Check if already processed
                    if self.is_document_processed(media_id):
                        continue
                    
                    # Get media URL
                    media_response = requests.get(
                        f"https://graph.facebook.com/v18.0/{media_id}",
                        headers=headers,
                        params={"fields": "url,mime_type"}
                    )
                    
                    if media_response.status_code == 200:
                        media_data = media_response.json()
                        
                        # Download file
                        file_response = requests.get(media_data["url"], headers=headers)
                        
                        if file_response.status_code == 200:
                            document = Document(
                                source="whatsapp",
                                filename=f"whatsapp_{media_id}",
                                content=file_response.content,
                                content_type=media_data.get("mime_type", "application/octet-stream"),
                                metadata={
                                    "message_id": message["id"],
                                    "from": message["from"],
                                    "timestamp": message["timestamp"],
                                    "media_id": media_id,
                                    "department": "field_operations"  # WhatsApp typically field reports
                                },
                                document_id=media_id,
                                uploaded_at=datetime.now(),
                                language="mixed"  # WhatsApp can be Malayalam/English
                            )
                            
                            documents.append(document)
            
            logger.info("WhatsApp documents fetched", count=len(documents))
            return documents
            
        except Exception as e:
            logger.error("WhatsApp connector error", error=str(e))
            raise Exception(f"WhatsApp connector failed: {str(e)}")
```

---

## **Phase 3: Celery Scheduler for Automatic Ingestion (Week 4)**

### **3.1 Connector Scheduler**
```python
# backend/kmrl-connectors/scheduler.py
from celery import Celery
from celery.schedules import crontab
import structlog
from connectors.email_connector import EmailConnector
from connectors.maximo_connector import MaximoConnector
from connectors.sharepoint_connector import SharePointConnector
from connectors.whatsapp_connector import WhatsAppConnector
from utils.credentials_manager import CredentialsManager

logger = structlog.get_logger()

# Initialize Celery
celery_app = Celery('kmrl-connectors')
celery_app.config_from_object('config.celery_config')

# Initialize credentials manager
credentials_manager = CredentialsManager()

@celery_app.task
def fetch_email_documents():
    """Automatically fetch new email attachments every 5 minutes"""
    try:
        connector = EmailConnector(
            imap_host=credentials_manager.get_email_imap_host(),
            imap_port=credentials_manager.get_email_imap_port()
        )
        
        credentials = credentials_manager.get_email_credentials()
        connector.sync_documents(credentials)
        
        logger.info("Email fetch completed")
        
    except Exception as e:
        logger.error("Email fetch failed", error=str(e))

@celery_app.task
def fetch_maximo_documents():
    """Automatically fetch new Maximo work orders every 15 minutes"""
    try:
        connector = MaximoConnector(
            base_url=credentials_manager.get_maximo_base_url()
        )
        
        credentials = credentials_manager.get_maximo_credentials()
        connector.sync_documents(credentials)
        
        logger.info("Maximo fetch completed")
        
    except Exception as e:
        logger.error("Maximo fetch failed", error=str(e))

@celery_app.task
def fetch_sharepoint_documents():
    """Automatically fetch new SharePoint documents every 30 minutes"""
    try:
        connector = SharePointConnector(
            site_url=credentials_manager.get_sharepoint_site_url()
        )
        
        credentials = credentials_manager.get_sharepoint_credentials()
        connector.sync_documents(credentials)
        
        logger.info("SharePoint fetch completed")
        
    except Exception as e:
        logger.error("SharePoint fetch failed", error=str(e))

@celery_app.task
def fetch_whatsapp_documents():
    """Automatically fetch new WhatsApp documents every 10 minutes"""
    try:
        connector = WhatsAppConnector(
            phone_number_id=credentials_manager.get_whatsapp_phone_number_id()
        )
        
        credentials = credentials_manager.get_whatsapp_credentials()
        connector.sync_documents(credentials)
        
        logger.info("WhatsApp fetch completed")
        
    except Exception as e:
        logger.error("WhatsApp fetch failed", error=str(e))

# Schedule automatic ingestion for KMRL
celery_app.conf.beat_schedule = {
    'fetch-email-every-5-minutes': {
        'task': 'scheduler.fetch_email_documents',
        'schedule': crontab(minute='*/5'),
    },
    'fetch-maximo-every-15-minutes': {
        'task': 'scheduler.fetch_maximo_documents',
        'schedule': crontab(minute='*/15'),
    },
    'fetch-sharepoint-every-30-minutes': {
        'task': 'scheduler.fetch_sharepoint_documents',
        'schedule': crontab(minute='*/30'),
    },
    'fetch-whatsapp-every-10-minutes': {
        'task': 'scheduler.fetch_whatsapp_documents',
        'schedule': crontab(minute='*/10'),
    },
}
```

---

## **Phase 4: API Gateway Implementation (Week 5-6)**

### **4.1 FastAPI Gateway for KMRL**
```python
# backend/kmrl-gateway/app.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog
from auth.jwt_handler import JWTHandler
from auth.api_key_auth import APIKeyAuth
from middleware.rate_limiter import RateLimiter
from services.file_validator import FileValidator
from services.storage_service import StorageService
from services.queue_service import QueueService
from models.document import DocumentModel
import json

logger = structlog.get_logger()

app = FastAPI(
    title="KMRL Document Gateway",
    description="Unified API for KMRL document ingestion and processing",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Initialize services
jwt_handler = JWTHandler()
api_key_auth = APIKeyAuth()
rate_limiter = RateLimiter()
file_validator = FileValidator()
storage_service = StorageService()
queue_service = QueueService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "kmrl-gateway"}

@app.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form(...),
    metadata: str = Form(...),
    api_key: str = Depends(api_key_auth.verify_api_key)
):
    """Unified document upload endpoint for KMRL"""
    try:
        # Rate limiting
        await rate_limiter.check_rate_limit(api_key)
        
        # File validation for KMRL document types
        validation_result = await file_validator.validate_kmrl_file(file)
        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata format")
        
        # Store file
        storage_result = await storage_service.store_file(file, source)
        
        # Create database record
        document = DocumentModel(
            filename=file.filename,
            source=source,
            content_type=file.content_type,
            file_size=file.size,
            storage_path=storage_result["path"],
            metadata=metadata_dict,
            status="pending"
        )
        
        # Queue processing task
        task_id = await queue_service.queue_document_processing(document)
        
        logger.info("KMRL document uploaded successfully", 
                   filename=file.filename, 
                   source=source,
                   task_id=task_id)
        
        return {
            "status": "success",
            "document_id": document.id,
            "task_id": task_id,
            "message": "Document queued for processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Document upload failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    api_key: str = Depends(api_key_auth.verify_api_key)
):
    """Get document processing status"""
    try:
        document = await DocumentModel.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "document_id": document.id,
            "status": document.status,
            "filename": document.filename,
            "source": document.source,
            "confidence_score": document.confidence_score,
            "language": document.language,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get document status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
```

### **4.2 File Validator for KMRL Documents**
```python
# backend/kmrl-gateway/services/file_validator.py
import magic
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

class FileValidator:
    """File validator for KMRL document types"""
    
    def __init__(self):
        self.max_file_size = 200 * 1024 * 1024  # 200MB
        self.allowed_extensions = [
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
            '.dwg', '.dxf', '.step', '.stp', '.iges', '.igs',
            '.txt', '.md', '.rst', '.html', '.xml', '.json', '.csv'
        ]
        self.blocked_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif']
    
    async def validate_kmrl_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate file for KMRL document processing"""
        try:
            # Check file size
            if file.size > self.max_file_size:
                return {
                    "valid": False,
                    "error": f"File size {file.size} exceeds maximum allowed size of {self.max_file_size} bytes"
                }
            
            # Check file extension
            if file.filename:
                file_ext = '.' + file.filename.split('.')[-1].lower()
                if file_ext in self.blocked_extensions:
                    return {
                        "valid": False,
                        "error": f"File type {file_ext} is not allowed for security reasons"
                    }
                
                if file_ext not in self.allowed_extensions:
                    return {
                        "valid": False,
                        "error": f"File type {file_ext} is not supported. Allowed types: {', '.join(self.allowed_extensions)}"
                    }
            
            # Read file content for MIME type validation
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Validate MIME type
            mime_type = magic.from_buffer(content, mime=True)
            if not self.is_valid_mime_type(mime_type):
                return {
                    "valid": False,
                    "error": f"MIME type {mime_type} is not supported"
                }
            
            return {"valid": True, "mime_type": mime_type}
            
        except Exception as e:
            logger.error("File validation error", error=str(e))
            return {
                "valid": False,
                "error": f"File validation failed: {str(e)}"
            }
    
    def is_valid_mime_type(self, mime_type: str) -> bool:
        """Check if MIME type is valid for KMRL documents"""
        valid_mime_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/tiff',
            'image/webp',
            'text/plain',
            'text/html',
            'text/xml',
            'application/json',
            'text/csv',
            'application/octet-stream'  # For CAD files
        ]
        return mime_type in valid_mime_types
```

---

## **Phase 5: Django Web Application (Week 7-8)**

### **5.1 Django Settings for KMRL**
```python
# backend/kmrl-webapp/kmrl_webapp/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'kmrl-secret-key-2024')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'apps.users',
    'apps.documents',
    'apps.departments',
    'apps.notifications',
    'apps.analytics',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kmrl_webapp.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'kmrl_db'),
        'USER': os.getenv('DB_USER', 'kmrl_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'kmrl_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Celery configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/kmrl_webapp.log',
        },
    },
    'loggers': {
        'kmrl_webapp': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### **5.2 Django Models for KMRL**
```python
# backend/kmrl-webapp/apps/documents/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class Document(models.Model):
    """KMRL Document model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255)
    source = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('maximo', 'Maximo'),
        ('sharepoint', 'SharePoint'),
        ('whatsapp', 'WhatsApp'),
        ('manual', 'Manual Upload')
    ])
    content_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    storage_path = models.TextField()
    metadata = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rejected', 'Rejected')
    ], default='pending')
    confidence_score = models.FloatField(null=True, blank=True)
    language = models.CharField(max_length=10, choices=[
        ('english', 'English'),
        ('malayalam', 'Malayalam'),
        ('mixed', 'Mixed'),
        ('unknown', 'Unknown')
    ], default='unknown')
    department = models.CharField(max_length=50, choices=[
        ('engineering', 'Engineering'),
        ('finance', 'Finance'),
        ('hr', 'Human Resources'),
        ('safety', 'Safety'),
        ('operations', 'Operations'),
        ('executive', 'Executive'),
        ('general', 'General')
    ], default='general')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} ({self.source})"

class DocumentChunk(models.Model):
    """Document chunks for RAG processing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_text = models.TextField()
    chunk_index = models.IntegerField()
    embedding = models.JSONField(null=True, blank=True)  # Store embedding vector
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['chunk_index']
    
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.filename}"

class Notification(models.Model):
    """Smart notifications for KMRL stakeholders"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=[
        ('urgent_maintenance', 'Urgent Maintenance'),
        ('safety_incident', 'Safety Incident'),
        ('compliance_violation', 'Compliance Violation'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('budget_exceeded', 'Budget Exceeded')
    ])
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ])
    recipients = models.ManyToManyField(User, related_name='notifications')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.priority})"
```

---

## **Phase 6: Implementation Timeline**

### **Week 1-2: Foundation Setup**
- Set up project structure
- Install and configure PostgreSQL, Redis, MinIO, OpenSearch
- Implement base connector architecture
- Set up development environment

### **Week 3-4: Connector Implementation**
- Implement Email connector with Malayalam detection
- Implement Maximo connector for maintenance documents
- Implement SharePoint connector for corporate documents
- Implement WhatsApp connector for field reports
- Test all connectors with real KMRL data

### **Week 5-6: API Gateway**
- Implement FastAPI gateway with authentication
- Add file validation for KMRL document types
- Implement storage service with MinIO
- Add rate limiting and monitoring
- Test document upload pipeline

### **Week 7-8: Django Web Application**
- Set up Django project with KMRL-specific models
- Implement user management and department classification
- Create document management APIs
- Add notification system for stakeholders
- Implement analytics dashboard

### **Week 9-10: Integration & Testing**
- Integrate all components
- Test automatic ingestion from all sources
- Add comprehensive error handling
- Performance optimization
- Documentation and deployment preparation

---

## **Key Benefits for KMRL**

1. **Solves Information Latency**: Front-line managers get instant access to relevant documents
2. **Eliminates Siloed Awareness**: Cross-department document visibility
3. **Ensures Compliance**: Automated tracking of regulatory documents
4. **Preserves Knowledge**: Institutional memory captured and searchable
5. **Reduces Duplication**: Centralized document processing eliminates redundant work

This implementation directly addresses KMRL's core challenges while providing a scalable foundation for future growth and IoT integration.