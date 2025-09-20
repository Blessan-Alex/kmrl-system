"""
Language Detector for KMRL
Detects English, Malayalam, and mixed language content
"""

import re
from typing import str
import structlog

logger = structlog.get_logger()

class LanguageDetector:
    """Language detector for KMRL documents"""
    
    def __init__(self):
        # Malayalam Unicode ranges
        self.malayalam_pattern = re.compile(r'[\u0D00-\u0D7F]+')
        # English pattern
        self.english_pattern = re.compile(r'[a-zA-Z]+')
    
    def detect_language(self, text: str) -> str:
        """Detect language of text content"""
        try:
            if not text or len(text.strip()) < 5:
                return "unknown"
            
            # Count Malayalam and English characters
            malayalam_chars = len(self.malayalam_pattern.findall(text))
            english_chars = len(self.english_pattern.findall(text))
            
            total_chars = malayalam_chars + english_chars
            
            if total_chars == 0:
                return "unknown"
            
            malayalam_ratio = malayalam_chars / total_chars
            english_ratio = english_chars / total_chars
            
            # Determine language based on ratios
            if malayalam_ratio > 0.7:
                return "malayalam"
            elif english_ratio > 0.7:
                return "english"
            elif malayalam_ratio > 0.3 and english_ratio > 0.3:
                return "mixed"
            else:
                return "unknown"
                
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "unknown"
    
    def has_malayalam(self, text: str) -> bool:
        """Check if text contains Malayalam characters"""
        try:
            return bool(self.malayalam_pattern.search(text))
        except Exception as e:
            logger.error(f"Malayalam detection failed: {e}")
            return False
    
    def has_english(self, text: str) -> bool:
        """Check if text contains English characters"""
        try:
            return bool(self.english_pattern.search(text))
        except Exception as e:
            logger.error(f"English detection failed: {e}")
            return False
