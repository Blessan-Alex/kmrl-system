# KMRL Document Pipeline Visualization

## Enhanced Pipeline Flow Diagram

```mermaid
graph TB
    subgraph "Data Sources"
        A1[Email Server<br/>Gmail Connector]
        A2[SharePoint<br/>Repository]
        A3[Maximo<br/>Exports]
        A4[WhatsApp<br/>Business]
        A5[Manual Upload<br/>UI]
    end
    
    subgraph "Ingestion Layer"
        B1[Connector Layer<br/>Authentication]
        B2[API Gateway<br/>POST /api/v1/documents/upload]
        B3[File Validation<br/>Size, Type, Security]
    end
    
    subgraph "Storage Layer"
        C1[MinIO<br/>Original Files]
        C2[PostgreSQL<br/>Metadata & Users]
        C3[Redis<br/>Queues & Cache]
    end
    
    subgraph "Processing Layer"
        D1[File Type Detection<br/>PDF, Office, Images, CAD]
        D2[Quality Assessment<br/>Confidence Scoring]
        D3[Text Extraction<br/>Markitdown, OCR, CAD]
        D4[Language Detection<br/>English, Malayalam, Mixed]
    end
    
    subgraph "Enhanced Preprocessing"
        E1[Confidence Enhancement<br/>Low-confidence text improvement]
        E2[Language Processing<br/>Malayalam translation]
        E3[Document-Type Cleaning<br/>Maintenance, Incident, Financial]
        E4[KMRL Standardization<br/>Terminology, OCR fixes]
    end
    
    subgraph "Smart Chunking"
        F1[Document-Type Chunkers<br/>Specialized strategies]
        F2[Metadata Extraction<br/>Technical drawings]
        F3[Chunk Quality Validation<br/>Content verification]
    end
    
    subgraph "Embedding Generation"
        G1[Vector Generation<br/>OpenAI/All-MiniLM]
        G2[Batch Processing<br/>Optimized throughput]
        G3[OpenSearch Storage<br/>Vector database]
    end
    
    subgraph "Intelligence Layer"
        H1[Notification Scanner<br/>Vector similarity]
        H2[RAG Query Engine<br/>Context retrieval]
        H3[LLM Response Generator<br/>Gemini/OpenAI]
    end
    
    subgraph "User Interfaces"
        I1[Department Dashboards<br/>Role-based views]
        I2[Intelligent Search<br/>RAG-powered]
        I3[Chat Interface<br/>Conversational AI]
        I4[Mobile App<br/>Field workers]
    end
    
    %% Data Flow
    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    A5 --> B2
    
    B1 --> B2
    B2 --> B3
    B3 --> C1
    B3 --> C2
    B3 --> C3
    
    C3 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> D4
    
    D4 --> E1
    E1 --> E2
    E2 --> E3
    E3 --> E4
    
    E4 --> F1
    F1 --> F2
    F2 --> F3
    
    F3 --> G1
    G1 --> G2
    G2 --> G3
    
    G3 --> H1
    G3 --> H2
    H2 --> H3
    
    H1 --> I1
    H2 --> I2
    H3 --> I3
    I1 --> I4
    
    %% Styling
    classDef dataSource fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef ingestion fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef storage fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef processing fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef preprocessing fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef chunking fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef embedding fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef intelligence fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px
    classDef ui fill:#fafafa,stroke:#424242,stroke-width:2px
    
    class A1,A2,A3,A4,A5 dataSource
    class B1,B2,B3 ingestion
    class C1,C2,C3 storage
    class D1,D2,D3,D4 processing
    class E1,E2,E3,E4 preprocessing
    class F1,F2,F3 chunking
    class G1,G2,G3 embedding
    class H1,H2,H3 intelligence
    class I1,I2,I3,I4 ui
```

## Document Processing Stages

### Stage 1: Document Ingestion
```
Raw Documents → Connectors → API Gateway → File Validation → Storage
```

**Input**: Various document formats from multiple sources
**Processing**: Authentication, validation, initial metadata extraction
**Output**: Validated documents stored in MinIO with PostgreSQL metadata

### Stage 2: Document Processing
```
Stored Documents → File Type Detection → Quality Assessment → Text Extraction → Language Detection
```

**Input**: Validated document files
**Processing**: File type detection, quality assessment, text extraction, language detection
**Output**: Extracted text with confidence scores and language information

### Stage 3: Enhanced Preprocessing
```
Extracted Text → Confidence Enhancement → Language Processing → Document-Type Cleaning → KMRL Standardization
```

**Input**: Extracted text with metadata
**Processing**: Confidence-based enhancement, language-specific processing, document-type cleaning
**Output**: Clean, standardized text ready for chunking

### Stage 4: Smart Chunking
```
Preprocessed Text → Document-Type Chunkers → Metadata Extraction → Quality Validation
```

**Input**: Preprocessed text
**Processing**: Document-type specific chunking strategies
**Output**: Optimized chunks with metadata

### Stage 5: Embedding Generation
```
Chunks → Vector Generation → Batch Processing → OpenSearch Storage
```

**Input**: Chunked documents
**Processing**: Vector embedding generation, batch processing
**Output**: Vector embeddings stored in OpenSearch

### Stage 6: Intelligence Layer
```
Embeddings → Notification Scanner → RAG Query Engine → LLM Response Generator
```

**Input**: Vector embeddings
**Processing**: Similarity search, context retrieval, response generation
**Output**: Intelligent responses and notifications

## Data Flow Summary

1. **Documents** flow from various sources through connectors
2. **Validation** ensures file integrity and security
3. **Storage** preserves original files and metadata
4. **Processing** extracts text and detects language
5. **Preprocessing** enhances quality and standardizes content
6. **Chunking** creates optimized segments for processing
7. **Embedding** generates vector representations
8. **Intelligence** provides search and response capabilities

## Key Processing Points

- **Multilingual Support**: Malayalam translation and mixed-language processing
- **Document-Type Specific**: Specialized handling for different document categories
- **Quality Assurance**: Confidence scoring and validation throughout
- **Performance Optimization**: Batch processing and parallel execution
- **Error Handling**: Comprehensive error recovery and logging
