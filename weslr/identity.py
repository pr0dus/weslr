"""Weslr Identity Foundation — Bundle G v1

Minimal identity envelope for principal resolution.
Supports single-user (operator) mode now, extensible for
onboarding/invite-code and multi-principal expansion later.

No persistence yet. No role system yet. No permission model yet.
"""

from __future__ import annotations

from config import DEFAULT_PRINCIPAL, KNOWN_PRINCIPALS


def get_current_principal(
    user_id: str | None = None,
    context: dict | None = None,
) -> str:
    """
    Resolve the canonical principal for this turn.

    Resolution order:
      1. Explicit user_id parameter, if it is in KNOWN_PRINCIPALS
      2. user_id from context dict, if in KNOWN_PRINCIPALS
      3. DEFAULT_PRINCIPAL fallback

    This function is the single canonical place for identity resolution.
    All hardcoded "operator" references should route through here.

    Args:
        user_id: Explicit principal identifier passed by caller.
        context: Optional dict with "user_id" key, e.g. research_context.

    Returns:
        A known principal string. Never returns None.
    """
    # 1. Explicit parameter
    if user_id and isinstance(user_id, str) and user_id.strip():
        candidate = user_id.strip()
        if candidate in KNOWN_PRINCIPALS:
            return candidate

    # 2. Context lookup
    if context and isinstance(context, dict):
        ctx_id = context.get("user_id")
        if ctx_id and isinstance(ctx_id, str) and ctx_id.strip():
            candidate = ctx_id.strip()
            if candidate in KNOWN_PRINCIPALS:
                return candidate

    # 3. Fallback — never return None
    return DEFAULT_PRINCIPAL
