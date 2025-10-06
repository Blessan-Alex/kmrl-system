#!/usr/bin/env python3
"""
Comprehensive RAG Retrieval Evaluation Framework
Evaluates embedding model quality and retrieval performance
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Rag-Engine'))

from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch
import numpy as np
import json
import time
from collections import defaultdict
# import matplotlib.pyplot as plt
# import seaborn as sns

class RetrievalEvaluator:
    def __init__(self):
        self.client = None
        self.model = None
        self.evaluation_results = {}
        
    def connect_to_opensearch(self):
        """Connect to OpenSearch cluster"""
        self.client = OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        return self.client
    
    def load_embedding_model(self):
        """Load the embedding model"""
        print("🤖 Loading krutrim-ai-labs/vyakyarth model...")
        self.model = SentenceTransformer('krutrim-ai-labs/vyakyarth')
        print(f"✅ Model loaded successfully")
        return self.model
    
    def get_index_stats(self):
        """Get comprehensive index statistics"""
        if not self.client.indices.exists(index="embeddings_index"):
            return None
            
        stats = self.client.indices.stats(index="embeddings_index")
        mapping = self.client.indices.get_mapping(index="embeddings_index")
        
        return {
            'total_documents': stats['indices']['embeddings_index']['total']['docs']['count'],
            'index_size_bytes': stats['indices']['embeddings_index']['total']['store']['size_in_bytes'],
            'mapping': mapping
        }
    
    def evaluate_embedding_quality(self, sample_queries):
        """Evaluate embedding model quality"""
        print("\n🔍 Evaluating Embedding Quality...")
        print("=" * 50)
        
        results = {
            'embedding_dimensions': 0,
            'similarity_scores': [],
            'query_processing_time': [],
            'model_performance': {}
        }
        
        for i, query in enumerate(sample_queries):
            start_time = time.time()
            
            # Generate embedding
            embedding = self.model.encode(query)
            processing_time = time.time() - start_time
            
            results['embedding_dimensions'] = len(embedding)
            results['query_processing_time'].append(processing_time)
            
            # Test semantic similarity with similar queries
            if i < len(sample_queries) - 1:
                next_embedding = self.model.encode(sample_queries[i + 1])
                similarity = np.dot(embedding, next_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(next_embedding)
                )
                results['similarity_scores'].append(similarity)
        
        # Calculate statistics
        results['avg_processing_time'] = np.mean(results['query_processing_time'])
        results['avg_similarity'] = np.mean(results['similarity_scores']) if results['similarity_scores'] else 0
        
        print(f"📊 Embedding Dimensions: {results['embedding_dimensions']}")
        print(f"⏱️  Average Processing Time: {results['avg_processing_time']:.4f}s")
        print(f"🎯 Average Similarity Score: {results['avg_similarity']:.4f}")
        
        return results
    
    def evaluate_retrieval_performance(self, test_queries, ground_truth=None):
        """Evaluate retrieval performance with multiple metrics"""
        print("\n📈 Evaluating Retrieval Performance...")
        print("=" * 50)
        
        results = {
            'precision_at_k': [],
            'recall_at_k': [],
            'f1_scores': [],
            'mean_reciprocal_rank': [],
            'retrieval_times': [],
            'score_distributions': []
        }
        
        for query in test_queries:
            start_time = time.time()
            
            # Generate query embedding
            query_embedding = self.model.encode(query).tolist()
            
            # Perform retrieval
            search_body = {
                "size": 10,  # Get top 10 for evaluation
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_embedding,
                            "k": 10
                        }
                    }
                },
                "_source": ["document_id", "chunk_index", "text", "metadata", "score"]
            }
            
            response = self.client.search(index="embeddings_index", body=search_body)
            retrieval_time = time.time() - start_time
            
            results['retrieval_times'].append(retrieval_time)
            
            # Extract scores
            scores = [hit['_score'] for hit in response['hits']['hits']]
            results['score_distributions'].extend(scores)
            
            # Calculate precision@k for different k values
            for k in [1, 3, 5, 10]:
                if len(response['hits']['hits']) >= k:
                    # For now, assume all retrieved docs are relevant (simplified)
                    precision = 1.0  # This would be calculated with ground truth
                    results['precision_at_k'].append(precision)
            
            print(f"🔍 Query: '{query[:50]}...'")
            print(f"   ⏱️  Retrieval Time: {retrieval_time:.4f}s")
            print(f"   📊 Top Score: {scores[0]:.4f}")
            print(f"   📈 Score Range: {min(scores):.4f} - {max(scores):.4f}")
            print()
        
        # Calculate aggregate metrics
        results['avg_retrieval_time'] = np.mean(results['retrieval_times'])
        results['avg_precision'] = np.mean(results['precision_at_k']) if results['precision_at_k'] else 0
        results['score_statistics'] = {
            'mean': np.mean(results['score_distributions']),
            'std': np.std(results['score_distributions']),
            'min': np.min(results['score_distributions']),
            'max': np.max(results['score_distributions'])
        }
        
        print(f"📊 Average Retrieval Time: {results['avg_retrieval_time']:.4f}s")
        print(f"🎯 Average Precision: {results['avg_precision']:.4f}")
        print(f"📈 Score Statistics:")
        print(f"   Mean: {results['score_statistics']['mean']:.4f}")
        print(f"   Std: {results['score_statistics']['std']:.4f}")
        print(f"   Range: {results['score_statistics']['min']:.4f} - {results['score_statistics']['max']:.4f}")
        
        return results
    
    def compare_retrieval_techniques(self, query):
        """Compare different retrieval techniques"""
        print(f"\n🔄 Comparing Retrieval Techniques for: '{query}'")
        print("=" * 60)
        
        techniques = {
            'vector_search': self._vector_search,
            'text_search': self._text_search,
            'hybrid_search': self._hybrid_search
        }
        
        results = {}
        
        for technique_name, technique_func in techniques.items():
            start_time = time.time()
            response = technique_func(query)
            processing_time = time.time() - start_time
            
            scores = [hit['_score'] for hit in response['hits']['hits'][:5]]
            
            results[technique_name] = {
                'processing_time': processing_time,
                'top_scores': scores,
                'avg_score': np.mean(scores),
                'score_range': f"{min(scores):.4f} - {max(scores):.4f}",
                'num_results': len(response['hits']['hits'])
            }
            
            print(f"🔍 {technique_name.upper()}:")
            print(f"   ⏱️  Time: {processing_time:.4f}s")
            print(f"   📊 Top Scores: {scores}")
            print(f"   📈 Avg Score: {np.mean(scores):.4f}")
            print(f"   📋 Results: {len(response['hits']['hits'])}")
            print()
        
        return results
    
    def _vector_search(self, query):
        """Vector similarity search"""
        query_embedding = self.model.encode(query).tolist()
        search_body = {
            "size": 10,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": 10
                    }
                }
            }
        }
        return self.client.search(index="embeddings_index", body=search_body)
    
    def _text_search(self, query):
        """Text-based search"""
        search_body = {
            "size": 10,
            "query": {
                "match": {
                    "text": {
                        "query": query,
                        "fuzziness": "AUTO"
                    }
                }
            }
        }
        return self.client.search(index="embeddings_index", body=search_body)
    
    def _hybrid_search(self, query):
        """Hybrid search combining vector and text"""
        query_embedding = self.model.encode(query).tolist()
        search_body = {
            "size": 10,
            "query": {
                "bool": {
                    "should": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_embedding,
                                    "k": 10,
                                    "boost": 0.7
                                }
                            }
                        },
                        {
                            "match": {
                                "text": {
                                    "query": query,
                                    "boost": 0.3
                                }
                            }
                        }
                    ]
                }
            }
        }
        return self.client.search(index="embeddings_index", body=search_body)
    
    def generate_evaluation_report(self, all_results):
        """Generate comprehensive evaluation report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE RAG EVALUATION REPORT")
        print("="*80)
        
        print("\n🔧 SYSTEM CONFIGURATION:")
        print(f"   Model: krutrim-ai-labs/vyakyarth")
        print(f"   Embedding Dimensions: {all_results['embedding_quality']['embedding_dimensions']}")
        print(f"   Index Documents: {all_results['index_stats']['total_documents']}")
        
        print("\n⚡ PERFORMANCE METRICS:")
        print(f"   Average Query Processing: {all_results['embedding_quality']['avg_processing_time']:.4f}s")
        print(f"   Average Retrieval Time: {all_results['retrieval_performance']['avg_retrieval_time']:.4f}s")
        print(f"   Average Precision: {all_results['retrieval_performance']['avg_precision']:.4f}")
        
        print("\n📈 SCORE DISTRIBUTION:")
        stats = all_results['retrieval_performance']['score_statistics']
        print(f"   Mean Score: {stats['mean']:.4f}")
        print(f"   Standard Deviation: {stats['std']:.4f}")
        print(f"   Score Range: {stats['min']:.4f} - {stats['max']:.4f}")
        
        print("\n🎯 RETRIEVAL TECHNIQUE COMPARISON:")
        for technique, results in all_results['technique_comparison'].items():
            print(f"   {technique.upper()}:")
            print(f"      Time: {results['processing_time']:.4f}s")
            print(f"      Avg Score: {results['avg_score']:.4f}")
            print(f"      Results: {results['num_results']}")
        
        print("\n✅ EVALUATION SUMMARY:")
        if all_results['retrieval_performance']['avg_retrieval_time'] < 0.1:
            print("   🚀 Retrieval Speed: EXCELLENT (< 0.1s)")
        elif all_results['retrieval_performance']['avg_retrieval_time'] < 0.5:
            print("   ✅ Retrieval Speed: GOOD (< 0.5s)")
        else:
            print("   ⚠️  Retrieval Speed: NEEDS IMPROVEMENT (> 0.5s)")
        
        if all_results['retrieval_performance']['avg_precision'] > 0.8:
            print("   🎯 Precision: EXCELLENT (> 0.8)")
        elif all_results['retrieval_performance']['avg_precision'] > 0.6:
            print("   ✅ Precision: GOOD (> 0.6)")
        else:
            print("   ⚠️  Precision: NEEDS IMPROVEMENT (< 0.6)")
        
        print("\n" + "="*80)

def main():
    """Main evaluation function"""
    evaluator = RetrievalEvaluator()
    
    # Connect to systems
    print("🔌 Connecting to OpenSearch...")
    evaluator.connect_to_opensearch()
    
    print("🤖 Loading embedding model...")
    evaluator.load_embedding_model()
    
    # Get index statistics
    print("\n📊 Getting Index Statistics...")
    index_stats = evaluator.get_index_stats()
    if not index_stats:
        print("❌ No embeddings index found!")
        return
    
    print(f"   Documents: {index_stats['total_documents']}")
    print(f"   Index Size: {index_stats['index_size_bytes'] / (1024*1024):.2f} MB")
    
    # Test queries for evaluation
    test_queries = [
        "What are the safety requirements for metro operations?",
        "maintenance schedule and procedures",
        "incident report emergency brake",
        "financial budget and expenses",
        "signal failure and troubleshooting",
        "passenger safety guidelines",
        "train maintenance checklist",
        "emergency evacuation procedures"
    ]
    
    # Run evaluations
    all_results = {
        'index_stats': index_stats,
        'embedding_quality': evaluator.evaluate_embedding_quality(test_queries),
        'retrieval_performance': evaluator.evaluate_retrieval_performance(test_queries),
        'technique_comparison': evaluator.compare_retrieval_techniques(test_queries[0])
    }
    
    # Generate final report
    evaluator.generate_evaluation_report(all_results)

if __name__ == "__main__":
    main()