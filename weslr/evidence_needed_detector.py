"""
WESLR Evidence Needed Detector V1

Read-only detector for open knowledge questions that require external evidence.
Does NOT perform searches — only classifies and builds placeholder responses.

Authority: classification_only — no writes, no web requests, no search.
"""

import re
from typing import Optional


# Patterns that indicate a question needs external evidence
_DEFINITION_PATTERNS = [
    r"^what (is|are|was|were) ",          # what is X, what are X
    r"^define ",                           # define X
    r"^explain the concept of ",
    r"^what do you mean by ",
    r"^what does .* mean",
]

_OPEN_KNOWLEDGE_PATTERNS = [
    r"explain .+ (in detail|deeply|thoroughly|comprehensively)",
    r"tell me about ",
    r"(deep|thorough|comprehensive) .+ explanation",
    r"how (does|do|does) .+ work",
    r"what happens during ",
    r"why does .+ happen",
    r"what is the process of ",
]

_SOURCE_REQUEST_PATTERNS = [
    r"what is the source",
    r"what are the sources",
    r"where (does|do) .+ come from",
    r"who (said|discovered|proposed|created) ",
    r"what evidence supports",
    r"can you cite",
    r"what study",
    r"what paper",
    r"what research",
    r"what documentation",
]

_LOOKUP_REQUEST_PATTERNS = [
    r"look up ",
    r"search for ",
    r"find information about ",
    r"google ",
    r"can you search",
    r"find out about ",
    r"check what ",
    r"look into ",
]

_LATEST_INFORMATION_PATTERNS = [
    r"latest ",
    r"recent ",
    r"newest ",
    r"current .+ research",
    r"new .+ findings",
    r"what's new in ",
    r"up to date ",
    r"breaking .+ research",
    r"state of the art ",
    r"202[0-9] .+ research",
]

# Patterns that indicate NO evidence is needed (already handled by WESLR)
_EXEMPT_PATTERNS = [
    r"^hi\b",
    r"^hello\b",
    r"^hey\b",
    r"^what are you\b",
    r"^what can you help\b",
    r"^what can you do\b",
    r"^what should i try\b",
    r"^what should we try\b",
    r"^how do i \b",
    r"^how can i \b",
    r"^can you tell me about yourself\b",
    r"^can you explain yourself\b",
    r"^i need help",
    r"^show me\b",
    r"^list",
    r"^what is your current architecture",
    r"^what is unsafe to automate",
    r"^what needs attention",
    r"^what is implemented",
    r"^what does composite",
    r"^what does AAI",
    # NOTE: ^can you alone is NOT an exempt pattern — "can you search for X" IS an evidence need
    # Only specific capability questions are exempt
    r"^help me\b",
    r"^explain that more simply\b",
    r"^what happens if you do not know\b",
    r"^can you remember what\b",
    r"^i want to understand how you improve\b",
]


def classify_evidence_need(message: str) -> dict:
    """
    Classify whether a message needs external evidence/search.

    Returns:
        {
            "record_type": "evidence_need_classification_v1",
            "evidence_needed": bool,
            "need_type": str,
            "confidence": float,
            "reason": str,
            "authority": "classification_only",
            "automatic_search_allowed": false
        }
    """
    if not message or not message.strip():
        return {
            "record_type": "evidence_need_classification_v1",
            "evidence_needed": False,
            "need_type": "none",
            "confidence": 0.0,
            "reason": "Empty message",
            "authority": "classification_only",
            "automatic_search_allowed": False,
        }

    lower = message.lower().strip()
    original = message.strip()

    # Check exemptions first
    for pattern in _EXEMPT_PATTERNS:
        if re.search(pattern, lower):
            return {
                "record_type": "evidence_need_classification_v1",
                "evidence_needed": False,
                "need_type": "none",
                "confidence": 0.95,
                "reason": f"Matches exempt pattern: {pattern}",
                "authority": "classification_only",
                "automatic_search_allowed": False,
            }

    # Check need type patterns
    need_type = None
    confidence = 0.0
    matched_pattern = None

    # Source request — highest priority
    for pattern in _SOURCE_REQUEST_PATTERNS:
        if re.search(pattern, lower):
            need_type = "source_request"
            confidence = 0.88
            matched_pattern = pattern
            break

    # Latest information
    if not need_type:
        for pattern in _LATEST_INFORMATION_PATTERNS:
            if re.search(pattern, lower):
                need_type = "latest_information"
                confidence = 0.85
                matched_pattern = pattern
                break

    # Lookup request
    if not need_type:
        for pattern in _LOOKUP_REQUEST_PATTERNS:
            if re.search(pattern, lower):
                need_type = "lookup_request"
                confidence = 0.88
                matched_pattern = pattern
                break

    # Definition request
    if not need_type:
        for pattern in _DEFINITION_PATTERNS:
            if re.search(pattern, lower):
                need_type = "definition_request"
                confidence = 0.78
                matched_pattern = pattern
                break

    # Open knowledge
    if not need_type:
        for pattern in _OPEN_KNOWLEDGE_PATTERNS:
            if re.search(pattern, lower):
                need_type = "open_knowledge"
                confidence = 0.75
                matched_pattern = pattern
                break

    if need_type:
        return {
            "record_type": "evidence_need_classification_v1",
            "evidence_needed": True,
            "need_type": need_type,
            "confidence": confidence,
            "reason": f"Matched {need_type} pattern: {matched_pattern}",
            "authority": "classification_only",
            "automatic_search_allowed": False,
        }

    # Fallback: check if message is a question about external knowledge
    question_indicators = [
        r"^what ",
        r"^how ",
        r"^why ",
        r"^when ",
        r"^where ",
        r"^who ",
    ]
    for pattern in question_indicators:
        if re.search(pattern, lower):
            return {
                "record_type": "evidence_need_classification_v1",
                "evidence_needed": True,
                "need_type": "open_knowledge",
                "confidence": 0.60,
                "reason": "Question pattern detected but no specific pattern matched",
                "authority": "classification_only",
                "automatic_search_allowed": False,
            }

    return {
        "record_type": "evidence_need_classification_v1",
        "evidence_needed": False,
        "need_type": "none",
        "confidence": 0.55,
        "reason": "No evidence-need patterns matched",
        "authority": "classification_only",
        "automatic_search_allowed": False,
    }


def build_evidence_needed_response(message: str) -> dict:
    """
    Build a response for a message that needs external evidence.

    Does NOT perform any web requests or searches.
    Returns a placeholder response indicating evidence is not yet available.

    Returns:
        {
            "record_type": "evidence_needed_response_v1",
            "path": "evidence_needed",
            "response_contract": "uncertainty_boundary",
            "response_text": "...",
            "classification": {...},
            "automatic_search_allowed": false,
            "authority": "classification_only"
        }
    """
    classification = classify_evidence_need(message)

    response_text = (
        "This question likely requires external evidence or search to answer fully. "
        "Search is not yet wired into this staging surface — I don't have a confirmed answer yet. "
        "Any external findings I surface would be kept entirely separate from structured system knowledge "
        "and marked as evidence-only, never mixed into authoritative responses. "
        "I'm operating in read-only classification mode for now, so I can't look this up yet — "
        "but when a search adapter is added, this classification will route it correctly."
    )

    return {
        "record_type": "evidence_needed_response_v1",
        "path": "evidence_needed",
        "response_contract": "uncertainty_boundary",
        "response_text": response_text,
        "classification": classification,
        "automatic_search_allowed": False,
        "authority": "classification_only",
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        print(f"Message: {message}")
        print()
        result = classify_evidence_need(message)
        print(f"Evidence needed: {result['evidence_needed']}")
        print(f"Type: {result['need_type']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Reason: {result['reason']}")
    else:
        print("Usage: python evidence_needed_detector.py '<message>'")
        print("\nExamples:")
        for msg in [
            "What is entropy?",
            "Explain entropy very deeply.",
            "What is the source for entropy?",
            "Can you search the web for entropy?",
            "Look up entropy.",
            "What is the latest AI research about uncertainty?",
            "Hi",
            "What are you?",
        ]:
            result = classify_evidence_need(msg)
            print(f"  [{result['evidence_needed']}] {msg} -> {result['need_type']}")