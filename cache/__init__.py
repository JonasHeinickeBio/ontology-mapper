"""
Cache module for ontology mapping tool.
Provides in-memory and persistent caching for API responses.
"""

from .cache_manager import CacheManager
from .cache_config import CacheConfig

__all__ = ['CacheManager', 'CacheConfig']
