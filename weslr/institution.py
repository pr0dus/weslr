# weslr/institution.py — Layer 2 Role Timeline Foundation
# Minimum safe foundation: role timeline schema, lifecycle helpers, Layer 2 governance boundaries.
#
# DO NOT yet build full vacancy replacement flows, handover synthesis, or Layer 3.
# DO NOT yet build governor UI or institution registry.
# This module provides the Layer 2 foundation; Layer 3 and governance protocol are separate slices.

from __future__ import annotations

import time
from typing import Any


# =============================================================================
# LAYER 2 — ROLE TIMELINE
# =============================================================================
# Layer 2 is the role timeline layer. Each role in the institution has exactly
# one Role Timeline. A Role Timeline is owned by the institution, not by any
# individual human. It is permanent and survives occupant changes.
#
# Governance rules (Layer 2):
# - institution_id is the parent — role timelines belong to an institution
# - current occupant is a Layer 1 timeline_id reference (may be None if vacant)
# - role owner is a human authorized to manage the role (Layer 1 timeline_id)
# - role clearance level is the minimum SS-TDE trust level for actions from this role
# - deny-by-default: humans can only interact with a role timeline if authorized
#
# NOT YET implemented (Layer 3 territory):
# - delegation chains (Layer 3 governance action)
# - institutional policy (Layer 3)
# - vacancy replacement workflow
# - handover synthesis
# =============================================================================


# =============================================================================
# ROLE TIMELINE STATUS
# =============================================================================

class RoleStatus:
    ACTIVE = "active"       # Role has a current occupant
    VACANT = "vacant"       # Role has no occupant
    ARCHIVED = "archived"  # Role is no longer active but preserved in audit record


# =============================================================================
# ROLE TIMELINE SCHEMA FACTORY
# =============================================================================

def new_role_timeline(
    role_id: str,
    institution_id: str,
    role_name: str,
    role_description: str = "",
    role_scope: str = "",
    role_owner_id: str | None = None,
    role_clearance_level: int = 1,
) -> dict:
    """Create a new Layer 2 Role Timeline record.

    This is the foundation for all institutional role continuity. A Role Timeline
    is created when a new role is established in the institution. It is permanent
    and survives occupant changes — vacancy does not delete the record.

    Args:
        role_id: Unique identifier for this role (e.g. "role-engineering-lead")
        institution_id: The institution this role belongs to
        role_name: Human-readable role name (e.g. "Engineering Lead")
        role_description: Short description of the role's purpose
        role_scope: Description of the role's authority and scope
        role_owner_id: Layer 1 timeline_id of the human who can manage this role
        role_clearance_level: Minimum SS-TDE trust level for this role (default 1=L1 Sensitive)

    Returns:
        A role timeline record dict.
    """
    now = time.time()
    return {
        # Core identity
        "role_id": role_id,
        "institution_id": institution_id,
        "role_name": role_name,
        "role_description": role_description,
        "role_scope": role_scope,
        # Lifecycle
        "status": RoleStatus.ACTIVE,
        "created_at": now,
        "archived_at": None,
        # Occupancy (Layer 1 reference)
        "current_occupant_id": None,  # Layer 1 timeline_id — set when assigned
        "current_occupant_assigned_at": None,
        "occupant_history": [],  # list of {timeline_id, started_at, ended_at, reason}
        # Access control
        "role_owner_id": role_owner_id,  # Layer 1 timeline_id of role manager
        "role_clearance_level": role_clearance_level,  # SS-TDE minimum for this role
        # Delegation hooks (Layer 3 territory — placeholder for now)
        "delegated_principals": [],  # list of Layer 1 timeline_ids with delegated access
        # Audit metadata
        "last_updated_at": now,
        "last_vacancy_at": None,
        "vacancy_count": 0,
    }


def archive_role_timeline(role_record: dict) -> dict:
    """Archive a role timeline — mark it as no longer active.

    Args:
        role_record: The role timeline record to archive

    Returns:
        The archived role timeline record.
    """
    record = dict(role_record)
    now = time.time()
    record["status"] = RoleStatus.ARCHIVED
    record["archived_at"] = now
    record["current_occupant_id"] = None
    record["current_occupant_assigned_at"] = None
    record["last_updated_at"] = now
    return record


# =============================================================================
# ROLE TIMELINE LIFECYCLE HELPERS
# =============================================================================

def assign_occupant(
    role_record: dict,
    occupant_timeline_id: str,
    assigned_by: str | None = None,
) -> dict:
    """Assign a human (Layer 1 timeline) as the current occupant of this role.

    If the role was vacant, this is a new assignment.
    If the role was occupied, the previous occupant is moved to history before
    the new occupant is assigned.

    Args:
        role_record: The current role timeline record
        occupant_timeline_id: The Layer 1 timeline_id of the human to assign
        assigned_by: Layer 1 timeline_id of who authorized this assignment (optional)

    Returns:
        The updated role timeline record with the new occupant set.
    """
    record = dict(role_record)
    now = time.time()
    now_ts = now  # Alias for clarity in occupant history entries

    # Archive previous occupant to history if reassigning
    prev_occupant = record.get("current_occupant_id")
    if prev_occupant and prev_occupant != occupant_timeline_id:
        history_entry = {
            "timeline_id": prev_occupant,
            "started_at": record.get("current_occupant_assigned_at", now),
            "ended_at": now,
            "reason": "reassigned",
            "ended_by": assigned_by,
        }
        record["occupant_history"] = record.get("occupant_history", []) + [history_entry]

    record["current_occupant_id"] = occupant_timeline_id
    record["current_occupant_assigned_at"] = now
    record["status"] = RoleStatus.ACTIVE
    record["last_updated_at"] = now
    return record


def vacate_role(
    role_record: dict,
    reason: str = "manual_vacancy",
    vacated_by: str | None = None,
) -> dict:
    """Vacate a role — remove the current occupant and mark the role as vacant.

    The previous occupant is moved to occupant history before the role is vacated.

    Args:
        role_record: The current role timeline record
        reason: Why the role is being vacated (e.g. "human_departed", "transfer", "manual_vacancy")
        vacated_by: Layer 1 timeline_id of who initiated the vacancy (optional)

    Returns:
        The updated role timeline record marked as vacant.
    """
    record = dict(role_record)
    now = time.time()

    prev_occupant = record.get("current_occupant_id")
    if prev_occupant:
        history_entry = {
            "timeline_id": prev_occupant,
            "started_at": record.get("current_occupant_assigned_at", now),
            "ended_at": now,
            "reason": reason,
            "ended_by": vacated_by,
        }
        record["occupant_history"] = record.get("occupant_history", []) + [history_entry]

    record["current_occupant_id"] = None
    record["current_occupant_assigned_at"] = None
    record["status"] = RoleStatus.VACANT
    record["last_updated_at"] = now
    record["last_vacancy_at"] = now
    record["vacancy_count"] = record.get("vacancy_count", 0) + 1
    return record


def get_role_status(role_record: dict) -> dict:
    """Return a human-readable status summary for a role timeline.

    Args:
        role_record: A role timeline record dict

    Returns:
        A status dict with keys: role_id, role_name, status, current_occupant_id,
        is_vacant, vacancy_count, days_since_vacancy, days_occupied.
    """
    now = time.time()
    record = role_record
    status = record.get("status", RoleStatus.VACANT)
    is_vacant = status == RoleStatus.VACANT
    last_vacancy = record.get("last_vacancy_at")

    result = {
        "role_id": record.get("role_id", ""),
        "role_name": record.get("role_name", ""),
        "status": status,
        "current_occupant_id": record.get("current_occupant_id"),
        "is_vacant": is_vacant,
        "vacancy_count": record.get("vacancy_count", 0),
        "institution_id": record.get("institution_id", ""),
        "role_clearance_level": record.get("role_clearance_level", 1),
        "role_owner_id": record.get("role_owner_id"),
    }

    if last_vacancy and is_vacant:
        result["days_since_vacancy"] = (now - last_vacancy) / 86400

    current_occ = record.get("current_occupant_id")
    if current_occ:
        assigned_at = record.get("current_occupant_assigned_at")
        if assigned_at:
            result["days_occupied"] = (now - assigned_at) / 86400

    return result


def is_authorized_for_role(
    role_record: dict,
    timeline_id: str,
    action: str = "read",
) -> bool:
    """Check if a Layer 1 timeline is authorized to perform an action on a role.

    Authorization rules (deny-by-default):
    - "read": role owner OR current occupant OR institution admin
    - "write": role owner OR institution admin
    - "vacate": role owner OR institution admin
    - "assign": role owner OR institution admin

    Institution admin is determined by checking if the timeline_id has
    a governor role in the institution (Layer 3 check — delegated to caller).

    Args:
        role_record: The role timeline record
        timeline_id: The Layer 1 timeline_id to check
        action: One of "read", "write", "vacate", "assign"

    Returns:
        True if authorized, False otherwise.
    """
    record = role_record
    role_owner = record.get("role_owner_id")
    current_occupant = record.get("current_occupant_id")

    # Role owner always has access
    if timeline_id == role_owner:
        return True

    # Current occupant has read access
    if timeline_id == current_occupant and action == "read":
        return True

    # Institution admin check via Layer 3 registry (same module — no circular risk)
    is_admin = is_institution_admin(timeline_id, record.get("institution_id", ""))
    if is_admin:
        return True

    return False


def add_delegated_principal(
    role_record: dict,
    delegate_timeline_id: str,
    ttl_seconds: int = 3600,
    scope: str = "read",
) -> dict:
    """Add a delegated principal to a role timeline (Scoped access grant).

    This is a Layer 2 delegation stub — it grants a human (Layer 1) scoped
    access to this role timeline for a bounded time. Full delegation requires
    Layer 3 governance protocol. This function is for role-owner-level grants.

    Args:
        role_record: The role timeline record
        delegate_timeline_id: Layer 1 timeline_id to grant access to
        ttl_seconds: Time-to-live for this delegation (default 1 hour)
        scope: Access scope — "read" or "read_write"

    Returns:
        The updated role timeline record with the new delegated principal.
    """
    now = time.time()
    record = dict(role_record)

    existing = record.get("delegated_principals", [])
    # Remove any prior delegation for this same delegate
    filtered = [d for d in existing if d.get("timeline_id") != delegate_timeline_id]

    new_delegation = {
        "timeline_id": delegate_timeline_id,
        "granted_at": now,
        "expires_at": now + ttl_seconds,
        "scope": scope,
    }
    filtered.append(new_delegation)
    record["delegated_principals"] = filtered
    record["last_updated_at"] = now
    return record


def revoke_delegated_principal(
    role_record: dict,
    delegate_timeline_id: str,
) -> dict:
    """Revoke a delegated principal's access from a role timeline.

    Args:
        role_record: The role timeline record
        delegate_timeline_id: Layer 1 timeline_id of the delegation to revoke

    Returns:
        The updated role timeline record with the delegation removed.
    """
    record = dict(role_record)
    now = time.time()
    record["delegated_principals"] = [
        d for d in record.get("delegated_principals", [])
        if d.get("timeline_id") != delegate_timeline_id
    ]
    record["last_updated_at"] = now
    return record


def get_active_delegations(role_record: dict) -> list[dict]:
    """Return all currently valid (non-expired) delegations for a role timeline.

    Args:
        role_record: A role timeline record dict

    Returns:
        List of active delegation dicts (those whose expires_at > now).
    """
    now = time.time()
    all_delegations = role_record.get("delegated_principals", [])
    return [
        d for d in all_delegations
        if d.get("expires_at", 0) > now
    ]


# =============================================================================
# IN-PROCESS ROLE TIMELINE STORE (stub — replace with DB in production)
# =============================================================================
# Role timelines are held in memory. In production, replace with a persistent store.
_ROLE_TIMELINES: dict[str, dict] = {}  # role_id -> role timeline record
_INSTITUTION_ROLES: dict[str, set[str]] = {}  # institution_id -> set of role_ids


def store_role_timeline(role_record: dict) -> None:
    """Store a role timeline record and auto-link it to the institution registry.

    This function bridges Layer 2 and Layer 3: after storing the role timeline
    locally, it also links the role to the institution's registry record so that
    list_institution_roles and governance checks stay in sync.
    """
    role_id = role_record.get("role_id")
    _ROLE_TIMELINES[role_id] = role_record
    institution_id = role_record.get("institution_id", "")
    if institution_id:
        _INSTITUTION_ROLES.setdefault(institution_id, set()).add(role_id)
        # Bridge to Layer 3: keep institution registry role list in sync
        inst = _INSTITUTIONS.get(institution_id)
        if inst and role_id not in inst.get("role_timeline_ids", []):
            updated = link_role_to_institution(inst, role_id)
            _INSTITUTIONS[institution_id] = updated


def get_role_timeline(role_id: str) -> dict | None:
    """Retrieve a role timeline by role_id (in-process)."""
    return _ROLE_TIMELINES.get(role_id)


def list_institution_roles(institution_id: str) -> list[dict]:
    """List all role timelines for an institution (in-process)."""
    role_ids = _INSTITUTION_ROLES.get(institution_id, set())
    return [_ROLE_TIMELINES.get(rid) for rid in role_ids if _ROLE_TIMELINES.get(rid)]


def list_vacant_roles(institution_id: str | None = None) -> list[dict]:
    """List all vacant role timelines, optionally filtered by institution."""
    all_roles = []
    if institution_id:
        all_roles = list_institution_roles(institution_id)
    else:
        all_roles = list(_ROLE_TIMELINES.values())

    return [
        r for r in all_roles
        if r and r.get("status") == RoleStatus.VACANT
    ]


# =============================================================================
# LAYER 3 — INSTITUTION REGISTRY
# =============================================================================
# Layer 3 is the institution timeline layer. The institution is the top-level
# container for all role timelines and roster members. It provides institutional
# identity, governor bindings, and cross-role governance metadata.
#
# Governance rules (Layer 3):
# - institution_id is the top-level identifier
# - governors are Layer 1 timeline_ids with administrative authority over the institution
# - roster members are Layer 1 timeline_ids affiliated with the institution
# - role timelines belong to the institution (Layer 2 ownership)
# - deny-by-default: only governors can perform institutional administrative actions
#
# NOT YET implemented:
# - delegated access workflows (Layer 3 extended)
# - vacancy replacement workflow orchestration
# - institutional policy storage and enforcement
# - handover synthesis
# =============================================================================


# =============================================================================
# INSTITUTION STATUS
# =============================================================================

class InstitutionStatus:
    ACTIVE = "active"      # Institution is operating normally
    INACTIVE = "inactive" # Institution is dormant but preserved
    ARCHIVED = "archived" # Institution is archived (no new roles/roster changes)


# =============================================================================
# INSTITUTION REGISTRY SCHEMA FACTORY
# =============================================================================

def new_institution(
    institution_id: str,
    institution_name: str,
    institution_metadata: dict | None = None,
    founding_governor_id: str | None = None,
) -> dict:
    """Create a new Layer 3 Institution Registry record.

    This is the top-level record for the institution. All role timelines (Layer 2)
    and roster members belong to an institution. The institution is permanent —
    it survives role vacancies and roster changes.

    Args:
        institution_id: Unique identifier for this institution
        institution_name: Human-readable institution name
        institution_metadata: Arbitrary key-value metadata dict (optional)
        founding_governor_id: Layer 1 timeline_id of the founding governor (optional)

    Returns:
        An institution registry record dict.
    """
    now = time.time()
    record = {
        # Core identity
        "institution_id": institution_id,
        "institution_name": institution_name,
        "institution_metadata": dict(institution_metadata or {}),
        # Lifecycle
        "status": InstitutionStatus.ACTIVE,
        "created_at": now,
        "archived_at": None,
        # Governance — governors are Layer 1 timeline_ids with admin authority
        "governors": [],  # list of Layer 1 timeline_ids
        "governor_history": [],  # list of {timeline_id, added_at, removed_at, reason}
        # Cross-layer references
        "role_timeline_ids": [],  # list of role_ids belonging to this institution
        "roster": [],  # list of Layer 1 timeline_ids affiliated with this institution
        # Audit metadata
        "last_updated_at": now,
        "last_governor_change_at": None,
    }

    # Automatically bind founding governor if provided
    if founding_governor_id:
        record = bind_governor(record, founding_governor_id, reason="founding")
    else:
        # Store even without a founding governor so is_institution_admin can resolve
        store_institution(record)

    return record


# =============================================================================
# INSTITUTION LIFECYCLE HELPERS
# =============================================================================

def get_institution_status(institution_record: dict) -> dict:
    """Return a human-readable status summary for an institution.

    Args:
        institution_record: An institution registry record dict

    Returns:
        A status dict with keys: institution_id, institution_name, status,
        governor_count, role_count, roster_size, is_active.
    """
    record = institution_record
    return {
        "institution_id": record.get("institution_id", ""),
        "institution_name": record.get("institution_name", ""),
        "status": record.get("status", InstitutionStatus.INACTIVE),
        "is_active": record.get("status") == InstitutionStatus.ACTIVE,
        "governor_count": len(record.get("governors", [])),
        "role_timeline_count": len(record.get("role_timeline_ids", [])),
        "roster_size": len(record.get("roster", [])),
        "institution_metadata": record.get("institution_metadata", {}),
    }


def archive_institution(institution_record: dict) -> dict:
    """Archive an institution — mark it as no longer active.

    Args:
        institution_record: The institution registry record to archive

    Returns:
        The archived institution record.
    """
    record = dict(institution_record)
    now = time.time()
    record["status"] = InstitutionStatus.ARCHIVED
    record["archived_at"] = now
    record["last_updated_at"] = now
    return record


# =============================================================================
# GOVERNOR BINDINGS
# =============================================================================

def bind_governor(
    institution_record: dict,
    governor_timeline_id: str,
    bound_by: str | None = None,
    reason: str = "added",
) -> dict:
    """Bind a Layer 1 human timeline as a governor of the institution.

    Governors have administrative authority over the institution and all its
    role timelines. Binding a governor appends them to the governors list
    and records the action in governor history. This function auto-stores
    the institution record so that is_institution_admin can immediately resolve
    the governor check.

    Args:
        institution_record: The institution registry record
        governor_timeline_id: Layer 1 timeline_id to grant governor authority
        bound_by: Layer 1 timeline_id of who authorized this binding (optional)
        reason: Why the governor is being added (e.g. "founding", "promoted", "delegated")

    Returns:
        The updated institution record with the new governor bound.
    """
    record = dict(institution_record)
    now = time.time()

    existing = record.get("governors", [])
    if governor_timeline_id not in existing:
        existing = existing + [governor_timeline_id]
        record["governors"] = existing
        record["last_governor_change_at"] = now
        record["last_updated_at"] = now

        history_entry = {
            "timeline_id": governor_timeline_id,
            "added_at": now,
            "removed_at": None,
            "reason": reason,
            "bound_by": bound_by,
        }
        record["governor_history"] = record.get("governor_history", []) + [history_entry]

    # Auto-store so is_institution_admin can immediately resolve this governor
    store_institution(record)
    return record


def unbind_governor(
    institution_record: dict,
    governor_timeline_id: str,
    unbound_by: str | None = None,
    reason: str = "removed",
) -> dict:
    """Unbind a Layer 1 human timeline from governor authority.

    Removes the timeline from the governors list and closes the history entry.
    This function auto-stores the updated record so is_institution_admin
    immediately reflects the removal.

    Args:
        institution_record: The institution registry record
        governor_timeline_id: Layer 1 timeline_id to remove from governors
        unbound_by: Layer 1 timeline_id of who authorized this removal (optional)
        reason: Why the governor is being removed (e.g. "resigned", "dismissed")

    Returns:
        The updated institution record with the governor unbound.
    """
    record = dict(institution_record)
    now = time.time()

    existing = record.get("governors", [])
    if governor_timeline_id in existing:
        record["governors"] = [g for g in existing if g != governor_timeline_id]
        record["last_governor_change_at"] = now
        record["last_updated_at"] = now

        # Close the open history entry for this governor
        updated_history = []
        for entry in record.get("governor_history", []):
            if entry.get("timeline_id") == governor_timeline_id and entry.get("removed_at") is None:
                closed = dict(entry)
                closed["removed_at"] = now
                closed["reason"] = reason
                closed["unbound_by"] = unbound_by
                updated_history.append(closed)
            else:
                updated_history.append(entry)
        record["governor_history"] = updated_history

    # Auto-store so is_institution_admin immediately reflects the removal
    store_institution(record)
    return record


def list_governors(institution_record: dict) -> list[dict]:
    """Return the list of currently active governors for the institution.

    Args:
        institution_record: An institution registry record dict

    Returns:
        List of governor entry dicts (those with removed_at == None).
    """
    return [
        e for e in institution_record.get("governor_history", [])
        if e.get("removed_at") is None
    ]


def is_governor(institution_record: dict, timeline_id: str) -> bool:
    """Return True if the given Layer 1 timeline is an active governor.

    Args:
        institution_record: An institution registry record dict
        timeline_id: Layer 1 timeline_id to check

    Returns:
        True if the timeline is a current governor, False otherwise.
    """
    return timeline_id in institution_record.get("governors", [])


# =============================================================================
# GOVERNOR-GATED ADMIN CHECK (replaces stub in Layer 2)
# =============================================================================

def is_institution_admin(timeline_id: str, institution_id: str) -> bool:
    """Return True if the given Layer 1 timeline is a governor of the institution.

    This function requires Layer 3 institution registry. If the registry is
    not loaded, returns False (deny-by-default).

    Args:
        timeline_id: Layer 1 timeline_id to check
        institution_id: Institution to check against

    Returns:
        True if the timeline is an active governor of the institution.
    """
    inst = _INSTITUTIONS.get(institution_id)
    if inst is None:
        return False
    return is_governor(inst, timeline_id)


# =============================================================================
# IN-PROCESS INSTITUTION STORE (stub — replace with DB in production)
# =============================================================================
_INSTITUTIONS: dict[str, dict] = {}  # institution_id -> institution record


def store_institution(institution_record: dict) -> None:
    """Store an institution registry record (in-process)."""
    inst_id = institution_record.get("institution_id")
    _INSTITUTIONS[inst_id] = institution_record


def get_institution(institution_id: str) -> dict | None:
    """Retrieve an institution registry record by institution_id (in-process)."""
    return _INSTITUTIONS.get(institution_id)


def list_institutions(status: str | None = None) -> list[dict]:
    """List all institutions, optionally filtered by status.

    Args:
        status: Optional status filter (InstitutionStatus enum value)

    Returns:
        List of institution records matching the filter.
    """
    if status is None:
        return list(_INSTITUTIONS.values())
    return [i for i in _INSTITUTIONS.values() if i.get("status") == status]


# =============================================================================
# CROSS-LAYER LINKAGE HELPERS
# =============================================================================

def link_role_to_institution(institution_record: dict, role_id: str) -> dict:
    """Link a Layer 2 role timeline to this institution.

    Args:
        institution_record: The institution registry record
        role_id: The role_id to link

    Returns:
        The updated institution record with the role_id added.
    """
    record = dict(institution_record)
    now = time.time()
    role_ids = record.get("role_timeline_ids", [])
    if role_id not in role_ids:
        record["role_timeline_ids"] = role_ids + [role_id]
        record["last_updated_at"] = now
    return record


def add_roster_member(
    institution_record: dict,
    timeline_id: str,
    added_by: str | None = None,
) -> dict:
    """Add a Layer 1 timeline to the institution's roster.

    Roster members are humans affiliated with the institution but not necessarily
    in an active role. Roster membership is informational.

    Args:
        institution_record: The institution registry record
        timeline_id: Layer 1 timeline_id to add to the roster
        added_by: Layer 1 timeline_id of who added this member (optional)

    Returns:
        The updated institution record with the roster member added.
    """
    record = dict(institution_record)
    now = time.time()
    roster = record.get("roster", [])
    if timeline_id not in roster:
        record["roster"] = roster + [timeline_id]
        record["last_updated_at"] = now
    return record


def remove_roster_member(
    institution_record: dict,
    timeline_id: str,
) -> dict:
    """Remove a Layer 1 timeline from the institution's roster.

    Args:
        institution_record: The institution registry record
        timeline_id: Layer 1 timeline_id to remove from the roster

    Returns:
        The updated institution record with the roster member removed.
    """
    record = dict(institution_record)
    now = time.time()
    record["roster"] = [m for m in record.get("roster", []) if m != timeline_id]
    record["last_updated_at"] = now
    return record


def list_roster(institution_record: dict) -> list[str]:
    """Return the list of roster member timeline_ids for the institution.

    Args:
        institution_record: An institution registry record dict

    Returns:
        List of Layer 1 timeline_ids.
    """
    return list(institution_record.get("roster", []))


# =============================================================================
# GOVERNANCE HEALTH REPORT — Layer 3 operator-facing aggregator
# =============================================================================
# Thin read-only aggregator that consolidates institutional health signals
# from existing modules into one coherent operator-facing summary.
#
# Categories:
# - subsystem_health       → self_architecture.py
# - governance_quality     → governance_scorecard.py, governance_surface.py
# - observability_freshness → capsule_observability.py, observability.py
# - bootstrap_readiness    → bootstrap.py
# - audit_trace_health     → audit_ledger.py, audit_replay.py
# - bottleneck_pressure     → deterministic_synthesis.py
# - recommended_next_actions → improvement_engine.py, governance_surface.py
#
# Rules:
# - read-only, no writes, no side effects
# - graceful degradation: missing modules are skipped (not fatal)
# - operator-facing view: no raw subsystem IDs, no internal trace details
# =============================================================================

import time as _time


def _safe_import(module_path: str, names: tuple[str, ...]):
    """Try importing names from a module; return (None, None) on failure."""
    try:
        mod = __import__(module_path, fromlist=names)
        return tuple(getattr(mod, n) for n in names)
    except Exception:
        return tuple(None for _ in names)


def get_institutional_health_summary() -> dict:
    """Return a read-only governance health summary for the institution.

    Aggregates signals from existing modules into one operator-facing view.
    Each category is independently populated — a failure in one module does
    not block the others.

    Returns:
        A dict with keys:
        - generated_at: Unix timestamp
        - subsystem_health: dict with counts by status, open risks by severity
        - governance_quality: dict with decisions by type, pending count
        - observability_freshness: dict with capsule status, freshness, routing counts
        - bootstrap_readiness: dict with completed/pending counts
        - audit_trace_health: dict with trace summary, open forensic reports
        - bottleneck_pressure: dict with recurrence summaries
        - recommended_next_actions: list of prioritized improvement items
    """
    now = _time.time()
    report = {
        "generated_at": now,
        "subsystem_health": _get_subsystem_health(),
        "governance_quality": _get_governance_quality(),
        "observability_freshness": _get_observability_freshness(),
        "bootstrap_readiness": _get_bootstrap_readiness(),
        "audit_trace_health": _get_audit_trace_health(),
        "bottleneck_pressure": _get_bottleneck_pressure(),
        "recommended_next_actions": _get_recommended_actions(),
    }
    return report


def _get_subsystem_health() -> dict:
    """Aggregate subsystem health from self_architecture.py."""
    try:
        from weslr.self_architecture import SelfArchitecture
        arch = SelfArchitecture.load()
        active = arch.get_subsystems_by_status("active")
        degraded = arch.get_subsystems_by_status("degraded")
        offline = arch.get_subsystems_by_status("offline")
        critical_risks = arch.get_risks_by_severity("critical")
        high_risks = arch.get_risks_by_severity("high")
        return {
            "subsystem_count": len(arch.subsystems),
            "active_count": len(active),
            "degraded_count": len(degraded),
            "offline_count": len(offline),
            "critical_risk_count": len(critical_risks),
            "high_risk_count": len(high_risks),
            "risk_names": (
                [r.description for r in critical_risks] +
                [r.description for r in high_risks]
            ),
        }
    except Exception:
        return {"error": "self_architecture unavailable"}


def _get_governance_quality() -> dict:
    """Aggregate governance quality from governance_scorecard + governance_surface."""
    result = {"decisions_by_type": {}, "pending_proposal_count": 0}
    try:
        from weslr import observability
        gov_summary = observability.export_governance_summary()
        result["decisions_by_type"] = gov_summary.get("decisions_by_type", {})
    except Exception:
        pass
    try:
        from weslr.self_architecture import SelfArchitecture
        arch = SelfArchitecture.load()
        pending = arch.get_pending_proposals()
        result["pending_proposal_count"] = len(pending)
    except Exception:
        pass
    return result


def _get_observability_freshness() -> dict:
    """Aggregate observability freshness from capsule_observability + observability."""
    result = {"capsule_status": {}, "routing_summary": {}}
    try:
        from weslr.capsule_observability import get_capsule_status
        result["capsule_status"] = get_capsule_status()
    except Exception:
        pass
    try:
        from weslr import observability
        result["routing_summary"] = observability.export_routing_summary()
    except Exception:
        pass
    return result


def _get_bootstrap_readiness() -> dict:
    """Aggregate bootstrap readiness from bootstrap.py."""
    try:
        from weslr.bootstrap import (
            list_completed_bootstraps,
            list_pending_bootstraps,
        )
        completed = list_completed_bootstraps()
        pending = list_pending_bootstraps()
        expired = [p for p in pending if p.get("activation_expires_at", float("inf")) < _time.time()]
        return {
            "completed_count": len(completed),
            "pending_count": len(pending),
            "expired_count": len(expired),
        }
    except Exception:
        return {"error": "bootstrap module unavailable"}


def _get_audit_trace_health() -> dict:
    """Aggregate audit trace health from audit_ledger + audit_replay."""
    result = {"trace_summary": {}, "open_forensic_report_count": 0}
    try:
        from weslr.audit_ledger import AuditLedger
        ledger = AuditLedger()
        summary = ledger.get_trace_summary("__placeholder__")
        result["trace_summary"] = summary
    except Exception:
        pass
    try:
        from weslr.audit_replay import AuditReplayStore
        store = AuditReplayStore()
        reports = store._load_reports() if hasattr(store, "_load_reports") else []
        open_reports = [r for r in reports if r.get("status") in ("draft", "review")]
        result["open_forensic_report_count"] = len(open_reports)
    except Exception:
        pass
    return result


def _get_bottleneck_pressure() -> dict:
    """Aggregate bottleneck pressure from deterministic_synthesis.py."""
    try:
        from weslr.deterministic_synthesis import (
            ConfidenceTrendSummary,
            BottleneckRecurrenceSummary,
        )
        return {
            "note": "bottleneck events require input — call synthesize_bottleneck_recurrences() separately",
            "recurrence_summary_count": 0,
        }
    except Exception:
        return {"error": "deterministic_synthesis unavailable"}


def _get_recommended_actions() -> list[dict]:
    """Aggregate recommended next actions from improvement_engine + governance_surface."""
    actions = []
    try:
        from weslr.improvement_engine import ImprovementEngine
        engine = ImprovementEngine()
        for suggestion in engine.get_top_suggestions(limit=5):
            actions.append({
                "improvement_id": suggestion.get("improvement_id", ""),
                "description": suggestion.get("description", ""),
                "rationale": suggestion.get("rationale", ""),
                "priority": suggestion.get("priority", "unknown"),
                "risk_level": suggestion.get("risk_level", "unknown"),
                "affected_subsystem": suggestion.get("affected_subsystem", ""),
            })
    except Exception:
        pass
    try:
        from weslr.self_architecture import SelfArchitecture
        arch = SelfArchitecture.load()
        pending = arch.get_pending_proposals()
        for p in pending[:5]:
            actions.append({
                "improvement_id": p.get("proposal_id", ""),
                "description": p.get("description", ""),
                "rationale": p.get("reasoning", ""),
                "priority": "pending_review",
                "risk_level": "unknown",
                "affected_subsystem": "",
            })
    except Exception:
        pass
    return actions[:10]

# =============================================================================
# BACKGROUND REFLECTIVE DRIFT LOOP — Layer 3 governance observation
# =============================================================================
# Quiet background drift observation and aggregation. Accumulates evidence
# of institutional friction, degradation, and continuity failures over time,
# surfacing only when convergence thresholds are met or high-confidence
# signals are detected.
#
# Rules:
# - evidence-based only; no speculation
# - no self-modification without operator approval
# - surfacing requires convergence (2+ independent signals) or high-confidence threshold
# - cooldown prevents repeated re-surfacing of the same concern
# - reflections produce proposals via governance_surface, never self-authorize
#
# Signal types:
# - LATENCY          — response time drift
# - MEMORY_QUALITY   — memory retrieval failures
# - HANDOVER_GAP     — role vacancy without timely assignment
# - OVERRIDE         — human overrides of WESLR recommendations
# - ESCALATION       — repeated security/escalation friction
# - LIFECYCLE_STALE  — stagnant bootstrap or role states
# - INSTITUTION_REC  — repeated vacancy in the same role
# - BOTTLENECK_REC   — recurring bottleneck events
# - SUGGESTION_REJECT — consistent low-fit suggestion assessments
# =============================================================================

import time as _time


class DriftSignalType:
    LATENCY = "latency"
    MEMORY_QUALITY = "memory_quality"
    HANDOVER_GAP = "handover_gap"
    OVERRIDE = "governance_override"
    ESCALATION = "escalation"
    LIFECYCLE_STALE = "lifecycle_stale"
    INSTITUTION_REC = "institution_recurrence"
    BOTTLENECK_REC = "bottleneck_recurrence"
    SUGGESTION_REJECT = "suggestion_reject"


class ReflectionStatus:
    PENDING = "pending"      # Meets convergence/threshold, ready to surface
    COOLDOWN = "cooldown"    # Recently surfaced, waiting for cooldown expiry
    SURFACED = "surfaced"    # Operator has been shown this
    DISMISSED = "dismissed"  # Operator explicitly dismissed this concern


class DriftSignal:
    """A single observed drift signal from the system."""

    def __init__(
        self,
        signal_type: str,
        value: float,
        context: dict | None = None,
        severity: str = "medium",
    ):
        self.signal_type = signal_type
        self.value = value
        self.context = context or {}
        self.severity = severity
        self.observed_at = _time.time()

    def to_dict(self) -> dict:
        return {
            "signal_type": self.signal_type,
            "value": self.value,
            "context": self.context,
            "severity": self.severity,
            "observed_at": self.observed_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DriftSignal":
        sig = cls(d["signal_type"], d["value"], d.get("context"), d.get("severity", "medium"))
        sig.observed_at = d.get("observed_at", _time.time())
        return sig


class Reflection:
    """A reflective observation ready for operator surfacing."""

    CONVERGENCE_THRESHOLD = 2  # minimum independent signal types for convergence
    HIGH_CONFIDENCE_SAMPLES = 5  # single-signal high-confidence sample count
    DEFAULT_COOLDOWN_SECS = 86400  # 24 hours

    def __init__(
        self,
        concern: str,
        signals: list[DriftSignal],
        confidence: str = "medium",
        description: str = "",
        proposal_hint: str = "",
    ):
        self.concern = concern
        self.signals = signals
        self.confidence = confidence
        self.description = description
        self.proposal_hint = proposal_hint
        self.status = ReflectionStatus.PENDING
        self.created_at = _time.time()
        self.last_surfaced_at: float | None = None
        self.cooldown_until: float | None = None
        self.dismissed_reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "concern": self.concern,
            "confidence": self.confidence,
            "description": self.description,
            "proposal_hint": self.proposal_hint,
            "status": self.status,
            "created_at": self.created_at,
            "last_surfaced_at": self.last_surfaced_at,
            "cooldown_until": self.cooldown_until,
            "dismissed_reason": self.dismissed_reason,
            "signal_count": len(self.signals),
            "signal_types": list(set(s.signal_type for s in self.signals)),
        }

    def enter_cooldown(self, seconds: float | None = None) -> None:
        self.status = ReflectionStatus.COOLDOWN
        self.cooldown_until = _time.time() + (seconds or self.DEFAULT_COOLDOWN_SECS)

    def dismiss(self, reason: str = "") -> None:
        self.status = ReflectionStatus.DISMISSED
        self.dismissed_reason = reason
        self.cooldown_until = None

    def mark_surfaced(self) -> None:
        self.status = ReflectionStatus.SURFACED
        self.last_surfaced_at = _time.time()


# =============================================================================
# IN-PROCESS DRIFT SIGNAL STORE
# =============================================================================
_DRIFT_SIGNALS: list[DriftSignal] = []
_REFLECTIONS: list[Reflection] = []
_DRIFT_WINDOW_SECS = 172800  # 48-hour rolling window
_MAX_SIGNALS = 1000


def record_drift_signal(
    signal_type: str,
    value: float,
    context: dict | None = None,
    severity: str = "medium",
) -> None:
    """Record a drift signal observation.

    Args:
        signal_type: One of DriftSignalType values
        value: Numeric signal value
        context: Arbitrary context dict
        severity: "low", "medium", "high", "critical"
    """
    valid = {
        DriftSignalType.LATENCY, DriftSignalType.MEMORY_QUALITY,
        DriftSignalType.HANDOVER_GAP, DriftSignalType.OVERRIDE,
        DriftSignalType.ESCALATION, DriftSignalType.LIFECYCLE_STALE,
        DriftSignalType.INSTITUTION_REC, DriftSignalType.BOTTLENECK_REC,
        DriftSignalType.SUGGESTION_REJECT,
    }
    if signal_type not in valid:
        return
    signal = DriftSignal(signal_type, value, context, severity)
    _DRIFT_SIGNALS.append(signal)
    now = _time.time()
    cutoff = now - _DRIFT_WINDOW_SECS
    # Evict stale signals; cap at _MAX_SIGNALS
    kept = [s for s in _DRIFT_SIGNALS if s.observed_at > cutoff]
    if len(kept) > _MAX_SIGNALS:
        kept = kept[-_MAX_SIGNALS:]
    _DRIFT_SIGNALS[:] = kept


def _active_by_type(stype: str, window: float = _DRIFT_WINDOW_SECS) -> list[DriftSignal]:
    now = _time.time()
    return [s for s in _DRIFT_SIGNALS if s.signal_type == stype and (now - s.observed_at) < window]


def _recent(window: float = _DRIFT_WINDOW_SECS) -> list[DriftSignal]:
    now = _time.time()
    return [s for s in _DRIFT_SIGNALS if (now - s.observed_at) < window]


def _e_latency() -> list[DriftSignal] | None:
    s = _active_by_type(DriftSignalType.LATENCY)
    if len(s) < 5:
        return None
    vals = [x.value for x in s]
    if vals[-1] > (sum(vals) / len(vals)) * 1.3:
        return s[-3:]
    return None


def _e_memory() -> list[DriftSignal] | None:
    r = _recent()
    if len(r) < 20:
        return None
    fails = [s for s in r if s.signal_type == DriftSignalType.MEMORY_QUALITY and s.value < 0.5]
    if len(fails) / len(r) > 0.3:
        return fails[-3:]
    return None


def _e_handover() -> list[DriftSignal] | None:
    s = _active_by_type(DriftSignalType.HANDOVER_GAP)
    return s[-2:] if len(s) >= 2 else None


def _e_override() -> list[DriftSignal] | None:
    s = _active_by_type(DriftSignalType.OVERRIDE)
    return s[-3:] if len(s) >= 3 else None


def _e_escalation() -> list[DriftSignal] | None:
    s = _active_by_type(DriftSignalType.ESCALATION)
    return s[-3:] if len(s) >= 3 else None


def _e_lifecycle() -> list[DriftSignal] | None:
    s = _active_by_type(DriftSignalType.LIFECYCLE_STALE)
    crit = [x for x in s if x.severity == "critical"]
    if crit:
        return crit
    return s[-3:] if len(s) >= 5 else None


def _e_institution() -> list[DriftSignal] | None:
    s = _active_by_type(DriftSignalType.INSTITUTION_REC)
    return s[-2:] if len(s) >= 2 else None


def _e_bottleneck() -> list[DriftSignal] | None:
    s = _active_by_type(DriftSignalType.BOTTLENECK_REC)
    return s[-3:] if len(s) >= 3 else None


def _e_suggestion() -> list[DriftSignal] | None:
    r = _recent()
    s = [x for x in r if x.signal_type == DriftSignalType.SUGGESTION_REJECT]
    if len(s) >= 5:
        rej = [x for x in s if x.value < 0.3]
        if len(rej) / len(s) > 0.5:
            return s[-3:]
    return None


_CONCERN_EVALUATORS = {
    "latency_drift": _e_latency,
    "memory_quality_degradation": _e_memory,
    "handover_gap": _e_handover,
    "governance_override_frequency": _e_override,
    "escalation_friction": _e_escalation,
    "lifecycle_stagnation": _e_lifecycle,
    "institution_role_recurrence": _e_institution,
    "bottleneck_recurrence": _e_bottleneck,
    "suggestion_rejection_trend": _e_suggestion,
}

_CONCERN_DESCRIPTIONS = {
    "latency_drift": "Response latency has drifted significantly over the observation window.",
    "memory_quality_degradation": "Memory retrieval quality has degraded — recall failures are above baseline.",
    "handover_gap": "Role handover gaps detected — vacancies are not being resolved within expected time.",
    "governance_override_frequency": "Human override frequency is elevated — operator is frequently correcting WESLR recommendations.",
    "escalation_friction": "Escalation friction is recurring — similar escalations are being triggered repeatedly.",
    "lifecycle_stagnation": "Lifecycle stagnation detected — one or more states have been stale longer than expected.",
    "institution_role_recurrence": "A role has been vacant multiple times recently — this may indicate a structural gap.",
    "bottleneck_recurrence": "Bottleneck events are recurring — the same constraint is triggering repeatedly.",
    "suggestion_rejection_trend": "Suggestion rejection rate is elevated — suggested capabilities are consistently not meeting fit thresholds.",
}


def run_drift_observation_pass() -> list[dict]:
    """Run one drift observation pass.

    Evaluates all concern types against the rolling signal window.
    Returns reflections ready to surface (pending, not in cooldown).

    Returns:
        List of reflection dicts.
    """
    now = _time.time()
    surfaced = []

    for concern, evaluator in _CONCERN_EVALUATORS.items():
        existing = [r for r in _REFLECTIONS if r.concern == concern and r.status == ReflectionStatus.COOLDOWN]
        if existing and existing[0].cooldown_until and existing[0].cooldown_until > now:
            continue
        for ref in existing:
            if ref.cooldown_until and ref.cooldown_until <= now:
                ref.status = ReflectionStatus.PENDING

        signals = evaluator()
        if not signals:
            continue

        stypes = set(s.signal_type for s in signals)
        conf = "high"
        if len(signals) < Reflection.HIGH_CONFIDENCE_SAMPLES and not any(s.severity == "critical" for s in signals):
            conf = "medium"
        if len(stypes) >= Reflection.CONVERGENCE_THRESHOLD:
            conf = "high"

        description = _CONCERN_DESCRIPTIONS.get(concern, f"Drift concern: {concern}")
        reflection = Reflection(concern, signals, conf, description)
        _REFLECTIONS.append(reflection)
        d = reflection.to_dict()
        surfaced.append(d)
        reflection.enter_cooldown()

    return surfaced


def get_pending_reflections() -> list[dict]:
    """Return pending reflections not in cooldown."""
    now = _time.time()
    return [
        r.to_dict() for r in _REFLECTIONS
        if r.status == ReflectionStatus.PENDING
        and not (r.cooldown_until and r.cooldown_until > now)
    ]


def acknowledge_reflection(concern: str, outcome: str = "surfaced") -> bool:
    """Acknowledge a pending or cooldown reflection.

    Args:
        concern: Concern string
        outcome: "surfaced" or "dismissed"

    Returns:
        True if found and updated.
    """
    ref = next(
        (r for r in _REFLECTIONS
         if r.concern == concern and r.status in (ReflectionStatus.PENDING, ReflectionStatus.COOLDOWN)),
        None,
    )
    if not ref:
        return False
    if outcome == "dismissed":
        ref.dismiss()
    else:
        ref.mark_surfaced()
        ref.enter_cooldown()
    return True


def get_reflection_status_summary() -> dict:
    """Return count summary of all reflection states."""
    return {
        "pending": len([r for r in _REFLECTIONS if r.status == ReflectionStatus.PENDING]),
        "cooldown": len([r for r in _REFLECTIONS if r.status == ReflectionStatus.COOLDOWN]),
        "surfaced": len([r for r in _REFLECTIONS if r.status == ReflectionStatus.SURFACED]),
        "dismissed": len([r for r in _REFLECTIONS if r.status == ReflectionStatus.DISMISSED]),
        "total_signals": len(_DRIFT_SIGNALS),
    }
