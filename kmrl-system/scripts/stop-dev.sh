#!/bin/bash
# KMRL System Development Stop Script

echo "Stopping KMRL System development environment..."

# Stop services using PIDs
if [ -f ".pids/minio.pid" ]; then
    kill $(cat .pids/minio.pid) 2>/dev/null
    rm .pids/minio.pid
fi

if [ -f ".pids/opensearch.pid" ]; then
    kill $(cat .pids/opensearch.pid) 2>/dev/null
    rm .pids/opensearch.pid
fi

if [ -f ".pids/gateway.pid" ]; then
    kill $(cat .pids/gateway.pid) 2>/dev/null
    rm .pids/gateway.pid
fi

if [ -f ".pids/scheduler.pid" ]; then
    kill $(cat .pids/scheduler.pid) 2>/dev/null
    rm .pids/scheduler.pid
fi

if [ -f ".pids/worker.pid" ]; then
    kill $(cat .pids/worker.pid) 2>/dev/null
    rm .pids/worker.pid
fi

if [ -f ".pids/document-worker.pid" ]; then
    kill $(cat .pids/document-worker.pid) 2>/dev/null
    rm .pids/document-worker.pid
fi

if [ -f ".pids/rag-worker.pid" ]; then
    kill $(cat .pids/rag-worker.pid) 2>/dev/null
    rm .pids/rag-worker.pid
fi

if [ -f ".pids/notification-worker.pid" ]; then
    kill $(cat .pids/notification-worker.pid) 2>/dev/null
    rm .pids/notification-worker.pid
fi

if [ -f ".pids/django.pid" ]; then
    kill $(cat .pids/django.pid) 2>/dev/null
    rm .pids/django.pid
fi

if [ -f ".pids/frontend.pid" ]; then
    kill $(cat .pids/frontend.pid) 2>/dev/null
    rm .pids/frontend.pid
fi

# Stop Redis
redis-cli shutdown 2>/dev/null

# Stop any remaining Python processes
pkill -f "python.*kmrl" 2>/dev/null

# Stop any remaining Node processes
pkill -f "npm.*start" 2>/dev/null

# Stop MinIO
pkill -f minio 2>/dev/null

# Stop OpenSearch
pkill -f opensearch 2>/dev/null

echo "All services stopped!"
