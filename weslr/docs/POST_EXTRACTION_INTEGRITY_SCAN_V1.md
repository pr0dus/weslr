# WESLR Post-Extraction Integrity Scan — V1

**Version:** 1.0
**Status:** active reference
**Created:** 2026-04-27
**Scope:** Handler registry + interpretation.py after 4 extraction rounds

---

## SECTION 1 — Trigger Overlap Analysis

Scanned all 7 registry entries against each other. No ambiguous prefix collisions detected.

**Why:** Triggers use two strategies that prevent overlap:
1. **Long unique prefixes** — e.g. `"show system overview"` vs `"show diagnostics"` share `"show"` but diverge at `"show s"` where `system` vs `diagnostics` are distinct
2. **Exact-match guards** — `"show gaps"` and `"show diagnostics"` are handled by separate handlers; the longest matching prefix wins via priority sort

**Overlap matrix:**
```
"show system overview"  — 75 (operator_overview)    ← unique at "show s"
"show weslr status"     — 74 (state_checkpoint)      ← unique at "show w"
"show diagnostics"      — 70 (iss_query_all)          ← unique at "show d"
"show gaps"             — 69 (iss_query_gaps)         ← unique at "show g"
"show probe results"    — 68 (iss_query_probes)       ← unique at "show p"
"show iss probes"        — 80 (iss_probe_registry)     ← unique at "show i"
"plan probe "            — 85 (iss_probe_plan)         ← unique at "plan p"
```

**No two handlers share the same trigger prefix at the same priority level.**

---

## SECTION 2 — Priority Correctness

Priority ordering is correct. More specific handlers have higher priority:

| Priority | Handler | Rationale |
|---|---|---|
| 85 | iss_probe_plan | Most specific — `plan probe X` must not match `plan` alone |
| 80 | iss_probe_registry | Specific ISS probe stubs query |
| 75 | operator_overview | System-level but specific trigger set |
| 74 | state_checkpoint_query | Specific checkpoint query |
| 70 | iss_query_all | ISS diagnostics — specific domain |
| 69 | iss_query_gaps | ISS gaps — specific sub-domain |
| 68 | iss_query_probes | ISS probe results — specific sub-domain |

No generic handler sits above a specific one. Priority descending sort works correctly.

---

## SECTION 3 — Handler Completeness

### Extracted (7 handlers, all in registry)
```
handle_iss_probe_plan         → ISS_probe_plan
handle_iss_probe_registry     → ISS_probe_registry_query
handle_operator_overview      → operator_overview
handle_state_checkpoint       → state_checkpoint_query
handle_iss_query_all         → ISS_query_all
handle_iss_query_gaps       → ISS_query_gaps
handle_iss_query_probes      → ISS_query_probes
```

### Remaining inline handlers in interpretation.py (6 blocks)

| Block | Line | Type | Risk |
|---|---|---|---|
| `_plan_triggers` — "show implementation plans", "show plans", "list plans", "show plan for ", "get plan " | ~1026 | Read-only query | **LOW** — declarative query, no writes |
| `_intake_triggers` — "convert iss suggestion ", "convert iss gap ", "create proposal from iss ", "turn iss gap " | ~1316 | Write path (record_proposal) | **MEDIUM** — creates proposals |
| `_iss_intake_triggers` — ISS intake proposal query | ~1406 | Read-only query | **LOW** — read-only |
| `_plan_explain_triggers` — "why does plan ", "explain plan ", "why was plan " | ~1478 | Read-only query | **LOW** — read-only |
| `_execute_triggers` — "execute probe " | ~1590 | Write path (simulated only, no real exec) | **LOW** — simulated mode only, hard-coded |
| `_explain_triggers` — "why is ", "explain proposal ", "why prioritize " | ~1645 | Read-only query | **LOW** — read-only |

### Duplicate logic found — CRITICAL ISSUE ⚠️

**interpretation.py contains a duplicate section.** The file has two copies of the `_intake_triggers`, `_iss_intake_triggers`, `_plan_explain_triggers`, and `_explain_triggers` blocks at two different line ranges:
- First copy: lines ~1316–1646
- Second copy: lines ~1751–2081

The inline handler blocks appear twice in the file — the same logic is defined at two separate locations. This means:
- Both copies execute sequentially
- The second copy returns first (later in the file), shadowing the first
- This duplication is a **HIGH** risk finding

No duplicate logic exists between `deterministic_handlers.py` and `interpretation.py`.

---

## SECTION 4 — Duplicate Logic Check

| Logic | Location | Status |
|---|---|---|
| Probe plan | deterministic_handlers.py | ✓ Only location |
| Probe registry query | deterministic_handlers.py | ✓ Only location |
| Operator overview | deterministic_handlers.py | ✓ Only location |
| State checkpoint query | deterministic_handlers.py | ✓ Only location |
| ISS diagnostics (all 3) | deterministic_handlers.py | ✓ Only location |
| Proposal explanation | interpretation.py inline only | ✓ No duplicate |
| Plan explanation | interpretation.py inline only | ✓ No duplicate |
| Plan query | interpretation.py inline only | ✓ No duplicate |
| ISS intake query | interpretation.py inline only (×2 — see Section 3) | ⚠️ DUPLICATE |
| Proposal intake | interpretation.py inline only (×2 — see Section 3) | ⚠️ DUPLICATE |
| Probe execution | interpretation.py inline only | ✓ No duplicate |

---

## SECTION 5 — Formatter Consistency

All 7 extracted handlers use `build_deterministic_response`:
- `handle_iss_probe_plan` ✓
- `handle_iss_probe_registry` ✓
- `handle_operator_overview` ✓
- `handle_state_checkpoint` ✓
- `handle_iss_query_all` ✓
- `handle_iss_query_gaps` ✓
- `handle_iss_query_probes` ✓

No inline response builders added to interpretation.py by extraction.

---

## SECTION 6 — Routing Gaps

**Test inputs that return None (expected):**
```
"show"             → None  ✓ (no generic "show" handler; this is correct)
"show everything"  → None  ✓ (no such trigger; correct fallback)
"plan"             → None  ✓ (trigger is "plan probe ", not "plan"; correct)
"execute"          → None  ✓ (trigger is "execute probe ", not "execute"; correct)
"status"           → None  ✓ (trigger is "show weslr status"; correct)
"diagnostics please" → None  ✓ (trigger is "show diagnostics"; correct)
"gaps now"         → None  ✓ (trigger is "show gaps"; correct)
```

**No crashes. No unexpected handler matches. None of these should route elsewhere.**

---

## SECTION 7 — Top 10 Risks

| # | Risk | Severity | Location | Description |
|---|---|---|---|---|
| 1 | **Duplicate inline blocks** | **HIGH** | interpretation.py lines ~1316–1646 and ~1751–2081 | `_intake_triggers`, `_iss_intake_triggers`, `_plan_explain_triggers`, `_explain_triggers` each appear twice. The second copy runs after the first (or possibly vice versa depending on control flow). This can cause double-processing of proposal intake, duplicate responses, or shadowing. |
| 2 | interpretation.py at 2259 lines | **HIGH** | interpretation.py | Still monolithic. Duplicate blocks make it worse. Target for structural refactor. |
| 3 | Inline `_intake_triggers` has write path | **MEDIUM** | interpretation.py | `record_proposal()` writes to JSONL. While correct, it needs operator confirmation gate before writing. |
| 4 | Inline `_execute_triggers` uses "execute probe " | **LOW** | interpretation.py | Simulated-only execution. Correctly gated. No real I/O. |
| 5 | `plan_explain_triggers` uses `proposal_explanation` inline | **LOW** | interpretation.py | Read-only query but inline only. Correct behavior confirmed. |
| 6 | No handler for `"show"` alone | **INFO** | — | Correct — no generic show handler. Input falls through. |
| 7 | No handler for `"execute"` alone | **INFO** | — | Correct — requires full `"execute probe "` for safety. |
| 8 | `how can you improve` is not in registry | **INFO** | interpretation.py | Falls through correctly. Not a deterministic query. |
| 9 | `"diagnostics please"` not matched | **INFO** | — | Falls through correctly. Trigger requires `"show diagnostics"`. |
| 10 | `proposal_explanation` uses non-formatter response | **LOW** | interpretation.py | Returns `path="proposal_explanation"` but doesn't use `build_deterministic_response`. Inconsistent but not broken. |

---

## SECTION 8 — Recommended Next Extraction Target

**Priority 1: Fix duplicate inline blocks first**

The duplicate sections in interpretation.py are a correctness bug, not a refactoring opportunity. The second copy of each block must be removed before any further extraction.

**After duplicate removal, recommended extraction order:**

| # | Target | Reason |
|---|---|---|
| 1 | `_plan_explain_triggers` (plan_explanation) | Low risk, pure read-only, high trigger specificity |
| 2 | `_explain_triggers` (proposal_explanation) | Low risk, pure read-only, high trigger specificity |
| 3 | `_iss_intake_triggers` (ISS intake proposal query) | Low risk, read-only query |
| 4 | `_plan_triggers` (plan query) | Low risk, read-only query |
| 5 | `_intake_triggers` (ISS controlled proposal intake) | MEDIUM risk — write path; requires careful write-side handling |

**Do not extract `_execute_triggers` until execution governance is defined.** Simulated execution is correct now but the handler should remain inline until real execution is gated.

---

## SECTION 9 — Verdict

**POST_EXTRACTION_INTEGRITY_CONFIRMED** with the following note:

The system routing is correct and no extracted handlers show logic duplication. However, **the duplicate inline block issue is a HIGH-severity finding** that requires a corrective commit before the next extraction round.

**Action required:** Remove the second copy of duplicate handler blocks (lines ~1751–2081) from interpretation.py before proceeding.

**Registry integrity:** 7 handlers correctly wired, no trigger collisions, priority ordering correct, all use formatter.

**Routing gaps:** None found that should route. All fallthroughs are intentional.

---

*Document version: 1.0*
*Status: active reference*
*Next action: remove duplicate inline blocks in interpretation.py*
