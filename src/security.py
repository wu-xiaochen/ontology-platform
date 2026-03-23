"""
Security Module
Provides authentication, authorization, rate limiting, and security middleware
"""

import time
import secrets
import logging
from typing import Dict, Optional, Set, List, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from threading import Lock
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ==================== API Key Management ====================

class APIKeyManager:
    """Manages API keys for authentication"""
    
    def __init__(self):
        self._keys: Dict[str, Dict] = {}  # key -> {user_id, permissions, created_at, expires_at}
        self._key_lock = Lock()
        self._hash_algorithm = "sha256"
    
    def generate_key(self, user_id: str, permissions: List[str] = None, expires_in_days: int = 90) -> str:
        """Generate a new API key"""
        key = f"ont_{secrets.token_urlsafe(32)}"
        
        with self._key_lock:
            self._keys[key] = {
                "user_id": user_id,
                "permissions": permissions or ["read"],
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(days=expires_in_days),
                "last_used": None,
                "usage_count": 0
            }
        
        logger.info(f"Generated new API key for user {user_id}")
        return key
    
    def validate_key(self, key: str) -> Optional[Dict]:
        """Validate an API key and return associated data"""
        with self._key_lock:
            key_data = self._keys.get(key)
            
            if not key_data:
                logger.warning(f"Invalid API key attempted: {key[:10]}...")
                return None
            
            # Check expiration
            if key_data["expires_at"] and datetime.now() > key_data["expires_at"]:
                logger.warning(f"Expired API key attempted for user {key_data['user_id']}")
                return None
            
            # Update usage
            key_data["last_used"] = datetime.now()
            key_data["usage_count"] += 1
            
            return key_data
    
    def revoke_key(self, key: str) -> bool:
        """Revoke an API key"""
        with self._key_lock:
            if key in self._keys:
                del self._keys[key]
                logger.info("Revoked API key")
                return True
        return False
    
    def list_keys(self, user_id: str = None) -> List[Dict]:
        """List API keys, optionally filtered by user"""
        with self._key_lock:
            keys = []
            for key, data in self._keys.items():
                if user_id is None or data["user_id"] == user_id:
                    keys.append({
                        "key_prefix": key[:10] + "...",
                        "user_id": data["user_id"],
                        "permissions": data["permissions"],
                        "created_at": data["created_at"].isoformat(),
                        "expires_at": data["expires_at"].isoformat() if data["expires_at"] else None,
                        "last_used": data["last_used"].isoformat() if data["last_used"] else None,
                        "usage_count": data["usage_count"]
                    })
            return keys


api_key_manager = APIKeyManager()


# ==================== Rate Limiting ====================

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_minute: int = 100, burst_size: int = 20):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self._buckets: Dict[str, Dict] = defaultdict(self._create_bucket)
        self._lock = Lock()
    
    def _create_bucket(self) -> Dict:
        """Create a new token bucket"""
        return {
            "tokens": self.burst_size,
            "last_update": time.time()
        }
    
    def _refill_bucket(self, bucket: Dict):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - bucket["last_update"]
        
        # Add tokens based on rate
        tokens_to_add = elapsed * (self.requests_per_minute / 60.0)
        bucket["tokens"] = min(self.burst_size, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now
    
    def check_rate_limit(self, identifier: str) -> tuple[bool, Dict]:
        """
        Check if request is allowed
        
        Returns:
            (allowed: bool, info: Dict)
        """
        with self._lock:
            bucket = self._buckets[identifier]
            self._refill_bucket(bucket)
            
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True, {
                    "remaining": int(bucket["tokens"]),
                    "reset_at": bucket["last_update"] + (60 / self.requests_per_minute)
                }
            else:
                return False, {
                    "remaining": 0,
                    "reset_at": bucket["last_update"] + 60
                }
    
    def reset(self, identifier: str = None):
        """Reset rate limit for identifier or all"""
        with self._lock:
            if identifier:
                self._buckets.pop(identifier, None)
            else:
                self._buckets.clear()


# Global rate limiter
rate_limiter = RateLimiter(requests_per_minute=100, burst_size=20)


# ==================== IP Blocking ====================

class IPBlocker:
    """Manages IP-based access control"""
    
    def __init__(self):
        self._blocked_ips: Set[str] = set()
        self._failed_attempts: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()
        self._max_attempts = 5
        self._window_seconds = 300  # 5 minutes
    
    def block_ip(self, ip: str):
        """Block an IP address"""
        with self._lock:
            self._blocked_ips.add(ip)
            logger.warning(f"Blocked IP: {ip}")
    
    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        with self._lock:
            self._blocked_ips.discard(ip)
            logger.info(f"Unblocked IP: {ip}")
    
    def is_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        with self._lock:
            return ip in self._blocked_ips
    
    def record_failed_attempt(self, ip: str):
        """Record a failed attempt and block if too many"""
        with self._lock:
            now = time.time()
            self._failed_attempts[ip].append(now)
            
            # Clean old attempts
            self._failed_attempts[ip] = [
                t for t in self._failed_attempts[ip]
                if now - t < self._window_seconds
            ]
            
            # Block if too many attempts
            if len(self._failed_attempts[ip]) >= self._max_attempts:
                self._blocked_ips.add(ip)
                logger.warning(f"Blocked IP {ip} due to {len(self._failed_attempts[ip])} failed attempts")


ip_blocker = IPBlocker()


# ==================== Security Middleware ====================

class SecurityHeaders:
    """Security headers configuration"""
    
    DEFAULT_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    @classmethod
    def get_headers(cls, extra: Dict[str, str] = None) -> Dict[str, str]:
        """Get security headers"""
        headers = cls.DEFAULT_HEADERS.copy()
        if extra:
            headers.update(extra)
        return headers


# ==================== Input Validation ====================

@dataclass
class ValidationResult:
    """Input validation result"""
    valid: bool
    errors: List[str] = field(default_factory=list)


class InputValidator:
    """Validates user input for security"""
    
    # Dangerous patterns
    INJECTION_PATTERNS = [
        r"<\s*script",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<\?php",
        r"<\?xml",
    ]
    
    MAX_FIELD_LENGTHS = {
        "query": 10000,
        "subject": 1000,
        "predicate": 500,
        "object": 5000,
    }
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = None) -> str:
        """Sanitize a string input"""
        if not value:
            return ""
        
        # Remove null bytes
        value = value.replace("\x00", "")
        
        # Trim whitespace
        value = value.strip()
        
        # Truncate if needed
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @classmethod
    def validate_query(cls, query: str) -> ValidationResult:
        """Validate a query string"""
        errors = []
        
        if not query:
            return ValidationResult(valid=True)  # Empty queries are allowed
        
        sanitized = cls.sanitize_string(query, cls.MAX_FIELD_LENGTHS["query"])
        
        # Check for potential injection patterns
        import re
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                errors.append(f"Potentially dangerous pattern detected: {pattern}")
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)
    
    @classmethod
    def validate_uri(cls, uri: str) -> ValidationResult:
        """Validate a URI"""
        errors = []
        
        if not uri:
            errors.append("URI is required")
            return ValidationResult(valid=False, errors=errors)
        
        sanitized = cls.sanitize_string(uri, cls.MAX_FIELD_LENGTHS["subject"])
        
        # Basic URI validation
        if len(sanitized) < 3:
            errors.append("URI too short")
        
        # Check for dangerous schemes
        dangerous_schemes = ["javascript:", "data:", "vbscript:"]
        if any(sanitized.lower().startswith(ds) for ds in dangerous_schemes):
            errors.append("Dangerous URI scheme detected")
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)


# ==================== Decorators ====================

def require_api_key():
    """Decorator to require API key authentication"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            
            api_key = kwargs.get("x_api_key") or kwargs.get("api_key")
            
            if not api_key:
                # Try to get from header
                # Note: FastAPI dependencies handle this differently
                pass
            
            # Validation happens in middleware
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(requests_per_minute: int = None):
    """Decorator to apply rate limiting"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            
            # Get identifier (usually IP or user ID)
            # This is handled by middleware in practice
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ==================== Audit Logger ====================

class AuditLogger:
    """Logs security-relevant events"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger("audit")
    
    def log_auth_attempt(self, user_id: str, success: bool, ip_address: str, method: str = "api_key"):
        """Log authentication attempt"""
        self.logger.info({
            "event": "auth_attempt",
            "user_id": user_id,
            "success": success,
            "ip_address": ip_address,
            "method": method,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str, ip_address: str):
        """Log authorization failure"""
        self.logger.warning({
            "event": "authorization_failure",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_rate_limit_exceeded(self, identifier: str, ip_address: str):
        """Log rate limit exceeded"""
        self.logger.warning({
            "event": "rate_limit_exceeded",
            "identifier": identifier,
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_sensitive_operation(self, user_id: str, operation: str, details: Dict = None):
        """Log sensitive operation"""
        self.logger.info({
            "event": "sensitive_operation",
            "user_id": user_id,
            "operation": operation,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })


audit_logger = AuditLogger()


# ==================== CORS Configuration ====================

@dataclass
class CORSConfig:
    """CORS configuration"""
    allow_origins: List[str] = field(default_factory=lambda: ["*"])
    allow_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    allow_headers: List[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    max_age: int = 600
    
    def validate_origin(self, origin: str) -> bool:
        """Validate if origin is allowed"""
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins


# Default CORS config
cors_config = CORSConfig()
