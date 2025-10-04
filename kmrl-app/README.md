# 🚇 KMRL Intelligent Document Management System

![KMRL System Architecture](kmrl-app/assets/diagram-export-10-4-2025-1_23_51-PM.png)

## Overview

The **KMRL Intelligent Document Management System** revolutionizes how Kochi Metro Rail Limited handles its vast repository of technical documents, maintenance records, and operational data. Built to address the critical challenges of document processing, multilingual content handling, and intelligent information retrieval in railway operations.

**Problem Solved**: KMRL faces massive document management challenges with thousands of technical drawings, maintenance reports, incident records, and financial documents scattered across multiple systems. The system provides intelligent document processing, multilingual OCR (including Malayalam), and AI-powered search capabilities to transform unstructured data into actionable insights.

## ⚡ Key Features

- **📄 Multi-Format Document Processing** - Handles PDFs, Office docs, CAD files, images, and technical drawings
- **🌐 Multilingual OCR** - Advanced OCR with Malayalam and English language support
- **🤖 AI-Powered RAG Pipeline** - Intelligent document chunking and vector-based search
- **📱 Modern Web Interface** - Responsive Next.js frontend with real-time chat capabilities
- **🔍 Smart Search & Analytics** - Context-aware document retrieval and trend analysis
- **📊 Department Dashboards** - Specialized views for Operations, Engineering, Finance, and HR
- **🔔 Intelligent Notifications** - Automated alerts for maintenance, safety incidents, and compliance
- **🔗 System Integration** - Connects with Maximo, email systems, and third-party APIs

## 📂 Project Structure

```
kmrl-app/
├── 🖥️ backend/                    # FastAPI backend services
│   ├── Document_Extraction/       # Core document processing engine
│   ├── rag/                       # RAG pipeline and embeddings
│   ├── Rag-Engine/               # Advanced query processing
│   ├── connectors/                # External system integrations
│   ├── gateway/                   # API gateway and routing
│   └── services/                  # Business logic services
├── 🎨 frontend/frnt-km/           # Next.js React frontend
│   ├── app/                       # Next.js app router pages
│   ├── components/                # Reusable UI components
│   └── hooks/                     # Custom React hooks
└── 📋 kmrl-plan/                 # Project documentation and planning
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI, Uvicorn
- **Database**: PostgreSQL, Redis
- **Task Queue**: Celery
- **Storage**: MinIO (S3-compatible)
- **Document Processing**: PyMuPDF, Tesseract OCR, OpenCV
- **AI/ML**: OpenAI Embeddings, Vector Search

### Frontend
- **Framework**: Next.js 15, React 19
- **Styling**: Tailwind CSS, Radix UI
- **State Management**: React Hooks, Context
- **Animations**: Framer Motion, GSAP
- **Authentication**: JWT, bcrypt

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Vector Database**: OpenSearch
- **Monitoring**: Prometheus, Structured Logging
- **Security**: JWT Authentication, Rate Limiting

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL
- Redis
- Docker (optional)

### Backend Setup
```bash
cd kmrl-app/backend
pip install -r requirements.txt

# Start services
python start_kmrl_system.py
```

### Frontend Setup
```bash
cd kmrl-app/frontend/frnt-km
npm install
npm run dev
```

### Quick Start with Docker
```bash
# Start all services
docker-compose up -d
```

## 🔧 Core Components

### Document Processing Pipeline
- **File Type Detection** - Automatic format identification
- **Quality Assessment** - Image enhancement and confidence scoring
- **Multilingual OCR** - Malayalam and English text extraction
- **Smart Chunking** - Context-aware document segmentation

### RAG Engine
- **Vector Embeddings** - OpenAI text-embedding-3-large
- **Similarity Search** - Cosine similarity with configurable thresholds
- **Context Assembly** - Intelligent chunk combination
- **LLM Integration** - GPT-powered response generation

### Smart Notifications
- **Trigger Detection** - Pattern matching for urgent maintenance
- **Multi-channel** - Email, SMS, Slack integration
- **Priority Routing** - Automated recipient determination

## 📊 System Architecture

The system follows a microservices architecture with:
- **API Gateway** for request routing and authentication
- **Document Processing Workers** for async file processing
- **RAG Pipeline** for intelligent search and retrieval
- **Notification Engine** for automated alerts
- **Analytics Dashboard** for insights and monitoring

## 🚧 Phase 2: Advanced Features (In Development)

### **Enhanced Document Processing**
- **🔧 Advanced OCR Pipeline** - Multi-engine OCR with Tesseract, PaddleOCR, and cloud fallbacks
- **📊 Smart Table Extraction** - Camelot/Tabula for vector PDFs, deep learning models for scanned tables
- **🎯 Technical Drawing Processing** - DWG/DXF conversion with ODA File Converter, metadata extraction
- **🌐 Bilingual Language Support** - Enhanced Malayalam OCR with specialized models and language detection

### **Production-Grade Connectors**
- **📧 Gmail Integration** - OAuth2 authentication, incremental sync, attachment processing
- **☁️ Google Drive Connector** - Real-time file monitoring, permission management
- **📱 WhatsApp Business API** - Message processing, media extraction, contact management
- **🏢 SharePoint Integration** - Document library sync, metadata preservation
- **🔧 Maximo Integration** - Work order documents, maintenance records sync

### **Advanced RAG Pipeline**
- **🧠 Smart Chunking** - Document-type aware chunking (maintenance docs, incident reports, financial data)
- **🔍 Vector Search Optimization** - OpenSearch integration with similarity thresholds
- **📈 Confidence Scoring** - Multi-level confidence assessment for OCR and extraction
- **🔄 Human-in-the-Loop** - Review interface for low-confidence documents

### **Monitoring & Analytics**
- **📊 Processing Metrics** - Real-time monitoring of document processing pipeline
- **🎯 Quality Analytics** - OCR accuracy tracking, processing success rates
- **📈 Usage Insights** - Document access patterns, search analytics
- **🔔 Smart Notifications** - Automated alerts for urgent maintenance, safety incidents

## 🤝 Contributors

Built for **Kochi Metro Rail Limited** to modernize document management and improve operational efficiency through AI-powered document processing and intelligent search capabilities.

---

**Ready to transform your document management?** 🚀
