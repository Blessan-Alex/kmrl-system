"""
Similarity Calculator for KMRL
Calculates similarity between text content and keywords
"""

import re
from typing import List, str
import structlog
from sentence_transformers import SentenceTransformer
import numpy as np

logger = structlog.get_logger()

class SimilarityCalculator:
    """Similarity calculator for KMRL notifications"""
    
    def __init__(self):
        # Initialize sentence transformer for semantic similarity
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def calculate_similarity(self, text: str, keywords: List[str]) -> float:
        """Calculate similarity between text and keywords"""
        try:
            if not text or not keywords:
                return 0.0
            
            # Generate embeddings
            text_embedding = self.model.encode(text)
            keywords_embedding = self.model.encode(' '.join(keywords))
            
            # Calculate cosine similarity
            similarity = np.dot(text_embedding, keywords_embedding) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(keywords_embedding)
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def calculate_keyword_similarity(self, text: str, keywords: List[str]) -> float:
        """Calculate keyword-based similarity"""
        try:
            if not text or not keywords:
                return 0.0
            
            text_lower = text.lower()
            matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            
            # Calculate ratio of matches
            similarity = matches / len(keywords)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Keyword similarity calculation failed: {e}")
            return 0.0
    
    def calculate_combined_similarity(self, text: str, keywords: List[str]) -> float:
        """Calculate combined semantic and keyword similarity"""
        try:
            semantic_similarity = self.calculate_similarity(text, keywords)
            keyword_similarity = self.calculate_keyword_similarity(text, keywords)
            
            # Weighted combination (70% semantic, 30% keyword)
            combined_similarity = 0.7 * semantic_similarity + 0.3 * keyword_similarity
            
            return combined_similarity
            
        except Exception as e:
            logger.error(f"Combined similarity calculation failed: {e}")
            return 0.0
