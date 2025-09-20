"""
Embedding Generator for KMRL
Generates embeddings for text chunks using sentence transformers
"""

import os
import numpy as np
from typing import List, np.ndarray
import structlog
from sentence_transformers import SentenceTransformer

logger = structlog.get_logger()

class EmbeddingGenerator:
    """Embedding generator for KMRL documents"""
    
    def __init__(self):
        # Initialize sentence transformer model
        model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        try:
            if not text or len(text.strip()) < 5:
                return np.zeros(self.embedding_dim)
            
            # Generate embedding
            embedding = self.model.encode(text)
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return np.zeros(self.embedding_dim)
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        try:
            if not texts:
                return []
            
            # Generate batch embeddings
            embeddings = self.model.encode(texts)
            
            # Normalize each embedding
            normalized_embeddings = []
            for embedding in embeddings:
                normalized = embedding / np.linalg.norm(embedding)
                normalized_embeddings.append(normalized)
            
            return normalized_embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            return [np.zeros(self.embedding_dim) for _ in texts]
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            similarity = np.dot(embedding1, embedding2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
