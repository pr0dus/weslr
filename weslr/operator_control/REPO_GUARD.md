# REPO GUARD — WESLR Operator Workflow

Strict rules for development operators.

---

## Authoritative Paths

- **Workspace**: `/data/data/com.termux/files/home/.openclaw/workspace`
- **WESLR scope**: `/data/data/com.termux/files/home/.openclaw/workspace/weslr`

---

## Scope Rules

- WESLR Python files only (`*.py` in `weslr/`)
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

---

## Completion Rules

- Never claim complete before:
  - Tests pass
  - Commit created
  - Exact commit hash reported

---

## Sealing Rules

- Always require exact commit hash
- No partial or ambiguous seals
- Update `OPERATOR_STATE.json` with new seal reference

---

## Continuity Rules

- Continuity helps planning but never replaces repo truth
- Always anchor to latest sealed commit from repo

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
