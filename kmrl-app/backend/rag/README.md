# OpenSearch Embeddings Upload

This project helps you upload document embeddings from a pickle file to OpenSearch for efficient similarity search and retrieval.

## 🚀 Quick Start

### 1. Start OpenSearch

```bash
# Start OpenSearch cluster with Docker Compose
docker-compose up -d

# Wait for services to be ready (about 30-60 seconds)
docker-compose logs -f opensearch-node1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Upload Embeddings

```bash
python upload_embeddings.py
```

### 4. Search Your Embeddings

```bash
python search_embeddings.py
```

## 📁 Project Structure

```
rag/
├── chunk_embeddings.pkl      # Your embeddings data
├── docker-compose.yml        # OpenSearch cluster setup
├── requirements.txt          # Python dependencies
├── upload_embeddings.py      # Upload script
├── search_embeddings.py      # Search interface
└── README.md                # This file
```

## 🔧 Configuration

### OpenSearch Access
- **OpenSearch API**: http://localhost:9200
- **OpenSearch Dashboards**: http://localhost:5601
- **Index Name**: `embeddings_index`

### Index Configuration
- **Embedding Dimension**: 384
- **Vector Search**: HNSW algorithm with L2 distance
- **Shards**: 1
- **Replicas**: 0 (for development)

## 📊 Data Structure

Your pickle file contains:
```python
{
    (document_id, chunk_index): {
        'document_id': str,
        'chunk_index': int,
        'text': str,
        'embedding': numpy.array(384, float32),
        'metadata': {
            'department': str,
            'source': str,
            'timestamp': str
        }
    }
}
```

## 🔍 Search Capabilities

### 1. Text Search
```python
response = search_by_text(client, "salary report")
```

### 2. Vector Search (k-NN)
```python
response = search_by_embedding(client, query_embedding_vector)
```

### 3. Department Filter
```python
response = search_by_department(client, "accounts")
```

### 4. Hybrid Search
```python
response = hybrid_search(client, "query text", embedding_vector)
```

## 🛠️ Advanced Usage

### Custom Search Query
```python
search_body = {
    "size": 10,
    "query": {
        "bool": {
            "must": [
                {"term": {"metadata.department": "accounts"}},
                {"knn": {
                    "embedding": {
                        "vector": your_embedding,
                        "k": 10
                    }
                }}
            ]
        }
    }
}
response = client.search(index="embeddings_index", body=search_body)
```

### Bulk Operations
```python
# Bulk insert
helpers.bulk(client, documents)

# Bulk update
helpers.bulk(client, update_documents)
```

## 🔧 Troubleshooting

### Connection Issues
```bash
# Check if OpenSearch is running
curl http://localhost:9200

# Check cluster health
curl http://localhost:9200/_cluster/health
```

### Memory Issues
```bash
# Increase Docker memory limits in docker-compose.yml
"OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"
```

### Index Issues
```python
# Delete and recreate index
client.indices.delete(index="embeddings_index")
create_index(client)
```

## 📈 Performance Tips

1. **Batch Size**: Adjust batch size in upload script (default: 100)
2. **Memory**: Increase OpenSearch heap size for large datasets
3. **Shards**: Add more shards for horizontal scaling
4. **Replicas**: Enable replicas for production use

## 🔒 Production Considerations

1. **Security**: Enable security plugins
2. **Authentication**: Add user authentication
3. **SSL/TLS**: Enable encrypted connections
4. **Backup**: Set up regular backups
5. **Monitoring**: Add monitoring and alerting

## 📚 Resources

- [OpenSearch Documentation](https://opensearch.org/docs/)
- [k-NN Search Guide](https://opensearch.org/docs/latest/search-plugins/knn/)
- [Python Client](https://opensearch.org/docs/latest/clients/python/)

## 🤝 Support

If you encounter issues:
1. Check OpenSearch logs: `docker-compose logs opensearch-node1`
2. Verify index mapping: `curl http://localhost:9200/embeddings_index/_mapping`
3. Check cluster health: `curl http://localhost:9200/_cluster/health`
