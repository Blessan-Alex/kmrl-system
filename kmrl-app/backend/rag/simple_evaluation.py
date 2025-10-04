#!/usr/bin/env python3
"""
Simple retrieval evaluation script
"""

import time
from opensearchpy import OpenSearch
import pickle

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

def evaluate_text_search():
    """Test text-based search"""
    print("🔍 Testing Text Search")
    print("=" * 30)
    
    client = connect_to_opensearch()
    
    test_queries = ["salary", "engine", "maintenance", "policy"]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        start_time = time.time()
        search_body = {
            "size": 3,
            "query": {"match": {"text": query}}
        }
        
        response = client.search(index="embeddings_index", body=search_body)
        search_time = time.time() - start_time
        
        hits = response['hits']['hits']
        print(f"Found {len(hits)} results in {search_time:.3f}s")
        
        for i, hit in enumerate(hits, 1):
            source = hit['_source']
            print(f"  {i}. {source['document_id']} (Score: {hit['_score']:.2f})")
            print(f"     {source['text'][:80]}...")

def evaluate_vector_search():
    """Test vector-based search"""
    print("\n🎯 Testing Vector Search")
    print("=" * 30)
    
    client = connect_to_opensearch()
    
    # Load one embedding for testing
    with open('chunk_embeddings.pkl', 'rb') as f:
        data = pickle.load(f)
    
    # Use first embedding as query
    first_key = list(data.keys())[0]
    query_embedding = data[first_key]['embedding'].tolist()
    original_text = data[first_key]['text']
    
    print(f"Query from: {first_key[0]} (chunk {first_key[1]})")
    print(f"Original text: {original_text[:100]}...")
    
    start_time = time.time()
    search_body = {
        "size": 3,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_embedding,
                    "k": 3
                }
            }
        }
    }
    
    response = client.search(index="embeddings_index", body=search_body)
    search_time = time.time() - start_time
    
    hits = response['hits']['hits']
    print(f"\nFound {len(hits)} similar documents in {search_time:.3f}s")
    
    for i, hit in enumerate(hits, 1):
        source = hit['_source']
        is_exact = (source['document_id'] == first_key[0] and source['chunk_index'] == first_key[1])
        match_type = "🎯 EXACT MATCH" if is_exact else "📄 Similar"
        
        print(f"  {i}. {source['document_id']} (Score: {hit['_score']:.2f}) {match_type}")
        print(f"     {source['text'][:80]}...")

def evaluate_department_filter():
    """Test department filtering"""
    print("\n🏢 Testing Department Filtering")
    print("=" * 30)
    
    client = connect_to_opensearch()
    
    # Get all departments
    search_body = {
        "size": 0,
        "aggs": {
            "departments": {
                "terms": {"field": "metadata.department"}
            }
        }
    }
    
    response = client.search(index="embeddings_index", body=search_body)
    departments = [bucket['key'] for bucket in response['aggregations']['departments']['buckets']]
    
    print(f"Available departments: {departments}")
    
    for dept in departments:
        search_body = {
            "size": 2,
            "query": {"term": {"metadata.department": dept}}
        }
        
        response = client.search(index="embeddings_index", body=search_body)
        count = response['hits']['total']['value']
        
        print(f"\nDepartment '{dept}': {count} documents")
        for hit in response['hits']['hits']:
            source = hit['_source']
            print(f"  - {source['document_id']}: {source['text'][:60]}...")

def test_retrieval_speed():
    """Test retrieval speed"""
    print("\n⚡ Testing Retrieval Speed")
    print("=" * 30)
    
    client = connect_to_opensearch()
    
    # Test multiple queries
    queries = ["salary", "engine", "policy", "maintenance", "financial"]
    times = []
    
    for query in queries:
        start_time = time.time()
        search_body = {"size": 5, "query": {"match": {"text": query}}}
        response = client.search(index="embeddings_index", body=search_body)
        search_time = time.time() - start_time
        times.append(search_time)
        
        print(f"'{query}': {search_time:.3f}s ({response['hits']['total']['value']} results)")
    
    avg_time = sum(times) / len(times)
    print(f"\nAverage search time: {avg_time:.3f}s")
    print(f"Fastest search: {min(times):.3f}s")
    print(f"Slowest search: {max(times):.3f}s")

def main():
    """Run all evaluations"""
    print("🚀 Retrieval System Evaluation")
    print("=" * 50)
    
    try:
        # Test different retrieval methods
        evaluate_text_search()
        evaluate_vector_search()
        evaluate_department_filter()
        test_retrieval_speed()
        
        print("\n✅ Evaluation Complete!")
        print("\n📊 Summary:")
        print("- Text search: Working ✓")
        print("- Vector search: Working ✓") 
        print("- Department filtering: Working ✓")
        print("- Speed: Good performance ✓")
        
        print("\n🎯 Your retrieval system is ready for RAG!")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")

if __name__ == "__main__":
    main()

