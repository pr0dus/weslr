# WESLR Release Checklist — V1

**Version:** 1.0
**Status:** active reference
**Created:** 2026-04-27

Use this checklist before committing any WESLR change. All items must be confirmed before the commit is final. If an item cannot be confirmed, it must be explicitly deferred with a reason.

---

## Pre-Commit Checklist

### G1 — Git Clean Check
```
git status --short
```
- [ ] No untracked files in weslr/ that shouldn't be committed
- [ ] No unexpected modifications to OpenClaw core files
- [ ] No modifications to TIA bridge C# files
- [ ] Only WESLR Python files and docs in scope of the change
- [ ] Untracked temp files (e.g., `*.bak`, `_*.py`) are cleaned or explicitly ignored

### G2 — Test Suite Pass

Run in order:

1. **T3 — JSONL malformed-line read tests**
   ```
   python3 <<'PY' [malformed-line test code from TEST_STRATEGY_V1] PY
   ```
   - [ ] All 3 loaders skip malformed lines
   - [ ] Missing file returns `[]`

2. **T2 — Write-side schema guard tests**
   ```
   python3 <<'PY' [write-side schema guard test code from TEST_STRATEGY_V1] PY
   ```
   - [ ] All 6 invalid write cases raise `ValueError`

3. **T1 — Deterministic route smoke tests**
   ```
   python3 <<'PY' [smoke test code from TEST_STRATEGY_V1] PY
   ```
   - [ ] All routes match expected paths
   - [ ] All expected payload fields present

4. **T4 — No-write safety tests**
   ```
   python3 <<'PY' [no-write safety test code from TEST_STRATEGY_V1] PY
   ```
   - [ ] All JSONL file hashes identical before/after

5. **T6 — Full smoke command list**
   ```
   python3 <<'PY' [full smoke test code from TEST_STRATEGY_V1] PY
   ```
   - [ ] No exceptions raised
   - [ ] All commands return a response dict

### G3 — JSONL Backup Note

**Before any write test that appends to JSONL:**
- [ ] Note current JSONL line counts:
  - `proposal_trace.jsonl`: _____ lines
  - `implementation_plans.jsonl`: _____ lines
  - `iss_diagnostic_records.jsonl`: _____ lines
- [ ] After tests, confirm no net new lines added to production files (test records may be appended but should be minimal)
- [ ] If line counts increased, confirm all appended records are intentionally added by tests

### G4 — No execution_allowed=True Check

For any change that touches JSONL schema or plan/probe creation:
- [ ] Run: `grep -r "execution_allowed.*True" /data/data/com.termux/files/home/.openclaw/workspace/weslr/ --include="*.py"`
- [ ] Confirm: zero results (no `execution_allowed=True` in codebase)
- [ ] If found, the change must not introduce any new `execution_allowed=True` in written records

### G5 — No OpenClaw Core Touched

- [ ] `git diff --stat HEAD --name-only | grep -v weslr/` confirms no OpenClaw core files modified
- [ ] `grep -r "TIA\|openclaw/core\|openclaw/gateway" --include="*.py" weslr/` confirms no cross-repo imports that shouldn't exist

### G6 — Commit Hash Recorded

After commit:
- [ ] Note the commit hash: `________`
- [ ] Verify: `git log --oneline -1` matches expected commit
- [ ] Update this field in the relevant tracking document if one exists

### G7 — Rollback Note

For each commit, document the rollback command:

```
git revert <commit-hash>
```

- [ ] Rollback command confirmed working
- [ ] Rollback does not affect JSONL data files (append-only logs cannot be reverted by git revert alone)

If the change includes JSONL schema changes:
- [ ] Rollback note: "JSONL schema changes are append-only; rollback via `git revert` only reverts code, not data"
- [ ] If data rollback needed, operator must manually trim JSONL files (extreme case; not expected)

---

## Scope Guards

### These files are in-scope for WESLR changes:
```
weslr/*.py                          — WESLR Python modules
weslr/docs/**/*.md                  — WESLR documentation
weslr/docs/engineering/**/*.md      — Engineering docs
```

### These files are NOT in-scope:
```
interpretation.py                   — may be modified within scope
main.py                            — OpenClaw entry point
entity_graph.py                     — entity graph (separate subsystem)
plugins/                           — OpenClaw plugin directory
memory/                            — session memory files
continuity/                        — continuity artifacts
weslr/docs/tia-bridge/             — commercial TIA docs only
```

### These are always off-limits:
```
openclaw/                           — OpenClaw core
/data/data/com.termux/files/home/    — Termux system files
TIA bridge C# codebase             — private repo
```

---

## Release Decision Table

| Check | Decision |
|---|---|
| G1 clean | Proceed or defer non-essential files |
| T3 pass | Required before any write test |
| T2 pass | Required before commit |
| T1 pass | Required before commit |
| T4 pass | Required before commit |
| T6 pass | Required before commit |
| G3 JSONL backup noted | Required for any write change |
| G4 execution_allowed=True check | Required for any schema/plan/probe change |
| G5 OpenClaw core not touched | Required always |
| G6 commit hash recorded | Required for all commits |
| G7 rollback note | Required for all commits |

If **any required item is not confirmed**, the release must be **deferred** until the item is resolved or explicitly waived by the operator with a documented reason.

---

*Release Checklist V1 — 2026-04-27*
*Run all checks before every WESLR commit*
