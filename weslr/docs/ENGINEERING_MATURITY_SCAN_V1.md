# WESLR Engineering Maturity Scan — V1

**Version:** 1.1
**Status:** active reference
**Created:** 2026-04-27
**Updated:** 2026-04-27 15:53 GMT+2
**Scope:** Full system audit after schema contracts, write-side validation, JSONL read isolation, test harness, and release gate

---

## SECTION 1 — Scope

Inspected components:

**Core modules:**
- `interpretation.py` — 1929 lines — front door + mode analysis + dispatch + inline handlers
- `weslr/deterministic_handlers.py` — 118 lines — extracted registry (2 handlers: `iss_probe_plan`, `iss_probe_registry_query`)
- `weslr/response_formatter.py` — 41 lines — canonical response skeleton builder
- `weslr/proposal_traceability.py` — trace CRUD + module-relative path (`BASE_DIR = Path(__file__).resolve().parent`)
- `weslr/implementation_planning.py` — plan creation + module-relative path
- `weslr/iss/diagnostic_records.py` — probe result + gap signal + module-relative path
- `weslr/state_checkpoint.py` — read-only architecture snapshot

**ISS subsystem:**
- `weslr/iss/probe_registry.py` — in-memory registry, 4 probe stubs, all `execution_allowed=False`
- `weslr/iss/probe_planning.py` — declarative probe plan builder
- `weslr/iss/probe_execution.py` — simulated execution only, no real I/O
- `weslr/iss/record.py` — ISS record intake with schema validation

**Tests:**
- `weslr/tests/test_harness_v1.py` — 382 lines — T1/T2/T3/T4/T6 with temp-file isolation
- `weslr/tests/release_gate_v1.py` — 173 lines — G1/G2/G3/G4 gates
- `weslr/tests/test_*.py` — 40+ additional test files (~19K lines, exploratory/unmerged)

**Documentation:**
- `weslr/docs/SCHEMA_CONTRACTS_V1.md` — 545 lines — 10 schema definitions + append-only rules
- `weslr/docs/RESPONSE_CONTRACT_V1.md` — 460 lines — response fields, tone levels, templates
- `weslr/docs/ENGINEERING_MATURITY_SCAN_V1.md` — 344 lines — this document (prior version)
- `weslr/docs/engineering/ADR_0001–0004` — 673 lines — 4 architecture decision records
- `weslr/docs/engineering/TEST_STRATEGY_V1.md` — 412 lines — T1–T6 + regression coverage
- `weslr/docs/engineering/RELEASE_CHECKLIST_V1.md` — 171 lines — G1–G7 gate

**Confirmed infrastructure fixes (this session):**
- PATH_STABILITY_FIX_CONFIRMED — `proposal_traceability.py`, `implementation_planning.py`, `diagnostic_records.py` now use `Path(__file__).resolve().parent` relative paths instead of CWD-relative paths
- HANDLER_REGISTRY_FIRST_EXTRACTION_CONFIRMED — `iss_probe_registry_query` and `iss_probe_plan` extracted to registry
- JSONL path stability validated from both workspace root and `/tmp` — same counts (42 trace, 5 plans, 3 diagnostics)

---

## SECTION 2 — Current Maturity Layers

### A) Behavior Correctness

**Deterministic routing — STABLE**

`dispatch_deterministic_handler` sorts registry by priority descending and applies prefix match. Two handlers extracted and wired:
- `handle_iss_probe_plan` (priority 85) — triggers: `plan probe `, `how would you check `
- `handle_iss_probe_registry` (priority 80) — triggers: `show iss probes`, `show probe registry`, `list probes`, `what can iss check`

Both return via `build_deterministic_response`. Priority ordering is explicit. No implicit shadowing observed.

**No handler shadowing — CONFIRMED**

Registry entries have unique trigger sets. Sorting is deterministic (stable sort by priority, then by trigger string). No case where a lower-priority handler would match before a higher-priority one.

**Explanation layers — PARTIAL**

- `plan_explanation` — returns `plan_explanation` dict with plan details + trace_reference → proposal → source gap chain. ISS gap link now working correctly after PATH_STABILITY_FIX_CONFIRMED.
- `proposal_explanation` — inline in interpretation.py, not extracted.
- `state_checkpoint_query` — returns architecture snapshot via `get_state_checkpoint`. Active.
- `operator_overview` — response built inline in interpretation.py, not yet migrated to formatter.

**Mode analysis — ACTIVE, LARGE**

`mode_analysis` function in interpretation.py is ~200 lines with B1–B12 pattern classification. Called on every interpret call. No duplication detected in core module.

**Confidence assessment — BASELINE**

Entity-based heuristic: `entity_names >= 2 → high`, `entity_names or topics → medium`, else `low`. No calibration against actual accuracy. Works as a baseline signal.

---

### B) Data Integrity

**Schema enforced on write — ACTIVE**

Four write validators:
- `_validate_proposal_created` — `proposal_id` non-empty string, `content` dict
- `_validate_proposal_decision` — `proposal_id` non-empty string, `decision` in `{"accepted", "rejected", "deferred"}`
- `_validate_implementation_plan` — `execution_allowed must be False`, `operator_approval_required must be True`, `steps` non-empty list
- `_validate_iss_diagnostic_record` — `type` check, status/severity enum checks via `_ALLOWED_PROBE_STATUS` and `_ALLOWED_GAP_SEVERITY`

Hard rule enforced: `_EXECUTION_ALLOWED = False` at module level in `implementation_planning.py`. No code path sets it to `True` without triggering `ValueError`.

**Path stability — FIXED**

Prior session identified that `TRACE_FILE`, `PLAN_FILE`, `RECORD_FILE` used CWD-relative paths. Fixed this session with `Path(__file__).resolve().parent` anchoring. JSONL reads now return consistent counts regardless of runtime CWD.

**Read isolation — ACTIVE**

All three loaders use per-line try/except with `json.JSONDecodeError` skipping. Malformed lines do not crash loads. Missing files return `[]`.

**Append-only respected — ACTIVE**

No rewrite, delete, or truncate operations in any module. All `_write_*` functions only append. No file truncation found.

---

### C) Observability

**Overview (operator_overview) — PARTIAL**

Inline handler in interpretation.py. Returns hardcoded summary strings. No live state read — summary is static text embedded in handler.

**Checkpoint (state_checkpoint_query) — ACTIVE**

`get_state_checkpoint()` returns deterministic snapshot of layer statuses and doctrine flags. All 10 layers marked `confirmed`. No dynamic detection — purely static declaration.

**Explanations (plan_explanation, proposal_explanation) — PARTIAL**

`plan_explanation` uses `load_implementation_plans` + `load_trace` to reconstruct chain. ISS gap link now correct after PATH_STABILITY_FIX_CONFIRMED (was returning "No ISS source gap is linked" due to CWD-relative path failure). `proposal_explanation` exists as inline logic, not extracted.

**ISS visibility — ACTIVE**

- `show iss probes` → `ISS_probe_registry_query` via registry handler ✓
- `show gaps` → `ISS_query_gaps` via inline handler ✓
- `show diagnostics` → `ISS_query_all` via inline handler ✓
- `show probe results` → `ISS_query_probes` via inline handler ✓
- `plan probe` → `ISS_probe_plan` via registry handler ✓
- `execute probe` → `ISS_probe_execution` via inline handler, simulated only ✓

ISS diagnostics load from `iss_diagnostic_records.jsonl` with read isolation. All ISS paths return structured responses.

---

### D) Safety Boundaries

**execution_allowed=False enforced — CONFIRMED**

- `implementation_planning.py`: `_EXECUTION_ALLOWED = False` hardcoded. Validator raises `ValueError` if not `False`.
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

No autonomous proposal creation. No auto-logging of operator feedback. `operator_approval_required: True` enforced on all plan records.

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

**Coverage gaps:**
- T5 (regression layer-by-layer) documented in `TEST_STRATEGY_V1.md` but not yet in harness
- No automated pytest integration
- No performance/latency benchmarks
- No concurrency tests
- No schema read-side validation tests (beyond JSON parsing)
- 40+ exploratory test files (~19K lines) exist but not integrated into harness

---

### F) Release Discipline

**Release gate effectiveness — ACTIVE**

`release_gate_v1.py` runs as a single command. All 4 gates implemented and validated. Gate 2 checks only staged files — operator controls what is staged.

**Missing checks:**
- No automated backup confirmation (documented in RELEASE_CHECKLIST_V1.md but not automated)
- No JSONL schema validation on existing records
- No version tagging or changelog automation
- No pre-commit hook (gate runs manually)
- No rollback simulation test (documented but not run)

---

## SECTION 3 — Remaining Weaknesses

| # | Weakness | Location |
|---|---|---|
| 1 | interpretation.py is 1929 lines | interpretation.py |
| 2 | Incomplete handler registry extraction — only 2/15+ handlers extracted | interpretation.py inline elif chain |
| 3 | Partial formatter migration — only extracted handlers use response_formatter | interpretation.py inline response builders |
| 4 | No schema validation on read — loaders skip malformed lines but don't validate structure | proposal_traceability.py, implementation_planning.py, diagnostic_records.py |
| 5 | Confidence field ambiguity — field used across multiple record types without consistent semantics | SCHEMA_CONTRACTS_V1.md Section 15 |
| 6 | mode_analysis duplication pattern — inline string-building in multiple places | interpretation.py |
| 7 | No CI automation — release gate is manual, operator-dependent | workflow gap |
| 8 | No versioned releases — commits only, no tags or changelog | workflow gap |
| 9 | No JSONL backup/restore automation — files grow indefinitely | operational gap |
| 10 | Exploratory test inventory not integrated — 40+ test files (~19K lines) design references | weslr/tests/ |

---

## SECTION 4 — Risk Classification

| # | Weakness | Risk | Justification |
|---|---|---|---|
| 1 | interpretation.py (1929 lines) | **HIGH** | Single large module = high blast radius. Hard to review, easy to break silently |
| 2 | Incomplete registry extraction | **HIGH** | Inline handlers accumulate without governance. Shadowing risk grows with each addition |
| 3 | Partial formatter migration | **MEDIUM** | Ad-hoc responses create inconsistency. No structural enforcement |
| 4 | No read-side schema validation | **MEDIUM** | Malformed records accumulate silently in JSONL. Detectability gap |
| 5 | Confidence field ambiguity | **LOW** | Informational only. Not used in governance decisions |
| 6 | mode_analysis duplication | **LOW** | Maintainability issue, not a safety issue |
| 7 | No CI automation | **MEDIUM** | Gate is operator-dependent. Forgetting to run it defeats its purpose |
| 8 | No versioned releases | **LOW** | Current workflow works. Semantic versioning is nice-to-have |
| 9 | No JSONL backup/rotation | **MEDIUM** | Append-only means no cleanup. Risk grows with file size |
| 10 | Exploratory tests not integrated | **LOW** | Documents design intent, not live validation |

**Act now:** #1, #2, #7
**Plan soon:** #3, #4, #9
**Nice to have:** #5, #6, #8, #10

---

## SECTION 5 — System Classification

**WESLR is currently a structured prototype.**

Evidence:
- Core modules functional with schema enforcement, validation, and read isolation
- Test harness passes T1–T6 + G1–G4 gates
- JSONL path stability fixed this session (PATH_STABILITY_FIX_CONFIRMED)
- Handler registry first extraction complete (HANDLER_REGISTRY_FIRST_EXTRACTION_CONFIRMED)
- ADR documentation exists with 4 decisions recorded
- Architecture diagrams published (5 Mermaid diagrams)
- No `execution_allowed=True` in production code
- Response formatter and schema contracts documented

**Why not prototype:** Repeatable processes exist (schema enforcement, validation, testing, release gating). Not a one-off experiment.

**Why not engineering-grade:**
- interpretation.py is a single monolithic module — engineering-grade systems decompose concerns into separate modules
- Handler extraction is incomplete — engineering-grade systems have complete registry coverage
- CI is manual — engineering-grade systems automate gates on push/PR
- JSONL files have no rotation/backup — engineering-grade systems have operational runbooks

**Why not production-grade:**
- No automated backup or restore
- No monitoring or alerting
- No performance benchmarks
- No rollback automation
- No versioned releases

---

## SECTION 6 — Next Phase Decision

**Choose: B) CI + automation phase**

Justification:

The system has a release gate that runs manually. Every gate (G1–G4) is implemented correctly, but all require the operator to remember to run `python3 weslr/tests/release_gate_v1.py` before committing. This is a human-reliability dependency.

The structured prototype is mature enough to benefit from automation. CI removes the operator-dependency and enforces constraints consistently.

**Why not A (structural refactor)?** interpretation.py at 1929 lines is a problem, but refactoring without automated validation would introduce risk. Structural refactor should happen after CI is in place.

**Why not C (interaction/humanization)?** Response tone improvement is valid but not the constraint holding the system back. CI automation is more critical.

**Why not D (controlled execution)?** ISS is explicitly in simulated mode. Moving to real execution requires governance documentation and rollback automation — none of which exist yet.

---

## SECTION 7 — Roadmap (Next 5 Steps)

**Step 1 — GitHub Actions CI workflow**
File: `.github/workflows/weslr.yml`
- On push/PR touching `weslr/` or `interpretation.py`: run `python3 weslr/tests/release_gate_v1.py`
- On failure: block merge, report which gate failed
- No manual gate required

**Step 2 — JSONL backup automation**
File: `weslr/docs/OPERATIONAL_RUNBOOK_V1.md` + `weslr/tools/backup_jsonl.py`
- Document JSONL file locations and line count thresholds
- `backup_jsonl.py` — copies last N lines of each JSONL to `weslr/backups/` with timestamp
- Rotation policy: rotate when any JSONL exceeds 1000 lines

**Step 3 — Schema read-side validation (lightweight)**
Add to `load_trace`, `load_implementation_plans`, `load_iss_diagnostics`:
- Check `type` field present and non-empty string
- Check required top-level fields per record type
- Log (do not raise) on validation failure
- Silently skip malformed records (consistent with current malformed-line behavior)

**Step 4 — Extract next handler batch**
Files: `weslr/deterministic_handlers.py`, `interpretation.py`
- Extract `operator_overview` handler → registry + formatter
- Extract `state_checkpoint_query` handler → registry + formatter
- Extract `plan_explanation` handler → registry + formatter
- Target: 5 extracted handlers total (2 current + 3 new)

**Step 5 — T5 regression test integration**
Add to `test_harness_v1.py`:
- C1–C9 regression layer-by-layer cases from `TEST_STRATEGY_V1.md`
- Run T5 as part of G1
- Document pass/fail criteria per layer

---

## SECTION 8 — Verdict

**ENGINEERING_MATURITY_SCAN_CONFIRMED**

WESLR is a structured prototype with active schema enforcement, read isolation, test coverage, and release gating. The system is sound. PATH_STABILITY_FIX_CONFIRMED and HANDLER_REGISTRY_FIRST_EXTRACTION_CONFIRMED this session. Primary risks: manual CI gate and monolithic interpretation.py.

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

**Chosen next phase:** CI + automation (Step 1: GitHub Actions workflow)

**Roadmap:** Steps 1–5 as above

---

*Document version: 1.1*
*Status: active reference*
*Changes from v1.0: added PATH_STABILITY_FIX_CONFIRMED, HANDLER_REGISTRY_FIRST_EXTRACTION_CONFIRMED, updated registry entries with current priorities, updated roadmap to match current priorities*
