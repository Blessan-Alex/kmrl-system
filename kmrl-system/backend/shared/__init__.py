"""
Shared Libraries Package
========================

Common libraries and utilities for KMRL Knowledge Hub.

This package provides:
- Document processing utilities
- Language detection
- Department classification
- Notification management
- Similarity calculation
- Text processing

Usage:
    from shared import DocumentProcessor, LanguageDetector
"""

from .document_processor import DocumentProcessor
from .language_detector import LanguageDetector
from .department_classifier import DepartmentClassifier
from .text_chunker import TextChunker
from .embedding_generator import EmbeddingGenerator
from .notification_engine import NotificationEngine
from .stakeholder_manager import StakeholderManager
from .similarity_calculator import SimilarityCalculator

__all__ = [
    'DocumentProcessor',
    'LanguageDetector',
    'DepartmentClassifier',
    'TextChunker',
    'EmbeddingGenerator',
    'NotificationEngine',
    'StakeholderManager',
    'SimilarityCalculator',
]
