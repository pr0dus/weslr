# WESLR Extraction Status Scan V1
**Generated:** 2026-04-27 19:11 GMT+2
**Scope:** Handler extraction audit after plan query extraction (commit 6387e7f)

---

## 1. Registry Inventory

All handlers are dispatched through `dispatch_deterministic_handler()` from the registry in `weslr/deterministic_handlers.py`.

| # | id | path | priority | triggers | read_only | writes | category |
|---|-----|------|----------|---------|----------|--------|----------|
| 1 | `iss_probe_plan` | `ISS_probe_plan` | 85 | `plan probe `, `how would you check ` | ✅ | — | iss |
| 2 | `plan_explanation` | `plan_explanation` | 73 | `explain plan `, `why was plan `, `why does plan ` | ✅ | — | explanation |
| 3 | `proposal_explanation` | `proposal_explanation` | 72 | `why is `, `explain proposal `, `why prioritize ` | ✅ | — | explanation |
| 4 | `plan_query_single` | `C8_plan_query_single` | 71 | `show plan for `, `get plan for ` | ✅ | — | plan |
| 5 | `iss_probe_registry_query` | `ISS_probe_registry_query` | 80 | `show iss probes`, `show probe registry` | ✅ | — | iss |
| 6 | `operator_overview` | `operator_overview` | 75 | `show system overview` | ✅ | — | operator |
| 7 | `state_checkpoint_query` | `state_checkpoint_query` | 74 | `show weslr status` | ✅ | — | state |
| 8 | `plan_query_list` | `C8_plan_query_list` | 70 | `show implementation plans`, `list plans`, `show plans` | ✅ | — | plan |
| 9 | `iss_query_all` | `ISS_query_all` | 70 | `show diagnostics` | ✅ | — | iss |
| 10 | `iss_query_gaps` | `ISS_query_gaps` | 69 | `show gaps` | ✅ | — | iss |
| 11 | `iss_query_probes` | `ISS_query_probes` | 68 | `show probe results` | ✅ | — | iss |

**Total registry entries:** 11

**All 11 registry entries are `read_only=True` with empty `writes=[]`.**

---

## 2. Remaining Inline Blocks in interpretation.py

Three blocks remain inline at the bottom of `interpret_human_turn()`:

### Block A — ISS Controlled Proposal Intake
| Field | Value |
|-------|-------|
| Location | `interpretation.py:1228–1315` |
| Trigger var | `_intake_triggers` |
| Triggers | `convert iss suggestion `, `convert iss gap `, `create proposal from iss `, `turn iss gap ` |
| Path | `ISS_controlled_proposal_intake` |
| Read/Write | **WRITE** — calls `record_proposal()` → writes to `proposal_trace.jsonl` |
| Risk Level | **HIGH** — creates proposal records on operator request |
| Rationale for staying inline | Proposal creation is a governed write operation; requires operator context and approval flow |

### Block B — ISS Intake Proposal Query
| Field | Value |
|-------|-------|
| Location | `interpretation.py:1318–1377` |
| Trigger var | `_iss_intake_triggers` |
| Triggers | `show iss intake proposals`, `show proposals from iss`, `show converted iss proposals`, `list iss proposals` |
| Path | `ISS_intake_query` |
| Read/Write | **READ-ONLY** — loads trace, no writes |
| Files Read | `proposal_trace.jsonl` |
| Files Written | None |
| Risk Level | **LOW** — read-only query |
| Note | Supports only the exact trigger `"show iss intake proposals"`; `show intake proposals` alone does NOT match |

### Block C — ISS Probe Execution
| Field | Value |
|-------|-------|
| Location | `interpretation.py:1393–1448` |
| Trigger var | `_execute_triggers` |
| Triggers | `execute probe ` |
| Path | `ISS_probe_execution` |
| Read/Write | **SIMULATED** — calls `execute_probe_simulated()` which returns mock results, does not write files |
| Files Written | None (simulated mode only) |
| Risk Level | **MEDIUM** — simulated execution is safe but governed by confirmation pattern |
| Note | Requires `confirm` suffix; mode is explicitly `"simulated"` |

---

## 3. Monolith Status

| Metric | Value |
|--------|-------|
| `interpretation.py` line count | 1448 |
| `deterministic_handlers.py` line count | 680 |
| Handlers extracted to registry | 11 |
| Handlers remaining inline | 3 |
| Total handlers (extracted + inline) | 14 |

**Extraction progress:** 11/14 extracted (79%)

---

## 4. Behavior Safety

**Release gate (this session):**

```
GATE 1: test harness passed
GATE 2: no files staged — nothing to check
GATE 3: no execution_allowed=True in production weslr/*.py
GATE 4: no OpenClaw core or TIA C# in staged scope

WESLR_RELEASE_GATE_V1_OK
```

**No behavioral changes introduced in this session.**

---

## 5. Trigger Overlap Scan

Registry trigger strings vs. remaining inline trigger strings:

| Registry Trigger | Inline Trigger | Overlap? |
|-----------------|----------------|---------|
| `show implementation plans` | `convert iss suggestion ` | None |
| `show iss probes` | `execute probe ` | None |
| `show gaps` | `show iss intake proposals` | None |
| `explain plan ` | `show proposals from iss` | None |
| `why is ` | `create proposal from iss` | None |

**No overlaps detected.** Inline triggers are distinct strings not covered by any registry entry.

**Note on Block B (ISS_intake_query):** The trigger `"show iss intake proposals"` is narrowly defined. Phrases like `"show intake proposals"` or `"list iss proposals"` do NOT match — this is a pre-existing gap, not an extraction artifact.

---

## 6. Next Extraction Recommendation

**Recommended: A — ISS intake proposal query (read-only, Block B)**

### Rationale

| Option | Reason |
|--------|--------|
| **A (ISS intake query)** | Pure read-only, no writes, cleanly separable, identical pattern to previously extracted handlers |
| B (probe execution) | Simulated mode but confirmation-gated; extraction boundary is murkier |
| C (intake conversion) | **WRITE operation** — creates records; should stay inline until write-handler protocol is defined |
| D (stop + profile) | Premature without evidence of performance problem |

**Block B** (`ISS_intake_query`, lines 1318–1377) is the lowest-risk next extraction:
- No writes
- Same `load_trace()` pattern as `ISS_query_all` already in registry
- Triggers are narrowly defined, behavior is deterministic
- Removing it reduces `interpretation.py` by ~60 lines

---

## 7. Performance Note

Extraction moves query logic from `interpretation.py` into `deterministic_handlers.py`. This improves:

- **Modularity** — handlers are independently testable
- **Discoverability** — registry is a single source of truth for all read-only handlers
- **Auditability** — read vs. write boundary is explicit per entry

**Speed improvement is not guaranteed.** `interpretation.py` still imports and calls `dispatch_deterministic_handler()` at line ~798. The net effect on latency is:
- Slightly faster: handler lookup is O(n) sorted by priority, no-op branches eliminated from main flow
- Slightly slower: one extra function call indirection through `globals().get()`

**Actual speed impact requires profiling** (not performed here). The extraction is architecturally sound regardless.

---

## 8. Summary

| Item | Value |
|------|-------|
| Registry handlers | 11 (all read-only) |
| Inline handlers | 3 (1 write, 1 read-only, 1 simulated) |
| Extraction progress | 79% (11 of 14) |
| Unresolved inline writes | 1 (`ISS_controlled_proposal_intake`) |
| Next recommended extraction | Block B — `ISS_intake_query` (read-only, ~60 lines) |
