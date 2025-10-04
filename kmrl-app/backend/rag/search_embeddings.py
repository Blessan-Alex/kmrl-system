#!/usr/bin/env python3
"""
Script to search embeddings in OpenSearch
"""

import numpy as np
from opensearchpy import OpenSearch
import json

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

def search_by_text(client, query_text, index_name="embeddings_index", size=5):
    """Search by text content"""
    search_body = {
        "size": size,
        "query": {
            "match": {
                "text": {
                    "query": query_text,
                    "fuzziness": "AUTO"
                }
            }
        }
    }
    
    response = client.search(index=index_name, body=search_body)
    return response

def search_by_embedding(client, query_embedding, index_name="embeddings_index", size=5):
    """Search by embedding vector using k-NN"""
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

def search_by_department(client, department, index_name="embeddings_index", size=10):
    """Search by department"""
    search_body = {
        "size": size,
        "query": {
            "term": {
                "metadata.department": department
            }
        }
    }
    
    response = client.search(index=index_name, body=search_body)
    return response

def hybrid_search(client, query_text, query_embedding, index_name="embeddings_index", size=5):
    """Hybrid search combining text and vector search"""
    search_body = {
        "size": size,
        "query": {
            "bool": {
                "should": [
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_embedding,
                                "k": size,
                                "boost": 0.7
                            }
                        }
                    },
                    {
                        "match": {
                            "text": {
                                "query": query_text,
                                "boost": 0.3
                            }
                        }
                    }
                ]
            }
        }
    }
    
    response = client.search(index=index_name, body=search_body)
    return response

def display_results(response, search_type="Search"):
    """Display search results in a readable format"""
    print(f"\n{search_type} Results:")
    print("=" * 50)
    
    hits = response['hits']['hits']
    total = response['hits']['total']['value']
    
    print(f"Total matches: {total}")
    print(f"Showing top {len(hits)} results:\n")
    
    for i, hit in enumerate(hits, 1):
        source = hit['_source']
        score = hit['_score']
        
        print(f"{i}. Document: {source['document_id']} (Chunk {source['chunk_index']})")
        print(f"   Score: {score:.4f}")
        print(f"   Department: {source['metadata']['department']}")
        print(f"   Text: {source['text'][:150]}...")
        print("-" * 50)

def main():
    """Interactive search interface"""
    try:
        client = connect_to_opensearch()
        print("Connected to OpenSearch successfully!")
    except Exception as e:
        print(f"Failed to connect to OpenSearch: {e}")
        return
    
    while True:
        print("\n🔍 OpenSearch Embeddings Search")
        print("1. Search by text")
        print("2. Search by department")
        print("3. Get sample embeddings for vector search")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            query = input("Enter search text: ").strip()
            if query:
                response = search_by_text(client, query)
                display_results(response, "Text Search")
        
        elif choice == "2":
            departments = ["accounts", "engineering", "hr", "legal", "security"]
            print("Available departments:", ", ".join(departments))
            dept = input("Enter department: ").strip()
            if dept:
                response = search_by_department(client, dept)
                display_results(response, "Department Search")
        
        elif choice == "3":
            # Get a sample embedding from the first document
            search_body = {"size": 1, "query": {"match_all": {}}}
            response = client.search(index="embeddings_index", body=search_body)
            if response['hits']['hits']:
                sample_embedding = response['hits']['hits'][0]['_source']['embedding']
                print(f"Sample embedding (first 10 values): {sample_embedding[:10]}")
                print("You can use this for vector search in your application")
        
        elif choice == "4":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
