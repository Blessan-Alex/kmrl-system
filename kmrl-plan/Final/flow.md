
## Phase 1: Document Ingestion
Automatic Data Sources -> Connector services -> API Key Auth
Manual Upload Data sources [Drag n Drop, File Selection] -> Session Auth 
Single API Endpoint [POST api/v1/documents/upload]  [Document Upload API]


File Validation [Prevent malware etc]
Save to Minio/S3
Create a Database Record[Postgress]
Worker picks file from minio and start processing
Queue Processing Task (Redis + Celery)

## Phase 2: Document Processing
Wokrer Picks Task From Queue
File validation
Quality Assessment -> Quality Check -> Process/Enhance/Reject
Process -> Route to Processor
Enhance -> Image Enhancement -> Route to Processor
Reject -> Handle Poor Quality -> Rejected
Processor-> File Category Check ->Image/Text Document/Technical Drawings/Mixed Content
Image -> OCR Processing [Tesseract] -> Image Enhancement -> Language Detection
Language -> Malayalam/English/Mixed
Text -> Markitdown Processing -> Language Detection
Technical Documents -> CAD Processing -> Extract Metadata
Mixed -> Mixed Processing -> Text+OCR Processing
Confidence Assessment -> Confidence Check -> High / Low Confidence
High confidence -> Save results 
Low Confidence -> Flag for human review -> Create review task

## Phase 3: RAG Pipeline Preparation
Data Preprocessing
    ├── Clean text data
    ├── Remove duplicates
    ├── Fix OCR errors
    └── Standardize format[json]

Smart Chunking
    ├── Maintenance documents → Section-based chunks
    ├── Incident reports → Event-based chunks
    ├── Financial docs → Table-based chunks
    └── General docs → Paragraph-based chunks

Generate Embeddings
    ├── OpenAI text-embedding-3-large/ all-MiniLM-L6-v2
    ├── Batch processing
    └── Error handling

Store in Vector Database
    ├── OpenSearch index
    ├── Metadata association
    └── Chunk relationships

## Phase 4: RAG Query Processing

Query Processing
    ├── Convert query to embedding
    ├── Vector similarity search
    ├── Retrieve relevant chunks
    └── Rank by relevance

Context Assembly
    ├── Combine retrieved chunks
    ├── Add metadata context
    └── Prepare for LLM


LLM Response Generation
    ├── Provide context to LLM
    ├── Generate KMRL-specific response
    ├── Include source citations
    └── Return structured response