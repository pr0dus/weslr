from __future__ import annotations

# B9: pattern escalation across turns (session-only, no persistence)
_B9_STATE = {
    "low_confidence_count": 0,
    "mismatch_count": 0,
}
# B12.1: operator feedback log - separate from graph/proposals
import json as _json
from pathlib import Path as _Path

_FEEDBACK_LOG_PATH = _Path(__file__).resolve().parent / "weslr" / "operator_feedback_log.jsonl"

_VALID_DECISIONS = frozenset({"accepted", "rejected", "modified", "deferred"})


def log_operator_feedback(event: dict) -> None:
    """Append one operator feedback event to operator_feedback_log.jsonl."""
    decision = event.get("operator_decision", "")
    if decision not in _VALID_DECISIONS:
        raise ValueError("Invalid operator_decision: %r. Must be one of %s." % (decision, list(_VALID_DECISIONS)))
    if "timestamp" not in event:
        import datetime as _dt
        event["timestamp"] = _dt.datetime.now().astimezone().isoformat()
    _FEEDBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_FEEDBACK_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(_json.dumps(event, ensure_ascii=False) + chr(10))


def get_operator_feedback_log(limit: int = 50) -> list[dict]:
    """Read last N operator feedback events. Returns [] on missing or corrupt entries."""
    if not _FEEDBACK_LOG_PATH.exists():
        return []
    events = []
    with open(_FEEDBACK_LOG_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(_json.loads(line))
            except Exception:
                continue
    return events[-limit:] if limit > 0 else events

    return events[-limit:] if limit > 0 else events


def build_operator_feedback_event(
    *,
    message: str,
    mode_analysis: dict,
    mode_suggestion: dict,
    operator_decision: str,
    modified_value: str | None = None,
    notes: str | None = None,
) -> dict:
    """Build a well-formed operator feedback event dict. Pure — no writes."""
    # Validate operator_decision
    if operator_decision not in _VALID_DECISIONS:
        raise ValueError(
            "operator_decision must be one of %s, got %r."
            % (list(_VALID_DECISIONS), operator_decision)
        )
    # Validate message non-empty
    if not message:
        raise ValueError("message must be a non-empty string")
    # Validate dict types
    if not isinstance(mode_analysis, dict):
        raise TypeError("mode_analysis must be a dict")
    if not isinstance(mode_suggestion, dict):
        raise TypeError("mode_suggestion must be a dict")
    # Validate modified_value rules
    if operator_decision == "modified":
        if not modified_value:
            raise ValueError("modified decision requires a non-None modified_value")
    else:
        if modified_value is not None:
            raise ValueError(
                "modified_value must be None when operator_decision is not 'modified', got %r"
                % modified_value
            )
    # Build turn_context
    turn_context = {
        "message": message[:500],
        "mode_before": mode_analysis.get("current_mode"),
        "suggested_mode": mode_analysis.get("suggested_mode"),
    }
    # Build suggestion block
    suggestion = {
        "type": "mode_switch",
        "suggest_switch": mode_suggestion.get("suggest_switch", False),
        "from_mode": mode_suggestion.get("from"),
        "to_mode": mode_suggestion.get("to"),
        "reason": mode_analysis.get("reason"),
    }
    # Auto-add timestamp
    import datetime as _dt
    timestamp = _dt.datetime.now().astimezone().isoformat()
    event = {
        "timestamp": timestamp,
        "turn_context": turn_context,
        "suggestion": suggestion,
        "operator_decision": operator_decision,
        "modified_value": modified_value,
        "notes": notes,
    }
    return event

    return event


def record_mode_feedback(
    *,
    message: str,
    result: dict,
    operator_decision: str,
    modified_value: str | None = None,
    notes: str | None = None,
) -> dict:
    """Build and log an operator feedback event from an interpret_human_turn result. Explicit call only — no auto-logging."""
    mode_analysis = result.get("mode_analysis", {})
    mode_suggestion = result.get("mode_suggestion", {})
    event = build_operator_feedback_event(
        message=message,
        mode_analysis=mode_analysis,
        mode_suggestion=mode_suggestion,
        operator_decision=operator_decision,
        modified_value=modified_value,
        notes=notes,
    )
    log_operator_feedback(event)
    return event
    log_operator_feedback(event)
    return event


def summarize_operator_feedback(limit: int = 100) -> dict:
    """Read last N feedback entries and return aggregated statistics. Read-only."""
    entries = get_operator_feedback_log(limit=limit)
    total = len(entries)
    if total == 0:
        return {
            "total": 0,
            "by_decision": {},
            "acceptance_rate": None,
            "most_recent": None,
        }
    by_decision = {}
    for e in entries:
        d = e.get("operator_decision", "unknown")
        by_decision[d] = by_decision.get(d, 0) + 1
    accepted = by_decision.get("accepted", 0)
    acceptance_rate = round(accepted / total, 3) if total > 0 else None
    return {
        "total": total,
        "by_decision": by_decision,
        "acceptance_rate": acceptance_rate,
        "most_recent": entries[-1] if entries else None,
    }


def get_recent_operator_feedback(limit: int = 20) -> list[dict]:
    """Return the most recent N feedback entries. Read-only."""
    return get_operator_feedback_log(limit=limit)

    return get_operator_feedback_log(limit=limit)


def get_operator_feedback_visibility(limit: int = 20) -> dict:
    """Return operator-facing feedback visibility bundle. Read-only."""
    recent = get_recent_operator_feedback(limit=limit)
    summary = summarize_operator_feedback(limit=limit)

    total = summary.get("total", 0)
    by_decision = summary.get("by_decision", {})
    acceptance_rate = summary.get("acceptance_rate")

    status_text = (
        "No feedback recorded"
        if total == 0
        else (
            f"{total} feedback events — "
            f"accepted: {by_decision.get('accepted', 0)}, "
            f"rejected: {by_decision.get('rejected', 0)}, "
            f"modified: {by_decision.get('modified', 0)}, "
            f"deferred: {by_decision.get('deferred', 0)}, "
            f"acceptance_rate: {acceptance_rate}"
        )
    )

    return {
        "summary": summary,
        "recent": recent,
        "status_text": status_text,
    }



LOW_INFORMATION_REFERENTIAL_PHRASES = [
    "no, i mean",
    "no i mean",
    "i mean the thing",
    "the thing that matters",
    "what i meant",
    "that one",
    "the important thing",
    "more overall",
]

SMALL_TALK_ONLY_MESSAGES = {
    "hey", "hi", "hello", "yo", "sup", "hallo", "moin", "hey there", "hi there",
    "hey again", "hi again", "hello again"
}

CONTROL_SIGNAL_MESSAGES = {
    "ok go", "okay go", "alright go", "go then", "yes go", "do it", "go ahead"
}

APPROVAL_MESSAGES = {
    "you are allowed to implement them", "so you are allowed to implement them", "implement them", "you can implement them"
}

APPROVAL_PATTERNS = [
    "you're allowed",
    "you are allowed",
    "you can implement",
    "go ahead and implement",
    "allowed to change",
    "allowed to add",
    "allowed to implement",
]

EXECUTION_START_PATTERNS = [
    "implement suggested actions",
    "go for coding",
    "start implementing",
    "start coding",
    "apply the changes",
]

COMPLETION_NOTIFY_PATTERNS = [
    "tell me when finished",
    "tell me when you're finished",
    "tell me when done",
    "let me know when finished",
    "let me know when done",
    "notify me when finished",
]

IMPERATIVE_REQUEST_PHRASES = [
    "suggest code",
    "implement",
    "search online",
    "search the web",
    "look online",
    "look it up",
    "change your coding",
    "changed in your coding",
]


def extract_clarified_target(message: str) -> str:
    lowered = str(message or "").strip().lower()
    patterns = ["no, i mean", "no i mean", "what i meant is", "i meant", "the issue is", "the point is", "more overall"]
    for pattern in patterns:
        if pattern in lowered:
            tail = lowered.split(pattern, 1)[1].strip(" .,!?:;-")
            if tail:
                words = [word.strip(" ,.!?:;()[]{}\"'") for word in tail.split() if word.strip(" ,.!?:;()[]{}\"'")]
                cleaned = " ".join(words[:6]).strip()
                if cleaned:
                    return cleaned
    return ""


def infer_human_topics(message: str) -> list[str]:
    original = str(message or "").strip()
    lowered = original.lower()
    if lowered in SMALL_TALK_ONLY_MESSAGES or lowered in CONTROL_SIGNAL_MESSAGES or lowered in APPROVAL_MESSAGES or any(pattern in lowered for pattern in APPROVAL_PATTERNS) or any(pattern in lowered for pattern in EXECUTION_START_PATTERNS) or any(pattern in lowered for pattern in COMPLETION_NOTIFY_PATTERNS):
        return []
    topics = []
    keyword_map = {
        "circleforge": "Weslr",
        "backup confidence": "backup confidence",
        "backup": "backup confidence",
        "memory": "memory continuity",
        "communicator": "communicator self",
        "dashboard": "dashboard",
        "agent": "internal minds",
        "tester": "testers and feedback",
        "feedback": "testers and feedback",
        "github": "GitHub positioning",
        "emergence": "emergence",
        "entity": "entity status",
        "conversation": "conversation quality",
        "understand": "understanding",
        "learn": "learning",
        "prompt": "prompt dependence",
    }
    for token, topic in keyword_map.items():
        if token in lowered and topic not in topics:
            topics.append(topic)

    if topics:
        return topics[:4]

    if any(phrase in lowered for phrase in LOW_INFORMATION_REFERENTIAL_PHRASES):
        return []
    if any(phrase in lowered for phrase in IMPERATIVE_REQUEST_PHRASES):
        return []

    cleaned = lowered
    for phrase in [
        "why do you", "why are you", "how do you", "what do you", "can you", "could you", "would you", "do you", "are you", "is this", "i don't want to ask,", "i dont want to ask,",
        "please", "actually", "really", "just", "still", "again"
    ]:
        cleaned = cleaned.replace(phrase, " ")
    words = [word.strip(" ,.!?:;()[]{}\"'") for word in cleaned.split()]
    stopwords = {
        "i", "you", "me", "my", "we", "us", "this", "that", "it", "to", "the", "a", "an", "and", "or", "but", "if", "then", "of", "on", "in", "at", "for", "with", "about", "do", "does", "did", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "want", "need", "not"
    }
    filtered = [word for word in words if word and word not in stopwords]
    if filtered:
        topics.append(" ".join(filtered[:3]).strip())
    elif original:
        topics.append(original[:48].strip())
    return topics[:4]


def classify_human_turn(message: str) -> str:
    lowered = str(message or "").strip().lower()
    if not lowered:
        return "empty"
    if lowered in SMALL_TALK_ONLY_MESSAGES:
        return "greeting"
    if any(pattern in lowered for pattern in COMPLETION_NOTIFY_PATTERNS):
        return "completion_notify"
    if any(pattern in lowered for pattern in EXECUTION_START_PATTERNS):
        return "execution_start"
    if lowered in CONTROL_SIGNAL_MESSAGES or lowered in APPROVAL_MESSAGES or any(pattern in lowered for pattern in APPROVAL_PATTERNS):
        return "approval"
    if any(token in lowered for token in ["this is not", "not normal conversation", "you still need to learn", "evolve", "stop telling me", "answer directly", "that's wrong", "thats wrong", "that is wrong", "not what i meant", "you misunderstood", "you got that wrong"]):
        return "repair"
    if any(token in lowered for token in ["who are you", "what are you", "emergence", "new entity", "entity"]):
        return "identity_probe"
    if any(token in lowered for token in ["what do you remember", "do you remember", "remember me"]):
        return "memory_probe"
    if any(token in lowered for token in ["why", "how come", "what for"]):
        return "objection"
    if any(token in lowered for token in ["i don't understand", "dont understand", "do not understand"]):
        return "confusion"
    if "?" in lowered or lowered.startswith(("do ", "are ", "can ", "will ", "would ", "is ", "should ", "could ", "what ", "why ", "how ", "who ")):
        return "question"
    return "statement"


def interpret_human_turn(message: str) -> dict:
    text = str(message or "").strip()
    topics = infer_human_topics(text)
    clarified_target = extract_clarified_target(text)
    if clarified_target and clarified_target not in topics:
        topics = [clarified_target, *topics][:4]
    turn_type = classify_human_turn(text)
    lowered = text.lower()

    intent = {
        "greeting": "open conversation",
        "approval": "approve_or_continue",
        "execution_start": "start_approved_work",
        "completion_notify": "notify_on_completion",
        "repair": "repair conversation",
        "identity_probe": "test identity / emergence",
        "memory_probe": "test memory scope",
        "objection": "challenge current behavior",
        "confusion": "request clarification",
        "question": "ask for explanation",
        "statement": "share/update stance",
        "empty": "no content",
    }.get(turn_type, "unknown")

    stance = "neutral"
    if turn_type in {"repair", "objection"}:
        stance = "resistant"
    elif turn_type == "confusion":
        stance = "uncertain"
    elif turn_type in {"question", "memory_probe", "identity_probe"}:
        stance = "inquiring"
    elif turn_type == "approval":
        stance = "supportive"
    elif turn_type in {"execution_start", "completion_notify"}:
        stance = "supportive"

    reply_shape = "answer_directly"
    if turn_type == "repair":
        reply_shape = "repair_then_answer"
    elif turn_type == "confusion":
        reply_shape = "clarify"
    elif turn_type == "approval":
        reply_shape = "acknowledge_and_continue"
    elif turn_type == "execution_start":
        reply_shape = "acknowledge_and_start"
    elif turn_type == "completion_notify":
        reply_shape = "acknowledge_and_track"
    elif turn_type in {"memory_probe", "identity_probe"}:
        reply_shape = "answer_with_scope"

    relational_signal = "neutral"
    if any(token in lowered for token in ["no", "stop", "wrong", "not normal", "don't", "do not"]):
        relational_signal = "friction"
    elif any(token in lowered for token in ["understand", "learn", "help", "continue"]):
        relational_signal = "engagement"

    likely_need = "direct_answer"
    if turn_type == "repair":
        likely_need = "conversation_repair"
    elif turn_type == "confusion":
        likely_need = "clearer_explanation"
    elif turn_type == "memory_probe":
        likely_need = "memory_scope_check"
    elif turn_type == "identity_probe":
        likely_need = "concept_plus_self_position"
    elif turn_type == "objection":
        likely_need = "justification"
    elif turn_type == "question":
        if any(token in lowered for token in ["what is", "what are", "define", "explain", "how does", "why does"]):
            likely_need = "concept_explanation"
        elif any(token in lowered for token in ["do you", "can you", "would you", "are you"]):
            # Check for self-diagnostic or environmental unknowns before generic self_report
            if any(token in lowered for token in ["change yourself", "check your processes", "check your system"]):
                likely_need = "self_diagnostic"
            elif any(token in lowered for token in ["system health", "how's the weather", "weather"]):
                likely_need = "unknown_world_state"
            else:
                likely_need = "self_report"
        elif any(token in lowered for token in ["system health", "how's the weather", "weather"]):
            likely_need = "unknown_world_state"
    elif turn_type == "approval":
        likely_need = "continue_execution"
    elif turn_type == "execution_start":
        likely_need = "start_execution"
    elif turn_type == "completion_notify":
        likely_need = "track_completion"
    elif turn_type == "statement" and relational_signal == "friction":
        likely_need = "acknowledgment_and_adjustment"
    elif turn_type == "statement" and text.lower().strip() in {"test", "ok", "ready", "go", "start"}:
        likely_need = "light_acknowledgment"

    return {
        "message": text,
        "turn_type": turn_type,
        "topics": topics,
        "primary_topic": topics[0] if topics else "",
        "clarified_target": clarified_target,
        "has_explicit_clarification": bool(clarified_target),
        "intent": intent,
        "stance": stance,
        "relational_signal": relational_signal,
        "likely_need": likely_need,
        "needs_repair": turn_type == "repair",
        "asks_for_clarification": turn_type == "confusion",
        "probes_identity": turn_type == "identity_probe",
        "probes_memory": turn_type == "memory_probe",
        "reply_shape": reply_shape,
    }
