"""
Shared utilities for KMRL system
"""

import sys
import os

# Ensure backend root is in the path for all modules (highest priority)
backend_root = os.path.dirname(os.path.dirname(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Ensure Document_Extraction is in the path for all modules (lower priority)
document_extraction_path = os.path.join(os.path.dirname(__file__), '..', 'Document_Extraction')
if document_extraction_path not in sys.path:
    sys.path.insert(1, document_extraction_path)  # Insert at position 1, not 0
