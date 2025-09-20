#!/bin/bash
# KMRL System Implementation Verification Script

echo "Verifying KMRL System Implementation..."

# Check project structure
echo "Checking project structure..."
required_dirs=(
    "backend/kmrl-gateway"
    "backend/kmrl-connectors"
    "backend/kmrl-document-worker"
    "backend/kmrl-rag-worker"
    "backend/kmrl-notification-worker"
    "backend/kmrl-webapp"
    "backend/shared"
    "frontend/kmrl-web"
    "frontend/kmrl-mobile"
    "infrastructure/postgresql"
    "infrastructure/redis"
    "infrastructure/minio"
    "infrastructure/opensearch"
    "infrastructure/tesseract"
    "scripts"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir exists"
    else
        echo "✗ $dir missing"
    fi
done

# Check backend components
echo "Checking backend components..."

# Gateway
if [ -f "backend/kmrl-gateway/app.py" ]; then
    echo "✓ FastAPI Gateway implemented"
else
    echo "✗ FastAPI Gateway missing"
fi

# Connectors
connectors=("email_connector.py" "maximo_connector.py" "sharepoint_connector.py" "whatsapp_connector.py")
for connector in "${connectors[@]}"; do
    if [ -f "backend/kmrl-connectors/connectors/$connector" ]; then
        echo "✓ $connector implemented"
    else
        echo "✗ $connector missing"
    fi
done

# Workers
workers=("kmrl-document-worker" "kmrl-rag-worker" "kmrl-notification-worker")
for worker in "${workers[@]}"; do
    if [ -f "backend/$worker/worker.py" ]; then
        echo "✓ $worker implemented"
    else
        echo "✗ $worker missing"
    fi
done

# Django Web App
if [ -f "backend/kmrl-webapp/manage.py" ]; then
    echo "✓ Django Web App implemented"
else
    echo "✗ Django Web App missing"
fi

# Shared libraries
shared_libs=("document_processor.py" "language_detector.py" "department_classifier.py" "text_chunker.py" "embedding_generator.py" "notification_engine.py" "stakeholder_manager.py" "similarity_calculator.py")
for lib in "${shared_libs[@]}"; do
    if [ -f "backend/shared/$lib" ]; then
        echo "✓ $lib implemented"
    else
        echo "✗ $lib missing"
    fi
done

# Infrastructure setup
echo "Checking infrastructure setup..."
infra_files=("postgresql/setup.sql" "redis/redis.conf" "minio/setup.sh" "opensearch/opensearch.yml" "tesseract/setup.sh")
for file in "${infra_files[@]}"; do
    if [ -f "infrastructure/$file" ]; then
        echo "✓ $file implemented"
    else
        echo "✗ $file missing"
    fi
done

# Scripts
echo "Checking scripts..."
scripts=("setup.sh" "start-dev.sh" "stop-dev.sh")
for script in "${scripts[@]}"; do
    if [ -f "scripts/$script" ]; then
        echo "✓ $script implemented"
    else
        echo "✗ $script missing"
    fi
done

# Configuration files
echo "Checking configuration files..."
config_files=("requirements.txt" "env.example" "README.md")
for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file implemented"
    else
        echo "✗ $file missing"
    fi
done

# Check key features from plan.md
echo "Checking key features implementation..."

# Multi-language support
if grep -q "malayalam" backend/shared/language_detector.py; then
    echo "✓ Multi-language support (Malayalam/English) implemented"
else
    echo "✗ Multi-language support missing"
fi

# Department classification
if grep -q "department" backend/shared/department_classifier.py; then
    echo "✓ Department classification implemented"
else
    echo "✗ Department classification missing"
fi

# Smart notifications
if grep -q "notification" backend/kmrl-notification-worker/worker.py; then
    echo "✓ Smart notifications implemented"
else
    echo "✗ Smart notifications missing"
fi

# Automatic ingestion
if grep -q "celery" backend/kmrl-connectors/scheduler.py; then
    echo "✓ Automatic document ingestion implemented"
else
    echo "✗ Automatic document ingestion missing"
fi

# RAG pipeline
if grep -q "embedding" backend/kmrl-rag-worker/worker.py; then
    echo "✓ RAG pipeline implemented"
else
    echo "✗ RAG pipeline missing"
fi

# Document processing
if grep -q "tesseract" backend/shared/document_processor.py; then
    echo "✓ Document processing (OCR) implemented"
else
    echo "✗ Document processing missing"
fi

echo "Verification complete!"
echo "Check the output above for any missing components."
