#!/usr/bin/env python3
"""
Improved RAG Search Implementation
Implements score normalization, hybrid search, and better retrieval techniques
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Rag-Engine'))

from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch
import numpy as np
import time
from functools import lru_cache

class ImprovedRAGSearch:
    def __init__(self):
        self.client = None
        self.model = None
        self._connect_to_opensearch()
        self._load_model()
    
    def _connect_to_opensearch(self):
        """Connect to OpenSearch with optimized settings"""
        self.client = OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
    
    @lru_cache(maxsize=1)
    def _load_model(self):
        """Load and cache the embedding model"""
        print("🤖 Loading krutrim-ai-labs/vyakyarth model...")
        self.model = SentenceTransformer('krutrim-ai-labs/vyakyarth')
        print("✅ Model loaded and cached")
        return self.model
    
    def normalize_scores(self, scores):
        """Normalize similarity scores to 0-1 range"""
        if not scores:
            return scores
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        normalized = [(score - min_score) / (max_score - min_score) for score in scores]
        return normalized
    
    def improved_vector_search(self, query, top_k=5, boost_factor=1.0):
        """Improved vector search with score normalization"""
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Enhanced search with boost and normalization
        search_body = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": top_k,
                        "boost": boost_factor
                    }
                }
            },
            "_source": ["document_id", "chunk_index", "text", "metadata", "file_path", "chunk_text"],
            "sort": [
                {"_score": {"order": "desc"}}
            ]
        }
        
        response = self.client.search(index="embeddings_index", body=search_body)
        processing_time = time.time() - start_time
        
        # Extract and normalize scores
        hits = response['hits']['hits']
        scores = [hit['_score'] for hit in hits]
        normalized_scores = self.normalize_scores(scores)
        
        # Update scores in results
        for i, hit in enumerate(hits):
            hit['_score'] = normalized_scores[i]
        
        return {
            'results': hits,
            'processing_time': processing_time,
            'original_scores': scores,
            'normalized_scores': normalized_scores,
            'total_hits': response['hits']['total']['value']
        }
    
    def hybrid_search(self, query, top_k=5, vector_weight=0.7, text_weight=0.3):
        """Hybrid search combining vector and text search"""
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Hybrid search with weighted combination
        search_body = {
            "size": top_k,
            "query": {
                "bool": {
                    "should": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_embedding,
                                    "k": top_k,
                                    "boost": vector_weight
                                }
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["text^2", "chunk_text^1.5", "metadata.department^0.5"],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "boost": text_weight
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "_source": ["document_id", "chunk_index", "text", "metadata", "file_path", "chunk_text"]
        }
        
        response = self.client.search(index="embeddings_index", body=search_body)
        processing_time = time.time() - start_time
        
        # Extract and normalize scores
        hits = response['hits']['hits']
        scores = [hit['_score'] for hit in hits]
        normalized_scores = self.normalize_scores(scores)
        
        # Update scores in results
        for i, hit in enumerate(hits):
            hit['_score'] = normalized_scores[i]
        
        return {
            'results': hits,
            'processing_time': processing_time,
            'original_scores': scores,
            'normalized_scores': normalized_scores,
            'total_hits': response['hits']['total']['value']
        }
    
    def advanced_search(self, query, top_k=5, search_type="hybrid"):
        """Advanced search with multiple techniques"""
        if search_type == "vector":
            return self.improved_vector_search(query, top_k)
        elif search_type == "hybrid":
            return self.hybrid_search(query, top_k)
        else:
            raise ValueError("search_type must be 'vector' or 'hybrid'")
    
    def compare_search_methods(self, query, top_k=5):
        """Compare different search methods"""
        print(f"\n🔍 Comparing Search Methods for: '{query}'")
        print("=" * 60)
        
        methods = {
            'Improved Vector': self.improved_vector_search,
            'Hybrid Search': self.hybrid_search
        }
        
        results = {}
        
        for method_name, method_func in methods.items():
            print(f"\n🔍 {method_name}:")
            result = method_func(query, top_k)
            
            results[method_name] = {
                'processing_time': result['processing_time'],
                'top_scores': result['normalized_scores'][:3],
                'avg_score': np.mean(result['normalized_scores']),
                'score_range': f"{min(result['normalized_scores']):.4f} - {max(result['normalized_scores']):.4f}",
                'num_results': len(result['results'])
            }
            
            print(f"   ⏱️  Time: {result['processing_time']:.4f}s")
            print(f"   📊 Top Scores: {result['normalized_scores'][:3]}")
            print(f"   📈 Avg Score: {np.mean(result['normalized_scores']):.4f}")
            print(f"   📋 Results: {len(result['results'])}")
            
            # Show top result preview
            if result['results']:
                top_result = result['results'][0]
                preview = top_result['_source'].get('chunk_text', top_result['_source'].get('text', ''))[:100]
                print(f"   📝 Top Result: {preview}...")
        
        return results
    
    def evaluate_search_quality(self, test_queries):
        """Evaluate search quality across multiple queries"""
        print("\n📊 Evaluating Search Quality...")
        print("=" * 50)
        
        all_results = {
            'vector_search': [],
            'hybrid_search': []
        }
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query[:50]}...'")
            
            # Test vector search
            vector_result = self.improved_vector_search(query, top_k=5)
            all_results['vector_search'].append({
                'query': query,
                'processing_time': vector_result['processing_time'],
                'avg_score': np.mean(vector_result['normalized_scores']),
                'score_std': np.std(vector_result['normalized_scores']),
                'num_results': len(vector_result['results'])
            })
            
            # Test hybrid search
            hybrid_result = self.hybrid_search(query, top_k=5)
            all_results['hybrid_search'].append({
                'query': query,
                'processing_time': hybrid_result['processing_time'],
                'avg_score': np.mean(hybrid_result['normalized_scores']),
                'score_std': np.std(hybrid_result['normalized_scores']),
                'num_results': len(hybrid_result['results'])
            })
        
        # Calculate aggregate metrics
        print("\n📈 Aggregate Results:")
        for method, results in all_results.items():
            avg_time = np.mean([r['processing_time'] for r in results])
            avg_score = np.mean([r['avg_score'] for r in results])
            avg_std = np.mean([r['score_std'] for r in results])
            
            print(f"\n🔍 {method.upper()}:")
            print(f"   ⏱️  Avg Time: {avg_time:.4f}s")
            print(f"   📊 Avg Score: {avg_score:.4f}")
            print(f"   📈 Score Std: {avg_std:.4f}")
        
        return all_results

def main():
    """Test the improved search implementation"""
    print("🚀 Testing Improved RAG Search Implementation")
    print("=" * 60)
    
    # Initialize improved search
    search = ImprovedRAGSearch()
    
    # Test queries
    test_queries = [
        "What are the safety requirements for metro operations?",
        "maintenance schedule and procedures",
        "incident report emergency brake",
        "financial budget and expenses"
    ]
    
    # Compare search methods
    search.compare_search_methods(test_queries[0])
    
    # Evaluate search quality
    search.evaluate_search_quality(test_queries)

if __name__ == "__main__":
    main()
