"""
Monitoring and Metrics Module - 企业级可观测性系统

提供 Prometheus 指标、健康检查、性能监控和链路追踪。

v2.0.0 - 企业级增强版本
- 结构化日志（JSON格式）
- 推理链路追踪
- 关键操作指标采集
- 健康检查数据丰富化
"""

import time
import json
import logging
import uuid
import functools
from typing import Callable, Dict, Any, List, Optional
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


# ==================== Structured Logger ====================

class StructuredLogger:
    """
    结构化日志记录器
    
    输出 JSON 格式的结构化日志，便于日志聚合和分析。
    符合零硬编码原则，所有配置从 ConfigManager 读取。
    
    特性：
    - JSON 格式输出
    - 支持上下文字段
    - 支持日志级别过滤
    - 支持敏感数据脱敏
    """
    
    def __init__(self, name: str = "app"):
        """
        初始化结构化日志记录器
        
        参数：
            name: 日志记录器名称
        """
        self._name = name
        self._logger = logging.getLogger(name)
        
        # 从配置获取设置
        from ..utils.config import get_config
        config = get_config().observability
        
        self._structured = config.structured_logging
        self._log_format = config.log_format
        self._log_sensitive = config.log_sensitive_data
        
        # 静态字段（每次日志都会包含）
        self._static_fields: Dict[str, Any] = {}
    
    def set_static_field(self, key: str, value: Any):
        """设置静态字段"""
        self._static_fields[key] = value
    
    def _format_log(
        self,
        level: str,
        message: str,
        **kwargs,
    ) -> str:
        """
        格式化日志消息
        
        根据 _structured 配置输出 JSON 或文本格式。
        """
        # 构建日志数据
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": self._name,
            "message": message,
        }
        
        # 添加静态字段
        log_data.update(self._static_fields)
        
        # 添加动态字段
        for key, value in kwargs.items():
            # 敏感数据处理
            if not self._log_sensitive and self._is_sensitive(key):
                log_data[key] = "***REDACTED***"
            else:
                log_data[key] = value
        
        # 根据配置选择输出格式
        if self._structured:
            # 使用 default=str 处理 datetime 等非序列化类型，确保 JSON 格式规范
            return json.dumps(log_data, ensure_ascii=False, default=str)
        else:
            # 文本格式：对包含空格的值添加引号，确保格式规范
            def format_value(v: Any) -> str:
                # 如果值包含空格或特殊字符，使用引号包裹
                s = str(v)
                if ' ' in s or '\t' in s or '\n' in s or '"' in s:
                    # 转义双引号并添加引号（使用单引号包裹避免转义问题）
                    escaped = s.replace('"', '\\"')
                    return f'"{escaped}"'
                return s
            
            fields_str = " ".join(
                f"{k}={format_value(v)}" 
                for k, v in log_data.items() 
                if k not in ["timestamp", "level", "logger", "message"]
            )
            return f"[{log_data['timestamp']}] {level} [{self._name}] {message} {fields_str}"
    
    def _is_sensitive(self, key: str) -> bool:
        """检查字段名是否为敏感数据"""
        sensitive_patterns = [
            "password", "secret", "token", "key", "credential",
            "api_key", "auth", "private", "ssn", "credit",
        ]
        key_lower = key.lower()
        return any(p in key_lower for p in sensitive_patterns)
    
    def info(self, message: str, **kwargs):
        """记录 INFO 级别日志"""
        formatted = self._format_log("INFO", message, **kwargs)
        self._logger.info(formatted)
    
    def warning(self, message: str, **kwargs):
        """记录 WARNING 级别日志"""
        formatted = self._format_log("WARNING", message, **kwargs)
        self._logger.warning(formatted)
    
    def error(self, message: str, **kwargs):
        """记录 ERROR 级别日志"""
        formatted = self._format_log("ERROR", message, **kwargs)
        self._logger.error(formatted)
    
    def debug(self, message: str, **kwargs):
        """记录 DEBUG 级别日志"""
        formatted = self._format_log("DEBUG", message, **kwargs)
        self._logger.debug(formatted)
    
    def with_context(self, **kwargs) -> "StructuredLogger":
        """
        创建带上下文的日志记录器
        
        返回一个新的日志记录器实例，包含额外的上下文字段。
        """
        new_logger = StructuredLogger(self._name)
        new_logger._structured = self._structured
        new_logger._log_format = self._log_format
        new_logger._log_sensitive = self._log_sensitive
        new_logger._static_fields = {**self._static_fields, **kwargs}
        return new_logger


# 全局结构化日志记录器
structured_logger = StructuredLogger()


# ==================== Inference Tracer ====================

class InferenceTracer:
    """
    推理链路追踪器
    
    记录推理过程的每一步，包括：
    - 推理规则应用
    - 中间结果生成
    - 最终结论得出
    
    用于调试推理过程和分析推理性能。
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        # 单例模式
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
        
        # 从配置获取设置
        from ..utils.config import get_config
        config = get_config().observability
        
        self._enabled = config.enable_inference_tracing
        self._sample_rate = config.trace_sample_rate
        self._retention_seconds = config.trace_retention_seconds
        
        # 追踪数据存储：trace_id -> TraceData
        self._traces: Dict[str, Dict[str, Any]] = {}
        self._traces_lock = Lock()
        
        # 慢推理阈值
        self._slow_threshold = config.slow_inference_threshold
        
        logger.info(f"InferenceTracer 初始化完成: enabled={self._enabled}, sample_rate={self._sample_rate}")
    
    def start_trace(
        self,
        query: str,
        user_id: str = "",
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        开始一个新的推理追踪
        
        返回追踪ID。
        """
        if not self._enabled:
            return ""
        
        # 采样检查：采样率为 0 时完全禁用追踪，但记录日志而非静默丢弃
        import random
        if self._sample_rate <= 0:
            # 采样率为 0 表示追踪被显式禁用，记录调试日志帮助排查
            logger.debug(f"推理追踪被跳过（采样率为 0）: query={query[:50]}...")
            return ""
        if random.random() > self._sample_rate:
            # 被采样率过滤掉的追踪，返回空字符串表示未追踪
            return ""
        
        trace_id = f"trace:{uuid.uuid4().hex[:16]}"
        
        trace_data = {
            "trace_id": trace_id,
            "query": query,
            "user_id": user_id,
            "start_time": time.time(),
            "end_time": None,
            "duration_ms": None,
            "status": "running",
            "steps": [],
            "metadata": metadata or {},
            "conclusion": None,
        }
        
        with self._traces_lock:
            self._traces[trace_id] = trace_data
        
        return trace_id
    
    def record_step(
        self,
        trace_id: str,
        step_name: str,
        step_type: str,
        input_data: Any = None,
        output_data: Any = None,
        duration_ms: float = None,
        metadata: Dict[str, Any] = None,
    ):
        """
        记录推理步骤
        
        参数：
            trace_id: 追踪ID
            step_name: 步骤名称
            step_type: 步骤类型（rule_application, lookup, inference, aggregation 等）
            input_data: 输入数据
            output_data: 输出数据
            duration_ms: 步骤耗时（毫秒）
            metadata: 其他元数据
        """
        if not trace_id:
            # 当 trace_id 为空时记录警告，帮助开发者发现追踪链路断裂问题
            logger.warning(f"record_step 被调用但 trace_id 为空: step_name={step_name}, step_type={step_type}")
            return
        
        if not self._enabled:
            return
        
        step = {
            "step_name": step_name,
            "step_type": step_type,
            "timestamp": datetime.now().isoformat(),
            "input": self._sanitize_data(input_data),
            "output": self._sanitize_data(output_data),
            "duration_ms": duration_ms,
            "metadata": metadata or {},
        }
        
        with self._traces_lock:
            if trace_id in self._traces:
                self._traces[trace_id]["steps"].append(step)
    
    def end_trace(
        self,
        trace_id: str,
        conclusion: Any = None,
        status: str = "completed",
        error: str = None,
    ):
        """
        结束推理追踪
        
        参数：
            trace_id: 追踪ID
            conclusion: 推理结论
            status: 完成状态（completed, failed, timeout）
            error: 错误信息（如果有）
        """
        if not trace_id or not self._enabled:
            return
        
        end_time = time.time()
        
        with self._traces_lock:
            if trace_id not in self._traces:
                return
            
            trace = self._traces[trace_id]
            trace["end_time"] = end_time
            trace["duration_ms"] = (end_time - trace["start_time"]) * 1000
            trace["status"] = status
            trace["conclusion"] = self._sanitize_data(conclusion)
            
            if error:
                trace["error"] = error
            
            # 记录慢推理
            if trace["duration_ms"] > self._slow_threshold * 1000:
                structured_logger.warning(
                    f"慢推理检测: {trace['duration_ms']:.2f}ms",
                    trace_id=trace_id,
                    query=trace["query"][:100],
                    duration_ms=trace["duration_ms"],
                )
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """获取追踪详情"""
        with self._traces_lock:
            return self._traces.get(trace_id)
    
    def _sanitize_data(self, data: Any) -> Any:
        """
        清理数据，避免过大的数据被存储
        """
        if data is None:
            return None
        
        # 字符串截断
        if isinstance(data, str):
            return data[:500] if len(data) > 500 else data
        
        # 列表截断
        if isinstance(data, list):
            return data[:50] if len(data) > 50 else data
        
        # 字典递归处理
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in list(data.items())[:50]}
        
        return data
    
    def cleanup_old_traces(self):
        """清理过期的追踪数据"""
        cutoff_time = time.time() - self._retention_seconds
        
        with self._traces_lock:
            to_remove = [
                trace_id for trace_id, trace in self._traces.items()
                if trace.get("end_time") and trace["end_time"] < cutoff_time
            ]
            
            for trace_id in to_remove:
                del self._traces[trace_id]
            
            if to_remove:
                logger.debug(f"清理了 {len(to_remove)} 条过期追踪数据")


# 全局推理追踪器
inference_tracer = InferenceTracer()


# ==================== 指标采集增强 ====================

class OperationMetrics:
    """
    操作指标采集器
    
    采集关键操作的耗时指标，包括：
    - 推理耗时
    - 查询耗时
    - 学习耗时
    - 缓存命中率
    """
    
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
        
        # 操作耗时直方图
        self._operation_times: Dict[str, List[float]] = defaultdict(list)
        # 操作计数器
        self._operation_counts: Dict[str, int] = defaultdict(int)
        # 错误计数器
        self._error_counts: Dict[str, int] = defaultdict(int)
        # 缓存统计
        self._cache_hits = 0
        self._cache_misses = 0
        
        self._data_lock = Lock()
        
        # 保留最近的操作记录数量
        self._max_records = 1000
        
        # 从配置获取阈值
        from ..utils.config import get_config
        config = get_config().observability
        self._slow_query_threshold = config.slow_query_threshold
        self._slow_inference_threshold = config.slow_inference_threshold
    
    def record_operation(
        self,
        operation: str,
        duration_seconds: float,
        success: bool = True,
        metadata: Dict[str, Any] = None,
    ):
        """
        记录操作指标
        
        参数：
            operation: 操作名称（inference, query, learning 等）
            duration_seconds: 耗时（秒）
            success: 是否成功
            metadata: 其他元数据
        
        注意：本地内存统计和 Prometheus 指标可能不同步，原因如下：
        1. 本地统计有 _max_records 限制（最近 N 条），而 Prometheus 累积所有数据
        2. 本地统计在锁保护下更新，Prometheus 指标更新可能在锁外
        3. 如果 Prometheus 指标系统不可用，本地统计仍然继续记录
        这种设计确保了即使外部指标系统故障，本地监控能力也不受影响
        """
        with self._data_lock:
            # 记录耗时
            self._operation_times[operation].append(duration_seconds)
            if len(self._operation_times[operation]) > self._max_records:
                self._operation_times[operation] = self._operation_times[operation][-self._max_records:]
            
            # 记录计数
            self._operation_counts[operation] += 1
            
            if not success:
                self._error_counts[operation] += 1
        
        # 记录到 Prometheus 指标
        metrics.observe_histogram(
            f"operation_{operation}_duration_seconds",
            duration_seconds,
        )
        metrics.increment_counter(
            f"operation_{operation}_total",
            labels={"status": "success" if success else "failure"},
        )
        
        # 检查慢操作
        if operation == "query" and duration_seconds > self._slow_query_threshold:
            structured_logger.warning(
                f"慢查询检测",
                operation=operation,
                duration_ms=duration_seconds * 1000,
                metadata=metadata,
            )
        elif operation == "inference" and duration_seconds > self._slow_inference_threshold:
            structured_logger.warning(
                f"慢推理检测",
                operation=operation,
                duration_ms=duration_seconds * 1000,
                metadata=metadata,
            )
    
    def record_cache_hit(self):
        """记录缓存命中"""
        with self._data_lock:
            self._cache_hits += 1
        metrics.increment_counter("cache_hits_total")
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        with self._data_lock:
            self._cache_misses += 1
        metrics.increment_counter("cache_misses_total")
    
    def get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        with self._data_lock:
            total = self._cache_hits + self._cache_misses
            if total == 0:
                return 0.0
            return self._cache_hits / total
    
    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """
        获取操作统计信息
        
        返回：
            包含平均值、P50、P95、P99 等统计指标
        """
        with self._data_lock:
            times = self._operation_times.get(operation, [])
            if not times:
                return {
                    "operation": operation,
                    "count": 0,
                    "avg_ms": 0,
                    "p50_ms": 0,
                    "p95_ms": 0,
                    "p99_ms": 0,
                    "error_count": self._error_counts.get(operation, 0),
                }
            
            sorted_times = sorted(times)
            n = len(sorted_times)
            
            return {
                "operation": operation,
                "count": self._operation_counts.get(operation, 0),
                "avg_ms": sum(times) / n * 1000,
                "p50_ms": sorted_times[int(n * 0.5)] * 1000,
                "p95_ms": sorted_times[int(n * 0.95)] * 1000,
                "p99_ms": sorted_times[int(n * 0.99)] * 1000,
                "min_ms": sorted_times[0] * 1000,
                "max_ms": sorted_times[-1] * 1000,
                "error_count": self._error_counts.get(operation, 0),
                "error_rate": self._error_counts.get(operation, 0) / self._operation_counts.get(operation, 1),
            }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有操作的统计信息"""
        operations = set(self._operation_times.keys()) | set(self._operation_counts.keys())
        return {
            "operations": {op: self.get_operation_stats(op) for op in operations},
            "cache": {
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate": self.get_cache_hit_rate(),
            },
        }


# 全局操作指标采集器
operation_metrics = OperationMetrics()


# ==================== 指标采集装饰器 ====================

def track_operation(operation: str):
    """
    操作指标采集装饰器
    
    自动采集函数执行的耗时和成功/失败状态。
    
    使用示例：
        @track_operation("inference")
        def run_inference(...):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True
            try:
                return func(*args, **kwargs)
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start_time
                operation_metrics.record_operation(
                    operation=operation,
                    duration_seconds=duration,
                    success=success,
                )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start_time
                operation_metrics.record_operation(
                    operation=operation,
                    duration_seconds=duration,
                    success=success,
                )
        
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ==================== 健康检查增强 ====================

def get_enriched_health_data() -> Dict[str, Any]:
    """
    获取丰富的健康检查数据
    
    用于健康检查端点，返回系统各项指标。
    """
    from ..utils.config import get_config
    
    config = get_config()
    
    # 获取操作指标
    op_stats = operation_metrics.get_all_stats()
    
    # 获取性能快照
    perf_snapshot = performance_monitor.get_snapshot(
        active_connections=0,
        cache_hit_rate=op_stats["cache"]["hit_rate"],
    )
    
    # 构建健康数据
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "uptime_seconds": time.time() - _start_time if '_start_time' in dir() else 0,
        
        # 系统配置
        "config": {
            "debug": config.app.debug,
            "log_level": config.app.log_level,
            "llm_configured": config.llm.is_configured(),
        },
        
        # 性能指标
        "performance": {
            "requests_per_second": perf_snapshot.requests_per_second,
            "avg_response_time_ms": perf_snapshot.avg_response_time_ms,
            "cache_hit_rate": perf_snapshot.cache_hit_rate,
        },
        
        # 操作指标
        "operations": op_stats,
        
        # 组件状态
        "components": {
            "metrics_collector": "healthy",
            "structured_logger": "healthy" if structured_logger._structured else "degraded",
            "inference_tracer": "healthy" if inference_tracer._enabled else "disabled",
        },
    }
    
    # 检查是否有异常指标
    for op_name, op_stat in op_stats["operations"].items():
        if op_stat.get("error_rate", 0) > 0.1:  # 错误率超过 10%
            health_data["status"] = "degraded"
            health_data.setdefault("warnings", []).append(
                f"High error rate for {op_name}: {op_stat['error_rate']:.2%}"
            )
    
    return health_data


# 启动时间记录
_start_time = time.time()

