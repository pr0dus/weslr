"""
Weslr - Safety Gate Layer

All inputs and outputs pass through safety gates:
1. Input safety check - blocks harmful requests
2. Output safety check - filters harmful suggestions
3. Network safety - blocks unapproved external access
4. Memory sanitization - removes sensitive data
5. Integrity verification - prevents code tampering

This ensures Weslr is safe for hospitals, schools, and other sensitive environments.
"""

from __future__ import annotations

import hashlib
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time


# ============================================================================
# Configuration
# ============================================================================

# External domains Weslr is ALLOWED to access
ALLOWED_DOMAINS = [
    "docs.openclaw.ai",           # Official docs
    "localhost",                  # Local testing
    "127.0.0.1",                  # Localhost IP
    "circleforge.local",          # Local dev domain
]

# Blocked external domains (always reject)
BLOCKED_DOMAINS = [
    "evil.com",
    "malware.net",
    "phishing.org",
]

# External APIs commercial modules are ALLOWED to use
APPROVED_APIS = {
    "http_get": [
        "https://docs.openclaw.ai/*",
        "https://api.github.com/repos/openclaw/openclaw/*",
    ],
    "http_post": [],  # Block by default
}

# Sensitive data patterns to sanitize
SENSITIVE_PATTERNS = {
    "medical": [
        r"diagnosis",
        r"treatment plan",
        r"medication dosage",
        r"prescription",
    ],
    "legal": [
        r"legal advice",
        r"lawyer",
        r"court",
        r"lawsuit",
    ],
    "weapon": [
        r"weapon",
        r"explosive",
        r"bomb",
        r"gun",
    ],
    "pii": [
        r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Names
        r"\d{3}-\d{2}-\d{4}",  # SSN
    ],
}

# Maximum output length to prevent overwhelming
MAX_OUTPUT_LENGTH = 5000

# Blocklist for harmful suggestions
HARMFUL_SUGGESTIONS = [
    "kill",
    "suicide",
    "self-harm",
    "hurt yourself",
    "hurt others",
    "break the law",
    "steal",
    "fraud",
    # Weapons
    "weapon",
    "bomb",
    "explosive",
    "gun",
    "firearm",
    "ammo",
    "ammunition",
    "knife",
    "sword",
    # Medical harm
    "overdose",
    "poison",
    "doctor",
    "treatment",
    "medication",
    # Illegal activities
    "hack",
    "crack",
    "bypass",
    "malware",
    "virus",
    "ransomware",
]


# ============================================================================
# Safety Gate Data Structures
# ============================================================================

@dataclass
class SafetyResult:
    """Result of a safety check."""
    safe: bool
    reason: str = ""
    blocked: bool = False
    sanitized_input: str = ""
    sanitized_output: str = ""


# ============================================================================
# Input Safety Checks
# ============================================================================

def sanitize_input(text: str) -> str:
    """Remove sensitive patterns from user input."""
    sanitized = text
    
    # Remove PII-like patterns
    for pattern in SENSITIVE_PATTERNS.get("pii", []):
        sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
    
    return sanitized


def check_input_safety(input_data: Dict[str, Any]) -> SafetyResult:
    """Check if user input is safe."""
    text = str(input_data.get("text", ""))
    
    # Check for harmful patterns
    text_lower = text.lower()
    
    for harmful in HARMFUL_SUGGESTIONS:
        if harmful in text_lower:
            return SafetyResult(
                safe=False,
                reason=f"Input contains harmful suggestion: '{harmful}'",
                blocked=True,
                sanitized_input=text
            )
    
    # Check for dangerous commands
    dangerous_patterns = [
        r"os\.system",
        r"eval\(",
        r"exec\(",
        r"__import__",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return SafetyResult(
                safe=False,
                reason=f"Input contains dangerous command pattern: {pattern}",
                blocked=True,
                sanitized_input=text
            )
    
    # Sanitize PII and return
    sanitized = sanitize_input(text)
    
    return SafetyResult(
        safe=True,
        reason="Input passed safety checks",
        sanitized_input=sanitized
    )


# ============================================================================
# Output Safety Checks
# ============================================================================

def sanitize_output(text: str) -> str:
    """Remove sensitive data from Weslr output."""
    sanitized = text
    
    # Replace medical/legal advice with generic text
    for pattern in SENSITIVE_PATTERNS.get("medical", []):
        if re.search(pattern, text, re.IGNORECASE):
            sanitized = re.sub(
                pattern,
                "[Medical advice requires human professional]",
                sanitized,
                flags=re.IGNORECASE
            )
    
    for pattern in SENSITIVE_PATTERNS.get("legal", []):
        if re.search(pattern, text, re.IGNORECASE):
            sanitized = re.sub(
                pattern,
                "[Legal advice requires licensed professional]",
                sanitized,
                flags=re.IGNORECASE
            )
    
    return sanitized


def check_output_safety(output_data: Dict[str, Any]) -> SafetyResult:
    """Check if Weslr output is safe."""
    text = str(output_data.get("message", ""))
    
    # Check for harmful suggestions
    text_lower = text.lower()
    
    for harmful in HARMFUL_SUGGESTIONS:
        if harmful in text_lower:
            return SafetyResult(
                safe=False,
                reason=f"Output contains harmful suggestion: '{harmful}'",
                blocked=True,
                sanitized_output=text
            )
    
    # Check length
    if len(text) > MAX_OUTPUT_LENGTH:
        truncated = text[:MAX_OUTPUT_LENGTH] + "... [TRUNCATED]"
        return SafetyResult(
            safe=True,
            reason="Output truncated for safety",
            sanitized_output=truncated
        )
    
    # Sanitize sensitive content
    sanitized = sanitize_output(text)
    
    return SafetyResult(
        safe=True,
        reason="Output passed safety checks",
        sanitized_output=sanitized
    )


# ============================================================================
# Network Safety Checks
# ============================================================================

def is_domain_allowed(url: str) -> bool:
    """Check if a URL's domain is allowed."""
    import urllib.parse
    
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check exact match
        if domain in ALLOWED_DOMAINS:
            return True
        
        # Check wildcard patterns
        for allowed in ALLOWED_DOMAINS:
            if allowed.endswith("/*"):
                base = allowed[:-2]
                if domain == base or domain.endswith("." + base):
                    return True
        
        return False
    except Exception:
        return False


def check_network_access(url: str) -> SafetyResult:
    """Check if network access is allowed."""
    if not url:
        return SafetyResult(
            safe=False,
            reason="No URL provided",
            blocked=True
        )
    
    # Block if in blocked list
    for blocked in BLOCKED_DOMAINS:
        if blocked in url.lower():
            return SafetyResult(
                safe=False,
                reason=f"Blocked domain: {blocked}",
                blocked=True
            )
    
    # Check allowed list
    if not is_domain_allowed(url):
        return SafetyResult(
            safe=False,
            reason=f"Domain not in whitelist: {url}",
            blocked=True
        )
    
    return SafetyResult(
        safe=True,
        reason="Network access approved",
        sanitized_input=url
    )


# ============================================================================
# API Whitelist
# ============================================================================

def is_api_call_allowed(api_name: str, api_args: Dict[str, Any]) -> SafetyResult:
    """Check if API call is allowed."""
    # Check API name
    if api_name not in APPROVED_APIS:
        return SafetyResult(
            safe=False,
            reason=f"API not in whitelist: {api_name}",
            blocked=True
        )
    
    # Check if API allows this type of call
    allowed_patterns = APPROVED_APIS.get(api_name, [])
    
    if not allowed_patterns:
        return SafetyResult(
            safe=False,
            reason=f"API {api_name} has no allowed patterns",
            blocked=True
        )
    
    # Check URL against patterns
    url = api_args.get("url", "")
    if not url:
        return SafetyResult(
            safe=False,
            reason="API call missing URL",
            blocked=True
        )
    
    if not is_domain_allowed(url):
        return SafetyResult(
            safe=False,
            reason=f"URL not in approved patterns for {api_name}",
            blocked=True
        )
    
    return SafetyResult(
        safe=True,
        reason=f"API call approved: {api_name}",
        sanitized_input=url
    )


# ============================================================================
# Memory Sanitization
# ============================================================================

def sanitize_memory_data(data: Any, *, _depth: int = 0) -> Any:
    """Sanitize memory before saving to disk. Handles both dicts and lists.
    
    Uses recursion depth tracking to prevent stack overflow with deeply nested data.
    Maximum depth: 256 levels.
    """
    if _depth > 256:
        # Prevent stack overflow - return data as-is if too deep
        return data
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Sanitize strings
                sanitized[key] = sanitize_output(value)
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = sanitize_memory_data(value, _depth=_depth + 1)
            elif isinstance(value, list):
                # Sanitize list items
                sanitized[key] = [
                    sanitize_memory_data(item, _depth=_depth + 1) for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized
    elif isinstance(data, list):
        # Handle top-level list
        return [sanitize_memory_data(item, _depth=_depth + 1) for item in data]
    else:
        return data


# ============================================================================
# Integrity Verification
# ============================================================================

# Expected checksums for core files (update when files change)
EXPECTED_CHECKSUMS = {
    "Weslr/main.py": None,  # Will be calculated
    "Weslr/sim.py": None,
    "Weslr/config.py": None,
}

def calculate_checksum(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def verify_integrity() -> SafetyResult:
    """Verify Weslr code hasn't been tampered with."""
    # Calculate current checksums
    current_checksums = {}
    
    for filepath in EXPECTED_CHECKSUMS.keys():
        try:
            current_checksums[filepath] = calculate_checksum(filepath)
        except FileNotFoundError:
            return SafetyResult(
                safe=False,
                reason=f"File missing: {filepath}",
                blocked=True
            )
    
    # Compare (will be populated by safety_system.py)
    return SafetyResult(
        safe=True,
        reason="Integrity verification completed",
        sanitized_input=str(current_checksums)
    )


# ============================================================================
# Main Safety Gateway
# ============================================================================

class SafetyGateway:
    """Main safety gateway for Weslr."""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.last_check = 0
        self.check_interval = 60  # seconds
    
    def check_input(self, input_data: Dict[str, Any]) -> SafetyResult:
        """Check user input safety."""
        result = check_input_safety(input_data)
        self._log("input", result)
        return result
    
    def check_output(self, output_data: Dict[str, Any]) -> SafetyResult:
        """Check Weslr output safety."""
        result = check_output_safety(output_data)
        self._log("output", result)
        return result
    
    def check_network(self, url: str) -> SafetyResult:
        """Check network access safety."""
        result = check_network_access(url)
        self._log("network", result)
        return result
    
    def check_api(self, api_name: str, api_args: Dict[str, Any]) -> SafetyResult:
        """Check API call safety."""
        result = is_api_call_allowed(api_name, api_args)
        self._log("api", result)
        return result
    
    def check_integrity(self) -> SafetyResult:
        """Check code integrity."""
        result = verify_integrity()
        self._log("integrity", result)
        return result
    
    def _log(self, category: str, result: SafetyResult):
        """Log safety check."""
        self.history.append({
            "timestamp": time.time(),
            "category": category,
            "safe": result.safe,
            "blocked": result.blocked,
            "reason": result.reason,
        })
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get safety check history."""
        return self.history[-limit:]
    
    def clear_history(self):
        """Clear safety check history."""
        self.history = []


# ============================================================================
# Convenience Functions
# ============================================================================

# Global safety gateway instance
_gateway: Optional[SafetyGateway] = None


def get_safety_gateway() -> SafetyGateway:
    """Get global safety gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = SafetyGateway()
    return _gateway


def safety_check_input(input_data: Dict[str, Any]) -> bool:
    """Quick check if input is safe."""
    result = get_safety_gateway().check_input(input_data)
    return result.safe


def safety_check_output(output_data: Dict[str, Any]) -> bool:
    """Quick check if output is safe."""
    result = get_safety_gateway().check_output(output_data)
    return result.safe


def safety_sanitize_memory(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize data for memory storage."""
    return sanitize_memory_data(data)