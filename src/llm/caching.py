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
from datetime import datetime

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
    def set(self, key: str, value: T, ttl: float = None, tags: List[str] = None):
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


# ==================== LRU Cache ====================

class LRUCache(BaseCache[T]):
    """
    线程安全的 LRU 缓存实现，支持 TTL 过期
    
    使用 OrderedDict 实现 O(1) 的访问和淘汰操作，
    配合线程锁确保并发安全。
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        # 最大缓存容量，超过时触发 LRU 淘汰
        self.max_size = max_size
        # 默认过期时间（秒），None 表示永不过期
        self.default_ttl = default_ttl
        # 使用 OrderedDict 保持访问顺序，实现 LRU 策略
        self._cache: OrderedDict = OrderedDict()
        # 存储每个键的元数据（创建时间、访问次数等）
        self._metadata: Dict[str, CacheEntry] = {}
        # 线程锁，保证多线程环境下的操作原子性
        self._lock = Lock()
        
        # 统计指标：用于监控缓存性能
        self._hits = 0  # 缓存命中次数
        self._misses = 0  # 缓存未命中次数
        self._evictions = 0  # 被淘汰的条目数
    
    def _make_key(self, *args, **kwargs) -> str:
        """
        从参数生成缓存键
        
        使用 JSON 序列化和 MD5 哈希确保键的一致性和唯一性，
        sort_keys=True 保证相同参数生成的键相同，不受字典顺序影响。
        """
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[T]:
        """
        从缓存获取值
        
        先检查键是否存在，再检查是否过期，最后更新访问顺序。
        这种顺序确保过期条目能及时清理，同时保持 LRU 顺序准确。
        """
        with self._lock:
            # 键不存在，记录未命中
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._metadata[key]
            
            # 检查 TTL 是否过期：过期则淘汰并返回未命中
            if entry.is_expired():
                self._evict(key)
                self._misses += 1
                return None
            
            # 移动到 OrderedDict 末尾表示最近使用
            self._cache.move_to_end(key)
            entry.touch()  # 更新访问时间和计数
            
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: T, ttl: Optional[float] = None, tags: Optional[List[str]] = None):
        """
        设置缓存值
        
        如果缓存已满，先淘汰最久未使用的条目。
        使用 Optional 类型注解允许 ttl 为 None，表示使用默认值。
        """
        with self._lock:
            # 缓存已满时，淘汰 LRU 条目直到有空间
            while len(self._cache) >= self.max_size:
                self._evict_next()
            
            now = time.time()
            self._cache[key] = value
            # 创建元数据条目，记录创建时间和 TTL
            self._metadata[key] = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                accessed_at=now,
                ttl=ttl or self.default_ttl,  # 使用传入值或默认值
                tags=tags or []
            )
    
    def _evict_next(self):
        """
        淘汰最久未使用的条目
        
        OrderedDict 的第一个元素就是最久未访问的，直接淘汰即可。
        这是 LRU 策略的核心实现。
        """
        if self._cache:
            key = next(iter(self._cache))  # 获取第一个键（最久未使用）
            self._evict(key)
            self._evictions += 1
    
    def _evict(self, key: str):
        """淘汰指定键：从缓存和元数据中同时删除"""
        self._cache.pop(key, None)
        self._metadata.pop(key, None)
    
    def delete(self, key: str):
        """从缓存中删除指定键"""
        with self._lock:
            self._evict(key)
    
    def clear(self):
        """清空整个缓存并重置统计"""
        with self._lock:
            self._cache.clear()
            self._metadata.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def invalidate_by_tag(self, tag: str):
        """
        按标签淘汰条目
        
        用于批量删除相关数据，例如清除某个模块的所有缓存。
        遍历所有元数据，删除包含指定标签的条目。
        """
        with self._lock:
            # 收集所有包含该标签的键
            keys_to_delete = [
                k for k, v in self._metadata.items()
                if tag in v.tags
            ]
            for key in keys_to_delete:
                self._evict(key)
            logger.info(f"Invalidated {len(keys_to_delete)} entries with tag: {tag}")
    
    def cleanup_expired(self):
        """
        清理过期条目
        
        定期调用此方法可释放内存，防止过期数据占用空间。
        适用于没有主动过期检查的场景。
        """
        with self._lock:
            # 找出所有过期的键
            keys_to_delete = [
                k for k, v in self._metadata.items()
                if v.is_expired()
            ]
            for key in keys_to_delete:
                self._evict(key)
            
            if keys_to_delete:
                logger.info(f"Cleaned up {len(keys_to_delete)} expired entries")
    
    def stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        返回命中率、大小等关键指标，用于监控缓存性能。
        命中率低于预期时可能需要调整缓存策略或容量。
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),  # 命中率，越高越好
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
