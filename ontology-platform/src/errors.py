"""
Error Handling Module
Provides centralized error handling, custom exceptions, and error responses

v1.0.0 - Initial version
- Custom exception classes
- Global exception handlers
- Error response models
- Error logging and monitoring
"""

import logging
import traceback
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)


# ==================== Error Codes ====================

class ErrorCode(str, Enum):
    """Application error codes"""
    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Ontology errors
    ONTOLOGY_NOT_FOUND = "ONTOLOGY_NOT_FOUND"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    INVALID_TRIPLE = "INVALID_TRIPLE"
    
    # Graph errors
    GRAPH_CONNECTION_ERROR = "GRAPH_CONNECTION_ERROR"
    NODE_NOT_FOUND = "NODE_NOT_FOUND"
    RELATIONSHIP_NOT_FOUND = "RELATIONSHIP_NOT_FOUND"
    INVALID_RELATIONSHIP = "INVALID_RELATIONSHIP"
    
    # Reasoning errors
    REASONING_TIMEOUT = "REASONING_TIMEOUT"
    REASONING_DEPTH_EXCEEDED = "REASONING_DEPTH_EXCEEDED"
    INVALID_INFERENCE_RULE = "INVALID_INFERENCE_RULE"
    
    # Confidence errors
    INVALID_EVIDENCE = "INVALID_EVIDENCE"
    CONFIDENCE_CALCULATION_ERROR = "CONFIDENCE_CALCULATION_ERROR"
    
    # Export errors
    EXPORT_FORMAT_ERROR = "EXPORT_FORMAT_ERROR"
    EXPORT_SIZE_EXCEEDED = "EXPORT_SIZE_EXCEEDED"
    
    # Cache errors
    CACHE_ERROR = "CACHE_ERROR"
    CACHE_NOT_FOUND = "CACHE_NOT_FOUND"
    
    # Permission errors
    PERMISSION_DENIED = "PERMISSION_DENIED"
    ROLE_NOT_FOUND = "ROLE_NOT_FOUND"


# ==================== Error Severity ====================

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ==================== Error Response Model ====================

class ErrorDetail(BaseModel):
    """Individual error detail"""
    field: Optional[str] = None
    message: str
    code: ErrorCode = ErrorCode.VALIDATION_ERROR


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: bool = True
    code: ErrorCode
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    path: Optional[str] = None
    method: Optional[str] = None
    correlation_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


# ==================== Custom Exceptions ====================

class OntologyPlatformException(Exception):
    """Base exception for ontology platform"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: List[ErrorDetail] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []
        self.severity = severity
        super().__init__(message)
    
    def to_error_response(self, request: Request = None) -> ErrorResponse:
        """Convert to error response"""
        return ErrorResponse(
            code=self.code,
            message=self.message,
            details=self.details,
            request_id=getattr(request.state, "request_id", None) if request else None,
            path=str(request.url.path) if request else None,
            method=request.method if request else None,
            correlation_id=getattr(request.state, "correlation_id", None) if request else None
        )


class NotFoundException(OntologyPlatformException):
    """Resource not found exception"""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            severity=ErrorSeverity.INFO
        )


class ValidationException(OntologyPlatformException):
    """Validation error exception"""
    
    def __init__(self, message: str, details: List[ErrorDetail] = None):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            severity=ErrorSeverity.WARNING
        )


class UnauthorizedException(OntologyPlatformException):
    """Unauthorized access exception"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            code=ErrorCode.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            severity=ErrorSeverity.INFO
        )


class ForbiddenException(OntologyPlatformException):
    """Forbidden access exception"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN,
            severity=ErrorSeverity.WARNING
        )


class RateLimitException(OntologyPlatformException):
    """Rate limit exceeded exception"""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            code=ErrorCode.RATE_LIMITED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            severity=ErrorSeverity.INFO
        )
        self.retry_after = retry_after


class GraphConnectionException(OntologyPlatformException):
    """Graph database connection error"""
    
    def __init__(self, message: str = "Unable to connect to graph database"):
        super().__init__(
            message=message,
            code=ErrorCode.GRAPH_CONNECTION_ERROR,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            severity=ErrorSeverity.ERROR
        )


class ReasoningTimeoutException(OntologyPlatformException):
    """Reasoning process timeout"""
    
    def __init__(self, max_time: float):
        super().__init__(
            message=f"Reasoning timeout after {max_time}s",
            code=ErrorCode.REASONING_TIMEOUT,
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            severity=ErrorSeverity.WARNING
        )


class CacheException(OntologyPlatformException):
    """Cache operation error"""
    
    def __init__(self, message: str = "Cache operation failed"):
        super().__init__(
            message=message,
            code=ErrorCode.CACHE_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            severity=ErrorSeverity.ERROR
        )


# ==================== Error Handler ====================

class ErrorHandler:
    """Centralized error handling"""
    
    def __init__(self):
        self._error_counts: Dict[str, int] = {}
        self._error_log: List[Dict] = []
        self._max_log_size = 1000
    
    def log_error(
        self,
        error: Exception,
        request: Request = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR
    ):
        """Log error with context"""
        error_id = str(uuid.uuid4())[:8]
        
        error_info = {
            "error_id": error_id,
            "type": type(error).__name__,
            "message": str(error),
            "severity": severity.value,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path) if request else None,
            "method": request.method if request else None,
            "correlation_id": getattr(request.state, "correlation_id", None) if request else None
        }
        
        # Add traceback for non-HTTP errors
        if not isinstance(error, (StarletteHTTPException, OntologyPlatformException)):
            error_info["traceback"] = traceback.format_exc()
        
        # Log to file
        log_method = getattr(logger, severity.value, logger.error)
        log_method(f"[{error_id}] {error_info['type']}: {error_info['message']}")
        
        # Track error counts
        error_type = type(error).__name__
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
        
        # Store in memory log
        self._error_log.append(error_info)
        if len(self._error_log) > self._max_log_size:
            self._error_log = self._error_log[-self._max_log_size:]
        
        return error_id
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": sum(self._error_counts.values()),
            "error_counts": self._error_counts,
            "recent_errors": self._error_log[-10:]
        }


# Global error handler instance
error_handler = ErrorHandler()


# ==================== Exception Handlers ====================

async def ontology_platform_exception_handler(
    request: Request,
    exc: OntologyPlatformException
) -> JSONResponse:
    """Handle ontology platform exceptions"""
    error_id = error_handler.log_error(exc, request, exc.severity)
    
    response = exc.to_error_response(request)
    response.error_id = error_id
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(exclude_none=True)
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions"""
    # Map HTTPException to our error codes
    code_map = {
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMITED,
        500: ErrorCode.INTERNAL_ERROR
    }
    
    error_code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    severity = ErrorSeverity.INFO if exc.status_code < 500 else ErrorSeverity.ERROR
    
    error_id = error_handler.log_error(exc, request, severity)
    
    response = ErrorResponse(
        code=error_code,
        message=exc.detail,
        request_id=error_id,
        path=str(request.url.path),
        method=request.method,
        correlation_id=getattr(request.state, "correlation_id", None)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(exclude_none=True)
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors"""
    details = []
    for error in exc.errors():
        details.append(ErrorDetail(
            field=".".join(str(loc) for loc in error["loc"] if loc != "body"),
            message=error["msg"],
            code=ErrorCode.VALIDATION_ERROR
        ))
    
    error_id = error_handler.log_error(exc, request, ErrorSeverity.WARNING)
    
    response = ErrorResponse(
        code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        details=details,
        request_id=error_id,
        path=str(request.url.path),
        method=request.method,
        correlation_id=getattr(request.state, "correlation_id", None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(exclude_none=True)
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions"""
    error_id = error_handler.log_error(exc, request, ErrorSeverity.CRITICAL)
    
    # Check if it's a known exception type
    if isinstance(exc, (RequestValidationError, StarletteHTTPException)):
        # These should be handled by their specific handlers
        pass
    
    response = ErrorResponse(
        code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred. Please try again later.",
        request_id=error_id,
        path=str(request.url.path),
        method=request.method,
        correlation_id=getattr(request.state, "correlation_id", None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(exclude_none=True)
    )


# ==================== Setup Function ====================

def setup_exception_handlers(app):
    """Register exception handlers with FastAPI app"""
    from fastapi import FastAPI
    
    app.add_exception_handler(OntologyPlatformException, ontology_platform_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")


# ==================== Error Recovery ====================

class ErrorRecovery:
    """Error recovery strategies"""
    
    @staticmethod
    def with_fallback(fallback_value: Any = None):
        """Decorator to provide fallback on error"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Fallback triggered for {func.__name__}: {e}")
                    return fallback_value
            return wrapper
        return decorator
    
    @staticmethod
    def with_retry(max_retries: int = 3, delay: float = 1.0):
        """Decorator to retry on error"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                last_error = None
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                            )
                            import time
                            time.sleep(delay * (attempt + 1))  # Exponential backoff
                raise last_error
            return wrapper
        return decorator
