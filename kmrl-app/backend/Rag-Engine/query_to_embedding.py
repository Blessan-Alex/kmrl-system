# query_to_embedding

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

# Global model variable - will be loaded on first use
_model = None

def get_model():
    """Lazy load the embedding model"""
    global _model
    if _model is None:
        _model = SentenceTransformer('krutrim-ai-labs/vyakyarth')
    return _model

def query_to_embedding(query: str) -> List[float]:
    """
    Converts a text query to an embedding vector.
    Args:
        query (str): The input query string.
    Returns:
        list: Embedding vector as a list of floats.
    Raises:
        ValueError: If the query is empty or not a string.
    """
    try:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")
        model = get_model()
        embedding = model.encode(query)
        return embedding.tolist()
    except Exception as e:
        raise RuntimeError(f"Failed to generate embedding: {e}")

def normalize_vector(vec: List[float]) -> np.ndarray:
    """Normalize a vector to unit length."""
    try:
        vec = np.array(vec)
        norm = np.linalg.norm(vec)
        if norm == 0:
            raise ValueError("Cannot normalize a zero vector.")
        return vec / norm
    except Exception as e:
        raise RuntimeError(f"Failed to normalize vector: {e}")

if __name__ == "__main__":
    try:
        query = input("Enter your query: ").strip()
        if not query:
            print("Query cannot be empty.")
            exit(1)
        embedding = query_to_embedding(query)
        print(f"Embedding vector length: {len(embedding)}")
        
        # Example usage for vector similarity search
        # Dummy document embeddings for demonstration
        doc_embeddings = [
            query_to_embedding("Metro train schedule update"),
            query_to_embedding("Safety compliance report"),
            query_to_embedding("Procurement contract details"),
        ]
        #results = vector_similarity_search(embedding, doc_embeddings, top_k=2)
        #print("Top similar documents (index, similarity):", results)
    except Exception as e:
        print(f"Error: {e}")