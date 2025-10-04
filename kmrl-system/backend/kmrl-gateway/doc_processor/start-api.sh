#!/bin/sh
# start-api.sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for MinIO to be ready on port 9000
/wait-for-it.sh minio_storage

# wait for Postgres and Redis
/wait-for-it.sh postgres 5432
/wait-for-it.sh redis_queue 6379

echo "--> MinIO is ready. Giving the service 5 seconds to initialize..."
sleep 5

echo "--> Starting FastAPI server..."
# Execute the final command, replacing this shell process.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000