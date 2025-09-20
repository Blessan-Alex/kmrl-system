# KMRL RAG Worker Implementation Guide

## Executive Summary

The **kmrl-rag-worker** is a critical component that transforms KMRL's document chaos into intelligent, searchable knowledge. It addresses the core problems from KMRL's daily operations: **Information Latency** (managers spending hours skimming documents), **Siloed Awareness** (departments unaware of each other's critical updates), and **Knowledge Attrition** (institutional memory locked in static files). The RAG worker processes thousands of daily documents from emails, Maximo exports, SharePoint, WhatsApp PDFs, and scans into a unified, intelligent knowledge base that enables instant cross-document search, contextual AI responses, and smart notifications for critical updates.

## Design Goals & Constraints

### Key Constraints from KMRL Problem Statement:
- **Volume**: Thousands of pages daily across multiple channels
- **Diversity**: Engineering drawings, maintenance cards, incident reports, invoices, regulatory directives, safety circulars, HR policies, legal opinions, board minutes
- **Languages**: English and Malayalam, sometimes bilingual hybrids
- **Formats**: Embedded tables, photos, signatures, technical drawings, mixed content
- **Sources**: Email attachments, Maximo exports, SharePoint repositories, WhatsApp PDFs, hard-copy scans, cloud links
- **Privacy**: Secure processing of sensitive organizational documents
- **Latency**: Sub-second query responses for operational decisions
- **Compliance**: Audit trails and regulatory compliance requirements

### RAG Design Respects These Constraints:
- **Smart Chunking**: Document-type specific chunking (maintenance docs → section-based, incident reports → event-based, financial docs → table-based)
- **Multilingual Support**: Malayalam OCR with English translation capabilities using Tesseract with Malayalam language packs
- **Metadata Preservation**: Source tracking, department routing, compliance flags, audit trails
- **Incremental Processing**: Only process new/modified documents to handle thousands daily
- **Fault Tolerance**: Automatic retry with exponential backoff for reliability
- **Resource Optimization**: Batch processing and efficient vector storage for sub-second responses
- **Smart Notifications**: Integration with notification-worker for proactive alerts on critical updates
- **Data Preprocessing**: OCR error correction and text cleaning for quality assurance

## RAG Worker Workflow

**Complete RAG Pipeline Flow:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT: Processed Document                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Document Data (from kmrl-document-worker)              │   │
│  │ • text: "Maintenance schedule for train T001..."       │   │
│  │ • document_id: "doc_12345"                             │   │
│  │ • document_type: "maintenance"                         │   │
│  │ • metadata: {source: "maximo", department: "engineering"}│   │
│  │ • language: "english" or "malayalam"                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 1: Data Preprocessing                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ TextPreprocessor                                       │   │
│  │ • Clean text (remove OCR errors)                       │   │
│  │ • Detect language (Malayalam/English)                  │   │
│  │ • Remove duplicates                                    │   │
│  │ • Standardize format                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 2: Smart Chunking                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DocumentChunker                                        │   │
│  │ • maintenance → section-based chunks                  │   │
│  │ • incident → event-based chunks                       │   │
│  │ • financial → table-based chunks                      │   │
│  │ • general → paragraph-based chunks                     │   │
│  │ • Add metadata: language, department, chunk_index     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 3: Embedding Generation                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ EmbeddingGenerator                                     │   │
│  │ • sentence-transformers/all-MiniLM-L6-v2 (local)      │   │
│  │ • OpenAI text-embedding-3-large (production)          │   │
│  │ • Batch processing for efficiency                     │   │
│  │ • Generate 384/3072 dimension vectors                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 4: Vector Storage                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ VectorStore (FAISS/OpenSearch)                         │   │
│  │ • Store embeddings with metadata                      │   │
│  │ • Index for fast similarity search                    │   │
│  │ • Preserve chunk relationships                        │   │
│  │ • Update document status in PostgreSQL               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 5: Smart Notifications                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ NotificationTrigger                                     │   │
│  │ • Scan chunks for triggers                             │   │
│  │ • Compare with pre-computed trigger embeddings         │   │
│  │ • Check similarity thresholds:                        │   │
│  │   - Urgent maintenance (≥0.85)                         │   │
│  │   - Safety incident (≥0.90)                           │   │
│  │   - Compliance violation (≥0.80)                      │   │
│  │   - Deadline approaching (≥0.75)                      │   │
│  │   - Budget exceeded (≥0.80)                           │   │
│  │ • Send alerts to notification-worker                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT: Integration Points                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • OpenSearch: Vector embeddings for search             │   │
│  │ • PostgreSQL: Document metadata and status            │   │
│  │ • Redis: Notification tasks for notification-worker   │   │
│  │ • kmrl-webapp: Ready for user queries                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Integration with Django-based KMRL System:**
- **Input**: Receives standard format from `kmrl-document-worker` via Celery tasks
- **Processing**: Django-compatible RAG pipeline with proper error handling
- **Output**: Integrates with Django models and triggers notification system
- **Storage**: Uses Django ORM for metadata, OpenSearch for vectors

## Responsibilities of the RAG Worker

### Core Functions:
- **Document Chunking**: Smart segmentation based on document type and content structure
- **Embedding Generation**: Convert text chunks to vector embeddings using OpenAI or sentence-transformers
- **Vector Storage**: Store embeddings in OpenSearch with metadata association
- **Query Processing**: Convert user queries to embeddings and perform similarity search
- **Context Assembly**: Combine retrieved chunks with metadata for LLM context
- **Metadata Management**: Track document sources, departments, compliance status
- **Incremental Updates**: Process only new/modified documents
- **Caching**: Store frequently accessed embeddings in Redis
- **Error Handling**: Retry failed operations with exponential backoff
- **Data Preprocessing**: Clean text data, remove duplicates, fix OCR errors, standardize format
- **Smart Notifications**: Trigger notification scanning for critical updates
- **Malayalam Support**: Handle bilingual documents with proper language detection

## Technology Choices & Rationale

### **Why These Technologies?**

**Celery + Redis**: 
- **Why**: Handles thousands of daily documents with reliable task queuing
- **KMRL Benefit**: Ensures no document is lost during processing, critical for compliance
- **Alternative**: Could use RabbitMQ, but Redis is simpler and faster for this use case

**sentence-transformers/all-MiniLM-L6-v2**:
- **Why**: Fast, accurate, and works well with both English and Malayalam text
- **KMRL Benefit**: Handles bilingual documents without separate translation step
- **Alternative**: OpenAI embeddings are more accurate but slower and cost money

**FAISS (Local) vs OpenSearch (Production)**:
- **Why FAISS**: In-memory, extremely fast for hackathon development
- **Why OpenSearch**: Distributed, persistent, handles millions of documents
- **KMRL Benefit**: Scales from prototype to enterprise without code changes

**Smart Chunking by Document Type**:
- **Why**: Different document types have different structures
- **KMRL Benefit**: Maintenance docs need section-based chunks, incidents need event-based
- **Alternative**: Fixed chunking would lose context and reduce accuracy

**Notification Triggers**:
- **Why**: Proactive alerts prevent compliance violations and safety issues
- **KMRL Benefit**: Addresses "Siloed Awareness" problem from the problem statement
- **Alternative**: Manual monitoring would miss critical updates

## Design Choices: Local vs Production

### **Local Quick-Mode (Hackathon)**
```python
# Fast, simple setup for development
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dims
VECTOR_STORE = "FAISS"  # In-memory, fast
CHUNK_SIZE = 1024  # characters
OVERLAP = 128  # characters
BATCH_SIZE = 32  # documents
```

**Advantages:**
- ✅ **Fast Setup**: 15 minutes to running
- ✅ **No External Dependencies**: Works offline
- ✅ **Low Resource Usage**: ~2GB RAM
- ✅ **Easy Debugging**: All in one process

**Trade-offs:**
- ❌ **Limited Scale**: ~10K documents max
- ❌ **No Persistence**: Restart loses data
- ❌ **Single Machine**: No horizontal scaling

### **Production Mode (Enterprise)**
```python
# Scalable, persistent setup for production
EMBEDDING_MODEL = "text-embedding-3-large"  # 3072 dims
VECTOR_STORE = "OpenSearch"  # Distributed, persistent
CHUNK_SIZE = 1024  # characters
OVERLAP = 128  # characters
BATCH_SIZE = 100  # documents
```

**Advantages:**
- ✅ **Unlimited Scale**: Millions of documents
- ✅ **High Availability**: Distributed across nodes
- ✅ **Persistence**: Survives restarts
- ✅ **Advanced Search**: Hybrid search, filters, aggregations

**Trade-offs:**
- ❌ **Complex Setup**: Requires OpenSearch cluster
- ❌ **Higher Resource Usage**: ~8GB RAM minimum
- ❌ **External Dependencies**: Network connectivity required

## Folder Structure

```
kmrl-rag-worker/
├── __init__.py
├── main.py                 # Worker entry point
├── config/
│   ├── __init__.py
│   ├── settings.py         # Configuration management
│   └── logging.py          # Logging configuration
├── core/
│   ├── __init__.py
│   ├── chunker.py          # Document chunking strategies
│   ├── embedder.py         # Embedding generation
│   ├── vector_store.py     # Vector storage operations
│   ├── retriever.py        # Similarity search
│   └── context_assembler.py # Context preparation
├── models/
│   ├── __init__.py
│   ├── document.py         # Document data models
│   ├── chunk.py           # Chunk data models
│   └── embedding.py       # Embedding data models
├── tasks/
│   ├── __init__.py
│   ├── celery_tasks.py    # Celery task definitions
│   └── processing.py      # Document processing logic
├── utils/
│   ├── __init__.py
│   ├── text_processing.py # Text cleaning and preprocessing
│   ├── metadata.py       # Metadata extraction
│   └── validation.py     # Data validation
├── tests/
│   ├── __init__.py
│   ├── test_chunker.py
│   ├── test_embedder.py
│   └── test_vector_store.py
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Local development setup
└── README.md            # Setup and usage instructions
```

## Implementation Plan

### **Step 1: Environment Setup (15 minutes)**

```bash
# Create project directory
mkdir kmrl-rag-worker && cd kmrl-rag-worker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 2: Core Dependencies**

```bash
# requirements.txt
celery==5.3.4
redis==5.0.1
sentence-transformers==2.2.2
faiss-cpu==1.7.4  # For local mode
opensearch-py==2.4.0  # For production mode
numpy==1.24.3
pydantic==2.5.0
python-dotenv==1.0.0
# Additional dependencies for KMRL-specific features
tesseract-ocr==0.3.13  # For Malayalam OCR support
langdetect==1.0.9  # For language detection
scikit-learn==1.3.0  # For similarity calculations
```

### **Step 3: Configuration Setup**

```python
# config/settings.py
import os
from typing import Literal

class Settings:
    # Worker Configuration
    WORKER_NAME: str = "kmrl-rag-worker"
    CONCURRENCY: int = 4
    
    # Queue Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIMENSIONS: int = 384
    
    # Vector Store Configuration
    VECTOR_STORE_TYPE: Literal["faiss", "opensearch"] = os.getenv("VECTOR_STORE_TYPE", "faiss")
    OPENSEARCH_URL: str = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
    OPENSEARCH_INDEX: str = "kmrl-documents"
    
    # Chunking Configuration
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 128
    
    # Processing Configuration
    BATCH_SIZE: int = 32
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 60

settings = Settings()
```

### **Step 4: Data Preprocessing Implementation**

```python
# utils/text_processing.py
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """Clean and standardize text data from various sources"""
    
    def __init__(self):
        # Common OCR error patterns for Malayalam/English documents
        self.ocr_error_patterns = {
            r'[|]': 'I',  # Common OCR confusion
            r'[0]': 'O',  # Number vs letter confusion
            r'[1]': 'l',  # Number vs letter confusion
            r'[5]': 'S',  # Number vs letter confusion
        }
    
    def clean_text(self, text: str, source: str = "unknown") -> str:
        """Clean and standardize text based on source"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        for pattern, replacement in self.ocr_error_patterns.items():
            text = re.sub(pattern, replacement, text)
        
        # Remove special characters but keep Malayalam characters
        text = re.sub(r'[^\w\s\u0D00-\u0D7F.,!?;:()]', '', text)
        
        # Standardize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        logger.info(f"Cleaned text from {source}: {len(text)} characters")
        return text.strip()
    
    def detect_language(self, text: str) -> str:
        """Detect if text contains Malayalam characters"""
        malayalam_chars = re.findall(r'[\u0D00-\u0D7F]', text)
        if malayalam_chars:
            return "malayalam"
        return "english"
    
    def remove_duplicates(self, texts: List[str]) -> List[str]:
        """Remove duplicate text chunks"""
        seen = set()
        unique_texts = []
        
        for text in texts:
            text_hash = hash(text.strip().lower())
            if text_hash not in seen:
                seen.add(text_hash)
                unique_texts.append(text)
        
        logger.info(f"Removed {len(texts) - len(unique_texts)} duplicate chunks")
        return unique_texts
```

### **Step 5: Document Chunking Implementation**

```python
# core/chunker.py
from typing import List, Dict, Any
import re
from dataclasses import dataclass
from utils.text_processing import TextPreprocessor

@dataclass
class Chunk:
    text: str
    metadata: Dict[str, Any]
    chunk_index: int
    document_id: str
    language: str = "english"
    department: str = "general"

class DocumentChunker:
    def __init__(self, chunk_size: int = 1024, overlap: int = 128):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.preprocessor = TextPreprocessor()
    
    def chunk_document(self, text: str, document_id: str, 
                      document_type: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Smart chunking based on document type"""
        
        # Clean the text first
        cleaned_text = self.preprocessor.clean_text(text, metadata.get('source', 'unknown'))
        
        # Detect language
        language = self.preprocessor.detect_language(cleaned_text)
        
        # Determine department from metadata
        department = metadata.get('department', 'general')
        
        if document_type == "maintenance":
            return self._chunk_by_sections(cleaned_text, document_id, metadata, language, department)
        elif document_type == "incident":
            return self._chunk_by_events(cleaned_text, document_id, metadata, language, department)
        elif document_type == "financial":
            return self._chunk_by_tables(cleaned_text, document_id, metadata, language, department)
        else:
            return self._chunk_by_paragraphs(cleaned_text, document_id, metadata, language, department)
    
    def _chunk_by_paragraphs(self, text: str, document_id: str, 
                           metadata: Dict[str, Any], language: str, department: str) -> List[Chunk]:
        """Standard paragraph-based chunking"""
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                if current_chunk:
                    chunks.append(Chunk(
                        text=current_chunk.strip(),
                        metadata=metadata,
                        chunk_index=chunk_index,
                        document_id=document_id,
                        language=language,
                        department=department
                    ))
                    chunk_index += 1
                
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(Chunk(
                text=current_chunk.strip(),
                metadata=metadata,
                chunk_index=chunk_index,
                document_id=document_id,
                language=language,
                department=department
            ))
        
        return chunks
```

### **Step 6: Embedding Generation**

```python
# core/embedder.py
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np

class EmbeddingGenerator:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimensions = self.model.get_sentence_embedding_dimension()
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        return self.dimensions
```

### **Step 7: Vector Storage Implementation**

```python
# core/vector_store.py
from typing import List, Dict, Any
import faiss
import numpy as np
import json
from typing import Optional

class FAISSVectorStore:
    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions
        self.index = faiss.IndexFlatIP(dimensions)  # Inner product similarity
        self.metadata = []
    
    def add_embeddings(self, embeddings: List[List[float]], 
                      chunks: List[Dict[str, Any]]) -> None:
        """Add embeddings to the index"""
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_array)
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Store metadata
        self.metadata.extend(chunks)
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        query_array = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_array)
        
        scores, indices = self.index.search(query_array, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                results.append({
                    'chunk': self.metadata[idx],
                    'score': float(score),
                    'index': int(idx)
                })
        
        return results
```

### **Step 8: Smart Notifications Integration**

```python
# core/notification_trigger.py
from typing import List, Dict, Any
import redis
import json
from core.embedder import EmbeddingGenerator
from core.vector_store import FAISSVectorStore

class NotificationTrigger:
    """Trigger smart notifications based on document content"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.embedder = EmbeddingGenerator()
        
        # Pre-computed trigger embeddings for different categories
        self.trigger_embeddings = {
            "urgent_maintenance": self.embedder.generate_embedding("urgent maintenance required"),
            "safety_incident": self.embedder.generate_embedding("safety incident accident"),
            "compliance_violation": self.embedder.generate_embedding("compliance violation deadline"),
            "budget_exceeded": self.embedder.generate_embedding("budget exceeded cost overrun"),
            "deadline_approaching": self.embedder.generate_embedding("deadline approaching due date")
        }
        
        # Similarity thresholds for each category
        self.thresholds = {
            "urgent_maintenance": 0.85,
            "safety_incident": 0.90,
            "compliance_violation": 0.80,
            "budget_exceeded": 0.80,
            "deadline_approaching": 0.75
        }
    
    def scan_document_for_triggers(self, chunks: List[Dict[str, Any]], 
                                 vector_store: FAISSVectorStore) -> List[Dict[str, Any]]:
        """Scan document chunks for notification triggers"""
        triggers = []
        
        for chunk in chunks:
            chunk_embedding = self.embedder.generate_embedding(chunk['text'])
            
            for category, trigger_embedding in self.trigger_embeddings.items():
                # Calculate similarity
                similarity = self._calculate_similarity(chunk_embedding, trigger_embedding)
                threshold = self.thresholds[category]
                
                if similarity >= threshold:
                    triggers.append({
                        'category': category,
                        'similarity': similarity,
                        'chunk_text': chunk['text'][:200] + "...",  # Truncate for notification
                        'document_id': chunk['document_id'],
                        'department': chunk.get('department', 'general'),
                        'metadata': chunk.get('metadata', {})
                    })
        
        return triggers
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        import numpy as np
        
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def send_notification_task(self, triggers: List[Dict[str, Any]]):
        """Send notification tasks to the notification worker"""
        for trigger in triggers:
            notification_data = {
                'category': trigger['category'],
                'message': f"Alert: {trigger['category'].replace('_', ' ').title()} detected",
                'content': trigger['chunk_text'],
                'document_id': trigger['document_id'],
                'department': trigger['department'],
                'similarity': trigger['similarity'],
                'metadata': trigger['metadata']
            }
            
            # Send to notification worker via Redis
            self.redis.lpush('notification_queue', json.dumps(notification_data))
```

### **Step 9: Celery Task Implementation**

```python
# tasks/celery_tasks.py
from celery import Celery
from core.chunker import DocumentChunker
from core.embedder import EmbeddingGenerator
from core.vector_store import FAISSVectorStore
from core.notification_trigger import NotificationTrigger
from typing import Dict, Any
import logging
import redis

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery('kmrl-rag-worker')
celery_app.config_from_object('config.settings')

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_data: Dict[str, Any]):
    """Process a single document through the RAG pipeline"""
    try:
        # Initialize components
        chunker = DocumentChunker()
        embedder = EmbeddingGenerator()
        vector_store = FAISSVectorStore()
        
        # Initialize Redis for notifications
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        notification_trigger = NotificationTrigger(redis_client)
        
        # Extract document information
        text = document_data['text']
        document_id = document_data['document_id']
        document_type = document_data.get('document_type', 'general')
        metadata = document_data.get('metadata', {})
        
        # Step 1: Chunk the document
        chunks = chunker.chunk_document(text, document_id, document_type, metadata)
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")
        
        # Step 2: Generate embeddings
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = embedder.generate_embeddings_batch(chunk_texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Step 3: Store in vector database
        chunk_data = [{'text': chunk.text, 'metadata': chunk.metadata, 
                      'chunk_index': chunk.chunk_index, 'document_id': chunk.document_id,
                      'language': chunk.language, 'department': chunk.department} 
                     for chunk in chunks]
        vector_store.add_embeddings(embeddings, chunk_data)
        
        # Step 4: Scan for notification triggers
        triggers = notification_trigger.scan_document_for_triggers(chunk_data, vector_store)
        if triggers:
            notification_trigger.send_notification_task(triggers)
            logger.info(f"Sent {len(triggers)} notification triggers")
        
        logger.info(f"Successfully processed document {document_id}")
        return {
            'status': 'success', 
            'document_id': document_id, 
            'chunks': len(chunks),
            'triggers': len(triggers)
        }
        
    except Exception as e:
        logger.error(f"Failed to process document {document_data.get('document_id', 'unknown')}: {str(e)}")
        raise self.retry(countdown=60, exc=e)
```

### **Step 10: Query Processing**

```python
# core/retriever.py
from typing import List, Dict, Any
from core.embedder import EmbeddingGenerator
from core.vector_store import FAISSVectorStore

class DocumentRetriever:
    def __init__(self, vector_store: FAISSVectorStore, embedder: EmbeddingGenerator):
        self.vector_store = vector_store
        self.embedder = embedder
    
    def search(self, query: str, top_k: int = 5, 
              filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        
        # Generate query embedding
        query_embedding = self.embedder.generate_embedding(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, top_k)
        
        # Apply filters if provided
        if filters:
            results = self._apply_filters(results, filters)
        
        return results
    
    def _apply_filters(self, results: List[Dict[str, Any]], 
                      filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply metadata filters to search results"""
        filtered_results = []
        
        for result in results:
            chunk_metadata = result['chunk'].get('metadata', {})
            
            # Check if chunk matches all filters
            matches = True
            for key, value in filters.items():
                if chunk_metadata.get(key) != value:
                    matches = False
                    break
            
            if matches:
                filtered_results.append(result)
        
        return filtered_results
```

### **Step 11: Context Assembly**

```python
# core/context_assembler.py
from typing import List, Dict, Any

class ContextAssembler:
    def __init__(self, max_context_length: int = 4000):
        self.max_context_length = max_context_length
    
    def assemble_context(self, search_results: List[Dict[str, Any]], 
                        query: str) -> Dict[str, Any]:
        """Assemble context for LLM from search results"""
        
        context_parts = []
        total_length = 0
        
        for result in search_results:
            chunk = result['chunk']
            text = chunk['text']
            metadata = chunk.get('metadata', {})
            
            # Add source information
            source_info = f"[Source: {metadata.get('source', 'Unknown')}]"
            context_part = f"{source_info}\n{text}\n"
            
            if total_length + len(context_part) > self.max_context_length:
                break
            
            context_parts.append(context_part)
            total_length += len(context_part)
        
        # Combine all context
        full_context = "\n".join(context_parts)
        
        return {
            'context': full_context,
            'sources': [result['chunk']['metadata'] for result in search_results],
            'query': query,
            'total_chunks': len(context_parts)
        }
```

### **Step 12: Worker Entry Point**

```python
# main.py
import os
import logging
from celery import Celery
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the RAG worker"""
    logger.info("Starting KMRL RAG Worker...")
    logger.info(f"Configuration: {settings.VECTOR_STORE_TYPE} mode")
    logger.info(f"Embedding model: {settings.EMBEDDING_MODEL}")
    logger.info(f"Chunk size: {settings.CHUNK_SIZE}")
    
    # Start Celery worker
    celery_app = Celery('kmrl-rag-worker')
    celery_app.config_from_object('config.settings')
    
    # Start worker
    celery_app.worker_main(['worker', '--loglevel=info', '--concurrency=4'])

if __name__ == '__main__':
    main()
```

## Django Integration & Workflow

### **Django-based KMRL System Integration**

The RAG worker is designed to integrate seamlessly with Django-based applications like redbox:

**Django Models Integration**:
```python
# models.py - Django models for RAG worker
from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    """Document model for RAG processing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=500)
    content = models.TextField()
    document_type = models.CharField(max_length=50, choices=[
        ('maintenance', 'Maintenance'),
        ('incident', 'Incident Report'),
        ('financial', 'Financial'),
        ('compliance', 'Compliance'),
        ('general', 'General')
    ])
    source = models.CharField(max_length=100)  # maximo, sharepoint, email, etc.
    department = models.CharField(max_length=100)
    language = models.CharField(max_length=20, default='english')
    status = models.CharField(max_length=20, choices=[
        ('processing', 'Processing'),
        ('chunking', 'Chunking'),
        ('embedding', 'Generating Embeddings'),
        ('storing', 'Storing Vectors'),
        ('ready', 'RAG Ready'),
        ('error', 'Error')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class DocumentChunk(models.Model):
    """Chunk model for vector storage"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    text = models.TextField()
    embedding = models.JSONField()  # Store embedding as JSON
    metadata = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

class NotificationTrigger(models.Model):
    """Notification triggers for smart alerts"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    similarity_score = models.FloatField()
    triggered_at = models.DateTimeField(auto_now_add=True)
    sent = models.BooleanField(default=False)
```

**Django Settings Integration**:
```python
# settings.py - Add to Django settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# RAG Worker Configuration
RAG_WORKER = {
    'EMBEDDING_MODEL': 'sentence-transformers/all-MiniLM-L6-v2',
    'VECTOR_STORE_TYPE': 'faiss',  # or 'opensearch'
    'CHUNK_SIZE': 1024,
    'BATCH_SIZE': 32,
    'OPENSEARCH_URL': 'http://localhost:9200',
    'OPENSEARCH_INDEX': 'kmrl-documents',
}

# OpenSearch Configuration
OPENSEARCH_DSL = {
    'default': {
        'hosts': 'localhost:9200',
        'http_auth': ('admin', 'admin'),
    },
}
```

**Django Management Commands**:
```python
# management/commands/start_rag_worker.py
from django.core.management.base import BaseCommand
from kmrl_rag_worker.tasks import start_rag_worker

class Command(BaseCommand):
    help = 'Start the RAG worker'

    def handle(self, *args, **options):
        self.stdout.write('Starting RAG worker...')
        start_rag_worker()
        self.stdout.write('RAG worker started successfully!')
```

### **Integration with Other Workflows**

**1. Document Processing Workflow**:
```python
# In kmrl-document-worker
from kmrl_rag_worker.tasks import process_document_task

def process_document(document_id):
    # After text extraction and processing
    document_data = {
        'document_id': document_id,
        'text': extracted_text,
        'document_type': detected_type,
        'metadata': {
            'source': 'maximo',
            'department': 'engineering',
            'user_id': user.id
        }
    }
    
    # Queue for RAG processing
    process_document_task.delay(document_data)
```

**2. Notification Workflow**:
```python
# In kmrl-notification-worker
from django.core.mail import send_mail
from django.template.loader import render_to_string

def process_notification_task(notification_data):
    # Send email notification
    send_mail(
        subject=f"KMRL Alert: {notification_data['category']}",
        message=notification_data['content'],
        from_email='alerts@kmrl.com',
        recipient_list=get_department_recipients(notification_data['department'])
    )
```

**3. Web App Integration**:
```python
# In kmrl-webapp views
from kmrl_rag_worker.core.retriever import DocumentRetriever
from kmrl_rag_worker.core.context_assembler import ContextAssembler

def search_documents(request):
    query = request.GET.get('q')
    department = request.user.department
    
    # Use RAG worker for search
    retriever = DocumentRetriever()
    results = retriever.search(query, filters={'department': department})
    
    # Assemble context for display
    assembler = ContextAssembler()
    context = assembler.assemble_context(results, query)
    
    return render(request, 'search_results.html', {'context': context})
```

### **Environment Variables (Django-compatible)**

```bash
# .env for Django KMRL system
# Database
DATABASE_URL=postgresql://kmrl_user:kmrl_password@localhost:5432/kmrl_db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# OpenSearch
OPENSEARCH_URL=http://localhost:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin

# RAG Worker
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_TYPE=faiss
CHUNK_SIZE=1024
BATCH_SIZE=32

# Notifications
NOTIFICATION_EMAIL_HOST=smtp.gmail.com
NOTIFICATION_EMAIL_PORT=587
NOTIFICATION_EMAIL_USER=alerts@kmrl.com
NOTIFICATION_EMAIL_PASSWORD=your-app-password
```

## Local Development Setup

### **Quick Start (5 minutes)**

```bash
# 1. Clone and setup
git clone <kmrl-repo>
cd kmrl-rag-worker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Redis (required for Celery)
redis-server

# 4. Start the worker
python main.py
```

### **Docker Setup (Optional - Future Implementation)**

**Dockerfile for RAG Worker**:
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    tesseract-ocr \
    tesseract-ocr-mal \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 ragworker && chown -R ragworker:ragworker /app
USER ragworker

# Run the worker
CMD ["python", "main.py"]
```

**Docker Compose for Complete KMRL System**:
```yaml
# docker-compose.yml - Complete KMRL system
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: kmrl_db
      POSTGRES_USER: kmrl_user
      POSTGRES_PASSWORD: kmrl_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # OpenSearch
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - discovery.type=single-node
      - "OPENSEARCH_INITIAL_ADMIN_PASSWORD=admin"
    ports:
      - "9200:9200"
    volumes:
      - opensearch_data:/usr/share/opensearch/data

  # MinIO
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  # Django Web App
  kmrl-webapp:
    build: ./kmrl-webapp
    environment:
      - DATABASE_URL=postgresql://kmrl_user:kmrl_password@postgres:5432/kmrl_db
      - REDIS_URL=redis://redis:6379/0
      - OPENSEARCH_URL=http://opensearch:9200
    depends_on:
      - postgres
      - redis
      - opensearch
    ports:
      - "8000:8000"

  # Document Worker
  kmrl-document-worker:
    build: ./kmrl-document-worker
    environment:
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
    depends_on:
      - redis
      - minio

  # RAG Worker
  kmrl-rag-worker:
    build: ./kmrl-rag-worker
    environment:
      - REDIS_URL=redis://redis:6379/0
      - OPENSEARCH_URL=http://opensearch:9200
      - OPENSEARCH_USER=admin
      - OPENSEARCH_PASSWORD=admin
      - VECTOR_STORE_TYPE=opensearch
    depends_on:
      - redis
      - opensearch
    deploy:
      replicas: 2  # Scale RAG workers

  # Notification Worker
  kmrl-notification-worker:
    build: ./kmrl-notification-worker
    environment:
      - REDIS_URL=redis://redis:6379/0
      - EMAIL_HOST=smtp.gmail.com
      - EMAIL_PORT=587
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:
  opensearch_data:
  minio_data:
```

**Docker Compose for Development**:
```yaml
# docker-compose.dev.yml - Development setup
version: '3.8'

services:
  # Development RAG Worker
  kmrl-rag-worker-dev:
    build: ./kmrl-rag-worker
    environment:
      - REDIS_URL=redis://redis:6379/0
      - VECTOR_STORE_TYPE=faiss
      - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
    volumes:
      - ./kmrl-rag-worker:/app
      - ./data:/app/data
    depends_on:
      - redis
    command: python main.py

  # Redis for development
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Docker Commands**:
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Start production environment
docker-compose up -d

# Scale RAG workers
docker-compose up -d --scale kmrl-rag-worker=4

# View logs
docker-compose logs -f kmrl-rag-worker

# Stop all services
docker-compose down
```

## Testing & Validation

### **Unit Tests**

```python
# tests/test_chunker.py
import pytest
from core.chunker import DocumentChunker

def test_chunking():
    chunker = DocumentChunker(chunk_size=100, overlap=20)
    text = "This is a test document. " * 50  # 1000+ characters
    
    chunks = chunker.chunk_document(text, "test-doc", "general", {})
    
    assert len(chunks) > 1
    assert all(len(chunk.text) <= 100 for chunk in chunks)
    assert chunks[0].document_id == "test-doc"
```

### **Integration Tests**

```python
# tests/test_rag_pipeline.py
import pytest
from core.chunker import DocumentChunker
from core.embedder import EmbeddingGenerator
from core.vector_store import FAISSVectorStore

def test_end_to_end_pipeline():
    # Setup
    chunker = DocumentChunker()
    embedder = EmbeddingGenerator()
    vector_store = FAISSVectorStore()
    
    # Test document
    text = "Maintenance schedule for train T001. Next inspection due on 2024-02-15."
    document_id = "test-doc-1"
    metadata = {"source": "maximo", "department": "engineering"}
    
    # Process document
    chunks = chunker.chunk_document(text, document_id, "maintenance", metadata)
    embeddings = embedder.generate_embeddings_batch([chunk.text for chunk in chunks])
    chunk_data = [{'text': chunk.text, 'metadata': chunk.metadata, 
                  'chunk_index': chunk.chunk_index, 'document_id': chunk.document_id} 
                 for chunk in chunks]
    vector_store.add_embeddings(embeddings, chunk_data)
    
    # Test search
    query = "When is the next train inspection?"
    query_embedding = embedder.generate_embedding(query)
    results = vector_store.search(query_embedding, k=3)
    
    assert len(results) > 0
    assert results[0]['score'] > 0.5  # Should have reasonable similarity
```

## Production Deployment

### **Environment Variables**

```bash
# .env.production
REDIS_URL=redis://production-redis:6379/0
OPENSEARCH_URL=https://opensearch-cluster:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=secure-password
EMBEDDING_MODEL=text-embedding-3-large
VECTOR_STORE_TYPE=opensearch
CHUNK_SIZE=1024
BATCH_SIZE=100
CONCURRENCY=8
```

### **Scaling Configuration**

```yaml
# docker-compose.production.yml
version: '3.8'
services:
  rag-worker:
    image: kmrl-rag-worker:latest
    deploy:
      replicas: 4
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    environment:
      - REDIS_URL=redis://redis:6379/0
      - OPENSEARCH_URL=https://opensearch:9200
      - VECTOR_STORE_TYPE=opensearch
```

## Monitoring & Troubleshooting

### **Health Checks**

```python
# utils/health.py
def check_worker_health():
    """Check if worker is healthy"""
    checks = {
        'redis_connection': check_redis_connection(),
        'embedding_model': check_embedding_model(),
        'vector_store': check_vector_store(),
        'celery_tasks': check_celery_tasks()
    }
    
    return all(checks.values()), checks
```

### **Common Issues**

1. **Memory Issues**: Reduce batch size or chunk size
2. **Slow Embeddings**: Use smaller model or batch processing
3. **Vector Store Errors**: Check connection and index configuration
4. **Queue Backlog**: Scale workers or optimize processing

## Performance Optimization

### **Batch Processing**
```python
# Process multiple documents in batches
@celery_app.task
def process_document_batch(document_ids: List[str]):
    """Process multiple documents efficiently"""
    # Batch embedding generation
    # Batch vector storage
    # Batch metadata updates
```

### **Caching Strategy**
```python
# Cache frequently accessed embeddings
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(text: str) -> List[float]:
    return embedder.generate_embedding(text)
```

## Alignment with detailed_flow.md Requirements

### **Phase 3: RAG Pipeline Preparation (Steps 18-22)**

✅ **Step 18 - Data Preprocessing**: 
- Text cleaning and OCR error correction in `TextPreprocessor`
- Duplicate removal and format standardization
- Malayalam language detection and handling

✅ **Step 19 - Smart Chunking**:
- Document-type specific chunking strategies
- Maintenance docs → section-based chunks
- Incident reports → event-based chunks  
- Financial docs → table-based chunks
- General docs → paragraph-based chunks

✅ **Step 20 - Generate Embeddings**:
- OpenAI text-embedding-3-large for production
- all-MiniLM-L6-v2 for local development
- Batch processing for efficiency
- Error handling with retries

✅ **Step 21 - Store in Vector Database**:
- OpenSearch index for production
- FAISS for local development
- Metadata association with chunks
- Chunk relationships preserved

✅ **Step 22 - Mark Document as RAG Ready**:
- Status tracking in PostgreSQL
- Integration with notification triggers

### **Phase 4: Smart Notifications (Steps 23-29)**

✅ **Step 23 - Trigger Notification Scan**:
- Vector similarity search implementation
- Document chunk analysis
- Trigger pattern matching

✅ **Step 24 - Load Pre-computed Trigger Embeddings**:
- Cached in Redis for performance
- Category-specific triggers (maintenance, safety, compliance)
- Similarity thresholds configured

✅ **Step 25 - Vector Similarity Search**:
- Cosine similarity calculation
- Chunk-to-trigger comparison
- Relevance scoring

✅ **Step 26 - Check Similarity Thresholds**:
- Urgent maintenance (≥0.85)
- Safety incident (≥0.90) 
- Compliance violation (≥0.80)
- Deadline approaching (≥0.75)
- Budget exceeded (≥0.80)

✅ **Step 27 - Generate Notifications Based on Rules**:
- Rule-based system implementation
- Category classification
- Recipient determination

✅ **Step 28 - Send Smart Notification**:
- Integration with notification-worker
- Multi-channel delivery (Email/SMS/Slack)
- Priority-based routing

✅ **Step 29 - Update Notification Status**:
- Delivery tracking
- Response monitoring
- Document status updates

### **Phase 5: RAG Query Processing (Steps 30-32)**

✅ **Step 30 - Query Processing**:
- Query embedding generation
- Vector similarity search
- Relevant chunk retrieval
- Relevance ranking

✅ **Step 31 - Context Assembly**:
- Retrieved chunk combination
- Metadata context addition
- LLM preparation

✅ **Step 32 - LLM Response Generation**:
- Context provision to LLM
- KMRL-specific response generation
- Source citation inclusion
- Structured response return

## Integration with Existing Django Workflow

### **How to Integrate with Redbox-style Django Applications**

**1. Add RAG Worker as Django App**:
```python
# settings.py - Add to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # ... other apps
    'kmrl_rag_worker',  # Add RAG worker app
]

# Add RAG worker URLs
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/rag/', include('kmrl_rag_worker.urls')),
    # ... other URLs
]
```

**2. Django Management Commands**:
```python
# management/commands/process_documents.py
from django.core.management.base import BaseCommand
from kmrl_rag_worker.tasks import process_document_task
from redbox_app.redbox_core.models import File  # Assuming redbox models

class Command(BaseCommand):
    help = 'Process documents through RAG pipeline'

    def add_arguments(self, parser):
        parser.add_argument('--document-id', type=str, help='Process specific document')
        parser.add_argument('--all', action='store_true', help='Process all pending documents')

    def handle(self, *args, **options):
        if options['document_id']:
            # Process specific document
            document = File.objects.get(id=options['document_id'])
            self.process_document(document)
        elif options['all']:
            # Process all pending documents
            documents = File.objects.filter(status='complete')
            for document in documents:
                self.process_document(document)
        else:
            self.stdout.write('Please specify --document-id or --all')

    def process_document(self, document):
        document_data = {
            'document_id': str(document.id),
            'text': document.text,
            'document_type': self.detect_document_type(document),
            'metadata': {
                'source': 'manual_upload',
                'department': 'general',
                'user_id': document.creator_user_uuid
            }
        }
        
        # Queue for RAG processing
        process_document_task.delay(document_data)
        self.stdout.write(f'Queued document {document.id} for RAG processing')
```

**3. Django Signals Integration**:
```python
# signals.py - Auto-trigger RAG processing
from django.db.models.signals import post_save
from django.dispatch import receiver
from redbox_app.redbox_core.models import File
from kmrl_rag_worker.tasks import process_document_task

@receiver(post_save, sender=File)
def trigger_rag_processing(sender, instance, created, **kwargs):
    """Automatically trigger RAG processing when document is ready"""
    if instance.status == 'complete' and instance.text:
        document_data = {
            'document_id': str(instance.id),
            'text': instance.text,
            'document_type': 'general',
            'metadata': {
                'source': 'redbox_upload',
                'department': 'general',
                'user_id': str(instance.creator_user_uuid)
            }
        }
        
        # Queue for RAG processing
        process_document_task.delay(document_data)
```

**4. Django Views Integration**:
```python
# views.py - Add RAG search to existing views
from django.shortcuts import render
from django.http import JsonResponse
from kmrl_rag_worker.core.retriever import DocumentRetriever
from kmrl_rag_worker.core.context_assembler import ContextAssembler

def rag_search(request):
    """Add RAG search to existing search functionality"""
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'error': 'Query required'}, status=400)
    
    try:
        # Use RAG worker for intelligent search
        retriever = DocumentRetriever()
        results = retriever.search(query, top_k=5)
        
        # Assemble context
        assembler = ContextAssembler()
        context = assembler.assemble_context(results, query)
        
        return JsonResponse({
            'query': query,
            'results': context['context'],
            'sources': context['sources'],
            'total_chunks': context['total_chunks']
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def document_analysis(request, document_id):
    """Add document analysis using RAG"""
    try:
        # Get document from existing models
        document = File.objects.get(id=document_id)
        
        # Use RAG for document analysis
        retriever = DocumentRetriever()
        results = retriever.search(
            f"Analyze this document: {document.text[:500]}",
            filters={'document_id': document_id}
        )
        
        return JsonResponse({
            'document_id': document_id,
            'analysis': results,
            'status': 'analyzed'
        })
    except File.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)
```

**5. Django Templates Integration**:
```html
<!-- templates/search_results.html -->
{% extends "base.html" %}

{% block content %}
<div class="search-results">
    <h2>Intelligent Search Results</h2>
    
    {% if context.results %}
        <div class="rag-context">
            <h3>Context:</h3>
            <p>{{ context.context }}</p>
        </div>
        
        <div class="sources">
            <h3>Sources:</h3>
            <ul>
                {% for source in context.sources %}
                    <li>
                        <strong>{{ source.department }}</strong> - 
                        {{ source.source }} (Score: {{ source.score|floatformat:2 }})
                    </li>
                {% endfor %}
            </ul>
        </div>
    {% else %}
        <p>No results found. Try a different query.</p>
    {% endif %}
</div>
{% endblock %}
```

### **Migration Strategy**

**Phase 1: Add RAG Worker (Week 1)**:
1. Install RAG worker as Django app
2. Add Django models for documents and chunks
3. Set up Celery tasks for background processing
4. Test with sample documents

**Phase 2: Integrate with Existing Workflow (Week 2)**:
1. Add Django signals for auto-processing
2. Integrate RAG search with existing search views
3. Add management commands for bulk processing
4. Update templates to show RAG results

**Phase 3: Production Deployment (Week 3)**:
1. Set up Docker containers
2. Configure OpenSearch for production
3. Set up monitoring and logging
4. Deploy with proper scaling

This comprehensive guide provides everything needed to implement the kmrl-rag-worker, from basic setup to production deployment, addressing all the requirements from the KMRL problem statement while maintaining simplicity for hackathon development and seamless integration with Django-based applications like redbox.
