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

    # Institution admin check — lazy import to avoid circular dependency
    is_admin = False
    try:
        from weslr.institution import is_institution_admin
        is_admin = is_institution_admin(timeline_id, record.get("institution_id", ""))
    except Exception:
        pass  # Layer 3 not yet implemented — deny

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
    """Store a role timeline record (in-process)."""
    role_id = role_record.get("role_id")
    _ROLE_TIMELINES[role_id] = role_record
    institution_id = role_record.get("institution_id", "")
    if institution_id:
        _INSTITUTION_ROLES.setdefault(institution_id, set()).add(role_id)


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