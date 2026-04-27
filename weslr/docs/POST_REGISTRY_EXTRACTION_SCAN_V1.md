# WESLR Post-Registry Extraction Scan — V1

**Scan date:** 2026-04-27
**Commits inspected:** `50c1a69` (first extraction), `0834cb3` (second extraction)

---

## SECTION 1 — Scope

Files inspected:
- `interpretation.py` (1927 lines, was 1971 → cleaned by 44 lines net)
- `weslr/deterministic_handlers.py` (89 lines, new)
- `weslr/response_formatter.py` (from prior commit, confirmed in use)
- `weslr/docs/HANDLER_REGISTRY_DESIGN_V1.md`
- `weslr/docs/CANONICALITY_GAP_SCAN_V1.md`
- `weslr/docs/RESPONSE_CONTRACT_V1.md`

---

## SECTION 2 — Registry State

```
HANDLER_REGISTRY (2 entries, sorted desc by priority at dispatch)

[priority 85] iss_probe_plan
  id:         iss_probe_plan
  path:       ISS_probe_plan
  triggers:   ["plan probe ", "how would you check "]
  match_type:  prefix
  handler_fn:  handle_iss_probe_plan
  read_only:   True
  writes:      []
  requires_confirmation: False
  category:    iss

[priority 80] iss_probe_registry_query
  id:         iss_probe_registry_query
  path:       ISS_probe_registry_query
  triggers:   ["show iss probes", "show probe registry", "list probes", "what can iss check"]
  match_type:  prefix
  handler_fn:  handle_iss_probe_registry
  read_only:   True
  writes:      []
  requires_confirmation: False
  category:    iss
```

---

## SECTION 3 — interpretation.py State

**Current line count:** 1927 (was 1971 before first extraction)

**Removed inline handlers:**
- `_probe_triggers` block (lines 797–807 in old code) → replaced by registry dispatch for ISS_probe_registry_query
- `_plan_probe_triggers` block (lines 1685–1719 in old code) → replaced by registry dispatch for ISS_probe_plan

**Remaining inline deterministic handlers (13 groups):**
```
_plan_triggers           (line ~1027)  — plan query (C8)
_iss_triggers           (line ~1305)  — show diagnostics (ISS_query_gaps)
_ov_triggers           (line ~1363)  — operator overview
_intake_triggers       (line ~1420)  — accept gap / create proposal from gap
_iss_intake_triggers   (line ~1510)  — iss intake query
_plan_explain_triggers (line ~1582)  — plan explanation
_execute_triggers      (line ~1693)  — execute probe (ISS_probe_execution)
_explain_triggers      (line ~1748)  — proposal explanation
_ck_triggers          (line ~1843)  — state checkpoint
_capability_gaps_trigger (line ~871) — capability gaps (uses `in` check, not prefix)
_self_description_triggers — implicit via "who are you"/"what are you" in base turn
capability_list inline — implicit via "what can you do" in base turn
capability_proposal_ranked inline — via rank_capability_proposals()
```

**Dispatch call placement:** `dispatch_deterministic_handler(message, lowered)` at line 798 — called once after `lowered`/`lower_msg` are available and before inline deterministic handlers. Safe placement — no duplicate dispatch.

---

## SECTION 4 — Trigger/Order Risks After Extraction

| Check | Status | Notes |
|---|---|---|
| `plan probe` vs generic `plan` | **No risk** | iss_probe_plan priority 85 > C8 plan query; dispatch sorts before evaluation |
| `show iss probes` vs `show diagnostics`/`show gaps` | **No risk** | iss_probe_registry_query priority 80; ISS_query_gaps inline but separate trigger sets |
| `execute probe` still unchanged | **Correct** | _execute_triggers inline, confirmation-gated, appends to iss_diagnostic_records.jsonl |
| No handler shadowing introduced | **Confirmed** | iss_probe_plan priority 85 ensures it fires before any generic `plan` (priority 50 per design doc) |
| Dispatch sorts desc by priority | **Confirmed** | `sorted(..., key=lambda h: h["priority"], reverse=True)` at line 58 of deterministic_handlers.py |

---

## SECTION 5 — Behavior Drift Check

Route verification (all paths confirmed via test run):

| Input | Expected path | Result |
|---|---|---|
| `show iss probes` | ISS_probe_registry_query | OK |
| `show probe registry` | ISS_probe_registry_query | OK |
| `list probes` | ISS_probe_registry_query | OK |
| `what can iss check` | ISS_probe_registry_query | OK |
| `plan probe probe.front_door.chat` | ISS_probe_plan | OK |
| `how would you check probe.trace.proposals` | ISS_probe_plan | OK |
| `plan probe unknown.probe` | ISS_probe_plan (no-probe response) | OK |
| `execute probe probe.front_door.chat` | ISS_probe_execution | OK (inline, unchanged) |
| `show gaps` | ISS_query_gaps | OK (inline, unchanged) |
| `show implementation plans` | C8_plan_query_list | OK (inline, unchanged) |
| `how can you improve` | capability_gaps | OK* (uses `in` check, correct path) |
| `tell me about solar panels` | None | OK (open prompt) |

*`how can you improve` → `path=None` in raw dict return, but response_text is correctly populated via inline capability gaps handler. The handler builds its own response dict directly (not via `build_deterministic_response`), which is why `path=None` in the return — this is pre-existing behavior, not introduced by extraction.

---

## SECTION 6 — Response Formatter Use

| Handler | Uses response_formatter | Notes |
|---|---|---|
| handle_iss_probe_registry | **Yes** | build_deterministic_response |
| handle_iss_probe_plan | **Yes** | build_deterministic_response |
| All inline handlers | **No** | Build response dicts directly |

No response_text changes introduced by extraction. Both extracted handlers produce response_text identical to prior inline versions.

---

## SECTION 7 — Safety / Write Boundary Check

- Extracted handlers: `read_only=True`, `writes=[]` — confirmed
- `handle_iss_probe_plan` calls only `get_probe_registry()` + `create_probe_plan()` — both read-only
- JSONL line counts: proposal_trace=42, implementation_plans=5, iss_diagnostic_records=3 — **unchanged**
- Probe execution (`ISS_probe_execution`) remains inline only, confirmation-gated, appends to iss_diagnostic_records.jsonl
- No execution paths added or modified

---

## SECTION 8 — Remaining Architecture Risks

Updated from CANONICALITY_GAP_SCAN_V1.md:

| Risk | Status | Change |
|---|---|---|
| interpretation.py monolith | **Open** | 1927 lines still — 13 inline handler groups remain |
| Static state checkpoint | **Open** | get_state_checkpoint() still returns hardcoded dict |
| `_CAPABILITIES` staleness | **Open** | ISS: False still in interpretation.py |
| Missing JSON schemas | **Open** | No schemas yet for 4 JSONL record types |
| `load_implementation_plans` limit behavior | **Open** | No limit parameter — loads entire file |
| JSONL malformed-line risk | **Open** | No per-line error isolation |
| response_style migration incomplete | **Open** | Only 2 of ~15 handlers use response_formatter |
| No `no_handler_match` response | **Open** | dispatch returns None on no match; fallback is open prompt |
| Generic `plan ` overlap | **Mitigated** | Priority 85 ensures plan probe fires first |
| Handler ordering implicit in inline code | **Open** | 13 handler groups rely on relative line ordering |

---

## SECTION 9 — Recommended Next Step

**C) Response formatter migration**

Rationale: The two extracted handlers already use `build_deterministic_response`. The next logical step is to migrate one or two inline handlers that have simple, branching-free response_text construction — specifically `ISS_query_gaps` or `operator_overview` — to prove the formatter can handle slightly more complex payloads. This:
- Validates the formatter's utility on a real handler without the complexity of branching logic
- Establishes a migration pattern before tackling the more complex branching handlers
- Doesn't require resolving `_CAPABILITIES` staleness or schema issues first
- Is independent of the monolith problem (which requires a bigger refactor session)

**Why not A (continue extraction)?** With 2 handlers extracted, the immediate value is demonstrated. Continuing extraction without first establishing a broader migration pattern means the remaining 13 handlers will be extracted one-by-one into the same pattern without systemic improvement. The formatter migration is a prerequisite for clean extraction of more complex handlers.

**Why not B (schemas first)?** Schemas are important but blocking on them stops forward momentum. Schemas can be written in parallel after a migration pattern is established.

**Why not D (capability map extraction)?** `_CAPABILITIES` extraction requires resolving `ISS: False` staleness and would touch a wider surface area than the formatter migration.

---

## SECTION 10 — Top 10 Findings

1. **Extraction clean**: 2 handlers cleanly extracted, behavior-identical, committed in `50c1a69` and `0834cb3`
2. **Dispatch placement safe**: `dispatch_deterministic_handler` at line 798 runs before any inline handlers — no double-fire, no shadowing
3. **Priority order correct**: iss_probe_plan (85) > iss_probe_registry_query (80) > inline handlers — no regression introduced
4. **JSONL line counts unchanged**: 42 / 5 / 3 — no accidental writes from extracted handlers
5. **interpretation.py still a monolith**: 1927 lines, 13 inline handler groups — far from the HANDLER_REGISTRY_DESIGN_V1 intent
6. **No `no_handler_match` response**: dispatch returns `None` on no match — no structured "not matched" response exists yet
7. **`how can you improve` uses `in`-check not prefix**: not prefix-based, returns `path=None` — this is pre-existing inline behavior, not introduced by extraction
8. **All inline handlers still bypass response_formatter**: only extracted handlers use `build_deterministic_response` — response skeleton inconsistency grows
9. **`_CAPABILITIES` staleness unresolved**: `ISS: False` in capability map but ISS subsystem fully exists — this is documented but not fixed
10. **Generic `plan ` overlap risk remains**: `_plan_triggers` = `["plan"]` at priority ~50 per design doc; with plan probe at 85 the risk is mitigated, but if a third generic `plan` trigger were added at higher priority it would shadow plan probe

---

## SECTION 11 — Verdict

**POST_REGISTRY_EXTRACTION_SCAN_CONFIRMED**

Two ISS probe handlers cleanly extracted and behavior-validated. interpretation.py monolith still has 13 inline handler groups. Priority ordering confirmed correct. No write boundary violations. Next logical step: response formatter migration to establish a systemic pattern before further extraction.

---

*Document version: 1.0*
*Scan status: canonical reference*
*Next step: response formatter migration — ISS_query_gaps or operator_overview as first target*
