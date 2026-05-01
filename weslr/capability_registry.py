"""WESLR Capability Registry V1 — Read-Only Registry

Provides structured self-map of WESLR's live capabilities.
Registry entries are loaded from capability_registry.json at startup.
This module is READ-ONLY — no writes, no suggestions, no LLM calls.

Architecture:
- Registry entries define what WESLR can do
- Entries are maintained in capability_registry.json
- This module provides read-only query API
- No execution, no routing — only registry lookup
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Default registry path
_REGISTRY_FILENAME = "capability_registry.json"


def _default_registry_path() -> Path:
    """Resolve registry path relative to this module."""
    return Path(__file__).resolve().parent / _REGISTRY_FILENAME


def _load_raw_entries(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load and validate raw entries from JSON registry file.
    
    Skips malformed entries silently — does not crash on partial data.
    Returns empty list if registry cannot be loaded.
    """
    registry_path = path or _default_registry_path()
    
    if not registry_path.exists():
        return []
    
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    
    if not isinstance(data, list):
        return []
    
    validated = []
    for entry in data:
        if _is_valid_entry(entry):
            validated.append(entry)
    
    return validated


def _is_valid_entry(entry: Any) -> bool:
    """Check if an entry has the required registry fields."""
    if not isinstance(entry, dict):
        return False
    required = ("capability_id", "category", "label", "status", "risk_level", "authority")
    return all(field in entry for field in required)


def load_registry(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load all registry entries.
    
    Args:
        path: Optional custom path to registry JSON. Defaults to capability_registry.json.
    
    Returns:
        List of validated capability entries. Empty list on load failure.
    """
    return _load_raw_entries(path)


def list_capabilities(
    category: Optional[str] = None,
    status: Optional[str] = None,
    entries: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """List capabilities with optional filtering.
    
    Args:
        category: Filter by category substring match (case-insensitive)
        status: Filter by status (exact match)
        entries: Pre-loaded entries to filter. If None, loads from registry.
    
    Returns:
        Filtered list of capability entries.
    """
    if entries is None:
        entries = load_registry()
    
    result = entries
    
    if category is not None:
        cat_lower = category.lower()
        result = [e for e in result if cat_lower in e.get("category", "").lower()]
    
    if status is not None:
        result = [e for e in result if e.get("status") == status]
    
    return result


def get_capability(
    capability_id: str,
    entries: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Get a single capability by capability_id.
    
    Args:
        capability_id: The dot-namespaced capability ID (e.g. "evidence.search")
        entries: Pre-loaded entries. If None, loads from registry.
    
    Returns:
        The matching capability entry, or None if not found.
    """
    if entries is None:
        entries = load_registry()
    
    for entry in entries:
        if entry.get("capability_id") == capability_id:
            return entry
    return None


def get_by_slash_command(
    command: str,
    entries: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Look up a capability by its slash command alias.
    
    Args:
        command: Slash command string (with or without leading slash, e.g. "/help" or "help")
        entries: Pre-loaded entries. If None, loads from registry.
    
    Returns:
        The matching capability entry, or None if not found.
    """
    # Normalize: strip leading slash, lowercase
    normalized = command.strip().lstrip("/").lower()
    
    if entries is None:
        entries = load_registry()
    
    for entry in entries:
        slash_commands = entry.get("slash_commands", [])
        for cmd in slash_commands:
            if cmd.strip().lstrip("/").lower() == normalized:
                return entry
    return None


def _normalize_for_search(text: str) -> str:
    """Normalize text for trigger search: lowercase, strip punctuation."""
    text = text.lower()
    # Remove punctuation except apostrophes and hyphens within words
    text = re.sub(r"[^\w\s'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _trigger_matches(phrase: str, triggers: List[str]) -> tuple[int, List[str]]:
    """Score how well a phrase matches trigger phrases.
    
    Returns:
        (match_score, list of matched trigger phrases)
    """
    normalized_phrase = _normalize_for_search(phrase)
    phrase_words = set(normalized_phrase.split())
    matched = []
    
    for trigger in triggers:
        normalized_trigger = _normalize_for_search(trigger)
        trigger_words = set(normalized_trigger.split())
        
        # Exact phrase match
        if normalized_phrase == normalized_trigger:
            matched.append(trigger)
            continue
        
        # All words from trigger appear in phrase (trigger ⊆ phrase)
        if trigger_words and trigger_words.issubset(phrase_words):
            matched.append(trigger)
            continue
        
        # Partial overlap — at least half the trigger words match
        if trigger_words:
            overlap = phrase_words & trigger_words
            if len(overlap) >= len(trigger_words) * 0.5 and len(overlap) >= 1:
                matched.append(trigger)
    
    return len(matched), matched


def search_by_trigger(
    phrase: str,
    entries: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Search capabilities by natural language phrase matching against natural_triggers.
    
    Args:
        phrase: The user message or phrase to match against triggers
        entries: Pre-loaded entries. If None, loads from registry.
    
    Returns:
        List of entries with non-empty trigger matches, sorted by match count descending.
    """
    if entries is None:
        entries = load_registry()
    
    results = []
    
    for entry in entries:
        triggers = entry.get("natural_triggers", [])
        if not triggers:
            continue
        
        match_count, matched_triggers = _trigger_matches(phrase, triggers)
        
        if match_count > 0:
            results.append({
                "entry": entry,
                "match_count": match_count,
                "matched_triggers": matched_triggers,
            })
    
    # Sort by match count descending
    results.sort(key=lambda x: x["match_count"], reverse=True)
    
    return [
        {"capability": r["entry"], "matched_triggers": r["matched_triggers"]}
        for r in results
    ]


def group_capabilities_by_category(
    entries: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Group capability entries by their category.
    
    Args:
        entries: Pre-loaded entries. If None, loads from registry.
    
    Returns:
        Dict mapping category → list of entries in that category.
    """
    if entries is None:
        entries = load_registry()
    
    groups: Dict[str, List[Dict[str, Any]]] = {}
    
    for entry in entries:
        category = entry.get("category", "uncategorized")
        if category not in groups:
            groups[category] = []
        groups[category].append(entry)
    
    return groups


# ---- Convenience factory ----

def get_registry_summary() -> Dict[str, Any]:
    """Get a summary of the loaded registry.
    
    Returns:
        Summary dict with counts by category and status.
    """
    entries = load_registry()
    
    by_category: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    
    for entry in entries:
        cat = entry.get("category", "unknown")
        sta = entry.get("status", "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_status[sta] = by_status.get(sta, 0) + 1
    
    return {
        "total_entries": len(entries),
        "by_category": by_category,
        "by_status": by_status,
        "registry_path": str(_default_registry_path()),
    }
