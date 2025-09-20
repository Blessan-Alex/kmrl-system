# KMRL Knowledge Hub
## Solving KMRL's Document Management Crisis

### Problem Context
KMRL faces a **silent productivity tax** from thousands of daily documents across multiple channels (email, Maximo, SharePoint, WhatsApp) in English, Malayalam, and bilingual formats. The system provides **rapid, trustworthy snapshots** while preserving traceability to original sources.

### Key Challenges Addressed
- **Information latency**: Front-line managers get instant access to relevant documents
- **Siloed awareness**: Cross-department document visibility  
- **Compliance exposure**: Automated tracking of regulatory documents
- **Knowledge attrition**: Institutional memory captured and searchable
- **Duplicated effort**: Centralized document processing eliminates redundant work

### Architecture
- **Backend**: FastAPI Gateway + Django Web App + Connectors
- **Frontend**: React Dashboard + React Native Mobile
- **Infrastructure**: PostgreSQL + Redis + MinIO + OpenSearch
- **Processing**: Celery Workers + Tesseract OCR + Markitdown

### Quick Start
```bash
# Setup environment
./scripts/setup.sh

# Start all services
./scripts/start-dev.sh

# Access services
# Gateway: http://localhost:3000
# Web App: http://localhost:8000
# Frontend: http://localhost:3001
# MinIO Console: http://localhost:9001
# OpenSearch: http://localhost:9200
```

### Data Sources
- **Email**: IMAP-based attachment ingestion with Malayalam detection
- **Maximo**: Work order attachments and maintenance documents
- **SharePoint**: Corporate document libraries and policies
- **WhatsApp**: Field reports and mobile document uploads

### Features
- Automatic document ingestion from all KMRL sources
- Multi-language support (English, Malayalam, Mixed)
- Department-based document classification
- Smart notifications for stakeholders
- RAG-powered search and chat interface
- Mobile app for field workers
- Analytics and compliance monitoring
