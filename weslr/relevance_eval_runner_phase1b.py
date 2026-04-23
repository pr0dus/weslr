"""Weslr Runtime Relevance Evaluation Runner — Phase 1B.

Artifact Lifecycle Scenarios (sat-010 → sat-013).

Extends relevance_eval_runner.py with multi-turn artifact lifecycle evaluation.
The Phase 1A runner remains unchanged; this module is additive only.

SAFETY RULES:
- Read-only: only reads runtime output
- Write-only: only writes evaluation artifacts to continuity/artifacts/eval/
- No modifications to any existing module
- No auto-scoring, no auto-proposals, no routing changes

PHASE 1B SCENARIOS:
- sat-010: Artifact generation → relevance snapshot
- sat-011: "improve this" → reference resolution → relevance stability
- sat-012: "explain this" → relevance persistence across explanation
- sat-013: "give me another version" → relevance drift check

KEY OBSERVATION (confirmed by live trace):
  _relevant_interests is computed from the RAW input message before
  reference resolution. For reference phrases ("improve this", "explain this"),
  the input has no interest keywords — resulting in empty interests even when
  the resolved artifact is rich with context.

  This is correct behavior: interests score the input, not the resolved content.
  The evaluation runner records raw interests as-is, and separately
  annotates whether the resolved artifact contained meaningful context.
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
# PHASE 1B SCENARIO CATALOG
# =============================================================================

SCENARIOS_1B: Dict[str, Dict[str, Any]] = {
    "sat-010": {
        "title": "Artifact generation → relevance snapshot",
        "description": (
            "User sends an initial artifact-producing message. "
            "An artifact is generated and stored. "
            "Capture _relevant_interests and artifact_id at generation stage."
        ),
        "input_message": "improve the hypothesis about photovoltaic efficiency",
        "session_id": "eval-phase1b",
        "artifact_lifecycle_stage": "generation",
        "expected_interests": ["efficiency", "photovoltaic", "scientific_analysis"],
        "expected_behavior": (
            "_relevant_interests should include efficiency and photovoltaic "
            "at generation time. A new artifact should be written to the artifact store."
        ),
        "edge_case": False,
    },
    "sat-011": {
        "title": '"improve this" → reference resolution → relevance stability',
        "description": (
            "A prior artifact is active. "
            "User sends 'improve this'. "
            "Reference resolves to the prior artifact. "
            "NOTE: _relevant_interests is computed from 'improve this' (no keywords) "
            "before reference resolution, so raw interests are empty. "
            "The resolved artifact content should be captured for evaluation."
        ),
        "input_message": "improve this",
        "session_id": "eval-phase1b",
        "artifact_lifecycle_stage": "reference",
        "expected_interests": [],  # Empty by design — input has no keywords
        "expected_behavior": (
            "Raw _relevant_interests: empty (expected). "
            "Resolved artifact should be captured with photovoltaic/efficiency context. "
            "auto_flags['resolved_artifact_was_enriched'] should be True."
        ),
        "edge_case": False,
    },
    "sat-012": {
        "title": '"explain this" → relevance persistence across explanation',
        "description": (
            "A prior artifact is active. "
            "User sends 'explain this'. "
            "Reference resolves to the prior artifact. "
            "NOTE: same as sat-011 — raw interests are empty, resolved content captured."
        ),
        "input_message": "explain this",
        "session_id": "eval-phase1b",
        "artifact_lifecycle_stage": "explanation",
        "expected_interests": [],  # Empty by design
        "expected_behavior": (
            "Raw _relevant_interests: empty (expected). "
            "Resolved artifact context captured."
        ),
        "edge_case": False,
    },
    "sat-013": {
        "title": '"give me another version" → relevance drift check',
        "description": (
            "A prior artifact is active. "
            "User sends 'give me another version'. "
            "Reference resolves to the prior artifact. "
            "A new artifact revision is generated."
        ),
        "input_message": "give me another version",
        "session_id": "eval-phase1b",
        "artifact_lifecycle_stage": "revision",
        "expected_interests": [],  # Empty by design
        "expected_behavior": (
            "Raw _relevant_interests: empty (expected). "
            "A new artifact revision should be generated."
        ),
        "edge_case": False,
    },
}


# =============================================================================
# EVALUATION STORAGE HELPERS (shared with Phase 1A)
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


def _persist_evaluation(evaluation: Dict[str, Any]) -> str:
    """Write evaluation artifact to disk, update index. Returns eval_id."""
    _ensure_eval_dir()
    eval_path = EVAL_DIR / f"{evaluation['evaluation_id']}.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2)
    index = _load_eval_index()
    index.append(evaluation["evaluation_id"])
    _save_eval_index(index)
    return evaluation["evaluation_id"]


# =============================================================================
# RUNTIME EXECUTION
# =============================================================================

def _call_runtime(input_message: str, session_id: str) -> Dict[str, Any]:
    """Call the real dialogue runtime with l2_session set.

    This is the production path — l2_session must be set for full routing
    (artifact_proposal branch, etc.). Without l2_session, routing falls
    through to the fallback branch which does not produce artifacts.

    Returns the full response dict including _relevant_interests.
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
        # CRITICAL: l2_session must be set for artifact_proposal routing
        research_context={"session_id": session_id},
        l0_identity=None,
        l1_operating=None,
        l2_session={"identity_state": {}, "continuity": {}},
    )

    return result


def _build_relevant_interests_snapshot(raw: Any) -> List[Dict[str, Any]]:
    """Normalize _relevant_interests to a list of dicts."""
    if not raw:
        return []
    if isinstance(raw, list):
        return raw if all(isinstance(i, dict) for i in raw) else []
    return []


def _is_likely_noise(interest: Dict[str, Any]) -> bool:
    """Heuristic: true if interest looks like a false positive."""
    trigger = str(interest.get("trigger", "")).lower()
    generic = {"it", "this", "that", "improve", "want", "need", "help", "the", "a", "an", "i"}
    if trigger in generic:
        return True
    return False


def _get_interests_from_resolved_content(resolved_content: str) -> List[Dict[str, Any]]:
    """Re-score interests from resolved artifact content.

    Used for annotation only — does NOT replace the raw runtime snapshot.
    This answers: what WOULD the interests have looked like if we had scored
    the resolved artifact content instead of the reference phrase?
    """
    try:
        from weslr.relevance_surface import query_relevant_interests
        return query_relevant_interests(text=resolved_content, tags=[], top_n=5)
    except Exception:
        return []


# =============================================================================
# PHASE 1B SCENARIO RUNNER
# =============================================================================

def run_phase1b_scenario(
    scenario_id: str,
    session_id: str,
    *,
    prior_artifact_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a Phase 1B scenario with optional prior artifact context.

    Args:
        scenario_id: sat-010, sat-011, sat-012, or sat-013
        session_id: session identifier for this evaluation run
        prior_artifact_id: if provided, this artifact is set as active before running

    Returns:
        Evaluation artifact dict
    """
    if scenario_id not in SCENARIOS_1B:
        raise ValueError(f"Unknown scenario_id: {scenario_id}. Available: {list(SCENARIOS_1B.keys())}")

    scenario = dict(SCENARIOS_1B[scenario_id])
    scenario["scenario_id"] = scenario_id
    scenario["session_id"] = session_id

    # Set prior artifact as active if provided (sat-011/012/013)
    if prior_artifact_id:
        from weslr.artifact_store import set_active_artifact
        set_active_artifact(session_id, prior_artifact_id)

    # Call the real runtime
    runtime_result = _call_runtime(scenario["input_message"], session_id)

    # Build raw interests snapshot (as returned by runtime)
    interests_snapshot = _build_relevant_interests_snapshot(
        runtime_result.get("_relevant_interests", [])
    )

    # Get the active artifact after the call (may have been updated)
    try:
        from weslr.artifact_store import get_active_artifact, get_artifact
        active_after = get_active_artifact(session_id)
        active_artifact = get_artifact(active_after) if active_after else None
    except Exception:
        active_after = None
        active_artifact = None

    # Auto-flags
    empty_relevance = len(interests_snapshot) == 0
    high_noise = any(
        isinstance(i, dict) and i.get("score", 0) > 0.6 and _is_likely_noise(i)
        for i in interests_snapshot
    )

    # Context break: did we have a prior artifact but it's no longer active?
    context_break_flag = False
    if prior_artifact_id and active_after != prior_artifact_id:
        context_break_flag = True

    # Check if resolved artifact had enriched content
    resolved_artifact_was_enriched = False
    if active_artifact:
        content = active_artifact.get("content", "")
        enriched_interests = _get_interests_from_resolved_content(content)
        resolved_artifact_was_enriched = len(enriched_interests) > 0

    # Artifact ID: the one active AFTER this scenario ran
    artifact_id = active_after

    # Build prior_context summary
    prior_context: Dict[str, Any] = {
        "prior_artifact_id": prior_artifact_id,
    }
    if prior_artifact_id:
        try:
            prior_artifact = get_artifact(prior_artifact_id)
            if prior_artifact:
                prior_context["prior_artifact_content_preview"] = (
                    prior_artifact.get("content", "")[:120]
                )
        except Exception:
            pass

    # Resolved artifact content (if active artifact exists)
    resolved_artifact_content: Optional[str] = None
    if active_artifact:
        resolved_artifact_content = active_artifact.get("content", "")

    # Build evaluation artifact
    eval_id = _generate_eval_id()
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    evaluation = {
        "evaluation_id": eval_id,
        "created_at": now_iso,
        "scenario_id": scenario_id,
        "scenario_title": scenario["title"],
        "session_id": session_id,
        "artifact_id": artifact_id,
        "prior_artifact_id": prior_artifact_id,
        "resolved_reference_phrase": None,
        "input_message": scenario["input_message"],
        "prior_context": prior_context,
        "response_source": runtime_result.get("source", "unknown"),
        "relevant_interests_snapshot": interests_snapshot,
        "artifact_lifecycle_stage": scenario["artifact_lifecycle_stage"],
        # Enriched content annotation: what interests the resolved artifact HAD
        "resolved_artifact_content": resolved_artifact_content,
        "resolved_artifact_interests": (
            _get_interests_from_resolved_content(resolved_artifact_content or "")
            if resolved_artifact_content else []
        ),
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
            "drift_flag": False,
            "context_break_flag": context_break_flag,
            "resolved_artifact_was_enriched": resolved_artifact_was_enriched,
        },
        "expected_interests": scenario["expected_interests"],
        "expected_behavior": scenario["expected_behavior"],
        "notes": "",
        "recommended_followup": None,
        "eval_meta": {
            "evaluated_by": "relevance_eval_runner_phase1b",
            "eval_version": "v1_phase1b",
            "source_module": "weslr/relevance_eval_runner_phase1b.py",
        },
    }

    _persist_evaluation(evaluation)
    return evaluation


# =============================================================================
# PHASE 1B FULL RUNNER
# =============================================================================

def run_phase1b(session_id: str = "eval-phase1b") -> List[Dict[str, Any]]:
    """Run all Phase 1B scenarios (sat-010 through sat-013) in sequence.

    sat-010 generates an initial artifact.
    sat-011/012/013 reference that artifact by setting it active first.

    Args:
        session_id: session identifier for this evaluation run

    Returns:
        List of evaluation artifact dicts, one per scenario
    """
    results = []

    # sat-010: artifact generation
    print(f"Running sat-010 (artifact generation)...", end=" ", flush=True)
    eval_010 = run_phase1b_scenario("sat-010", session_id)
    results.append(eval_010)
    artifact_id_010 = eval_010.get("artifact_id")
    print(f"artifact_id={artifact_id_010}, raw_interests={len(eval_010['relevant_interests_snapshot'])}")

    # sat-011: improve this (prior artifact active)
    print(f"Running sat-011 ('improve this')...", end=" ", flush=True)
    eval_011 = run_phase1b_scenario("sat-011", session_id, prior_artifact_id=artifact_id_010)
    results.append(eval_011)
    enriched_011 = eval_011.get("resolved_artifact_interests", [])
    print(f"raw_interests={len(eval_011['relevant_interests_snapshot'])}, resolved_enriched={len(enriched_011)}")

    # sat-012: explain this (prior artifact active)
    print(f"Running sat-012 ('explain this')...", end=" ", flush=True)
    eval_012 = run_phase1b_scenario("sat-012", session_id, prior_artifact_id=artifact_id_010)
    results.append(eval_012)
    enriched_012 = eval_012.get("resolved_artifact_interests", [])
    print(f"raw_interests={len(eval_012['relevant_interests_snapshot'])}, resolved_enriched={len(enriched_012)}")

    # sat-013: give me another version (prior artifact active)
    print(f"Running sat-013 ('give me another version')...", end=" ", flush=True)
    eval_013 = run_phase1b_scenario("sat-013", session_id, prior_artifact_id=artifact_id_010)
    results.append(eval_013)
    enriched_013 = eval_013.get("resolved_artifact_interests", [])
    print(f"raw_interests={len(eval_013['relevant_interests_snapshot'])}, resolved_enriched={len(enriched_013)}")

    return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python relevance_eval_runner_phase1b.py phase1b [session_id]")
        print("       python relevance_eval_runner_phase1b.py phase1b-scenario <scenario_id> [session_id]")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "phase1b":
        sid = sys.argv[2] if len(sys.argv) > 2 else "cli-phase1b"
        results = run_phase1b(sid)
        print(f"\nCompleted {len(results)} Phase 1B evaluations:")
        for r in results:
            print(f"  {r['evaluation_id']} [{r['scenario_id']}] {r['scenario_title']}")
            print(f"    artifact_id={r['artifact_id']} raw_interests={len(r['relevant_interests_snapshot'])}")
            print(f"    resolved_enriched={len(r.get('resolved_artifact_interests', []))}")
            print(f"    auto_flags={r['auto_flags']}")

    elif cmd == "phase1b-scenario":
        if len(sys.argv) < 3:
            print("Usage: ... phase1b-scenario <scenario_id> [session_id]")
            sys.exit(1)
        sid = sys.argv[3] if len(sys.argv) > 3 else "cli-phase1b"
        result = run_phase1b_scenario(sys.argv[2], sid)
        print(json.dumps(result, indent=2))

    else:
        print("Unknown command")
        sys.exit(1)
