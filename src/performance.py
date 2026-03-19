"""
Performance Optimization Module
Provides caching, connection pooling, and async optimizations
"""

import time
import asyncio
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, Generic, List
from dataclasses import dataclass
from functools import wraps
from collections import OrderedDict
from threading import Lock
from datetime import datetime, timedelta
import weakref

logger = logging.getLogger(__name__)


# ==================== LRU Cache ====================

T = TypeVar('T')

class LRUCache(Generic[T]):
    """Thread-safe LRU cache implementation"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = Lock()
    
    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            if key in self._timestamps:
                if time.time() - self._timestamps[key] > self.ttl:
                    del self._cache[key]
                    del self._timestamps[key]
                    return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
    
    def set(self, key: str, value: T):
        """Set value in cache"""
        with self._lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._timestamps.pop(oldest_key, None)
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def delete(self, key: str):
        """Delete value from cache"""
        with self._lock:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            now = time.time()
            expired_keys = [
                k for k, ts in self._timestamps.items()
                if now - ts > self.ttl
            ]
            for key in expired_keys:
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl
            }


# Global inference cache
inference_cache = LRUCache(max_size=1000, ttl_seconds=3600)


# ==================== Decorator for Caching ====================

def cached(cache: LRUCache = None, key_func: Callable = None):
    """Decorator to cache function results"""
    if cache is None:
        cache = inference_cache
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._make_key(*args, **kwargs)
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key[:8]}...")
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result)
            logger.debug(f"Cache miss for {func.__name__}: {cache_key[:8]}...")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._make_key(*args, **kwargs)
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key[:8]}...")
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result)
            logger.debug(f"Cache miss for {func.__name__}: {cache_key[:8]}...")
            
            return result
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ==================== Connection Pool ====================

@dataclass
class PoolConfig:
    """Connection pool configuration"""
    min_size: int = 2
    max_size: int = 20
    max_idle_time: int = 300  # seconds
    checkout_timeout: int = 30  # seconds
    recycle_time: int = 3600  # seconds


class ConnectionPool(Generic[T]):
    """Generic connection pool"""
    
    def __init__(
        self,
        factory: Callable[[], T],
        config: PoolConfig = None
    ):
        self.factory = factory
        self.config = config or PoolConfig()
        self._pool: list = []
        self._in_use: set = set()
        self._lock = Lock()
        self._semaphore: asyncio.Semaphore = None
    
    async def initialize(self):
        """Initialize the pool"""
        if asyncio.get_event_loop().is_running():
            self._semaphore = asyncio.Semaphore(self.config.max_size)
        
        # Create initial connections
        for _ in range(self.config.min_size):
            conn = await self._create_connection()
            self._pool.append(conn)
        
        logger.info(f"Connection pool initialized with {self.config.min_size} connections")
    
    async def _create_connection(self) -> T:
        """Create a new connection"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.factory
        )
    
    async def acquire(self) -> T:
        """Acquire a connection from the pool"""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.config.max_size)
        
        await self._semaphore.acquire()
        
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
                self._in_use.add(id(conn))
                return conn
        
        # Create new connection if pool is empty
        conn = await self._create_connection()
        with self._lock:
            self._in_use.add(id(conn))
        return conn
    
    def release(self, conn: T):
        """Release a connection back to the pool"""
        with self._lock:
            conn_id = id(conn)
            if conn_id in self._in_use:
                self._in_use.discard(conn_id)
                self._pool.append(conn)
        
        if self._semaphore:
            self._semaphore.release()
    
    async def close(self):
        """Close all connections"""
        with self._lock:
            for conn in self._pool:
                if hasattr(conn, 'close'):
                    await asyncio.get_event_loop().run_in_executor(None, conn.close)
            self._pool.clear()
            self._in_use.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            return {
                "total": len(self._pool) + len(self._in_use),
                "available": len(self._pool),
                "in_use": len(self._in_use),
                "max_size": self.config.max_size
            }


# ==================== Async Utilities ====================

async def run_in_executor_pool(
    func: Callable,
    *args,
    max_workers: int = 4,
    **kwargs
):
    """Run CPU-intensive function in a thread pool"""
    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    
    try:
        result = await loop.run_in_executor(
            executor,
            lambda: func(*args, **kwargs)
        )
        return result
    finally:
        executor.shutdown(wait=False)


import concurrent.futures


class AsyncBatchProcessor:
    """Process multiple async tasks in batches"""
    
    def __init__(self, batch_size: int = 10, max_concurrent: int = 5):
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process(
        self,
        items: list,
        processor: Callable
    ) -> list:
        """Process items in batches"""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            async def process_item(item):
                async with self.semaphore:
                    return await processor(item)
            
            batch_results = await asyncio.gather(
                *[process_item(item) for item in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
        
        return results


# ==================== Query Optimizer ====================

class QueryOptimizer:
    """Optimizes database queries"""
    
    def __init__(self):
        self._query_cache = LRUCache(max_size=500, ttl_seconds=600)
    
    def optimize_query(self, query: str, params: Dict) -> Dict[str, Any]:
        """Optimize a query"""
        # Simple query analysis
        analysis = {
            "original_query": query,
            "suggestions": [],
            "estimated_cost": 1.0
        }
        
        # Check for common issues
        query_lower = query.lower()
        
        # Warn about SELECT *
        if "select *" in query_lower:
            analysis["suggestions"].append("Avoid SELECT * - specify required columns")
            analysis["estimated_cost"] += 0.5
        
        # Warn about missing limits
        if "limit" not in query_lower and "top" not in query_lower:
            analysis["suggestions"].append("Consider adding LIMIT to prevent large result sets")
            analysis["estimated_cost"] += 0.3
        
        # Warn about OR conditions
        if " or " in query_lower:
            analysis["suggestions"].append("Consider using UNION instead of OR for better performance")
            analysis["estimated_cost"] += 0.2
        
        return analysis
    
    def should_cache(self, query: str) -> bool:
        """Determine if query result should be cached"""
        # Don't cache write operations
        write_keywords = ["insert", "update", "delete", "create", "drop"]
        query_lower = query.lower()
        
        for keyword in write_keywords:
            if keyword in query_lower:
                return False
        
        return True


query_optimizer = QueryOptimizer()


# ==================== Performance Profiler ====================

@dataclass
class ProfileResult:
    """Profile result"""
    function_name: str
    call_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float


class PerformanceProfiler:
    """Profile function performance"""
    
    def __init__(self):
        self._profiles: Dict[str, Dict] = {}
        self._lock = Lock()
    
    def profile(self, func: Callable):
        """Decorator to profile a function"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                self._record(func.__name__, duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                self._record(func.__name__, duration)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    def _record(self, name: str, duration: float):
        """Record execution time"""
        with self._lock:
            if name not in self._profiles:
                self._profiles[name] = {
                    "count": 0,
                    "total": 0,
                    "min": float("inf"),
                    "max": 0
                }
            
            profile = self._profiles[name]
            profile["count"] += 1
            profile["total"] += duration
            profile["min"] = min(profile["min"], duration)
            profile["max"] = max(profile["max"], duration)
    
    def get_results(self) -> List[ProfileResult]:
        """Get profiling results"""
        results = []
        with self._lock:
            for name, data in self._profiles.items():
                results.append(ProfileResult(
                    function_name=name,
                    call_count=data["count"],
                    total_time=data["total"],
                    avg_time=data["total"] / data["count"] if data["count"] > 0 else 0,
                    min_time=data["min"],
                    max_time=data["max"]
                ))
        
        return sorted(results, key=lambda x: x.total_time, reverse=True)
    
    def reset(self):
        """Reset profiling data"""
        with self._lock:
            self._profiles.clear()


# Global profiler
profiler = PerformanceProfiler()


# ==================== Resource Manager ====================

class ResourceManager:
    """Manage application resources"""
    
    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._lock = Lock()
    
    def register(self, name: str, resource: Any, cleanup: Callable = None):
        """Register a resource"""
        with self._lock:
            self._resources[name] = {
                "resource": resource,
                "cleanup": cleanup,
                "registered_at": datetime.now()
            }
            logger.info(f"Registered resource: {name}")
    
    def get(self, name: str) -> Optional[Any]:
        """Get a registered resource"""
        with self._lock:
            return self._resources.get(name, {}).get("resource")
    
    async def cleanup(self, name: str):
        """Cleanup a specific resource"""
        with self._lock:
            if name in self._resources:
                data = self._resources[name]
                if data["cleanup"]:
                    await data["cleanup"]()
                del self._resources[name]
                logger.info(f"Cleaned up resource: {name}")
    
    async def cleanup_all(self):
        """Cleanup all resources"""
        names = list(self._resources.keys())
        for name in names:
            await self.cleanup(name)


# Global resource manager
resource_manager = ResourceManager()


# ==================== Optimization Config ====================

@dataclass
class OptimizationConfig:
    """Optimization configuration"""
    # Caching
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000
    
    # Connection pool
    pool_min_size: int = 2
    pool_max_size: int = 20
    
    # Query optimization
    enable_query_cache: bool = True
    query_cache_ttl: int = 600
    
    # Batch processing
    batch_size: int = 10
    max_concurrent_batches: int = 5
    
    # Profiling
    enable_profiling: bool = False


# Default config
optimization_config = OptimizationConfig()
