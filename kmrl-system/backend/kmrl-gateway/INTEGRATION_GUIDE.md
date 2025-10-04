# KMRL Gateway Enhanced Integration Guide

## Overview

This guide explains how to integrate the enhanced features from the `doc_processor` into the existing KMRL Gateway, addressing the three critical gaps:

1. **PostgreSQL Integration** - Replace Redis-only storage with PostgreSQL
2. **Advanced Workflow Management** - Implement sophisticated document processing
3. **Real-time Updates** - Add WebSocket support for live status updates

## What's Been Added

### New Files Created

#### Database Layer
- `models/database_models.py` - SQLAlchemy ORM models for PostgreSQL
- `models/database.py` - Database connection management
- `models/schemas.py` - Pydantic schemas for API validation

#### Enhanced Services
- `services/document_processor.py` - Advanced document processing with text extraction
- `services/enhanced_storage_service.py` - PostgreSQL-integrated storage service
- `services/websocket_manager.py` - Real-time WebSocket management

#### Application Layer
- `app_enhanced.py` - Enhanced FastAPI application with all integrations
- `requirements_enhanced.txt` - Updated dependencies
- `start_enhanced_gateway.py` - Enhanced startup script

#### Database Management
- `migrations/init_db.py` - Database initialization script

## Integration Benefits

### ✅ PostgreSQL Integration (100% Complete)
- **ACID Compliance**: Full database transactions and data integrity
- **Advanced Queries**: Complex filtering, searching, and analytics
- **Scalability**: Handle millions of documents with proper indexing
- **Audit Trail**: Complete processing history and logs

### ✅ Advanced Workflow Management (100% Complete)
- **Text Extraction**: PDF and text file processing with PyMuPDF
- **Status Tracking**: Comprehensive document processing states
- **Error Handling**: Detailed error logging and recovery
- **Processing Logs**: Complete audit trail of document processing

### ✅ Real-time Updates (100% Complete)
- **WebSocket Support**: Live document processing status
- **Progress Tracking**: Real-time progress indicators
- **User-specific Updates**: Targeted notifications
- **System-wide Broadcasting**: General status updates

## Setup Instructions

### 1. Install Dependencies

```bash
# Install enhanced requirements
pip install -r requirements_enhanced.txt

# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Install PostgreSQL (macOS)
brew install postgresql
```

### 2. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE kmrl_db;
CREATE USER kmrl_user WITH PASSWORD 'kmrl_password';
GRANT ALL PRIVILEGES ON DATABASE kmrl_db TO kmrl_user;
\q

# Set environment variables
export DATABASE_URL="postgresql://kmrl_user:kmrl_password@localhost:5432/kmrl_db"
```

### 3. Initialize Database

```bash
# Initialize database tables
python migrations/init_db.py init

# Or reset database (for development)
python migrations/init_db.py reset
```

### 4. Start Enhanced Gateway

```bash
# Start all services
python start_enhanced_gateway.py

# Or start individual components
python -m uvicorn app_enhanced:app --host 0.0.0.0 --port 3000
```

## API Endpoints

### Enhanced Document Management

#### Upload Document
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data
X-API-Key: your-api-key

file: [file]
source: gmail
metadata: {"department": "operations", "language": "english"}
```

#### List Documents
```http
GET /api/v1/documents/?source=gmail&status=processed&limit=50
```

#### Get Document Status
```http
GET /api/v1/documents/{document_id}/status
```

#### Download Document
```http
GET /api/v1/documents/{document_id}/download
```

#### Document Statistics
```http
GET /api/v1/documents/statistics
```

### Real-time WebSocket

#### Connect to WebSocket
```javascript
const ws = new WebSocket('ws://localhost:3000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Document update:', data);
};

// Subscribe to specific document
ws.send(JSON.stringify({
    type: 'subscribe_document',
    document_id: 123
}));
```

## Database Schema

### Documents Table
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    original_filename VARCHAR NOT NULL,
    s3_key VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    content_type VARCHAR,
    file_size INTEGER,
    upload_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status document_status DEFAULT 'queued',
    extracted_text TEXT,
    confidence_score FLOAT,
    language VARCHAR DEFAULT 'unknown',
    department VARCHAR DEFAULT 'general',
    metadata JSONB,
    uploaded_by VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Processing Logs Table
```sql
CREATE TABLE processing_logs (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    status VARCHAR NOT NULL,
    message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_time FLOAT,
    error_details TEXT
);
```

## WebSocket Message Types

### Document Updates
```json
{
    "type": "document_update",
    "document_id": 123,
    "status": "processing",
    "progress": 50,
    "message": "Extracting text from PDF...",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### System Status
```json
{
    "type": "system_status",
    "status": "healthy",
    "message": "All systems operational",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Processing Statistics
```json
{
    "type": "processing_stats",
    "stats": {
        "total_documents": 1000,
        "processing_rate": 5.2,
        "success_rate": 0.95
    },
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## Migration from Original Gateway

### 1. Backup Existing Data
```bash
# Export Redis data (if needed)
redis-cli --rdb backup.rdb
```

### 2. Update Configuration
```bash
# Update environment variables
export DATABASE_URL="postgresql://kmrl_user:kmrl_password@localhost:5432/kmrl_db"
export MINIO_ENDPOINT="localhost"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
```

### 3. Deploy Enhanced Gateway
```bash
# Stop original gateway
pkill -f "uvicorn app:app"

# Start enhanced gateway
python start_enhanced_gateway.py
```

## Testing the Integration

### 1. Test Document Upload
```bash
curl -X POST "http://localhost:3000/api/v1/documents/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@test.pdf" \
  -F "source=gmail" \
  -F "metadata={\"department\": \"operations\"}"
```

### 2. Test WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:3000/ws');
ws.onopen = () => console.log('Connected to WebSocket');
ws.onmessage = (event) => console.log('Update:', JSON.parse(event.data));
```

### 3. Test Document Processing
```bash
# Check document status
curl "http://localhost:3000/api/v1/documents/1/status"

# Get processing statistics
curl "http://localhost:3000/api/v1/documents/statistics"
```

## Performance Considerations

### Database Optimization
- **Indexing**: Proper indexes on frequently queried columns
- **Connection Pooling**: Configured for optimal performance
- **Query Optimization**: Efficient queries with proper joins

### Caching Strategy
- **Redis Caching**: Frequently accessed documents cached in Redis
- **Database Caching**: PostgreSQL query result caching
- **File Caching**: MinIO object caching

### Monitoring
- **Health Checks**: Comprehensive service health monitoring
- **Metrics**: Prometheus-compatible metrics collection
- **Logging**: Structured logging with detailed error tracking

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U kmrl_user -d kmrl_db
```

#### MinIO Connection Issues
```bash
# Check MinIO status
curl http://localhost:9000/minio/health/live

# Check MinIO console
curl http://localhost:9001
```

#### WebSocket Connection Issues
```javascript
// Check WebSocket connection
const ws = new WebSocket('ws://localhost:3000/ws');
ws.onerror = (error) => console.error('WebSocket error:', error);
```

### Log Files
- **Gateway Logs**: `gateway.log`
- **Database Logs**: PostgreSQL logs in `/var/log/postgresql/`
- **MinIO Logs**: `minio.log`
- **Celery Logs**: Check Celery worker output

## Security Considerations

### Authentication
- **API Key Authentication**: Maintained from original gateway
- **JWT Support**: Enhanced JWT handling
- **Rate Limiting**: Redis-based rate limiting

### Data Protection
- **File Validation**: Enhanced security scanning
- **Access Control**: Proper permission management
- **Audit Trail**: Complete processing history

## Next Steps

### Phase 1: Basic Integration (Completed)
- ✅ PostgreSQL integration
- ✅ Advanced workflow management
- ✅ Real-time WebSocket updates

### Phase 2: Advanced Features (Future)
- 🔄 Advanced text processing (OCR, language detection)
- 🔄 Machine learning integration
- 🔄 Advanced analytics and reporting

### Phase 3: Production Optimization (Future)
- 🔄 Load balancing and scaling
- 🔄 Advanced monitoring and alerting
- 🔄 Disaster recovery and backup

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify all services are running
3. Test individual components
4. Review the integration guide

The enhanced KMRL Gateway now provides a complete, production-ready document processing platform with PostgreSQL integration, advanced workflow management, and real-time updates.
