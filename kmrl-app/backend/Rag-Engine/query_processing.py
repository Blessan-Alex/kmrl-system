# Query Processing with OpenSearch Integration

import logging
from typing import List, Tuple, Dict, Any, Optional
from query_to_embedding import query_to_embedding, normalize_vector
import numpy as np
from sklearn.neighbors import NearestNeighbors
from opensearch_query_processor import OpenSearchQueryProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    Args:
        vec1 (List[float]): First vector.
        vec2 (List[float]): Second vector.

    Returns:
        float: Cosine similarity score.

    Raises:
        ValueError: If vectors are not the same length or are zero vectors.
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must be of the same length.")
    # Normalize vectors before similarity
    vec1 = normalize_vector(vec1)
    vec2 = normalize_vector(vec2)
    return float(np.dot(vec1, vec2))

def vector_similarity_search(
    query_embedding: List[float],
    doc_embeddings: List[List[float]],
    top_k: int = 3
) -> List[Tuple[int, float]]:
    """
    Find the top_k most similar document embeddings to the query embedding.

    Args:
        query_embedding (List[float]): Embedding vector for the query.
        doc_embeddings (List[List[float]]): List of embedding vectors for documents.
        top_k (int): Number of top similar documents to return.

    Returns:
        List[Tuple[int, float]]: Each tuple is (index, similarity_score).

    Raises:
        ValueError: If doc_embeddings is empty.
    """
    if not doc_embeddings:
        raise ValueError("Document embeddings list is empty.")
    similarities = [
        (idx, cosine_similarity(query_embedding, doc_emb))
        for idx, doc_emb in enumerate(doc_embeddings)
    ]
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]

def knn_vector_similarity_search(
    query_embedding: List[float],
    doc_embeddings: List[List[float]],
    top_k: int = 3
) -> List[Tuple[int, float]]:
    """
    Optimized KNN search to find the top_k most similar document embeddings to the query embedding.

    Args:
        query_embedding (List[float]): Embedding vector for the query.
        doc_embeddings (List[List[float]]): List of embedding vectors for documents.
        top_k (int): Number of top similar documents to return.

    Returns:
        List[Tuple[int, float]]: Each tuple is (index, similarity_score).

    Raises:
        ValueError: If doc_embeddings is empty.
    """
    if not doc_embeddings:
        raise ValueError("Document embeddings list is empty.")
    # Normalize all embeddings
    doc_matrix = np.array([normalize_vector(vec) for vec in doc_embeddings])
    query_vec = normalize_vector(query_embedding)
    # Use sklearn NearestNeighbors for cosine similarity (metric='cosine')
    # Note: cosine distance = 1 - cosine similarity
    nbrs = NearestNeighbors(n_neighbors=top_k, metric='cosine').fit(doc_matrix)
    distances, indices = nbrs.kneighbors([query_vec])
    similarities = [(int(idx), 1 - float(dist)) for idx, dist in zip(indices[0], distances[0])]
    return similarities

# Note: The current implementation of vector_similarity_search is NOT using a true k-nearest neighbors (KNN) algorithm or library.
# It computes cosine similarity between the query and all document embeddings, sorts them, and returns the top_k most similar.
# This is a brute-force search, not an optimized KNN search (like with FAISS, Annoy, or sklearn's NearestNeighbors).

def opensearch_similarity_search(
    query: str,
    opensearch_host: str = "localhost",
    opensearch_port: int = 9200,
    index_name: str = "embeddings_index",
    top_k: int = 5,
    department: Optional[str] = None,
    search_type: str = "vector"
) -> List[Dict[str, Any]]:
    """
    Search for similar documents using OpenSearch.
    
    Args:
        query: Natural language query
        opensearch_host: OpenSearch host
        opensearch_port: OpenSearch port
        index_name: Name of the index containing embeddings
        top_k: Number of results to return
        department: Optional department filter
        search_type: Type of search ("vector", "text", "hybrid")
        
    Returns:
        List of search results with metadata
    """
    try:
        # Initialize OpenSearch query processor
        processor = OpenSearchQueryProcessor(
            opensearch_host=opensearch_host,
            opensearch_port=opensearch_port,
            index_name=index_name
        )
        
        # Perform search based on type
        if search_type == "vector":
            results = processor.search_by_query_text(query, size=top_k, department=department)
        elif search_type == "text":
            results = processor.search_by_text(query, size=top_k, department=department)
        elif search_type == "hybrid":
            results = processor.hybrid_search(query, size=top_k, department=department)
        else:
            raise ValueError(f"Invalid search type: {search_type}")
        
        logging.info(f"Found {len(results)} results for query: '{query}'")
        return results
        
    except Exception as e:
        logging.error(f"OpenSearch search failed: {e}")
        return []


def display_opensearch_results(results: List[Dict[str, Any]], query: str):
    """Display OpenSearch results in a readable format"""
    print(f"\n🔍 Search Results for: '{query}'")
    print("=" * 60)
    
    if not results:
        print("No results found.")
        return
    
    print(f"Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. Document: {result['document_id']} (Chunk {result['chunk_index']})")
        print(f"   Similarity Score: {result['similarity_score']:.4f}")
        print(f"   Department: {result['metadata'].get('department', 'Unknown')}")
        print(f"   Source: {result['metadata'].get('source', 'Unknown')}")
        print(f"   Text: {result['text'][:200]}...")
        print("-" * 60)


if __name__ == "__main__":
    try:
        print("🚀 OpenSearch Query Processing")
        print("=" * 40)
        
        # Get query from user
        query = input("Enter your query: ").strip()
        if not query:
            logging.error("Query cannot be empty.")
            exit(1)
        
        # Get search preferences
        print("\nSearch Options:")
        print("1. Vector search (semantic similarity)")
        print("2. Text search (keyword matching)")
        print("3. Hybrid search (vector + text)")
        
        search_choice = input("Choose search type (1-3, default=1): ").strip() or "1"
        search_types = {"1": "vector", "2": "text", "3": "hybrid"}
        search_type = search_types.get(search_choice, "vector")
        
        # Optional department filter
        department = input("Enter department filter (optional, press Enter to skip): ").strip() or None
        
        # Get number of results
        try:
            top_k = int(input("Number of results (default=5): ").strip() or "5")
        except ValueError:
            top_k = 5
        
        # Perform search
        results = opensearch_similarity_search(
            query=query,
            top_k=top_k,
            department=department,
            search_type=search_type
        )
        
        # Display results
        display_opensearch_results(results, query)
        
        # Show additional info
        if results:
            print(f"\n📊 Search Summary:")
            print(f"   Query: '{query}'")
            print(f"   Search Type: {search_type}")
            print(f"   Results Found: {len(results)}")
            if department:
                print(f"   Department Filter: {department}")
            print(f"   Best Match Score: {results[0]['similarity_score']:.4f}")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        print(f"Error: {e}")