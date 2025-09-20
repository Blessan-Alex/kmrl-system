# Dockerfile for connector service
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY connectors/ .
COPY config/ .

CMD ["python", "connector_manager.py"]