"""
Enhanced Cache Strategy Module
Advanced caching strategies with Redis support, distributed caching, and cache warming

v1.1.0 - Enhanced version
- Redis distributed cache support
- Cache warming strategies
- Cache-aside pattern
- Write-through/write-back caching
- Adaptive cache management
"""

import time
import json
import hashlib
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, TypeVar, Generic, List, Set
from dataclasses import dataclass, field
from functools import wraps
from collections import OrderedDict
from threading import Lock
from datetime import datetime, timedelta
from enum import Enum
import weakref

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Try to import Redis (optional dependency)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache only")


# ==================== Cache Strategy Types ====================

class CacheStrategy(str, Enum):
    """Cache strategy types"""
    LRU = "lru"           # Least Recently Used
    LFU = "lfu"           # Least Frequently Used
    FIFO = "fifo"         # First In First Out
    TTL = "ttl"           # Time To Live
    ADAPTIVE = "adaptive" # Adaptive based on access patterns


class CacheMode(str, Enum):
    """Cache operation modes"""
    CACHE_ASIDE = "cache_aside"      # Check cache, populate on miss
    WRITE_THROUGH = "write_through"  # Write to cache and DB simultaneously
    WRITE_BACK = "write_back"         # Write to cache, defer DB write


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
    priority: int = 0  # Higher priority items are evicted last
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """Update access time and count"""
        self.accessed_at = time.time()
        self.access_count += 1
    
    def get_age(self) -> float:
        """Get entry age in seconds"""
        return time.time() - self.created_at


# ==================== Base Cache ====================

class BaseCache(Generic[T]):
    """Base cache interface"""
    
    def get(self, key: str) -> Optional[T]:
        raise NotImplementedError
    
    def set(self, key: str, value: T, ttl: float = None, tags: List[str] = None, priority: int = 0):
        raise NotImplementedError
    
    def delete(self, key: str):
        raise NotImplementedError
    
    def clear(self):
        raise NotImplementedError
    
    def stats(self) -> Dict[str, Any]:
        raise NotImplementedError


# ==================== LRU Cache (Enhanced) ====================

class EnhancedLRUCache(BaseCache[T]):
    """Thread-safe LRU cache with TTL, tags, and priority support"""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 3600,
        enable_stats: bool = True,
        cleanup_interval: float = 60
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._metadata: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._enable_stats = enable_stats
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expired = 0
        
        # Periodic cleanup
        self._last_cleanup = time.time()
        self._cleanup_interval = cleanup_interval
    
    def _maybe_cleanup(self):
        """Periodic cleanup of expired entries"""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = now
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        keys_to_delete = [
            k for k, v in self._metadata.items()
            if v.is_expired()
        ]
        for key in keys_to_delete:
            self._evict(key)
            self._expired += 1
        if keys_to_delete:
            logger.debug(f"Cleaned up {len(keys_to_delete)} expired entries")
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache"""
        with self._lock:
            self._maybe_cleanup()
            
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._metadata[key]
            
            # Check TTL
            if entry.is_expired():
                self._evict(key)
                self._misses += 1
                self._expired += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: T, ttl: float = None, tags: List[str] = None, priority: int = 0):
        """Set value in cache"""
        with self._lock:
            # Remove oldest if at capacity (consider priority)
            while len(self._cache) >= self.max_size:
                self._evict_lru()
            
            now = time.time()
            
            # Update existing or create new
            if key in self._cache:
                self._evict(key)
            
            self._cache[key] = value
            self._metadata[key] = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                accessed_at=now,
                ttl=ttl or self.default_ttl,
                tags=tags or [],
                priority=priority
            )
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if self._cache:
            # Find entry with lowest priority, then oldest access
            min_priority = min(v.priority for v in self._metadata.values())
            candidates = [k for k, v in self._metadata.items() if v.priority == min_priority]
            
            # Evict oldest accessed
            key = min(candidates, key=lambda k: self._metadata[k].accessed_at)
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
            self._expired = 0
    
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
    
    def invalidate_by_pattern(self, pattern: str):
        """Invalidate all entries matching a pattern"""
        import fnmatch
        with self._lock:
            keys_to_delete = [
                k for k in self._cache.keys()
                if fnmatch.fnmatch(k, pattern)
            ]
            for key in keys_to_delete:
                self._evict(key)
            logger.info(f"Invalidated {len(keys_to_delete)} entries matching pattern: {pattern}")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            
            # Calculate average metrics
            ages = [v.get_age() for v in self._metadata.values()]
            access_counts = [v.access_count for v in self._metadata.values()]
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "evictions": self._evictions,
                "expired": self._expired,
                "default_ttl": self.default_ttl,
                "avg_age_seconds": round(sum(ages) / len(ages), 2) if ages else 0,
                "avg_access_count": round(sum(access_counts) / len(access_counts), 2) if access_counts else 0
            }


# ==================== Redis Distributed Cache ====================

class RedisCache(BaseCache[T]):
    """Redis-backed distributed cache"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "ontology:",
        default_ttl: float = 3600,
        ssl: bool = False
    ):
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis is not available. Install with: pip install redis")
        
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        
        self._client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            ssl=ssl
        )
        
        # Statistics
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{self.key_prefix}{key}"
    
    def get(self, key: str) -> Optional[T]:
        """Get value from Redis"""
        try:
            value = self._client.get(self._make_key(key))
            if value is None:
                self._misses += 1
                return None
            
            self._hits += 1
            return json.loads(value)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._misses += 1
            return None
    
    def set(
        self,
        key: str,
        value: T,
        ttl: float = None,
        tags: List[str] = None,
        priority: int = 0
    ):
        """Set value in Redis"""
        try:
            serialized = json.dumps(value, default=str)
            ttl = ttl or self.default_ttl
            self._client.setex(
                self._make_key(key),
                ttl,
                serialized
            )
            
            # Store tags for invalidation
            if tags:
                tag_key = f"{self.key_prefix}tags:{key}"
                self._client.sadd(tag_key, *tags)
                self._client.expire(tag_key, ttl)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    def delete(self, key: str):
        """Delete from Redis"""
        try:
            self._client.delete(self._make_key(key))
            self._client.delete(f"{self.key_prefix}tags:{key}")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
    
    def clear(self):
        """Clear cache (with prefix)"""
        try:
            keys = self._client.keys(f"{self.key_prefix}*")
            if keys:
                self._client.delete(*keys)
            self._hits = 0
            self._misses = 0
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
    
    def invalidate_by_tag(self, tag: str):
        """Invalidate by tag"""
        try:
            # Find all keys with this tag
            pattern = f"{self.key_prefix}tags:*"
            tag_keys = self._client.keys(pattern)
            
            keys_to_delete = []
            for tag_key in tag_keys:
                members = self._client.smembers(tag_key)
                if tag in members:
                    # Extract original key from tag key
                    original_key = tag_key.replace(f"{self.key_prefix}tags:", "")
                    keys_to_delete.append(original_key)
            
            # Delete all
            for key in keys_to_delete:
                self.delete(key)
            
            logger.info(f"Invalidated {len(keys_to_delete)} entries with tag: {tag}")
        except Exception as e:
            logger.error(f"Redis invalidate error: {e}")
    
    def stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        try:
            info = self._client.info("stats")
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "redis_connected": True,
                "key_prefix": self.key_prefix
            }
        except Exception as e:
            return {"error": str(e), "redis_connected": False}


# ==================== Two-Level Cache ====================

class TwoLevelCache(BaseCache[T]):
    """Two-level cache: L1 (memory) + L2 (Redis)"""
    
    def __init__(
        self,
        l1_size: int = 100,
        l1_ttl: float = 60,
        l2_config: Dict[str, Any] = None,
        l2_ttl: float = 3600,
        async_mode: bool = False
    ):
        self.l1 = EnhancedLRUCache[T](max_size=l1_size, default_ttl=l1_ttl)
        
        # L2 is optional
        if l2_config and REDIS_AVAILABLE:
            try:
                self.l2 = RedisCache(
                    host=l2_config.get("host", "localhost"),
                    port=l2_config.get("port", 6379),
                    db=l2_config.get("db", 0),
                    password=l2_config.get("password"),
                    key_prefix=l2_config.get("prefix", "ontology:"),
                    default_ttl=l2_ttl
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Redis L2 cache: {e}")
                self.l2 = None
        else:
            self.l2 = None
        
        self._async_mode = async_mode
        
        # Statistics
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
        if self.l2:
            value = self.l2.get(key)
            if value is not None:
                # Promote to L1
                self.l1.set(key, value)
                self._hits_l2 += 1
                return value
        
        self._misses += 1
        return None
    
    def set(
        self,
        key: str,
        value: T,
        ttl: float = None,
        tags: List[str] = None,
        priority: int = 0
    ):
        """Set value in both levels"""
        # L1 has shorter TTL
        self.l1.set(key, value, ttl=min(ttl or 60, 60), tags=tags, priority=priority)
        
        # L2 has longer TTL
        if self.l2:
            self.l2.set(key, value, ttl=ttl, tags=tags, priority=priority)
    
    def delete(self, key: str):
        """Delete from both levels"""
        self.l1.delete(key)
        if self.l2:
            self.l2.delete(key)
    
    def clear(self):
        """Clear both levels"""
        self.l1.clear()
        if self.l2:
            self.l2.clear()
        self._hits_l1 = 0
        self._hits_l2 = 0
        self._misses = 0
    
    def invalidate_by_tag(self, tag: str):
        """Invalidate by tag in both levels"""
        self.l1.invalidate_by_tag(tag)
        if self.l2:
            self.l2.invalidate_by_tag(tag)
    
    def stats(self) -> Dict[str, Any]:
        """Get combined statistics"""
        stats = {
            "l1": self.l1.stats(),
            "hits_l1": self._hits_l1,
            "hits_l2": self._hits_l2,
            "misses": self._misses
        }
        
        if self.l2:
            stats["l2"] = self.l2.stats()
        
        total = self._hits_l1 + self._hits_l2 + self._misses
        hit_rate = (self._hits_l1 + self._hits_l2) / total if total > 0 else 0
        stats["hit_rate"] = round(hit_rate, 4)
        
        return stats


# ==================== Cache Warmer ====================

class CacheWarmer:
    """Warms cache with frequently accessed data"""
    
    def __init__(self, cache: BaseCache):
        self._cache = cache
        self._warm_tasks: Dict[str, Callable] = {}
    
    def register(self, key_pattern: str, loader: Callable):
        """Register a warming task"""
        self._warm_tasks[key_pattern] = loader
    
    def warm(self, keys: List[str]):
        """Warm cache with specified keys"""
        for key in keys:
            if self._cache.get(key) is None:
                # Check if we have a loader for this key
                for pattern, loader in self._warm_tasks.items():
                    if key.startswith(pattern.replace("*", "")):
                        try:
                            value = loader(key)
                            self._cache.set(key, value)
                            logger.info(f"Warmed cache: {key}")
                        except Exception as e:
                            logger.error(f"Failed to warm {key}: {e}")
                        break
    
    async def warm_async(self, keys: List[str]):
        """Async warming"""
        for key in keys:
            if self._cache.get(key) is None:
                for pattern, loader in self._warm_tasks.items():
                    if key.startswith(pattern.replace("*", "")):
                        try:
                            if asyncio.iscoroutinefunction(loader):
                                value = await loader(key)
                            else:
                                value = loader(key)
                            self._cache.set(key, value)
                        except Exception as e:
                            logger.error(f"Failed to warm {key}: {e}")
                        break


# ==================== Cache Decorator ====================

def cached(
    cache: BaseCache = None,
    ttl: float = None,
    tags: List[str] = None,
    key_func: Callable = None,
    priority: int = 0
):
    """Decorator to cache function results"""
    if cache is None:
        cache = EnhancedLRUCache()
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
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
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl=ttl, tags=tags, priority=priority)
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
            cache.set(cache_key, result, ttl=ttl, tags=tags, priority=priority)
            logger.debug(f"Cache miss for {func.__name__}")
            
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ==================== Global Cache Instances ====================

# Main inference cache (enhanced)
inference_cache = EnhancedLRUCache(max_size=1000, default_ttl=3600)

# Two-level cache for queries
query_cache = TwoLevelCache(
    l1_size=100,
    l1_ttl=60,
    l2_ttl=3600
)

# Monitored cache for debugging
debug_cache = EnhancedLRUCache(max_size=500, default_ttl=1800)


# ==================== Cache Factory ====================

def create_cache(
    cache_type: str = "lru",
    max_size: int = 1000,
    default_ttl: float = 3600,
    redis_config: Dict[str, Any] = None,
    **kwargs
) -> BaseCache:
    """Factory function to create cache instances"""
    if cache_type == "lru":
        return EnhancedLRUCache(max_size=max_size, default_ttl=default_ttl)
    elif cache_type == "two_level":
        return TwoLevelCache(
            l1_size=kwargs.get("l1_size", 100),
            l1_ttl=kwargs.get("l1_ttl", 60),
            l2_config=redis_config,
            l2_ttl=default_ttl
        )
    elif cache_type == "redis":
        if not redis_config:
            raise ValueError("Redis config required for Redis cache")
        return RedisCache(
            host=redis_config.get("host", "localhost"),
            port=redis_config.get("port", 6379),
            db=redis_config.get("db", 0),
            password=redis_config.get("password"),
            key_prefix=redis_config.get("prefix", "ontology:"),
            default_ttl=default_ttl
        )
    else:
        raise ValueError(f"Unknown cache type: {cache_type}")


# ==================== Cache Configuration ====================

@dataclass
class CacheConfig:
    """Cache configuration"""
    strategy: CacheStrategy = CacheStrategy.LRU
    max_size: int = 1000
    default_ttl: float = 3600
    enable_redis: bool = False
    redis_config: Optional[Dict[str, Any]] = None
    cleanup_interval: float = 60
    enable_stats: bool = True
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "CacheConfig":
        """Create from dictionary"""
        return cls(
            strategy=CacheStrategy(config.get("strategy", "lru")),
            max_size=config.get("max_size", 1000),
            default_ttl=config.get("default_ttl", 3600),
            enable_redis=config.get("enable_redis", False),
            redis_config=config.get("redis_config"),
            cleanup_interval=config.get("cleanup_interval", 60),
            enable_stats=config.get("enable_stats", True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "strategy": self.strategy.value,
            "max_size": self.max_size,
            "default_ttl": self.default_ttl,
            "enable_redis": self.enable_redis,
            "redis_config": self.redis_config,
            "cleanup_interval": self.cleanup_interval,
            "enable_stats": self.enable_stats
        }
