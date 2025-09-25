"""
Language detection utilities
"""
from typing import Optional
from loguru import logger

try:
    from langdetect import detect, DetectorFactory
    LANGDETECT_AVAILABLE = True
    # Set seed for consistent results
    DetectorFactory.seed = 0
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available. Install with: pip install langdetect")


class LanguageDetector:
    """Detects language of text content"""
    
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'ml': 'Malayalam',
            'hi': 'Hindi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'gu': 'Gujarati',
            'bn': 'Bengali',
            'mr': 'Marathi',
            'pa': 'Punjabi'
        }
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of text content
        
        Args:
            text: Text content to analyze
            
        Returns:
            Language code (e.g., 'en', 'ml')
        """
        if not text or not text.strip():
            return 'unknown'
        
        try:
            if LANGDETECT_AVAILABLE:
                # Use langdetect for primary detection
                detected_lang = detect(text)
                
                # Validate detected language
                if detected_lang in self.supported_languages:
                    return detected_lang
                else:
                    # Fallback to English for unsupported languages
                    logger.warning(f"Unsupported language detected: {detected_lang}, defaulting to English")
                    return 'en'
            else:
                # Fallback to simple heuristic detection
                return self._heuristic_detection(text)
                
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}, defaulting to English")
            return 'en'
    
    def _heuristic_detection(self, text: str) -> str:
        """Simple heuristic language detection"""
        # Check for Malayalam characters (Unicode range: 0D00-0D7F)
        malayalam_chars = sum(1 for char in text if '\u0D00' <= char <= '\u0D7F')
        total_chars = len([char for char in text if char.isalpha()])
        
        if total_chars > 0 and malayalam_chars / total_chars > 0.1:
            return 'ml'
        
        # Check for Hindi characters (Unicode range: 0900-097F)
        hindi_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        if total_chars > 0 and hindi_chars / total_chars > 0.1:
            return 'hi'
        
        # Check for Tamil characters (Unicode range: 0B80-0BFF)
        tamil_chars = sum(1 for char in text if '\u0B80' <= char <= '\u0BFF')
        if total_chars > 0 and tamil_chars / total_chars > 0.1:
            return 'ta'
        
        # Default to English
        return 'en'
    
    def get_language_name(self, lang_code: str) -> str:
        """Get full language name from code"""
        return self.supported_languages.get(lang_code, 'Unknown')
    
    def is_indian_language(self, lang_code: str) -> bool:
        """Check if language is an Indian language"""
        indian_languages = {'ml', 'hi', 'ta', 'te', 'kn', 'gu', 'bn', 'mr', 'pa'}
        return lang_code in indian_languages
    
    def needs_translation(self, lang_code: str) -> bool:
        """Check if language needs translation to English"""
        return lang_code != 'en'
