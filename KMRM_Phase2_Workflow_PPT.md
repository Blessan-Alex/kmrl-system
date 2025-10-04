# 🚇 KMRM Phase 2 - Document Processing Workflow
## Hackathon MVP Implementation

---

## 🎯 **Overview**
**End-to-End Document Intelligence Pipeline for Kochi Metro Operations**

---

## 📋 **Phase 2 Components**

### 1. **Data Connectors** 🔌
- **Gmail Connector** → Historical + Incremental sync
- **Google Drive Connector** → File discovery + sync
- **Universal Logging** → Traceability & debugging

### 2. **Document Processing** 📄
- **File Type Detection** → PDF, Images, Office docs, Text
- **Content Extraction** → OCR, Text parsing, Language detection
- **Quality Assessment** → Chunking, Preprocessing

### 3. **Data Preprocessing** 🔧
- **Text Normalization** → Format standardization, noise removal
- **Language Detection** → EN/Malayalam identification
- **Quality Enhancement** → Error correction, validation

### 4. **Smart Chunking** ✂️
- **Chonkie Strategies** → Specialized document segmentation
- **Semantic Chunking** → Context-aware splitting
- **Chunk Optimization** → Size & overlap management

### 5. **Embedding & Vector Storage** 🧠
- **Vyakarth Model** → Multilingual embedding generation
- **OpenSearch** → Vector database storage & indexing
- **Similarity Indexing** → Fast retrieval optimization

### 6. **Query & Retrieval** 🔍
- **Hybrid Search** → Semantic + Keyword combination
- **Cosine Similarity** → Vector similarity matching
- **Context Ranking** → Relevance scoring

### 7. **AI Response Generation** 🤖
- **Gemini/OpenAI** → Advanced language models
- **Context Integration** → Retrieved knowledge fusion
- **Response Validation** → Quality & accuracy checks

### 8. **User Interface** 💬
- **Bilingual Chat** → English + Malayalam support
- **Audio Chat** → Voice input/output processing
- **Role-Based Access** → Permission management

### 9. **Notification System** 📱
- **SMS Integration** → Text message alerts
- **Email Notifications** → Detailed updates
- **Event-Driven Triggers** → Smart notification delivery

### 10. **Storage & Queue** 💾
- **MinIO** → Raw file storage
- **PostgreSQL** → Metadata & extracted content
- **Redis/Celery** → Processing queue

---

## 🔄 **Workflow Steps**

### **Step 1: Data Ingestion**
```
Gmail/Drive → Historical Sync → Incremental Sync → File Discovery
```

### **Step 2: Security & Filtering**
```
Virus Scan (ClamAV) → File Type Validation → Accept/Reject Decision
```

### **Step 3: Storage**
```
Raw Files → MinIO Bucket → Metadata → PostgreSQL Database
```

### **Step 4: Processing Queue**
```
Document ID → Redis/Celery Queue → Worker Assignment
```

### **Step 5: Content Extraction**
```
File Type Detection → Route Processing → Text Extraction → Language Detection
```

### **Step 6: Data Preprocessing**
```
Text Normalization → Noise Reduction → Language Detection → Quality Enhancement
```

### **Step 7: Smart Chunking**
```
Semantic Chunking → Chonkie Strategies → Context Preservation → Chunk Optimization
```

### **Step 8: Embedding Generation**
```
Vyakarth Model → Vector Conversion → Embedding Storage → Index Creation
```

### **Step 9: Vector Database Storage**
```
OpenSearch Indexing → Metadata Association → Similarity Indexing → Performance Optimization
```

### **Step 10: Query Processing**
```
User Query → Query Embedding → Vector Search → Context Retrieval
```

### **Step 11: Answer Generation**
```
Gemini/OpenAI → Context Processing → Response Generation → Quality Validation
```

### **Step 12: Notification System**
```
Event Detection → SMS/Email Triggers → User Preferences → Delivery Confirmation
```

---

## 📊 **Processing Routes**

| File Type | Processing Method | Output |
|-----------|------------------|---------|
| **PDF** | PyMuPDF + Tesseract OCR | Text + Images |
| **Images** | Tesseract (EN + Malayalam) | OCR Text |
| **Office** | python-docx/openpyxl | Structured Text |
| **Text/CSV** | Direct Reading | Normalized Text |
| **Technical Drawings** | Store as-is | Metadata Only |

---

## 🗄️ **Database Schema**

### **Documents Table**
- `id`, `minio_id`, `source_system`, `file_name`
- `file_type`, `mime_type`, `file_size`
- `ingestion_ts`, `department`, `doc_category`
- `checksum`, `status`, `rejection_reason`

### **Extraction Outputs Table**
- `doc_id`, `chunk_id`, `extracted_text`
- `language`, `confidence_score`, `processing_ts`

### **Chunks Table**
- `chunk_id`, `doc_id`, `chunk_text`, `chunk_type`
- `semantic_boundary`, `overlap_score`, `metadata`
- `created_ts`, `updated_ts`

### **Embeddings Table**
- `embedding_id`, `chunk_id`, `vector_data`
- `model_version`, `dimensions`, `created_ts`
- `quality_score`, `language_code`

### **Users & Roles Table**
- `user_id`, `username`, `email`, `phone`
- `role_id`, `department`, `permissions`
- `created_ts`, `last_login`, `status`

### **Notifications Table**
- `notification_id`, `user_id`, `type`, `channel`
- `content`, `status`, `sent_ts`, `delivery_ts`
- `retry_count`, `error_message`

### **Chat Sessions Table**
- `session_id`, `user_id`, `query`, `response`
- `language`, `audio_path`, `created_ts`
- `feedback_score`, `context_ids`

### **OpenSearch Vector Schema**
```json
{
  "mappings": {
    "properties": {
      "chunk_id": {"type": "keyword"},
      "content": {"type": "text", "analyzer": "standard"},
      "embedding": {"type": "knn_vector", "dimension": 768},
      "metadata": {"type": "object"},
      "department": {"type": "keyword"},
      "language": {"type": "keyword"},
      "created_ts": {"type": "date"}
    }
  }
}
```

---

## 🚀 **Airflow DAGs**

### **Complete Document Processing Pipeline**
```
connectors → scan_and_store → queue_extraction → doc_processing_worker → 
data_preprocessing → smart_chunking → embedding_generation → 
vector_storage → notification_ready
```

### **Connector Pipeline**
```
gmail_connector → scan_and_store → push_to_queue
drive_connector → scan_and_store → push_to_queue
```

### **Processing Pipeline**
```
queue_extraction → doc_processing_worker → postgres (extraction_outputs)
```

### **Preprocessing & Chunking Pipeline**
```
extracted_content → text_normalization → language_detection → 
semantic_chunking → chunk_optimization → quality_validation
```

### **Embedding & Vector Pipeline**
```
chunks → vyakarth_embedding → vector_generation → 
opensearch_indexing → similarity_indexing → retrieval_ready
```

### **Query Processing Pipeline**
```
user_query → query_embedding → vector_search → context_ranking → 
gemini_generation → response_validation → notification_trigger
```

### **Notification Pipeline**
```
event_detection → user_preferences → sms_gateway → email_service → 
delivery_tracking → retry_mechanism
```

### **Role-Based Access Pipeline**
```
user_authentication → role_verification → permission_check → 
resource_access → audit_logging
```

---

## 🎯 **Hackathon Goals**

✅ **End-to-End Demo**: Gmail → MinIO → OCR → PostgreSQL → RAG Ready  
✅ **Multi-Format Support**: PDF, Images, Office, Text  
✅ **Language Detection**: English + Malayalam  
✅ **Scalable Architecture**: Queue-based processing  
✅ **Traceability**: Universal logging system  
✅ **Smart Chunking**: Chonkie + semantic strategies  
✅ **Advanced Embeddings**: Vyakarth multilingual model  
✅ **Hybrid Retrieval**: Semantic + keyword search  
✅ **AI Integration**: Gemini/OpenAI response generation  
✅ **Bilingual Support**: EN + Malayalam chat interface  
✅ **Audio Processing**: Voice input/output capabilities  
✅ **Notification System**: SMS + Email alerts  
✅ **Role-Based Access**: Secure permission management  

---

## 🔧 **Technology Stack**

### **Core Technologies**
- **Connectors**: Python, Google APIs, OAuth2, Requests
- **Processing**: PyMuPDF, Tesseract, OpenCV, PIL
- **Storage**: MinIO, PostgreSQL, OpenSearch
- **Queue**: Redis, Celery, RabbitMQ
- **Orchestration**: Apache Airflow, Kubernetes

### **AI & ML Stack**
- **Embeddings**: Vyakarth Model, Sentence Transformers
- **Language Models**: Gemini API, OpenAI GPT-4, HuggingFace
- **Chunking**: Chonkie, LangChain, spaCy
- **Vector Search**: OpenSearch KNN, Faiss, ChromaDB

### **Preprocessing & NLP**
- **Text Processing**: NLTK, spaCy, langdetect
- **OCR**: Tesseract, PaddleOCR, EasyOCR
- **Language Detection**: langdetect, fasttext
- **Normalization**: regex, unicodedata

### **User Interface**
- **Frontend**: React, Next.js, Tailwind CSS
- **Backend**: FastAPI, Flask, Django
- **Audio Processing**: WebRTC, SpeechRecognition, pyttsx3
- **Real-time**: WebSockets, Socket.io

### **Notifications & Integration**
- **SMS**: Twilio, AWS SNS, TextLocal
- **Email**: SendGrid, AWS SES, SMTP
- **Authentication**: JWT, OAuth2, LDAP
- **Monitoring**: Prometheus, Grafana, ELK Stack

### **Infrastructure**
- **Containerization**: Docker, Kubernetes
- **Cloud**: AWS, GCP, Azure
- **CI/CD**: GitHub Actions, Jenkins
- **Security**: Vault, KMS, SSL/TLS

---

## 📈 **Success Metrics**

### **Performance Metrics**
- **Processing Speed**: < 30 seconds per document
- **Accuracy**: > 95% text extraction
- **Throughput**: 100+ documents/hour
- **Uptime**: 99.9% availability
- **Query Response**: < 2 seconds average

### **Quality Metrics**
- **Embedding Quality**: > 90% semantic similarity
- **Chunking Efficiency**: < 5% information loss
- **Retrieval Precision**: > 85% relevant results
- **Multi-language**: English + Malayalam support
- **Audio Accuracy**: > 90% speech recognition

### **User Experience Metrics**
- **User Satisfaction**: > 4.5/5 rating
- **Response Relevance**: > 90% user approval
- **Notification Delivery**: > 98% success rate
- **Access Control**: Zero unauthorized access
- **System Reliability**: < 0.1% error rate

---

## 🔍 **Recommended Retrieval Technique for KMRL**

### **Hybrid Search Strategy**
**Combination of Semantic + Keyword + Contextual Retrieval**

#### **1. Semantic Vector Search (Primary)**
- **Vyakarth Embeddings** → 768-dimensional vectors
- **Cosine Similarity** → Vector distance calculation
- **Threshold**: 0.75+ similarity score
- **Language-Aware**: Separate indices for EN/Malayalam

#### **2. Keyword Search (Secondary)**
- **BM25 Algorithm** → Traditional keyword matching
- **Multi-field Search** → Title, content, metadata
- **Fuzzy Matching** → Typo tolerance for user queries
- **Boost Factors** → Recent docs, department relevance

#### **3. Contextual Retrieval (Enhancement)**
- **Department Filtering** → Role-based document access
- **Temporal Ranking** → Recent documents prioritized
- **Document Type Weighting** → Policy docs > general docs
- **User History** → Personalized relevance scoring

#### **4. Advanced Features**
- **Re-ranking Pipeline** → Cross-encoder for final ranking
- **Query Expansion** → Synonyms + related terms
- **Multi-modal Search** → Text + image content
- **Conversation Context** → Previous query context

#### **5. KMRL-Specific Optimizations**
- **Metro Terminology** → Domain-specific vocabulary
- **Safety Protocols** → High-priority content ranking
- **Maintenance Procedures** → Technical document boosting
- **Regulatory Compliance** → Official document prioritization

### **Implementation Architecture**
```
User Query → Query Preprocessing → Embedding Generation → 
Vector Search (OpenSearch) → Keyword Search (BM25) → 
Context Filtering → Re-ranking → Top-K Results
```

---

## 🚀 **Implementation Roadmap**

### **Phase 1: Foundation (Weeks 1-2)**
1. **Setup Infrastructure** (MinIO + PostgreSQL + Redis)
2. **Implement Connectors** (Gmail + Drive OAuth)
3. **Basic Document Processing** (OCR + Extraction)
4. **Airflow DAG Configuration** (Basic pipelines)

### **Phase 2: Intelligence Layer (Weeks 3-4)**
5. **Data Preprocessing Pipeline** (Normalization + Language Detection)
6. **Smart Chunking Implementation** (Chonkie + Semantic strategies)
7. **Vyakarth Embedding Integration** (Vector generation)
8. **OpenSearch Vector Database** (Indexing + Storage)

### **Phase 3: AI & Retrieval (Weeks 5-6)**
9. **Hybrid Search Implementation** (Semantic + Keyword)
10. **Gemini/OpenAI Integration** (Response generation)
11. **Query Processing Pipeline** (Embedding + Ranking)
12. **Context-Aware Retrieval** (Relevance scoring)

### **Phase 4: User Interface (Weeks 7-8)**
13. **Bilingual Chat Interface** (EN + Malayalam)
14. **Audio Processing** (Speech-to-text + Text-to-speech)
15. **Role-Based Access Control** (Authentication + Authorization)
16. **Frontend Development** (React + Real-time updates)

### **Phase 5: Notifications & Integration (Weeks 9-10)**
17. **Notification System** (SMS + Email integration)
18. **Event-Driven Architecture** (Smart triggers)
19. **Monitoring & Logging** (Performance tracking)
20. **Testing & Validation** (End-to-end pipeline)

### **Phase 6: Production Ready (Weeks 11-12)**
21. **Performance Optimization** (Caching + Load balancing)
22. **Security Hardening** (Encryption + Audit logs)
23. **Deployment & CI/CD** (Docker + Kubernetes)
24. **Go-Live & Support** (Production deployment)

---

*Ready for Kochi Metro's intelligent document processing! 🚇📄*
