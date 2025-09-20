"""
Base Connector Package
=====================

Base classes and utilities for KMRL data source connectors.

This package provides:
- BaseConnector: Abstract base class for all connectors
- Document: Unified document model
- Common utilities and patterns

Usage:
    from kmrl_connectors.base import BaseConnector, Document
"""

from .base_connector import BaseConnector, Document

__all__ = [
    'BaseConnector',
    'Document',
]
