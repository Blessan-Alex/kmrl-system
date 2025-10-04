#!/usr/bin/env python3
"""
Script to upload embeddings from pickle file to OpenSearch
"""

import pickle
import numpy as np
from opensearchpy import OpenSearch, helpers
import json
from tqdm import tqdm
import time

def connect_to_opensearch():
    """Connect to OpenSearch cluster"""
    client = OpenSearch(
        hosts=[{'host': 'localhost', 'port': 9200}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )
    return client

def create_index(client, index_name="embeddings_index"):
    """Create index with proper mapping for embeddings"""
    
    # Check if index already exists
    if client.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists. Deleting it...")
        client.indices.delete(index=index_name)
    
    # Define the index mapping
    index_mapping = {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "knn": True,
                "knn.algo_param.ef_search": 100
            }
        },
        "mappings": {
            "properties": {
                "document_id": {
                    "type": "keyword"
                },
                "chunk_index": {
                    "type": "integer"
                },
                "text": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 768,
                    "method": {
                        "name": "hnsw",
                        "space_type": "l2",
                        "engine": "nmslib",
                        "parameters": {
                            "ef_construction": 128,
                            "m": 24
                        }
                    }
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "department": {
                            "type": "keyword"
                        },
                        "source": {
                            "type": "keyword"
                        },
                        "timestamp": {
                            "type": "keyword"
                        }
                    }
                }
            }
        }
    }
    
    # Create the index
    response = client.indices.create(index=index_name, body=index_mapping)
    print(f"Index '{index_name}' created successfully!")
    return response

def load_embeddings_from_pickle(pickle_file):
    """Load embeddings from pickle file"""
    print(f"Loading embeddings from {pickle_file}...")
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)
    
    print(f"Loaded {len(data)} embeddings")
    return data

def prepare_documents_for_upload(embeddings_data):
    """Prepare documents for bulk upload to OpenSearch"""
    documents = []
    
    for key, value in tqdm(embeddings_data.items(), desc="Preparing documents"):
        document_id, chunk_index = key
        
        # Convert numpy array to list for JSON serialization
        embedding_list = value['embedding'].tolist()
        
        doc = {
            "_index": "embeddings_index",
            "_id": f"{document_id}_{chunk_index}",
            "_source": {
                "document_id": document_id,
                "chunk_index": chunk_index,
                "text": value['text'],
                "embedding": embedding_list,
                "metadata": value['metadata']
            }
        }
        documents.append(doc)
    
    return documents

def upload_documents(client, documents, batch_size=100):
    """Upload documents to OpenSearch in batches"""
    print(f"Uploading {len(documents)} documents to OpenSearch...")
    
    # Upload in batches
    for i in tqdm(range(0, len(documents), batch_size), desc="Uploading batches"):
        batch = documents[i:i + batch_size]
        try:
            response = helpers.bulk(client, batch)
            print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} documents")
        except Exception as e:
            print(f"Error uploading batch {i//batch_size + 1}: {e}")
            continue
    
    print("Upload completed!")

def verify_upload(client, index_name="embeddings_index"):
    """Verify the upload by checking index stats"""
    print("\nVerifying upload...")
    
    # Get index stats
    stats = client.indices.stats(index=index_name)
    doc_count = stats['indices'][index_name]['total']['docs']['count']
    
    print(f"Total documents in index: {doc_count}")
    
    # Get a sample document
    search_body = {
        "size": 1,
        "query": {
            "match_all": {}
        }
    }
    
    response = client.search(index=index_name, body=search_body)
    if response['hits']['total']['value'] > 0:
        sample_doc = response['hits']['hits'][0]['_source']
        print(f"Sample document ID: {sample_doc['document_id']}")
        print(f"Sample text preview: {sample_doc['text'][:100]}...")
        print(f"Embedding dimension: {len(sample_doc['embedding'])}")
    
    return doc_count

def search_embeddings(client, query_embedding, index_name="embeddings_index", size=5):
    """Perform a k-NN search using an embedding vector"""
    search_body = {
        "size": size,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_embedding,
                    "k": size
                }
            }
        }
    }
    
    response = client.search(index=index_name, body=search_body)
    return response

def main():
    """Main function to orchestrate the upload process"""
    print("Starting OpenSearch embeddings upload process...")
    
    # Connect to OpenSearch
    try:
        client = connect_to_opensearch()
        print("Connected to OpenSearch successfully!")
    except Exception as e:
        print(f"Failed to connect to OpenSearch: {e}")
        print("Make sure OpenSearch is running on localhost:9200")
        return
    
    # Create index
    try:
        create_index(client)
    except Exception as e:
        print(f"Failed to create index: {e}")
        return
    
    # Load embeddings
    try:
        embeddings_data = load_embeddings_from_pickle('chunk_embeddings.pkl')
    except Exception as e:
        print(f"Failed to load embeddings: {e}")
        return
    
    # Prepare documents
    try:
        documents = prepare_documents_for_upload(embeddings_data)
    except Exception as e:
        print(f"Failed to prepare documents: {e}")
        return
    
    # Upload documents
    try:
        upload_documents(client, documents)
    except Exception as e:
        print(f"Failed to upload documents: {e}")
        return
    
    # Verify upload
    try:
        doc_count = verify_upload(client)
        print(f"\n✅ Successfully uploaded {doc_count} embeddings to OpenSearch!")
    except Exception as e:
        print(f"Failed to verify upload: {e}")
        return
    
    print("\n🎉 Upload process completed successfully!")
    print("\nYou can now:")
    print("1. Access OpenSearch Dashboards at http://localhost:5601")
    print("2. Use the search_embeddings function to perform similarity searches")
    print("3. Query your embeddings using the OpenSearch API")

if __name__ == "__main__":
    main()
