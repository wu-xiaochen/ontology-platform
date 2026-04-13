"""
Clawra Platform Interface

自主进化 Agent 框架 - 零硬编码、领域自适应
"""
from .clawra import Clawra, create_clawra
from .core.reasoner import Reasoner, Fact
from .evolution.unified_logic import UnifiedLogicLayer
from .evolution.meta_learner import MetaLearner
from .evolution.rule_discovery import RuleDiscoveryEngine
from .memory.manager import UnifiedMemory
from .agents.orchestrator import Orchestrator
from .agents.metacognition import MetacognitiveAgent

# 向后兼容重导出 - 这些模块已从根目录移至子目录
from .core.loader import OntologyLoader

# 异常类导入添加 try-except 保护，确保即使 core.errors 模块异常也不会导致整个包无法导入
try:
    from .core.errors import (
        OntologyPlatformException, NotFoundException, ValidationException,
        UnauthorizedException, ForbiddenException, RateLimitException
    )
except ImportError as _e:
    # 当 core.errors 模块导入失败时，创建占位异常类以确保代码兼容性
    # 这些占位类会在实际使用时抛出 RuntimeError 提示用户修复依赖
    class OntologyPlatformException(Exception):
        def __init__(self, *args, **kwargs):
            raise RuntimeError(f"OntologyPlatformException 未正确加载，请检查 core.errors 模块: {_e}")
    
    class NotFoundException(OntologyPlatformException):
        pass
    
    class ValidationException(OntologyPlatformException):
        pass
    
    class UnauthorizedException(OntologyPlatformException):
        pass
    
    class ForbiddenException(OntologyPlatformException):
        pass
    
    class RateLimitException(OntologyPlatformException):
        pass

from .core.permissions import Permission, Resource, ResourceType, permission_manager
from .core.security import (
    api_key_manager, rate_limiter, ip_blocker,
    SecurityHeaders, InputValidator, audit_logger, cors_config
)
from .eval.confidence import ConfidenceCalculator, Evidence, ConfidenceResult
from .eval.monitoring import metrics, health_checker, request_logger, performance_monitor
from .eval.performance import inference_cache, cached, profiler
from .eval.export import DataExporter, ExportFormat, ExportOptions, data_exporter
from .llm.caching import query_cache, debug_cache, create_cache
from .llm.cache_strategy import (
    EnhancedLRUCache, TwoLevelCache, RedisCache, CacheWarmer,
    CacheConfig, CacheStrategy
)

__all__ = [
    # 主类
    "Clawra",
    "create_clawra",
    # 核心组件
    "Reasoner",
    "Fact",
    "UnifiedLogicLayer",
    "MetaLearner",
    "RuleDiscoveryEngine",
    "UnifiedMemory",
    # Agent
    "Orchestrator",
    "MetacognitiveAgent",
    # 向后兼容导出 - 核心加载器
    "OntologyLoader",
    # 异常类 - 核心异常体系
    "OntologyPlatformException",
    "NotFoundException",
    "ValidationException",
    "UnauthorizedException",
    "ForbiddenException",
    "RateLimitException",
    # 权限与安全
    "Permission",
    "Resource",
    "ResourceType",
    "permission_manager",
    "api_key_manager",
    "rate_limiter",
    "ip_blocker",
    "SecurityHeaders",
    "InputValidator",
    "audit_logger",
    "cors_config",
    # 置信度计算
    "ConfidenceCalculator",
    "Evidence",
    "ConfidenceResult",
    # 监控与性能
    "metrics",
    "health_checker",
    "request_logger",
    "performance_monitor",
    "inference_cache",
    "cached",
    "profiler",
    # 数据导出
    "DataExporter",
    "ExportFormat",
    "ExportOptions",
    "data_exporter",
    # 缓存系统
    "query_cache",
    "debug_cache",
    "create_cache",
    "EnhancedLRUCache",
    "TwoLevelCache",
    "RedisCache",
    "CacheWarmer",
    "CacheConfig",
    "CacheStrategy",
]
