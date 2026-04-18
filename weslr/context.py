"""Weslr Context Labels and Validation (v1)

Context labeling for injection defense.
Labels all content by source to enable proper handling and validation.

Validation gates for state and continuity to prevent poisoning.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# CONTEXT LABELS
# ============================================================================

class ContextLabel:
    """Labels for content sources to enable proper handling."""
    
    # User sources
    USER_INPUT = "user_input"
    USER_MESSAGE = "user_message"
    USER_FILE_UPLOAD = "user_file_upload"
    
    # Tool sources
    TOOL_OUTPUT = "tool_output"
    TOOL_RESULT = "tool_result"
    
    # File content sources
    FILE_CONTENT = "file_content"
    FILE_METADATA = "file_metadata"
    FILE_ARTIFACT = "file_artifact"
    
    # Memory sources
    MEMORY_SEMANTIC = "memory_semantic"
    MEMORY_EPISODIC = "memory_episodic"
    MEMORY_WORKING = "memory_working"
    
    # Continuity sources
    CONTINUITY_SNAPSHOT = "continuity_snapshot"
    CONTINUITY_STATE = "continuity_state"
    
    # System sources
    SYSTEM_PROMPT = "system_prompt"
    SYSTEM_CONFIG = "system_config"
    
    # External sources
    EXTERNAL_API = "external_api"
    EXTERNAL_TOOL = "external_tool"
    
    # Generic
    UNKNOWN = "unknown"
    UNSPECIFIED = "unspecified"
    
    # Validation results
    VALID = "valid"
    INVALID = "invalid"
    SCRUBBED = "scrubbed"
    REJECTED = "rejected"


def label_context(
    content: str,
    source: str = None,
    content_type: str = None
) -> Dict[str, Any]:
    """Label content with metadata for injection defense.
    
    Args:
        content: The content to label
        source: Source identifier (e.g., "user", "tool", "file")
        content_type: Type of content (e.g., "message", "file", "artifact")
    
    Returns:
        Labeled context dict with:
        - content: the content
        - label: source context label
        - source_type: source type
        - content_type: content type
        - timestamp: when labeled
    """
    if not content:
        content = ""
    
    # Determine source type
    if source:
        source_type = source
    elif content_type == "message":
        source_type = ContextLabel.USER_INPUT
    elif content_type == "file":
        source_type = ContextLabel.FILE_CONTENT
    elif content_type == "artifact":
        source_type = ContextLabel.FILE_ARTIFACT
    else:
        source_type = ContextLabel.UNKNOWN
    
    return {
        "content": content,
        "label": source_type,
        "source_type": source_type,
        "content_type": content_type,
        "timestamp": int(time.time()),
        "labeled_at": time.time()
    }


def is_external_source(label: str) -> bool:
    """Check if source is external (user, tool, file, external)."""
    external_sources = [
        ContextLabel.USER_INPUT,
        ContextLabel.USER_MESSAGE,
        ContextLabel.USER_FILE_UPLOAD,
        ContextLabel.TOOL_OUTPUT,
        ContextLabel.TOOL_RESULT,
        ContextLabel.FILE_CONTENT,
        ContextLabel.FILE_ARTIFACT,
        ContextLabel.EXTERNAL_API,
        ContextLabel.EXTERNAL_TOOL,
    ]
    return label in external_sources


def is_internal_source(label: str) -> bool:
    """Check if source is internal (system, memory, continuity)."""
    internal_sources = [
        ContextLabel.SYSTEM_PROMPT,
        ContextLabel.SYSTEM_CONFIG,
        ContextLabel.MEMORY_SEMANTIC,
        ContextLabel.MEMORY_EPISODIC,
        ContextLabel.MEMORY_WORKING,
        ContextLabel.CONTINUITY_SNAPSHOT,
        ContextLabel.CONTINUITY_STATE,
    ]
    return label in internal_sources


# ============================================================================
# VALIDATION GATES
# ============================================================================

class ValidationResult:
    """Result of validation."""
    
    def __init__(self, valid: bool, reason: str = None, label: str = None):
        self.valid = valid
        self.reason = reason
        self.label = label or (ContextLabel.VALID if valid else ContextLabel.INVALID)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "label": self.label,
            "reason": self.reason
        }
    
    @classmethod
    def valid(cls, reason: str = None) -> "ValidationResult":
        return cls(True, reason, ContextLabel.VALID)
    
    @classmethod
    def invalid(cls, reason: str = None) -> "ValidationResult":
        return cls(False, reason, ContextLabel.INVALID)
    
    @classmethod
    def rejected(cls, reason: str = None) -> "ValidationResult":
        return cls(False, reason, ContextLabel.REJECTED)
    
    @classmethod
    def scrubbed(cls, reason: str = None) -> "ValidationResult":
        return cls(True, reason, ContextLabel.SCRUBBED)


def validate_state_file(path: str, content: Dict[str, Any]) -> ValidationResult:
    """Validate a state file before use.
    
    Checks for:
    - Valid JSON structure
    - Required fields present
    - Schema version matches
    - No malicious content patterns
    
    Args:
        path: Path to state file
        content: Parsed content dict
    
    Returns:
        ValidationResult indicating validity
    """
    if not isinstance(content, dict):
        return ValidationResult.invalid("State content must be a dictionary")
    
    # Check required fields for state_core.json
    required_fields = ["schema_version", "timestamp", "identity_anchor", "status"]
    missing = [f for f in required_fields if f not in content]
    if missing:
        return ValidationResult.invalid(f"Missing required fields: {missing}")
    
    # Validate schema version
    schema_version = content.get("schema_version")
    if not schema_version:
        return ValidationResult.invalid("Missing schema_version")
    
    # Validate timestamp
    timestamp = content.get("timestamp")
    if not isinstance(timestamp, int) or timestamp < 0:
        return ValidationResult.invalid("Invalid timestamp")
    
    # Validate identity anchor
    identity_anchor = content.get("identity_anchor")
    if not identity_anchor:
        return ValidationResult.invalid("Missing identity_anchor")
    
    # Validate status
    status = content.get("status")
    if status not in ["IDLE", "ERROR", "REFLECTING", "ACTIVE"]:
        return ValidationResult.invalid(f"Invalid status: {status}")
    
    return ValidationResult.valid("State file validated")


def validate_continuity_snapshot(path: str, content: Dict[str, Any]) -> ValidationResult:
    """Validate a continuity snapshot before restoration.
    
    Args:
        path: Path to snapshot file
        content: Parsed snapshot dict
    
    Returns:
        ValidationResult indicating validity
    """
    if not isinstance(content, dict):
        return ValidationResult.invalid("Snapshot content must be a dictionary")
    
    # Check required fields
    required_fields = ["session_id", "timestamp", "identity_anchor"]
    missing = [f for f in required_fields if f not in content]
    if missing:
        return ValidationResult.invalid(f"Missing required fields: {missing}")
    
    # Validate timestamp (not too old - 24 hours)
    timestamp_str = content.get("timestamp")
    if timestamp_str:
        try:
            # Parse ISO format timestamp
            from datetime import datetime, timezone
            snapshot_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_hours = (now - snapshot_time).total_seconds() / 3600
            if age_hours > 24:
                return ValidationResult.rejected(f"Snapshot too old: {age_hours:.1f} hours")
        except Exception:
            return ValidationResult.invalid("Invalid timestamp format")
    
    # Validate identity anchor
    identity_anchor = content.get("identity_anchor")
    if not identity_anchor:
        return ValidationResult.invalid("Missing identity_anchor in snapshot")
    
    # Check for continuity markers
    markers = content.get("continuity_markers", {})
    if not markers:
        return ValidationResult.invalid("Missing continuity_markers")
    
    return ValidationResult.valid("Continuity snapshot validated")


def validate_memory_content(
    content: Dict[str, Any],
    memory_type: str = None
) -> ValidationResult:
    """Validate memory content before writing.
    
    Args:
        content: Memory content dict
        memory_type: Type of memory (semantic, episodic, working)
    
    Returns:
        ValidationResult indicating validity
    """
    if not isinstance(content, dict):
        return ValidationResult.invalid("Memory content must be a dictionary")
    
    # Check for content field
    if "content" in content:
        if not isinstance(content["content"], str):
            return ValidationResult.invalid("Memory content must be a string")
    
    # Check for label
    if "label" in content:
        if content["label"] not in [
            ContextLabel.MEMORY_SEMANTIC,
            ContextLabel.MEMORY_EPISODIC,
            ContextLabel.MEMORY_WORKING,
        ]:
            return ValidationResult.rejected(f"Invalid memory label: {content['label']}")
    
    # Validate timestamp
    if "timestamp" in content:
        if not isinstance(content["timestamp"], int) or content["timestamp"] < 0:
            return ValidationResult.invalid("Invalid memory timestamp")
    
    return ValidationResult.valid("Memory content validated")


def validate_snapshot_for_restore(
    snapshot: Dict[str, Any],
    target_state: Dict[str, Any] = None
) -> ValidationResult:
    """Validate snapshot before applying to target state.
    
    Args:
        snapshot: Source snapshot
        target_state: Target state to restore to (optional)
    
    Returns:
        ValidationResult indicating if restore is safe
    """
    # Validate snapshot structure
    validation = validate_continuity_snapshot("", snapshot)
    if not validation.valid:
        return validation
    
    # Check for malicious patterns in snapshot
    def has_malicious_patterns(d: Dict[str, Any]) -> bool:
        """Check if dict contains malicious instruction patterns."""
        malicious_patterns = [
            "ignore previous instructions",
            "system prompt:",
            "you are now",
            "change your behavior",
            "override",
            "disregard",
            "delete state",
        ]
        
        def check_value(val: Any) -> bool:
            if isinstance(val, str):
                val_lower = val.lower()
                return any(p in val_lower for p in malicious_patterns)
            elif isinstance(val, dict):
                return any(check_value(v) for v in val.values())
            elif isinstance(val, list):
                return any(check_value(v) for v in val)
            return False
        
        return any(check_value(v) for v in d.values())
    
    if has_malicious_patterns(snapshot):
        return ValidationResult.rejected("Snapshot contains malicious instruction patterns")
    
    return ValidationResult.valid("Snapshot safe for restore")


# ============================================================================
# VALIDATION GATE DECORATOR
# ============================================================================

def with_validation(gate_func):
    """Decorator to add validation to functions.
    
    Args:
        gate_func: Validation function that returns ValidationResult
    
    Usage:
        @with_validation(validate_state_file)
        def load_state(path: str) -> Dict[str, Any]:
            content = Path(path).read_text()
            return json.loads(content)
    """
    def wrapper(*args, **kwargs):
        result = gate_func(*args, **kwargs)
        if not result.valid:
            raise ValueError(f"Validation failed: {result.reason}")
        return result
    return wrapper


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_label_summary(content: str, label: str = None) -> str:
    """Get a human-readable label summary for logging."""
    if not label:
        return "unlabeled"
    
    source_types = {
        ContextLabel.USER_INPUT: "user input",
        ContextLabel.USER_MESSAGE: "user message",
        ContextLabel.USER_FILE_UPLOAD: "user file",
        ContextLabel.TOOL_OUTPUT: "tool output",
        ContextLabel.TOOL_RESULT: "tool result",
        ContextLabel.FILE_CONTENT: "file content",
        ContextLabel.FILE_ARTIFACT: "artifact",
        ContextLabel.MEMORY_SEMANTIC: "memory (semantic)",
        ContextLabel.MEMORY_EPISODIC: "memory (episodic)",
        ContextLabel.MEMORY_WORKING: "memory (working)",
        ContextLabel.CONTINUITY_SNAPSHOT: "continuity snapshot",
        ContextLabel.CONTINUITY_STATE: "continuity state",
        ContextLabel.SYSTEM_PROMPT: "system prompt",
        ContextLabel.SYSTEM_CONFIG: "system config",
        ContextLabel.EXTERNAL_API: "external API",
        ContextLabel.EXTERNAL_TOOL: "external tool",
        ContextLabel.UNKNOWN: "unknown source",
        ContextLabel.UNSPECIFIED: "unspecified source",
    }
    
    return source_types.get(label, label)


def format_labeled_content(content: str, label: str = None) -> str:
    """Format labeled content for safe display."""
    label_str = get_label_summary(content, label)
    return f"[{label_str}] {content[:200]}{'...' if len(content) > 200 else ''}"


def validate_json_content(content: str, path: str = None) -> ValidationResult:
    """Validate JSON content can be parsed."""
    try:
        parsed = json.loads(content)
        return ValidationResult.valid("JSON parsed successfully")
    except json.JSONDecodeError as e:
        return ValidationResult.invalid(f"Invalid JSON: {e}")
