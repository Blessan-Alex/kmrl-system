#!/bin/bash
# KMRL System Development Start Script

echo "Starting KMRL System development environment..."

# Activate virtual environment
source venv/bin/activate

# Start infrastructure services
echo "Starting infrastructure services..."

# Start Redis
redis-server --daemonize yes

# Start MinIO
minio server ./data/minio --console-address ":9001" &
MINIO_PID=$!

# Start OpenSearch
cd opensearch-2.11.0
./bin/opensearch &
OPENSEARCH_PID=$!
cd ..

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Start backend services
echo "Starting backend services..."

# Start API Gateway
cd backend/kmrl-gateway
python app.py &
GATEWAY_PID=$!
cd ../..

# Start Connector Scheduler
cd backend/kmrl-connectors
celery -A scheduler beat --loglevel=info &
SCHEDULER_PID=$!
cd ../..

# Start Connector Workers
cd backend/kmrl-connectors
celery -A scheduler worker --loglevel=info --concurrency=2 &
WORKER_PID=$!
cd ../..

# Start Document Worker
cd backend/kmrl-document-worker
celery -A worker worker --loglevel=info --concurrency=2 &
DOCUMENT_WORKER_PID=$!
cd ../..

# Start RAG Worker
cd backend/kmrl-rag-worker
celery -A worker worker --loglevel=info --concurrency=2 &
RAG_WORKER_PID=$!
cd ../..

# Start Notification Worker
cd backend/kmrl-notification-worker
celery -A worker worker --loglevel=info --concurrency=1 &
NOTIFICATION_WORKER_PID=$!
cd ../..

# Start Django Web App
cd backend/kmrl-webapp
python manage.py migrate
python manage.py runserver 8000 &
DJANGO_PID=$!
cd ../..

# Start Frontend (if available)
if [ -d "frontend/kmrl-web" ]; then
    echo "Starting React frontend..."
    cd frontend/kmrl-web
    npm install
    npm start &
    FRONTEND_PID=$!
    cd ../..
fi

echo "All services started!"
echo "Gateway: http://localhost:3000"
echo "Web App: http://localhost:8000"
echo "Frontend: http://localhost:3001"
echo "MinIO Console: http://localhost:9001"
echo "OpenSearch: http://localhost:9200"

# Save PIDs for cleanup
echo $MINIO_PID > .pids/minio.pid
echo $OPENSEARCH_PID > .pids/opensearch.pid
echo $GATEWAY_PID > .pids/gateway.pid
echo $SCHEDULER_PID > .pids/scheduler.pid
echo $WORKER_PID > .pids/worker.pid
echo $DOCUMENT_WORKER_PID > .pids/document-worker.pid
echo $RAG_WORKER_PID > .pids/rag-worker.pid
echo $NOTIFICATION_WORKER_PID > .pids/notification-worker.pid
echo $DJANGO_PID > .pids/django.pid
if [ ! -z "$FRONTEND_PID" ]; then
    echo $FRONTEND_PID > .pids/frontend.pid
fi

echo "Use ./scripts/stop-dev.sh to stop all services"
