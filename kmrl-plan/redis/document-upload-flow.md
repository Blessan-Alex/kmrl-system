# Document Upload Flow with Redis - Complete Implementation Guide

## 🎯 **What This Guide Covers**

This guide focuses on the **core document processing flow** in KMRL:
1. **Document Upload API** - Users upload documents
2. **File Validation** - Check if file is valid
3. **Redis Queue** - Store processing task
4. **Worker Picks Up** - Background processing
5. **Testing** - How to test the entire flow

---

## 🏗️ **The Complete Flow Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Upload Flow                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Uploads Document                                      │
│         ↓                                                   │
│  ┌─────────────────┐                                       │
│  │   API Gateway   │  ← FastAPI with file validation      │
│  │  (Port 3000)    │                                       │
│  └─────────────────┘                                       │
│         ↓                                                   │
│  ┌─────────────────┐                                       │
│  │   MinIO/S3      │  ← Store original file               │
│  │  (File Storage) │                                       │
│  └─────────────────┘                                       │
│         ↓                                                   │
│  ┌─────────────────┐                                       │
│  │   PostgreSQL    │  ← Store document metadata          │
│  │   (Database)    │                                       │
│  └─────────────────┘                                       │
│         ↓                                                   │
│  ┌─────────────────┐                                       │
│  │     REDIS       │  ← Queue processing task            │
│  │   (Task Queue)  │                                       │
│  └─────────────────┘                                       │
│         ↓                                                   │
│  ┌─────────────────┐                                       │
│  │   Worker        │  ← Background processing             │
│  │  (Celery)       │                                       │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 **Step 1: Document Upload API (FastAPI)**

### **Why FastAPI?**
- **Fast**: One of the fastest Python web frameworks
- **Easy**: Simple to write and understand
- **Modern**: Built-in validation and documentation
- **Async**: Handles many requests simultaneously

### **Implementation**

```python
# backend/kmrl-gateway/app.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import uuid
from datetime import datetime
from typing import Optional

# Initialize FastAPI app
app = FastAPI(
    title="KMRL Document Gateway",
    description="Unified API for document upload and processing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis connection
redis_client = redis.Redis.from_url("redis://localhost:6379")

# File validation function
def validate_file(file: UploadFile) -> dict:
    """Validate uploaded file"""
    
    # Check file size (max 200MB)
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
    
    # Check file type
    ALLOWED_EXTENSIONS = {
        '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
        '.txt', '.md', '.dwg', '.dxf', '.step', '.stp'
    }
    
    # Get file extension
    if not file.filename:
        return {"valid": False, "error": "No filename provided"}
    
    file_extension = '.' + file.filename.split('.')[-1].lower()
    
    if file_extension not in ALLOWED_EXTENSIONS:
        return {
            "valid": False, 
            "error": f"File type {file_extension} not allowed"
        }
    
    # Check file size (we'll check this after reading)
    file_content = file.file.read()
    file.file.seek(0)  # Reset file pointer
    
    if len(file_content) > MAX_FILE_SIZE:
        return {
            "valid": False,
            "error": f"File too large. Max size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        }
    
    return {"valid": True, "file_size": len(file_content)}

# Document upload endpoint
@app.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form(...),
    department: str = Form(default="general"),
    description: str = Form(default="")
):
    """
    Upload a document for processing
    
    Args:
        file: The document file to upload
        source: Source of the document (email, manual, maximo, etc.)
        department: Department classification
        description: Optional description
    """
    
    try:
        # Step 1: Validate file
        validation_result = validate_file(file)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=validation_result["error"]
            )
        
        # Step 2: Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Step 3: Store file in MinIO/S3 (simplified - in real implementation)
        file_path = f"documents/{document_id}/{file.filename}"
        
        # Step 4: Store metadata in PostgreSQL (simplified)
        document_metadata = {
            "document_id": document_id,
            "filename": file.filename,
            "source": source,
            "department": department,
            "description": description,
            "file_size": validation_result["file_size"],
            "file_path": file_path,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # Step 5: Queue processing task in Redis
        processing_task = {
            "task_id": str(uuid.uuid4()),
            "document_id": document_id,
            "filename": file.filename,
            "source": source,
            "department": department,
            "file_path": file_path,
            "file_size": validation_result["file_size"],
            "created_at": datetime.now().isoformat(),
            "priority": "normal"
        }
        
        # Add task to Redis queue
        redis_client.lpush("document_processing_queue", json.dumps(processing_task))
        
        # Step 6: Return response
        return {
            "status": "success",
            "message": "Document uploaded and queued for processing",
            "document_id": document_id,
            "task_id": processing_task["task_id"],
            "filename": file.filename,
            "file_size": validation_result["file_size"],
            "source": source,
            "department": department
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Upload failed: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is healthy"""
    try:
        # Check Redis connection
        redis_client.ping()
        return {
            "status": "healthy",
            "service": "kmrl-gateway",
            "redis": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "kmrl-gateway",
            "redis": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Get document status
@app.get("/api/v1/documents/{document_id}/status")
async def get_document_status(document_id: str):
    """Get the processing status of a document"""
    try:
        # Check if document exists in Redis
        task_key = f"document_task:{document_id}"
        task_data = redis_client.get(task_key)
        
        if not task_data:
            raise HTTPException(
                status_code=404, 
                detail="Document not found"
            )
        
        task = json.loads(task_data)
        
        return {
            "document_id": document_id,
            "status": task.get("status", "unknown"),
            "filename": task.get("filename"),
            "source": task.get("source"),
            "department": task.get("department"),
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document status: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
```

---

## 🔧 **Step 2: Redis Configuration**

### **Why Redis for Task Queues?**
- **Speed**: Instant task queuing and retrieval
- **Reliability**: Tasks persist even if workers restart
- **Scalability**: Multiple workers can process tasks
- **Monitoring**: Track task status and results

### **Redis Setup**

```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis-server

# Test Redis
redis-cli ping
# Should return: PONG
```

### **Redis Configuration**

```conf
# /etc/redis/redis.conf
# Network
bind 127.0.0.1
port 6379

# Memory
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

---

## 👷 **Step 3: Worker Implementation (Celery)**

### **Why Celery?**
- **Background Tasks**: Process documents without blocking the API
- **Reliability**: Retry failed tasks automatically
- **Scalability**: Add more workers as needed
- **Monitoring**: Track task progress and results

### **Worker Implementation**

```python
# backend/kmrl-document-worker/worker.py
from celery import Celery
import redis
import json
import time
from datetime import datetime
from typing import Dict, Any

# Initialize Celery
celery_app = Celery('kmrl-document-worker')

# Celery configuration
celery_app.conf.update(
    broker_url='redis://localhost:6379',
    result_backend='redis://localhost:6379',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)

# Initialize Redis
redis_client = redis.Redis.from_url("redis://localhost:6379")

@celery_app.task(bind=True, name='process_document')
def process_document(self, task_data: Dict[str, Any]):
    """
    Process a document from the queue
    
    Args:
        task_data: Document processing task data
    """
    
    document_id = task_data.get('document_id')
    filename = task_data.get('filename')
    source = task_data.get('source')
    department = task_data.get('department')
    
    try:
        # Update task status to 'processing'
        self.update_state(
            state='PROCESSING',
            meta={
                'document_id': document_id,
                'filename': filename,
                'status': 'processing',
                'started_at': datetime.now().isoformat()
            }
        )
        
        # Store task in Redis for status tracking
        task_key = f"document_task:{document_id}"
        task_info = {
            "document_id": document_id,
            "filename": filename,
            "source": source,
            "department": department,
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "worker_id": self.request.id
        }
        redis_client.setex(task_key, 3600, json.dumps(task_info))  # Expire in 1 hour
        
        # Simulate document processing
        print(f"Processing document: {filename} (ID: {document_id})")
        
        # Step 1: File type detection
        file_extension = '.' + filename.split('.')[-1].lower()
        print(f"File type detected: {file_extension}")
        
        # Step 2: Quality assessment
        quality_score = assess_document_quality(filename, file_extension)
        print(f"Quality score: {quality_score}")
        
        # Step 3: Route to appropriate processor
        if file_extension in ['.pdf', '.docx', '.doc', '.txt']:
            result = process_text_document(filename, document_id)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff']:
            result = process_image_document(filename, document_id)
        elif file_extension in ['.dwg', '.dxf', '.step', '.stp']:
            result = process_cad_document(filename, document_id)
        else:
            result = process_unknown_document(filename, document_id)
        
        # Step 4: Update task status to 'completed'
        task_info.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "result": result,
            "quality_score": quality_score
        })
        redis_client.setex(task_key, 3600, json.dumps(task_info))
        
        # Update Celery task state
        self.update_state(
            state='SUCCESS',
            meta={
                'document_id': document_id,
                'filename': filename,
                'status': 'completed',
                'result': result,
                'completed_at': datetime.now().isoformat()
            }
        )
        
        print(f"Document processed successfully: {filename}")
        return {
            'status': 'success',
            'document_id': document_id,
            'filename': filename,
            'result': result,
            'quality_score': quality_score
        }
        
    except Exception as e:
        # Update task status to 'failed'
        error_info = {
            "document_id": document_id,
            "filename": filename,
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }
        redis_client.setex(task_key, 3600, json.dumps(error_info))
        
        self.update_state(
            state='FAILURE',
            meta={
                'document_id': document_id,
                'filename': filename,
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.now().isoformat()
            }
        )
        
        print(f"Document processing failed: {filename} - {str(e)}")
        raise

def assess_document_quality(filename: str, file_extension: str) -> float:
    """Assess document quality (simplified)"""
    # Simulate quality assessment
    import random
    return round(random.uniform(0.6, 0.95), 2)

def process_text_document(filename: str, document_id: str) -> Dict[str, Any]:
    """Process text-based documents"""
    print(f"Processing text document: {filename}")
    
    # Simulate text processing
    time.sleep(2)  # Simulate processing time
    
    return {
        "type": "text",
        "pages": 5,
        "word_count": 1250,
        "language": "english",
        "processing_method": "markitdown"
    }

def process_image_document(filename: str, document_id: str) -> Dict[str, Any]:
    """Process image documents with OCR"""
    print(f"Processing image document: {filename}")
    
    # Simulate OCR processing
    time.sleep(3)  # Simulate OCR time
    
    return {
        "type": "image",
        "ocr_confidence": 0.87,
        "text_extracted": True,
        "language": "malayalam",
        "processing_method": "tesseract_ocr"
    }

def process_cad_document(filename: str, document_id: str) -> Dict[str, Any]:
    """Process CAD documents"""
    print(f"Processing CAD document: {filename}")
    
    # Simulate CAD processing
    time.sleep(4)  # Simulate CAD processing time
    
    return {
        "type": "cad",
        "format": "dwg",
        "metadata_extracted": True,
        "processing_method": "cad_parser"
    }

def process_unknown_document(filename: str, document_id: str) -> Dict[str, Any]:
    """Process unknown document types"""
    print(f"Processing unknown document: {filename}")
    
    # Simulate unknown processing
    time.sleep(1)
    
    return {
        "type": "unknown",
        "processing_method": "generic",
        "status": "flagged_for_review"
    }

# Worker startup
if __name__ == '__main__':
    celery_app.start()
```

---

## 🧪 **Step 4: Testing the Complete Flow**

### **Test Script**

```python
# test_document_flow.py
import requests
import json
import time
import redis
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:3000"
REDIS_URL = "redis://localhost:6379"

# Initialize Redis
redis_client = redis.Redis.from_url(REDIS_URL)

def test_document_upload():
    """Test the complete document upload flow"""
    
    print("🧪 Testing KMRL Document Upload Flow")
    print("=" * 50)
    
    # Step 1: Test API health
    print("\n1️⃣ Testing API Health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
            print(f"   Response: {response.json()}")
        else:
            print("❌ API health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Step 2: Test document upload
    print("\n2️⃣ Testing Document Upload...")
    
    # Create a test file
    test_content = "This is a test document for KMRL system."
    test_filename = "test_document.txt"
    
    # Prepare upload data
    files = {
        'file': (test_filename, test_content, 'text/plain')
    }
    data = {
        'source': 'manual',
        'department': 'engineering',
        'description': 'Test document for KMRL system'
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/documents/upload",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Document uploaded successfully")
            print(f"   Document ID: {result['document_id']}")
            print(f"   Task ID: {result['task_id']}")
            print(f"   Filename: {result['filename']}")
            print(f"   File Size: {result['file_size']} bytes")
            
            document_id = result['document_id']
            task_id = result['task_id']
            
            # Step 3: Check Redis queue
            print("\n3️⃣ Checking Redis Queue...")
            queue_length = redis_client.llen("document_processing_queue")
            print(f"   Queue length: {queue_length}")
            
            if queue_length > 0:
                print("✅ Task found in queue")
                
                # Get task from queue
                task_data = redis_client.rpop("document_processing_queue")
                if task_data:
                    task = json.loads(task_data)
                    print(f"   Task: {task['filename']} - {task['source']}")
                    
                    # Put task back in queue for worker
                    redis_client.lpush("document_processing_queue", task_data)
                    print("✅ Task returned to queue for worker")
            
            # Step 4: Check document status
            print("\n4️⃣ Checking Document Status...")
            time.sleep(2)  # Wait a bit
            
            try:
                status_response = requests.get(
                    f"{API_BASE_URL}/api/v1/documents/{document_id}/status"
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    print("✅ Document status retrieved")
                    print(f"   Status: {status['status']}")
                    print(f"   Filename: {status['filename']}")
                    print(f"   Source: {status['source']}")
                    print(f"   Department: {status['department']}")
                else:
                    print("❌ Failed to get document status")
                    
            except Exception as e:
                print(f"❌ Error checking status: {e}")
            
            # Step 5: Monitor Redis for task updates
            print("\n5️⃣ Monitoring Task Updates...")
            print("   (This would normally be handled by the worker)")
            
            # Check if task exists in Redis
            task_key = f"document_task:{document_id}"
            task_info = redis_client.get(task_key)
            
            if task_info:
                task = json.loads(task_info)
                print(f"   Task found in Redis: {task['status']}")
            else:
                print("   Task not yet processed by worker")
            
        else:
            print("❌ Document upload failed")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")

def test_redis_connection():
    """Test Redis connection and basic operations"""
    
    print("\n🔧 Testing Redis Connection...")
    
    try:
        # Test basic connection
        redis_client.ping()
        print("✅ Redis connection successful")
        
        # Test basic operations
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        print(f"✅ Redis operations working: {value.decode()}")
        
        # Clean up
        redis_client.delete("test_key")
        print("✅ Redis cleanup successful")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

def test_worker_simulation():
    """Simulate worker processing"""
    
    print("\n👷 Simulating Worker Processing...")
    
    try:
        # Check queue
        queue_length = redis_client.llen("document_processing_queue")
        print(f"   Queue length: {queue_length}")
        
        if queue_length > 0:
            # Get task from queue
            task_data = redis_client.rpop("document_processing_queue")
            if task_data:
                task = json.loads(task_data)
                print(f"   Processing task: {task['filename']}")
                
                # Simulate processing
                time.sleep(2)
                
                # Update task status
                task_key = f"document_task:{task['document_id']}"
                task_info = {
                    "document_id": task['document_id'],
                    "filename": task['filename'],
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                    "result": {"type": "text", "pages": 1, "word_count": 50}
                }
                redis_client.setex(task_key, 3600, json.dumps(task_info))
                
                print("✅ Task processed successfully")
                print(f"   Result: {task_info['result']}")
            else:
                print("   No tasks in queue")
        else:
            print("   No tasks in queue")
            
    except Exception as e:
        print(f"❌ Worker simulation failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting KMRL Document Flow Tests")
    print("=" * 50)
    
    # Test Redis connection first
    test_redis_connection()
    
    # Test document upload flow
    test_document_upload()
    
    # Simulate worker processing
    test_worker_simulation()
    
    print("\n🎉 Testing Complete!")
    print("=" * 50)
```

### **Run the Tests**

```bash
# Start Redis
sudo systemctl start redis-server

# Start API Gateway
cd backend/kmrl-gateway
python app.py &

# Start Worker (in another terminal)
cd backend/kmrl-document-worker
celery -A worker worker --loglevel=info &

# Run tests
python test_document_flow.py
```

---

## 🎯 **Why This Architecture Works**

### **1. Separation of Concerns** 🏗️
- **API Gateway**: Handles user requests and validation
- **Redis**: Manages task queuing and state
- **Worker**: Processes documents in background
- **Database**: Stores persistent data

### **2. Scalability** 📈
- **Multiple Workers**: Add more workers to process more documents
- **Load Balancing**: Redis distributes tasks across workers
- **Horizontal Scaling**: Add more servers as needed

### **3. Reliability** 🔒
- **Task Persistence**: Tasks survive worker restarts
- **Error Handling**: Failed tasks can be retried
- **Monitoring**: Track task status and progress

### **4. Performance** ⚡
- **Async Processing**: API responds immediately
- **Background Processing**: Heavy tasks don't block API
- **Redis Speed**: Sub-millisecond task queuing

---

## 🚀 **Next Steps**

1. **Install Dependencies**:
   ```bash
   pip install fastapi uvicorn redis celery
   ```

2. **Start Services**:
   ```bash
   # Start Redis
   sudo systemctl start redis-server
   
   # Start API Gateway
   python app.py
   
   # Start Worker
   celery -A worker worker --loglevel=info
   ```

3. **Test the Flow**:
   ```bash
   python test_document_flow.py
   ```

4. **Monitor Progress**:
   ```bash
   # Check Redis queue
   redis-cli llen document_processing_queue
   
   # Check task status
   redis-cli get "document_task:your-document-id"
   ```

This architecture provides a **robust, scalable, and reliable** document processing system that can handle thousands of documents efficiently! 🎉
