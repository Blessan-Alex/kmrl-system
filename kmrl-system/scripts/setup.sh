#!/bin/bash
# KMRL System Setup Script

echo "Setting up KMRL System..."

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p data/minio
mkdir -p data/opensearch
mkdir -p .pids

# Setup PostgreSQL
echo "Setting up PostgreSQL..."
sudo -u postgres psql -f infrastructure/postgresql/setup.sql

# Setup Redis
echo "Setting up Redis..."
sudo cp infrastructure/redis/redis.conf /etc/redis/redis.conf
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Setup MinIO
echo "Setting up MinIO..."
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/
chmod +x infrastructure/minio/setup.sh
./infrastructure/minio/setup.sh

# Setup OpenSearch
echo "Setting up OpenSearch..."
wget https://artifacts.opensearch.org/releases/bundle/opensearch/2.11.0/opensearch-2.11.0-linux-x64.tar.gz
tar -xzf opensearch-2.11.0-linux-x64.tar.gz
cd opensearch-2.11.0
cp ../infrastructure/opensearch/opensearch.yml config/
cd ..

# Setup Tesseract OCR
echo "Setting up Tesseract OCR..."
chmod +x infrastructure/tesseract/setup.sh
./infrastructure/tesseract/setup.sh

# Copy environment file
echo "Setting up environment..."
cp env.example .env
echo "Please edit .env file with your configuration"

echo "Setup complete! Run ./scripts/start-dev.sh to start all services"
