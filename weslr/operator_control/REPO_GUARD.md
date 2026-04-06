# REPO GUARD — WESLR Operator Workflow

Strict rules for development operators.

---

## Authoritative Paths

- **Workspace**: `/data/data/com.termux/files/home/.openclaw/workspace`
- **WESLR scope**: `/data/data/com.termux/files/home/.openclaw/workspace/weslr`

---

## Scope Rules

- **Active scope**: WESLR Python files only (`*.py` in `weslr/`)
- **Excluded scope** (never routed):
  - `TIA`
  - `collector`
  - `industrial_slice`
  - `product_runtime_expansion`
- **No TIA**, **no C#**, unless explicitly requested
- **No product runtime expansion** — internal operator workflow only

---

## Pre-Edit Checks (Mandatory)

Before any edit:

1. Verify `pwd` matches authoritative workspace path
2. Confirm `git rev-parse --show-toplevel` matches repo root
3. Check `git branch --show-current` and `git rev-parse HEAD`
4. Run `git status --short` to confirm working tree state
5. Confirm WESLR scope contains only Python files (unless explicitly requested otherwise)
6. Verify `active_scope` in `OPERATOR_STATE.json` is `weslr` only
7. Verify `excluded_scope` does not contain any active routing target

---

## Routing Discipline

**Allowed next categories** (only these can be `next_priority`):
- `weslr_core_layer`
- `weslr_infrastructure`
- `operator_workflow`

**Excluded scopes** (never route here):
- `TIA`
- `collector`
- `industrial_slice`
- `product_runtime_expansion`

**Rule**: `weslr next` must only select from allowed categories. Never route to excluded scopes.

---

## Completion Rules

- Never claim complete before:
  - Tests pass
  - Commit created
  - Exact commit hash reported
- Never report "0 bottlenecks" if WESLR core roadmap has pending items

---

## Sealing Rules

- Always require exact commit hash
- No partial or ambiguous seals
- Update `OPERATOR_STATE.json` with new seal reference
- Confirm `next_priority` belongs to allowed categories

---

## Continuity Rules

- Continuity helps planning but never replaces repo truth
- Always anchor to latest sealed commit from repo
- Never allow excluded scopes to become active routing targets

---

## Repo Truth Rules

- Repo truth remains authoritative at all times
- No repo drift allowed
- No hidden scope expansion
- No untracked changes assumed safe without verification

---

## Forbidden Actions

- No unverified external edits
- No direct manipulation of sealed checkpoints
- No workflow bypass without explicit override
- No product runtime expansion without explicit instruction
- No routing to excluded scopes (TIA, collector, industrial_slice, product_runtime_expansion)

## Test Doctrine

- Apply TEST_DOCTRINE.md for all new layers
- All new layers must include model, behavior, integration, and backward compatibility tests
- Test failures block merge until resolved

---

## Operator State Hardening Rules

- `active_bottlenecks` must only include WESLR core scope items
- `archived_or_external_bottlenecks` must include excluded scope items
- Never mix excluded scope items into active bottleneck counts
- `next_priority` must always belong to `allowed_next_categories`
- `excluded_scope` must never appear in active routing decisions
