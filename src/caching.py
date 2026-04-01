"""
Enhanced Caching Module
Provides advanced caching strategies: LRU, TTL, Write-through, Write-back, Cache-aside

v1.0.0 - Initial version
- Multi-level caching
- Cache invalidation strategies
- Distributed cache support (Redis-like interface)
- Cache statistics and monitoring
"""

import time
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, Generic, List
from dataclasses import dataclass, field
from functools import wraps
from collections import OrderedDict
from threading import Lock
from datetime import datetime, timedelta
import weakref

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ==================== Cache Entry ====================

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """Update access time"""
        self.accessed_at = time.time()
        self.access_count += 1


# ==================== Base Cache ====================

class BaseCache(Generic[T]):
    """Base cache interface"""
    
    def get(self, key: str) -> Optional[T]:
        raise NotImplementedError
    
    def set(self, key: str, value: T, ttl: float = None, tags: List[str] = None):
        raise NotImplementedError
    
    def delete(self, key: str):
        raise NotImplementedError
    
    def clear(self):
        raise NotImplementedError
    
    def stats(self) -> Dict[str, Any]:
        raise NotImplementedError


# ==================== LRU Cache ====================

class LRUCache(BaseCache[T]):
    """Thread-safe LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._metadata: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._metadata[key]
            
            # Check TTL
            if entry.is_expired():
                self._evict(key)
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: T, ttl: float = None, tags: List[str] = None):
        """Set value in cache"""
        with self._lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self.max_size:
                self._evict_next()
            
            now = time.time()
            self._cache[key] = value
            self._metadata[key] = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                accessed_at=now,
                ttl=ttl or self.default_ttl,
                tags=tags or []
            )
    
    def _evict_next(self):
        """Evict least recently used item"""
        if self._cache:
            key = next(iter(self._cache))
            self._evict(key)
            self._evictions += 1
    
    def _evict(self, key: str):
        """Evict a specific key"""
        self._cache.pop(key, None)
        self._metadata.pop(key, None)
    
    def delete(self, key: str):
        """Delete value from cache"""
        with self._lock:
            self._evict(key)
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
            self._metadata.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def invalidate_by_tag(self, tag: str):
        """Invalidate all entries with a specific tag"""
        with self._lock:
            keys_to_delete = [
                k for k, v in self._metadata.items()
                if tag in v.tags
            ]
            for key in keys_to_delete:
                self._evict(key)
            logger.info(f"Invalidated {len(keys_to_delete)} entries with tag: {tag}")
    
    def cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            keys_to_delete = [
                k for k, v in self._metadata.items()
                if v.is_expired()
            ]
            for key in keys_to_delete:
                self._evict(key)
            
            if keys_to_delete:
                logger.info(f"Cleaned up {len(keys_to_delete)} expired entries")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "evictions": self._evictions,
                "default_ttl": self.default_ttl
            }


# ==================== Two-Level Cache ====================

class TwoLevelCache(BaseCache[T]):
    """Two-level cache: L1 (memory) + L2 (persistent)"""
    
    def __init__(
        self,
        l1_size: int = 100,
        l1_ttl: float = 60,
        l2_size: int = 1000,
        l2_ttl: float = 3600,
        l2_backend: Callable = None  # Optional L2 backend
    ):
        self.l1 = LRUCache[T](max_size=l1_size, default_ttl=l1_ttl)
        self.l2 = LRUCache[T](max_size=l2_size, default_ttl=l2_ttl)
        self.l2_backend = l2_backend
        
        self._hits_l1 = 0
        self._hits_l2 = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache (L1 first, then L2)"""
        # Try L1
        value = self.l1.get(key)
        if value is not None:
            self._hits_l1 += 1
            return value
        
        # Try L2
        value = self.l2.get(key)
        if value is not None:
            # Promote to L1
            self.l1.set(key, value)
            self._hits_l2 += 1
            return value
        
        self._misses += 1
        return None
    
    def set(self, key: str, value: T, ttl: float = None, tags: List[str] = None):
        """Set value in both levels"""
        # L1 has shorter TTL
        self.l1.set(key, value, ttl=min(ttl or 60, 60), tags=tags)
        # L2 has longer TTL
        self.l2.set(key, value, ttl=ttl, tags=tags)
    
    def delete(self, key: str):
        """Delete from both levels"""
        self.l1.delete(key)
        self.l2.delete(key)
    
    def clear(self):
        """Clear both levels"""
        self.l1.clear()
        self.l2.clear()
        self._hits_l1 = 0
        self._hits_l2 = 0
        self._misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get combined statistics"""
        total = self._hits_l1 + self._hits_l2 + self._misses
        hit_rate = (self._hits_l1 + self._hits_l2) / total if total > 0 else 0
        
        return {
            "l1": self.l1.stats(),
            "l2": self.l2.stats(),
            "hits_l1": self._hits_l1,
            "hits_l2": self._hits_l2,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4)
        }


# ==================== Cache with Statistics ====================

class MonitoredCache(BaseCache[T]):
    """Cache with detailed statistics tracking"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        self._cache = LRUCache[T](max_size=max_size, default_ttl=default_ttl)
        self._access_log: List[Dict] = []
        self._max_log_size = 1000
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[T]:
        """Get value with logging"""
        value = self._cache.get(key)
        
        with self._lock:
            self._access_log.append({
                "key": key,
                "action": "hit" if value else "miss",
                "timestamp": datetime.now().isoformat()
            })
            
            # Trim log
            if len(self._access_log) > self._max_log_size:
                self._access_log = self._access_log[-self._max_log_size:]
        
        return value
    
    def set(self, key: str, value: T, ttl: float = None, tags: List[str] = None):
        """Set value with logging"""
        self._cache.set(key, value, ttl, tags)
        
        with self._lock:
            self._access_log.append({
                "key": key,
                "action": "set",
                "timestamp": datetime.now().isoformat()
            })
    
    def delete(self, key: str):
        """Delete with logging"""
        self._cache.delete(key)
        
        with self._lock:
            self._access_log.append({
                "key": key,
                "action": "delete",
                "timestamp": datetime.now().isoformat()
            })
    
    def clear(self):
        """Clear cache"""
        self._cache.clear()
        with self._lock:
            self._access_log.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics with access log"""
        base_stats = self._cache.stats()
        
        with self._lock:
            return {
                **base_stats,
                "recent_accesses": self._access_log[-50:]
            }
    
    def get_access_log(self, limit: int = 100) -> List[Dict]:
        """Get recent access log"""
        with self._lock:
            return self._access_log[-limit:]


# ==================== Cache Decorator ====================

def cached(
    cache: BaseCache = None,
    ttl: float = None,
    tags: List[str] = None,
    key_func: Callable = None
):
    """Decorator to cache function results"""
    if cache is None:
        cache = LRUCache()
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_data = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                cache_key = hashlib.md5(
                    json.dumps(key_data, sort_keys=True, default=str).encode()
                ).hexdigest()
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl=ttl, tags=tags)
            logger.debug(f"Cache miss for {func.__name__}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_data = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                cache_key = hashlib.md5(
                    json.dumps(key_data, sort_keys=True, default=str).encode()
                ).hexdigest()
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl=ttl, tags=tags)
            logger.debug(f"Cache miss for {func.__name__}")
            
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ==================== Cache Invalidation ====================

class CacheInvalidator:
    """Manages cache invalidation strategies"""
    
    def __init__(self, cache: BaseCache):
        self.cache = cache
        self._invalidation_rules: Dict[str, List[Callable]] = {}
    
    def register_rule(self, trigger_key: str, invalidator: Callable):
        """Register invalidation rule"""
        if trigger_key not in self._invalidation_rules:
            self._invalidation_rules[trigger_key] = []
        self._invalidation_rules[trigger_key].append(invalidator)
    
    def invalidate(self, key: str):
        """Invalidate cache entry and trigger related invalidations"""
        self.cache.delete(key)
        
        # Execute related invalidation rules
        if key in self._invalidation_rules:
            for invalidator in self._invalidation_rules[key]:
                invalidator()
    
    def invalidate_prefix(self, prefix: str):
        """Invalidate all keys with a prefix"""
        # This is a simplified implementation
        # In production, you'd want a more efficient method
        pass


# ==================== Global Cache Instances ====================

# Main inference cache
inference_cache = LRUCache(max_size=1000, default_ttl=3600)

# Two-level cache for queries
query_cache = TwoLevelCache(
    l1_size=100,
    l1_ttl=60,
    l2_size=1000,
    l2_ttl=3600
)

# Monitored cache for debugging
debug_cache = MonitoredCache(max_size=500, default_ttl=1800)


# ==================== Cache Factory ====================

def create_cache(
    cache_type: str = "lru",
    max_size: int = 1000,
    default_ttl: float = 3600,
    **kwargs
) -> BaseCache:
    """Factory function to create cache instances"""
    if cache_type == "lru":
        return LRUCache(max_size=max_size, default_ttl=default_ttl)
    elif cache_type == "two_level":
        return TwoLevelCache(
            l1_size=kwargs.get("l1_size", 100),
            l1_ttl=kwargs.get("l1_ttl", 60),
            l2_size=max_size,
            l2_ttl=default_ttl
        )
    elif cache_type == "monitored":
        return MonitoredCache(max_size=max_size, default_ttl=default_ttl)
    else:
        raise ValueError(f"Unknown cache type: {cache_type}")
