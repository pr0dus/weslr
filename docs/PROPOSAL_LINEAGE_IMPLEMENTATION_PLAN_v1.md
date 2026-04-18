# Proposal Lineage View — Implementation Plan (v1)

**Scope:** Planning/checklist only. No code changes in this document. Target: first slice as defined in doctrine — read-only lineage record structure, immutable origin block, append-only status/audit, governed permissions, no UI, no external effects.

## SECTION 1 — IMPLEMENTATION TARGET (LOCKED)
- Read-only lineage record structure.
- Immutable origin block (proposal_id, source_loop_id, workspace_id, user_id, trigger_reason, originating_evidence_signal, timestamp, linked_checkpoint, initial confidence).
- Append-only status history (state machine) and append-only audit entries (view/status/export actions).
- Permission checks for view and status change per governance framework.
- No UI; no external effects; no write surface beyond governed status append.

## SECTION 2 — FILE PLAN (LOCKED)
- `weslr/lineage/__init__.py` (package scaffold).
- `weslr/lineage/model.py` (data structures for lineage record, status entry, audit entry; serialization helpers).
- `weslr/lineage/storage.py` (persistence adapter stub for in-memory or file-backed store; read-only + append-only writes).
- `weslr/lineage/validators.py` (required-field checks, immutability enforcement, schema validation).
- `weslr/lineage/permissions.py` (view/status-change permission checks; role gating hooks to governance framework).
- Tests:
  - `weslr/test_lineage_model.py` (schema/immutability/append-only behaviors).
  - `weslr/test_lineage_permissions.py` (permission enforcement).
  - `weslr/test_lineage_storage.py` (append/read filters, checkpoint linkage).
- Docs (existing doctrine reference: `docs/PROPOSAL_LINEAGE_VIEW_v1.md` once available; this plan: `docs/PROPOSAL_LINEAGE_IMPLEMENTATION_PLAN_v1.md`).

## SECTION 3 — BUILD ORDER (SAFE, MINIMAL)
1) Scaffolding: create `weslr/lineage/` package with model definitions (data classes, enums for status, actions).
2) Validators: required fields + immutability guards + append-only checks.
3) Permissions: stub permission hooks calling governance/role checks; deny by default until wired.
4) Storage adapter: minimal in-memory/file-backed append + read with filters; enforce validators + permissions on entry.
5) Wire audit/status appends within storage functions (no external side effects).
6) Test fixtures for sample lineage records and entries.
7) Tests green in isolation (no UI/no external effects).

## SECTION 4 — TEST ORDER
1) Model/validation tests: required fields, immutability rejection, append-only enforcement.
2) Permission tests: view/status allowed for owner/admin; denied for others unless explicitly granted.
3) Storage tests: creation (with immutable block), status append, audit append, filters (proposal_id/source_loop_id/workspace_id/user_id/status/time window), checkpoint link preserved.
4) Audit logging tests: read/status change produces audit entry; history is append-only.

## SECTION 5 — IMPLEMENTATION CHECKLIST
- [ ] Confirm branch `weslr/canonical-clean-signals` and clean worktree before coding.
- [ ] Add lineage package scaffold (`weslr/lineage/`).
- [ ] Define data models (lineage record, status entry, audit entry) with enums and serialization.
- [ ] Implement validators (required fields, immutability, append-only guards).
- [ ] Implement permission hooks (view, status change) leveraging governance framework.
- [ ] Implement minimal storage adapter (append-only writes, read with filters, audit on access).
- [ ] Add tests for model/validation, permissions, storage/audit.
- [ ] Run tests; ensure green.
- [ ] Document any deltas to doctrine if discovered; otherwise keep aligned with `PROPOSAL_LINEAGE_VIEW_v1`.
- [ ] Keep zero external effects; no UI.

## SECTION 6 — NOTES
- Planning-only; no code changes have been made in this doc.
- If `docs/PROPOSAL_LINEAGE_VIEW_v1.md` is missing on this branch, port/reference the canonical doctrine before coding.
