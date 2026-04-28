"""WESLR OmniChat Policy Engine V1 — deterministic response policy decision layer.

Decides response type, expansion layers, depth, evidence mode, and LLM usage
for every WESLR query — based on handler output, mode, and safety flags.

Rules are strict and deterministic: same inputs always produce same policy.
LLM formatter is always False in V1 (no LLM yet).
"""

from __future__ import annotations

from typing import Dict, Any


# Guided intent classes that route to the guided response path
_GUIDED_INTENT_CLASSES = frozenset({
    "system_definition_query",
    "origin_query",
    "comparison_query",
    "continuity_explanation",
    "improvement_query",
    "usage_guidance",
    "agi_clarification",
    "self_improvement_clarification",
    "learning_clarification",
})

# Mode → maximum depth
_MODE_MAX_DEPTH: Dict[str, str] = {
    "public_demo_readonly": "standard",
    "local_demo": "deep",
    "private_dev": "expert",
    "gated_beta": "deep",
    "production": "expert",
}


def decide_response_policy(
    response: Dict[str, Any],
    message: str,
    mode: str,
) -> Dict[str, Any]:
    """Decide the expansion policy for a handler response.

    Args:
        response: Handler output dict. Expected fields:
            - path: str — the deterministic handler path label
            - response_text: str — human-readable answer
            - _weslr_deterministic: bool — whether this is a deterministic response
            (may contain additional fields)
        message: Original user message (lowercased by caller)
        mode: Current WESLR mode string

    Returns:
        Policy dict with keys:
            final_response_type: str
            expansion_layers: list[str]
            depth_level: str
            llm_formatter_allowed: bool (always False in V1)
            evidence_mode_offered: bool
            evidence_mode_active: bool (always False in V1)
            policy_reason: str
    """
    path = response.get("path", "unknown") if response else "unknown"

    # ── Priority 1: Safety override — blocked write ──────────────────────────
    if path == "blocked_write":
        return _policy_blocked_write(mode)

    # ── Priority 2: Fallback ─────────────────────────────────────────────────
    if path == "fallback_safe" or path == "rate_limited":
        return _policy_fallback(mode)

    # ── Priority 3: Guided query ──────────────────────────────────────────────
    # Check if the handler path matches a guided class or if the response
    # targets one of the known guided intent classes.
    intent_class = _extract_intent_class(response)
    if intent_class in _GUIDED_INTENT_CLASSES or _is_guided_path(path):
        return _policy_guided(mode, response)

    # ── Priority 4: Deterministic handler ─────────────────────────────────────
    if response.get("_weslr_deterministic"):
        return _policy_deterministic(mode, response)

    # ── Catch-all: unknown response type → treated as deterministic ─────────────
    return _policy_deterministic(mode, response)


# ─── Individual policy builders ────────────────────────────────────────────────

def _policy_blocked_write(mode: str) -> Dict[str, Any]:
    max_depth = _MODE_MAX_DEPTH.get(mode, "standard")
    return {
        "final_response_type": "blocked_write",
        "expansion_layers": ["L1", "L2", "L4"],
        "depth_level": min_depth("standard", max_depth),
        "llm_formatter_allowed": False,
        "evidence_mode_offered": False,
        "evidence_mode_active": False,
        "policy_reason": "Safety override — write attempted in mode that blocks writes.",
    }


def _policy_fallback(mode: str) -> Dict[str, Any]:
    max_depth = _MODE_MAX_DEPTH.get(mode, "standard")
    return {
        "final_response_type": "fallback",
        "expansion_layers": ["L1", "L2", "L4"],
        "depth_level": min_depth("standard", max_depth),
        "llm_formatter_allowed": False,
        "evidence_mode_offered": True,
        "evidence_mode_active": False,
        "policy_reason": "No structured handler matched — fallback with guidance and evidence offer.",
    }


def _policy_guided(mode: str, response: Dict[str, Any]) -> Dict[str, Any]:
    max_depth = _MODE_MAX_DEPTH.get(mode, "standard")
    return {
        "final_response_type": "guided",
        "expansion_layers": ["L1", "L2", "L4"],
        "depth_level": min_depth("standard", max_depth),
        "llm_formatter_allowed": False,
        "evidence_mode_offered": False,
        "evidence_mode_active": False,
        "policy_reason": "Guided identity or clarification path — pre-authorized structured response.",
    }


def _policy_deterministic(mode: str, response: Dict[str, Any]) -> Dict[str, Any]:
    max_depth = _MODE_MAX_DEPTH.get(mode, "standard")
    return {
        "final_response_type": "deterministic",
        "expansion_layers": ["L1", "L2", "L4"],
        "depth_level": min_depth("standard", max_depth),
        "llm_formatter_allowed": False,
        "evidence_mode_offered": False,
        "evidence_mode_active": False,
        "policy_reason": "Registered deterministic handler — authoritative structured answer.",
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _extract_intent_class(response: Dict[str, Any]) -> str:
    """Extract intent_class from response if present."""
    return response.get("intent_class", "")


def _is_guided_path(path: str) -> bool:
    """Known guided handler path prefixes."""
    guided_prefixes = (
        "system_definition",
        "origin_query",
        "comparison_query",
        "continuity_explanation",
        "improvement_query",
        "usage_guidance",
        "agi_clarification",
        "self_improvement_clarification",
        "learning_clarification",
        "guided_",
    )
    return any(path.startswith(p) for p in guided_prefixes)


def min_depth(requested: str, max_allowed: str) -> str:
    """Return the lower of two depth levels."""
    order = ["minimal", "standard", "deep", "expert"]
    try:
        req_idx = order.index(requested)
    except ValueError:
        req_idx = order.index("standard")
    try:
        max_idx = order.index(max_allowed)
    except ValueError:
        max_idx = order.index("standard")
    return order[min(req_idx, max_idx)]
