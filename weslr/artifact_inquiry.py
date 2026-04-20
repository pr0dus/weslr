"""
Weslr Artifact Inquiry Suggestion — v1

Minimal, bounded suggestion of one open question when an artifact
clearly warrants it. Uses open_question_registry as backend.

Rules:
- Max 1 question per artifact interaction
- No duplicate questions (checks open registry)
- Source = "weslr"
- Triggered only by clear evidence gaps / confidence gaps
- Additive and reversible only
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from .open_question_registry import add_question, get_open, load_registry

# ── Trigger Detection ─────────────────────────────────────────────────────────

TRIGGER_FIELDS = {
    "confidence", "internal_score", "stability_score", "research_confidence",
    "clarity_score", "reusability_score", "novelty_score", "exportability_score",
}
GAP_INDICATOR_FIELDS = {
    "limitation", "gap_reason", "problem_statement", "existing_solution_friction",
    "substance_warnings", "if_interest_exists",
}


def _score_is_low(value: Any) -> bool:
    """Return True if a score numeric field is low enough to warrant a question."""
    try:
        v = float(value)
        return v < 0.65
    except (TypeError, ValueError):
        return False


def _has_gap_text(value: Any) -> bool:
    """Return True if a text field has non-empty meaningful content."""
    return (isinstance(value, str) and len(value.strip()) > 10) or (isinstance(value, list) and len(value) > 0)





def _artifact_has_clear_gap(artifact_meta: Dict[str, Any]) -> bool:
    """Return True if artifact has clear limitation evidence warranting a question."""
    # Check for low scores
    low_scores = [_score_is_low(artifact_meta.get(f)) for f in TRIGGER_FIELDS]
    if any(low_scores):
        return True
    # Check for gap/limitation text
    for field in GAP_INDICATOR_FIELDS:
        if _has_gap_text(artifact_meta.get(field)):
            return True
    return False


def _build_inquiry_question(artifact_meta: Dict[str, Any]) -> str:
    """Build a single, grounded inquiry question from artifact metadata."""
    # Priority order for question generation
    limitations = artifact_meta.get("limitation")
    if isinstance(limitations, list) and limitations:
        limitation = limitations[0]
    elif isinstance(limitations, str) and limitations:
        limitation = limitations
    else:
        limitation = artifact_meta.get("gap_reason") or artifact_meta.get("problem_statement") or ""

    scores = {}
    for field in ["internal_score", "stability_score", "research_confidence"]:
        v = artifact_meta.get(field)
        if v is not None:
            try:
                scores[field] = float(v)
            except (TypeError, ValueError):
                pass

    # Pick the lowest score to frame the question around
    if scores:
        weakest = min(scores, key=lambda k: scores[k])
        v = scores[weakest]
        if limitation:
            return f"Should the {weakest.replace('_', ' ')} gap ({v:.0%}) and limitation ({limitation[:60]}) both be addressed before external sharing?"
        else:
            return f"Should the {weakest.replace('_', ' ')} gap ({v:.0%}) be addressed before external sharing?"
    elif limitation:
        return f"Should this limitation be addressed before external sharing: {limitation[:80]}?"

    return "What evidence would most increase confidence in this artifact?"


# ── Duplicate Control ──────────────────────────────────────────────────────────

def _already_has_open_question(artifact_link: Optional[str], question_text: str) -> bool:
    """Return True if this artifact/version already has the same or near-identical question open."""
    if not artifact_link:
        return False
    for item in get_open():
        if item.get("linked_artifact_or_version") == artifact_link:
            # Exact question match
            if item["question"] == question_text:
                return True
            # Near-identical (first 60 chars match — catches version variants)
            if item["question"][:60] == question_text[:60]:
                return True
    return False


# ── Main Suggestion Function ────────────────────────────────────────────────────

def suggest_inquiry_for_artifact(
    artifact_meta: Dict[str, Any],
    artifact_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Analyze artifact metadata. If a clear gap exists, suggest one open question.
    
    Returns None if no gap found or if question already exists in registry.
    Returns the created registry item if a question was added.
    
    Call this once per artifact interaction. No automatic repeated calling.
    """
    if not _artifact_has_clear_gap(artifact_meta):
        return None

    question = _build_inquiry_question(artifact_meta)

    # Build artifact link
    artifact_link = artifact_name or artifact_meta.get("id") or artifact_meta.get("title")
    if not artifact_link:
        return None

    # Duplicate check
    if _already_has_open_question(artifact_link, question):
        return None

    # Add to registry
    item = add_question(
        question=question,
        context=_build_context(artifact_meta),
        source="weslr",
        linked_artifact_or_version=artifact_link,
    )
    return item


def _build_context(artifact_meta: Dict[str, Any]) -> str:
    """Build a minimal context string for the question."""
    parts = []
    for field in ["internal_score", "stability_score", "gap_reason"]:
        v = artifact_meta.get(field)
        if v is not None:
            parts.append(f"{field}={v}")
    title = artifact_meta.get("title") or artifact_meta.get("id", "unknown")
    return f"Artifact: {title} | {' | '.join(parts[:3])}"


# ── Surface Integration Helper ───────────────────────────────────────────────────

def surface_inquiry_item(item: Dict[str, Any]) -> str:
    """Format a registry item as a single labeled line for embedding in a response."""
    return f"[Open question: {item['question']}]"


# ── Resolution Suggestion ───────────────────────────────────────────────────────

SCORE_FIELDS = {"internal_score", "stability_score", "research_confidence",
                "clarity_score", "reusability_score", "novelty_score", "exportability_score"}
TEXT_COMPARE_FIELDS = {"gap_reason", "problem_statement", "limitation", "limitation_reason",
                       "existing_solution_friction", "if_interest_exists"}


def _keywords_from_meta(meta: Dict[str, Any]) -> set:
    """Extract all meaningful keywords from artifact metadata."""
    keywords = set()
    for field in ["title", "artifact_type", "category", "family", "niche_theme",
                 "problem_statement", "gap_reason", "limitation"]:
        v = meta.get(field)
        if isinstance(v, str):
            for word in v.lower().split():
                if len(word) > 4:
                    keywords.add(word)
    return keywords


def _keywords_from_question(question: str) -> set:
    """Extract keywords from an open question text."""
    return {w.lower() for w in question.split() if len(w) > 4}


def _score_improvement(meta: Dict[str, Any], linked_question: Dict[str, Any]) -> Optional[Dict]:
    """Detect if this artifact significantly improves a score field relevant to the question."""
    context = linked_question.get("context", "")
    for field in SCORE_FIELDS:
        v = meta.get(field)
        if v is None:
            continue
        # Check if the question was about this field
        if field.replace("_", " ") in context.lower() or field in context:
            try:
                score_v = float(v)
                if score_v >= 0.65:
                    return {"field": field, "value": score_v}
            except (TypeError, ValueError):
                pass
    return None


def _match_resolution(meta: Dict[str, Any], exclude_ids: Optional[set] = None) -> Optional[Dict[str, Any]]:
    """
    Find the best open question this artifact might resolve.
    
    Match strategy:
    1. linked_artifact_or_version prefix match (v1→v2)
    2. keyword overlap between question text and artifact fields
    3. score improvement on a field mentioned in the question context
    """
    artifact_name = meta.get("title") or meta.get("id") or ""
    artifact_keywords = _keywords_from_meta(meta)

    candidates = []
    exclude_ids = exclude_ids or set()
    for item in get_open():
        if item["id"] in exclude_ids:
            continue
        linked = item.get("linked_artifact_or_version", "") or ""
        question_keywords = _keywords_from_question(item["question"])
        context = item.get("context", "")

        score_signal = None
        # Strategy 1: version suffix match (e.g., "governance_transparency_review:v2" matches "governance_transparency_review")
        if artifact_name and linked:
            base_link = linked.split(":")[0] if ":" in linked else linked
            base_name = artifact_name.split(":")[0] if ":" in artifact_name else artifact_name
            if base_link and base_name and base_link == base_name and linked != artifact_name:
                score_signal = "version_upgrade"

        # Strategy 2: keyword overlap (at least 2 shared significant words)
        overlap = artifact_keywords & question_keywords
        if len(overlap) >= 2:
            score_signal = score_signal or "keyword_overlap"

        # Strategy 3: score improvement
        improvement = _score_improvement(meta, item)
        if improvement:
            score_signal = score_signal or "score_improvement"

        if score_signal:
            candidates.append((score_signal, len(overlap), item))

    if not candidates:
        return None

    # Sort by signal priority: version_upgrade > score_improvement > keyword_overlap
    signal_priority = {"version_upgrade": 0, "score_improvement": 1, "keyword_overlap": 2}
    candidates.sort(key=lambda c: (signal_priority.get(c[0], 3), -c[1]))
    best_signal, _, best_item = candidates[0]

    return _build_resolution(best_item, meta, best_signal)


def _build_resolution(question_item: Dict[str, Any], meta: Dict[str, Any], signal: str) -> Dict[str, Any]:
    """Build a resolution suggestion dict from matched question + artifact."""
    title = meta.get("title") or meta.get("id") or "this artifact"

    what_changed = []
    for field in ["internal_score", "stability_score", "research_confidence"]:
        v = meta.get(field)
        if v is not None:
            try:
                what_changed.append(f"{field}={float(v):.0%}")
            except (TypeError, ValueError):
                pass

    improvement = _score_improvement(meta, question_item)
    if improvement:
        change_desc = f"{improvement['field']} improved to {improvement['value']:.0%}"
    elif what_changed:
        change_desc = f"new scores: {' '.join(what_changed[:3])}"
    else:
        change_desc = "addresses the stated limitation"

    return {
        "question": question_item["question"],
        "question_id": question_item["id"],
        "linked_artifact": question_item.get("linked_artifact_or_version"),
        "resolving_artifact": title,
        "signal": signal,
        "change_summary": change_desc,
    }


def suggest_resolution_for_artifact(
    meta: Dict[str, Any],
    exclude_question_ids: Optional[set] = None,
) -> Optional[Dict[str, Any]]:
    """
    Analyze artifact metadata for potential resolution of an existing open question.
    
    Returns None if no match found.
    Returns a resolution suggestion dict (not applied to registry).
    
    Max 1 resolution per artifact interaction.
    """
    return _match_resolution(meta, exclude_ids=exclude_question_ids)


def surface_resolution_item(resolution: Dict[str, Any]) -> str:
    """Format a resolution suggestion as a single labeled line."""
    signal_label = {
        "version_upgrade": "version resolves question",
        "score_improvement": "score improvement",
        "keyword_overlap": "related artifact",
    }.get(resolution["signal"], "may resolve")
    return f"[Possible resolution: {resolution['question'][:80]} — {resolution['change_summary']}]"


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json, sys

    if len(sys.argv) < 2:
        print("Usage: artifact_inquiry.py <path-to-artifact-meta.json>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    result = suggest_inquiry_for_artifact(meta, artifact_name=meta.get("title") or path)
    if result:
        print(f"Suggested: {result['question']}")
        print(f"Linked to: {result['linked_artifact_or_version']}")
        print(f"Context: {result['context']}")
    else:
        print("No inquiry warranted.")