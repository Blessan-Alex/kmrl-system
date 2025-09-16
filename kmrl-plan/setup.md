# KMRL System Setup Guide (Non-Docker)

## Overview
This guide provides alternative setup methods for the KMRL Knowledge Hub system without using Docker containers. Perfect for development, testing, or environments where Docker is not available.

## Setup Options

### **Option 1: Local Development Setup (Recommended for Hackathon)**

#### **Prerequisites**
- Python 3.9+ 
- Node.js 18+ (for frontend)
- PostgreSQL 13+
- Redis 6+
- MinIO or AWS S3 access
- **OpenSearch 2.x** (for vector storage and search)
- **Tesseract OCR** (for image processing)
- **Celery** (for task queue management)
- **Markitdown** (for document processing)
- **OpenAI API** or **Hugging Face** (for embeddings)

#### **Project Structure**
```
kmrl-system/
├── backend/
│   ├── kmrl-gateway/          # API Gateway + Auth
│   ├── kmrl-connectors/       # Data source connectors
│   ├── kmrl-document-worker/  # Document processing
│   ├── kmrl-rag-worker/       # RAG pipeline
│   ├── kmrl-notification-worker/ # Smart notifications
│   ├── kmrl-webapp/           # Django backend
│   └── shared/                # Common libraries
├── frontend/
│   ├── kmrl-web/              # React web interface
│   └── kmrl-mobile/           # React Native mobile app
├── infrastructure/
│   ├── postgresql/            # Database setup
│   ├── redis/                 # Cache & queues
│   ├── minio/                 # Object storage
│   ├── opensearch/           # Vector database
│   └── tesseract/            # OCR engine
└── scripts/
    ├── setup.sh               # Automated setup
    ├── start-dev.sh           # Start all services
    └── stop-dev.sh            # Stop all services
```

#### **Step-by-Step Setup**

**1. Environment Setup**
```bash
# Create project directory
mkdir kmrl-system && cd kmrl-system

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

**2. Database Setup**
```bash
# Install PostgreSQL
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# macOS:
brew install postgresql

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database and user
sudo -u postgres psql
CREATE DATABASE kmrl_db;
CREATE USER kmrl_user WITH PASSWORD 'kmrl_password';
GRANT ALL PRIVILEGES ON DATABASE kmrl_db TO kmrl_user;
```

**3. Redis Setup**
```bash
# Install Redis
# Ubuntu/Debian:
sudo apt-get install redis-server

# macOS:
brew install redis

# Start Redis
sudo systemctl start redis-server  # Linux
brew services start redis           # macOS
```

**4. MinIO Setup (Object Storage)**
```bash
# Download MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio

# Start MinIO server
./minio server ./data --console-address ":9001"
# Access: http://localhost:9001 (admin/minioadmin)
```

**5. OpenSearch Setup (Vector Database)**
```bash
# Install OpenSearch
# Ubuntu/Debian:
wget https://artifacts.opensearch.org/releases/bundle/opensearch/2.11.0/opensearch-2.11.0-linux-x64.tar.gz
tar -xzf opensearch-2.11.0-linux-x64.tar.gz
cd opensearch-2.11.0

# Configure OpenSearch
echo "network.host: 0.0.0.0" >> config/opensearch.yml
echo "discovery.type: single-node" >> config/opensearch.yml

# Start OpenSearch
./bin/opensearch
# Access: http://localhost:9200 (admin/admin)
```

**6. Tesseract OCR Setup**
```bash
# Install Tesseract OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-mal

# macOS:
brew install tesseract tesseract-lang

# Verify installation
tesseract --version
tesseract --list-langs  # Should show 'eng' and 'mal'
```

**7. Service Configuration**

**Backend Services (Python)**
```bash
# Each service runs as a separate Python process
cd backend/kmrl-gateway
python app.py --port 3000

cd backend/kmrl-connectors  
python scheduler.py

cd backend/kmrl-document-worker
python worker.py

cd backend/kmrl-rag-worker
python worker.py

cd backend/kmrl-notification-worker
python worker.py

cd backend/kmrl-webapp
python manage.py runserver 8000
```

**Frontend Services (Node.js)**
```bash
# Web interface
cd frontend/kmrl-web
npm install
npm start  # Runs on port 3001

# Mobile app (for development)
cd frontend/kmrl-mobile
npm install
npx react-native start
```

### **Option 2: Cloud Deployment Setup**

#### **AWS Deployment**
```bash
# EC2 Instance Setup
# Instance type: t3.medium or larger
# OS: Ubuntu 20.04 LTS

# Install dependencies
sudo apt update
sudo apt install python3.9 python3-pip postgresql redis-server nginx

# Setup application
git clone <kmrl-repo>
cd kmrl-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure services
sudo systemctl enable postgresql redis-server nginx
sudo systemctl start postgresql redis-server nginx
```

#### **Google Cloud Platform**
```bash
# Compute Engine Setup
# Machine type: e2-medium or larger
# OS: Ubuntu 20.04 LTS

# Install dependencies
sudo apt update
sudo apt install python3.9 python3-pip postgresql redis-server

# Setup application
git clone <kmrl-repo>
cd kmrl-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Option 3: Hybrid Setup (Local + Cloud)**

#### **Local Development + Cloud Services**
```bash
# Run services locally but use cloud databases
# PostgreSQL: AWS RDS or Google Cloud SQL
# Redis: AWS ElastiCache or Google Cloud Memorystore
# Storage: AWS S3 or Google Cloud Storage

# Environment variables
export DATABASE_URL="postgresql://user:pass@cloud-db:5432/kmrl_db"
export REDIS_URL="redis://cloud-redis:6379"
export STORAGE_URL="s3://kmrl-bucket"
```

## Service Management

### **Process Management with PM2**
```bash
# Install PM2
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'kmrl-gateway',
      script: 'backend/kmrl-gateway/app.py',
      interpreter: 'python3',
      port: 3000
    },
    {
      name: 'kmrl-connectors',
      script: 'backend/kmrl-connectors/scheduler.py',
      interpreter: 'python3'
    },
    {
      name: 'kmrl-document-worker',
      script: 'backend/kmrl-document-worker/worker.py',
      interpreter: 'python3',
      instances: 2
    },
    {
      name: 'kmrl-rag-worker',
      script: 'backend/kmrl-rag-worker/worker.py',
      interpreter: 'python3',
      instances: 2
    },
    {
      name: 'kmrl-notification-worker',
      script: 'backend/kmrl-notification-worker/worker.py',
      interpreter: 'python3',
      instances: 1
    },
    {
      name: 'kmrl-webapp',
      script: 'backend/kmrl-webapp/manage.py',
      args: 'runserver 0.0.0.0:8000',
      interpreter: 'python3'
    },
    {
      name: 'kmrl-web',
      script: 'frontend/kmrl-web/package.json',
      args: 'start',
      interpreter: 'npm',
      port: 3001
    }
  ]
};
EOF

# Start all services
pm2 start ecosystem.config.js

# Monitor services
pm2 monit

# Stop services
pm2 stop all
```

### **Systemd Service Management**
```bash
# Create systemd service files for each component
sudo tee /etc/systemd/system/kmrl-gateway.service << EOF
[Unit]
Description=KMRL API Gateway
After=network.target

[Service]
Type=simple
User=kmrl
WorkingDirectory=/opt/kmrl-system/backend/kmrl-gateway
ExecStart=/opt/kmrl-system/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable kmrl-gateway
sudo systemctl start kmrl-gateway
```

## Development Workflow

### **Local Development Scripts**
```bash
# setup.sh - Initial setup
#!/bin/bash
echo "Setting up KMRL system..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Redis
redis-server --daemonize yes

# Start MinIO
./minio server ./data --console-address ":9001" &

echo "Setup complete! Run ./start-dev.sh to start all services"
```

```bash
# start-dev.sh - Start all services
#!/bin/bash
echo "Starting KMRL development environment..."

# Start infrastructure services
redis-server --daemonize yes
./minio server ./data --console-address ":9001" &
./opensearch-2.11.0/bin/opensearch &

# Start backend services
cd backend/kmrl-gateway && python app.py &
cd backend/kmrl-connectors && python scheduler.py &
cd backend/kmrl-document-worker && python worker.py &
cd backend/kmrl-rag-worker && python worker.py &
cd backend/kmrl-notification-worker && python worker.py &
cd backend/kmrl-webapp && python manage.py runserver 8000 &

# Start frontend
cd frontend/kmrl-web && npm start &

echo "All services started!"
echo "Gateway: http://localhost:3000"
echo "Web App: http://localhost:8000"
echo "Frontend: http://localhost:3001"
echo "MinIO Console: http://localhost:9001"
echo "OpenSearch: http://localhost:9200"
```

```bash
# stop-dev.sh - Stop all services
#!/bin/bash
echo "Stopping KMRL development environment..."

# Stop Python processes
pkill -f "python.*kmrl"

# Stop Node processes
pkill -f "npm.*start"

# Stop Redis
redis-cli shutdown

# Stop MinIO
pkill -f minio

# Stop OpenSearch
pkill -f opensearch

echo "All services stopped!"
```

## Configuration Management

### **Environment Variables**
```bash
# .env file for each service
# kmrl-gateway/.env
PORT=3000
DATABASE_URL=postgresql://kmrl_user:kmrl_password@localhost:5432/kmrl_db
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-jwt-secret-key
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
OPENSEARCH_URL=http://localhost:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin
OPENAI_API_KEY=your-openai-api-key
TESSERACT_PATH=/usr/bin/tesseract

# kmrl-connectors/.env
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_USER=kmrl@company.com
EMAIL_PASSWORD=app-password
MAXIMO_URL=https://maximo.company.com
MAXIMO_USER=kmrl_user
MAXIMO_PASSWORD=maximo_password
SHAREPOINT_URL=https://company.sharepoint.com
SHAREPOINT_TOKEN=sharepoint-token
```

### **Service Configuration Files**
```yaml
# config/services.yaml
services:
  gateway:
    port: 3000
    health_check: /health
    rate_limit: 1000/hour
    
  connectors:
    email:
      check_interval: 300  # 5 minutes
      batch_size: 50
    maximo:
      check_interval: 900  # 15 minutes
      batch_size: 100
    sharepoint:
      check_interval: 1800  # 30 minutes
      batch_size: 200
      
  workers:
    document:
      concurrency: 4
      max_retries: 3
    rag:
      concurrency: 2
      max_retries: 3
```

## Monitoring & Logging

### **Log Management**
```bash
# Centralized logging with logrotate
sudo tee /etc/logrotate.d/kmrl << EOF
/opt/kmrl-system/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 kmrl kmrl
}
EOF
```

### **Health Monitoring**
```bash
# health-check.sh
#!/bin/bash
echo "Checking KMRL system health..."

# Check services
curl -f http://localhost:3000/health || echo "Gateway DOWN"
curl -f http://localhost:8000/health || echo "Web App DOWN"
curl -f http://localhost:3001 || echo "Frontend DOWN"

# Check databases
pg_isready -h localhost -p 5432 || echo "PostgreSQL DOWN"
redis-cli ping || echo "Redis DOWN"

# Check storage
curl -f http://localhost:9000/minio/health/live || echo "MinIO DOWN"

# Check OpenSearch
curl -f http://localhost:9200/_cluster/health || echo "OpenSearch DOWN"

# Check Tesseract
tesseract --version || echo "Tesseract DOWN"
```

## Troubleshooting

### **Common Issues**

**1. Port Conflicts**
```bash
# Check what's using ports
sudo netstat -tlnp | grep :3000
sudo lsof -i :3000

# Kill processes using ports
sudo kill -9 $(sudo lsof -t -i:3000)
```

**2. Database Connection Issues**
```bash
# Test PostgreSQL connection
psql -h localhost -U kmrl_user -d kmrl_db

# Test Redis connection
redis-cli ping

# Test OpenSearch connection
curl -u admin:admin http://localhost:9200/_cluster/health

# Test Tesseract
tesseract --version
```

**3. Service Startup Issues**
```bash
# Check service logs
tail -f /opt/kmrl-system/logs/gateway.log
tail -f /opt/kmrl-system/logs/worker.log

# Check system resources
htop
df -h
free -h
```

## Performance Optimization

### **Resource Allocation**
```bash
# Optimize PostgreSQL
sudo nano /etc/postgresql/13/main/postgresql.conf
# shared_buffers = 256MB
# effective_cache_size = 1GB
# work_mem = 4MB

# Optimize Redis
sudo nano /etc/redis/redis.conf
# maxmemory 512mb
# maxmemory-policy allkeys-lru

# Optimize OpenSearch
sudo nano /etc/opensearch/opensearch.yml
# cluster.name: kmrl-cluster
# node.name: kmrl-node-1
# bootstrap.memory_lock: true
# "ES_JAVA_OPTS=-Xms1g -Xmx1g"
```

### **Scaling Workers**
```bash
# Increase worker instances
pm2 scale kmrl-document-worker 4
pm2 scale kmrl-rag-worker 3
pm2 scale kmrl-notification-worker 2

# Monitor performance
pm2 monit
```

This setup provides a comprehensive non-Docker approach for running the KMRL system, suitable for development, testing, and production deployment scenarios.
