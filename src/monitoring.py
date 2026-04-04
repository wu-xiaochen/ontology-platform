"""
Monitoring and Metrics Module
Provides Prometheus metrics, health checks, and performance monitoring
"""

import time
import logging
from typing import Callable, Dict, Any
from functools import wraps
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


# ==================== Metrics Collectors ====================

class MetricsCollector:
    """Custom metrics collector for the application"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)
        self._histogram_lock = Lock()
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None, value: int = 1):
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observe a histogram value"""
        key = self._make_key(name, labels)
        with self._histogram_lock:
            self._histograms[key].append(value)
            # Keep only last 1000 values per key
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> str:
        """Export all metrics in Prometheus format"""
        lines = []
        
        # Export counters
        with self._lock:
            for key, value in self._counters.items():
                lines.append(f"# TYPE {key} counter")
                lines.append(f"{key} {value}")
        
        # Export gauges
        with self._lock:
            for key, value in self._gauges.items():
                lines.append(f"# TYPE {key} gauge")
                lines.append(f"{key} {value}")
        
        # Export histograms
        with self._histogram_lock:
            for key, values in self._histograms.items():
                if values:
                    sorted_values = sorted(values)
                    n = len(sorted_values)
                    lines.append(f"# TYPE {key} summary")
                    lines.append(f"{key}_count {n}")
                    lines.append(f"{key}_sum {sum(sorted_values)}")
                    # Percentiles
                    for p in [0.5, 0.9, 0.95, 0.99]:
                        idx = int(n * p)
                        lines.append(f'{key}{{quantile="{p}"}} {sorted_values[min(idx, n-1)]}')
        
        return "\n".join(lines) + "\n"
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
        with self._histogram_lock:
            self._histograms.clear()


# Global metrics collector
metrics = MetricsCollector()


# ==================== Decorators for Metrics ====================

def track_request_time(endpoint: str = None):
    """Decorator to track request time"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            labels = {"endpoint": endpoint or func.__name__}
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                metrics.observe_histogram("http_request_duration_seconds", duration, labels)
                metrics.increment_counter("http_requests_total", {**labels, "status": "success"})
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            labels = {"endpoint": endpoint or func.__name__}
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                metrics.observe_histogram("http_request_duration_seconds", duration, labels)
                metrics.increment_counter("http_requests_total", {**labels, "status": "success"})
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def track_inference_time(ontology_type: str = None):
    """Decorator to track inference time"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            labels = {"ontology": ontology_type or "default"}
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                metrics.observe_histogram("inference_duration_seconds", duration, labels)
                metrics.increment_counter("inferences_total", labels)
        return wrapper
    return decorator


# ==================== Health Checks ====================

@dataclass
class HealthStatus:
    """Health check status"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    checks: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """Health checker for various components"""
    
    def __init__(self):
        self._checks: Dict[str, Callable] = {}
    
    def register_check(self, name: str, check_fn: Callable):
        """Register a health check function"""
        self._checks[name] = check_fn
    
    async def check_all(self) -> HealthStatus:
        """Run all health checks"""
        results = {}
        overall_status = "healthy"
        
        for name, check_fn in self._checks.items():
            try:
                if asyncio.iscoroutinefunction(check_fn):
                    result = await check_fn()
                else:
                    result = check_fn()
                results[name] = result
                
                if result.get("status") == "unhealthy":
                    overall_status = "unhealthy"
                elif result.get("status") == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"
            except Exception as e:
                results[name] = {"status": "unhealthy", "error": str(e)}
                overall_status = "unhealthy"
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            checks=results
        )


import asyncio
health_checker = HealthChecker()


# ==================== Application Metrics ====================

def setup_app_metrics(app):
    """Setup metrics endpoints for FastAPI app"""
    from fastapi import APIRouter, Response
    
    router = APIRouter()
    
    @router.get("/metrics")
    async def metrics_endpoint():
        """Prometheus metrics endpoint"""
        return Response(
            content=metrics.get_metrics(),
            media_type="text/plain"
        )
    
    @router.get("/health/detailed")
    async def detailed_health():
        """Detailed health check"""
        status = await health_checker.check_all()
        return {
            "status": status.status,
            "timestamp": status.timestamp,
            "checks": status.checks
        }
    
    app.include_router(router, tags=["Monitoring"])
    
    return router


# ==================== Request Logging ====================

class RequestLogger:
    """Structured request logging with correlation IDs"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger("request")
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        correlation_id: str = None,
        user_id: str = None,
        extra: Dict[str, Any] = None
    ):
        """Log HTTP request with structured data"""
        log_data = {
            "type": "request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": datetime.now().isoformat(),
        }
        
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        if user_id:
            log_data["user_id"] = user_id
        if extra:
            log_data.update(extra)
        
        # Determine log level based on status code
        if status_code >= 500:
            self.logger.error(log_data)
        elif status_code >= 400:
            self.logger.warning(log_data)
        else:
            self.logger.info(log_data)


request_logger = RequestLogger()


# ==================== Performance Monitor ====================

@dataclass
class PerformanceSnapshot:
    """Performance snapshot at a point in time"""
    timestamp: str
    requests_per_second: float
    avg_response_time_ms: float
    active_connections: int
    cache_hit_rate: float


class PerformanceMonitor:
    """Monitor application performance"""
    
    def __init__(self):
        self._request_times: list = []
        self._request_count = 0
        self._last_reset = time.time()
        self._lock = Lock()
    
    def record_request(self, duration: float):
        """Record a request duration"""
        with self._lock:
            now = time.time()
            self._request_times.append((now, duration))
            self._request_count += 1
            
            # Keep only last 60 seconds
            cutoff = now - 60
            self._request_times = [(t, d) for t, d in self._request_times if t > cutoff]
    
    def get_snapshot(self, active_connections: int = 0, cache_hit_rate: float = 0.0) -> PerformanceSnapshot:
        """Get current performance snapshot"""
        with self._lock:
            now = time.time()
            window = 60  # seconds
            
            # Calculate requests per second
            recent_requests = [(t, d) for t, d in self._request_times if t > now - window]
            rps = len(recent_requests) / window if window > 0 else 0
            
            # Calculate average response time
            durations = [d for _, d in recent_requests]
            avg_time = sum(durations) / len(durations) if durations else 0
            
            return PerformanceSnapshot(
                timestamp=datetime.now().isoformat(),
                requests_per_second=round(rps, 2),
                avg_response_time_ms=round(avg_time * 1000, 2),
                active_connections=active_connections,
                cache_hit_rate=round(cache_hit_rate, 4)
            )


performance_monitor = PerformanceMonitor()
