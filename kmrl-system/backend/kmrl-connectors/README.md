# KMRL Connectors

## Overview
The KMRL Connectors module provides automatic document ingestion from multiple data sources for the KMRL Knowledge Hub. It implements a unified architecture for fetching documents from Email, Maximo, SharePoint, and WhatsApp sources.

## Architecture

### Base Connector
- **File**: `base/base_connector.py`
- **Purpose**: Abstract base class for all connectors
- **Features**: 
  - State management with Redis
  - Duplicate prevention
  - API integration
  - Sync status tracking

### Data Source Connectors

#### 1. Email Connector
- **File**: `connectors/email_connector.py`
- **Purpose**: Fetches email attachments from IMAP servers
- **Features**:
  - Malayalam/English language detection
  - Department classification (6 departments)
  - IMAP SSL support
  - Attachment filtering

#### 2. Maximo Connector
- **File**: `connectors/maximo_connector.py`
- **Purpose**: Fetches work order attachments from Maximo
- **Features**:
  - Work order metadata extraction
  - Department classification based on work type
  - Enhanced error handling
  - Timeout management

#### 3. SharePoint Connector
- **File**: `connectors/sharepoint_connector.py`
- **Purpose**: Fetches documents from SharePoint libraries
- **Features**:
  - OAuth2 authentication
  - Content type detection
  - File metadata extraction
  - Department classification

#### 4. WhatsApp Connector
- **File**: `connectors/whatsapp_connector.py`
- **Purpose**: Fetches documents from WhatsApp Business API
- **Features**:
  - Media file processing
  - Language detection from message text
  - Department classification
  - Filename extraction

### Scheduler
- **File**: `scheduler.py`
- **Purpose**: Celery-based automatic document ingestion
- **Features**:
  - Scheduled fetching (5-30 minute intervals)
  - Retry logic with exponential backoff
  - Health monitoring
  - Task cleanup

### Utilities
- **File**: `utils/credentials_manager.py`
- **Purpose**: Secure credential management
- **Features**:
  - Environment variable integration
  - Credential validation
  - Multi-source support

## Configuration

### Environment Variables
```bash
# Email Configuration
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_USER=kmrl@company.com
EMAIL_PASSWORD=app_password

# Maximo Configuration
MAXIMO_URL=https://maximo.company.com
MAXIMO_USER=kmrl_user
MAXIMO_PASSWORD=maximo_password

# SharePoint Configuration
SHAREPOINT_URL=https://company.sharepoint.com
SHAREPOINT_CLIENT_ID=client_id
SHAREPOINT_CLIENT_SECRET=client_secret

# WhatsApp Configuration
WHATSAPP_ACCESS_TOKEN=access_token
WHATSAPP_PHONE_NUMBER_ID=phone_number_id

# Redis Configuration
REDIS_URL=redis://localhost:6379
```

### Celery Configuration
```python
# config/celery_config.py
broker_url = 'redis://localhost:6379'
result_backend = 'redis://localhost:6379'
task_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Kolkata'
```

## Usage

### Running the Scheduler
```bash
# Start Celery Beat (scheduler)
celery -A scheduler beat --loglevel=info

# Start Celery Worker
celery -A scheduler worker --loglevel=info --concurrency=2
```

### Manual Testing
```bash
# Run connector tests
python test_connectors.py

# Test individual connectors
python -c "from connectors.email_connector import EmailConnector; print('Email connector loaded')"
```

### API Integration
```python
from connectors.email_connector import EmailConnector

# Initialize connector
connector = EmailConnector(imap_host="imap.gmail.com", imap_port=993)

# Fetch documents
credentials = {"email": "user@company.com", "password": "password"}
documents = connector.fetch_documents(credentials)

# Sync documents
connector.sync_documents(credentials)
```

## Features

### Language Detection
- **English**: Standard processing
- **Malayalam**: Unicode range detection
- **Mixed**: Bilingual document handling

### Department Classification
- **Engineering**: Maintenance, technical documents
- **Finance**: Invoices, budgets, payments
- **Safety**: Incidents, compliance, regulations
- **HR**: Personnel, training, policies
- **Operations**: Field reports, procedures
- **Executive**: Board meetings, policies, decisions

### Error Handling
- **Retry Logic**: Exponential backoff for failed requests
- **Timeout Management**: Configurable timeouts for API calls
- **Graceful Degradation**: Continue processing on individual failures
- **Comprehensive Logging**: Structured logging with context

### Monitoring
- **Health Checks**: Regular connector status monitoring
- **Sync Status**: Track last sync times and processed counts
- **Task Monitoring**: Celery task status and performance
- **Error Tracking**: Detailed error logging and reporting

## Schedule

| Connector | Frequency | Purpose |
|-----------|-----------|---------|
| Email | Every 5 minutes | Email attachments |
| Maximo | Every 15 minutes | Work order documents |
| SharePoint | Every 30 minutes | Corporate documents |
| WhatsApp | Every 10 minutes | Field reports |
| Health Check | Every hour | System monitoring |
| Cleanup | Daily at 2 AM | Task cleanup |

## Testing

### Unit Tests
```bash
# Run all tests
python test_connectors.py

# Test specific connector
python -c "from test_connectors import test_email_connector; test_email_connector()"
```

### Integration Tests
```bash
# Test with real credentials (development only)
export EMAIL_USER="test@company.com"
export EMAIL_PASSWORD="test_password"
python -c "from connectors.email_connector import EmailConnector; connector = EmailConnector('imap.gmail.com'); print('Integration test passed')"
```

## Troubleshooting

### Common Issues

#### 1. Authentication Failures
```bash
# Check credentials
echo $EMAIL_USER
echo $MAXIMO_USER

# Test connection
python -c "from utils.credentials_manager import CredentialsManager; cm = CredentialsManager(); print(cm.get_email_credentials())"
```

#### 2. Redis Connection Issues
```bash
# Check Redis status
redis-cli ping

# Check Redis configuration
redis-cli config get "*"
```

#### 3. Celery Task Failures
```bash
# Check Celery status
celery -A scheduler inspect active

# Check task results
celery -A scheduler inspect stats
```

### Logs
```bash
# View connector logs
tail -f logs/kmrl-connectors.log

# View Celery logs
tail -f logs/celery.log
```

## Performance

### Optimization
- **Connection Pooling**: Reuse connections where possible
- **Batch Processing**: Process multiple documents in batches
- **Rate Limiting**: Respect API rate limits
- **Memory Management**: Clean up large file content

### Monitoring
- **Task Duration**: Track processing times
- **Memory Usage**: Monitor memory consumption
- **Error Rates**: Track failure rates
- **Throughput**: Documents processed per minute

## Security

### Credential Management
- **Environment Variables**: Store credentials securely
- **Encryption**: Encrypt sensitive data in transit
- **Access Control**: Limit connector access to required systems
- **Audit Logging**: Log all connector activities

### Data Protection
- **Content Filtering**: Filter sensitive documents
- **Access Logging**: Track document access
- **Retention Policies**: Implement document retention
- **Compliance**: Ensure regulatory compliance

## Deployment

### Production Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with production values

# Start services
celery -A scheduler beat --daemonize
celery -A scheduler worker --daemonize --concurrency=4

# Monitor services
celery -A scheduler inspect active
```

### Docker Deployment
```bash
# Build image
docker build -t kmrl-connectors .

# Run container
docker run -d --name kmrl-connectors \
  -e REDIS_URL=redis://redis:6379 \
  -e EMAIL_USER=user@company.com \
  kmrl-connectors
```

## Contributing

### Development
1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Add tests
5. Submit pull request

### Code Standards
- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations
- **Docstrings**: Document all functions
- **Testing**: Maintain test coverage

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Support
For support and questions:
- **Documentation**: Check this README and inline comments
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Email**: Contact the development team
