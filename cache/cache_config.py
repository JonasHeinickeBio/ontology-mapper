"""
Configuration for the caching mechanism.
"""

import os
from typing import Optional


class CacheConfig:
    """Configuration for cache behavior"""
    
    def __init__(self):
        # Cache enabled by default
        self.enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        
        # Default TTL: 24 hours (in seconds)
        self.ttl = int(os.getenv('CACHE_TTL', '86400'))
        
        # Cache directory for persistent storage
        self.cache_dir = os.getenv('CACHE_DIR', os.path.join(os.path.expanduser('~'), '.ontology_mapper_cache'))
        
        # Max cache size in MB (0 = unlimited)
        self.max_size_mb = int(os.getenv('CACHE_MAX_SIZE_MB', '100'))
        
        # Whether to use persistent cache (file-based)
        self.persistent = os.getenv('CACHE_PERSISTENT', 'true').lower() == 'true'
        
    def __repr__(self):
        return (f"CacheConfig(enabled={self.enabled}, ttl={self.ttl}s, "
                f"persistent={self.persistent}, dir={self.cache_dir}, "
                f"max_size={self.max_size_mb}MB)")
