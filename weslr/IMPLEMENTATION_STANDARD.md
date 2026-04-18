# IMPLEMENTATION_STANDARD.md - WESLR Execution Contract

## 1. Two-Phase Workflow

**Phase 1: planning only**
- Analyze requirements and existing codebase
- Identify exact files to modify/create
- Define test strategy
- Produce execution plan

**Phase 2: implementation only**
- Execute the approved plan
- Make code changes
- Run tests
- Commit changes

**Seal only after tests + git truth** — never before both are verified.

---

## 2. Approved File-Touch Rules

| Step Type | Allowed Files |
|-----------|---------------|
| Implementation steps | Only approved files (from plan) |
| Checkpoint refresh | Architecture/operator/release files only |
| Entity restoration | Restore `entity_graph.json` before seal if modified unrelated to scope |

**Memory files** are operator artifacts, not product changes.

---

## 3. Seal Criteria

A layer is sealed only when **all four** criteria are met:

- ✅ Scoped code changes exist
- ✅ Scoped tests pass
- ✅ Commit exists (with descriptive message)
- ✅ Git truth confirms clean enough tree (no untracked/unstaged non-excluded files)

---

## 4. Scope Discipline

**Must be:**
- Read-only or operator-facing unless explicitly changed

**Explicitly forbidden:**
- TIA/C# code
- Orchestration logic
- Sharding logic
- Aggregation logic
- Scheduler/task engine code
- Backend/service/UI code
- Automatic remediation logic

---

## 5. Heuristic / Measurement Honesty

- Confidence scores are **guidance**, not certainty
- Similarity, significance, drift, escalation are **heuristics**
- Inferred vs measured data **must be clearly separated**

---

## 6. Lightweight Store/Event Rule

- No accidental persistence subsystem
- No accidental event/telemetry framework expansion

---

## 7. Required Output Contract

### For Planning Output:
- Repo verification status
- Exact file plan (paths only)
- Exact implementation scope (what changes, why)
- Exact test plan (commands, expectations)

### For Completion Output:
- Exact files changed (list)
- Validation result (pass/fail + details)
- Exact full commit hash
- Git truth result
- Seal status (`sealed` or `not sealed`)

---

## Validation Checklist

- [x] Concise — no fluff, no boilerplate
- [x] Implementation-oriented — executable guidance
- [x] Aligned with current WESLR workflow
- [x] No runtime code changes required

---

## Output Format

**Completion must output exactly:**

1. Exact files changed  
2. Validation result  
3. Exact commit hash  
4. `stop`
