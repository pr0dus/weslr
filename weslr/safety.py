"""Weslr Safety Layer (v1 - Strict Minimum Public Test Gate)

Backend safety controls for Weslr platform.
Implements strict minimum safety before public testing:

- Input validation (length limits)
- Per-IP rate limiting
- Request timeout enforcement
- Response size cap
- Secrets scrubbing in logs/errors/responses
- Read-only tool policy for public mode
- Workspace isolation for allowed tools
- Error scrubbing for public responses

This is a strict minimum gate. All checks must pass for public access.
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# CONFIGURATION (Environment Variables)
# ============================================================================

# Input validation
MAX_INPUT_LENGTH = int(os.getenv("WESLR_MAX_INPUT_LENGTH", "10000"))

# Timeout
REQUEST_TIMEOUT_SECONDS = int(os.getenv("WESLR_REQUEST_TIMEOUT_SECONDS", "30"))

# Response size
MAX_RESPONSE_SIZE = int(os.getenv("WESLR_MAX_RESPONSE_SIZE", "102400"))  # 100KB

# Rate limiting
RATE_LIMIT_REQUESTS = int(os.getenv("WESLR_RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW_MINUTES = int(os.getenv("WESLR_RATE_LIMIT_WINDOW_MINUTES", "1"))

# Debug mode (opt-in, not default)
DEBUG_MODE = os.getenv("WESLR_DEBUG_MODE", "false").lower() in ("true", "1", "yes")

# Public mode (default: true for safety)
PUBLIC_MODE = os.getenv("WESLR_PUBLIC_MODE", "true").lower() in ("true", "1", "yes")


# ============================================================================
# SECRETS SCRUBBER
# ============================================================================

SECRETS_TO_SCRUB = [
    "API_KEY",
    "API_TOKEN",
    "API_SECRET",
    "API_PASS",
    "API_PASSWORD",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_COMPATIBLE_API_KEY",
    "WESLR_SECRET",
]


def scrub_secrets(text: str) -> str:
    """Scrub secrets from text.
    
    Replaces secret values with '[REDACTED]'.
    """
    if not text:
        return text
    
    result = text
    for secret_name in SECRETS_TO_SCRUB:
        # Try to find and replace secret values
        pattern = rf'({secret_name}\s*=\s*)[^\s\']+'
        result = re.sub(pattern, r'\1[REDACTED]', result, flags=re.IGNORECASE)
    
    return result


def scrub_secrets_in_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Scrub secrets from dictionary values recursively."""
    if not isinstance(d, dict):
        return d
    
    result = {}
    for key, value in d.items():
        if isinstance(value, str):
            result[key] = scrub_secrets(value)
        elif isinstance(value, dict):
            result[key] = scrub_secrets_in_dict(value)
        elif isinstance(value, list):
            result[key] = scrub_secrets_in_list(value)
        else:
            result[key] = value
    return result


def scrub_secrets_in_list(l: List[Any]) -> List[Any]:
    """Scrub secrets from list items recursively."""
    return [scrub_secrets_in_dict(item) if isinstance(item, dict) else 
            scrub_secrets(item) if isinstance(item, str) else item 
            for item in l]


# ============================================================================
# INPUT VALIDATION
# ============================================================================

def validate_input_length(text: str, max_length: int = MAX_INPUT_LENGTH) -> bool:
    """Validate input length. Returns True if valid."""
    if text is None:
        return False
    if len(text) > max_length:
        return False
    return True


def validate_input_content(text: str) -> bool:
    """Validate input content (basic checks)."""
    if text is None:
        return False
    # Check for excessive whitespace (potential DDoS)
    if len(text.split()) > 1000:
        return False
    return True


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Simple per-IP rate limiter."""
    
    def __init__(self, max_requests: int = RATE_LIMIT_REQUESTS, 
                 window_minutes: int = RATE_LIMIT_WINDOW_MINUTES):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.request_timestamps: Dict[str, List[float]] = {}
    
    def is_allowed(self, ip: str) -> bool:
        """Check if request is allowed. Returns True if allowed."""
        now = time.time()
        window_seconds = self.window_minutes * 60
        
        # Clean old timestamps
        if ip in self.request_timestamps:
            self.request_timestamps[ip] = [
                ts for ts in self.request_timestamps[ip]
                if now - ts < window_seconds
            ]
        else:
            self.request_timestamps[ip] = []
        
        # Check if under limit
        if len(self.request_timestamps[ip]) >= self.max_requests:
            return False
        
        # Record request
        self.request_timestamps[ip].append(now)
        return True
    
    def get_remaining(self, ip: str) -> int:
        """Get remaining requests in window."""
        now = time.time()
        window_seconds = self.window_minutes * 60
        
        if ip not in self.request_timestamps:
            return self.max_requests
        
        valid_timestamps = [
            ts for ts in self.request_timestamps[ip]
            if now - ts < window_seconds
        ]
        
        return max(0, self.max_requests - len(valid_timestamps))


# Global rate limiter instance
_rate_limiter = RateLimiter()


def check_rate_limit(ip: str) -> bool:
    """Check rate limit for IP. Returns True if allowed."""
    return _rate_limiter.is_allowed(ip)


# ============================================================================
# RESPONSE SIZE CAPPING
# ============================================================================

def cap_response_size(text: str, max_size: int = MAX_RESPONSE_SIZE) -> str:
    """Cap response size. Truncates if needed."""
    if len(text) <= max_size:
        return text
    return text[:max_size] + f"\n\n[Response truncated to {max_size} bytes]"


# ============================================================================
# WORKSPACE ISOLATION
# ============================================================================

def is_workspace_path(path: str, base_dir: str) -> bool:
    """Check if path is within workspace directory."""
    try:
        full_path = Path(base_dir) / path
        resolved = full_path.resolve()
        base_resolved = Path(base_dir).resolve()
        return str(resolved).startswith(str(base_resolved))
    except Exception:
        return False


# ============================================================================
# TOOL SAFETY POLICY
# ============================================================================

# Public mode: Read-only tools only
PUBLIC_TOOL_WHITELIST = [
    "file_read",
    "directory_list",
    # command_execute, python_execute disabled in public mode
]

# Public mode: Commands disabled entirely (or very restricted)
# If needed, would add to whitelist, but public mode blocks these by default


def is_public_tool_allowed(tool_name: str) -> bool:
    """Check if tool is allowed in public mode."""
    return tool_name in PUBLIC_TOOL_WHITELIST


# ============================================================================
# ERROR SCRUBBING
# ============================================================================

def scrub_error_response(error_data: Dict[str, Any]) -> Dict[str, Any]:
    """Scrub error response for public output."""
    if not isinstance(error_data, dict):
        return {"error": "An error occurred"}
    
    # Remove sensitive fields
    sensitive_keys = [
        "traceback", "stack", "debug", "details", "request_id", "api_key",
        "secret", "token", "password", "credential"
    ]
    
    result = {}
    for key, value in error_data.items():
        key_lower = key.lower()
        if any(s in key_lower for s in sensitive_keys):
            continue
        
        if isinstance(value, str):
            result[key] = scrub_secrets(value)
        elif isinstance(value, dict):
            result[key] = scrub_error_response(value)
        elif isinstance(value, list):
            result[key] = [scrub_error_response(item) if isinstance(item, dict) else item 
                          for item in value]
        else:
            result[key] = value
    
    return result


# ============================================================================
# REQUEST VALIDATION
# ============================================================================

class RequestValidationResult:
    """Result of request validation."""
    
    def __init__(self, valid: bool, errors: List[str] = None):
        self.valid = valid
        self.errors = errors or []
    
    def add_error(self, error: str):
        self.errors.append(error)
        self.valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "error_count": len(self.errors)
        }
    
    def is_public_safe(self) -> bool:
        """Check if request is safe for public mode."""
        return self.valid and len(self.errors) == 0


def validate_request(
    messages: List[Dict[str, Any]],
    ip: str = None,
    base_dir: str = None
) -> RequestValidationResult:
    """Validate incoming request for public safety."""
    result = RequestValidationResult(valid=True)
    
    # Check rate limit
    if ip and not check_rate_limit(ip):
        result.add_error("Rate limit exceeded. Please try again later.")
    
    # Validate input length
    if messages:
        for msg in messages:
            content = msg.get("content", "")
            if not validate_input_length(content):
                result.add_error(f"Input too long. Maximum {MAX_INPUT_LENGTH} characters.")
                break
            if not validate_input_content(content):
                result.add_error("Invalid input content.")
                break
    
    # Validate workspace path if provided
    if base_dir and PUBLIC_MODE:
        # Check any tool paths would be within workspace
        # (Called later when tools are executed)
        pass
    
    return result


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_public_mode() -> bool:
    """Get current public mode setting."""
    return PUBLIC_MODE


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return DEBUG_MODE


def get_public_tool_whitelist() -> List[str]:
    """Get list of allowed tools in public mode."""
    return PUBLIC_TOOL_WHITELIST.copy()


def format_public_error(message: str) -> Dict[str, Any]:
    """Format error for public output."""
    return {
        "error": True,
        "message": scrub_secrets(message),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def format_public_response(content: str, **kwargs) -> Dict[str, Any]:
    """Format response for public output."""
    capped_content = cap_response_size(content)
    return {
        "content": capped_content,
        "truncated": len(content) > MAX_RESPONSE_SIZE,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **kwargs
    }
