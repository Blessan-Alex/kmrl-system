"""
RAG Pipeline Worker for KMRL
Handles document chunking, embedding generation, and vector storage
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
import structlog
from celery import Celery
# Note: sentence_transformers, opensearchpy and shared modules need to be installed/implemented
# from sentence_transformers import SentenceTransformer
# from opensearchpy import OpenSearch
# from shared.text_chunker import TextChunker
# from shared.embedding_generator import EmbeddingGenerator

logger = structlog.get_logger()

# Initialize Celery
celery_app = Celery('kmrl-rag-worker')
celery_app.config_from_object('config.celery_config.CELERY_CONFIG')

# Autodiscover tasks to ensure all are registered
celery_app.autodiscover_tasks(['workers.rag_worker.worker'])

# Initialize OpenSearch client (commented out until opensearchpy is installed)
# opensearch_client = OpenSearch(
#     hosts=[os.getenv('OPENSEARCH_URL', 'http://localhost:9200')],
#     http_auth=(os.getenv('OPENSEARCH_USER', 'admin'), os.getenv('OPENSEARCH_PASSWORD', 'admin')),
#     use_ssl=False,
#     verify_certs=False
# )

# Initialize processors (commented out until shared modules are implemented)
# text_chunker = TextChunker()
# embedding_generator = EmbeddingGenerator()

@celery_app.task
def prepare_rag_pipeline(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare document for RAG pipeline"""
    try:
        document_id = document_data.get('document_id')
        text_content = document_data.get('text_content')
        language = document_data.get('language')
        department = document_data.get('department')
        
        logger.info(f"Preparing RAG pipeline for document: {document_id}")
        
        # Step 1: Chunk text content
        chunks = text_chunker.chunk_text(text_content, language)
        
        # Step 2: Generate embeddings for each chunk
        chunk_embeddings = []
        for i, chunk in enumerate(chunks):
            embedding = embedding_generator.generate_embedding(chunk['text'])
            chunk_data = {
                "chunk_id": str(uuid.uuid4()),
                "document_id": document_id,
                "chunk_index": i,
                "chunk_text": chunk['text'],
                "embedding": embedding.tolist(),
                "metadata": {
                    "language": language,
                    "department": department,
                    "chunk_type": chunk.get('type', 'text'),
                    "created_at": datetime.now().isoformat()
                }
            }
            chunk_embeddings.append(chunk_data)
        
        # Step 3: Store in OpenSearch
        index_name = f"kmrl-documents-{datetime.now().strftime('%Y%m')}"
        for chunk_data in chunk_embeddings:
            opensearch_client.index(
                index=index_name,
                id=chunk_data['chunk_id'],
                body=chunk_data
            )
        
        result = {
            "document_id": document_id,
            "status": "rag_ready",
            "chunks_created": len(chunk_embeddings),
            "index_name": index_name,
            "processed_at": datetime.now().isoformat()
        }
        
        logger.info(f"RAG pipeline prepared successfully: {document_id}")
        return result
        
    except Exception as e:
        logger.error(f"RAG pipeline preparation failed: {e}")
        return {
            "document_id": document_data.get('document_id'),
            "status": "failed",
            "error": str(e),
            "processed_at": datetime.now().isoformat()
        }

@celery_app.task
def search_similar_documents(query: str, department: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for similar documents using vector similarity"""
    try:
        # Generate query embedding
        query_embedding = embedding_generator.generate_embedding(query)
        
        # Build search query
        search_body = {
            "query": {
                "knn": {
                    "field": "embedding",
                    "query_vector": query_embedding.tolist(),
                    "k": limit
                }
            }
        }
        
        if department:
            search_body["query"]["knn"]["filter"] = {
                "term": {"metadata.department": department}
            }
        
        # Search OpenSearch
        response = opensearch_client.search(
            index="kmrl-documents-*",
            body=search_body
        )
        
        results = []
        for hit in response['hits']['hits']:
            results.append({
                "chunk_id": hit['_id'],
                "document_id": hit['_source']['document_id'],
                "chunk_text": hit['_source']['chunk_text'],
                "similarity_score": hit['_score'],
                "metadata": hit['_source']['metadata']
            })
        
        logger.info(f"Found {len(results)} similar documents for query: {query}")
        return results
        
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        return []

if __name__ == "__main__":
    celery_app.start()
