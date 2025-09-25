# KMRL Connector Queuing System Analysis

## 🔄 **How Connectors Are Queued**

### **1. Celery Task Queue System**
The KMRL system uses **Celery** with **Redis** as the message broker for queuing connector tasks:

```python
# Queue Configuration
'broker_url': 'redis://localhost:6379/0'
'result_backend': 'redis://localhost:6379/0'
'task_routes': {
    'connectors.tasks.sync_tasks.*': {'queue': 'kmrl:connectors'},
    'services.processing.document_processor.*': {'queue': 'kmrl:documents'},
    'workers.document_worker.*': {'queue': 'kmrl:documents'},
    'workers.rag_worker.*': {'queue': 'kmrl:rag'},
    'workers.notification_worker.*': {'queue': 'kmrl:notifications'},
}
```

### **2. Scheduled Task Execution**
Connectors are scheduled using **Celery Beat** with specific intervals:

```python
'beat_schedule': {
    'sync-gmail-incremental': {
        'task': 'connectors.tasks.sync_tasks.sync_gmail_incremental',
        'schedule': 120.0,  # Every 2 minutes
    },
    'sync-google-drive-incremental': {
        'task': 'connectors.tasks.sync_tasks.sync_google_drive_incremental',
        'schedule': 120.0,  # Every 2 minutes
    },
    'sync-gmail-historical': {
        'task': 'connectors.tasks.sync_tasks.sync_gmail_historical',
        'schedule': 120.0,  # Every 2 minutes
        'args': [365],  # 1 year of history
    },
    'sync-google-drive-historical': {
        'task': 'connectors.tasks.sync_tasks.sync_google_drive_historical',
        'schedule': 120.0,  # Every 2 minutes
        'args': [365],  # 1 year of history
    },
}
```

## ⚡ **Concurrent Processing**

### **1. Multiple Connectors Can Run Simultaneously**
**YES** - Gmail and Google Drive connectors can run at the same time:

#### **Worker Configuration:**
```python
# Connector workers run with concurrency=2
'--concurrency=2', '--queues=kmrl:connectors'
```

#### **Task Execution:**
- **Gmail incremental** runs every 2 minutes
- **Google Drive incremental** runs every 2 minutes  
- **Gmail historical** runs every 2 minutes
- **Google Drive historical** runs every 2 minutes
- **Health check** runs every 1 minute

### **2. Concurrent Processing Details:**

#### **Queue Separation:**
- `kmrl:connectors` → Connector sync tasks
- `kmrl:documents` → Document processing tasks
- `kmrl:rag` → RAG processing tasks
- `kmrl:notifications` → Notification tasks

#### **Worker Concurrency:**
- **Connector Workers**: `--concurrency=2` (2 parallel tasks)
- **Document Workers**: `--concurrency=1` (1 task at a time)
- **RAG Workers**: `--concurrency=1` (1 task at a time)
- **Notification Workers**: `--concurrency=1` (1 task at a time)

## 📥 **Document Download Process**

### **1. Sequential Document Processing Within Each Connector**
Each connector processes documents **one by one** within a batch:

```python
def sync_incremental(self, credentials: Dict[str, str], force: bool = False):
    for document_batch in self.fetch_documents_incremental(credentials, state):
        for document in document_batch:
            if not self.is_document_processed(document.document_id):
                try:
                    self.upload_to_api(document)  # Process one by one
                    self.mark_document_processed(document)
                    processed_in_batch += 1
                except Exception as e:
                    self.log_sync_error(str(e), {'document_id': document.document_id})
```

### **2. Batch Processing**
Documents are fetched in **batches** but processed **sequentially**:

```python
# Gmail connector batch size
batch_size = 50  # Fetch 50 emails at a time

# Google Drive connector batch size  
batch_size = 100  # Fetch 100 files at a time
```

### **3. Duplicate Prevention**
Each document is checked before processing:

```python
def is_document_processed(self, document_id: str) -> bool:
    """Check if document has already been processed"""
    return self.redis_client.exists(f"kmrl:processed:{document_id}")
```

## 🔍 **File Validation System**

### **1. File Validator Location**
File validation is handled by: `services/processing/file_validator.py`

### **2. Validation Process:**

#### **File Type Validation:**
```python
allowed_extensions = [
    '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
    '.dwg', '.dxf', '.step', '.stp', '.iges', '.igs',
    '.txt', '.md', '.rst', '.html', '.xml', '.json', '.csv'
]

blocked_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.sh', '.ps1']
```

#### **Security Scanning:**
```python
suspicious_patterns = [
    b'<script', b'javascript:', b'data:text/html', b'eval(', b'exec(',
    b'../', b'..\\', b'cmd.exe', b'powershell', b'bash'
]
```

#### **File Size Limits:**
```python
max_file_size = 200 * 1024 * 1024  # 200MB
max_image_size = 50 * 1024 * 1024  # 50MB for images
```

### **3. Validation Integration:**
File validation is integrated into the upload process:

```python
# In gateway/app.py upload endpoint
validator = FileValidator()
if not validator.validate_file(file_path):
    raise HTTPException(status_code=400, detail="File validation failed")
```

## 🏗️ **System Architecture**

### **1. Task Flow:**
```
Celery Beat Scheduler
    ↓ (schedules tasks)
Redis Queue (kmrl:connectors)
    ↓ (distributes tasks)
Connector Workers (concurrency=2)
    ↓ (processes documents)
API Gateway (upload endpoint)
    ↓ (validates files)
File Validator
    ↓ (stores files)
MinIO + PostgreSQL
```

### **2. Worker Distribution:**
```
┌─────────────────┐    ┌─────────────────┐
│ Connector Worker│    │ Connector Worker│
│ (Gmail)         │    │ (Google Drive)  │
│ concurrency=2   │    │ concurrency=2   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌─────────────────┐
         │ Redis Queue     │
         │ (kmrl:connectors)│
         └─────────────────┘
```

## ⚙️ **Configuration Details**

### **1. Task Timeouts:**
```python
'task_time_limit': 300,  # 5 minutes
'task_soft_time_limit': 240,  # 4 minutes
```

### **2. Retry Logic:**
```python
@celery_app.task(bind=True)
def sync_gmail_incremental(self):
    try:
        # ... sync logic
    except Exception as e:
        raise self.retry(exc=e, countdown=60, max_retries=3)
```

### **3. Worker Settings:**
```python
'worker_prefetch_multiplier': 1,  # Process one task at a time
'task_acks_late': True,  # Acknowledge after completion
'worker_disable_rate_limits': True,  # No rate limiting
```

## 📊 **Performance Characteristics**

### **1. Concurrent Execution:**
- ✅ **Gmail and Google Drive can run simultaneously**
- ✅ **2 connector workers** can process different connectors
- ✅ **Tasks are queued** and distributed by Redis

### **2. Sequential Processing:**
- ⚠️ **Documents within a batch are processed one by one**
- ⚠️ **No parallel document processing** within a single connector
- ⚠️ **File validation happens sequentially** for each document

### **3. Resource Management:**
- **Redis** handles task queuing and distribution
- **Celery Beat** schedules tasks at specified intervals
- **Worker processes** handle actual document processing
- **File validation** occurs before storage

## 🎯 **Summary**

### **Queue System:**
- ✅ **Celery + Redis** for task queuing
- ✅ **Separate queues** for different task types
- ✅ **Scheduled execution** every 2 minutes

### **Concurrent Processing:**
- ✅ **Multiple connectors** can run simultaneously
- ✅ **2 worker processes** for connector tasks
- ⚠️ **Documents processed sequentially** within each connector

### **File Validation:**
- ✅ **Comprehensive validation** in `services/processing/file_validator.py`
- ✅ **Security scanning** for malicious content
- ✅ **File type and size** restrictions
- ✅ **Integrated into upload process**

The system is designed for **reliable, sequential document processing** with **concurrent connector execution** but **sequential file processing** within each connector to ensure data integrity and prevent race conditions.


I'll analyze the connector queuing system, concurrent processing, and file validation mechanisms in the KMRL system. Let me examine the relevant code files.


[7 tools called]

Now let me examine the queue configuration and how tasks are scheduled:


[2 tools called]

Now let me create a comprehensive analysis of the connector queuing system:


[1 tool called]

## 🔄 **KMRL Connector Queuing System Analysis**

Based on my analysis of the code, here's how the connector queuing system works:

### **�� Queue System Architecture:**

#### **1. Celery + Redis Queue System:**
- **Message Broker**: Redis (`redis://localhost:6379/0`)
- **Task Queue**: `kmrl:connectors` for connector tasks
- **Scheduler**: Celery Beat for scheduled execution
- **Workers**: 2 connector workers with `--concurrency=2`

#### **2. Task Scheduling:**
```python
# Every 2 minutes:
- Gmail incremental sync
- Google Drive incremental sync  
- Gmail historical sync
- Google Drive historical sync

# Every 1 minute:
- Health check connectors
```

### **⚡ Concurrent Processing:**

#### **✅ YES - Multiple Connectors Run Simultaneously:**
- **Gmail and Google Drive** can run at the same time
- **2 worker processes** handle different connectors concurrently
- **Separate queues** prevent interference

#### **⚠️ Sequential Document Processing:**
- **Documents within each connector** are processed **one by one**
- **No parallel document processing** within a single connector
- **Batch fetching** (50-100 documents) but **sequential processing**

### **📥 Document Download Process:**

#### **1. Batch Fetching:**
```python
# Gmail: 50 emails per batch
# Google Drive: 100 files per batch
```

#### **2. Sequential Processing:**
```python
for document in document_batch:
    if not self.is_document_processed(document.document_id):
        self.upload_to_api(document)  # One by one
        self.mark_document_processed(document)
```

#### **3. Duplicate Prevention:**
- **Redis cache** tracks processed documents
- **Prevents re-processing** same documents
- **Document ID** based on source + filename + checksum

### **🔍 File Validation System:**

#### **Location**: `services/processing/file_validator.py`

#### **Validation Process:**
1. **File Type Check**: Allowed extensions (PDF, DOCX, images, etc.)
2. **Security Scan**: Suspicious patterns detection
3. **Size Limits**: 200MB max, 50MB for images
4. **Blocked Extensions**: .exe, .bat, .cmd, etc.

#### **Integration:**
- **Validates before storage** in MinIO
- **Rejects unsupported files** (like .ics, .pkpass)
- **Logs validation errors** to Redis for frontend display

### **��️ System Flow:**

```
Celery Beat Scheduler (every 2 min)
    ↓
Redis Queue (kmrl:connectors)
    ↓
Connector Workers (concurrency=2)
    ↓
Fetch Documents (batch of 50-100)
    ↓
Process Documents (one by one)
    ↓
File Validation (type, security, size)
    ↓
Upload to API Gateway
    ↓
Store in MinIO + PostgreSQL
```

### **⚙️ Key Configuration:**

#### **Worker Settings:**
- **Connector Workers**: `--concurrency=2` (2 parallel tasks)
- **Task Timeout**: 5 minutes max, 4 minutes soft limit
- **Retry Logic**: 3 retries with 60-second delay
- **Prefetch**: 1 task at a time per worker

#### **Queue Separation:**
- `kmrl:connectors` → Connector sync tasks
- `kmrl:documents` → Document processing
- `kmrl:rag` → RAG processing
- `kmrl:notifications` → Notifications

### **🎯 Summary:**

**✅ Concurrent Connectors**: Gmail and Google Drive can run simultaneously
**⚠️ Sequential Documents**: Documents processed one by one within each connector
**✅ Queue System**: Celery + Redis for reliable task management
**✅ File Validation**: Comprehensive validation before storage
**✅ Duplicate Prevention**: Redis-based tracking prevents re-processing

The system is designed for **reliable, sequential document processing** with **concurrent connector execution** to ensure data integrity while maximizing throughput! 🚀