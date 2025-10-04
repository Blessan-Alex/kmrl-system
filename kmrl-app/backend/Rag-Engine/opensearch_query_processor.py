# OpenSearch Query Processor
# Integrates with OpenSearch for vector similarity search

import logging
from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch
from query_to_embedding import query_to_embedding
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

class OpenSearchQueryProcessor:
    """Query processor that uses OpenSearch for vector similarity search"""
    
    def __init__(self, 
                 opensearch_host: str = "localhost",
                 opensearch_port: int = 9200,
                 index_name: str = "embeddings_index",
                 use_ssl: bool = False):
        """
        Initialize OpenSearch query processor
        
        Args:
            opensearch_host: OpenSearch host
            opensearch_port: OpenSearch port
            index_name: Name of the index containing embeddings
            use_ssl: Whether to use SSL connection
        """
        self.index_name = index_name
        self.client = self._connect_to_opensearch(opensearch_host, opensearch_port, use_ssl)
        
    def _connect_to_opensearch(self, host: str, port: int, use_ssl: bool) -> OpenSearch:
        """Connect to OpenSearch cluster"""
        try:
            client = OpenSearch(
                hosts=[{'host': host, 'port': port}],
                http_compress=True,
                use_ssl=use_ssl,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
            )
            # Test connection
            client.info()
            logging.info(f"Connected to OpenSearch at {host}:{port}")
            return client
        except Exception as e:
            logging.error(f"Failed to connect to OpenSearch: {e}")
            raise
    
    def search_by_text(self, query_text: str, size: int = 5, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search documents by text content using OpenSearch text search
        
        Args:
            query_text: Text query to search for
            size: Number of results to return
            department: Optional department filter
            
        Returns:
            List of search results with metadata
        """
        try:
            search_body = {
                "size": size,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "text": {
                                        "query": query_text,
                                        "fuzziness": "AUTO"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            
            # Add department filter if specified
            if department:
                search_body["query"]["bool"]["filter"] = {
                    "term": {"metadata.department": department}
                }
            
            response = self.client.search(index=self.index_name, body=search_body)
            return self._format_search_results(response)
            
        except Exception as e:
            logging.error(f"Text search failed: {e}")
            return []
    
    def search_by_embedding(self, query_embedding: List[float], size: int = 5, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search documents by embedding vector using k-NN search
        
        Args:
            query_embedding: Query embedding vector
            size: Number of results to return
            department: Optional department filter
            
        Returns:
            List of search results with metadata
        """
        try:
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
            
            # Add department filter if specified
            if department:
                search_body["query"]["knn"]["filter"] = {
                    "term": {"metadata.department": department}
                }
            
            response = self.client.search(index=self.index_name, body=search_body)
            return self._format_search_results(response)
            
        except Exception as e:
            logging.error(f"Vector search failed: {e}")
            return []
    
    def search_by_query_text(self, query_text: str, size: int = 5, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search documents by converting query text to embedding and performing vector search
        
        Args:
            query_text: Natural language query
            size: Number of results to return
            department: Optional department filter
            
        Returns:
            List of search results with metadata
        """
        try:
            # Convert query text to embedding
            query_embedding = query_to_embedding(query_text)
            logging.info(f"Generated embedding for query: '{query_text}'")
            
            # Perform vector search
            return self.search_by_embedding(query_embedding, size, department)
            
        except Exception as e:
            logging.error(f"Query text search failed: {e}")
            return []
    
    def hybrid_search(self, query_text: str, size: int = 5, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining text and vector search
        
        Args:
            query_text: Natural language query
            size: Number of results to return
            department: Optional department filter
            
        Returns:
            List of search results with metadata
        """
        try:
            # Convert query text to embedding
            query_embedding = query_to_embedding(query_text)
            
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
            
            # Add department filter if specified
            if department:
                search_body["query"]["bool"]["filter"] = {
                    "term": {"metadata.department": department}
                }
            
            response = self.client.search(index=self.index_name, body=search_body)
            return self._format_search_results(response)
            
        except Exception as e:
            logging.error(f"Hybrid search failed: {e}")
            return []
    
    def _format_search_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format OpenSearch response into standardized results"""
        results = []
        
        for hit in response['hits']['hits']:
            source = hit['_source']
            result = {
                'document_id': source.get('document_id'),
                'chunk_index': source.get('chunk_index'),
                'text': source.get('text'),
                'similarity_score': hit['_score'],
                'metadata': source.get('metadata', {}),
                'opensearch_id': hit['_id']
            }
            results.append(result)
        
        return results
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the embeddings index"""
        try:
            stats = self.client.indices.stats(index=self.index_name)
            doc_count = stats['indices'][self.index_name]['total']['docs']['count']
            
            # Get sample document structure
            search_body = {"size": 1, "query": {"match_all": {}}}
            response = self.client.search(index=self.index_name, body=search_body)
            
            sample_doc = None
            if response['hits']['hits']:
                sample_doc = response['hits']['hits'][0]['_source']
            
            return {
                'total_documents': doc_count,
                'index_name': self.index_name,
                'sample_document': sample_doc
            }
            
        except Exception as e:
            logging.error(f"Failed to get index stats: {e}")
            return {}
    
    def search_departments(self) -> List[str]:
        """Get list of available departments in the index"""
        try:
            search_body = {
                "size": 0,
                "aggs": {
                    "departments": {
                        "terms": {
                            "field": "metadata.department",
                            "size": 100
                        }
                    }
                }
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            departments = [bucket['key'] for bucket in response['aggregations']['departments']['buckets']]
            return departments
            
        except Exception as e:
            logging.error(f"Failed to get departments: {e}")
            return []


def main():
    """Interactive query interface"""
    try:
        # Initialize query processor
        processor = OpenSearchQueryProcessor()
        
        # Get index stats
        stats = processor.get_index_stats()
        print(f"📊 Index Stats:")
        print(f"   Total documents: {stats.get('total_documents', 'Unknown')}")
        print(f"   Index name: {stats.get('index_name', 'Unknown')}")
        
        # Get available departments
        departments = processor.search_departments()
        if departments:
            print(f"   Available departments: {', '.join(departments)}")
        
        print("\n🔍 OpenSearch Query Interface")
        print("=" * 50)
        
        while True:
            print("\nSearch Options:")
            print("1. Search by text (text search)")
            print("2. Search by query (vector search)")
            print("3. Hybrid search (text + vector)")
            print("4. Search by department")
            print("5. Show index stats")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                query = input("Enter search text: ").strip()
                if query:
                    dept = input("Enter department (optional, press Enter to skip): ").strip() or None
                    results = processor.search_by_text(query, size=5, department=dept)
                    display_results(results, "Text Search")
            
            elif choice == "2":
                query = input("Enter your query: ").strip()
                if query:
                    dept = input("Enter department (optional, press Enter to skip): ").strip() or None
                    results = processor.search_by_query_text(query, size=5, department=dept)
                    display_results(results, "Vector Search")
            
            elif choice == "3":
                query = input("Enter your query: ").strip()
                if query:
                    dept = input("Enter department (optional, press Enter to skip): ").strip() or None
                    results = processor.hybrid_search(query, size=5, department=dept)
                    display_results(results, "Hybrid Search")
            
            elif choice == "4":
                if departments:
                    print(f"Available departments: {', '.join(departments)}")
                    dept = input("Enter department: ").strip()
                    if dept:
                        results = processor.search_by_text("", size=10, department=dept)
                        display_results(results, f"Department: {dept}")
                else:
                    print("No departments found in index")
            
            elif choice == "5":
                stats = processor.get_index_stats()
                print(f"\n📊 Index Statistics:")
                print(f"   Total documents: {stats.get('total_documents', 'Unknown')}")
                print(f"   Index name: {stats.get('index_name', 'Unknown')}")
                
                sample = stats.get('sample_document')
                if sample:
                    print(f"   Sample document ID: {sample.get('document_id', 'Unknown')}")
                    print(f"   Sample text: {sample.get('text', '')[:100]}...")
                    print(f"   Embedding dimension: {len(sample.get('embedding', []))}")
            
            elif choice == "6":
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please try again.")
                
    except Exception as e:
        logging.error(f"Query interface failed: {e}")
        print(f"Error: {e}")


def display_results(results: List[Dict[str, Any]], search_type: str):
    """Display search results in a readable format"""
    print(f"\n{search_type} Results:")
    print("=" * 50)
    
    if not results:
        print("No results found.")
        return
    
    print(f"Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. Document: {result['document_id']} (Chunk {result['chunk_index']})")
        print(f"   Score: {result['similarity_score']:.4f}")
        print(f"   Department: {result['metadata'].get('department', 'Unknown')}")
        print(f"   Text: {result['text'][:150]}...")
        print("-" * 50)


if __name__ == "__main__":
    main()
