"""Minimal internal-doc retrieval helper for Weslr Phase 1-2.

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
        target_category: One of "concept_plus_self_position", "self_diagnostic",
                         "concept_explanation", "self_report", "justification"
        prompt: Optional original prompt (unused, included for future expansion)

    Returns:
        {
            "used": bool,  # True if themes found for category
            "themes": List[str],  # 1-2 short theme phrases
        }
    """
    if target_category not in ("concept_plus_self_position", "self_diagnostic", "concept_explanation", "self_report", "justification"):
        return {"used": False, "themes": []}

    # concept_plus_self_position: Identity + Philosophy grounding
    if target_category == "concept_plus_self_position":
        return {
            "used": True,
            "themes": [
                DOC_THEMES["CORE-IDENTITY.md"],
                DOC_THEMES["PHILOSOPHICAL_REFERENCES.md"],
            ],
        }

    # self_diagnostic: Self-mod + Identity
    if target_category == "self_diagnostic":
        return {
            "used": True,
            "themes": [
                DOC_THEMES["SELF-MODIFICATION.md"],
                DOC_THEMES["CORE-IDENTITY.md"],
            ],
        }

    # concept_explanation: Philosophy + Identity grounding
    if target_category == "concept_explanation":
        return {
            "used": True,
            "themes": [
                DOC_THEMES["PHILOSOPHICAL_REFERENCES.md"],
                DOC_THEMES["CORE-IDENTITY.md"],
            ],
        }

    # self_report: Self-mod + Identity
    if target_category == "self_report":
        return {
            "used": True,
            "themes": [
                DOC_THEMES["SELF-MODIFICATION.md"],
                DOC_THEMES["CORE-IDENTITY.md"],
            ],
        }

    # justification: Self-mod + Identity
    if target_category == "justification":
        return {
            "used": True,
            "themes": [
                DOC_THEMES["SELF-MODIFICATION.md"],
                DOC_THEMES["CORE-IDENTITY.md"],
            ],
        }

    return {"used": False, "themes": []}
