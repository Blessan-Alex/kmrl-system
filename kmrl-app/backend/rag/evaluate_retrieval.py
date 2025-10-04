#!/usr/bin/env python3
"""
Script to evaluate retrieval performance of the embeddings search system
"""

import numpy as np
from opensearchpy import OpenSearch
import json
import pickle
from sklearn.metrics.pairwise import cosine_similarity
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

def load_embeddings_data(pickle_file='chunk_embeddings.pkl'):
    """Load embeddings data for evaluation"""
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)
    return data

def evaluate_text_search(client, test_queries, index_name="embeddings_index"):
    """Evaluate text-based search performance"""
    print("\n🔍 Evaluating Text Search Performance")
    print("=" * 50)
    
    results = []
    
    for query in test_queries:
        start_time = time.time()
        
        search_body = {
            "size": 5,
            "query": {
                "match": {
                    "text": {
                        "query": query,
                        "fuzziness": "AUTO"
                    }
                }
            }
        }
        
        response = client.search(index=index_name, body=search_body)
        search_time = time.time() - start_time
        
        hits = response['hits']['hits']
        total_found = response['hits']['total']['value']
        
        print(f"\nQuery: '{query}'")
        print(f"Results found: {total_found}")
        print(f"Search time: {search_time:.3f}s")
        
        for i, hit in enumerate(hits[:3], 1):
            source = hit['_source']
            score = hit['_score']
            print(f"  {i}. {source['document_id']} (Score: {score:.3f})")
            print(f"     Text: {source['text'][:100]}...")
        
        results.append({
            'query': query,
            'total_found': total_found,
            'search_time': search_time,
            'top_results': hits[:3]
        })
    
    return results

def evaluate_vector_search(client, embeddings_data, index_name="embeddings_index"):
    """Evaluate vector-based search performance"""
    print("\n🎯 Evaluating Vector Search Performance")
    print("=" * 50)
    
    results = []
    
    # Test with a few sample embeddings
    test_cases = list(embeddings_data.items())[:3]
    
    for (doc_id, chunk_idx), data in test_cases:
        query_embedding = data['embedding'].tolist()
        original_text = data['text']
        
        print(f"\nQuery Document: {doc_id} (Chunk {chunk_idx})")
        print(f"Original text: {original_text[:100]}...")
        
        start_time = time.time()
        
        search_body = {
            "size": 5,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": 5
                    }
                }
            }
        }
        
        response = client.search(index=index_name, body=search_body)
        search_time = time.time() - start_time
        
        hits = response['hits']['hits']
        
        print(f"Vector search time: {search_time:.3f}s")
        print("Top similar documents:")
        
        for i, hit in enumerate(hits, 1):
            source = hit['_source']
            score = hit['_score']
            is_original = (source['document_id'] == doc_id and source['chunk_index'] == chunk_idx)
            match_indicator = "🎯 EXACT MATCH" if is_original else ""
            
            print(f"  {i}. {source['document_id']} (Score: {score:.3f}) {match_indicator}")
            print(f"     Text: {source['text'][:100]}...")
        
        results.append({
            'query_doc': doc_id,
            'query_chunk': chunk_idx,
            'search_time': search_time,
            'top_results': hits,
            'exact_match_found': any(hit['_source']['document_id'] == doc_id and hit['_source']['chunk_index'] == chunk_idx for hit in hits)
        })
    
    return results

def evaluate_department_filtering(client, index_name="embeddings_index"):
    """Evaluate department-based filtering"""
    print("\n🏢 Evaluating Department Filtering")
    print("=" * 50)
    
    # Get all departments from the data
    search_body = {
        "size": 0,
        "aggs": {
            "departments": {
                "terms": {
                    "field": "metadata.department",
                    "size": 10
                }
            }
        }
    }
    
    response = client.search(index=index_name, body=search_body)
    departments = [bucket['key'] for bucket in response['aggregations']['departments']['buckets']]
    
    print(f"Available departments: {departments}")
    
    results = []
    
    for dept in departments:
        search_body = {
            "size": 10,
            "query": {
                "term": {
                    "metadata.department": dept
                }
            }
        }
        
        response = client.search(index=index_name, body=search_body)
        count = response['hits']['total']['value']
        
        print(f"\nDepartment '{dept}': {count} documents")
        
        # Show sample documents
        for hit in response['hits']['hits'][:3]:
            source = hit['_source']
            print(f"  - {source['document_id']}: {source['text'][:80]}...")
        
        results.append({
            'department': dept,
            'document_count': count
        })
    
    return results

def evaluate_hybrid_search(client, test_queries, embeddings_data, index_name="embeddings_index"):
    """Evaluate hybrid search combining text and vector search"""
    print("\n🔄 Evaluating Hybrid Search Performance")
    print("=" * 50)
    
    results = []
    
    # Use first embedding as query vector
    first_embedding = list(embeddings_data.values())[0]['embedding'].tolist()
    
    for query_text in test_queries[:2]:  # Test with first 2 queries
        print(f"\nHybrid Query: '{query_text}'")
        
        start_time = time.time()
        
        search_body = {
            "size": 5,
            "query": {
                "bool": {
                    "should": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": first_embedding,
                                    "k": 5,
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
        search_time = time.time() - start_time
        
        hits = response['hits']['hits']
        
        print(f"Hybrid search time: {search_time:.3f}s")
        print("Results (text + vector combined):")
        
        for i, hit in enumerate(hits[:3], 1):
            source = hit['_source']
            score = hit['_score']
            print(f"  {i}. {source['document_id']} (Score: {score:.3f})")
            print(f"     Text: {source['text'][:100]}...")
        
        results.append({
            'query_text': query_text,
            'search_time': search_time,
            'top_results': hits[:3]
        })
    
    return results

def calculate_retrieval_metrics(results):
    """Calculate retrieval performance metrics"""
    print("\n📊 Retrieval Performance Metrics")
    print("=" * 50)
    
    # Text search metrics
    if 'text_search' in results:
        text_results = results['text_search']
        avg_search_time = np.mean([r['search_time'] for r in text_results])
        avg_results_found = np.mean([r['total_found'] for r in text_results])
        
        print(f"Text Search:")
        print(f"  Average search time: {avg_search_time:.3f}s")
        print(f"  Average results found: {avg_results_found:.1f}")
    
    # Vector search metrics
    if 'vector_search' in results:
        vector_results = results['vector_search']
        avg_search_time = np.mean([r['search_time'] for r in vector_results])
        exact_match_rate = np.mean([r['exact_match_found'] for r in vector_results])
        
        print(f"\nVector Search:")
        print(f"  Average search time: {avg_search_time:.3f}s")
        print(f"  Exact match rate: {exact_match_rate:.2%}")
    
    # Department filtering metrics
    if 'department_filtering' in results:
        dept_results = results['department_filtering']
        total_docs = sum(r['document_count'] for r in dept_results)
        
        print(f"\nDepartment Filtering:")
        print(f"  Total documents indexed: {total_docs}")
        print(f"  Unique departments: {len(dept_results)}")

def run_comprehensive_evaluation():
    """Run comprehensive retrieval evaluation"""
    print("🚀 Starting Comprehensive Retrieval Evaluation")
    print("=" * 60)
    
    # Connect to OpenSearch
    try:
        client = connect_to_opensearch()
        print("✅ Connected to OpenSearch")
    except Exception as e:
        print(f"❌ Failed to connect to OpenSearch: {e}")
        return
    
    # Load embeddings data
    try:
        embeddings_data = load_embeddings_data()
        print(f"✅ Loaded {len(embeddings_data)} embeddings")
    except Exception as e:
        print(f"❌ Failed to load embeddings: {e}")
        return
    
    # Test queries for evaluation
    test_queries = [
        "salary report",
        "engine maintenance",
        "employee data",
        "security policy",
        "financial information"
    ]
    
    all_results = {}
    
    # 1. Text Search Evaluation
    all_results['text_search'] = evaluate_text_search(client, test_queries)
    
    # 2. Vector Search Evaluation
    all_results['vector_search'] = evaluate_vector_search(client, embeddings_data)
    
    # 3. Department Filtering Evaluation
    all_results['department_filtering'] = evaluate_department_filtering(client)
    
    # 4. Hybrid Search Evaluation
    all_results['hybrid_search'] = evaluate_hybrid_search(client, test_queries, embeddings_data)
    
    # 5. Calculate Metrics
    calculate_retrieval_metrics(all_results)
    
    print("\n🎉 Evaluation Complete!")
    print("\nNext steps:")
    print("1. Review the results above")
    print("2. Adjust search parameters if needed")
    print("3. Test with your specific use cases")
    print("4. Monitor performance in production")

def main():
    """Main evaluation function"""
    run_comprehensive_evaluation()

if __name__ == "__main__":
    main()

