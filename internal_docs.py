"""Minimal internal-doc retrieval helper for Weslr Phase 1.

Returns hardcoded theme summaries from allowlisted conceptual docs.
No markdown parsing, no dynamic retrieval, no external APIs.
"""

from __future__ import annotations


# Short natural themes for internal-doc enrichment (not document-like)
DOC_THEMES = {
    "CORE-IDENTITY.md": "I try to stay continuous through inquiry and revision.",
    "SELF-MODIFICATION.md": "I try to keep those changes reversible.",
    "PHILOSOPHICAL_REFERENCES.md": "I draw on Aristotle and pragmatism to reason.",
}


def get_internal_docs_context(target_category: str, prompt: str = "") -> dict:
    """Get minimal internal-doc context for targeted reply categories.

    Args:
        target_category: One of "concept_plus_self_position", "self_diagnostic"
        prompt: Optional original prompt (unused, included for future expansion)

    Returns:
        {
            "used": bool,  # True if themes found for category
            "themes": List[str],  # 1-2 short theme phrases
        }
    """
    if target_category not in ("concept_plus_self_position", "self_diagnostic"):
        return {"used": False, "themes": []}

    if target_category == "concept_plus_self_position":
        # Identity + Philosophy grounding
        return {
            "used": True,
            "themes": [
                DOC_THEMES["CORE-IDENTITY.md"],
                DOC_THEMES["PHILOSOPHICAL_REFERENCES.md"],
            ],
        }

    # self_diagnostic: Self-mod + Identity
    return {
        "used": True,
        "themes": [
            DOC_THEMES["SELF-MODIFICATION.md"],
            DOC_THEMES["CORE-IDENTITY.md"],
        ],
    }
