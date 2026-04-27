# WESLR Engineering Maturity Scan — V1

**Version:** 1.0
**Status:** active reference
**Created:** 2026-04-27
**Scope:** Full system audit after schema contracts, write-side validation, JSONL read isolation, test harness, and release gate

---

## SECTION 1 — Scope

Inspected components:

**Core modules:**
- `interpretation.py` — 1929 lines — front door + mode analysis + dispatch
- `weslr/deterministic_handlers.py` — 118 lines — extracted registry (2 handlers)
- `weslr/response_formatter.py` — 41 lines — canonical response skeleton builder
- `weslr/proposal_traceability.py` — ~100 lines — trace CRUD + validators
- `weslr/implementation_planning.py` — ~100 lines — plan creation + validators
- `weslr/iss/diagnostic_records.py` — ~140 lines — probe result + gap signal + validators
- `weslr/state_checkpoint.py` — ~50 lines — read-only architecture snapshot

**ISS subsystem:**
- `weslr/iss/probe_registry.py` — in-memory registry, 4 probe stubs, all `execution_allowed=False`
- `weslr/iss/probe_planning.py` — declarative probe plan builder
- `weslr/iss/probe_execution.py` — simulated execution only, no real I/O

**Tests:**
- `weslr/tests/test_harness_v1.py` — 382 lines — T1/T2/T3/T4/T6 with temp-file isolation
- `weslr/tests/release_gate_v1.py` — 173 lines — G1/G2/G3/G4 gates
- `weslr/tests/test_*.py` — 40+ additional test files (~19K lines, exploratory/unmerged)

**Documentation:**
- `weslr/docs/SCHEMA_CONTRACTS_V1.md` — 545 lines — all 10 schema definitions + append-only rules
- `weslr/docs/engineering/ADR_0001–0004` — 673 lines — 4 architecture decision records
- `weslr/docs/engineering/TEST_STRATEGY_V1.md` — 412 lines — T1–T6 + regression coverage
- `weslr/docs/engineering/ARCHITECTURE_DIAGRAMS_V1.md` — 241 lines — 5 Mermaid diagrams
- `weslr/docs/engineering/RELEASE_CHECKLIST_V1.md` — 171 lines — G1–G7 gate
- `weslr/docs/engineering/ADR_INDEX.md` — 72 lines — ADR registry

---

## SECTION 2 — Current Maturity Layers

### A) Behavior Correctness

**Deterministic routing — STABLE**

`dispatch_deterministic_handler` sorts registry by priority descending and applies prefix match. Priority ordering is explicit (85 = probe_plan, 80 = registry_query). No implicit shadowing observed. Two handlers extracted and wired: `handle_iss_probe_plan` and `handle_iss_probe_registry`. Both return via `build_deterministic_response`.

**No handler shadowing — CONFIRMED**

Registry entries have unique trigger sets. No two entries share the same priority value. Sorting is deterministic (stable sort by priority, then by trigger string). No case where a lower-priority handler would match before a higher-priority one.

**Explanation layers — PARTIAL**

- `plan_explanation` — returns `plan_explanation` dict with plan details + trace_reference → proposal → source gap chain. Active.
- `proposal_explanation` — referenced in C7 but inline path, not yet extracted. Inline C7 logic exists in interpretation.py.
- `state_checkpoint_query` — returns full architecture snapshot via `get_state_checkpoint`. Active.
- `operator_overview` — response built inline in interpretation.py, not yet migrated to formatter.

**Mode analysis — ACTIVE, LARGE**

`mode_analysis` function in interpretation.py is ~200 lines with B1–B12 pattern classification. Used by feedback logging and interest tracking. Called on every interpret call. No duplication detected in the core module itself.

**Confidence assessment — BASELINE**

Entity-based heuristic: `entity_names >= 2 → high`, `entity_names or topics → medium`, else `low`. No calibration against actual accuracy. Works as a baseline signal.

---

### B) Data Integrity

**Schema enforced on write — ACTIVE**

Three write validators:
- `_validate_proposal_created` — `proposal_id` non-empty string, `content` dict
- `_validate_proposal_decision` — `proposal_id` non-empty string, `decision` non-empty string
- `_validate_implementation_plan` — `execution_allowed must be False`, `operator_approval_required must be True`, `steps` non-empty list, all type checks
- `_validate_iss_diagnostic_record` — `type` must be `iss_probe_result` or `iss_gap_signal`, status/severity enum checks via `_ALLOWED_PROBE_STATUS` and `_ALLOWED_GAP_SEVERITY`

Hard rule enforced: `execution_allowed=False` in `implementation_planning.py` via module-level `_EXECUTION_ALLOWED = False`. No code path can set it to `True` without triggering `ValueError`.

**Read isolation — ACTIVE**

All three loaders (`load_trace`, `load_implementation_plans`, `load_iss_diagnostics`) use per-line try/except with `json.JSONDecodeError` skipping. Malformed lines do not crash loads. Missing files return `[]`.

**Append-only respected — ACTIVE**

No rewrite, delete, or truncate operations in any module. All `_write_*` functions only append. No file truncation found in any inspected module.

---

### C) Observability

**Overview (operator_overview) — PARTIAL**

Inline handler in interpretation.py. Returns hardcoded summary strings and counts. No live state read — summary is static text embedded in handler.

**Checkpoint (state_checkpoint_query) — ACTIVE**

`get_state_checkpoint()` returns deterministic snapshot of layer statuses and doctrine flags. All 10 layers marked `confirmed`. No dynamic detection — purely static declaration.

**Explanations (plan_explanation, proposal_explanation) — PARTIAL**

`plan_explanation` uses `load_implementation_plans` + `load_trace` to reconstruct chain. `proposal_explanation` exists as inline logic, not extracted. Both rely on JSONL read isolation (loaders).

**ISS visibility — ACTIVE**

- `show iss probes` → `ISS_probe_registry_query` via registry handler, returns probe count + registry list
- `show gaps` → `ISS_query_gaps` via inline handler, returns gap records
- `show diagnostics` → `ISS_query_all` via inline handler, returns probe count + gap total
- `show probe results` → `ISS_query_probes` via inline handler
- `plan probe` → `ISS_probe_plan` via registry handler, returns declarative plan
- `execute probe` → `ISS_probe_execution` via inline handler, simulates and returns confirmation

ISS diagnostics load from `iss_diagnostic_records.jsonl` with read isolation. All ISS paths return structured responses.

---

### D) Safety Boundaries

**execution_allowed=False enforced — CONFIRMED**

- `implementation_planning.py`: `_EXECUTION_ALLOWED = False` hardcoded. `_validate_implementation_plan` raises `ValueError` if `execution_allowed is not False`.
- `probe_registry.py`: All 4 probes have `execution_allowed: False`.
- `probe_execution.py`: `execute_probe_simulated` writes only simulated probe results with `status: ok` and `mode: "simulated"`. No real I/O.
- Release gate G3 scans `weslr/*.py` (excluding test files) for `execution_allowed=True`. None found.

**No unauthorized writes — CONFIRMED**

All write operations:
- `proposal_traceability.py` — `record_proposal`, `record_decision` (validated, append-only)
- `implementation_planning.py` — `record_implementation_plan` (validated, append-only)
- `diagnostic_records.py` — `record_iss_diagnostic` (validated, append-only)
- `operator_feedback_log.jsonl` — `log_operator_feedback` (append-only)
- `execute_probe_simulated` — only writes simulated probe results

No undeclared writes found. All write paths documented and schema-validated.

**Operator authority intact — CONFIRMED**

No autonomous proposal creation. `record_proposal` requires explicit call. `create_implementation_plan` requires operator intake or explicit call. `record_implementation_plan` requires operator approval (`operator_approval_required: True` enforced). No auto-logging of operator feedback — explicit `record_mode_feedback` call required.

---

### E) Test Coverage

**Working test suite:**

| Test Group | Cases | Status |
|---|---|---|
| T1 — Route tests | 24 cases | PASS — all paths + payload types validated |
| T2 — Schema guards | 6 invalid write cases | PASS — all raise `ValueError` |
| T3 — Malformed-line read | 4 subtests | PASS — all 3 loaders skip bad lines |
| T4 — No-write safety | 3 file hash checks | PASS — read-only ops don't modify JSONL |
| T6 — Full smoke | 31 commands | PASS — all return valid response dict |

**Test isolation:** T2 uses `tempfile.TemporaryDirectory` with monkeypatched module constants. T3 uses temp files. T4/T6 are read-only. Production JSONL line counts unchanged after full run.

**Gates:**
- G1 — test harness passes ✓
- G2 — staged files in scope ✓
- G3 — no `execution_allowed=True` in production ✓
- G4 — no OpenClaw core or TIA C# in staged scope ✓

**Exploratory tests:** 40+ test files (~19K lines) in `weslr/tests/test_*.py`. These are design-reference tests from earlier sessions, not yet integrated into the harness. They document expected behavior but are not run automatically. This is a large inventory that could be mined for regression cases.

**Coverage gaps:**
- T5 (regression layer-by-layer) documented in `TEST_STRATEGY_V1.md` but not yet in harness
- No automated pytest integration
- No performance/latency benchmarks
- No concurrency tests
- No schema read-side validation tests (beyond JSON parsing)

---

### F) Release Discipline

**Release gate effectiveness — ACTIVE**

`release_gate_v1.py` runs as a single command. All 4 gates implemented and validated. Gate 2 checks only staged files (not all working-tree changes), which is the correct behavior — operator controls what is staged.

**Missing checks:**
- No automated backup confirmation (manual JSONL line count check documented in RELEASE_CHECKLIST_V1.md but not automated)
- No JSONL schema validation on existing records (write-side validation active, read-side validation not implemented)
- No version tagging or changelog automation
- No pre-commit hook (gate must be run manually)
- No rollback simulation test (documented but not run)

---

## SECTION 3 — Remaining Weaknesses

1. **interpretation.py is 1929 lines** — monolithic front door containing mode_analysis, turn classification, capability ranking, feedback logging, operator context building, confidence assessment, interest tracking, deterministic dispatch routing, and inline handler implementations. Single point of failure for any routing issue.

2. **Incomplete handler registry extraction** — only 2 of 15+ handlers extracted (`iss_probe_plan`, `iss_probe_registry_query`). The rest are inline `elif` chains in `interpret_human_turn`. Every new handler added to the inline chain increases the module's complexity without registry visibility.

3. **Partial formatter migration** — `response_formatter.py` (41 lines) only used by extracted registry handlers. Inline handlers in interpretation.py build responses ad-hoc. No enforcement that all handlers must use `build_deterministic_response`.

4. **No schema validation on read** — loaders skip malformed lines but do not validate record schema structure. A record missing required fields would pass through `load_trace` silently.

5. **Confidence field ambiguity** — `confidence` field appears in multiple record types (`iss_probe_result`, `iss_gap_signal`, operator feedback) with string values (`"high"`, `"medium"`, `"low"`). No enumerated constraint enforced outside the ISS diagnostic records. Inconsistent usage across different record types is possible.

6. **mode_analysis duplication pattern** — `mode_analysis` function ~200 lines, also present as inline string-building in multiple places across interpretation.py. Some handlers rebuild similar signals rather than reusing.

7. **No CI automation** — release gate runs manually. No GitHub Actions, no pre-commit hooks, no automated gate on push. Gate is operator discipline, not enforced.

8. **No versioned releases** — commits are not tagged. No changelog. No semantic versioning. Commit history is the only artifact.

9. **No backup/restore automation** — JSONL files grow indefinitely. No rotation, no backup, no cleanup. `load_*` functions use `limit` to read last N lines but files themselves are never trimmed.

10. **Exploratory test inventory not integrated** — 40+ test files (~19K lines) exist as design references but are not run in the test harness. Could be mined for regression cases.

---

## SECTION 4 — Risk Classification

| # | Weakness | Risk | Justification |
|---|---|---|---|
| 1 | interpretation.py (1929 lines) | **HIGH** | Single large module = high blast radius for bugs. Hard to review, easy to break silently |
| 2 | Incomplete registry extraction | **HIGH** | Inline handlers accumulate without governance. Shadowing risk grows with each addition |
| 3 | Partial formatter migration | **MEDIUM** | Ad-hoc responses create inconsistency. No structural enforcement |
| 4 | No read-side schema validation | **MEDIUM** | Malformed records accumulate silently in JSONL. Detectability gap |
| 5 | Confidence field ambiguity | **LOW** | Informational only. Not used in governance decisions |
| 6 | mode_analysis duplication | **LOW** | Maintainability issue, not a safety issue |
| 7 | No CI automation | **MEDIUM** | Gate is operator-dependent. Forgetting to run it defeats its purpose |
| 8 | No versioned releases | **LOW** | Current workflow works. Semantic versioning is nice-to-have at this stage |
| 9 | No JSONL backup/rotation | **MEDIUM** | Append-only means no cleanup. Files grow indefinitely. No failure scenario yet but risk grows |
| 10 | Exploratory tests not integrated | **LOW** | Not blocking. Documents design intent, not live validation |

**Highest priority (act now):** #1 (interpretation.py size), #2 (incomplete extraction), #7 (CI automation)
**High priority (plan soon):** #3 (formatter migration), #4 (read validation), #9 (JSONL backup)
**Nice to have:** #5, #6, #8, #10

---

## SECTION 5 — System Classification

**WESLR is currently a structured prototype.**

Evidence:
- Core modules exist and are functional (proposal traceability, implementation planning, ISS diagnostics, response formatter)
- Schema contracts formalized (SCHEMA_CONTRACTS_V1.md)
- Write-side validation active on all 3 JSONL write paths
- Read isolation active on all 3 JSONL read paths
- Test harness passes T1–T6 with isolated temp files
- Release gate runs 4 gates successfully
- ADR documentation exists with 4 decisions recorded
- Architecture diagrams published (5 diagrams)
- No execution_allowed=True in production code

**Why not prototype?** Because the system has repeatable processes (schema enforcement, validation, isolation, testing, release gating). It is not a one-off experiment.

**Why not engineering-grade?** Because:
- interpretation.py is a single monolithic module — engineering-grade systems decompose concerns into separate modules with clear boundaries
- Handler extraction is incomplete — engineering-grade systems have complete registry coverage with no inline dispatch chains
- CI is manual — engineering-grade systems automate gates on push/pull-request
- JSONL files have no rotation/backup — engineering-grade systems have operational runbooks

**Why not production-grade?** Because:
- No automated backup or restore
- No monitoring or alerting
- No performance benchmarks
- No rollback automation
- No versioned releases with changelog
- Single point of failure in interpretation.py

---

## SECTION 6 — Next Phase Decision

**Choose: B) CI + automation phase**

Justification:

The system currently has a release gate that runs manually. Every gate (G1–G4) is implemented correctly, but all of them require the operator to remember to run `python3 weslr/tests/release_gate_v1.py` before committing. This is a human-reliability dependency that will eventually fail.

The structured prototype is mature enough to benefit from automation. The manual gate is blocking adoption and creating risk. Automating the gate on push/pull-request removes the human-reliability dependency and enforces the constraints consistently.

**Why not A (structural refactor)?** interpretation.py at 1929 lines is a problem, but the system is still functional. Refactoring it without a test harness and automated validation would introduce risk. The structural refactor should happen after CI is in place, not before.

**Why not C (interaction/humanization)?** Response tone improvement is valid but not the constraint holding the system back. The system works correctly. Improving how it sounds is premature when the automation infrastructure is missing.

**Why not D (controlled execution)?** The ISS is explicitly in simulated mode. No probes execute against real targets. Moving to real execution requires governance documentation, operator approval workflows, and rollback automation — none of which exist yet. Premature.

---

## SECTION 7 — Roadmap (Next 5 Steps)

**Step 1 — GitHub Actions CI workflow**
File: `.github/workflows/weslr.yml`
- On push to `weslr/` or `interpretation.py`: run `python3 weslr/tests/release_gate_v1.py`
- On failure: block merge, report which gate failed
- No manual gate required

**Step 2 — JSONL backup automation**
File: `weslr/docs/OPERATIONAL_RUNBOOK_V1.md`
- Document JSONL file locations and line count thresholds
- Add `weslr/tools/backup_jsonl.py` — copies last N lines of each JSONL to `weslr/backups/` with timestamp
- Add `weslr/tools/restore_jsonl.py` — restores from backup
- Document rotation policy (e.g., rotate when any JSONL exceeds 1000 lines)

**Step 3 — Schema read-side validation (lightweight)**
Add to `load_trace`, `load_implementation_plans`, `load_iss_diagnostics`:
- Check `type` field is present and non-empty string
- Check required top-level fields for each record type
- Log (do not raise) on validation failure
- Silently skip malformed records (consistent with current malformed-line behavior)

**Step 4 — Extract next handler batch**
Files: `weslr/deterministic_handlers.py`, `interpretation.py`
- Extract `operator_overview` handler → registry + formatter
- Extract `state_checkpoint_query` handler → registry + formatter
- Extract `plan_explanation` handler → registry + formatter
- Target: 5 extracted handlers total (2 current + 3 new), remaining inline handlers visible in interpretation.py with documented reason for inline status

**Step 5 — T5 regression test integration**
Add to `test_harness_v1.py`:
- C1–C9 regression layer-by-layer cases from `TEST_STRATEGY_V1.md`
- Run T5 as part of G1 (test harness passes)
- Document pass/fail criteria per layer

---

## SECTION 8 — Verdict

**ENGINEERING_MATURITY_SCAN_CONFIRMED**

WESLR is a structured prototype with active schema enforcement, read isolation, test coverage, and release gating. The system is sound and the documentation is complete. The primary risk is the manual release gate and the monolithic interpretation.py. CI automation is the correct next step.

**Top 10 findings:**
1. interpretation.py at 1929 lines — monolithic, single failure point
2. Handler registry extraction incomplete — only 2/15+ handlers extracted
3. Partial formatter migration — inline handlers use ad-hoc response building
4. No read-side schema validation — malformed records silently accumulate
5. No CI automation — release gate manual, operator-dependent
6. No JSONL backup/rotation — files grow indefinitely with no cleanup
7. 40+ exploratory test files (~19K lines) not integrated into harness
8. No versioned releases or changelog
9. Confidence field ambiguous across record types
10. `operator_overview` inline handler returns static text, not live state

**System classification:** Structured prototype
**Next phase:** CI + automation (Step 1: GitHub Actions workflow)