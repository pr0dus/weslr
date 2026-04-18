"""Weslr Platform: Continuity Core (v1)

Weslr-native continuity logic, portable across runtimes.
No runtime-specific dependencies.

Paths are configurable via BASE_DIR parameter to support multiple runtime adapters.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from . import contracts


# Try to import adapter, fall back to None if not available
try:
    from .adapters.openclaw import OpenClawPaths
except ImportError:
    OpenClawPaths = None

# Default paths (override via adapter parameter in functions)
# The adapter will provide paths - this is just a fallback for testing
DEFAULT_BASE_DIR = None  # adapter will provide this; None means "auto-detect"
DEFAULT_CONTINUITY_DIR = "continuity"


def get_paths(base_dir: str = None, adapter: "OpenClawPaths" = None) -> tuple[str, str, str, str]:
    """Get continuity paths, configurable via adapter or base_dir.
    
    Priority:
    1. adapter.base_dir() if adapter provided
    2. base_dir if provided (for direct use without adapter)
    3. OpenClawPaths auto-detection if both are None
    """
    if adapter is not None:
        base_dir = adapter.base_dir()
    # base_dir can be None here - OpenClawPaths will auto-detect
    if base_dir is None:
        paths = OpenClawPaths() if OpenClawPaths else None
        if paths:
            base_dir = paths.base_dir()
        else:
            base_dir = DEFAULT_BASE_DIR
    continuity_dir = os.path.join(base_dir, DEFAULT_CONTINUITY_DIR)
    snapshot_dir = os.path.join(continuity_dir, "snapshots")
    metrics_file = os.path.join(continuity_dir, "metrics.json")
    return base_dir, continuity_dir, snapshot_dir, metrics_file


# ===== WESLRContinuityState — the actual state we snapshot =====

def load_weslr_continuity_state(base_dir: str = None, adapter: "OpenClawPaths" = None) -> Dict[str, Any]:
    """Load the real WESLR continuity state from source files.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    base_dir, _, _, _ = get_paths(base_dir, adapter)
    state = {
        "identity_anchor": None,
        "communicator_continuity": {},
        "session_continuity": {},
        "unresolved_shared_threads": [],
        "opportunity_board": {},
        "categories": {},
        "review_queue": [],
        "export_queue": [],
        "operator_work": [],
    }

    # Load identity
    try:
        with open(os.path.join(base_dir, "state_core.json")) as f:
            core = json.load(f)
            state["identity_anchor"] = core.get("identity_anchor")
            state["communicator_continuity"]["status"] = core.get("status")
            state["communicator_continuity"]["session_count"] = core.get("continuity", {}).get("session_count", 0)
            state["unresolved_shared_threads"] = core.get("unresolved_shared_threads", [])
    except Exception:
        pass

    # Load communicator_self continuity signals
    try:
        with open(os.path.join(base_dir, "communicator_self.json")) as f:
            comm = json.load(f)
            state["communicator_continuity"]["confidence_score"] = comm.get("continuity", {}).get("confidence_score", 0.0)
            state["communicator_continuity"]["known_humans"] = comm.get("relationships", {}).get("known_humans", [])
            state["communicator_continuity"]["active_threads"] = list(comm.get("memory_layers", {}).get("working", {}).get("active_concern_topics", []))
    except Exception:
        pass

    # Load session_continuity state (optional, may not exist in all runtimes)
    try:
        from session_continuity import load_session_state, get_session_continuity
        session_state = load_session_state()
        continuity = get_session_continuity()
        state["session_continuity"] = {
            "session_count": session_state.get("session_count", 0),
            "sessions": session_state.get("sessions", []),
            "active_threads_from_prev": continuity.get("active_threads_from_prev", []),
        }
    except Exception:
        pass

    # Load opportunity_board
    try:
        with open(os.path.join(base_dir, "opportunity_board.json")) as f:
            state["opportunity_board"] = json.load(f)
    except Exception:
        pass

    # Load categories (category_proposals.json)
    try:
        with open(os.path.join(base_dir, "category_proposals.json")) as f:
            state["categories"] = json.load(f)
    except Exception:
        pass

    # Load review_queue
    try:
        with open(os.path.join(base_dir, "review_queue.json")) as f:
            state["review_queue"] = json.load(f)
    except Exception:
        pass

    # Load export_queue
    try:
        with open(os.path.join(base_dir, "export_queue.json")) as f:
            state["export_queue"] = json.load(f)
    except Exception:
        pass

    # Load operator/work continuity (work_items.json)
    try:
        with open(os.path.join(base_dir, "work_items.json")) as f:
            state["operator_work"] = json.load(f)
    except Exception:
        pass

    return state


# ===== SNAPSHOT STRUCTURE (WESLR fields) =====

def build_snapshot(session_id: str, state_or_base_dir: Any = None, state: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build snapshot from real WESLR continuity state."""
    if state is not None:
        # state provided directly (backward compat)
        state = state
    elif isinstance(state_or_base_dir, dict):
        # state provided as positional arg (backward compat)
        state = state_or_base_dir
    else:
        # base_dir provided
        state = load_weslr_continuity_state(state_or_base_dir)
    return {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "identity_anchor": state.get("identity_anchor"),
        "communicator_continuity": state.get("communicator_continuity", {}),
        "session_continuity": state.get("session_continuity", {}),
        "unresolved_shared_threads": state.get("unresolved_shared_threads", []),
        "opportunity_board": state.get("opportunity_board", {}),
        "categories": state.get("categories", {}),
        "review_queue": state.get("review_queue", []),
        "export_queue": state.get("export_queue", []),
        "operator_work": state.get("operator_work", []),
        "continuity_markers": {
            "confidence": calculate_confidence(state),
            "debt": calculate_continuity_debt(state),
            "fields": list(state.keys()),
        },
        "restore_plan": build_restore_plan(state),
    }


def save_snapshot(snapshot: Dict[str, Any], base_dir: str = None, adapter: "OpenClawPaths" = None, overwrite: bool = False) -> str:
    """Save snapshot to continuity/snapshots/.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    _, _, snapshot_dir, _ = get_paths(base_dir, adapter)
    os.makedirs(snapshot_dir, exist_ok=True)
    ts = snapshot["timestamp"].replace(":", "-").replace(".", "-")
    filename = f"snapshot_{ts}_{snapshot['session_id'][:8]}.json"
    path = os.path.join(snapshot_dir, filename)
    if not overwrite and os.path.exists(path):
        raise FileExistsError(f"Snapshot exists: {path}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return filename


def load_snapshot(filename: str, base_dir: str = None, adapter: "OpenClawPaths" = None) -> Dict[str, Any]:
    """Load snapshot from continuity/snapshots/.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    _, _, snapshot_dir, _ = get_paths(base_dir, adapter)
    path = os.path.join(snapshot_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_snapshots(base_dir: str = None, adapter: "OpenClawPaths" = None) -> List[str]:
    """List snapshot filenames in continuity/snapshots/.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    _, _, snapshot_dir, _ = get_paths(base_dir, adapter)
    if not os.path.exists(snapshot_dir):
        return []
    return sorted([f for f in os.listdir(snapshot_dir) if f.startswith("snapshot_")])


# ===== CONFIDENCE / DEBT (WESLR continuity model) =====

def calculate_confidence(state: Dict[str, Any]) -> float:
    """Calculate confidence based on WESLR continuity signals."""
    base = 100.0
    comm = state.get("communicator_continuity", {})
    if comm.get("confidence_score", 0) >= 0.7:
        base += 5
    if len(comm.get("known_humans", [])) > 0:
        base += 3
    if len(comm.get("active_threads", [])) > 0:
        base += 5
    sess = state.get("session_continuity", {})
    if sess.get("session_count", 0) >= 5:
        base += 5
    if len(sess.get("active_threads_from_prev", [])) > 0:
        base += 5
    if state.get("identity_anchor"):
        base += 5
    if len(state.get("unresolved_shared_threads", [])) > 2:
        base -= 10
    if len(state.get("review_queue", [])) > 0:
        base -= 5
    return max(0.0, min(100.0, round(base, 1)))


def calculate_continuity_debt(state: Dict[str, Any]) -> float:
    """Calculate continuity debt — unresolved threads, pending reviews, missing anchors."""
    debt = 0.0
    unresolved = state.get("unresolved_shared_threads", [])
    debt += 10 * len(unresolved)
    review_queue = state.get("review_queue", [])
    debt += 5 * len(review_queue)
    export_queue = state.get("export_queue", [])
    debt += 3 * len(export_queue)
    if not state.get("identity_anchor"):
        debt += 20
    comm = state.get("communicator_continuity", {})
    if comm.get("confidence_score", 1.0) < 0.5:
        debt += 15
    return min(100.0, round(debt, 1))


# ===== RESTORE PLAN BUILDER (WESLR fields) =====

def build_restore_plan(state: Dict[str, Any]) -> Dict[str, Any]:
    """Build restore plan using contracts.
    
    This delegates to contracts.create_restore_plan
    to maintain consistency across the platform.
    """
    plan = contracts.create_restore_plan(
        strategy="continuity_preservation",
        fallback="state_core_restore",
        fields=[
            "identity_anchor",
            "communicator_continuity",
            "session_continuity",
            "unresolved_shared_threads",
            "opportunity_board",
            "categories",
            "review_queue",
            "export_queue",
            "operator_work",
        ]
    )
    # Fill in items based on state
    for key in plan["continuity_fields"]:
        value = state.get(key)
        if value is None:
            plan["items"].append({"key": key, "action": "skip", "reason": "missing"})
        elif isinstance(value, (str, int, float, bool)):
            plan["items"].append({"key": key, "action": "direct", "value": value})
        elif isinstance(value, list):
            plan["items"].append({"key": key, "action": "restore_list", "count": len(value)})
        elif isinstance(value, dict):
            plan["items"].append({"key": key, "action": "restore_dict", "keys": list(value.keys())})
        else:
            plan["items"].append({"key": key, "action": "manual", "reason": "complex_type"})
    return plan


# ===== UTILS =====

def get_current_snapshot_info(base_dir: str = None, adapter: "OpenClawPaths" = None) -> Optional[Dict[str, Any]]:
    """Get info about the most recent snapshot.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    snapshots = list_snapshots(base_dir, adapter)
    if not snapshots:
        return None
    try:
        return load_snapshot(snapshots[-1], base_dir, adapter)
    except Exception:
        return None


def restore_from_plan(snapshot: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """Simulate restore from plan (dry_run=True) or apply (dry_run=False)."""
    plan = snapshot.get("restore_plan", {})
    result = {
        "snapshot_id": snapshot.get("session_id"),
        "fields": plan.get("continuity_fields", []),
        "items_processed": 0,
        "items_failed": 0,
        "items_skipped": 0,
        "actions": [],
    }
    for item in plan.get("items", []):
        key = item["key"]
        action = item["action"]
        if action == "skip":
            result["items_skipped"] += 1
            result["actions"].append({"key": key, "action": "skipped", "reason": item.get("reason")})
        elif action in ("direct", "restore_list", "restore_dict"):
            if not dry_run:
                result["actions"].append({"key": key, "action": "applied"})
            result["items_processed"] += 1
        else:
            result["items_failed"] += 1
            result["actions"].append({"key": key, "action": "failed", "reason": item.get("reason")})
    return result


# ===== PHASE 3: RESTORE DECISION LOGIC (CONSERVATIVE, NOT HEROIC) =====

RESTORE_NO_RESTORE = "no_restore"
RESTORE_PARTIAL_RESTORE = "partial_restore"
RESTORE_BLOCKED = "restore_blocked"
RESTORE_SKIPPED_STALE = "restore_skipped_stale"


def load_latest_snapshot(base_dir: str = None, adapter: "OpenClawPaths" = None) -> Optional[Dict[str, Any]]:
    """Load the most recent snapshot.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    try:
        return load_snapshot("latest.json", base_dir, adapter)
    except Exception:
        return None


def get_snapshot_age_hours(snapshot: Dict[str, Any]) -> float:
    """Calculate snapshot age in hours."""
    try:
        timestamp = snapshot.get("timestamp", "")
        if not timestamp:
            return float("inf")
        snapshot_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(snapshot_time.tzinfo)
        delta = now - snapshot_time
        return delta.total_seconds() / 3600.0
    except Exception:
        return float("inf")


def should_attempt_restore(base_dir: str = None, adapter: "OpenClawPaths" = None) -> bool:
    """Check if restore should be attempted based on state_core.json validity.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    base_dir, _, _, _ = get_paths(base_dir, adapter)
    try:
        with open(os.path.join(base_dir, "state_core.json")) as f:
            state = json.load(f)
        if all(state.get(f) for f in ["identity_anchor", "status", "continuity"]):
            return False
        return True
    except Exception:
        return True


def check_restore_conditions(base_dir: str = None, adapter: "OpenClawPaths" = None) -> Dict[str, Any]:
    """Check restore conditions and return decision.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    if not should_attempt_restore(base_dir, adapter):
        return {"decision": RESTORE_NO_RESTORE, "reason": "state_core.json is valid"}
    snapshot = load_latest_snapshot(base_dir, adapter)
    if snapshot is None:
        return {"decision": RESTORE_NO_RESTORE, "reason": "no snapshot exists"}
    age_hours = get_snapshot_age_hours(snapshot)
    if age_hours > 24:
        return {"decision": RESTORE_SKIPPED_STALE, "reason": f"snapshot too old ({age_hours:.1f}h)", "age_hours": age_hours}
    markers = snapshot.get("continuity_markers", {})
    confidence = markers.get("confidence", 100.0)
    if confidence < 50:
        return {"decision": RESTORE_BLOCKED, "reason": f"low confidence ({confidence:.1f} < 50%)", "confidence": confidence, "age_hours": age_hours}
    debt = markers.get("debt", 0.0)
    if debt >= 50:
        return {"decision": RESTORE_BLOCKED, "reason": f"high debt ({debt:.1f} >= 50)", "confidence": confidence, "debt": debt, "age_hours": age_hours}
    return {"decision": RESTORE_PARTIAL_RESTORE, "reason": "snapshot validated", "confidence": confidence, "debt": debt, "age_hours": age_hours}


def apply_partial_restore(base_dir: str = None, adapter: "OpenClawPaths" = None) -> Dict[str, Any]:
    """Apply conservative partial restore from latest snapshot.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    result = {"status": "success", "fields_restored": [], "fields_skipped": [], "actions": []}
    snapshot = load_latest_snapshot(base_dir)
    if snapshot is None:
        result["status"] = "error"
        result["reason"] = "no snapshot available"
        return result
    decision_info = check_restore_conditions(base_dir)
    if decision_info["decision"] != RESTORE_PARTIAL_RESTORE:
        result["status"] = "skipped"
        result["reason"] = decision_info["reason"]
        return result
    base_dir, _, _, _ = get_paths(base_dir)
    state_core_path = os.path.join(base_dir, "state_core.json")
    communicator_self_path = os.path.join(base_dir, "communicator_self.json")
    try:
        with open(state_core_path) as f:
            state_core = json.load(f)
    except Exception:
        state_core = {"schema_version": "1.0.0", "timestamp": int(datetime.now().timestamp()), "identity_anchor": "", "status": "IDLE", "continuity": {}, "unresolved_shared_threads": [], "narrative_state": {}}
    try:
        with open(communicator_self_path) as f:
            comm_self = json.load(f)
    except Exception:
        comm_self = {}
    if "identity_anchor" in snapshot:
        state_core["identity_anchor"] = snapshot["identity_anchor"]
        result["fields_restored"].append("identity_anchor")
        result["actions"].append({"field": "identity_anchor", "action": "restored", "from": "snapshot"})
    if "continuity" in snapshot:
        if "continuity" not in state_core:
            state_core["continuity"] = {}
        state_core["continuity"]["session_count"] = snapshot["continuity"].get("session_count", 0)
        result["fields_restored"].append("continuity.session_count")
        result["actions"].append({"field": "continuity.session_count", "action": "restored", "from": "snapshot"})
    if "unresolved_shared_threads" in snapshot:
        state_core["unresolved_shared_threads"] = snapshot["unresolved_shared_threads"]
        result["fields_restored"].append("unresolved_shared_threads")
        result["actions"].append({"field": "unresolved_shared_threads", "action": "restored", "from": "snapshot"})
    if "narrative_state" in snapshot and snapshot["narrative_state"]:
        state_core["narrative_state"] = snapshot["narrative_state"]
        result["fields_restored"].append("narrative_state")
        result["actions"].append({"field": "narrative_state", "action": "restored", "from": "snapshot"})
    try:
        with open(state_core_path, "w") as f:
            json.dump(state_core, f, indent=2)
        result["state_core_saved"] = True
    except Exception as e:
        result["state_core_saved"] = False
        result["state_core_error"] = str(e)
    if "continuity" not in comm_self:
        comm_self["continuity"] = {}
    comm_self["continuity"]["session_count"] = snapshot.get("continuity", {}).get("session_count", 0)
    try:
        with open(communicator_self_path, "w") as f:
            json.dump(comm_self, f, indent=2)
        result["communicator_saved"] = True
    except Exception as e:
        result["communicator_saved"] = False
        result["communicator_error"] = str(e)
    return result


# ===== PHASE 5: OBSERVABILITY METRICS (INTERNAL ONLY) =====

def load_continuity_metrics(base_dir: str = None, adapter: "OpenClawPaths" = None) -> Dict[str, Any]:
    """Load continuity metrics from metrics.json.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    _, _, _, metrics_file = get_paths(base_dir, adapter)
    try:
        with open(metrics_file) as f:
            return json.load(f)
    except Exception:
        return {
            "snapshot_count": 0,
            "last_snapshot_at": None,
            "restore_attempts": 0,
            "restore_success_count": 0,
            "restore_skipped_count": 0,
            "restore_blocked_count": 0,
            "restore_error_count": 0,
            "latest_confidence": None,
            "latest_debt": None,
        }


def save_continuity_metrics(metrics: Dict[str, Any], base_dir: str = None, adapter: "OpenClawPaths" = None) -> None:
    """Save continuity metrics to metrics.json.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    _, continuity_dir, _, _ = get_paths(base_dir, adapter)
    os.makedirs(continuity_dir, exist_ok=True)
    with open(os.path.join(continuity_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)


def update_metrics_after_snapshot(confidence: float, debt: float, base_dir: str = None, adapter: "OpenClawPaths" = None) -> None:
    """Update metrics after a snapshot write.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    metrics = load_continuity_metrics(base_dir, adapter)
    metrics["snapshot_count"] = metrics.get("snapshot_count", 0) + 1
    metrics["last_snapshot_at"] = datetime.utcnow().isoformat() + "Z"
    metrics["latest_confidence"] = confidence
    metrics["latest_debt"] = debt
    save_continuity_metrics(metrics, base_dir, adapter)


def update_metrics_after_restore(result: Dict[str, Any], base_dir: str = None, adapter: "OpenClawPaths" = None) -> None:
    """Update metrics after a restore attempt.
    
    Accepts either base_dir or adapter parameter.
    Adapter takes precedence if both are provided.
    """
    metrics = load_continuity_metrics(base_dir, adapter)
    metrics["restore_attempts"] = metrics.get("restore_attempts", 0) + 1
    status = result.get("status", "error")
    if status == "success":
        metrics["restore_success_count"] = metrics.get("restore_success_count", 0) + 1
    elif status == "skipped":
        metrics["restore_skipped_count"] = metrics.get("restore_skipped_count", 0) + 1
    elif status == "blocked":
        metrics["restore_blocked_count"] = metrics.get("restore_blocked_count", 0) + 1
    else:
        metrics["restore_error_count"] = metrics.get("restore_error_count", 0) + 1
    save_continuity_metrics(metrics, base_dir, adapter)


# ===== v93a: SILENT ACTIVE WORK CAPSULE (ADDITIVE ONLY, NO BREAKING CHANGES) =====

def load_active_work_capsule(base_dir: str = None) -> Optional[Any]:
    """Load latest active work capsule (silently, v93a).
    
    Accepts base_dir parameter. Returns None if file missing or invalid.
    No external calls, no user-visible output.
    """
    from .capsule_recovery import CapsuleRebuilder
    return CapsuleRebuilder.load_capsule_file(base_dir)


def restore_from_capsule(base_dir: str = None, validate: bool = True) -> Dict[str, Any]:
    """Restore working context from capsule (silently, v93a, internal only).
    
    Accepts base_dir parameter. Returns dict with status and optionally
    reconstructed context. No breaking changes to existing continuity logic.
    v93c: Added validate parameter for boundary enforcement.
    v93d: Added freshness policy validation layer.
    """
    from .capsule_recovery import CapsuleRebuilder, CapsuleValidator
    from .capsule_policy import CapsuleFreshnessPolicy
    
    result = CapsuleRebuilder.rebuild_from_file(base_dir)
    
    if result.get("status") == "success" and validate:
        # Apply v93c validation boundary
        context = result.get("context", {})
        validation = CapsuleValidator.validate_restored_context(context)
        if validation["status"] != "valid":
            return {
                "status": "blocked",
                "reason": validation["status"],
                "validation": validation
            }
        
        # Apply v93d freshness policy validation
        freshness = CapsuleFreshnessPolicy.validate_freshness(context)
        if freshness.status != "fresh":
            return {
                "status": "blocked",
                "reason": freshness.status,
                "validation": validation,
                "freshness": freshness.to_dict()
            }
        
        result["context"] = context
    
    return result


# ===== v93e: Silent Resume Trigger (Capsule Invocation Boundary) =====

def resume_from_capsule(base_dir: str = None) -> Dict[str, Any]:
    """Load and validate capsule, returning decision for silent invocation.
    
    v93e: Capsule Invocation Boundary / Silent Resume Trigger.
    
    Internal helper only - no automatic invocation, no startup/session wiring.
    Returns explicit structured decision:
    - "apply"    — capsule is fresh and valid, ready for silent resume
    - "ignore"   — no capsule file exists, nothing to resume
    - "stale"    — capsule exists but exceeds 24h age threshold
    - "invalid"  — capsule structure/content is malformed
    
    Silent/internal only, no user-visible behavior, no /new semantic changes.
    
    Args:
        base_dir: Base directory containing continuity/active_work_capsule.json
        
    Returns:
        Dict with keys:
        - status: "apply" | "ignore" | "stale" | "invalid"
        - reason: Human-readable explanation for decision
        - context: (optional) Reconstructed context if status="apply"
    """
    from .capsule_recovery import CapsuleRebuilder
    from .capsule_policy import CapsuleFreshnessPolicy
    
    # Load capsule from file
    capsule = CapsuleRebuilder.load_capsule_file(base_dir)
    
    if capsule is None:
        return {"status": "ignore", "reason": "no_capsule_file"}
    
    # Build minimal context from capsule
    context = CapsuleRebuilder.rebuild_from_capsule(capsule)
    
    # Validate via v93d freshness policy
    freshness = CapsuleFreshnessPolicy.validate_freshness(context)
    
    if freshness.status == "fresh":
        return {
            "status": "apply",
            "reason": "capsule_fresh_and_valid",
            "context": context
        }
    
    return {
        "status": "stale" if freshness.status == "stale" else "invalid",
        "reason": freshness.reason,
        "freshness": freshness.to_dict()
    }
