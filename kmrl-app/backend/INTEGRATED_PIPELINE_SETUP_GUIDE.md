# Integrated KMRL Pipeline Setup Guide
**Complete Guide to Running the KMRL System with Document_Extraction Integration**

---

## 🎯 Overview

This guide will help you run the complete KMRL system with the newly integrated Document_Extraction pipeline. The system includes:
- **Gateway API** (FastAPI)
- **Document Processing** (Enhanced with Document_Extraction)
- **Connectors** (Gmail, Google Drive, etc.)
- **Workers** (Document, Notification, RAG)
- **Storage** (MinIO, PostgreSQL, Redis)

---

## ✅ Prerequisites Checklist

### 1. **System Requirements**
- [ ] Python 3.8+ installed
- [ ] PostgreSQL running (port 5432)
- [ ] Redis running (port 6379)
- [ ] Tesseract OCR installed
- [ ] System dependencies (see below)

### 2. **Database Setup**
- [ ] PostgreSQL database created
- [ ] Database migration applied
- [ ] Connection credentials configured

### 3. **Dependencies Installed**
- [ ] Python packages installed
- [ ] Document_Extraction requirements installed
- [ ] System dependencies installed

---

## 🚀 Step-by-Step Setup

### **Step 1: Install System Dependencies**

#### Ubuntu/Debian:
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib redis-server tesseract-ocr tesseract-ocr-mal

# Install Python dependencies
sudo apt-get install -y python3-pip python3-venv python3-dev
sudo apt-get install -y libpq-dev libmagic1 libmagic-dev
sudo apt-get install -y libtesseract-dev libleptonica-dev
```

#### Windows:
```bash
# Install Tesseract OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR\

# Install Python dependencies
pip install --break-system-packages -r requirements.txt
```

### **Step 2: Database Setup**

```bash
# 1. Create PostgreSQL database
sudo -u postgres createdb kmrl_database

# 2. Create user (optional)
sudo -u postgres createuser kmrl_user
sudo -u postgres psql -c "ALTER USER kmrl_user PASSWORD 'kmrl_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kmrl_database TO kmrl_user;"

# 3. Apply database migration
psql -d kmrl_database -f migrations/add_document_extraction_fields.sql
```

### **Step 3: Environment Configuration**

Create `.env` file in `kmrl-app/backend/`:
```bash
# Database Configuration
DATABASE_URL=postgresql://kmrl_user:kmrl_password@localhost:5432/kmrl_database

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=kmrl-documents

# Document_Extraction Configuration
DOCUMENT_EXTRACTION_ENABLED=True
TESSERACT_CMD=/usr/bin/tesseract
TESSERACT_LANGUAGES=mal+eng
MAX_FILE_SIZE_MB=50
IMAGE_QUALITY_THRESHOLD=0.7
TEXT_DENSITY_THRESHOLD=0.1

# Processing Configuration
ENHANCED_PROCESSING_ENABLED=True
QUALITY_THRESHOLD_PROCESS=0.7
QUALITY_THRESHOLD_ENHANCE=0.4
QUALITY_THRESHOLD_REJECT=0.2

# Logging
LOG_LEVEL=INFO
ENABLE_DETAILED_LOGGING=True
```

### **Step 4: Install Python Dependencies**

```bash
cd kmrl-app/backend

# Install main requirements
pip install --break-system-packages -r requirements.txt

# Install Document_Extraction specific requirements
pip install --break-system-packages -r services/document_extraction/requirements.txt

# Install additional dependencies
pip install --break-system-packages loguru opencv-python pytesseract
```

### **Step 5: Verify Installation**

```bash
# Test Document_Extraction import
python3 -c "
import sys
sys.path.append('services/document_extraction')
try:
    from document_processor.tasks import process_document
    print('✅ Document_Extraction import successful')
except ImportError as e:
    print(f'⚠️ Document_Extraction import failed: {e}')
"

# Test database connection
python3 -c "
from models.database import SessionLocal
try:
    db = SessionLocal()
    db.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# Test Redis connection
python3 -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
"
```

---

## 🚀 Running the Integrated System

### **Method 1: Using start_kmrl_system.py (Recommended)**

```bash
cd kmrl-app/backend

# Set environment variables
export DOCUMENT_EXTRACTION_ENABLED=True
export TESSERACT_CMD=/usr/bin/tesseract
export TESSERACT_LANGUAGES=mal+eng

# Run the complete system
python3 start_kmrl_system.py
```

**What this does:**
- ✅ Starts PostgreSQL, Redis, MinIO
- ✅ Starts Gateway API (FastAPI)
- ✅ Starts Gateway Worker (with Document_Extraction)
- ✅ Starts Connector Workers
- ✅ Starts Document, Notification, RAG Workers
- ✅ Performs health checks
- ✅ Provides monitoring

### **Method 2: Manual Startup (For Development)**

```bash
# Terminal 1: Start Infrastructure
redis-server &
sudo systemctl start postgresql
./minio server ./minio-data --console-address :9001 &

# Terminal 2: Start Gateway
cd kmrl-app/backend
python3 -m uvicorn gateway.app:app --host 0.0.0.0 --port 3000 &

# Terminal 3: Start Gateway Worker
cd kmrl-app/backend
celery -A services.processing.document_processor worker --loglevel=info --queues=kmrl:documents &

# Terminal 4: Start Connector Worker
cd kmrl-app/backend
celery -A connectors.tasks.sync_tasks worker --loglevel=info --queues=kmrl:connectors &

# Terminal 5: Start Document Worker
cd kmrl-app/backend
celery -A workers.document_worker.worker worker --loglevel=info --queues=kmrl:documents &
```

---

## 🔍 Verification & Testing

### **1. System Health Check**

```bash
# Check Gateway API
curl http://localhost:3000/health

# Check MinIO
curl http://localhost:9001

# Check Redis
redis-cli ping

# Check PostgreSQL
pg_isready -h localhost -p 5432
```

### **2. Test Document Processing**

```bash
# Upload a test document via API
curl -X POST "http://localhost:3000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test-docs/maintenance_checklist_weekly_inspection.pdf" \
  -F "source=gmail"

# Check processing status
curl http://localhost:3000/api/v1/documents/1/status
```

### **3. Monitor Processing**

```bash
# Check Celery workers
celery -A services.processing.document_processor inspect active

# Check Redis queues
redis-cli llen kmrl:documents

# Check logs
tail -f logs/document_processor.log
```

---

## 🛠️ Troubleshooting

### **Common Issues & Solutions**

#### **1. Document_Extraction Import Errors**
```bash
# Error: No module named 'document_extraction'
# Solution: Check path and install dependencies
export PYTHONPATH="${PYTHONPATH}:$(pwd)/services"
pip install --break-system-packages -r services/document_extraction/requirements.txt
```

#### **2. Tesseract Not Found**
```bash
# Error: TesseractNotFoundError
# Solution: Install Tesseract and set path
sudo apt-get install tesseract-ocr tesseract-ocr-mal
export TESSERACT_CMD=/usr/bin/tesseract
```

#### **3. Database Connection Issues**
```bash
# Error: Database connection failed
# Solution: Check PostgreSQL and credentials
sudo systemctl start postgresql
sudo -u postgres psql -c "CREATE DATABASE kmrl_database;"
```

#### **4. Redis Connection Issues**
```bash
# Error: Redis connection failed
# Solution: Start Redis service
sudo systemctl start redis-server
redis-cli ping
```

#### **5. MinIO Issues**
```bash
# Error: MinIO not accessible
# Solution: Check MinIO binary and permissions
chmod +x minio
./minio server ./minio-data --console-address :9001
```

---

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Connectors    │    │     Gateway     │    │     Workers     │
│                 │    │                 │    │                 │
│ • Gmail         │───▶│ • FastAPI       │───▶│ • Document      │
│ • Google Drive  │    │ • Upload API    │    │ • Notification  │
│ • SharePoint    │    │ • Health Check  │    │ • RAG          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Storage       │    │   Processing    │    │   Document_     │
│                 │    │                 │    │   Extraction    │
│ • PostgreSQL    │    │ • Celery Queue  │    │                 │
│ • Redis         │    │ • Task Routing  │    │ • OCR           │
│ • MinIO         │    │ • Error Handling│    │ • Quality Check │
└─────────────────┘    └─────────────────┘    │ • Language Det. │
                                               │ • File Type Det.│
                                               └─────────────────┘
```

---

## 🎯 Expected Behavior

### **When You Run `start_kmrl_system.py`:**

1. **Infrastructure Services** (5-10 seconds)
   - ✅ PostgreSQL check
   - ✅ Redis check  
   - ✅ MinIO startup

2. **Gateway Services** (10-15 seconds)
   - ✅ FastAPI server on port 3000
   - ✅ Gateway Celery worker
   - ✅ Document_Extraction integration

3. **Connector Services** (5-10 seconds)
   - ✅ Connector Celery worker
   - ✅ Connector Celery beat

4. **Worker Services** (5-10 seconds)
   - ✅ Document worker
   - ✅ Notification worker
   - ✅ RAG worker

5. **Health Check** (5 seconds)
   - ✅ All services verified
   - ✅ System ready

### **Access Points:**
- **Gateway API:** http://localhost:3000
- **API Documentation:** http://localhost:3000/docs
- **Health Check:** http://localhost:3000/health
- **MinIO Console:** http://localhost:9001

---

## 🚨 Important Notes

### **Document_Extraction Integration:**
- ✅ **Enhanced Processing:** Documents will be processed with Document_Extraction
- ✅ **Fallback Mechanism:** If Document_Extraction fails, basic processing continues
- ✅ **Quality Assessment:** Documents get quality scores and decisions
- ✅ **Language Detection:** Malayalam and English text detection
- ✅ **File Type Detection:** Automatic file type classification

### **Performance Considerations:**
- **Memory Usage:** Document_Extraction adds ~200MB RAM usage
- **Processing Time:** Enhanced processing takes 2-5x longer than basic
- **Storage:** Additional metadata stored in PostgreSQL
- **Concurrency:** Adjust worker concurrency based on system resources

---

## 🎉 Success Indicators

When everything is working correctly, you should see:

```
🎉 Unified KMRL System Started Successfully!
==================================================
📊 Services Status:
✅ PostgreSQL: Database ready
✅ Redis: Cache and queue ready  
✅ MinIO: Object storage ready
✅ Gateway: API ready
✅ Connectors: Data ingestion ready
✅ Workers: Processing ready

🌐 Access Points:
• Gateway API: http://localhost:3000
• API Docs: http://localhost:3000/docs
• Health Check: http://localhost:3000/health
• MinIO Console: http://localhost:9001
```

---

## 📝 Next Steps

1. **Test Document Upload:** Upload a test document via API
2. **Monitor Processing:** Check logs for Document_Extraction processing
3. **Verify Results:** Check database for enhanced metadata
4. **Scale Workers:** Adjust concurrency based on load
5. **Monitor Performance:** Track processing times and quality scores

---

**🎯 The integrated system is now ready for production use with enhanced document processing capabilities!**
