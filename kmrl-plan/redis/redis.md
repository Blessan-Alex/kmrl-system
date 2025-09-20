# Redis in KMRL Knowledge Hub - Complete Guide

## 🎯 **What is Redis and Why Do We Need It?**

Redis (Remote Dictionary Server) is an **in-memory data structure store** that acts as a **super-fast database, cache, and message broker** all in one. Think of it as a **lightning-fast temporary storage** that sits between your application and your main database.

### **Why Redis for KMRL?**
- **Speed**: 100x faster than PostgreSQL for temporary data
- **Reliability**: Handles thousands of concurrent operations
- **Flexibility**: Multiple data types (strings, lists, sets, hashes)
- **Scalability**: Can handle millions of operations per second

---

## 🏗️ **Redis Architecture in KMRL System**

```
┌─────────────────────────────────────────────────────────────┐
│                    KMRL System Architecture                │
├─────────────────────────────────────────────────────────────┤
│  Data Sources → Connectors → API Gateway → Processing      │
│       ↓              ↓           ↓            ↓           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                REDIS (Central Hub)                    │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │ │
│  │  │   Queues    │ │    Cache    │ │    State    │    │ │
│  │  │ (Celery)    │ │  (Fast)     │ │ (Sync Info) │    │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘    │ │
│  └─────────────────────────────────────────────────────────┘ │
│       ↓              ↓           ↓            ↓           │
│  PostgreSQL    MinIO/S3    OpenSearch    Notifications   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 **Redis Usage Patterns in KMRL**

### **1. Task Queues (Celery Message Broker)** 🚀

**What it does**: Manages background tasks like document processing, RAG pipeline, and notifications.

**Why Redis**: 
- **Reliability**: Tasks won't be lost if worker crashes
- **Scalability**: Multiple workers can process tasks in parallel
- **Monitoring**: Track task status and results

**Implementation**:
```python
# Celery Configuration
broker_url = 'redis://localhost:6379'
result_backend = 'redis://localhost:6379'

# Task Queues
task_routes = {
    'process_document': {'queue': 'document_processing'},
    'prepare_rag_pipeline': {'queue': 'rag_processing'},
    'send_notification': {'queue': 'notifications'},
}
```

**Real Example**:
```python
# When a document is uploaded
@celery_app.task
def process_document(document_id):
    # This task gets queued in Redis
    # Workers pick it up and process
    pass
```

### **2. State Management (Connector Sync)** 📊

**What it does**: Tracks what documents have been processed and when each connector last synced.

**Why Redis**:
- **Speed**: Instant lookups for duplicate prevention
- **Persistence**: Survives system restarts
- **Atomic Operations**: Thread-safe operations

**Implementation**:
```python
class BaseConnector:
    def __init__(self, source_name: str):
        self.redis_client = redis.Redis.from_url("redis://localhost:6379")
        self.state_key = f"connector_state:{source_name.lower()}"
        self.processed_key = f"processed_docs:{source_name.lower()}"
    
    def get_last_sync_time(self) -> datetime:
        """Get when we last synced this connector"""
        last_sync = self.redis_client.get(self.state_key)
        if last_sync:
            return datetime.fromisoformat(last_sync.decode())
        return datetime.min
    
    def mark_document_processed(self, document_id: str):
        """Mark document as processed to avoid duplicates"""
        self.redis_client.sadd(self.processed_key, document_id)
    
    def is_document_processed(self, document_id: str) -> bool:
        """Check if we already processed this document"""
        return self.redis_client.sismember(self.processed_key, document_id)
```

**Real Example**:
```python
# Email connector checks Redis before processing
if not self.is_document_processed(doc_id):
    # Process the document
    self.process_document(doc)
    self.mark_document_processed(doc_id)
```

### **3. Caching (Fast Data Access)** ⚡

**What it does**: Stores frequently accessed data to avoid slow database queries.

**Why Redis**:
- **Speed**: 100x faster than database queries
- **Memory Efficiency**: Stores data in RAM
- **Expiration**: Automatic cleanup of old data

**Implementation**:
```python
# Cache API responses
def get_document_status(document_id):
    cache_key = f"doc_status:{document_id}"
    
    # Try cache first
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    # If not in cache, query database
    result = database.query(f"SELECT * FROM documents WHERE id = {document_id}")
    
    # Store in cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(result))
    return result
```

**Real Example**:
```python
# Cache user permissions
def get_user_permissions(user_id):
    cache_key = f"user_perms:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query database and cache for 1 hour
    perms = database.get_user_permissions(user_id)
    redis_client.setex(cache_key, 3600, json.dumps(perms))
    return perms
```

### **4. Rate Limiting (API Protection)** 🛡️

**What it does**: Prevents users from overwhelming the system with too many requests.

**Why Redis**:
- **Atomic Operations**: Thread-safe counters
- **Expiration**: Automatic cleanup
- **Distributed**: Works across multiple servers

**Implementation**:
```python
class RateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis.from_url("redis://localhost:6379")
    
    async def check_rate_limit(self, api_key: str, limit: int = 100, window: int = 3600):
        """Check if API key has exceeded rate limit"""
        key = f"rate_limit:{api_key}"
        
        # Get current count
        current = self.redis_client.get(key)
        if current and int(current) >= limit:
            return False  # Rate limit exceeded
        
        # Increment counter
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        pipe.execute()
        
        return True
```

**Real Example**:
```python
# API Gateway rate limiting
@app.post("/api/v1/documents/upload")
async def upload_document(api_key: str = Depends(verify_api_key)):
    # Check rate limit: 100 requests per hour
    if not await rate_limiter.check_rate_limit(api_key, 100, 3600):
        raise HTTPException(429, "Rate limit exceeded")
    
    # Process upload...
```

### **5. Session Management (User Authentication)** 🔐

**What it does**: Stores user session data for fast authentication.

**Why Redis**:
- **Speed**: Instant session validation
- **Expiration**: Automatic session cleanup
- **Security**: Can store encrypted session data

**Implementation**:
```python
class SessionManager:
    def __init__(self):
        self.redis_client = redis.Redis.from_url("redis://localhost:6379")
    
    def create_session(self, user_id: str, session_data: dict):
        """Create user session"""
        session_id = str(uuid.uuid4())
        key = f"session:{session_id}"
        
        # Store session data for 24 hours
        self.redis_client.setex(key, 86400, json.dumps(session_data))
        return session_id
    
    def validate_session(self, session_id: str):
        """Validate user session"""
        key = f"session:{session_id}"
        session_data = self.redis_client.get(key)
        
        if session_data:
            return json.loads(session_data)
        return None
```

### **6. Real-time Notifications (Pub/Sub)** 📢

**What it does**: Enables real-time communication between system components.

**Why Redis**:
- **Pub/Sub**: Publish-subscribe messaging
- **Real-time**: Instant message delivery
- **Scalable**: Multiple subscribers

**Implementation**:
```python
class NotificationService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url("redis://localhost:6379")
        self.pubsub = self.redis_client.pubsub()
    
    def publish_notification(self, channel: str, message: dict):
        """Publish notification to channel"""
        self.redis_client.publish(channel, json.dumps(message))
    
    def subscribe_to_notifications(self, channel: str):
        """Subscribe to notification channel"""
        self.pubsub.subscribe(channel)
        return self.pubsub.listen()
```

**Real Example**:
```python
# When document is processed
def on_document_processed(document_id, status):
    notification = {
        "type": "document_processed",
        "document_id": document_id,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    # Publish to all subscribers
    notification_service.publish_notification("document_updates", notification)
```

---

## 🗂️ **Redis Data Structures Used in KMRL**

### **1. Strings** 📝
**Used for**: Simple key-value storage
```python
# Store last sync time
redis_client.set("connector_state:email", "2024-12-19T10:30:00")

# Store API key
redis_client.set("kmrl_api_key", "kmrl-api-key-2024")
```

### **2. Sets** 🎯
**Used for**: Tracking processed documents
```python
# Add processed document
redis_client.sadd("processed_docs:email", "doc_123")

# Check if processed
is_processed = redis_client.sismember("processed_docs:email", "doc_123")
```

### **3. Hashes** 🗃️
**Used for**: Complex data structures
```python
# Store document metadata
redis_client.hset("document:123", mapping={
    "filename": "report.pdf",
    "source": "email",
    "status": "processing",
    "department": "engineering"
})
```

### **4. Lists** 📋
**Used for**: Task queues and ordered data
```python
# Add task to queue
redis_client.lpush("task_queue:document_processing", json.dumps(task_data))

# Get next task
task = redis_client.rpop("task_queue:document_processing")
```

### **5. Sorted Sets** 🏆
**Used for**: Priority queues and rankings
```python
# Add document with priority
redis_client.zadd("priority_queue", {"doc_123": 10, "doc_456": 5})

# Get highest priority document
highest = redis_client.zpopmax("priority_queue")
```

---

## ⚙️ **Redis Configuration for KMRL**

### **Production Configuration**
```conf
# Redis Configuration for KMRL Knowledge Hub

# Network
bind 0.0.0.0
port 6379

# Memory Management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence (Data Safety)
save 900 1      # Save if 1 key changed in 900 seconds
save 300 10     # Save if 10 keys changed in 300 seconds
save 60 10000   # Save if 10000 keys changed in 60 seconds

# Security
requirepass your_secure_password

# Performance
tcp-keepalive 300
timeout 0

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Keyspace notifications (for monitoring)
notify-keyspace-events Ex
```

### **Development Configuration**
```conf
# Development Redis Configuration

# Network
bind 127.0.0.1
port 6379

# Memory (smaller for development)
maxmemory 512mb
maxmemory-policy allkeys-lru

# No persistence (faster for development)
save ""

# No password (easier for development)
# requirepass ""

# Logging
loglevel debug
```

---

## 🚀 **Redis Setup and Installation**

### **1. Install Redis**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server

# macOS
brew install redis

# Windows (WSL)
wsl --install Ubuntu
# Then follow Ubuntu instructions
```

### **2. Start Redis**
```bash
# Start Redis server
sudo systemctl start redis-server  # Linux
brew services start redis          # macOS

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### **3. Configure Redis**
```bash
# Edit Redis configuration
sudo nano /etc/redis/redis.conf

# Set password
requirepass your_secure_password

# Set memory limit
maxmemory 2gb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server
```

### **4. Test Redis Connection**
```bash
# Connect to Redis
redis-cli

# Test basic operations
SET test_key "Hello Redis"
GET test_key
# Should return: "Hello Redis"

# Test with password
AUTH your_secure_password
```

---

## 🔍 **Redis Monitoring and Health Checks**

### **1. Basic Health Check**
```bash
# Check Redis status
redis-cli ping

# Check Redis info
redis-cli info

# Check memory usage
redis-cli info memory

# Check connected clients
redis-cli info clients
```

### **2. Monitor Redis Operations**
```bash
# Monitor all Redis commands in real-time
redis-cli monitor

# Check slow queries
redis-cli slowlog get 10

# Check key statistics
redis-cli info keyspace
```

### **3. Redis Health Check Script**
```bash
#!/bin/bash
# redis-health-check.sh

echo "Checking Redis health..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running"
    exit 1
fi

# Check memory usage
memory_usage=$(redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
echo "✅ Memory usage: $memory_usage"

# Check connected clients
clients=$(redis-cli info clients | grep connected_clients | cut -d: -f2 | tr -d '\r')
echo "✅ Connected clients: $clients"

# Check uptime
uptime=$(redis-cli info server | grep uptime_in_seconds | cut -d: -f2 | tr -d '\r')
echo "✅ Uptime: $uptime seconds"

echo "✅ Redis is healthy!"
```

---

## 🛠️ **Redis Troubleshooting**

### **Common Issues and Solutions**

#### **1. Redis Not Starting**
```bash
# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log

# Check if port is in use
sudo netstat -tlnp | grep :6379

# Kill process using port
sudo kill -9 $(sudo lsof -t -i:6379)
```

#### **2. Memory Issues**
```bash
# Check memory usage
redis-cli info memory

# Clear all keys (DANGER: This deletes all data!)
redis-cli FLUSHALL

# Clear specific keys
redis-cli DEL key_name
```

#### **3. Connection Issues**
```bash
# Test connection
redis-cli ping

# Check Redis configuration
redis-cli config get "*"

# Restart Redis
sudo systemctl restart redis-server
```

#### **4. Performance Issues**
```bash
# Check slow queries
redis-cli slowlog get 10

# Monitor operations
redis-cli monitor

# Check memory fragmentation
redis-cli info memory | grep mem_fragmentation_ratio
```

---

## 📊 **Redis Performance Optimization**

### **1. Memory Optimization**
```conf
# Set appropriate memory limit
maxmemory 2gb

# Use LRU eviction policy
maxmemory-policy allkeys-lru

# Enable memory optimization
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
```

### **2. Persistence Optimization**
```conf
# For production (data safety)
save 900 1
save 300 10
save 60 10000

# For development (speed)
save ""
```

### **3. Network Optimization**
```conf
# Enable TCP keepalive
tcp-keepalive 300

# Set timeout
timeout 0

# Enable compression
tcp-compression yes
```

---

## 🔒 **Redis Security Best Practices**

### **1. Authentication**
```conf
# Set strong password
requirepass your_very_secure_password_here

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

### **2. Network Security**
```conf
# Bind to specific interface
bind 127.0.0.1

# Use firewall
sudo ufw allow from 192.168.1.0/24 to any port 6379
```

### **3. Data Encryption**
```python
# Encrypt sensitive data before storing
import json
from cryptography.fernet import Fernet

def encrypt_data(data):
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt(json.dumps(data).encode())
    return encrypted, key
```

---

## 🎯 **Redis in KMRL: Real-World Examples**

### **Example 1: Document Processing Queue**
```python
# When document is uploaded
document_task = {
    "document_id": "doc_123",
    "filename": "report.pdf",
    "source": "email",
    "priority": "high"
}

# Add to processing queue
redis_client.lpush("document_processing_queue", json.dumps(document_task))

# Worker picks up task
task = redis_client.rpop("document_processing_queue")
if task:
    process_document(json.loads(task))
```

### **Example 2: Connector State Management**
```python
# Email connector sync
def sync_email_documents():
    # Get last sync time
    last_sync = redis_client.get("connector_state:email")
    if last_sync:
        last_sync_time = datetime.fromisoformat(last_sync.decode())
    else:
        last_sync_time = datetime.min
    
    # Fetch new emails since last sync
    new_emails = fetch_emails_since(last_sync_time)
    
    for email in new_emails:
        doc_id = f"email_{email['id']}"
        
        # Check if already processed
        if not redis_client.sismember("processed_docs:email", doc_id):
            # Process document
            process_document(email)
            # Mark as processed
            redis_client.sadd("processed_docs:email", doc_id)
    
    # Update last sync time
    redis_client.set("connector_state:email", datetime.now().isoformat())
```

### **Example 3: Rate Limiting API**
```python
# API Gateway rate limiting
def check_rate_limit(api_key, limit=100, window=3600):
    key = f"rate_limit:{api_key}"
    
    # Get current count
    current = redis_client.get(key)
    if current and int(current) >= limit:
        return False  # Rate limit exceeded
    
    # Increment counter with expiration
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    pipe.execute()
    
    return True
```

---

## 🎉 **Summary: Why Redis is Perfect for KMRL**

### **🚀 Speed**
- **100x faster** than database queries
- **Sub-millisecond** response times
- **Handles thousands** of concurrent operations

### **🔄 Reliability**
- **Persistent data** survives restarts
- **Atomic operations** prevent data corruption
- **Built-in replication** for high availability

### **📈 Scalability**
- **Horizontal scaling** with Redis Cluster
- **Load balancing** across multiple Redis instances
- **Handles millions** of operations per second

### **🛠️ Flexibility**
- **Multiple data types** for different use cases
- **Pub/Sub messaging** for real-time features
- **Lua scripting** for complex operations

### **🔧 Easy Integration**
- **Simple API** for all programming languages
- **Celery integration** for task queues
- **Django integration** for caching

---

## 🎯 **Next Steps**

1. **Install Redis** on your development machine
2. **Configure Redis** with appropriate settings
3. **Test Redis** with basic operations
4. **Integrate Redis** with your KMRL application
5. **Monitor Redis** performance and health

Redis is the **backbone** of the KMRL system, providing the speed, reliability, and scalability needed to handle thousands of documents efficiently! 🚀
