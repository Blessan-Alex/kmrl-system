# OpenSearch RAG Engine

This directory contains the RAG (Retrieval-Augmented Generation) engine that integrates with OpenSearch for vector similarity search.

## 🚀 Quick Start

### Prerequisites
- OpenSearch running on localhost:9200
- Embeddings uploaded to OpenSearch (use `../rag/upload_embeddings.py`)

### Installation
```bash
pip install -r requirements.txt
```

### Usage

#### 1. Simple Query Interface
```bash
python query_interface.py
```
This provides an interactive interface for testing queries.

#### 2. Programmatic Usage
```python
from opensearch_query_processor import OpenSearchQueryProcessor

# Initialize processor
processor = OpenSearchQueryProcessor()

# Search by query text (vector search)
results = processor.search_by_query_text("metro train schedule", size=5)

# Search by text (keyword search)
results = processor.search_by_text("safety report", size=5)

# Hybrid search (vector + text)
results = processor.hybrid_search("maintenance schedule", size=5)

# Search with department filter
results = processor.search_by_query_text(
    "budget report", 
    size=5, 
    department="accounts"
)
```

#### 3. Using the Updated Query Processing
```bash
python query_processing.py
```
This runs the updated query processor with OpenSearch integration.

## 📁 Files Overview

### Core Files
- **`opensearch_query_processor.py`** - Main OpenSearch integration class
- **`query_processing.py`** - Updated query processor with OpenSearch support
- **`query_to_embedding.py`** - Text-to-embedding conversion
- **`query_test.py`** - Unit tests for the RAG engine

### Interface Files
- **`query_interface.py`** - Simple interactive query interface
- **`requirements.txt`** - Python dependencies
- **`README.md`** - This documentation

## 🔍 Search Types

### 1. Vector Search (Semantic Similarity)
- Converts query text to embedding
- Uses k-NN search in OpenSearch
- Best for semantic understanding

### 2. Text Search (Keyword Matching)
- Direct text matching with fuzzy search
- Good for exact keyword queries
- Fast and lightweight

### 3. Hybrid Search
- Combines vector and text search
- Balances semantic and keyword matching
- Best overall results

## 🛠️ Configuration

### OpenSearch Connection
```python
processor = OpenSearchQueryProcessor(
    opensearch_host="localhost",
    opensearch_port=9200,
    index_name="embeddings_index",
    use_ssl=False
)
```

### Search Parameters
```python
results = processor.search_by_query_text(
    query="your query",
    size=5,                    # Number of results
    department="engineering"   # Optional department filter
)
```

## 📊 Results Format

Each search result contains:
```python
{
    'document_id': 'doc_12345',
    'chunk_index': 2,
    'text': 'Document content...',
    'similarity_score': 0.8542,
    'metadata': {
        'department': 'engineering',
        'source': 'email_connector',
        'timestamp': '2024-01-15T10:30:00Z'
    },
    'opensearch_id': 'doc_12345_2'
}
```

## 🔧 Troubleshooting

### Connection Issues
1. Ensure OpenSearch is running: `curl http://localhost:9200`
2. Check if embeddings index exists
3. Verify OpenSearch credentials

### No Results
1. Check if embeddings are uploaded to OpenSearch
2. Try different search types (vector vs text)
3. Verify query text is not empty
4. Check department filters

### Performance Issues
1. Reduce `size` parameter for fewer results
2. Use department filters to narrow search
3. Check OpenSearch cluster health

## 🧪 Testing

Run the test suite:
```bash
python query_test.py
```

Test OpenSearch connection:
```bash
python query_interface.py
```

## 📈 Performance Tips

1. **Use appropriate search type**:
   - Vector search for semantic queries
   - Text search for exact keywords
   - Hybrid search for best results

2. **Filter by department** when possible to reduce search space

3. **Limit results** with `size` parameter for better performance

4. **Monitor OpenSearch** cluster health and performance metrics
