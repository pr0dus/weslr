from __future__ import annotations

# B9: pattern escalation across turns (session-only, no persistence)
_B9_STATE = {
    "low_confidence_count": 0,
    "mismatch_count": 0,
}
# ---- Public demo mode guard ----

# Modes: private_dev | local_demo | public_demo_readonly
# Default is private_dev (no restrictions, developer/operator use)
_WESLR_MODE = "private_dev"

# Per-session request tracking for rate limiting (session-only, no persistence)
# Structure: {session_id: [timestamp, ...]}
_RATE_LIMIT_STATE: dict[str, list[float]] = {}

# Per-session LLM call tracking (only meaningful in LLM-enabled modes)
_LLM_CALL_STATE: dict[str, int] = {}

# Rate limit constants
_MAX_REQUESTS_PER_MINUTE = 10   # public_demo_readonly
_MAX_LLM_CALLS_PER_SESSION = 5  # public_demo_readonly


def _get_session_id() -> str:
    """Return a session identifier for rate limiting.
    
    In webchat/CLI context, use a fixed 'default' session marker.
    In production, this would be replaced with real session IDs from the transport layer.
    """
    return "default"


def _is_public_demo_readonly() -> bool:
    return _WESLR_MODE == "public_demo_readonly"


def _check_rate_limit() -> tuple[bool, str]:
    """Check if current session is within rate limit.
    
    Returns (allowed, reason). If not allowed, reason explains why.
    """
    import time
    if not _is_public_demo_readonly():
        return True, ""
    
    session_id = _get_session_id()
    now = time.time()
    window = 60.0  # 1-minute window
    
    # Initialize or clean old timestamps
    if session_id not in _RATE_LIMIT_STATE:
        _RATE_LIMIT_STATE[session_id] = []
    
    # Remove timestamps outside the window
    _RATE_LIMIT_STATE[session_id] = [
        ts for ts in _RATE_LIMIT_STATE[session_id]
        if now - ts < window
    ]
    
    if len(_RATE_LIMIT_STATE[session_id]) >= _MAX_REQUESTS_PER_MINUTE:
        return False, (
            f"Rate limit exceeded. Please wait. "
            f"({_MAX_REQUESTS_PER_MINUTE} requests/minute in public demo mode.)"
        )
    
    _RATE_LIMIT_STATE[session_id].append(now)
    return True, ""


def _check_llm_limit() -> tuple[bool, str]:
    """Check if LLM calls are still allowed in current session.
    
    Returns (allowed, reason). Only meaningful in public_demo_readonly mode.
    """
    if not _is_public_demo_readonly():
        return True, ""
    
    session_id = _get_session_id()
    count = _LLM_CALL_STATE.get(session_id, 0)
    
    if count >= _MAX_LLM_CALLS_PER_SESSION:
        return False, (
            f"Model usage limit reached for demo. "
            f"Try again later. ({_MAX_LLM_CALLS_PER_SESSION} LLM calls allowed per session.)"
        )
    
    _LLM_CALL_STATE[session_id] = count + 1
    return True, ""


def _build_safe_response(message: str, path: str, response_text: str, confidence: str = "low") -> dict:
    """Build a sanitized response that never leaks internal state."""
    return {
        "path": path,
        "response_text": response_text,
        "confidence": confidence,
        "message": message,
        "_weslr_mode": _WESLR_MODE,
    }


def set_weslr_mode(mode: str) -> None:
    """Set WESLR operating mode. Call this before interpret_human_turn in demo deployments.
    
    Valid modes: private_dev | local_demo | public_demo_readonly
    """
    global _WESLR_MODE
    if mode not in ("private_dev", "local_demo", "public_demo_readonly"):
        raise ValueError(f"Unknown WESLR mode: {mode!r}")
    _WESLR_MODE = mode


def get_weslr_mode() -> str:
    """Return the current WESLR operating mode."""
    return _WESLR_MODE


def _log_minimal_access(message: str, path: str, latency: float) -> None:
    """Minimal logging for public demo mode. Logs only route, timestamp, latency.
    
    DO NOT log raw user input, personal data, or internal paths.
    """
    # In public_demo_readonly, this would write to an access log.
    # In private_dev/local_demo, this is a no-op by default.
    pass


# B12.1: operator feedback log - separate from graph/proposals
import json as _json
from pathlib import Path as _Path
from weslr.proposal_traceability import record_proposal, record_decision, load_trace
from weslr.implementation_planning import create_implementation_plan, record_implementation_plan, load_implementation_plans
from weslr.iss.diagnostic_records import load_iss_diagnostics
from weslr.iss.probe_registry import get_probe_registry
from weslr.iss.probe_planning import create_probe_plan
from weslr.iss.probe_execution import execute_probe_simulated
from weslr.response_formatter import build_deterministic_response
from weslr.deterministic_handlers import dispatch_deterministic_handler
from weslr.write_handlers import dispatch_write_handler
from weslr.state_checkpoint import get_state_checkpoint
from entity_extractor import extract_entity_names_from_text

_FEEDBACK_LOG_PATH = _Path(__file__).resolve().parent / "weslr" / "operator_feedback_log.jsonl"

_VALID_DECISIONS = frozenset({"accepted", "rejected", "modified", "deferred"})

# C2_REAL: grounded capability map — reflects live code only, no future claims
_CAPABILITIES = {
    "interpretation": True,
    "entity_detection": True,
    "topic_detection": True,
    "confidence_assessment": True,
    "structured_response_text": True,
    "suggested_mode": True,
    "mode_analysis": True,
    "mode_explanation": True,
    "operator_suggestion": True,
    "interest_tracking": True,
    "interest_surfacing": True,
    "feedback_logging": True,
    "feedback_visibility": True,
    "write_control_modes": False,
    "autonomous_action": False,
    "self_modification": False,
    "learning_from_feedback": False,
    "capability_gap_detection": False,
    "capability_proposals": False,
    "ISS": False,
}


def _score_to_tier(score: float) -> str:
    if score >= 0.8:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def rank_capability_proposals(proposals: list[dict]) -> dict:
    """
    Rank C4 proposals by deterministic scoring against read-only signals.
    Read-only: get_interest_summary() + summarize_operator_feedback().
    No writes, no learning, no mutation beyond adding score metadata.
    """
    # History imports (read-only)
    try:
        trace_records = load_trace(100)
        plan_records = load_implementation_plans(100)
        # Build per-proposal history counts
        history = {}
        for r in trace_records:
            pid = r.get("proposal_id", "")
            if pid not in history:
                history[pid] = {"proposed": 0, "accepted": 0, "rejected": 0}
            if r.get("type") == "proposal_created":
                history[pid]["proposed"] = history[pid].get("proposed", 0) + 1
            elif r.get("type") == "proposal_decision":
                d = r.get("decision", "")
                if d == "accepted":
                    history[pid]["accepted"] = history[pid].get("accepted", 0) + 1
                elif d == "rejected":
                    history[pid]["rejected"] = history[pid].get("rejected", 0) + 1
        for r in plan_records:
            pid = r.get("proposal_id", "")
            if pid not in history:
                history[pid] = {"proposed": 0, "accepted": 0, "rejected": 0, "planned": 0}
            if "planned" not in history[pid]:
                history[pid]["planned"] = 0
            history[pid]["planned"] = history[pid].get("planned", 0) + 1
        history_checked = True
    except Exception:
        history = {}
        history_checked = False

    # Step 1: read interests (read-only)
    try:
        from interpretation import get_interest_summary
        interest_summary = get_interest_summary(limit=20)
        interests_checked = True
    except Exception:
        interest_summary = {}
        interests_checked = False

    # Step 2: read feedback (read-only)
    try:
        from interpretation import summarize_operator_feedback
        fb_summary = summarize_operator_feedback(limit=100)
        feedback_checked = True
    except Exception:
        fb_summary = {}
        feedback_checked = False

    # Step 3: score each proposal
    scored = []
    for p in proposals:
        cap = p["capability"]
        boost = 0.0

        # +0.1 if top interests exist
        if interests_checked and interest_summary:
            top = interest_summary.get("top_interests", [])
            if top:
                boost += 0.1

        # +0.2 if feedback summary has accepted count > 0
        if feedback_checked and fb_summary:
            accepted_count = fb_summary.get("total_accepted", 0)
            if accepted_count > 0:
                boost += 0.2

        base = 0.5
        # History modifiers (read-only)
        hist = history.get(cap, {})
        proposed = hist.get("proposed", 0)
        accepted = hist.get("accepted", 0)
        rejected = hist.get("rejected", 0)
        planned = hist.get("planned", 0)
        if proposed > 1:
            boost += 0.1
        if accepted > 0:
            boost += 0.2
        if rejected > 2:
            boost -= 0.2
        if accepted > 0 and planned == 0:
            boost += 0.2
        final = min(1.0, max(0.0, base + boost))

        # build reason string
        if boost == 0.0:
            reason = f"Baseline score only; no active operator signal for {cap}"
        else:
            parts = ["operator interest signal"] if boost >= 0.1 else []
            if boost >= 0.2:
                parts.append("positive feedback signal")
            reason = f"Score boosted ({', '.join(parts)}) for {cap}"

        scored.append({
            "capability": cap,
            "proposal": p["proposal"],
            "base_score": base,
            "signal_boost": boost,
            "final_score": final,
            "tier": _score_to_tier(final),
            "signal_source": {
                "interests_used": interests_checked,
                "feedback_used": feedback_checked,
            },
            "ranking_reason": reason,
            "history_signal": {
                "proposed": proposed,
                "accepted": accepted,
                "rejected": rejected,
                "planned": planned,
            },
        })

    # Step 4: sort by tier then alphabetically (deterministic, no randomness)
    tier_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ranked = sorted(scored, key=lambda x: (tier_order[x["tier"]], x["capability"]))

    return {
        "ranked_proposals": ranked,
        "signal_summary": {
            "interests_checked": interests_checked,
            "feedback_checked": feedback_checked,
            "history_checked": history_checked,
        },
    }


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


# Interest Tracker v1 — additive pattern tracking, no graph/proposal mutation

_INTEREST_TRACKER_PATH = _Path(__file__).resolve().parent / "weslr" / "interest_tracker.json"

_SOURCE_MULTIPLIERS = {
    "topic": 1.0,
    "entity": 1.5,
    "mode_suggestion": 0.5,
    "feedback_accepted": 2.0,
    "feedback_rejected": 0.0,  # recorded as evidence but does NOT reset count/score (v1)
}

_MAX_EVIDENCE_PER_INTEREST = 10


def _load_interest_tracker_state() -> dict:
    """Read current interest_tracker.json or return empty structure."""
    if not _INTEREST_TRACKER_PATH.exists():
        return {"interests": {}, "last_updated": None}
    with open(_INTEREST_TRACKER_PATH, "r", encoding="utf-8") as fh:
        return _json.loads(fh.read())


def _save_interest_tracker_state(state: dict) -> None:
    """Write state to interest_tracker.json."""
    _INTEREST_TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    import datetime as _dt
    state["last_updated"] = _dt.datetime.now().astimezone().isoformat()
    with open(_INTEREST_TRACKER_PATH, "w", encoding="utf-8") as fh:
        fh.write(_json.dumps(state, ensure_ascii=False, indent=2))


def record_interest_signal(
    *,
    topics: list[str] | None = None,
    entities: list[str] | None = None,
    suggested_mode: str | None = None,
    mode_mismatch: bool = False,
    escalation_level: str | None = None,
    operator_decision: str | None = None,
) -> dict:
    """Record one turn's interest signals. Additive only — no deletion, no auto-learning."""
    import datetime as _dt
    now = _dt.datetime.now().astimezone().isoformat()

    state = _load_interest_tracker_state()
    interests = state.get("interests", {})
    recorded_keys = []

    # Topics
    if topics:
        for topic in topics:
            key = topic.lower().strip()
            if key not in interests:
                interests[key] = {"key": key, "count": 0, "first_seen": now, "last_seen": now,
                                  "sources": [], "evidence": [], "score": 0.0}
            interests[key]["count"] += 1
            interests[key]["last_seen"] = now
            if "topic" not in interests[key]["sources"]:
                interests[key]["sources"].append("topic")
            interests[key]["evidence"].append({"type": "topic", "value": topic, "at": now})
            if len(interests[key]["evidence"]) > _MAX_EVIDENCE_PER_INTEREST:
                interests[key]["evidence"] = interests[key]["evidence"][-_MAX_EVIDENCE_PER_INTEREST:]
            _recompute_interest_score(interests[key])
            recorded_keys.append(key)

    # Entities
    if entities:
        for entity in entities:
            key = entity.lower().strip()
            if key not in interests:
                interests[key] = {"key": key, "count": 0, "first_seen": now, "last_seen": now,
                                  "sources": [], "evidence": [], "score": 0.0}
            interests[key]["count"] += 1
            interests[key]["last_seen"] = now
            if "entity" not in interests[key]["sources"]:
                interests[key]["sources"].append("entity")
            interests[key]["evidence"].append({"type": "entity", "value": entity, "at": now})
            if len(interests[key]["evidence"]) > _MAX_EVIDENCE_PER_INTEREST:
                interests[key]["evidence"] = interests[key]["evidence"][-_MAX_EVIDENCE_PER_INTEREST:]
            _recompute_interest_score(interests[key])
            recorded_keys.append(key)

    # Mode suggestion
    if suggested_mode:
        key = suggested_mode.lower().strip()
        if key not in interests:
            interests[key] = {"key": key, "count": 0, "first_seen": now, "last_seen": now,
                              "sources": [], "evidence": [], "score": 0.0}
        interests[key]["count"] += 1
        interests[key]["last_seen"] = now
        if "mode_suggestion" not in interests[key]["sources"]:
            interests[key]["sources"].append("mode_suggestion")
        interests[key]["evidence"].append({"type": "mode_suggestion", "value": suggested_mode, "at": now})
        if len(interests[key]["evidence"]) > _MAX_EVIDENCE_PER_INTEREST:
            interests[key]["evidence"] = interests[key]["evidence"][-_MAX_EVIDENCE_PER_INTEREST:]
        _recompute_interest_score(interests[key])
        recorded_keys.append(key)

    # Mode mismatch flag
    if mode_mismatch:
        key = "mode_mismatch"
        if key not in interests:
            interests[key] = {"key": key, "count": 0, "first_seen": now, "last_seen": now,
                              "sources": [], "evidence": [], "score": 0.0}
        interests[key]["count"] += 1
        interests[key]["last_seen"] = now
        if "mode_mismatch" not in interests[key]["sources"]:
            interests[key]["sources"].append("mode_mismatch")
        interests[key]["evidence"].append({"type": "mode_mismatch", "value": "true", "at": now})
        if len(interests[key]["evidence"]) > _MAX_EVIDENCE_PER_INTEREST:
            interests[key]["evidence"] = interests[key]["evidence"][-_MAX_EVIDENCE_PER_INTEREST:]
        _recompute_interest_score(interests[key])
        recorded_keys.append(key)

    # Escalation level
    if escalation_level:
        key = "escalation_" + escalation_level
        if key not in interests:
            interests[key] = {"key": key, "count": 0, "first_seen": now, "last_seen": now,
                              "sources": [], "evidence": [], "score": 0.0}
        interests[key]["count"] += 1
        interests[key]["last_seen"] = now
        if "escalation" not in interests[key]["sources"]:
            interests[key]["sources"].append("escalation")
        interests[key]["evidence"].append({"type": "escalation", "value": escalation_level, "at": now})
        if len(interests[key]["evidence"]) > _MAX_EVIDENCE_PER_INTEREST:
            interests[key]["evidence"] = interests[key]["evidence"][-_MAX_EVIDENCE_PER_INTEREST:]
        _recompute_interest_score(interests[key])
        recorded_keys.append(key)

    # Operator feedback decision
    if operator_decision:
        key = "feedback_" + operator_decision
        if key not in interests:
            interests[key] = {"key": key, "count": 0, "first_seen": now, "last_seen": now,
                              "sources": [], "evidence": [], "score": 0.0}
        interests[key]["count"] += 1
        interests[key]["last_seen"] = now
        src = "feedback_" + operator_decision
        if src not in interests[key]["sources"]:
            interests[key]["sources"].append(src)
        interests[key]["evidence"].append({"type": "feedback", "value": operator_decision, "at": now})
        if len(interests[key]["evidence"]) > _MAX_EVIDENCE_PER_INTEREST:
            interests[key]["evidence"] = interests[key]["evidence"][-_MAX_EVIDENCE_PER_INTEREST:]
        _recompute_interest_score(interests[key])
        recorded_keys.append(key)

        # Also record suggestion_accepted when feedback is accepted
        if operator_decision == "accepted":
            accepted_key = "suggestion_accepted"
            if accepted_key not in interests:
                interests[accepted_key] = {"key": accepted_key, "count": 0, "first_seen": now, "last_seen": now,
                                            "sources": [], "evidence": [], "score": 0.0}
            interests[accepted_key]["count"] += 1
            interests[accepted_key]["last_seen"] = now
            if "feedback_accepted" not in interests[accepted_key]["sources"]:
                interests[accepted_key]["sources"].append("feedback_accepted")
            interests[accepted_key]["evidence"].append({"type": "feedback", "value": "accepted", "at": now})
            if len(interests[accepted_key]["evidence"]) > _MAX_EVIDENCE_PER_INTEREST:
                interests[accepted_key]["evidence"] = interests[accepted_key]["evidence"][-_MAX_EVIDENCE_PER_INTEREST:]
            _recompute_interest_score(interests[accepted_key])

    state["interests"] = interests
    _save_interest_tracker_state(state)

    return {"recorded": True, "interests_updated": list(set(recorded_keys))}


def _recompute_interest_score(interest: dict) -> None:
    """Recompute score from count and source multipliers. Deterministic only."""
    count = interest.get("count", 0)
    total_mult = 0.0
    for src in interest.get("sources", []):
        total_mult += _SOURCE_MULTIPLIERS.get(src, 0.0)
    interest["score"] = round(count * total_mult, 3)


def get_interest_summary(limit: int = 20) -> dict:
    """Return top interests sorted by score descending. Read-only."""
    state = _load_interest_tracker_state()
    interests = sorted(
        state.get("interests", {}).values(),
        key=lambda x: x.get("score", 0.0),
        reverse=True,
    )[:limit]
    return {
        "total_interests": len(state.get("interests", {})),
        "last_updated": state.get("last_updated"),
        "top_interests": interests,
    }


def list_top_interests(n: int = 10) -> list[dict]:
    """Return top N interests by score. Convenience wrapper."""
    summary = get_interest_summary(limit=n)
    return summary["top_interests"]


def get_interest_visibility(limit: int = 10) -> dict:
    """Return operator-facing interest visibility. Read-only."""
    summary = get_interest_summary(limit=limit)
    top = summary.get("top_interests", [])

    if not top:
        status_text = "No recurring interests detected"
    else:
        formatted = ", ".join(
            f"{i['key']} ({round(i.get('score', 0), 2)})"
            for i in top[:5]
        )
        status_text = f"Top interests: {formatted}"

    return {
        "summary": summary,
        "top": top,
        "status_text": status_text,
    }


def should_surface_interests(limit: int = 10) -> dict:
    """Determine if interest patterns should be surfaced. Read-only."""
    summary = get_interest_summary(limit=limit)
    top = summary.get("top_interests", [])

    if not top:
        return {"show": False, "reason": "no_interests"}

    highest = top[0]
    count = highest.get("count", 0)
    score = highest.get("score", 0.0)

    # simple deterministic thresholds
    if count >= 3:
        return {
            "show": True,
            "reason": "repeated_interest",
            "interest": highest["key"],
            "count": count,
            "score": score,
        }

    return {"show": False, "reason": "below_threshold"}


def format_interest_for_chat(limit: int = 10) -> str | None:
    """Return chat-safe interest observation line, or None."""
    surface = should_surface_interests(limit=limit)

    if not surface.get("show"):
        return None

    interest = surface.get("interest")
    count = surface.get("count")

    if not interest:
        return None

    return f"Observation: You have repeatedly interacted with '{interest}' ({count} times)."


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
    import time as _time
    _t0 = _time.perf_counter()
    text = str(message or "").strip()
    lowered = text.lower()

    # SECTION 1/3 — Rate limit check (public_demo_readonly)
    rate_ok, rate_reason = _check_rate_limit()
    if not rate_ok:
        return _build_safe_response(
            message=message,
            path="rate_limited",
            response_text=rate_reason,
            confidence="high",
        )

    # SECTION 2/3 — Write handler block (public_demo_readonly)
    # In public_demo_readonly, write handlers are never dispatched.
    if _is_public_demo_readonly():
        # First check if a write handler would have matched.
        # We inspect the triggers without calling the handler (avoids side effects).
        from weslr.write_handlers import WRITE_HANDLER_REGISTRY
        write_triggered = False
        for entry in sorted(WRITE_HANDLER_REGISTRY, key=lambda h: h["priority"], reverse=True):
            for trigger in entry["triggers"]:
                if lowered.startswith(trigger):
                    write_triggered = True
                    break
                # Also check bare trigger without trailing space (e.g. "convert iss suggestion")
                if lowered == trigger.rstrip():
                    write_triggered = True
                    break
            if write_triggered:
                break

        if write_triggered:
            return _build_safe_response(
                message=message,
                path="blocked_write",
                response_text="This action is disabled in public demo mode.",
                confidence="high",
            )

        # Not a write — try deterministic (read-only) handlers
        dispatched = dispatch_deterministic_handler(message, lowered)
        if dispatched is not None:
            return dispatched

        # No handler matched at all — safe fallback
        return _build_safe_response(
            message=message,
            path="fallback_safe",
            response_text="I'm not able to process that request.",
            confidence="low",
        )

    # SECTION 3/3 — Normal flow (private_dev / local_demo)
    # Handler registry dispatch — read-only queries first
    dispatched = dispatch_deterministic_handler(message, lowered)
    if dispatched is not None:
        return dispatched

    # ISS probe execution (governed, simulated) — inline, not in deterministic_handlers
    # because it requires confirmation logic and simulated execution state.
    _execute_triggers = ["execute probe "]
    _triggered_execute = None
    for t in _execute_triggers:
        if lowered.startswith(t):
            _triggered_execute = t
            break
    if _triggered_execute:
        raw_input = lowered[len(_triggered_execute):].strip().strip('"').strip("'")
        requires_confirm = " confirm" in raw_input
        probe_id = raw_input.replace(" confirm", "").strip()
        probes = get_probe_registry()
        matched = next((p for p in probes if p["probe_id"] == probe_id), None)
        if not matched:
            return {
                "message": message,
                "response_text": "No probe found for '" + probe_id + "'. Use 'show iss probes' to inspect available probes.",
                "path": "ISS_probe_execution",
                "_weslr_deterministic": True,
                "confidence": "high",
                "probe_execution": {
                    "executed": False,
                    "requires_confirmation": False,
                    "mode": "simulated",
                    "probe_id": probe_id,
                },
            }
        if not requires_confirm:
            return {
                "message": message,
                "response_text": "Probe execution requires confirmation. Say: 'execute probe " + probe_id + " confirm'. This will run simulated execution only.",
                "path": "ISS_probe_execution",
                "_weslr_deterministic": True,
                "confidence": "high",
                "probe_execution": {
                    "executed": False,
                    "requires_confirmation": True,
                    "mode": "simulated",
                    "probe_id": probe_id,
                },
            }
        result = execute_probe_simulated(matched)
        return {
            "message": message,
            "response_text": "Probe '" + probe_id + "' executed in simulated mode. Status: " + str(result["status"]) + ".",
            "path": "ISS_probe_execution",
            "_weslr_deterministic": True,
            "confidence": "high",
            "probe_execution": {
                "executed": True,
                "mode": "simulated",
                "result": result,
            },
        }

    # Write handler dispatch — state-changing operations
    write_result = dispatch_write_handler(message, lowered)
    if write_result is not None:
        return write_result

    # Safe fallback for None returns
    return _build_safe_response(
        message=message,
        path="fallback_safe",
        response_text="I'm not able to process that request.",
        confidence="low",
    )
    # C1/C2/C3 handlers must be ordered: more specific queries before shorter substrings
    if "what can you do" in lowered or "your capabilities" in lowered or "what are your capabilities" in lowered:
        return {
            "message": message,
            "response_text": (
                "I can analyze input for entities and topics, assess confidence, "
                "produce structured response text, suggest interpretation modes, explain those suggestions, "
                "track repeated interests, surface repeated interests, and record operator feedback. "
                "I cannot currently act autonomously, modify myself, learn from feedback, or generate capability proposals."
            ),
            "confidence": "high",
            "suggested_mode": "observe",
            "mode_analysis": {
                "current_mode": None,
                "suggested_mode": "observe",
                "match": True,
                "mismatch": False,
                "reason": "Capability query"
            },
            "mode_suggestion": None,
            "suggestion_surface": {"show": False, "priority": "low"},
            "capabilities": _CAPABILITIES,
            "_weslr_deterministic": True,
        }
    if "what can't you do" in lowered or "what are you missing" in lowered or "what are your limitations" in lowered or "what can you not do" in lowered:
        missing = [k for k, v in _CAPABILITIES.items() if v is False]
        # ISS bridge: include diagnostic gap signals in visibility only
        iss_gap_summaries = []
        try:
            records = load_iss_diagnostics(50)
            iss_gaps = [r for r in records if r.get("type") == "iss_gap_signal"]
            iss_gap_summaries = [
                {
                    "gap_id": r.get("gap_id"),
                    "summary": r.get("summary"),
                    "severity": r.get("severity"),
                    "confidence": r.get("confidence"),
                    "source_probe_id": r.get("source_probe_id"),
                }
                for r in iss_gaps
            ]
        except Exception:
            pass  # must never break C3
        iss_note = ""
        if iss_gap_summaries:
            iss_note = f" Observed ISS diagnostic gaps: {len(iss_gap_summaries)}. Use 'show gaps' for details."
        return {
            "message": message,
            "response_text": (
                "I currently do not have the following capabilities: "
                + ", ".join(missing)
                + ". These represent areas where functionality is not yet implemented."
                + iss_note
            ),
            "confidence": "high",
            "suggested_mode": "observe",
            "mode_analysis": {
                "current_mode": None,
                "suggested_mode": "observe",
                "match": True,
                "mismatch": False,
                "reason": "Capability gap query"
            },
            "mode_suggestion": None,
            "suggestion_surface": {"show": False, "priority": "low"},
            "missing_capabilities": missing,
            "iss_gap_signals": iss_gap_summaries,
            "iss_gap_count": len(iss_gap_summaries),
            "_weslr_deterministic": True,
        }
    if "how can you improve" in lowered or "what could be added" in lowered or "what are possible improvements" in lowered or "can you add intelligence layers" in lowered or "how can you become better" in lowered:
        missing = [k for k, v in _CAPABILITIES.items() if v is False]
        proposals = []
        # build proposal dicts for ranking
        raw_proposals = []
        if "learning_from_feedback" in missing:
            raw_proposals.append({"capability": "learning_from_feedback", "proposal": "A feedback learning layer to analyze accepted/rejected suggestions"})
        if "capability_gap_detection" in missing:
            raw_proposals.append({"capability": "capability_gap_detection", "proposal": "A capability gap detection layer to identify missing functionality automatically"})
        if "capability_proposals" in missing:
            raw_proposals.append({"capability": "capability_proposals", "proposal": "A capability proposal system to suggest new modules based on usage patterns"})
        if "autonomous_action" in missing:
            raw_proposals.append({"capability": "autonomous_action", "proposal": "A controlled execution layer for safe, operator-approved actions"})

        # C5_REAL: rank proposals (read-only, no writes)
        try:
            ranked = rank_capability_proposals(raw_proposals)
            ranked_proposals = ranked["ranked_proposals"]
            signal_summary = ranked["signal_summary"]
            for p in ranked_proposals:
                record_proposal(p["capability"], {
                    "proposal": p["proposal"],
                    "base_score": p["base_score"],
                    "signal_boost": p["signal_boost"],
                    "final_score": p["final_score"],
                    "tier": p["tier"],
                    "ranking_reason": p["ranking_reason"],
                })
        except Exception:
            ranked_proposals = raw_proposals
            signal_summary = {"interests_checked": False, "feedback_checked": False}

        # ISS bridge: surface gap-derived suggestions (non-binding, separate from ranked proposals)
        iss_suggestions = []
        try:
            iss_records = load_iss_diagnostics(50)
            for gap in iss_records:
                if gap.get("type") != "iss_gap_signal":
                    continue
                gap_id = gap.get("gap_id", "")
                # Strip "gap." prefix to form proposal_id
                proposal_id = gap_id[4:] if gap_id.startswith("gap.") else gap_id
                iss_suggestions.append({
                    "proposal_id": proposal_id,
                    "source": "ISS",
                    "summary": gap.get("summary", ""),
                    "severity": gap.get("severity", "medium"),
                    "confidence": gap.get("confidence", "medium"),
                    "suggested": True,
                })
        except Exception:
            pass  # must never break C4

        iss_note = ""
        if iss_suggestions:
            iss_note = f" ISS suggests {len(iss_suggestions)} additional capability area(s). These are diagnostic suggestions, not active proposals."

        proposal_texts = [p["proposal"] for p in ranked_proposals]
        return {
            "message": message,
            "response_text": (
                "Based on my current limitations, the following improvements could be considered: "
                + "; ".join(proposal_texts)
                + ". These are suggestions only and would require operator approval to implement."
                + iss_note
            ),
            "confidence": "high",
            "suggested_mode": "observe",
            "mode_analysis": {
                "current_mode": None,
                "suggested_mode": "observe",
                "match": True,
                "mismatch": False,
                "reason": "Capability proposal query"
            },
            "mode_suggestion": None,
            "suggestion_surface": {"show": False, "priority": "low"},
            "proposed_capabilities": ranked_proposals,
            "proposal_signal_summary": signal_summary,
            "iss_suggested_proposals": iss_suggestions,
            "iss_suggestion_count": len(iss_suggestions),
            "_weslr_deterministic": True,
        }
    # C6_REAL: operator approval workflow
    lower_msg = lowered
    decision = None
    cap = None
    if lower_msg.startswith("accept proposal "):
        decision = "accepted"
        cap = lower_msg[len("accept proposal "):].strip()
    elif lower_msg.startswith("approve proposal "):
        decision = "accepted"
        cap = lower_msg[len("approve proposal "):].strip()
    elif lower_msg.startswith("reject proposal "):
        decision = "rejected"
        cap = lower_msg[len("reject proposal "):].strip()
    elif lower_msg.startswith("deny proposal "):
        decision = "rejected"
        cap = lower_msg[len("deny proposal "):].strip()
    if decision is not None:
        # Allow any proposal_id (including dot-separated like iss.not_integrated)
        # The check against _CAPABILITIES is removed so ISS intake proposals can be approved
        if cap not in _CAPABILITIES:
            # Fallback: check if it's a known proposal in trace history
            trace = load_trace(100)
            known_ids = set(r.get("proposal_id") for r in trace if r.get("type") == "proposal_created")
            if cap not in known_ids:
                return {
                    "message": message,
                    "response_text": f"Capability '{cap}' is not a recognized proposal.",
                    "confidence": "high",
                    "suggested_mode": "observe",
                    "mode_analysis": {"current_mode": None, "suggested_mode": "observe", "match": True, "mismatch": False, "reason": "Operator decision recorded"},
                    "mode_suggestion": None,
                    "suggestion_surface": {"show": False, "priority": "low"},
                    "decision_recorded": False,
                }
        event = {"operator_decision": decision, "capability": cap, "type": "capability_proposal"}
        log_operator_feedback(event)
        record_decision(cap, decision)
        impl_plan = None
        if decision == "accepted":
            import time as _time
            proposal_content = {
                "summary": f"Approved proposal: {cap}",
                "decision": decision,
                "decision_timestamp": _time.time(),
            }
            impl_plan = create_implementation_plan(cap, proposal_content)
            record_implementation_plan(impl_plan)
        return {
            "message": message,
            "response_text": f"Proposal '{cap}' has been {decision} by the operator. No changes have been applied.",
            "confidence": "high",
            "suggested_mode": "observe",
            "mode_analysis": {
                "current_mode": None,
                "suggested_mode": "observe",
                "match": True,
                "mismatch": False,
                "reason": "Operator decision recorded"
            },
            "mode_suggestion": None,
            "suggestion_surface": {"show": False, "priority": "low"},
            "decision_recorded": True,
            "_weslr_deterministic": True,
            "implementation_plan": {
                "plan_id": impl_plan["plan_id"] if impl_plan else None,
                "proposal_id": impl_plan["proposal_id"] if impl_plan else None,
                "status": impl_plan["status"] if impl_plan else None,
                "execution_allowed": impl_plan["execution_allowed"] if impl_plan else None,
                "operator_approval_required": impl_plan["operator_approval_required"] if impl_plan else None,
            } if impl_plan else None,
        }

    # C8Q: implementation plan queries (read-only) — now in deterministic_handlers.py
    if "who are you" in lowered or "what are you" in lowered:
        return {
            "message": message,
            "response_text": (
                "I am Weslr, a structured interpretation system. "
                "I analyze input for entities and topics, assess confidence, "
                "suggest interpretation modes, and track repeated patterns over time. "
                "I do not act autonomously or modify my own behavior. "
                "All suggestions are advisory and operator-controlled."
            ),
            "confidence": "high",
            "suggested_mode": "observe",
            "mode_analysis": {
                "current_mode": None,
                "suggested_mode": "observe",
                "match": True,
                "mismatch": False,
                "reason": "System self-description request"
            },
            "mode_suggestion": None,
            "suggestion_surface": {"show": False, "priority": "low"},
            "_weslr_deterministic": True,
        }
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

    # IT1.1: passive interest tracking (non-blocking, no side effects)
    try:
        record_interest_signal(
            topics=topics,
            entities=None,
            suggested_mode=None,
            mode_mismatch=False,
            escalation_level=None,
            operator_decision=None,
        )
    except Exception:
        pass  # must never break main flow

    surface = should_surface_interests(limit=10)

    # B1_REAL: confidence assessment
    try:
        entity_names = extract_entity_names_from_text(message)
    except Exception:
        entity_names = []
    if entity_names and len(entity_names) >= 2:
        confidence = "high"
    elif entity_names or topics:
        confidence = "medium"
    else:
        confidence = "low"

    # B3_REAL: suggested_mode advisory
    if confidence == "low":
        suggested_mode = "observe"
    elif len(entity_names) >= 2:
        suggested_mode = "entity_only"
    elif topics:
        suggested_mode = "topic_only"
    else:
        suggested_mode = "normal"

    # B4_REAL: mode_analysis structure
    # current_mode not yet available as input — for now always match
    mode_match = True
    mode_mismatch = False

    # B5_REAL: explanation of why suggested_mode was chosen
    if suggested_mode == "observe":
        mode_reason = "Low signal detected; observation mode is appropriate"
    elif suggested_mode == "entity_only":
        mode_reason = f"Detected {len(entity_names)} entities; structural interpretation is appropriate"
    elif suggested_mode == "topic_only":
        mode_reason = "Detected topics; pattern-level interpretation is appropriate"
    else:
        mode_reason = "Default interpretation is appropriate"

    # B6_REAL: operator-facing suggestion
    if suggested_mode == "entity_only":
        mode_suggestion = f"Consider focusing on entity relationships for this input"
    elif suggested_mode == "topic_only":
        mode_suggestion = f"Consider focusing on topic patterns for this input"
    elif suggested_mode == "observe":
        mode_suggestion = f"Consider gathering more input before deeper interpretation"
    else:
        mode_suggestion = None

    # B7_REAL: controlled suggestion surfacing
    if confidence == "low":
        show_suggestion = True
        suggestion_priority = "medium"
    elif suggested_mode == "entity_only":
        show_suggestion = True
        suggestion_priority = "high"
    elif suggested_mode == "topic_only":
        show_suggestion = True
        suggestion_priority = "medium"
    else:
        show_suggestion = False
        suggestion_priority = "low"


    # ---- proposal_id normalizer (private helper) ----
    _STOP_SUFFIXES = [" important", " important?", " high priority", " prioritized", " priority", "?"]

    def _normalize_proposal_id(raw: str) -> str:
        value = raw.strip().strip('"').strip("'").strip()
        lowered = value.lower()
        for suffix in _STOP_SUFFIXES:
            if lowered.endswith(suffix):
                value = value[: -len(suffix)].strip()
                lowered = value.lower()
        return value

    # ---- ISS controlled proposal intake — now in weslr/write_handlers.py

    # ---- ISS intake proposal query (read-only) — now in deterministic_handlers.py

    # ISS probe planning (declarative, non-executing) — now in deterministic_handlers.py

    # ISS probe execution (governed, simulated)
    _execute_triggers = ["execute probe "]
    _triggered_execute = None
    for t in _execute_triggers:
        if lowered.startswith(t):
            _triggered_execute = t
            break
    if _triggered_execute:
        raw_input = lowered[len(_triggered_execute):].strip().strip('"').strip("'")
        requires_confirm = " confirm" in raw_input
        probe_id = raw_input.replace(" confirm", "").strip()
        probes = get_probe_registry()
        matched = next((p for p in probes if p["probe_id"] == probe_id), None)
        if not matched:
            return {
                "message": message,
                "response_text": "No probe found for '" + probe_id + "'. Use 'show iss probes' to inspect available probes.",
                "path": "ISS_probe_execution",
                "_weslr_deterministic": True,
                "confidence": "high",
                "probe_execution": {
                    "executed": False,
                    "requires_confirmation": False,
                    "mode": "simulated",
                    "probe_id": probe_id,
                },
            }
        if not requires_confirm:
            return {
                "message": message,
                "response_text": "Probe execution requires confirmation. Say: 'execute probe " + probe_id + " confirm'. This will run simulated execution only.",
                "path": "ISS_probe_execution",
                "_weslr_deterministic": True,
                "confidence": "high",
                "probe_execution": {
                    "executed": False,
                    "requires_confirmation": True,
                    "mode": "simulated",
                    "probe_id": probe_id,
                },
            }
        result = execute_probe_simulated(matched)
        return {
            "message": message,
            "response_text": "Probe '" + probe_id + "' executed in simulated mode. Status: " + str(result["status"]) + ".",
            "path": "ISS_probe_execution",
            "_weslr_deterministic": True,
            "confidence": "high",
            "probe_execution": {
                "executed": True,
                "mode": "simulated",
                "result": result,
            },
        }

    # Proposal explanation layer (read-only) — now in deterministic_handlers.py

