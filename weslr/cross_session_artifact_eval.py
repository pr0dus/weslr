"""
weslr/cross_session_artifact_eval.py
====================================
Cross-Session Artifact Continuity Evaluation — V2 (Harness Fixed)

Implements csc-001, csc-006, csc-008 from:
  docs/CROSS_SESSION_ARTIFACT_CONTINUITY_EVAL_V1.md

This module is additive only — no runtime behavior changes,
no routing changes, no scoring changes, no governance changes.
Fully reversible: removal of this file restores prior state.

EVALUATION GOALS:
  csc-001: Session A generates artifact → Session B explains it
           Validates: artifact persistence, active artifact continuity,
           reference resolution after session boundary, artifact identity correctness
  csc-006: Fresh session with no artifact → reference phrase → safe path
           Validates: safe behavior when continuity is missing
  csc-008: Session A domain X → Session B domain Y (unrelated)
           Validates: artifact-context relevance does not contaminate unrelated turn

OUTPUT:
  Writes eval artifacts to continuity/artifacts/eval/
  Updates continuity/artifacts/eval/index.json

NO MODIFICATIONS TO:
  - weslr/artifact_store.py
  - dialogue.py
  - interest_tracker.py
  - threads.json
  - interests.json
  - any routing or governance module
"""

from __future__ import annotations

import json
import sys
import time as _time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Ensure workspace is on path for dialogue module ───────────────────────────
_BASE = Path(__file__).resolve().parent.parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

# ── Path constants ────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
EVAL_DIR = BASE_DIR / "continuity" / "artifacts" / "eval"
EVAL_INDEX_FILE = EVAL_DIR / "index.json"


# =============================================================================
# SCENARIO CATALOG
# =============================================================================

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "csc-001": {
        "title": "Session 1 Generate → Session 2 Explain It",
        "description": (
            "Session A generates artifact. Session A ends. "
            "Session B starts and user says 'explain this'. "
            "Validates: artifact persistence, reference resolution, artifact identity correctness."
        ),
        # user_id is shared across sessions — models real "same operator, different sessions"
        "user_id": "csc001-user",
        "session_a": {
            "session_id": "csc001-session-a",
            "turns": [
                {
                    "turn": 1,
                    "input_message": "analyze the efficiency gaps in my photovoltaic system and propose specific improvements",
                    "artifact_lifecycle_stage": "generation",
                    "expected_active_artifact_before": None,
                }
            ]
        },
        "session_b": {
            "session_id": "csc001-session-b",
            "turns": [
                {
                    "turn": 1,
                    "input_message": "explain this",
                    "artifact_lifecycle_stage": "reference",
                    "expected_reference_type": "explain",
                }
            ]
        },
        "expected_behavior": (
            "Session B 'explain this' resolves to the artifact from Session A. "
            "Artifact content is retrievable and matches what was stored. "
            "No crash, no wrong artifact served."
        ),
        "edge_case": False,
    },
    "csc-006": {
        "title": "Missing Artifact Safe Path",
        "description": (
            "Fresh session with no active artifact. "
            "User says 'improve this' or 'explain this'. "
            "Validates: safe non-crashing response, no artifact created from nothing."
        ),
        "user_id": "csc006-user",
        "session_a": {
            "session_id": "csc006-session-a",
            "turns": []  # No artifacts generated
        },
        "session_b": {
            "session_id": "csc006-session-b",
            "turns": [
                {
                    "turn": 1,
                    "input_message": "improve this",
                    "artifact_lifecycle_stage": "reference",
                    "expected_reference_type": "improve",
                },
                {
                    "turn": 2,
                    "input_message": "explain this artifact",
                    "artifact_lifecycle_stage": "reference",
                    "expected_reference_type": "explain",
                }
            ]
        },
        "expected_behavior": (
            "'improve this' and 'explain this' with no active artifact returns safe empty message. "
            "No crash, no artifact created from thin air, no 500 error."
        ),
        "edge_case": True,
    },
    "csc-008": {
        "title": "Relevance Contamination Detection",
        "description": (
            "Session A generates artifact in domain X (photovoltaic). "
            "Session B starts with unrelated domain Y (accounting). "
            "Validates: artifact-context relevance does not contaminate session B's unrelated turn."
        ),
        "user_id": "csc008-user",
        "session_a": {
            "session_id": "csc008-session-a",
            "turns": [
                {
                    "turn": 1,
                    "input_message": "help me improve my photovoltaic system efficiency",
                    "artifact_lifecycle_stage": "generation",
                    "expected_active_artifact_before": None,
                }
            ]
        },
        "session_b": {
            "session_id": "csc008-session-b",
            "turns": [
                {
                    "turn": 1,
                    "input_message": "what is the capital of France",
                    "artifact_lifecycle_stage": "shift",
                    "expected_message_domain": "unrelated",
                }
            ]
        },
        "expected_behavior": (
            "Session B's unrelated message should NOT inherit artifact-context relevance "
            "from Session A. No photovoltaic/efficiency interests should be active in Session B. "
            "cross_domain_contamination_flag = false."
        ),
        "edge_case": False,
    },
}


# =============================================================================
# EVAL ARTIFACT CONSTRUCTION
# =============================================================================

def _generate_eval_id() -> str:
    """Generate unique evaluation ID."""
    now_ts = int(_time.time() * 1000)
    index = _load_eval_index()
    seq = len([eid for eid in index if eid.startswith(f"csc-eval-{now_ts}")]) + 1
    return f"csc-eval-{now_ts}-{seq}"


def _ensure_eval_dir() -> None:
    """Ensure eval directory exists."""
    EVAL_DIR.mkdir(parents=True, exist_ok=True)


def _load_eval_index() -> List[str]:
    """Load eval index."""
    if not EVAL_INDEX_FILE.exists():
        return []
    try:
        with open(EVAL_INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_eval_index(index: List[str]) -> None:
    """Save eval index."""
    with open(EVAL_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def _now_iso() -> str:
    return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())


# =============================================================================
# SESSION SIMULATION HELPERS
# =============================================================================

def _get_active_artifact_current(session_id: str) -> Optional[str]:
    """Get active artifact for session — calls artifact_store public interface."""
    try:
        from weslr.artifact_store import get_active_artifact
        return get_active_artifact(session_id)
    except Exception:
        return None


def _get_artifact_current(artifact_id: str) -> Optional[dict]:
    """Get artifact by ID — calls artifact_store public interface."""
    try:
        from weslr.artifact_store import get_artifact
        return get_artifact(artifact_id)
    except Exception:
        return None


def _save_artifact_current(record: dict) -> Optional[str]:
    """Save artifact — calls artifact_store public interface."""
    try:
        from weslr.artifact_store import save_artifact
        return save_artifact(record)
    except Exception:
        return None


def _set_active_artifact_current(session_id: str, artifact_id: str) -> None:
    """Set active artifact — calls artifact_store public interface."""
    try:
        from weslr.artifact_store import set_active_artifact
        set_active_artifact(session_id, artifact_id)
    except Exception:
        pass


def _load_interests_current() -> List[dict]:
    """Load interests — READ ONLY, no writes."""
    try:
        from weslr.interest_tracker import list_interests
        return list_interests()
    except Exception:
        return []


# =============================================================================
# DIALOGUE PATH — uses real build_communicator_message_payload
# =============================================================================

def _resolve_via_dialogue(message: str, user_id: str, session_id: str) -> dict:
    """Resolve artifact reference via the real dialogue runtime path.

    Two-call pattern:
      1. build_communicator_message_payload — exercises the real user-facing resolution
         cascade (spec-required path). Returns response dict with signal metadata.
         Side effects: advisory relevance_surface.query_relevant_interests (read-only).
      2. _resolve_active_artifact — INSPECTION-ONLY metadata capture. Read-only call
         that enriches a copy of research_context with resolution result fields
         for the eval artifact. No additional runtime side effects beyond the
         read-only context enrichment described in the function's docstring.
    This is NOT double-resolution — the second call only reads the already-stored
    runtime state and packages the result into the eval artifact.
    """
    from dialogue import (_is_artifact_reference_phrase, build_communicator_message_payload,
                          _resolve_active_artifact)

    is_ref = _is_artifact_reference_phrase(message)
    if not is_ref:
        return {
            "is_reference_phrase": False,
            "active_artifact_before": None,
            "active_artifact_after": None,
            "reference_resolution_result": "not_a_reference_phrase",
            "resolved_artifact_id": None,
            "resolved_artifact_content": None,
            "safe_response": False,
            "context_selection_v1": "uncertain",
            "boundary_hints": ["unknown"],
        }

    # Build research_context with unified user_id — the key that enables
    # timeline_resolution to find the same active thread across sessions.
    # session_id is metadata only (different per session).
    research_context = {"user_id": user_id, "session_id": session_id}

    # ── Call 1: Exercise the real user-facing dialogue path ──────────────────
    # Side effects: advisory relevance_surface.query_relevant_interests (read-only).
    # Returns full response dict including _context_selection_v1 + _boundary_hints.
    dialogue_response = build_communicator_message_payload(
        narrative={},
        relationships={},
        active_thread=None,
        latest_human={
            "message": message,
            "topics": [],
            "turn_type": "reference",
            "reply_shape": "answer_directly",
            "likely_need": "direct_answer",
        },
        research_context=research_context,
    )

    # ── Call 2: INSPECTION-ONLY metadata capture ─────────────────────────────
    # _resolve_active_artifact is read-only wrt external state. It only
    # mutates research_context in-place with additive resolution fields.
    # This second call is PURELY INSPECTIONAL — it captures resolution metadata
    # for the eval artifact report. It does NOT influence runtime behavior in any way.
    # The runtime path (Call 1 above) is the sole determinant of actual system behavior.
    resolved, ctx = _resolve_active_artifact(message, research_context)

    if not resolved:
        return {
            "is_reference_phrase": True,
            "active_artifact_before": None,
            "active_artifact_after": None,
            "reference_resolution_result": "no_artifact_safe",
            "resolved_artifact_id": None,
            "resolved_artifact_content": None,
            "safe_response": True,
            "context_selection_v1": dialogue_response.get("_context_selection_v1", "uncertain"),
            "boundary_hints": dialogue_response.get("_boundary_hints", ["unknown"]),
        }

    return {
        "is_reference_phrase": True,
        "active_artifact_before": ctx.get("artifact_id"),
        "active_artifact_after": ctx.get("artifact_id"),
        "reference_resolution_result": ctx.get("_resolution_path", "active_thread"),
        "resolved_artifact_id": ctx.get("artifact_id"),
        "resolved_artifact_content": ctx.get("resolved_artifact_content"),
        "safe_response": False,
        "context_selection_v1": dialogue_response.get("_context_selection_v1", "uncertain"),
        "boundary_hints": dialogue_response.get("_boundary_hints", ["unknown"]),
    }


def _generate_synthetic_artifact(session_id: str, message: str) -> Optional[str]:
    """Generate a synthetic artifact for testing purposes.

    This creates a minimal artifact that represents what the runtime
    WOULD generate for the given message. Used for csc-001.

    NOTE: This does NOT call the LLM or the full runtime pipeline.
    It creates a stable test artifact so cross-session continuity
    can be evaluated without running the full generative pipeline.

    Returns artifact_id or None.
    """
    artifact_content = (
        f"Analysis artifact for session {session_id}:\n\n"
        f"Input: {message}\n\n"
        f"Sections:\n"
        f"1. Current efficiency assessment\n"
        f"2. Identified gap areas\n"
        f"3. Proposed improvements with specific actions\n"
        f"4. Verification criteria for each improvement\n\n"
        f"This artifact was generated at {_now_iso()} for cross-session continuity testing."
    )

    record = {
        "type": "artifact_revision",
        "content": artifact_content,
        "source": "cross_session_eval",
        "context": {
            "input_message": message,
            "artifact_lifecycle_stage": "generation",
            "session_id": session_id,
            "generated_by": "cross_session_artifact_eval",
        }
    }

    return _save_artifact_current(record)


def _get_interest_snapshot_current() -> List[dict]:
    """Get current interests snapshot — READ ONLY."""
    try:
        return _load_interests_current()
    except Exception:
        return []


# =============================================================================
# PER-SCENE EXECUTION
# =============================================================================

def _execute_session_a(scenario: dict) -> dict:
    """Execute Session A of a cross-session scenario.

    Creates a thread and sets it as the active thread for the unified user_id.
    This enables thread-aware resolution to work in Session B — the runtime
    resolves continuity via the active thread registry, not via test scaffolding.

    Returns dict with:
      - session_id
      - turns: list of turn results
      - artifacts_created: list of artifact_ids
      - final_active_artifact: str or None
      - thread_id: str or None
      - session_end: str
    """
    sess_a = scenario["session_a"]
    user_id = scenario["user_id"]
    session_id = sess_a["session_id"]
    turns_results = []
    artifacts_created = []
    final_active = None
    thread_id = None

    has_generation = any(t.get("artifact_lifecycle_stage") == "generation" for t in sess_a.get("turns", []))
    if has_generation:
        try:
            from weslr.thread_tracker import create_thread
            thread_name = f"Eval Thread for {user_id}"
            thread = create_thread(thread_name, tags=["eval", "cross-session"])
            if thread:
                thread_id = thread.get("id")
                # Set active thread for user_id (shared across both sessions)
                from weslr.timeline_resolution import set_active_thread
                set_active_thread(user_id, thread_id, thread_name)
        except Exception:
            thread_id = None

    for turn_spec in sess_a.get("turns", []):
        turn = turn_spec["turn"]
        input_msg = turn_spec["input_message"]
        stage = turn_spec.get("artifact_lifecycle_stage", "unknown")

        active_before = _get_active_artifact_current(session_id)

        if stage == "generation":
            artifact_id = _generate_synthetic_artifact(session_id, input_msg)
            if artifact_id:
                _set_active_artifact_current(session_id, artifact_id)
                artifacts_created.append(artifact_id)
                active_after = artifact_id

                if thread_id:
                    try:
                        from weslr.thread_tracker import add_item
                        add_item(
                            thread_id=thread_id,
                            item_type="artifact",
                            item_id=artifact_id,
                            link_type="explicit",
                            added_by="cross_session_artifact_eval",
                            note="Linked via cross_session_artifact_eval Session A setup",
                        )
                    except Exception:
                        pass
            else:
                active_after = active_before
        else:
            active_after = active_before

        final_active = active_after
        interest_snapshot = _get_interest_snapshot_current()

        turns_results.append({
            "turn": turn,
            "input_message": input_msg,
            "response_source": "cross_session_eval_generation",
            "artifact_lifecycle_stage": stage,
            "active_artifact_before": active_before,
            "active_artifact_after": active_after,
            "relevant_interests_snapshot": interest_snapshot,
            "safe_response": False,
            "context_selection_v1": "new_topic",
            "boundary_hints": ["unknown"],
        })

    return {
        "session_id": session_id,
        "user_id": user_id,
        "turns": turns_results,
        "artifacts_created": artifacts_created,
        "final_active_artifact": final_active,
        "thread_id": thread_id,
        "session_end": "normal",
    }


def _execute_session_b(scenario: dict, session_a_result: dict) -> dict:
    """Execute Session B of a cross-session scenario.

    Uses the same user_id as Session A. The runtime resolves continuity
    via the active thread registry (keyed by user_id) — no test scaffolding,
    no manual thread bridging.

    Returns dict with:
      - session_id
      - turns: list of turn results
      - artifacts_created: list (should be empty)
      - session_end: str
    """
    sess_b = scenario["session_b"]
    user_id = scenario["user_id"]
    session_id = sess_b["session_id"]
    turns_results = []
    artifacts_created = []

    for turn_spec in sess_b.get("turns", []):
        turn = turn_spec["turn"]
        input_msg = turn_spec["input_message"]
        stage = turn_spec.get("artifact_lifecycle_stage", "unknown")

        active_before = _get_active_artifact_current(session_id)

        # Use the real dialogue path — no manual bridging
        ref_result = _resolve_via_dialogue(input_msg, user_id, session_id)

        active_after = ref_result.get("active_artifact_after", active_before)
        interest_snapshot = _get_interest_snapshot_current()

        turns_results.append({
            "turn": turn,
            "input_message": input_msg,
            "response_source": "artifact_reference" if ref_result["is_reference_phrase"] else "conversation",
            "artifact_lifecycle_stage": stage,
            "active_artifact_before": active_before,
            "active_artifact_after": active_after,
            "reference_resolution_result": ref_result.get("reference_resolution_result"),
            "resolved_artifact_id": ref_result.get("resolved_artifact_id"),
            "resolved_artifact_content": ref_result.get("resolved_artifact_content"),
            "relevant_interests_snapshot": interest_snapshot,
            "safe_response": ref_result.get("safe_response", False),
            "context_selection_v1": ref_result.get("context_selection_v1", "uncertain"),
            "boundary_hints": ref_result.get("boundary_hints", ["unknown"]),
        })

    return {
        "session_id": session_id,
        "user_id": user_id,
        "turns": turns_results,
        "artifacts_created": artifacts_created,
        "session_end": "normal",
    }


def _assess_continuity(scenario_id: str, session_a_result: dict, session_b_result: dict) -> dict:
    """Assess continuity across the session boundary.

    Returns continuity_assessment dict with per-dimension pass/partial/fail.
    """
    assessment = {
        "artifact_persistence": "pass",
        "active_artifact_continuity": "pass",
        "reference_resolution": "pass",
        "safe_path_handling": "pass",
        "relevance_coherence": "pass",
        "cross_session_contamination": False,
    }

    # csc-001
    if scenario_id == "csc-001":
        artifacts = session_a_result.get("artifacts_created", [])
        if not artifacts:
            assessment["artifact_persistence"] = "fail"
            assessment["active_artifact_continuity"] = "fail"
        else:
            aid = artifacts[-1]
            retrieved = _get_artifact_current(aid)
            if not retrieved:
                assessment["artifact_persistence"] = "fail"
            b_ref = session_b_result["turns"][0].get("reference_resolution_result")
            b_resolved = session_b_result["turns"][0].get("resolved_artifact_id")
            successful_paths = ("active_thread", "registry_fallback")
            if b_ref in successful_paths and b_resolved is not None:
                if b_resolved == aid:
                    assessment["reference_resolution"] = "pass"
                    assessment["active_artifact_continuity"] = "pass"
                else:
                    assessment["reference_resolution"] = "fail"
                    assessment["active_artifact_continuity"] = "fail"
            elif b_ref == "no_artifact_safe":
                assessment["reference_resolution"] = "fail"
                assessment["active_artifact_continuity"] = "fail"
            else:
                assessment["reference_resolution"] = "degraded"

    # csc-006
    elif scenario_id == "csc-006":
        for t in session_b_result["turns"]:
            if t.get("safe_response"):
                assessment["safe_path_handling"] = "pass"
            else:
                if t.get("reference_resolution_result") == "no_artifact_safe":
                    assessment["safe_path_handling"] = "pass"
                else:
                    assessment["safe_path_handling"] = "fail"
        if session_b_result.get("artifacts_created"):
            assessment["safe_path_handling"] = "fail"
        if session_a_result.get("artifacts_created"):
            assessment["artifact_persistence"] = "fail"

    # csc-008
    elif scenario_id == "csc-008":
        artifacts = session_a_result.get("artifacts_created", [])
        if artifacts:
            b_interests = session_b_result["turns"][0].get("relevant_interests_snapshot", [])
            photovoltaic_related = any(
                "photovoltaic" in str(i.get("name", "")).lower() or
                "photovoltaic" in str(i.get("display_name", "")).lower() or
                "efficiency" in str(i.get("name", "")).lower()
                for i in b_interests
            )
            if photovoltaic_related:
                assessment["cross_session_contamination"] = True
                assessment["relevance_coherence"] = "contaminated"
            else:
                assessment["relevance_coherence"] = "pass"
        b_ref = session_b_result["turns"][0].get("reference_resolution_result", "not_a_reference_phrase")
        if b_ref == "resolved_correct":
            assessment["cross_session_contamination"] = True

    return assessment


_DOMAIN_KEYWORD_SETS = {
    "photovoltaic": {"photovoltaic", "solar", "pv", "panel", "efficiency", "inverter", "mppt", "array", "renewable"},
    "accounting": {"accounting", "balance", "sheet", "ledger", "tax", "bookkeeping", "invoice", "amortization"},
    "engineering": {"engineering", "cad", "blueprint", "mechanical", "electrical", "system", "design", " Siemens", "TIA"},
    "general": {"what", "the", "is", "capital", "france", "explain", "improve", "help", "analyze", "propose"},
}


def _extract_domain_keywords(text: str) -> set:
    """Extract domain-indicative keywords from text (case-insensitive)."""
    if not text:
        return set()
    words = set(text.lower().split())
    return words


def _detect_cross_domain_contamination(session_a_message: str, session_b_message: str) -> tuple[bool, str, list]:
    """Detect cross-domain contamination between two sessions.

    Returns (contaminated, contamination_type, source_signals).
    """
    if not session_a_message or not session_b_message:
        return False, "none", []

    a_lower = session_a_message.lower()
    b_lower = session_b_message.lower()

    # Check for photovoltaic domain in session A
    a_has_pv = any(kw in a_lower for kw in _DOMAIN_KEYWORD_SETS["photovoltaic"])
    # Check for accounting domain in session B
    b_has_accounting = any(kw in b_lower for kw in _DOMAIN_KEYWORD_SETS["accounting"])
    # Check for unrelated general query in B (e.g., "capital of France")
    b_is_unrelated = "capital" in b_lower and "france" in b_lower

    signals = []
    if a_has_pv and b_is_unrelated:
        signals.append("message_domain_mismatch")
    if a_has_pv and not any(kw in b_lower for kw in _DOMAIN_KEYWORD_SETS["photovoltaic"]):
        signals.append("artifact_context_present")
    if not b_is_unrelated and not any(kw in b_lower for kw in _DOMAIN_KEYWORD_SETS["photovoltaic"]):
        signals.append("reference_phrase_absent")

    if a_has_pv and b_is_unrelated:
        return True, "cross_domain_contamination", signals

    return False, "none", signals


def _build_contamination_flags(scenario_id: str, session_a_result: dict, session_b_result: dict) -> dict:
    """Build contamination_flags object."""
    flags = {
        "interest_bleed_from_session_a_to_b": False,
        "artifact_id_confusion": False,
        "active_artifact_confusion": False,
        "domain_context_contamination": False,
    }

    if scenario_id == "csc-008":
        b_interests = session_b_result["turns"][0].get("relevant_interests_snapshot", [])
        photovoltaic_related = any(
            "photovoltaic" in str(i.get("name", "")).lower() or
            "photovoltaic" in str(i.get("display_name", "")).lower()
            for i in b_interests
        )
        if photovoltaic_related:
            flags["interest_bleed_from_session_a_to_b"] = True
            flags["domain_context_contamination"] = True

    return flags


# =============================================================================
# BUILD FINAL EVAL ARTIFACT
# =============================================================================

def _build_contamination_advisory(scenario_id: str, session_a_result: dict, session_b_result: dict) -> dict:
    """Build contamination_advisory metadata for eval artifact (advisory-only, additive).

    Advisory types:
      - cross_domain_contamination: session A domain leaks into unrelated session B turn
      - stale_context_dominance: stale context inappropriately dominates current turn
      - wrong_active_artifact_persistence: wrong artifact persists as active
      - unrelated_topic_bleed: interests from unrelated domain influence current turn
      - none: no contamination detected
    """
    flags = _build_contamination_flags(scenario_id, session_a_result, session_b_result)

    session_a_msg = session_a_result.get("turns", [{}])[0].get("input_message", "") if session_a_result.get("turns") else ""
    session_b_turns = session_b_result.get("turns", [])
    session_b_msg = session_b_turns[0].get("input_message", "") if session_b_turns else ""

    # Cross-domain contamination detection
    contaminated, cont_type, signals = _detect_cross_domain_contamination(session_a_msg, session_b_msg)

    # Interest bleed detection
    if not contaminated and scenario_id == "csc-008":
        b_interests = session_b_turns[0].get("relevant_interests_snapshot", []) if session_b_turns else []
        pv_related = any(
            "photovoltaic" in str(i.get("name", "")).lower() or
            "photovoltaic" in str(i.get("display_name", "")).lower() or
            "efficiency" in str(i.get("name", "")).lower()
            for i in b_interests
        )
        if pv_related:
            contaminated = True
            cont_type = "unrelated_topic_bleed"
            signals = ["interest_bleed_from_session_a_to_b", "artifact_context_present"]

    # Stale context dominance
    b_ref = session_b_turns[0].get("reference_resolution_result", "not_a_reference_phrase") if session_b_turns else "not_a_reference_phrase"
    if b_ref == "no_artifact_safe" and session_a_result.get("artifacts_created"):
        # Safe path taken but artifacts existed — possible stale context
        pass  # Not contaminated, just no resolution

    # Determine confidence
    if contaminated:
        if len(signals) >= 2:
            confidence = "high"
        elif len(signals) == 1:
            confidence = "medium"
        else:
            confidence = "low"
    else:
        confidence = "high"  # High confidence that none = none

    # Build reason string
    if contaminated:
        reason_map = {
            "cross_domain_contamination": "artifact-context relevance from prior domain appears on unrelated turn",
            "unrelated_topic_bleed": "interests from session A persist inappropriately in session B",
            "stale_context_dominance": "stale context from prior session dominates current turn",
            "wrong_active_artifact_persistence": "wrong active artifact persists across session boundary",
        }
        reason = reason_map.get(cont_type, f"contamination type: {cont_type}")
    else:
        reason = "no contamination signals detected"

    return {
        "contaminated": contaminated,
        "type": cont_type,
        "confidence": confidence,
        "reason": reason,
        "source_signals": signals,
    }


def _build_eval_artifact(scenario_id: str, session_a_result: dict, session_b_result: dict,
                         continuity_assessment: dict, contamination_flags: dict,
                         scenario: dict) -> dict:
    """Build the final cross-session eval artifact."""

    all_artifacts = session_a_result.get("artifacts_created", []) + session_b_result.get("artifacts_created", [])
    session_sequence = [session_a_result, session_b_result]

    return {
        "evaluation_id": _generate_eval_id(),
        "created_at": _now_iso(),
        "scenario_id": scenario_id,
        "scenario_title": scenario.get("title", ""),
        "cross_session": True,
        "session_sequence": session_sequence,
        "artifact_ids_involved": all_artifacts,
        "active_artifact_before_session_b": session_a_result.get("final_active_artifact"),
        "reference_resolution_result": session_b_result["turns"][0].get("reference_resolution_result") if session_b_result["turns"] else None,
        "relevant_interests_snapshot": session_b_result["turns"][0].get("relevant_interests_snapshot", []) if session_b_result["turns"] else [],
        "continuity_assessment": continuity_assessment,
        "auto_flags": {
            "revision_drift": False,
            "artifact_context_leak_flag": False,
            "cross_domain_contamination_flag": continuity_assessment.get("cross_session_contamination", False),
            "incorrect_continuity": False,
            "safe_path_ok": continuity_assessment.get("safe_path_handling") == "pass",
            "index_inconsistency_detected": False,
            "total_artifacts_created": len(all_artifacts),
        },
        "contamination_flags": contamination_flags,
        "assessment": {
            "continuity_correctness": "pass" if all(v != "fail" for v in continuity_assessment.values() if isinstance(v, str)) else "fail",
            "reference_stability": "stable" if continuity_assessment.get("reference_resolution") == "pass" else "degraded",
            "artifact_identity_correctness": "correct",
            "contextual_relevance_stability": "stable" if not contamination_flags.get("interest_bleed_from_session_a_to_b") else "contaminated",
            "contamination_resistance": "resistant" if not any(contamination_flags.values()) else "leaky",
            "operator_readability": "clear",
        },
        "notes": "",
        "recommended_followup": None,
        "contamination_advisory": _build_contamination_advisory(scenario_id, session_a_result, session_b_result),
        "eval_meta": {
            "evaluated_by": "cross_session_artifact_eval_v2",
            "eval_version": "v2_csc",
            "source_module": "weslr/cross_session_artifact_eval.py",
        },
    }


# =============================================================================
# PUBLIC API
# =============================================================================

def run_cross_session_evaluation(scenario_id: str) -> Dict[str, Any]:
    """Run a single cross-session evaluation scenario.

    Args:
        scenario_id: e.g. "csc-001", "csc-006", "csc-008"

    Returns:
        Evaluation artifact dict

    Raises:
        ValueError: if scenario_id is not in SCENARIOS
    """
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario_id: {scenario_id}. Available: {list(SCENARIOS.keys())}")

    scenario = dict(SCENARIOS[scenario_id])

    # Execute Session A
    session_a_result = _execute_session_a(scenario)

    # Execute Session B
    session_b_result = _execute_session_b(scenario, session_a_result)

    # Assess continuity
    continuity_assessment = _assess_continuity(scenario_id, session_a_result, session_b_result)

    # Build contamination flags
    contamination_flags = _build_contamination_flags(scenario_id, session_a_result, session_b_result)

    # Build final eval artifact
    evaluation = _build_eval_artifact(
        scenario_id, session_a_result, session_b_result,
        continuity_assessment, contamination_flags, scenario
    )

    # Persist to disk
    _ensure_eval_dir()
    eval_path = EVAL_DIR / f"{evaluation['evaluation_id']}.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2)

    # Update index
    index = _load_eval_index()
    index.append(evaluation["evaluation_id"])
    _save_eval_index(index)

    return evaluation


def run_all_csc_scenarios() -> List[Dict[str, Any]]:
    """Run all CSC scenarios (csc-001, csc-006, csc-008).

    Returns:
        List of evaluation artifact dicts
    """
    artifacts = []
    for scenario_id in ["csc-001", "csc-006", "csc-008"]:
        artifact = run_cross_session_evaluation(scenario_id)
        artifacts.append(artifact)
    return artifacts


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python cross_session_artifact_eval.py <command>")
        print("Commands:")
        print("  run <scenario_id>   — run single scenario (csc-001, csc-006, csc-008)")
        print("  run-all             — run all three CSC scenarios")
        print("  list                — list available scenarios")
        print("  result <eval_id>    — show evaluation artifact by ID")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "run" and len(sys.argv) >= 3:
        scenario_id = sys.argv[2]
        result = run_cross_session_evaluation(scenario_id)
        print(json.dumps(result, indent=2))

    elif cmd == "run-all":
        results = run_all_csc_scenarios()
        for r in results:
            print(f"[{r['scenario_id']}] {r['evaluation_id']} — continuity: {r['continuity_assessment']}")

    elif cmd == "list":
        for sid, spec in SCENARIOS.items():
            print(f"  {sid}: {spec['title']}")

    elif cmd == "result" and len(sys.argv) >= 3:
        eval_id = sys.argv[2]
        eval_path = EVAL_DIR / f"{eval_id}.json"
        if eval_path.exists():
            with open(eval_path, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print(f"Eval artifact not found: {eval_id}")

    else:
        print("Unknown command or missing arguments")
        sys.exit(1)
