"""
Cache manager for ontology API responses.
Provides both in-memory and persistent caching with TTL support.
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from pathlib import Path


class CacheManager:
    """Manages caching for API responses with in-memory and persistent storage"""
    
    def __init__(self, config):
        """Initialize cache manager with configuration
        
        Args:
            config: CacheConfig instance with cache settings
        """
        self.config = config
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        
        # Create cache directory if persistent cache is enabled
        if self.config.persistent and self.config.enabled:
            try:
                Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"⚠️  Warning: Could not create cache directory: {e}")
                self.config.persistent = False
    
    def _generate_key(self, query: str, ontologies: str, service: str) -> str:
        """Generate a cache key from query parameters
        
        Args:
            query: Search query string
            ontologies: Comma-separated ontology list
            service: Service name (bioportal/ols)
            
        Returns:
            SHA256 hash of the combined parameters
        """
        # Normalize inputs for consistent hashing
        normalized = f"{query.lower().strip()}|{ontologies.upper().strip()}|{service.lower()}"
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def _get_cache_file_path(self, key: str) -> str:
        """Get the file path for a cache key
        
        Args:
            key: Cache key
            
        Returns:
            Full path to the cache file
        """
        return os.path.join(self.config.cache_dir, f"{key}.json")
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cached entry has expired
        
        Args:
            timestamp: Unix timestamp when the entry was cached
            
        Returns:
            True if expired, False otherwise
        """
        if self.config.ttl == 0:  # 0 means no expiration
            return False
        return time.time() - timestamp > self.config.ttl
    
    def get(self, query: str, ontologies: str, service: str) -> Optional[List[Dict]]:
        """Get cached results for a query
        
        Args:
            query: Search query string
            ontologies: Comma-separated ontology list
            service: Service name (bioportal/ols)
            
        Returns:
            Cached results or None if not found/expired
        """
        if not self.config.enabled:
            return None
        
        key = self._generate_key(query, ontologies, service)
        
        # Try memory cache first
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if not self._is_expired(entry['timestamp']):
                self.stats['hits'] += 1
                return entry['data']
            else:
                # Remove expired entry
                del self.memory_cache[key]
        
        # Try persistent cache
        if self.config.persistent:
            try:
                cache_file = self._get_cache_file_path(key)
                if os.path.exists(cache_file):
                    with open(cache_file, 'r') as f:
                        entry = json.load(f)
                    
                    if not self._is_expired(entry['timestamp']):
                        # Load into memory cache
                        self.memory_cache[key] = entry
                        self.stats['hits'] += 1
                        return entry['data']
                    else:
                        # Remove expired file
                        os.remove(cache_file)
            except Exception as e:
                self.stats['errors'] += 1
                # Silently fail and treat as cache miss
        
        self.stats['misses'] += 1
        return None
    
    def set(self, query: str, ontologies: str, service: str, data: List[Dict]) -> bool:
        """Cache results for a query
        
        Args:
            query: Search query string
            ontologies: Comma-separated ontology list
            service: Service name (bioportal/ols)
            data: Results to cache
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self.config.enabled:
            return False
        
        key = self._generate_key(query, ontologies, service)
        entry = {
            'timestamp': time.time(),
            'data': data,
            'query': query,
            'ontologies': ontologies,
            'service': service
        }
        
        # Store in memory cache
        self.memory_cache[key] = entry
        
        # Store in persistent cache
        if self.config.persistent:
            try:
                cache_file = self._get_cache_file_path(key)
                with open(cache_file, 'w') as f:
                    json.dump(entry, f)
                
                # Check cache size and cleanup if needed
                self._cleanup_if_needed()
            except Exception as e:
                self.stats['errors'] += 1
                # Continue even if persistent cache fails
        
        self.stats['sets'] += 1
        return True
    
    def delete(self, query: str, ontologies: str, service: str) -> bool:
        """Delete cached results for a query
        
        Args:
            query: Search query string
            ontologies: Comma-separated ontology list
            service: Service name (bioportal/ols)
            
        Returns:
            True if deleted, False if not found
        """
        if not self.config.enabled:
            return False
        
        key = self._generate_key(query, ontologies, service)
        deleted = False
        
        # Remove from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
            deleted = True
        
        # Remove from persistent cache
        if self.config.persistent:
            try:
                cache_file = self._get_cache_file_path(key)
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    deleted = True
            except Exception as e:
                self.stats['errors'] += 1
        
        if deleted:
            self.stats['deletes'] += 1
        
        return deleted
    
    def clear(self) -> int:
        """Clear all cached data
        
        Returns:
            Number of entries cleared
        """
        count = 0
        
        # Clear memory cache
        count += len(self.memory_cache)
        self.memory_cache.clear()
        
        # Clear persistent cache
        if self.config.persistent and os.path.exists(self.config.cache_dir):
            try:
                for filename in os.listdir(self.config.cache_dir):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(self.config.cache_dir, filename))
                        count += 1
            except Exception as e:
                self.stats['errors'] += 1
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'enabled': self.config.enabled,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.1f}%",
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'errors': self.stats['errors'],
            'memory_entries': len(self.memory_cache),
            'persistent_enabled': self.config.persistent,
            'ttl_seconds': self.config.ttl
        }
    
    def _cleanup_if_needed(self):
        """Clean up old cache files if size limit is exceeded"""
        if not self.config.persistent or self.config.max_size_mb == 0:
            return
        
        try:
            cache_dir = Path(self.config.cache_dir)
            if not cache_dir.exists():
                return
            
            # Calculate total size
            total_size = sum(f.stat().st_size for f in cache_dir.glob('*.json'))
            max_size_bytes = self.config.max_size_mb * 1024 * 1024
            
            if total_size > max_size_bytes:
                # Remove oldest files until under limit
                files = sorted(cache_dir.glob('*.json'), key=lambda f: f.stat().st_mtime)
                for file in files:
                    if total_size <= max_size_bytes:
                        break
                    file_size = file.stat().st_size
                    file.unlink()
                    total_size -= file_size
        except Exception as e:
            self.stats['errors'] += 1
