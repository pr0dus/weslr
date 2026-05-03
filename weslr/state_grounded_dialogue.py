"""
WESLR State Grounded Dialogue V1

Read-only surface for answering architecture and system-state questions
from actual internal files and analysis modules, not scripted identity.

Authority: read_only — no writes, no automatic changes.
"""

import os
import re
from pathlib import Path
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
    r"what should not be automated",
    r"what requires approval",
    r"what needs operator",
    r"what cannot be automated",
    r"what is not automatable",
    r"what requires human",
    r"what must stay manual",
]

_BLOCKER_PATTERNS = [
    r"what are your current blockers",
    r"what is blocking",
    r"what is pending",
    r"what is waiting",
]

# ── Jarvis capability question patterns ──────────────────────────────────────

_VOICE_IO_PATTERNS = [
    r"what voice",
    r"voice i/o",
    r"speech (to|from) text",
    r"stt|tts",
    r"whisper",
    r"microphone|capture",
    r"how do i talk to you",
    r"can you hear me",
    r"voice capability",
    r"voice capability",
]

_PERSISTENT_MEMORY_PATTERNS = [
    r"persistent memory",
    r"across sessions",
    r"memory exists",
    r"what memory",
    r"long.term memory",
    r"memory between",
    r"remember (between|across)",
    r"what do you remember",
]

_PROACTIVE_SUGGESTION_PATTERNS = [
    r"proactive suggestion",
    r"suggestion delivery",
    r"what should i (do|explore|try)",
    r"what.*next$",
    r"what can we (do|work on)",
    r"what ideas",
    r"experiments.*pending|pending.*experiments",
    r"suggested next step",
    r"what.*we.*working on",
]

_ACTION_STUB_PATTERNS = [
    r"action stub",
    r"remind",
    r"todo",
    r"task tracking",
    r"reminder.*implement",
    r"can you remind",
    r"set a reminder",
]

_TEMPORAL_RELATIONAL_PATTERNS = [
    r"temporal",
    r"relational query",
    r"what.*when.*happen",
    r"what happened (after|before)",
    r"timeline of",
    r"chronolog",
    r"since.*until",
]

_SEMANTIC_SIMILARITY_PATTERNS = [
    r"semantic similarity",
    r"node matching",
    r"similarity search",
    r"embeddings?",
    r"vector search",
    r"semantic.*match",
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
            matched_type = "unsafe_automation"
            highest_confidence = max(highest_confidence, 0.85)

    for pattern in _BLOCKER_PATTERNS:
        if re.search(pattern, lower):
            matched_type = "pending_reviews"
            highest_confidence = max(highest_confidence, 0.80)

    # Jarvis capability questions — extend in priority order
    for pattern in _VOICE_IO_PATTERNS:
        if re.search(pattern, lower):
            matched_type = "voice_io"
            highest_confidence = max(highest_confidence, 0.88)

    if not matched_type:
        for pattern in _PERSISTENT_MEMORY_PATTERNS:
            if re.search(pattern, lower):
                matched_type = "persistent_memory"
                highest_confidence = max(highest_confidence, 0.88)

    if not matched_type:
        for pattern in _PROACTIVE_SUGGESTION_PATTERNS:
            if re.search(pattern, lower):
                matched_type = "proactive_suggestions"
                highest_confidence = max(highest_confidence, 0.80)

    if not matched_type:
        for pattern in _ACTION_STUB_PATTERNS:
            if re.search(pattern, lower):
                matched_type = "action_stubs"
                highest_confidence = max(highest_confidence, 0.85)

    if not matched_type:
        for pattern in _TEMPORAL_RELATIONAL_PATTERNS:
            if re.search(pattern, lower):
                matched_type = "temporal_relational"
                highest_confidence = max(highest_confidence, 0.82)

    if not matched_type:
        for pattern in _SEMANTIC_SIMILARITY_PATTERNS:
            if re.search(pattern, lower):
                matched_type = "semantic_similarity"
                highest_confidence = max(highest_confidence, 0.85)

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

    elif question_type == "unsafe_automation":
        # Direct list of categories that require operator approval — not AAI review queue
        answer_parts.append(
            "The following may not be automated silently. All require operator approval:"
        )
        answer_parts.append(
            "Contract changes — response contracts, observation rules, improvement proposals; "
            "Truth/state writes — modifying internal state, memory files, or JSONL records; "
            "Proposal approval/rejection — accepting or declining improvement proposals; "
            "Memory integration — adding to or removing from memory, long-term context; "
            "Governance changes — altering authority boundaries, operator rules, or approval contracts; "
            "Deployment changes — activating features, pushing updates, changing runtime behavior; "
            "External actions — network calls, filesystem writes beyond logs, third-party integrations; "
            "Public-facing behavior changes — anything visible to end users or external systems; "
            "Security-sensitive changes — authentication, access control, or credential modifications."
        )
        # Optionally include current AAI review status after the boundary list
        if "_error" not in aai and aai.get("record_type"):
            counts = aai.get("counts", {})
            operator_msg = aai.get("operator_message", "")
            answer_parts.append(
                f"Current AAI review queue: {counts.get('level 2 (propose)', 0)} proposal-ready, "
                f"{counts.get('level 3 (escalate', 0)} escalated. "
            )
            if operator_msg:
                answer_parts.append(f"Latest notice: {operator_msg}")
        answer_parts.append(
            "AAI and composite analysis may observe and rank these items but cannot authorize changes. "
            "Operator approval is required for all of the above."
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

    elif question_type == "voice_io":
        sources_used.append("voice_gateway.py")
        whisper_path = "/data/data/com.termux/files/home/whisper.cpp/build/bin/whisper-cli"
        whisper_installed = os.path.exists(whisper_path)
        model_path = "/data/data/com.termux/files/home/whisper.cpp/models/ggml-base.bin"
        model_installed = os.path.exists(model_path)
        if whisper_installed and model_installed:
            answer_parts.append(
                "Voice I/O is partially implemented. "
                "STT (speech-to-text): whisper.cpp is installed and active, "
                "converting audio to text via the voice gateway WebSocket interface. "
                "TTS (text-to-speech): handled client-side by the browser Web Speech API — "
                "no server-side TTS engine is running. "
                "A continuous voice session mode is available via the voice gateway."
            )
        else:
            answer_parts.append(
                "Voice I/O is in shim mode. "
                "STT: browser-side transcript injection (no server-side STT). "
                "TTS: browser Web Speech API only. "
                "For real STT, install whisper.cpp and a model at the standard paths."
            )
        answer_parts.append(
            "Would you like to create a proposal for a reminder handler or todo system?"
        )

    elif question_type == "persistent_memory":
        sources_used.append("memory modules")
        # Count entries in key JSONL stores
        base = Path(_WORKSPACE)
        counts = []
        for name, path in [
            ("entity timeline", base / ".weslr" / "timelines"),
            ("fact assertions", base / ".weslr" / "fact_assertions.jsonl"),
            ("project registry", base / ".weslr" / "project_registry.jsonl"),
            ("experiment proposals", base / ".weslr" / "experiment_proposals.jsonl"),
        ]:
            if path.is_file():
                try:
                    with open(path) as f:
                        lines = len(f.readlines())
                    counts.append(f"{lines} {name} records")
                except Exception:
                    pass
            elif path.is_dir():
                try:
                    event_files = list(path.rglob("events.jsonl"))
                    total = 0
                    for ef in event_files:
                        try:
                            with open(ef) as f:
                                total += len(f.readlines())
                        except Exception:
                            pass
                    if total > 0:
                        counts.append(f"{total} {name} events")
                except Exception:
                    pass

        answer_parts.append(
            "WESLR maintains several persistent memory layers across sessions:"
        )
        answer_parts.append(
            "1. User timeline memory — session summaries stored in memory/YYYY-MM-DD.md"
        )
        answer_parts.append(
            "2. Entity timeline memory — per-entity event logs in .weslr/timelines/"
        )
        answer_parts.append(
            "3. Fact assertions — structured facts extracted from sessions in .weslr/fact_assertions.jsonl"
        )
        answer_parts.append(
            "4. Project registry — project-scoped facts and metadata in .weslr/project_registry.jsonl"
        )
        answer_parts.append(
            "5. Long-term curated memory — MEMORY.md loaded at session start"
        )
        if counts:
            answer_parts.append(f"Current counts: {', '.join(counts)}.")
        answer_parts.append(
            "Note: memory persistence across voice sessions is limited — "
            "the voice gateway currently uses a default timeline."
        )

    elif question_type == "proactive_suggestions":
        sources_used.append("proactive_suggestions.py")
        answer_parts.append(
            "Proactive suggestion delivery exists in draft form. "
            "proactive_suggestions.py generates theme-based suggestions from recent session summaries "
            "and surfaces them through the workplace bridge when a user asks /workplace or 'what experiments are pending?'. "
            "However, there is no background daemon — suggestions are only produced on user request. "
            "No automatic push delivery, no cron-triggered suggestions, no notification channel."
        )
        answer_parts.append(
            "Not implemented yet: proactive_deamon.py, cron-triggered suggestion delivery, notification delivery."
        )
        answer_parts.append(
            "Would you like to create a proposal for one of these? Say 'propose a reminder handler' or 'propose a todo system'."
        )

    elif question_type == "action_stubs":
        sources_used.append("reminder_handler.py")
        import os as _os
        reminder_handler_exists = _os.path.exists(
            _os.path.join(_WESLR_ROOT, "reminder_handler.py")
        )
        if reminder_handler_exists:
            answer_parts.append(
                "Action stubs are partially implemented. "
                "reminder_handler.py is live — it handles: "
                "'remind me in N minutes to <msg>', 'remind me at HH:MM to <msg>', "
                "'show my reminders', and 'cancel reminder <id>'. "
                "Reminders are stored in .weslr/reminders.jsonl and fire into "
                ".weslr/pending_messages.jsonl for /chat delivery. "
                "The scheduler uses threading.Timer with a 60-second polling fallback. "
                "A todo system has not yet been implemented."
            )
        else:
            answer_parts.append(
                "Action stubs are not yet implemented as independent handlers. "
                "The architecture supports them via write_handlers.py and the experiment_proposal_store.py "
                "(which stores proposals with operator approval gates), but there is no /remind, /todo, "
                "or /task command, and no reminder_handler.py or todo_handler.py."
            )
            answer_parts.append(
                "Reminder scheduling would require a small handler (~100 lines) that writes to "
                ".weslr/reminders.jsonl and schedules via threading.Timer. A todo tracker would follow the same pattern."
            )
        answer_parts.append(
            "Would you like to create a proposal for a todo system? "
            "Say 'propose a todo system' and I will draft one."
        )

    elif question_type == "temporal_relational":
        sources_used.append("fact_extractor.py")
        answer_parts.append(
            "Temporal and relational query capabilities are partially implemented. "
            "The fact_extractor.py module has 10 deterministic temporal patterns "
            "(since_X, until_Y, next_Z, after_X, before_Y, during_Z, between_X_and_Y, last_N, "
            "first_X, most_recent) for extracting facts with temporal scope from session summaries."
        )
        answer_parts.append(
            "Project-scoped facts support relational queries via the fact_query_bridge. "
            "Entity timeline memory supports temporal queries per entity. "
            "However, there is no timestamp ordering across facts, no timeline projection, "
            "and no date arithmetic. This is basic pattern matching, not full temporal reasoning."
        )
        answer_parts.append(
            "Would you like to propose a temporal reasoning extension?"
        )

    elif question_type == "semantic_similarity":
        sources_used.append("doctrine P11, multi_graph_traversal.py")
        answer_parts.append(
            "Semantic similarity for node matching is not implemented. "
            "Doctrine P11 (added in commit dd1117a) explicitly permits it as a low-risk "
            "Layer 2 automation — semantic similarity for node disambiguation in fact queries. "
            "However, the current fact_query_bridge and multi_graph_traversal modules "
            "use deterministic keyword matching only. No vector embeddings, no ANN index, "
            "no sentence_transformers or semantic search."
        )
        answer_parts.append(
            "To implement: add a lightweight embedding model (e.g., sentence-transformers), "
            "index fact subject/predicate/object triples, and use cosine similarity for matching. "
            "This is a medium-effort addition."
        )
        answer_parts.append(
            "Would you like to create a proposal for semantic similarity?"
        )

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