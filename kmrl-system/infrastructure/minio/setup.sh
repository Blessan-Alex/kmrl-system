#!/bin/bash
# MinIO Setup for KMRL Knowledge Hub

# Create MinIO data directory
mkdir -p ./data/minio

# Set environment variables
export MINIO_ROOT_USER=minioadmin
export MINIO_ROOT_PASSWORD=minioadmin123

# Start MinIO server
minio server ./data/minio --console-address ":9001" &

# Wait for MinIO to start
sleep 5

# Create buckets
mc alias set myminio http://localhost:9000 minioadmin minioadmin123
mc mb myminio/kmrl-documents
mc mb myminio/kmrl-processed
mc mb myminio/kmrl-archived

# Set bucket policies
mc anonymous set public myminio/kmrl-documents
mc anonymous set public myminio/kmrl-processed

echo "MinIO setup complete!"
echo "Access: http://localhost:9001"
echo "Username: minioadmin"
echo "Password: minioadmin123"
