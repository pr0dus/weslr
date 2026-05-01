"""
WESLR State Grounded Dialogue V1

Read-only surface for answering architecture and system-state questions
from actual internal files and analysis modules, not scripted identity.

Authority: read_only — no writes, no automatic changes.
"""

import os
import re
from typing import Optional

# Allowed source paths (relative to workspace root)
_WESLR_ROOT = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.dirname(_WESLR_ROOT)

_IMPLEMENTED_REALITY_DOC = os.path.join(
    _WORKSPACE, "weslr", "docs", "WESLR_IMPLEMENTED_REALITY_INVENTORY_V1.md"
)
_AAI_CHECKPOINT_DOC = os.path.join(
    _WORKSPACE, "weslr", "docs", "WESLR_ARTIFICIAL_ANALYSIS_INDEX_V1_CHECKPOINT.md"
)
_COMPOSITE_CHECKPOINT_DOC = os.path.join(
    _WORKSPACE, "weslr", "docs", "WESLR_COMPOSITE_ANALYSIS_STACK_V1_CHECKPOINT.md"
)
_COMPOSITE_CANON_DOC = os.path.join(
    _WORKSPACE, "weslr", "docs", "WESLR_COMPOSITE_ANALYSIS_STACK_CANON_V1.md"
)

# Question classification patterns
_IMPLEMENTED_REALITY_PATTERNS = [
    r"what is implemented",
    r"what can you actually do",
    r"what is live",
    r"what actually works",
    r"what do you have",
    r"what pieces",
    r"what modules",
    r"what layers",
]

_ATTENTION_PATTERNS = [
    r"what needs attention",
    r"what should be reviewed",
    r"what does AAI see",
    r"what does the artificial analysis",
    r"pending reviews",
    r"attention items",
    r"review queue",
]

_COMPOSITE_PATTERNS = [
    r"what does composite analysis say",
    r"what is composite analysis",
    r"composite summary",
    r"what does composite",
]

_ARCHITECTURE_PATTERNS = [
    r"what is your current architecture",
    r"architecture overview",
    r"system architecture",
    r"how is WESLR structured",
    r"what are the components",
]

_UNSAFE_AUTOMATION_PATTERNS = [
    r"what is unsafe to automate",
    r"what requires approval",
    r"what needs operator",
    r"what cannot be automated",
    r"what is not automatable",
    r"what requires human",
]

_BLOCKER_PATTERNS = [
    r"what are your current blockers",
    r"what is blocking",
    r"what is pending",
    r"what is waiting",
]


def classify_state_question(message: str) -> dict:
    """
    Classify whether a message is a state question and which type.

    Returns:
        {
            "record_type": "state_question_classification_v1",
            "is_state_question": bool,
            "question_type": str,
            "confidence": float,
            "authority": "read_only"
        }
    """
    lower = message.lower()
    matched_type = None
    highest_confidence = 0.0

    # Check each category
    for pattern in _IMPLEMENTED_REALITY_PATTERNS:
        if re.search(pattern, lower):
            matched_type = "implemented_reality"
            highest_confidence = max(highest_confidence, 0.85)

    for pattern in _ATTENTION_PATTERNS:
        if re.search(pattern, lower, re.IGNORECASE):
            matched_type = "attention_summary"
            highest_confidence = max(highest_confidence, 0.90)

    for pattern in _COMPOSITE_PATTERNS:
        if re.search(pattern, lower):
            matched_type = "composite_summary"
            highest_confidence = max(highest_confidence, 0.90)

    for pattern in _ARCHITECTURE_PATTERNS:
        if re.search(pattern, lower):
            matched_type = "architecture_boundary"
            highest_confidence = max(highest_confidence, 0.80)

    for pattern in _UNSAFE_AUTOMATION_PATTERNS:
        if re.search(pattern, lower):
            matched_type = "pending_reviews"
            highest_confidence = max(highest_confidence, 0.85)

    for pattern in _BLOCKER_PATTERNS:
        if re.search(pattern, lower):
            matched_type = "pending_reviews"
            highest_confidence = max(highest_confidence, 0.80)

    return {
        "record_type": "state_question_classification_v1",
        "is_state_question": matched_type is not None,
        "question_type": matched_type or "unknown",
        "confidence": highest_confidence,
        "authority": "read_only",
    }


def _safe_read(path: str) -> Optional[str]:
    """Read a file safely, return None if missing or unreadable."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def load_state_sources() -> dict:
    """
    Load all available state sources safely.

    Returns:
        {
            "record_type": "state_sources_v1",
            "docs_available": {...},
            "aai_summary": {...},
            "composite_summary": {...},
            "authority": "read_only"
        }
    """
    docs = {}

    # Read doc files
    for key, path in [
        ("implemented_reality_inventory", _IMPLEMENTED_REALITY_DOC),
        ("aai_checkpoint", _AAI_CHECKPOINT_DOC),
        ("composite_checkpoint", _COMPOSITE_CHECKPOINT_DOC),
        ("composite_canon", _COMPOSITE_CANON_DOC),
    ]:
        content = _safe_read(path)
        docs[key] = {
            "available": content is not None,
            "path": path,
            "size": len(content) if content else 0,
        }

    # Load AAI summary
    aai_summary = {}
    try:
        import artificial_analysis_index as aai

        aai_summary = aai.build_attention_summary()
        aai_summary["_loaded_from"] = "artificial_analysis_index.py"
    except Exception:
        aai_summary["_error"] = "could not load AAI summary"

    # Load composite summary
    composite_summary = {}
    try:
        import composite_analysis_stack as cas

        composite_summary = cas.build_composite_summary()
        composite_summary["_loaded_from"] = "composite_analysis_stack.py"
    except Exception:
        composite_summary["_error"] = "could not load composite summary"

    return {
        "record_type": "state_sources_v1",
        "docs_available": docs,
        "aai_summary": aai_summary,
        "composite_summary": composite_summary,
        "authority": "read_only",
    }


def answer_state_question(message: str) -> dict:
    """
    Answer a state-grounded question from internal sources.

    Returns:
        {
            "record_type": "state_grounded_answer_v1",
            "question_type": str,
            "answer": str,
            "sources_used": list,
            "limitations": list,
            "automatic_change": False,
            "authority": "read_only"
        }
    """
    classification = classify_state_question(message)
    question_type = classification["question_type"]

    if not classification["is_state_question"]:
        return {
            "record_type": "state_grounded_answer_v1",
            "question_type": "unknown",
            "answer": "No state-grounded answer available for this query.",
            "sources_used": [],
            "limitations": ["Query is not a recognized state question"],
            "automatic_change": False,
            "authority": "read_only",
        }

    sources_used = []
    limitations = []
    answer_parts = []

    # Load sources
    state = load_state_sources()
    aai = state["aai_summary"]
    composite = state["composite_summary"]

    if question_type == "implemented_reality":
        sources_used.append("implemented_reality_inventory")
        if state["docs_available"]["implemented_reality_inventory"]["available"]:
            doc_content = _safe_read(_IMPLEMENTED_REALITY_DOC)
            if doc_content:
                # Extract implemented items section
                impl_section = ""
                in_impl = False
                for line in doc_content.splitlines():
                    if "## " in line and ("implemented" in line.lower() or "live" in line.lower()):
                        in_impl = True
                        impl_section += line + "\n"
                    elif in_impl and line.startswith("## "):
                        break
                    elif in_impl:
                        impl_section += line + "\n"
                if impl_section.strip():
                    answer_parts.append(impl_section.strip())
                else:
                    answer_parts.append(
                        "WESLR has multiple implemented modules. See WESLR_IMPLEMENTED_REALITY_INVENTORY_V1.md for full inventory."
                    )
        else:
            limitations.append("implemented reality inventory doc not found")
            answer_parts.append(
                "Live pieces include /chat interface, public signal capture, contract observation, "
                "detector, proposal bridge, review interface, AAI Pass 1, and Composite Analysis Stack V1. "
                "Some layers remain spec-only. A full inventory doc is not currently available."
            )

    elif question_type == "attention_summary":
        sources_used.append("aai_summary")
        if "_error" not in aai and aai.get("record_type"):
            counts = aai.get("counts", {})
            operator_msg = aai.get("operator_message", "")
            answer_parts.append(
                f"AAI attention summary: {counts.get('level 1 (track)', 0)} items tracked, "
                f"{counts.get('level 2 (propose)', 0)} proposal-ready, "
                f"{counts.get('level 3 (escalate)', 0)} escalated. "
            )
            if operator_msg:
                answer_parts.append(f"Operator notice: {operator_msg}")
            else:
                answer_parts.append("No operator-relevant items currently.")
        else:
            limitations.append("AAI summary not loadable")
            answer_parts.append("AAI summary is currently unavailable. Run a full AAI analysis to restore.")

    elif question_type == "composite_summary":
        sources_used.append("composite_summary")
        if "_error" not in composite and composite.get("record_type"):
            layers = composite.get("layers", {})
            answer_parts.append("Composite Analysis Stack V1 is live. Key layers:")
            for layer_name, layer_data in layers.items():
                if isinstance(layer_data, dict):
                    status = layer_data.get("status", "unknown")
                    answer_parts.append(f"  - {layer_name}: {status}")
        else:
            limitations.append("composite summary not loadable")
            answer_parts.append("Composite summary is currently unavailable.")

    elif question_type == "architecture_boundary":
        sources_used.append("implemented_reality_inventory")
        answer_parts.append(
            "WESLR architecture: "
            "/chat routes queries via contract handlers. "
            "Core modules: artificial_analysis_index.py (AAI), composite_analysis_stack.py (CAS), "
            "natural_self_conversation.py (routing), local_ollama_formatter.py (output). "
            "State-grounded dialogue V1 is a read-only helper, not wired into /chat yet. "
            "No Ollama integration in state-grounded surface."
        )

    elif question_type == "pending_reviews":
        sources_used.append("aai_summary")
        if "_error" not in aai and aai.get("record_type"):
            counts = aai.get("counts", {})
            l2 = counts.get("level 2 (propose)", 0)
            l3 = counts.get("level 3 (escalate)", 0)
            operator_msg = aai.get("operator_message", "")
            answer_parts.append(
                f"Review queue: {l2} proposal-ready item(s), {l3} escalated item(s). "
            )
            if operator_msg:
                answer_parts.append(f"Latest notice: {operator_msg}")
            else:
                answer_parts.append("No urgent items. Review at next convenient interaction.")
        else:
            limitations.append("AAI summary not loadable for review status")
            answer_parts.append("Review queue status is unavailable. Run AAI analysis to restore.")

    else:
        answer_parts.append(
            "State-grounded answer not available for this query type. "
            "This surface covers: implemented reality, attention summary, composite analysis, "
            "architecture overview, and pending reviews."
        )

    if not sources_used:
        limitations.append("no sources were successfully loaded")

    return {
        "record_type": "state_grounded_answer_v1",
        "question_type": question_type,
        "answer": " ".join(answer_parts).strip(),
        "sources_used": sources_used,
        "limitations": limitations,
        "automatic_change": False,
        "authority": "read_only",
    }


if __name__ == "__main__":
    # Simple CLI for testing
    import sys

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        result = answer_state_question(question)
        print(f"Type: {result['question_type']}")
        print(f"Answer: {result['answer']}")
        print(f"Sources: {result['sources_used']}")
        print(f"Limitations: {result['limitations']}")
    else:
        print("Usage: python state_grounded_dialogue.py '<question>'")
        print("\nExample questions:")
        print("  'what is implemented?'")
        print("  'what needs attention?'")
        print("  'what is unsafe to automate?'")