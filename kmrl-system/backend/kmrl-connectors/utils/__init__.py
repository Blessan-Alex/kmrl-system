"""
Utilities Package
=================

Utility classes and functions for KMRL connectors.

This package provides:
- CredentialsManager: Secure credential management
- Common utilities and helper functions

Usage:
    from kmrl_connectors.utils import CredentialsManager
"""

from .credentials_manager import CredentialsManager

__all__ = [
    'CredentialsManager',
]
