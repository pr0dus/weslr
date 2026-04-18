# Proposal Lineage View (v1) — Doctrine-First & Schema-Only

**Scope:** Doctrine and schema specification for the first slice of the operator-readable proposal lineage view. Implementation is out of scope for this doc. Origin fields are immutable; status/audit entries are append-only.

## SECTION 1 — PURPOSE
Preserve and expose per-proposal lineage so operators can audit origin, trigger, scope, evidence context, confidence, checkpoint link, and status evolution without altering runtime behavior.

## SECTION 2 — FIRST SLICE (REQUIRED FIELDS)
- `proposal_id`
- `source_loop_id`
- `workspace_id`
- `user_id`
- `trigger_reason`
- `originating_evidence_signal`
- `timestamp`
- `confidence`
- `linked_checkpoint`
- `current_status`

## SECTION 3 — IMMUTABILITY + APPEND RULES
- **Immutable origin block:** `proposal_id`, `source_loop_id`, `workspace_id`, `user_id`, `trigger_reason`, `originating_evidence_signal`, `timestamp`, `linked_checkpoint`, initial `confidence` at emission.
- **Append-only/status-updatable:** `current_status` (via governed state machine), status change trail, confidence annotations (subsequent assessments), audit entries (viewer/access logs), and commentary/reason notes.
- **Forbidden mutations:** No edits to immutable origin fields; no deletion or rewrite of historical audit/status entries; no re-assignment of `linked_checkpoint` once set.

## SECTION 4 — MINIMAL SCHEMA
### Lineage Record
```yaml
proposal_id: string (pk)
source_loop_id: string
workspace_id: string
user_id: string
trigger_reason: string
originating_evidence_signal: string | enum
timestamp: RFC3339
confidence: number (0..1) with optional rationale
linked_checkpoint: string | ref
current_status: enum[pending, under_review, approved, rejected, applied, superseded]
audit_log: [AuditEntry]
status_history: [StatusEntry]
```

### StatusEntry (append-only)
```yaml
proposal_id: string (fk)
from_status: enum
to_status: enum
actor: string (user_id or service id)
timestamp: RFC3339
note: string (optional)
```

### AuditEntry (append-only)
```yaml
proposal_id: string (fk)
action: enum[view, export, status_change]
actor: string (user_id or service id)
timestamp: RFC3339
context: string (optional: filter params, interface surface)
```

### Indexing / Filters
- Index on `proposal_id` (pk), `source_loop_id`, `workspace_id`, `user_id`, `current_status`, `timestamp` for efficient reads.
- Filters: by `source_loop_id`, `workspace_id`, `user_id`, `status`, time window.

## SECTION 5 — GOVERNANCE
- **View:** owner/admin by default; standard/limited only if explicitly granted via governance framework.
- **Status change:** owner/admin; delegated operators if explicitly granted; all changes logged append-only.
- **Clear history:** prohibited except via owner/admin override with explicit governance approval; even then, deletion should mark-tombstone rather than remove data.
- **Read-only:** immutable origin block, prior status entries, prior audit entries.

## SECTION 6 — VALIDATION RULES
- **Required fields:** Reject creation if any required field missing or malformed.
- **Immutability enforcement:** Prevent writes to immutable origin block after creation; prevent re-assignment of `linked_checkpoint`.
- **Permission enforcement:** Role/permission checks on view/status change/history clear; deny otherwise.
- **Append-only audit logging:** Every read and status change appends an AuditEntry; every status change appends a StatusEntry.
- **Export/read behavior:** Reads are governed; exports must include audit logging and respect the same permissions.

## SECTION 7 — IMPLEMENTATION GUARDRAILS
- Doctrine-first; schema-only in this version. No runtime code changes in this slice.
- Any future implementation must respect governed activation and permission framework and preserve immutability semantics.
