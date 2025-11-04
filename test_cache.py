#!/usr/bin/env python3
"""
Test script for caching functionality
"""

import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from cache import CacheManager, CacheConfig


def test_cache_config():
    """Test cache configuration"""
    print("Testing cache configuration...")
    config = CacheConfig()
    print(f"  Config: {config}")
    assert config.enabled == True
    assert config.ttl > 0
    print("✓ Cache configuration test passed")


def test_cache_basic_operations():
    """Test basic cache operations"""
    print("\nTesting basic cache operations...")
    
    config = CacheConfig()
    config.persistent = False  # Use only memory cache for testing
    cache = CacheManager(config)
    
    # Test set and get
    test_data = [{'uri': 'http://test.org/1', 'label': 'Test 1'}]
    cache.set('test query', 'HP,NCIT', 'bioportal', test_data)
    result = cache.get('test query', 'HP,NCIT', 'bioportal')
    assert result is not None
    assert len(result) == 1
    assert result[0]['label'] == 'Test 1'
    print("✓ Set and get test passed")
    
    # Test cache hit
    result2 = cache.get('test query', 'HP,NCIT', 'bioportal')
    assert result2 is not None
    stats = cache.get_stats()
    assert stats['hits'] >= 1
    print("✓ Cache hit test passed")
    
    # Test cache miss
    result3 = cache.get('nonexistent', 'HP', 'bioportal')
    assert result3 is None
    stats = cache.get_stats()
    assert stats['misses'] >= 1
    print("✓ Cache miss test passed")
    
    # Test delete
    deleted = cache.delete('test query', 'HP,NCIT', 'bioportal')
    assert deleted == True
    result4 = cache.get('test query', 'HP,NCIT', 'bioportal')
    assert result4 is None
    print("✓ Delete test passed")


def test_cache_key_generation():
    """Test cache key generation"""
    print("\nTesting cache key generation...")
    
    config = CacheConfig()
    config.persistent = False
    cache = CacheManager(config)
    
    # Same query should produce same key
    test_data = [{'uri': 'http://test.org/1', 'label': 'Test'}]
    cache.set('cancer', 'MONDO,HP', 'bioportal', test_data)
    
    # Case-insensitive and whitespace normalized
    result1 = cache.get('cancer', 'MONDO,HP', 'bioportal')
    result2 = cache.get('CANCER', 'mondo,hp', 'bioportal')
    result3 = cache.get('  cancer  ', '  MONDO,HP  ', 'bioportal')
    
    assert result1 is not None
    assert result2 is not None
    assert result3 is not None
    print("✓ Cache key normalization test passed")


def test_cache_ttl():
    """Test cache TTL expiration"""
    print("\nTesting cache TTL expiration...")
    
    config = CacheConfig()
    config.persistent = False
    config.ttl = 1  # 1 second TTL
    cache = CacheManager(config)
    
    test_data = [{'uri': 'http://test.org/1', 'label': 'Test'}]
    cache.set('expiring', 'HP', 'bioportal', test_data)
    
    # Should be available immediately
    result1 = cache.get('expiring', 'HP', 'bioportal')
    assert result1 is not None
    print("✓ Cache entry available immediately")
    
    # Wait for expiration
    print("  Waiting 2 seconds for TTL expiration...")
    time.sleep(2)
    
    # Should be expired
    result2 = cache.get('expiring', 'HP', 'bioportal')
    assert result2 is None
    print("✓ Cache entry expired after TTL")


def test_cache_clear():
    """Test cache clear operation"""
    print("\nTesting cache clear...")
    
    config = CacheConfig()
    config.persistent = False
    cache = CacheManager(config)
    
    # Add multiple entries
    for i in range(5):
        test_data = [{'uri': f'http://test.org/{i}', 'label': f'Test {i}'}]
        cache.set(f'query{i}', 'HP', 'bioportal', test_data)
    
    # Clear all
    count = cache.clear()
    assert count == 5
    
    # Verify all cleared
    for i in range(5):
        result = cache.get(f'query{i}', 'HP', 'bioportal')
        assert result is None
    
    print("✓ Cache clear test passed")


def test_cache_stats():
    """Test cache statistics"""
    print("\nTesting cache statistics...")
    
    config = CacheConfig()
    config.persistent = False
    cache = CacheManager(config)
    
    test_data = [{'uri': 'http://test.org/1', 'label': 'Test'}]
    
    # Perform various operations
    cache.set('query1', 'HP', 'bioportal', test_data)
    cache.get('query1', 'HP', 'bioportal')  # hit
    cache.get('nonexistent', 'HP', 'bioportal')  # miss
    cache.delete('query1', 'HP', 'bioportal')
    
    stats = cache.get_stats()
    assert stats['hits'] >= 1
    assert stats['misses'] >= 1
    assert stats['sets'] >= 1
    assert stats['deletes'] >= 1
    assert stats['enabled'] == True
    
    print(f"  Stats: {stats}")
    print("✓ Cache statistics test passed")


def main():
    print("Testing Cache Functionality...")
    print("=" * 50)
    
    try:
        test_cache_config()
        test_cache_basic_operations()
        test_cache_key_generation()
        test_cache_ttl()
        test_cache_clear()
        test_cache_stats()
        
        print("\n" + "=" * 50)
        print("✅ All cache tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
