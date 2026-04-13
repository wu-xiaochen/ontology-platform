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
from typing import Dict, Any, Optional, Callable, TypeVar, Generic, List
from dataclasses import dataclass, field
from functools import wraps
from collections import OrderedDict
from threading import Lock
from enum import Enum

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

from abc import ABC, abstractmethod


class BaseCache(ABC, Generic[T]):
    """
    缓存基类接口
    
    使用抽象基类模式定义缓存的标准接口，强制子类实现核心方法。
    这种设计确保所有缓存实现都遵循统一的契约，便于替换和扩展。
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """根据键获取缓存值，子类必须实现"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: T, ttl: Optional[float] = None, tags: Optional[List[str]] = None, priority: int = 0):
        """设置缓存值，子类必须实现"""
        pass
    
    @abstractmethod
    def delete(self, key: str):
        """删除指定键的缓存，子类必须实现"""
        pass
    
    @abstractmethod
    def clear(self):
        """清空所有缓存，子类必须实现"""
        pass
    
    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息，子类必须实现"""
        pass


# ==================== LRU Cache (Enhanced) ====================

class EnhancedLRUCache(BaseCache[T]):
    """
    增强型 LRU 缓存，支持 TTL、标签和优先级
    
    相比基础 LRUCache，增加了优先级支持和定期清理机制，
    适用于更复杂的缓存场景。
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 3600,
        enable_stats: bool = True,
        cleanup_interval: float = 60
    ):
        # 最大缓存容量
        self.max_size = max_size
        # 默认过期时间（秒）
        self.default_ttl = default_ttl
        # 使用 OrderedDict 保持访问顺序
        self._cache: OrderedDict = OrderedDict()
        # 存储每个键的元数据
        self._metadata: Dict[str, CacheEntry] = {}
        # 线程锁保证并发安全
        self._lock = Lock()
        # 是否启用统计
        self._enable_stats = enable_stats
        
        # 统计指标
        self._hits = 0  # 命中次数
        self._misses = 0  # 未命中次数
        self._evictions = 0  # 淘汰次数
        self._expired = 0  # 过期清理次数
        
        # 定期清理机制：记录上次清理时间和间隔
        self._last_cleanup = time.time()
        self._cleanup_interval = cleanup_interval
    
    def _maybe_cleanup(self):
        """
        触发定期清理检查
        
        只有当距离上次清理超过指定间隔时才执行，
        避免每次访问都进行全量扫描，降低性能开销。
        """
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = now
    
    def _cleanup_expired(self):
        """
        清理过期条目
        
        遍历所有元数据，删除已过期的条目。
        在数据量大时可能耗时，建议配合 _maybe_cleanup 使用。
        """
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
        """
        从缓存获取值
        
        先触发定期清理检查，再执行常规获取逻辑。
        这种设计确保过期数据能被及时清理，避免内存泄漏。
        """
        with self._lock:
            # 触发定期清理检查
            self._maybe_cleanup()
            
            # 键不存在，记录未命中
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._metadata[key]
            
            # 检查 TTL 是否过期
            if entry.is_expired():
                self._evict(key)
                self._misses += 1
                self._expired += 1
                return None
            
            # 移动到末尾表示最近使用
            self._cache.move_to_end(key)
            entry.touch()  # 更新访问时间和计数
            
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: T, ttl: Optional[float] = None, tags: Optional[List[str]] = None, priority: int = 0):
        """
        设置缓存值
        
        支持优先级设置，高优先级条目在淘汰时被保留。
        使用 Optional 类型注解，允许 ttl 和 tags 为 None。
        """
        with self._lock:
            # 缓存已满时，按优先级淘汰 LRU 条目
            while len(self._cache) >= self.max_size:
                self._evict_lru()
            
            now = time.time()
            
            # 如果键已存在，先删除旧值
            if key in self._cache:
                self._evict(key)
            
            self._cache[key] = value
            # 创建元数据，包含优先级信息
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
        """
        按优先级淘汰 LRU 条目
        
        先找出优先级最低的条目，再从中选择最久未访问的淘汰。
        这种策略确保高优先级数据被保留，低优先级数据优先淘汰。
        """
        if self._cache:
            # 找出最低优先级
            min_priority = min(v.priority for v in self._metadata.values())
            # 收集所有最低优先级的候选条目
            candidates = [k for k, v in self._metadata.items() if v.priority == min_priority]
            
            # 从候选中选择最久未访问的淘汰
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
        host: str = None,  # 从环境变量读取，默认 localhost
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "ontology:",
        default_ttl: float = 3600,
        ssl: bool = False
    ):
        # 从零硬编码原则：Redis 连接参数从环境变量读取，允许通过配置覆盖
        if host is None:
            host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", port))
        db = int(os.getenv("REDIS_DB", db))
        if password is None:
            password = os.getenv("REDIS_PASSWORD", None)
        ssl = os.getenv("REDIS_SSL", str(ssl)).lower() in ("true", "1", "yes")
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
            try:
                # 尝试将Redis存储的JSON字符串反序列化为Python对象
                return json.loads(value)
            except json.JSONDecodeError as e:
                # 缓存值不是有效的JSON格式，可能是数据损坏或存储格式不一致
                logger.error(f"Redis缓存值JSON解析失败，key={key}: {e}")
                self._misses += 1
                return None
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
            self._client.info("stats")
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
                # 从零硬编码原则：Redis 连接参数优先从环境变量读取，l2_config 作为覆盖
                import os
                self.l2 = RedisCache(
                    host=l2_config.get("host", os.getenv("REDIS_HOST", "localhost")),
                    port=l2_config.get("port", int(os.getenv("REDIS_PORT", "6379"))),
                    db=l2_config.get("db", int(os.getenv("REDIS_DB", "0"))),
                    password=l2_config.get("password") or os.getenv("REDIS_PASSWORD"),
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
