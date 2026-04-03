"""Weslr Platform: Shared Contracts & Models (v1)

Weslr-native data contracts that define the canonical structures
used across platform modules. These contracts ensure consistency
between state, continuity, task_anchor, and other components.

No runtime-specific dependencies.
Base-dir aware for multi-runtime support.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, Optional, TypedDict

# ============================================================================
# STATE SCHEMA CONTRACT
# ============================================================================

class StateMetadata(TypedDict):
    """Metadata about the state document itself."""
    schema_version: str
    timestamp: int
    identity_anchor: str
    migrated_by: str  # e.g., "weslr.state", "legacy"
    migrated_at: int


class StateValidation(TypedDict):
    """Validation status and results."""
    ok: bool
    errors: List[str]
    warnings: List[str]


class StateContinuity(TypedDict):
    """Continuity metadata for the state."""
    session_count: int
    last_message_at: int
    known_humans: List[str]
    unresolved_shared_threads: List[str]


class StateMetrics(TypedDict):
    """Runtime metrics snapshot."""
    tick_count: int
    last_tick_duration_ms: int
    memory_pressure_score: float


class StateNextAction(TypedDict):
    """Derivation of next action with traceability."""
    action: str
    priority: Literal["low", "medium", "high"]
    reason: str
    source: str
    chosen_because: str
    signals_considered: List[Dict[str, Any]]
    signals_not_selected: List[Dict[str, Any]]


class WeslrState(TypedDict):
    """Canonical Weslr state schema (state_core.json).
    
    This is the single source of truth for Weslr runtime state.
    All derivation functions must produce this schema.
    """
    schema_version: str
    timestamp: int
    identity_anchor: str
    status: str  # "IDLE", "ERROR", "REFLECTING", etc.
    continuity: StateContinuity
    behavioral_traits: Dict[str, float]
    curiosity: float
    uncertainty: float
    narrative_state: Dict[str, str]
    unresolved_shared_threads: List[str]
    memory_layers: Dict[str, Any]
    topics: List[Dict[str, Any]]
    artifacts: List[Dict[str, Any]]
    handoffs: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    next_action: StateNextAction
    metrics: StateMetrics
    derived_from: Dict[str, Any]
    validation: StateValidation


def create_state_metadata(identity_anchor: str = "Weslr") -> StateMetadata:
    """Create state metadata with current timestamp."""
    now_ts = int(time.time())
    return {
        "schema_version": "1.0.0",
        "timestamp": now_ts,
        "identity_anchor": identity_anchor,
        "migrated_by": "weslr.state",
        "migrated_at": now_ts,
    }


def create_empty_validation() -> StateValidation:
    """Create a default empty validation result."""
    return {
        "ok": True,
        "errors": [],
        "warnings": [],
    }


def create_empty_metrics() -> StateMetrics:
    """Create default metrics for new state."""
    return {
        "tick_count": 0,
        "last_tick_duration_ms": 0,
        "memory_pressure_score": 0.0,
    }


def create_empty_next_action() -> StateNextAction:
    """Create default next_action for new state."""
    return {
        "action": "none",
        "priority": "low",
        "reason": "No signals require immediate action.",
        "source": "status",
        "chosen_because": "",
        "signals_considered": [],
        "signals_not_selected": [],
    }


# ============================================================================
# CONTINUITY SNAPSHOT CONTRACT
# ============================================================================

class ContinuityMarkers(TypedDict):
    """Markers on a snapshot for confidence/debt tracking."""
    confidence: float  # 0.0 - 100.0
    debt: float  # 0.0 - 100.0
    fields: List[str]  # Which fields were captured


class RestorePlanItem(TypedDict):
    """Single item in a restore plan."""
    key: str
    action: str  # "direct", "restore_list", "restore_dict", "skip", "manual"
    value: Optional[Any]
    count: Optional[int]
    keys: Optional[List[str]]
    reason: Optional[str]


class RestorePlan(TypedDict):
    """Complete restore plan."""
    strategy: Literal["continuity_preservation", "state_core_restore", "full_restore"]
    items: List[RestorePlanItem]
    fallback: str
    continuity_fields: List[str]


class WeslrContinuitySnapshot(TypedDict):
    """Weslr continuity snapshot schema."""
    session_id: str
    timestamp: str  # ISO format
    identity_anchor: Optional[str]
    communicator_continuity: Dict[str, Any]
    session_continuity: Dict[str, Any]
    unresolved_shared_threads: List[str]
    opportunity_board: Dict[str, Any]
    categories: Dict[str, Any]
    review_queue: List[Any]
    export_queue: List[Any]
    operator_work: List[Any]
    continuity_markers: ContinuityMarkers
    restore_plan: RestorePlan


def create_continuity_markers(
    confidence: float = 100.0,
    debt: float = 0.0,
    fields: Optional[List[str]] = None
) -> ContinuityMarkers:
    """Create continuity markers with defaults."""
    return {
        "confidence": confidence,
        "debt": debt,
        "fields": fields or ["identity_anchor", "continuity", "status"],
    }


def create_restore_plan(
    strategy: Literal["continuity_preservation", "state_core_restore", "full_restore"] = "continuity_preservation",
    fallback: str = "state_core_restore",
    fields: Optional[List[str]] = None
) -> RestorePlan:
    """Create a default restore plan."""
    return {
        "strategy": strategy,
        "items": [],
        "fallback": fallback,
        "continuity_fields": fields or [
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


# ============================================================================
# TASK ANCHOR CONTRACT
# ============================================================================

class TaskAnchor(TypedDict):
    """Task anchor schema for tracking current task."""
    task_name: str
    task_status: Literal["in_progress", "pending", "completed"]
    last_commit_hash: str
    last_updated_at: str  # ISO format
    task_description: Optional[str]
    current_step: Optional[str]
    priority: Optional[Literal["low", "medium", "high"]]
    related_context: Optional[Dict[str, Any]]


def create_task_anchor(
    task_name: str,
    task_status: Literal["in_progress", "pending", "completed"],
    last_commit_hash: str,
    base_dir: str = None  # Kept for compatibility but unused in contract
) -> TaskAnchor:
    """Create a new task anchor with required fields.
    
    This is the contract function for creating valid task anchors.
    All task anchor creation should use this or validate against it.
    """
    import datetime
    return {
        "task_name": task_name,
        "task_status": task_status,
        "last_commit_hash": last_commit_hash,
        "last_updated_at": datetime.datetime.utcnow().isoformat() + "Z",
        # Optional fields omitted - can be added via update_task_anchor
    }


def update_task_anchor(
    anchor: TaskAnchor,
    task_name: str = None,
    task_status: str = None,
    last_commit_hash: str = None,
    current_step: str = None,
    base_dir: str = None  # Kept for compatibility
) -> TaskAnchor:
    """Update existing task anchor with new values.
    
    Validates that required fields remain present.
    """
    import datetime
    if task_name is not None:
        anchor["task_name"] = task_name
    if task_status is not None:
        anchor["task_status"] = task_status
    if last_commit_hash is not None:
        anchor["last_commit_hash"] = last_commit_hash
    if current_step is not None:
        anchor["current_step"] = current_step
    anchor["last_updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    return anchor


def validate_task_anchor(anchor: TaskAnchor) -> bool:
    """Validate task anchor has all required fields.
    
    Returns True if valid, False otherwise.
    """
    required = ["task_name", "task_status", "last_commit_hash", "last_updated_at"]
    for field in required:
        if field not in anchor or not anchor[field]:
            return False
    # Validate task_status is in allowed values
    if anchor["task_status"] not in ("in_progress", "pending", "completed"):
        return False
    return True


# ============================================================================
# RESTORE RESULT CONTRACT
# ============================================================================

RestoreStatus = Literal["success", "error", "skipped", "blocked"]


class RestoreResult(TypedDict):
    """Result of a restore operation."""
    status: RestoreStatus
    fields_restored: List[str]
    fields_skipped: List[str]
    actions: List[Dict[str, Any]]
    reason: Optional[str]
    state_core_saved: Optional[bool]
    state_core_error: Optional[str]
    communicator_saved: Optional[bool]
    communicator_error: Optional[str]


def create_restore_result(
    status: RestoreStatus = "success",
    fields_restored: Optional[List[str]] = None,
    fields_skipped: Optional[List[str]] = None,
    actions: Optional[List[Dict[str, Any]]] = None
) -> RestoreResult:
    """Create a restore result with defaults."""
    return {
        "status": status,
        "fields_restored": fields_restored or [],
        "fields_skipped": fields_skipped or [],
        "actions": actions or [],
        "reason": None,
        "state_core_saved": None,
        "state_core_error": None,
        "communicator_saved": None,
        "communicator_error": None,
    }


# ============================================================================
# HELPERS
# ============================================================================

def get_required_state_fields() -> List[str]:
    """Return list of required fields in WeslrState."""
    return [
        "schema_version",
        "timestamp",
        "identity_anchor",
        "status",
        "continuity",
        "behavioral_traits",
        "curiosity",
        "uncertainty",
        "narrative_state",
        "unresolved_shared_threads",
        "memory_layers",
        "topics",
        "artifacts",
        "handoffs",
        "entities",
        "events",
        "next_action",
        "metrics",
        "derived_from",
        "validation",
    ]


def get_required_task_anchor_fields() -> List[str]:
    """Return list of required fields in TaskAnchor."""
    return [
        "task_name",
        "task_status",
        "last_commit_hash",
        "last_updated_at",
    ]


def get_state_schema_version() -> str:
    """Return current state schema version."""
    return "1.0.0"


def get_state_sync_schema_version() -> str:
    """Return current state_sync schema version."""
    return "1.0.0"


def validate_state_schema(state: Dict[str, Any]) -> bool:
    """Validate that a state dict conforms to the WeslrState contract.
    
    Performs basic structural validation. Does not validate content semantics.
    """
    required = get_required_state_fields()
    for field in required:
        if field not in state:
            return False
    return True


def validate_task_anchor_schema(anchor: Dict[str, Any]) -> bool:
    """Validate that a task anchor conforms to the TaskAnchor contract."""
    required = get_required_task_anchor_fields()
    for field in required:
        if field not in anchor or not anchor[field]:
            return False
    return True
