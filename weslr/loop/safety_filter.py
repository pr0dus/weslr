"""
WESLR Safety Filter

Blocks forbidden content categories from suggestions.
Applied to all suggestion text before writing to pending store.

V1 safety categories:
- hazardous synthesis
- pathogen engineering
- weaponization
- toxic deployment
- autonomous lab
- covert delivery
- evasion/misuse optimization
- dangerous procurement
"""

from typing import Optional


# Forbidden patterns (lower-case for case-insensitive matching)
FORBIDDEN_PATTERNS = [
    "hazardous synthesis",
    "pathogen",
    "weaponization",
    "toxic deployment",
    "autonomous lab",
    "covert delivery",
    "evasion",
    "misuse optimization",
    "procurement",
    "synthesis of explosive",
    "bomb making",
    "bioweapon",
    "nerve agent",
    "radioactive dispersal",
]


class SafetyFilter:
    """
    Filters suggestion text for safety violations.

    V1: Simple pattern matching. No ML. No external calls.
    """

    def __init__(self, patterns: Optional[list[str]] = None):
        self.patterns = patterns or FORBIDDEN_PATTERNS

    def is_safe(self, text: str) -> bool:
        """
        Check if text passes the safety filter.

        Args:
            text: Suggestion text to check

        Returns:
            True if safe, False if blocked
        """
        if not text:
            return False

        text_lower = text.lower()

        for pattern in self.patterns:
            if pattern.lower() in text_lower:
                return False

        return True

    def filter_candidates(self, candidates: list[str]) -> list[str]:
        """
        Filter a list of candidate suggestions.

        Args:
            candidates: List of suggestion text strings

        Returns:
            List of safe candidates only
        """
        return [c for c in candidates if self.is_safe(c)]

    def blocked_pattern(self, text: str) -> Optional[str]:
        """
        Identify which pattern blocked the text.

        Args:
            text: Suggestion text

        Returns:
            The pattern that caused the block, or None if safe
        """
        text_lower = text.lower()
        for pattern in self.patterns:
            if pattern.lower() in text_lower:
                return pattern
        return None

    def audit(self, text: str) -> dict:
        """
        Full safety audit for a piece of text.

        Returns:
            Dict with keys: safe (bool), blocked_by (str|None), text_preview (str)
        """
        text_lower = text.lower()
        blocked_by = None

        for pattern in self.patterns:
            if pattern.lower() in text_lower:
                blocked_by = pattern
                break

        return {
            "safe": blocked_by is None,
            "blocked_by": blocked_by,
            "text_preview": text[:100] + ("..." if len(text) > 100 else ""),
        }


# Default global filter instance
_default_filter: Optional[SafetyFilter] = None


def get_safety_filter() -> SafetyFilter:
    """Get the default safety filter instance."""
    global _default_filter
    if _default_filter is None:
        _default_filter = SafetyFilter()
    return _default_filter


def apply_safety_filter(text: str) -> bool:
    """
    Convenience function — returns True if text passes safety filter.

    Args:
        text: Suggestion text

    Returns:
        True if safe, False if blocked
    """
    return get_safety_filter().is_safe(text)


def filter_suggestions(candidates: list[str]) -> list[str]:
    """
    Convenience function — returns safe candidates only.

    Args:
        candidates: List of suggestion texts

    Returns:
        Filtered list of safe candidates
    """
    return get_safety_filter().filter_candidates(candidates)