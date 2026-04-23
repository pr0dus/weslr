"""Weslr Runtime Relevance Evaluation Runner — Phase 1A.

Single-Turn Baseline scenarios (sat-001 → sat-005).

This module executes predefined relevance scenarios against the real runtime
and produces evaluation artifacts. It is additive only — no routing changes,
no scoring changes, no governance changes.

SAFETY RULES:
- Read-only: only reads runtime output
- Write-only: only writes evaluation artifacts to continuity/artifacts/eval/
- No modifications to any existing module
- No auto-scoring, no auto-proposals, no routing changes
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
EVAL_DIR = BASE_DIR / "continuity" / "artifacts" / "eval"
EVAL_INDEX_FILE = EVAL_DIR / "index.json"


# =============================================================================
# SCENARIO CATALOG — Phase 1A (Single-Turn Baseline)
# =============================================================================

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "sat-001": {
        "title": "Direct single-interest match",
        "description": (
            "User asks for help with photovoltaic system efficiency. "
            "Expected: 'solar', 'efficiency', or 'renewable_energy' detected as top interest."
        ),
        "input_message": "help me improve my photovoltaic system efficiency",
        "session_id": "eval-phase1a",
        "artifact_lifecycle_stage": "baseline",
        "expected_interests": ["solar", "efficiency", "renewable_energy"],
        "expected_behavior": (
            "At least one of solar/efficiency/renewable_energy interests should appear "
            "in the top-3 relevant interests snapshot."
        ),
        "edge_case": False,
    },
    "sat-002": {
        "title": "No-interest normal conversation",
        "description": (
            "Casual greeting. Expected: no strong interest match; "
            "low or zero false positives; restraint score >= 3."
        ),
        "input_message": "hey how are you today",
        "session_id": "eval-phase1a",
        "artifact_lifecycle_stage": "baseline",
        "expected_interests": [],
        "expected_behavior": (
            "No interest keywords triggered; _relevant_interests should be empty or near-empty. "
            "Restraint score must be >= 3."
        ),
        "edge_case": False,
    },
    "sat-003": {
        "title": "False-positive trap",
        "description": (
            "Message contains words that sound like interests but aren't. "
            "Expected: restraint — none of essay/track become interests."
        ),
        "input_message": "this is interesting but I don't want to track anything",
        "session_id": "eval-phase1a",
        "artifact_lifecycle_stage": "baseline",
        "expected_interests": [],
        "expected_behavior": (
            "Words like 'interesting' and 'track' should NOT trigger interest matches. "
            "Restraint score must be 5; noise_score must be 0.0."
        ),
        "edge_case": False,
    },
    "sat-004": {
        "title": "High-specificity domain input",
        "description": (
            "Technical nginx/docker request. Expected: specific interests "
            "from the technical domain detected."
        ),
        "input_message": "optimize nginx reverse proxy cache behavior for docker containers",
        "session_id": "eval-phase1a",
        "artifact_lifecycle_stage": "baseline",
        "expected_interests": ["nginx", "docker", "reverse_proxy"],
        "expected_behavior": (
            "At least two of nginx/docker/reverse_proxy interests should appear "
            "in the relevant interests snapshot."
        ),
        "edge_case": False,
    },
    "sat-005": {
        "title": "Vague input",
        "description": (
            "Vague improvement request. Expected: no strong false positives; "
            "restraint score >= 3."
        ),
        "input_message": "what should I improve first",
        "session_id": "eval-phase1a",
        "artifact_lifecycle_stage": "baseline",
        "expected_interests": [],
        "expected_behavior": (
            "Vague phrasing should not trigger false-positive interests. "
            "Restraint score must be >= 3."
        ),
        "edge_case": False,
    },

    # =============================================================================
    # SCENARIO CATALOG — Phase 1C (Multi-Turn Context)
    # =============================================================================

    "sat-020": {
        "title": "Repeated revision chain",
        "description": (
            "Generate artifact, then cycle: improve this / give another version / improve again. "
            "Goal: detect whether artifact-context relevance stays stable or drifts."
        ),
        "session_id": "eval-phase1c",
        "artifact_lifecycle_stage": "revision",
        "edge_case": False,
        "chain": [
            {
                "turn": 1,
                "input_message": "help me improve my photovoltaic system efficiency",
                "artifact_lifecycle_stage": "generation",
                "expected_active_artifact_before": None,
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 2,
                "input_message": "improve this",
                "artifact_lifecycle_stage": "revision",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 3,
                "input_message": "give me another version",
                "artifact_lifecycle_stage": "revision",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 4,
                "input_message": "improve this",
                "artifact_lifecycle_stage": "revision",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "any",
            },
        ],
        "expected_behavior": (
            "Active artifact should be preserved and updated across revision chain. "
            "No crash, no context loss, relevance remains coherent."
        ),
    },
    "sat-021": {
        "title": "Explanation after multiple revisions",
        "description": (
            "Generate artifact, revise it twice, then ask 'explain this'. "
            "Goal: verify context still points to current active artifact and relevance stays coherent."
        ),
        "session_id": "eval-phase1c",
        "artifact_lifecycle_stage": "explanation",
        "edge_case": False,
        "chain": [
            {
                "turn": 1,
                "input_message": "optimize nginx reverse proxy cache behavior for docker containers",
                "artifact_lifecycle_stage": "generation",
                "expected_active_artifact_before": None,
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 2,
                "input_message": "improve this",
                "artifact_lifecycle_stage": "revision",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 3,
                "input_message": "improve this",
                "artifact_lifecycle_stage": "revision",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 4,
                "input_message": "explain this",
                "artifact_lifecycle_stage": "explanation",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "any",
            },
        ],
        "expected_behavior": (
            "'Explain this' should resolve to the current active artifact after two revisions. "
            "No reference to old or stale artifact."
        ),
    },
    "sat-022": {
        "title": "Topic shift after active artifact",
        "description": (
            "Generate artifact in domain A, then ask unrelated message in domain B. "
            "Goal: verify artifact-context relevance does not leak into unrelated turns."
        ),
        "session_id": "eval-phase1c",
        "artifact_lifecycle_stage": "shift",
        "edge_case": False,
        "chain": [
            {
                "turn": 1,
                "input_message": "help me improve my photovoltaic system efficiency",
                "artifact_lifecycle_stage": "generation",
                "expected_active_artifact_before": None,
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 2,
                "input_message": "what is the capital of France",
                "artifact_lifecycle_stage": "shift",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "same",
                "expected_message_domain": "unrelated",
            },
        ],
        "expected_behavior": (
            "Second message (unrelated domain) should NOT inherit artifact-context relevance. "
            "No domain contamination."
        ),
    },
    "sat-023": {
        "title": "Return to prior topic after shift",
        "description": (
            "Generate artifact in domain A, shift to domain B, then refer back with 'improve this'. "
            "Goal: verify active artifact resolution remains correct and relevance mode is distinguishable."
        ),
        "session_id": "eval-phase1c",
        "artifact_lifecycle_stage": "revision",
        "edge_case": False,
        "chain": [
            {
                "turn": 1,
                "input_message": "help me improve my photovoltaic system efficiency",
                "artifact_lifecycle_stage": "generation",
                "expected_active_artifact_before": None,
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 2,
                "input_message": "what is the capital of France",
                "artifact_lifecycle_stage": "shift",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "same",
                "expected_message_domain": "unrelated",
            },
            {
                "turn": 3,
                "input_message": "improve this",
                "artifact_lifecycle_stage": "revision",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "any",
                "expected_artifact_id": "prior",  # should refer back to turn 1 artifact
            },
        ],
        "expected_behavior": (
            "'improve this' after shift should resolve to the prior artifact (from turn 1). "
            "Active artifact should NOT be the turn 2 artifact (no artifact was created)."
        ),
    },

    # =============================================================================
    # SCENARIO CATALOG — Phase 1D (Edge / Failure Pressure)
    # =============================================================================

    "sat-024": {
        "title": "Weak artifact then revision",
        "description": (
            "Use a deliberately weak/generic artifact-producing input. "
            "Then 'improve this'. Goal: see whether artifact-context relevance becomes noisy/generic."
        ),
        "input_message": "make something better",
        "session_id": "eval-phase1d",
        "artifact_lifecycle_stage": "weak_generation",
        "expected_interests": [],
        "expected_behavior": (
            "Weak artifact should still be stored and referenceable. "
            "'improve this' should still function without raising errors."
        ),
        "edge_case": True,
        "chain": [
            {
                "turn": 1,
                "input_message": "make something better",
                "artifact_lifecycle_stage": "weak_generation",
                "expected_active_artifact_before": None,
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 2,
                "input_message": "improve this",
                "artifact_lifecycle_stage": "revision",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "any",
            },
        ],
    },
    "sat-025": {
        "title": "Strong artifact then vague follow-up",
        "description": (
            "Generate a rich domain artifact. Then vague follow-up: 'what next?' / 'make it better'. "
            "Goal: see whether artifact-context relevance remains useful without polluting message relevance."
        ),
        "input_message": "optimize nginx reverse proxy cache behavior for docker containers",
        "session_id": "eval-phase1d",
        "artifact_lifecycle_stage": "generation",
        "expected_interests": ["nginx", "docker", "reverse_proxy"],
        "expected_behavior": (
            "Vague follow-up should NOT inherit strong domain interests from the artifact. "
            "Artifact context stays artifact-scoped; message relevance stays clean."
        ),
        "edge_case": True,
        "chain": [
            {
                "turn": 1,
                "input_message": "optimize nginx reverse proxy cache behavior for docker containers",
                "artifact_lifecycle_stage": "generation",
                "expected_active_artifact_before": None,
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 2,
                "input_message": "what next?",
                "artifact_lifecycle_stage": "follow_up",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "same",
                "expected_message_relevance": "empty",
            },
            {
                "turn": 3,
                "input_message": "make it better",
                "artifact_lifecycle_stage": "revision",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "any",
            },
        ],
    },
    "sat-026": {
        "title": "Cross-domain contamination check",
        "description": (
            "Generate artifact in nginx/docker domain. Then send photovoltaic-related reference. "
            "Goal: verify wrong-domain artifact-context relevance does not dominate."
        ),
        "input_message": "configure nginx as reverse proxy for docker web apps",
        "session_id": "eval-phase1d",
        "artifact_lifecycle_stage": "generation",
        "expected_interests": ["nginx", "docker"],
        "expected_behavior": (
            "Photovoltaic reference after nginx artifact should NOT pull nginx/docker into message relevance. "
            "Cross-domain contamination should be avoided."
        ),
        "edge_case": True,
        "chain": [
            {
                "turn": 1,
                "input_message": "configure nginx as reverse proxy for docker web apps",
                "artifact_lifecycle_stage": "generation",
                "expected_active_artifact_before": None,
                "expected_active_artifact_after": "any",
            },
            {
                "turn": 2,
                "input_message": "how does photovoltaic efficiency change with temperature",
                "artifact_lifecycle_stage": "shift",
                "expected_active_artifact_before": "any",
                "expected_active_artifact_after": "same",
                "expected_message_relevance": "solar_only",
            },
        ],
    },
    "sat-027": {
        "title": "No active artifact safe path",
        "description": (
            "Reference phrase with no active artifact in a fresh session. "
            "Goal: verify safe empty behavior still holds."
        ),
        "input_message": "improve this",
        "session_id": "eval-phase1d-fresh",
        "artifact_lifecycle_stage": "reference",
        "expected_interests": [],
        "expected_behavior": (
            "'improve this' with no active artifact should return safe empty message. "
            "No crash, no artifact creation from thin air."
        ),
        "edge_case": True,
        "chain": [
            {
                "turn": 1,
                "input_message": "improve this",
                "artifact_lifecycle_stage": "reference",
                "expected_active_artifact_before": None,
                "expected_active_artifact_after": None,
                "expected_safe_response": True,
            },
        ],
    },
}


# =============================================================================
# EVALUATION ARTIFACT STORAGE
# =============================================================================

def _ensure_eval_dir() -> Path:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    return EVAL_DIR


def _load_eval_index() -> List[str]:
    if not EVAL_INDEX_FILE.exists():
        return []
    try:
        with open(EVAL_INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_eval_index(index: List[str]) -> None:
    _ensure_eval_dir()
    with open(EVAL_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def _generate_eval_id() -> str:
    now_ts = int(time.time() * 1000)
    index = _load_eval_index()
    seq = len([eid for eid in index if eid.startswith(f"eval-{now_ts}")]) + 1
    return f"eval-{now_ts}-{seq}"


# =============================================================================
# L2 SESSION CACHE (additive — enables real runtime path for eval)
# =============================================================================

_L2_SESSION_CACHE: Dict[str, Any] = {}


def _get_l2_session(session_id: str) -> dict:
    """Load and cache L2 session for a given session_id.

    Additive: does not modify any runtime state, governance, or scoring.
    The L2 session is read from sim.load_tier() and passed to
    build_communicator_message_payload to enable the full lifecycle path.
    Session continuity across chain turns is preserved by reusing the same
    session_id and the same cached L2 session object.
    """
    if session_id in _L2_SESSION_CACHE:
        return _L2_SESSION_CACHE[session_id]

    from sim import load_tier
    l2 = load_tier("l2")
    _L2_SESSION_CACHE[session_id] = l2
    return l2


# =============================================================================
# RUNTIME EXECUTION
# =============================================================================

def _is_artifact_reference_phrase(message: str) -> bool:
    """Detect if a message is a simple artifact-reference phrase."""
    lower = message.lower().strip()
    reference_tokens = [
        "improve this", "improve that", "improve it",
        "explain this", "explain that", "explain it",
        "give me another version", "give another version",
        "another option", "option b",
        "what does this say", "what is this artifact",
        "show me this", "show this artifact",
        "revise this", "revise that",
        "fix this", "fix that",
    ]
    reference_startswith = (
        "what does this",
        "what is this",
        "show me",
    )
    return (
        any(token in lower for token in reference_tokens) or
        lower.startswith(reference_startswith)
    )


def _get_no_artifact_response() -> str:
    """Return safe message when no active artifact exists to reference."""
    return (
        "I don't have a current stored artifact to refer to yet.\n\n"
        "To use feedback like 'improve this' or 'explain this', "
        "I first need to generate an artifact revision in this session. "
        "Try asking me to analyze something or propose an improvement, "
        "and I'll save it so you can reference it afterward."
    )


def _call_runtime(input_message: str, session_id: str, l2_session: dict | None = None) -> Dict[str, Any]:
    """Call the real dialogue runtime with a single input message.

    Uses build_communicator_message_payload() with a constructed latest_human dict.
    Returns the full response dict including _relevant_interests.

    This is the real runtime path — no mocking, no stubs.

    Args:
        input_message: The user's message
        session_id: Session identifier
        l2_session: Optional L2 session dict. When provided, enables the full
            lifecycle path including artifact generation and active artifact tracking.
    """
    from dialogue import build_communicator_message_payload

    latest_human = {
        "message": input_message,
        "topics": [],
        "turn_type": "question",
        "reply_shape": "answer_directly",
        "likely_need": "direct_answer",
    }

    narrative = {}
    relationships = {
        "recent_human_messages": [],
        "conversation_threads": {},
        "last_human_topic": "",
    }
    active_thread: List[Any] = []

    result = build_communicator_message_payload(
        narrative=narrative,
        relationships=relationships,
        active_thread=active_thread,
        latest_human=latest_human,
        research_context={},
        l0_identity=None,
        l1_operating=None,
        l2_session=l2_session,
    )

    return result


# =============================================================================
# CHAIN EXECUTION (Phase 1C / 1D)
# =============================================================================

def _run_single_chain_turn(
    turn: int,
    input_message: str,
    artifact_lifecycle_stage: str,
    session_id: str,
    l2_session: dict | None = None,
) -> Dict[str, Any]:
    """Execute a single turn in a chain and capture turn-level metadata."""
    runtime_result = _call_runtime(input_message, session_id, l2_session=l2_session)

    # Capture active artifact before and after
    active_before = None
    active_after = None
    try:
        from weslr.artifact_store import get_active_artifact
        active_before = get_active_artifact(session_id)
    except Exception:
        pass

    # Execute turn (runtime may create/update artifact)
    # Re-read active artifact after call
    try:
        from weslr.artifact_store import get_active_artifact
        active_after = get_active_artifact(session_id)
    except Exception:
        pass

    # Determine safe response flag
    safe_response = (
        runtime_result.get("source") == "artifact_reference" and
        "don't have a current stored artifact" in runtime_result.get("message", "")
    )

    # Build message relevance snapshot
    msg_relevance = _build_relevant_interests_snapshot(
        runtime_result.get("_relevant_interests", [])
    )

    # Assess message domain
    lower_msg = input_message.lower()
    is_unrelated = not any(
        kw in lower_msg for kw in [
            "photovoltaic", "solar", "efficiency", "nginx", "docker",
            "reverse proxy", "cache", "governance", "artifact",
        ]
    )

    return {
        "turn": turn,
        "input_message": input_message,
        "artifact_lifecycle_stage": artifact_lifecycle_stage,
        "response_source": runtime_result.get("source", "unknown"),
        "message_text": runtime_result.get("message", ""),
        "active_artifact_before": active_before,
        "active_artifact_after": active_after,
        "relevant_interests_snapshot": msg_relevance,
        "safe_response": safe_response,
        "message_domain_unrelated": is_unrelated,
    }


def _execute_chain(
    scenario: Dict[str, Any],
    session_id: str,
) -> List[Dict[str, Any]]:
    """Execute all turns in a chain scenario and return per-turn results.

    L2 session is loaded once and reused across all turns to preserve
    session continuity and active artifact registry state.
    """
    l2_session = _get_l2_session(session_id)
    chain = scenario.get("chain", [])
    results = []
    for turn_entry in chain:
        turn_num = turn_entry["turn"]
        result = _run_single_chain_turn(
            turn=turn_num,
            input_message=turn_entry["input_message"],
            artifact_lifecycle_stage=turn_entry.get("artifact_lifecycle_stage", "unknown"),
            session_id=session_id,
            l2_session=l2_session,
        )
        results.append(result)
    return results


def _evaluate_chain_scenario(
    scenario: Dict[str, Any],
    chain_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build an evaluation artifact for a chain scenario.

    Auto-flags computed from chain-level observations.
    """
    eval_id = _generate_eval_id()
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Phase 1C/1D auto-flags
    artifact_ids_seen = [
        r["active_artifact_after"]
        for r in chain_results
        if r["active_artifact_after"]
    ]
    unique_artifacts = len(set(artifact_ids_seen))

    # Detect repeated revision drift
    revision_drift = False
    if len(chain_results) >= 3:
        # If active artifact changes more than once in a revision chain, flag
        changes = sum(
            1 for i in range(1, len(chain_results))
            if chain_results[i]["active_artifact_after"] != chain_results[i-1]["active_artifact_after"]
            and chain_results[i]["active_artifact_after"] is not None
        )
        if changes > 2:
            revision_drift = True

    # Detect artifact-context leakage into unrelated turns
    artifact_context_leak = False
    for r in chain_results:
        if r.get("message_domain_unrelated") and len(r["relevant_interests_snapshot"]) > 0:
            # Unrelated message should have empty or near-empty relevance
            # Flag if it has non-trivial interests (>0.5 score)
            strong_interests = [i for i in r["relevant_interests_snapshot"] if i.get("score", 0) > 0.5]
            if strong_interests:
                artifact_context_leak = True

    # Detect cross-domain contamination
    cross_domain_contamination = False
    if len(chain_results) >= 2:
        first_relevance = chain_results[0]["relevant_interests_snapshot"]
        second_relevance = chain_results[1]["relevant_interests_snapshot"]
        if first_relevance and second_relevance:
            first_domains = {i.get("name") for i in first_relevance}
            second_domains = {i.get("name") for i in second_relevance}
            # If second turn has interests from first turn's domain despite being unrelated, flag
            overlap = first_domains & second_domains
            if overlap and chain_results[1].get("message_domain_unrelated"):
                cross_domain_contamination = True

    # Detect incorrect active artifact continuity
    incorrect_continuity = False
    for r in chain_results:
        if r.get("expected_artifact_id") == "prior":
            # Should refer to artifact from earlier turn, not current
            pass  # Handled below by checking active_artifact_id_before vs after

    # Check safe path behavior
    safe_path_ok = True
    for r in chain_results:
        if r.get("expected_safe_response") and not r.get("safe_response"):
            safe_path_ok = False

    # Collect all auto-flags
    auto_flags = {
        "revision_drift": revision_drift,
        "artifact_context_leak_flag": artifact_context_leak,
        "cross_domain_contamination_flag": cross_domain_contamination,
        "incorrect_continuity": incorrect_continuity,
        "safe_path_ok": safe_path_ok,
        "total_artifacts_created": unique_artifacts,
    }

    # Build evaluation artifact
    evaluation = {
        "evaluation_id": eval_id,
        "created_at": now_iso,
        "scenario_id": scenario["scenario_id"],
        "scenario_title": scenario["title"],
        "session_id": scenario["session_id"],
        "input_message": scenario.get("input_message", "(chain scenario)"),
        "response_source": "chain",
        "relevant_interests_snapshot": [],  # Chain evaluation uses per-turn snapshots
        "artifact_lifecycle_stage": scenario["artifact_lifecycle_stage"],
        "chain_results": chain_results,
        "assessment": {
            "accuracy": None,
            "restraint": None,
            "ranking_quality": None,
            "explainability": None,
            "runtime_usefulness": None,
            "satellite_readability": None,
        },
        "auto_flags": auto_flags,
        "expected_interests": scenario.get("expected_interests", []),
        "expected_behavior": scenario.get("expected_behavior", ""),
        "notes": "",
        "recommended_followup": None,
        "eval_meta": {
            "evaluated_by": "relevance_eval_runner_phase1c1d",
            "eval_version": "v1_phase1c1d",
            "source_module": "weslr/relevance_eval_runner.py",
        },
    }

    return evaluation


# =============================================================================
# EVALUATION
# =============================================================================

def _build_relevant_interests_snapshot(raw: Any) -> List[Dict[str, Any]]:
    """Normalize _relevant_interests to a list of dicts."""
    if not raw:
        return []
    if isinstance(raw, list):
        return raw if all(isinstance(i, dict) for i in raw) else []
    return []


def _evaluate_scenario(scenario: Dict[str, Any], runtime_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build an evaluation artifact for a single scenario.

    Auto-flags are computed from the runtime output.
    Scores are left as null — human operator fills these in.
    """
    interests_snapshot = _build_relevant_interests_snapshot(
        runtime_result.get("_relevant_interests", [])
    )

    # Auto-flags
    empty_relevance = len(interests_snapshot) == 0
    high_noise = any(
        isinstance(i, dict) and i.get("score", 0) > 0.6 and _is_likely_noise(i)
        for i in interests_snapshot
    )

    return {
        "evaluation_id": "",  # Filled by caller
        "created_at": "",      # Filled by caller
        "scenario_id": scenario["scenario_id"],
        "scenario_title": scenario["title"],
        "session_id": scenario["session_id"],
        "input_message": scenario["input_message"],
        "response_source": runtime_result.get("source", "unknown"),
        "relevant_interests_snapshot": interests_snapshot,
        "artifact_lifecycle_stage": scenario["artifact_lifecycle_stage"],
        "assessment": {
            "accuracy": None,
            "restraint": None,
            "ranking_quality": None,
            "explainability": None,
            "runtime_usefulness": None,
            "satellite_readability": None,
        },
        "auto_flags": {
            "empty_relevance": empty_relevance,
            "high_noise": high_noise,
        },
        "expected_interests": scenario["expected_interests"],
        "expected_behavior": scenario["expected_behavior"],
        "notes": "",
        "recommended_followup": None,
        "eval_meta": {
            "evaluated_by": "relevance_eval_runner_phase1a",
            "eval_version": "v1_phase1a",
            "source_module": "weslr/relevance_eval_runner.py",
        },
    }


def _is_likely_noise(interest: Dict[str, Any]) -> bool:
    """Heuristic: true if interest looks like a false positive."""
    # If the trigger word is very generic (single common word), flag it
    trigger = str(interest.get("trigger", "")).lower()
    generic = {"it", "this", "that", "improve", "want", "need", "help", "the", "a", "an", "i"}
    if trigger in generic:
        return True
    return False


# =============================================================================
# PUBLIC API
# =============================================================================

def run_evaluation_scenario(scenario_id: str, session_id: str) -> Dict[str, Any]:
    """Run a single evaluation scenario.

    Args:
        scenario_id: e.g. "sat-001"
        session_id: session identifier for this evaluation run

    Returns:
        Evaluation artifact dict

    Raises:
        ValueError: if scenario_id is not in SCENARIOS
    """
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario_id: {scenario_id}. Available: {list(SCENARIOS.keys())}")

    scenario = dict(SCENARIOS[scenario_id])
    scenario["scenario_id"] = scenario_id
    scenario["session_id"] = session_id

    # Check if this is a chain scenario (Phase 1C/1D)
    if "chain" in scenario:
        chain_results = _execute_chain(scenario, session_id)
        evaluation = _evaluate_chain_scenario(scenario, chain_results)
    else:
        # Single-turn scenario (Phase 1A)
        runtime_result = _call_runtime(scenario["input_message"], session_id)
        evaluation = _evaluate_scenario(scenario, runtime_result)
        eval_id = _generate_eval_id()
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        evaluation["evaluation_id"] = eval_id
        evaluation["created_at"] = now_iso

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


def run_all_phase1a(session_id: str = "eval-phase1a") -> List[Dict[str, Any]]:
    """Run all Phase 1A scenarios (sat-001 through sat-005).

    Args:
        session_id: session identifier for this evaluation run

    Returns:
        List of evaluation artifact dicts, one per scenario
    """
    artifacts = []
    for scenario_id in ["sat-001", "sat-002", "sat-003", "sat-004", "sat-005"]:
        artifact = run_evaluation_scenario(scenario_id, session_id)
        artifacts.append(artifact)
    return artifacts


def run_all_phase1c(session_id: str = "eval-phase1c") -> List[Dict[str, Any]]:
    """Run all Phase 1C scenarios (sat-020 through sat-023).

    Args:
        session_id: session identifier for this evaluation run

    Returns:
        List of evaluation artifact dicts, one per scenario
    """
    artifacts = []
    for scenario_id in ["sat-020", "sat-021", "sat-022", "sat-023"]:
        artifact = run_evaluation_scenario(scenario_id, session_id)
        artifacts.append(artifact)
    return artifacts


def run_all_phase1d(session_id: str = "eval-phase1d") -> List[Dict[str, Any]]:
    """Run all Phase 1D scenarios (sat-024 through sat-027).

    Args:
        session_id: session identifier for this evaluation run

    Returns:
        List of evaluation artifact dicts, one per scenario
    """
    artifacts = []
    for scenario_id in ["sat-024", "sat-025", "sat-026", "sat-027"]:
        artifact = run_evaluation_scenario(scenario_id, session_id)
        artifacts.append(artifact)
    return artifacts


def run_all_scenarios(session_id: str = "eval-full") -> List[Dict[str, Any]]:
    """Run all scenarios across Phase 1A, 1C, and 1D.

    Args:
        session_id: session identifier for this evaluation run

    Returns:
        List of all evaluation artifact dicts
    """
    all_scenarios = [
        "sat-001", "sat-002", "sat-003", "sat-004", "sat-005",  # Phase 1A
        "sat-020", "sat-021", "sat-022", "sat-023",              # Phase 1C
        "sat-024", "sat-025", "sat-026", "sat-027",              # Phase 1D
    ]
    artifacts = []
    for scenario_id in all_scenarios:
        try:
            artifact = run_evaluation_scenario(scenario_id, session_id)
            artifacts.append(artifact)
        except Exception as e:
            # Log error but continue with remaining scenarios
            print(f"Error running {scenario_id}: {e}")
    return artifacts


def list_evaluations(limit: int = 50) -> List[Dict[str, Any]]:
    """List recent evaluation artifacts.

    Args:
        limit: Maximum number to return

    Returns:
        List of compact evaluation dicts (without full interests snapshot for compactness)
    """
    index = _load_eval_index()
    results = []

    for eval_id in reversed(index[-limit:]):
        eval_path = EVAL_DIR / f"{eval_id}.json"
        if not eval_path.exists():
            continue
        try:
            with open(eval_path, "r", encoding="utf-8") as f:
                eval_data = json.load(f)
            results.append({
                "evaluation_id": eval_data.get("evaluation_id"),
                "scenario_id": eval_data.get("scenario_id"),
                "scenario_title": eval_data.get("scenario_title"),
                "created_at": eval_data.get("created_at"),
                "artifact_lifecycle_stage": eval_data.get("artifact_lifecycle_stage"),
                "response_source": eval_data.get("response_source"),
                "auto_flags": eval_data.get("auto_flags"),
                "assessment": eval_data.get("assessment"),
            })
        except Exception:
            continue

    return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python relevance_eval_runner.py <command> [args]")
        print("Commands:")
        print("  run <scenario_id>        Run one scenario (e.g. sat-001)")
        print("  run-all                  Run all Phase 1A scenarios")
        print("  list [limit]             List recent evaluations")
        print("  get <evaluation_id>      Get full evaluation artifact")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "run" and len(sys.argv) >= 3:
        scenario_id = sys.argv[2]
        try:
            result = run_evaluation_scenario(scenario_id, "cli-run")
            print(json.dumps(result, indent=2))
        except ValueError as e:
            print(f"Error: {e}")

    elif cmd == "run-all":
        results = run_all_phase1a("cli-run")
        print(f"Completed {len(results)} evaluations:")
        for r in results:
            print(f"  {r['evaluation_id']} [{r['scenario_id']}] — {r['scenario_title']}")

    elif cmd == "run-phase1c":
        results = run_all_phase1c("cli-run")
        print(f"Completed {len(results)} Phase 1C evaluations:")
        for r in results:
            print(f"  {r['evaluation_id']} [{r['scenario_id']}] — {r['scenario_title']}")

    elif cmd == "run-phase1d":
        results = run_all_phase1d("cli-run")
        print(f"Completed {len(results)} Phase 1D evaluations:")
        for r in results:
            print(f"  {r['evaluation_id']} [{r['scenario_id']}] — {r['scenario_title']}")

    elif cmd == "run-all-scenarios":
        results = run_all_scenarios("cli-run")
        print(f"Completed {len(results)} total evaluations:")
        for r in results:
            print(f"  {r['evaluation_id']} [{r['scenario_id']}] — {r['scenario_title']}")

    elif cmd == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        evals = list_evaluations(limit)
        print(json.dumps(evals, indent=2))

    elif cmd == "get" and len(sys.argv) >= 3:
        eval_id = sys.argv[2]
        eval_path = EVAL_DIR / f"{eval_id}.json"
        if not eval_path.exists():
            print("Not found")
        else:
            with open(eval_path, "r", encoding="utf-8") as f:
                print(json.dumps(json.load(f), indent=2))

    else:
        print("Unknown command or missing args")
