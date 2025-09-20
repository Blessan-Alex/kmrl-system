Automatic Data Sources → Connector services → API Key Auth
Manual Upload Data sources → Session Auth
Single API Endpoint [POST api/v1/documents/upload]
File Validation [Prevent malware etc]
Save to MinIO/S3
Create Database Record [PostgreSQL]
Queue Processing Task [Redis + Celery]

Worker Picks Task from Queue
File Type Detection [DWG, PDF, Images, Office docs]
Quality Assessment [Resolution, contrast, blur check]
Route to Processor [Text/Image/CAD/Mixed]
Text Extraction [Markitdown for Office docs]
OCR Processing [Malayalam + English support]
Image Enhancement [Denoise, contrast, sharpen]
Quality Validation [Confidence scoring]
Human Review Flag [Low confidence documents]
Save Processing Results [Unified text format]

Data Preprocessing [Clean, deduplicate, fix OCR errors]
Smart Chunking [Department-specific strategies]
Generate Embeddings [OpenAI text-embedding-3-large/all-MiniLM-L6-v2]
Store in Vector Database [OpenSearch with HNSW]
Mark Document as RAG Ready

Trigger Notification Scan [Vector similarity search]
Load Pre-computed Trigger Embeddings [Cached in Redis]
Vector Similarity Search [Cosine similarity calculation]
Check Similarity Thresholds [Category-specific thresholds]
Generate Notifications Based on Rules [Rule-based system]
Send Smart Notification [Email, SMS, Slack based on priority]
Update Notification Status [Track delivery and response]

Department Dashboards [Role-based views]
Intelligent Search [RAG-powered search]
Chat Interface [Conversational AI]
Document Analytics [Usage patterns, insights]
Compliance Monitoring [Automated compliance checks]
Automated Workflows [Incident processing, maintenance requests]
Smart Notifications [Contextual alerts, deadline reminders]
External Integration [Maximo, Finance systems]
Mobile Application [Field worker access, offline capabilities]