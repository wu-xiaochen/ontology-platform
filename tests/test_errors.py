"""
test_errors.py - 错误处理模块测试

覆盖 src/core/errors.py 的核心功能：
- 错误码枚举
- 自定义异常类
- 错误响应模型
- 错误处理器
- 错误恢复策略
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.errors import (
    ErrorCode, ErrorSeverity, ErrorResponse, ErrorDetail,
    OntologyPlatformException, NotFoundException, ValidationException,
    UnauthorizedException, ForbiddenException, RateLimitException,
    GraphConnectionException, ReasoningTimeoutException, CacheException,
    ErrorHandler, ErrorRecovery,
)


class TestErrorCode:
    """测试错误码枚举"""

    def test_general_error_codes(self):
        """测试通用错误码"""
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.UNAUTHORIZED == "UNAUTHORIZED"
        assert ErrorCode.FORBIDDEN == "FORBIDDEN"
        assert ErrorCode.RATE_LIMITED == "RATE_LIMITED"

    def test_ontology_error_codes(self):
        """测试本体相关错误码"""
        assert ErrorCode.ONTOLOGY_NOT_FOUND == "ONTOLOGY_NOT_FOUND"
        assert ErrorCode.SCHEMA_VIOLATION == "SCHEMA_VIOLATION"
        assert ErrorCode.INVALID_TRIPLE == "INVALID_TRIPLE"

    def test_reasoning_error_codes(self):
        """测试推理相关错误码"""
        assert ErrorCode.REASONING_TIMEOUT == "REASONING_TIMEOUT"
        assert ErrorCode.REASONING_DEPTH_EXCEEDED == "REASONING_DEPTH_EXCEEDED"


class TestErrorSeverity:
    """测试错误严重级别"""

    def test_severity_levels(self):
        """测试严重级别枚举"""
        assert ErrorSeverity.DEBUG == "debug"
        assert ErrorSeverity.INFO == "info"
        assert ErrorSeverity.WARNING == "warning"
        assert ErrorSeverity.ERROR == "error"
        assert ErrorSeverity.CRITICAL == "critical"


class TestErrorResponse:
    """测试错误响应模型"""

    def test_create_error_response(self):
        """测试创建错误响应"""
        response = ErrorResponse(
            code=ErrorCode.NOT_FOUND,
            message="Resource not found: test"
        )
        assert response.error is True
        assert response.code == ErrorCode.NOT_FOUND
        assert response.message == "Resource not found: test"
        assert response.timestamp is not None

    def test_error_response_with_details(self):
        """测试带详情的错误响应"""
        details = [ErrorDetail(field="name", message="Required field")]
        response = ErrorResponse(
            code=ErrorCode.VALIDATION_ERROR,
            message="Validation failed",
            details=details
        )
        assert len(response.details) == 1
        assert response.details[0].field == "name"


class TestCustomExceptions:
    """测试自定义异常类"""

    def test_base_exception(self):
        """测试基础异常"""
        exc = OntologyPlatformException("Test error")
        assert str(exc) == "Test error"
        assert exc.code == ErrorCode.INTERNAL_ERROR
        assert exc.status_code == 500
        assert exc.severity == ErrorSeverity.ERROR

    def test_not_found_exception(self):
        """测试 NotFoundException"""
        exc = NotFoundException("Entity", "test_id")
        assert "Entity" in exc.message
        assert "test_id" in exc.message
        assert exc.code == ErrorCode.NOT_FOUND
        assert exc.status_code == 404
        assert exc.severity == ErrorSeverity.INFO

    def test_validation_exception(self):
        """测试 ValidationException"""
        exc = ValidationException("Invalid input")
        assert exc.code == ErrorCode.VALIDATION_ERROR
        assert exc.status_code == 422

    def test_unauthorized_exception(self):
        """测试 UnauthorizedException"""
        exc = UnauthorizedException()
        assert exc.code == ErrorCode.UNAUTHORIZED
        assert exc.status_code == 401

    def test_forbidden_exception(self):
        """测试 ForbiddenException"""
        exc = ForbiddenException()
        assert exc.code == ErrorCode.FORBIDDEN
        assert exc.status_code == 403

    def test_rate_limit_exception(self):
        """测试 RateLimitException"""
        exc = RateLimitException(retry_after=30)
        assert exc.code == ErrorCode.RATE_LIMITED
        assert exc.status_code == 429
        assert exc.retry_after == 30

    def test_graph_connection_exception(self):
        """测试 GraphConnectionException"""
        exc = GraphConnectionException()
        assert exc.code == ErrorCode.GRAPH_CONNECTION_ERROR
        assert exc.status_code == 503

    def test_reasoning_timeout_exception(self):
        """测试 ReasoningTimeoutException"""
        exc = ReasoningTimeoutException(max_time=5.0)
        assert "5.0" in exc.message
        assert exc.code == ErrorCode.REASONING_TIMEOUT
        assert exc.status_code == 408

    def test_cache_exception(self):
        """测试 CacheException"""
        exc = CacheException("Redis unavailable")
        assert exc.code == ErrorCode.CACHE_ERROR
        assert exc.status_code == 500

    def test_exception_to_error_response(self):
        """测试异常转换为错误响应"""
        exc = NotFoundException("Entity", "test")
        response = exc.to_error_response()
        assert isinstance(response, ErrorResponse)
        assert response.code == ErrorCode.NOT_FOUND


class TestErrorHandler:
    """测试错误处理器"""

    def test_log_error(self):
        """测试记录错误"""
        handler = ErrorHandler()
        error = ValueError("test error")
        error_id = handler.log_error(error)
        assert error_id is not None
        assert len(error_id) == 8  # UUID 前 8 位

    def test_get_error_stats(self):
        """测试获取错误统计"""
        handler = ErrorHandler()
        # 记录一些错误
        handler.log_error(ValueError("err1"))
        handler.log_error(ValueError("err2"))
        handler.log_error(TypeError("err3"))

        stats = handler.get_error_stats()
        assert stats["total_errors"] == 3
        assert stats["error_counts"]["ValueError"] == 2
        assert stats["error_counts"]["TypeError"] == 1
        assert len(stats["recent_errors"]) == 3

    def test_error_log_size_limit(self):
        """测试错误日志大小限制"""
        handler = ErrorHandler()
        handler._max_log_size = 5
        for i in range(10):
            handler.log_error(ValueError(f"error_{i}"))
        assert len(handler._error_log) == 5


class TestErrorRecovery:
    """测试错误恢复策略"""

    def test_with_fallback(self):
        """测试 fallback 装饰器"""
        @ErrorRecovery.with_fallback(fallback_value="default")
        def failing_func():
            raise ValueError("boom")

        result = failing_func()
        assert result == "default"

    def test_with_fallback_success(self):
        """测试 fallback 在函数正常时不介入"""
        @ErrorRecovery.with_fallback(fallback_value="default")
        def success_func():
            return "ok"

        result = success_func()
        assert result == "ok"

    def test_with_retry_success(self):
        """测试 retry 在最终成功时返回结果"""
        call_count = {"n": 0}

        @ErrorRecovery.with_retry(max_retries=3, delay=0.01)
        def eventually_succeeds():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("not yet")
            return "success"

        result = eventually_succeeds()
        assert result == "success"
        assert call_count["n"] == 3

    def test_with_retry_exhausted(self):
        """测试 retry 次数耗尽后抛出异常"""
        @ErrorRecovery.with_retry(max_retries=2, delay=0.01)
        def always_fails():
            raise ValueError("always")

        with pytest.raises(ValueError, match="always"):
            always_fails()
