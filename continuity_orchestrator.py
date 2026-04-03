"""Silent Continuity Orchestrator v1 Phase 1 — WESLR anchored.

Foundation: snapshot load/write, confidence/debt calculation, restore plan builder.
Tied explicitly to WESLR continuity architecture:
- identity_anchor, communicator_self, state_core
- unresolved_shared_threads, opportunity_board, categories, review_queue, export_queue
- session_continuity state (session_count, threads_continued, etc.)
- operator_work continuity (work_items.json)
No automatic restore yet. No user-facing flows.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

# Official WESLR continuity directories
BASE_DIR = "/data/data/com.termux/files/home/.openclaw/workspace"
CONTINUITY_DIR = os.path.join(BASE_DIR, "continuity")
SNAPSHOT_DIR = os.path.join(CONTINUITY_DIR, "snapshots")


# ===== WESLRContinuityState — the actual state we snapshot =====

def load_weslr_continuity_state() -> Dict[str, Any]:
    """Load the real WESLR continuity state from source files."""
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
        with open(os.path.join(BASE_DIR, "state_core.json")) as f:
            core = json.load(f)
            state["identity_anchor"] = core.get("identity_anchor")
            state["communicator_continuity"]["status"] = core.get("status")
            state["communicator_continuity"]["session_count"] = core.get("continuity", {}).get("session_count", 0)
            state["unresolved_shared_threads"] = core.get("unresolved_shared_threads", [])
    except Exception:
        pass

    # Load communicator_self continuity signals
    try:
        with open(os.path.join(BASE_DIR, "communicator_self.json")) as f:
            comm = json.load(f)
            state["communicator_continuity"]["confidence_score"] = comm.get("continuity", {}).get("confidence_score", 0.0)
            state["communicator_continuity"]["known_humans"] = comm.get("relationships", {}).get("known_humans", [])
            state["communicator_continuity"]["active_threads"] = list(comm.get("memory_layers", {}).get("working", {}).get("active_concern_topics", []))
    except Exception:
        pass

    # Load session_continuity state
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
        with open(os.path.join(BASE_DIR, "opportunity_board.json")) as f:
            state["opportunity_board"] = json.load(f)
    except Exception:
        pass

    # Load categories (category_proposals.json)
    try:
        with open(os.path.join(BASE_DIR, "category_proposals.json")) as f:
            state["categories"] = json.load(f)
    except Exception:
        pass

    # Load review_queue
    try:
        with open(os.path.join(BASE_DIR, "review_queue.json")) as f:
            state["review_queue"] = json.load(f)
    except Exception:
        pass

    # Load export_queue
    try:
        with open(os.path.join(BASE_DIR, "export_queue.json")) as f:
            state["export_queue"] = json.load(f)
    except Exception:
        pass

    # Load operator/work continuity (work_items.json)
    try:
        with open(os.path.join(BASE_DIR, "work_items.json")) as f:
            state["operator_work"] = json.load(f)
    except Exception:
        pass

    return state


# ===== SNAPSHOT STRUCTURE (WESLR fields) =====

def build_snapshot(session_id: str, state: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build snapshot from real WESLR continuity state."""
    state = state or load_weslr_continuity_state()

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


def save_snapshot(snapshot: Dict[str, Any], overwrite: bool = False) -> str:
    """Save snapshot to continuity/snapshots/."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    ts = snapshot["timestamp"].replace(":", "-").replace(".", "-")
    filename = f"snapshot_{ts}_{snapshot['session_id'][:8]}.json"
    path = os.path.join(SNAPSHOT_DIR, filename)

    if not overwrite and os.path.exists(path):
        raise FileExistsError(f"Snapshot exists: {path}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    return filename


def load_snapshot(filename: str) -> Dict[str, Any]:
    """Load snapshot from continuity/snapshots/."""
    path = os.path.join(SNAPSHOT_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_snapshots() -> List[str]:
    """List snapshot filenames in continuity/snapshots/."""
    if not os.path.exists(SNAPSHOT_DIR):
        return []
    return sorted([f for f in os.listdir(SNAPSHOT_DIR) if f.startswith("snapshot_")])


# ===== CONFIDENCE / DEBT (WESLR continuity model) =====

def calculate_confidence(state: Dict[str, Any]) -> float:
    """Calculate confidence based on WESLR continuity signals."""
    base = 100.0

    # Positive signals (add confidence)
    comm = state.get("communicator_continuity", {})
    if comm.get("confidence_score", 0) >= 0.7:
        base += 5
    if len(comm.get("known_humans", [])) > 0:
        base += 3
    if len(comm.get("active_threads", [])) > 0:
        base += 5

    # Session continuity
    sess = state.get("session_continuity", {})
    if sess.get("session_count", 0) >= 5:
        base += 5
    if len(sess.get("active_threads_from_prev", [])) > 0:
        base += 5

    # Identity anchor present
    if state.get("identity_anchor"):
        base += 5

    # Penalties
    if len(state.get("unresolved_shared_threads", [])) > 2:
        base -= 10
    if len(state.get("review_queue", [])) > 0:
        base -= 5

    return max(0.0, min(100.0, round(base, 1)))


def calculate_continuity_debt(state: Dict[str, Any]) -> float:
    """Calculate continuity debt — unresolved threads, pending reviews, missing anchors."""
    debt = 0.0

    # Unresolved shared threads (high weight)
    unresolved = state.get("unresolved_shared_threads", [])
    debt += 10 * len(unresolved)

    # Pending reviews
    review_queue = state.get("review_queue", [])
    debt += 5 * len(review_queue)

    # Export queue items not yet exported
    export_queue = state.get("export_queue", [])
    debt += 3 * len(export_queue)

    # No identity anchor
    if not state.get("identity_anchor"):
        debt += 20

    # Low communicator confidence
    comm = state.get("communicator_continuity", {})
    if comm.get("confidence_score", 1.0) < 0.5:
        debt += 15

    return min(100.0, round(debt, 1))


# ===== RESTORE PLAN BUILDER (WESLR fields) =====

def build_restore_plan(state: Dict[str, Any]) -> Dict[str, Any]:
    """Build restore plan targeting WESLR continuity fields."""
    plan: Dict[str, Any] = {
        "strategy": "continuity_preservation",
        "items": [],
        "fallback": "state_core_restore",
        "continuity_fields": [
            "identity_anchor",
            "communicator_continuity",
            "session_continuity",
            "unresolved_shared_threads",
            "opportunity_board",
            "categories",
            "review_queue",
            "export_queue",
            "operator_work",
        ],
    }

    # Identify restoration items by field type
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

def get_current_snapshot_info() -> Optional[Dict[str, Any]]:
    """Get info about the most recent snapshot."""
    snapshots = list_snapshots()
    if not snapshots:
        return None
    # Return latest snapshot or None if none exist
    try:
        return load_snapshot(snapshots[-1])
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
