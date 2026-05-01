"""
Evidence Chat Bridge V1

Guarded integration point for external evidence pipeline into chat.
Only activates when:
  1. message triggers evidence_needed=true from classify_evidence_need
  2. WESLR_SEARXNG_ENABLED=true
  3. message is NOT a self/system question ("what are you?", "how do you work?", etc.)
  4. current response would be a fallback/generic/direct_answer template

Returns a safe evidence-grounded answer with correct metadata.
Never writes to JSONL, memory, or truth stores.
"""

from weslr.evidence_needed_detector import classify_evidence_need
from weslr.searxng_search_adapter import is_searxng_enabled
from weslr.evidence_pipeline import run_evidence_pipeline


# Questions that should never trigger external search — these are
# self/system questions that have deterministic handlers.
_SELF_SYSTEM_PATTERNS = frozenset([
    "what are you",
    "who are you",
    "what is weslr",
    "what's weslr",
    "how do you work",
    "how are you",
    "what can you do",
    "what's your purpose",
    "describe yourself",
    "tell me about yourself",
    "are you conscious",
    "do you feel",
    "are you aware",
])


def _is_self_system_question(message: str) -> bool:
    """Return True if message is a self/system question that should not search."""
    lower = message.lower().strip()
    for pattern in _SELF_SYSTEM_PATTERNS:
        if pattern in lower:
            return True
    return False


def _detect_depth(message: str) -> str:
    """Detect requested answer depth from message."""
    lower = message.lower()
    if any(w in lower for w in ["very deep", "deeply", "in depth", "thorough", "comprehensive", "elaborate"]):
        return "deep"
    if any(w in lower for w in ["brief", "briefly", "simple", "in short", "summarize", "tl;dr", "quick"]):
        return "brief"
    return "normal"


def maybe_answer_with_evidence(message: str, current_message: str | None) -> dict | None:
    """
    Attempt to answer with external evidence if appropriate.

    Args:
        message: The original user message
        current_message: The current generated message (may be a fallback template)

    Returns:
        dict with evidence answer and metadata, or None if not applicable.
        Return dict has keys: message, path, evidence_metadata.
    """
    # Step 1: Never search for self/system questions
    if _is_self_system_question(message):
        return None

    # Step 2: Classify whether evidence is needed
    classification = classify_evidence_need(message)
    if not classification.get("evidence_needed", False):
        return None

    # Step 3: Check if search is enabled
    if not is_searxng_enabled():
        return None

    # Step 4: Only inject if current message is a fallback-style response
    # (template-based, low-confidence, or generic)
    # This prevents overriding genuine synthesis outputs.
    if current_message:
        lower_curr = current_message.lower()
        fallback_signals = [
            "my current best answer is that",
            "i don't have enough information",
            "i don't know",
            "i'm not sure",
            "i cannot answer",
        ]
        is_fallback = any(s in lower_curr for s in fallback_signals)
        # Only inject if message looks like a template/fallback answer
        if not is_fallback:
            return None

    # Step 5: Run evidence pipeline
    depth = _detect_depth(message)
    result = run_evidence_pipeline(message, depth=depth)

    # Step 6: Only use if safe and successful
    if result.get("reason") != "ok":
        return None

    answer = result.get("answer", {})
    if not answer.get("safe_for_user", False):
        return None

    return {
        "message": answer.get("answer", ""),
        "path": "evidence_grounded_answer",
        "response_contract": "uncertainty_boundary",
        "evidence_metadata": {
            "evidence_used": True,
            "authority": result.get("authority", "external_evidence_unverified"),
            "truth_status": result.get("truth_status", "unverified"),
            "automatic_truth_write": result.get("automatic_truth_write", False),
            "source_count": answer.get("source_count", 0),
            "source_urls": [s["url"] for s in answer.get("sources", []) if s.get("url")],
            "search_attempted": result.get("search_attempted", False),
            "classification": classification,
        },
    }