"""
Text Chunker for KMRL
Handles document chunking for RAG pipeline
"""

import re
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()

class TextChunker:
    """Text chunker for KMRL documents"""
    
    def __init__(self):
        self.chunk_size = 1000  # characters
        self.chunk_overlap = 200  # characters
    
    def chunk_text(self, text: str, language: str = "english") -> List[Dict[str, Any]]:
        """Chunk text into smaller pieces for RAG"""
        try:
            if not text or len(text.strip()) < 50:
                return [{"text": text, "type": "text", "index": 0}]
            
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            # Split into sentences
            sentences = self._split_into_sentences(cleaned_text, language)
            
            # Create chunks
            chunks = []
            current_chunk = ""
            chunk_index = 0
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= self.chunk_size:
                    current_chunk += sentence + " "
                else:
                    if current_chunk.strip():
                        chunks.append({
                            "text": current_chunk.strip(),
                            "type": "text",
                            "index": chunk_index
                        })
                        chunk_index += 1
                    
                    current_chunk = sentence + " "
            
            # Add final chunk
            if current_chunk.strip():
                chunks.append({
                    "text": current_chunk.strip(),
                    "type": "text",
                    "index": chunk_index
                })
            
            logger.info(f"Created {len(chunks)} chunks from text")
            return chunks
            
        except Exception as e:
            logger.error(f"Text chunking failed: {e}")
            return [{"text": text, "type": "text", "index": 0}]
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep Malayalam
        text = re.sub(r'[^\w\s\u0D00-\u0D7F]', ' ', text)
        return text.strip()
    
    def _split_into_sentences(self, text: str, language: str) -> List[str]:
        """Split text into sentences"""
        if language == "malayalam":
            # Malayalam sentence splitting
            sentences = re.split(r'[.!?]', text)
        else:
            # English sentence splitting
            sentences = re.split(r'[.!?]', text)
        
        return [s.strip() for s in sentences if s.strip()]
