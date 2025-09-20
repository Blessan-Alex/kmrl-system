## Optimized KMRL Container Architecture (8 Containers)

### **1. kmrl-gateway** (API Gateway)
**Components:** Entry Point & Request Routing
- Single API Endpoint (POST /api/v1/documents/upload)
- API Key Auth & Session Auth
- File validation (size limits, type validation, security scanning)
- Request routing and load balancing
- Rate limiting and throttling
- CORS handling
- Request/response logging

### **2. kmrl-connectors** (Data Source Connectors)
**Components:** Automatic Data Ingestion
- **Email Connector:** IMAP monitoring every 5 minutes
- **Maximo Connector:** Work order sync every 15 minutes
- **SharePoint Connector:** Document sync every 30 minutes
- **WhatsApp Business Connector:** Message sync every 10 minutes
- **Cloud Link Processor:** On-demand processing
- **Scheduled Ingestion:** Celery beat scheduler for automatic data pulling
- **State Management:** Redis-based duplicate prevention and incremental sync

### **3. kmrl-document-worker** (Document Processing)
**Components:** Core Document Processing Pipeline
- File type detection
- Quality assessment
- Route to appropriate processor
- Text processing (Markitdown, language detection)
- Image processing (OCR with Tesseract, enhancement)
- CAD processing (metadata extraction)
- Mixed content processing
- Quality validation and confidence scoring
- Error handling and fallbacks

**Scaling:** Multiple instances can run in parallel, each picking up tasks from the queue

### **4. kmrl-rag-worker** (RAG Pipeline)
**Components:** RAG Processing & Query Engine
- **RAG Pipeline Processing:**
  - Data preprocessing and cleaning
  - Smart chunking strategies
  - Embedding generation (OpenAI/all-MiniLM-L6-v2)
  - Vector storage in OpenSearch
  - Document indexing and metadata association
- **Query Processing:**
  - Query embedding generation
  - Vector similarity search
  - Context assembly
  - LLM response generation
  - Source citation handling

**Scaling:** Multiple instances for parallel processing of large document batches

### **5. kmrl-notification-worker** (Smart Notifications)
**Components:** Notification Processing
- Trigger notification scanning
- Vector similarity search
- Threshold checking
- Rule-based notification generation
- Multi-channel delivery (Email, SMS, Slack)
- Notification status tracking
- Delivery confirmation

**Scaling:** Multiple instances for handling notification bursts

### **6. kmrl-webapp** (Frontend + Backend Services)
**Components:** User Interfaces & Business Logic
- **User Interfaces:**
  - Department dashboards
  - Search interface
  - Chat interface
  - Analytics dashboard
  - Quality control dashboard
- **Backend Services:**
  - Human review workflows & quality control
  - Document rejection handling and logging
  - Review task assignment and priority management
  - Document analytics & compliance monitoring
  - Performance metrics calculation
  - Automated compliance checks
  - Audit trail management
- **Mobile Backend:**
  - Mobile-specific API endpoints
  - Field worker authentication and authorization
  - Offline data synchronization
  - Location-based query services
  - Emergency procedure access
  - Push notification services

### **7. kmrl-infrastructure** (Storage + Database + Queue)
**Components:** Data Persistence & Message Broker
- **File Storage Management:**
  - MinIO/S3 integration
  - File upload/download services
  - Storage optimization
- **Data Persistence:**
  - PostgreSQL with connection pooling
  - Document metadata storage
  - Status tracking and audit logs
- **Task Management & Message Broker:**
  - Redis cluster for high availability
  - Celery task distribution
  - Dead letter queues for failed tasks
  - Automatic ingestion scheduling
  - State tracking for connector sync timestamps
  - Fault tolerance with automatic retry

### **8. kmrl-integration** (External Systems + IoT + Monitoring)
**Components:** External Integration & System Monitoring
- **External System Integration:**
  - Maximo integration
  - Finance system sync
  - Email system integration
  - Third-party APIs
  - Webhook handling
- **Data Source Credential Management:**
  - Secure credential storage and rotation
  - Connection health monitoring
  - API rate limit management
  - Authentication token refresh
- **IoT Device Integration:**
  - IoT device registration and management
  - Real-time sensor data ingestion
  - Sensor data correlation and analysis
  - Device health monitoring
  - Predictive maintenance algorithms
  - Real-time alert generation
  - Device communication protocols (MQTT, HTTP, WebSocket)
- **System Monitoring:**
  - Container health monitoring
  - Performance metrics
  - Error tracking
  - Resource utilization monitoring
  - Prometheus metrics collection
  - Grafana dashboards

## Key Benefits of This 8-Container Approach:

1. **Balanced Architecture:** 8 containers provide good separation of concerns while remaining manageable

2. **Specialized Workers:** Dedicated workers for document processing, RAG pipeline, and notifications

3. **Independent Scaling:** Each worker type can be scaled independently based on load

4. **Clear Separation:** Gateway, connectors, workers, webapp, infrastructure, and integration are clearly separated

5. **Queue-Driven Architecture:** Workers pull tasks from Redis queues, enabling automatic load distribution

6. **Horizontal Scaling:** Multiple worker instances can run in parallel for high throughput

7. **Fault Tolerance:** If one worker fails, others continue processing

8. **Hackathon-Friendly:** Manageable number of containers with clear responsibilities

9. **Automatic Data Ingestion:** Continuous monitoring and ingestion from all KMRL data sources without manual intervention

10. **Duplicate Prevention:** Redis-based state management ensures no document is processed twice

11. **Incremental Sync:** Only new/modified documents are fetched, reducing bandwidth and processing overhead

12. **Monitoring Integration:** Built-in system monitoring and observability

## Automatic Data Ingestion Strategy:

**Data Sources Covered:**
- **Email Attachments:** IMAP monitoring every 5 minutes for new emails with attachments
- **Maximo Exports:** Work order sync every 15 minutes for in-progress orders with attachments
- **SharePoint Repositories:** Document library sync every 30 minutes for modified files
- **WhatsApp PDFs:** Business API monitoring every 10 minutes for new document messages
- **Cloud Links:** On-demand processing of shared cloud document links
- **Hard-copy Scans:** Manual upload endpoint for scanned documents

**Implementation Details:**
- **Celery Beat Scheduler:** Automated task scheduling for periodic data source monitoring
- **Redis State Management:** Tracks last sync times and processed document IDs
- **Incremental Processing:** Only fetches documents modified since last successful sync
- **Fault Tolerance:** Automatic retry with exponential backoff for failed ingestion attempts
- **Credential Management:** Secure storage and rotation of data source authentication credentials

This optimized 8-container architecture provides excellent separation of concerns while remaining hackathon-friendly. It comprehensively covers all functionality from the detailed flow while maintaining scalability, fault tolerance, and automatic data ingestion from all KMRL data sources.