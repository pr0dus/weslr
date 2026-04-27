# WESLR Canonicality Gap Scan — V1

## Scope

Files inspected: `interpretation.py` (1971 lines), `weslr/state_checkpoint.py`, `weslr/proposal_traceability.py`, `weslr/implementation_planning.py`, `weslr/iss/diagnostic_records.py`, `weslr/iss/probe_registry.py`, `weslr/iss/probe_planning.py`, `weslr/iss/probe_execution.py`

---

## SECTION 1 — Canonical Layers Currently Confirmed

1. **W1** — Front door deterministic routing (confirmed, not in code as a layer but referenced)
2. **C7** — `proposal_traceability.py`: `record_proposal()`, `record_decision()`, `load_trace()` — clean, minimal, append-only
3. **C8** — `implementation_planning.py`: `create_implementation_plan()`, `record_implementation_plan()`, `load_implementation_plans()` — clean separation of creation and recording
4. **C9** — Proposal→Decision→Plan linkage via `proposal_traceability` + `implementation_planning` cross-reference
5. **ISS_V1** — `diagnostic_records.py`: `make_probe_result()`, `make_gap_signal()`, `record_iss_diagnostic()`, `load_iss_diagnostics()` — well-formed record types
6. **ISS Probe Subsystem** — `probe_registry.py`, `probe_planning.py`, `probe_execution.py` — clean, declarative, non-executing
7. **State Checkpoint** — `get_state_checkpoint()` returns a static, hardcoded dict — no dynamic detection

---

## SECTION 2 — Non-Canonical / Scattered Logic

1. **interpretation.py is a monolith** (1971 lines). It contains: capabilities scoring, feedback logging, interest tracking, human turn interpretation, operator feedback summarization, interest surfacing, and 11+ separate deterministic handler blocks all in one file. No separation between "core interpretation" and "deterministic query responders."

2. **Response text is embedded directly inside handlers** — every handler builds its own `response_text` inline. There is no `format_response(path, data)` or centralized response builder. Adding a new field to all responses requires touching every handler.

3. **No central trigger registry** — triggers are defined as module-level lists (`_plan_triggers`, `_iss_triggers`, `_ov_triggers`, `_intake_triggers`, `_iss_intake_triggers`, `_plan_explain_triggers`, `_probe_triggers`, `_plan_probe_triggers`, `_execute_triggers`, `_explain_triggers`, `_ck_triggers`) but there is no `HANDLER_REGISTRY` dict mapping `path` → handler function. The dispatch is implicit via `if any(lowered.startswith(t) for t in _triggers)` fallthrough.

4. **`_B9_STATE` is a module-level mutable dict** (`_B9_STATE = {"low_confidence_count": 0, "mismatch_count": 0}`) — this is session-only state stored in code, not in a JSONL or state file. Not persistent, but also not clearly scoped.

5. **`_FEEDBACK_LOG_PATH` is a module-level Path computed at import time** from `__file__` — fragile if the file moves.

6. **ISS handlers inserted mid-function** — the ISS probe execution handler block (`_execute_triggers`) is placed between the plan explanation triggers and the proposal explanation layer — not grouped with other ISS handlers. Order is accidental, not designed.

---

## SECTION 3 — Missing Canonical Contracts

1. **No schema for `proposal_trace.jsonl` records** — `proposal_traceability.py` writes records with `type`, `proposal_id`, `content`, `timestamp` but there's no JSON schema defining required vs optional fields. The `content` field is unstructured dict.

2. **No schema for `implementation_plans.jsonl`** — `implementation_planning.py` writes plans but the record shape is implicit. `execution_allowed`, `operator_approval_required`, `plan_id`, `proposal_id` are accessed by string keys throughout.

3. **No schema for `iss_diagnostic_records.jsonl`** — `diagnostic_records.py` enforces type via `_ALLOWED_PROBE_STATUS` and `_ALLOWED_GAP_SEVERITY` but the actual record fields are defined in function return dicts, not in a shared schema.

4. **`state_checkpoint` is static and operator-maintained** — `get_state_checkpoint()` returns a hardcoded dict. It reflects what the operator last wrote, not what the code actually supports. Could be manually stale.

5. **No canonical `response_text` format contract** — each handler builds its own string. No standard sentence templates, no field injection pattern.

6. **No contract for `suggested_mode` values** — `observe`, `entity_only`, `diagnostic` appear but are not enumerated as an allowed set anywhere.

7. **`_CAPABILITIES` is hardcoded in interpretation.py** and has `ISS: False` — but the actual ISS subsystem exists. This is a lie by staleness.

---

## SECTION 4 — Duplicated Logic or Repeated Patterns

1. **Handler pattern repeated 11 times**: `for t in _X_triggers: if lowered.startswith(t): ...` — same structure with no abstraction. A `HandlerRegistry` would eliminate this.

2. **Duplicate `load_trace()` calls**: `interpretation.py` calls `load_trace(100)` in at least 3 different places (capability scoring, plan explanation, proposal explanation) — each re-reads from the same JSONL file.

3. **`execution_allowed` check pattern** appears in multiple handlers but is not abstracted — each handler independently checks or asserts it.

4. **Probe/execute confirmation gate** (`if not requires_confirm: return {requires_confirmation: True}`) is custom logic — could be a utility `require_confirmation(probe_id, message)`.

5. **No shared response skeleton function** — every handler builds the full return dict independently: `message + response_text + path + _weslr_deterministic + confidence + suggested_mode`.

6. **Interest tracking and feedback logging** are intermingled with core interpretation — `get_interest_summary()` and `summarize_operator_feedback()` are imported from within `interpretation.py` itself, creating circular-style import chains within the same module.

---

## SECTION 5 — Handler-Order Risks

1. **`_execute_triggers` comes before `_explain_triggers`** — "execute probe why is proposal X" would match `execute probe` first and fail. The ordering is accidental based on when each block was added.

2. **`"why does plan "` vs `"why is "`** — `_plan_explain_triggers` = `["why does plan ", "explain plan ", "why was plan "]` and `_explain_triggers` = `["why is ", "explain proposal ", "why prioritize "]`. These don't overlap but there is no enforced discipline — a new trigger added later could accidentally shadow an earlier one.

3. **`"plan probe "` vs `"plan "`** — `_plan_probe_triggers` = `["plan probe ", "how would you check "]` and `_plan_triggers` starts with `"plan "`. A query like `"plan probe.trace.proposals"` would match `_plan_triggers` first (starts with `"plan "`) before reaching `_plan_probe_triggers`. This is a real ordering risk.

4. **No "last resort" handler** — if no trigger matches, the function falls through to... nothing visible in the handler list. There is implicit fallthrough to non-structured response. No 404 equivalent.

5. **Trigger overlap with `show`**: `show diagnostics`, `show iss probes`, `show system overview` all share `show` prefix — handled separately but order matters.

---

## SECTION 6 — Data-File / JSONL Contract Risks

1. **`proposal_trace.jsonl` grows without limit** — `load_trace(limit)` caps read but write is append-only with no rotation or size guard. Over time this file could become large.

2. **`load_implementation_plans` returns all records from file** — no limit parameter, no filtering. If file grows large, entire file is loaded.

3. **`load_iss_diagnostics(limit)`** has limit but the file is append-only with no cleanup.

4. **No file integrity checking** — if a JSONL line is malformed, the load function crashes on that line (no error isolation).

5. **`proposal_trace.jsonl` has two records with `source_gap_ids: null`** — from the earlier `gap.iss.not_integrated` run. This was identified and fixed in plan explanation extraction, but the raw records remain with `null`. Not a bug now but a data cleanliness risk.

6. **`implementation_plans.jsonl` contains only 5 plans but all have `source_gap_ids: null`** — no plan in the file has a populated `source_gap_ids`. The fix for `plan_explanation` extracted from `content.source_gap_id`, but the plans themselves weren't backfilled.

---

## SECTION 7 — Response Style / Robotic-Output Risks

1. **All response_text is deterministic and formulaic** — `"Probe 'X' executed in simulated mode. Status: ok."` is correct but sounds like a template. If all WESLR responses follow a template, interaction feels mechanical.

2. **No variation in confirmation prompts** — `"Probe execution requires confirmation. Say: 'execute probe <id> confirm'. This will run simulated execution only."` is always identical regardless of probe type. Over time this reduces operator engagement.

3. **No natural language fallback** — for any input that doesn't match a trigger, `interpret_human_turn` returns the base turn type assessment (observe/entity_only/diagnostic) but no graceful "I don't have a specific handler for this" message.

4. **`confidence: "high"` on all deterministic responses** — `confidence` is always `"high"` for deterministic handlers. This is programmatically correct but semantically misleading — high confidence in what? The system isn't measuring accuracy here.

5. **`suggested_mode: "observe"` on all probe/planning handlers** — every query handler returns `suggested_mode: "observe"` even when the operator is performing an action. This conflates query-mode with observation-mode.

---

## SECTION 8 — What Should Become Modules Later

1. **`weslr/deterministic_responders.py`** — extract all 11+ trigger groups (`_plan_triggers`, `_iss_triggers`, `_ov_triggers`, etc.) into a `HandlerRegistry` dict mapping path→handler. Each handler is a pure function `(message, lowered) → dict`.

2. **`weslr/response_formatter.py`** — central `build_response(path, data, extra_fields=None)` function that wraps any handler result in the standard skeleton: `message + response_text + path + _weslr_deterministic + confidence + suggested_mode`.

3. **`weslr/schemas/`** — JSON schema files for:
   - `proposal_trace_record.json` — defines `proposal_created` and `proposal_decision` shapes
   - `implementation_plan.json` — defines plan record shape
   - `iss_diagnostic.json` — defines `iss_probe_result` and `iss_gap_signal` shapes
   - `probe_definition.json` — defines probe registry entry shape

4. **`weslr/state_checkpoint.py` → dynamic** — `get_state_checkpoint()` should read actual layer status from code rather than returning a hardcoded dict. Or at minimum, a schema validation ensures the hardcoded dict matches the actual implemented layers.

5. **`weslr/iss/probe_registry.py` → versioned registry with schemas** — each probe entry validated against a schema. Probe definitions become immutable versioned stubs.

6. **`weslr/capability_map.py`** — extract `_CAPABILITIES` dict from `interpretation.py` into its own file with schema, separate from interpretation logic. Update automatically via architecture scan rather than manually.

7. **`weslr/interest_tracker.py`** and **`weslr/feedback_log.py`** — interest and feedback subsystems are mixed into `interpretation.py`. Extract to separate modules.

8. **`weslr/operator_feedback_log.py`** — already has its own module but the import path `_FEEDBACK_LOG_PATH` is duplicated (defined in both the module and used via `_FEEDBACK_LOG_PATH` at module level).

---

## SECTION 9 — What Should NOT Be Changed Yet

1. **`execution_allowed: False` on all probes and plans** — this is the correct default and should not be softened until a formal operator approval workflow exists.

2. **Simulated execution model** — the simulated-only approach for probes is correct. Do not add real execution paths yet. The naming (`execute_probe_simulated`) is appropriately clear.

3. **`proposal_traceability.py` and `implementation_planning.py` interfaces** — these are clean. Their function signatures should not change. Only the data they manage may need schema formalization.

4. **`diagnostic_records.py` record type enforcement** — `_ALLOWED_PROBE_STATUS` and `_ALLOWED_GAP_SEVERITY` are good guards. Keep them.

5. **Handler ordering** — fixing order risks breaking existing trigger behavior. Any re-ordering must be tested against the full trigger set before shipping.

6. **Non-backfill policy** — do not go back and populate `source_gap_ids` on old plan records. The fix in plan explanation is correct; the data is what it is.

7. **`state_checkpoint` hardcoded dict** — it serves as a stable reference point. Making it dynamically computed risks producing inconsistent snapshots.

---

## SECTION 10 — Recommended Refactor Order

**Phase 1 (Low risk, high value)**
1. Create `weslr/schemas/` directory with JSON schemas for the 4 record types. No code change, only documentation. This formalizes contracts without touching behavior.
2. Add `execution_allowed: False` enforcement in `probe_execution.py` — make it a hard assert rather than a returned field.
3. Extract `_CAPABILITIES` into `weslr/capability_map.py` — update `ISS: False` → `ISS: True` so the capability map reflects reality.

**Phase 2 (Medium risk, extraction)**
4. Extract `weslr/response_formatter.py` — create `build_deterministic_response(path, response_text, extra)` and use it in 2-3 handlers first. Validate consistency.
5. Create `weslr/deterministic_responders.py` — define `HANDLER_REGISTRY` as a dict. Move `_probe_triggers` + handler into it as the first extraction test. Keep original code as fallback.

**Phase 3 (Higher risk, structural)**
6. Extract interest tracking (`get_interest_summary`, `get_top_interests`, `record_interest`) into `weslr/interest_tracker.py`.
7. Extract feedback logging into `weslr/operator_feedback_log.py` with its own module.
8. Add `limit` parameter to `load_implementation_plans()` for consistency with `load_trace()` and `load_iss_diagnostics()`.

**Phase 4 (Post-extraction validation)**
9. Run full trigger test suite after any extraction — verify no handler ordering changes.
10. Add JSONL integrity isolation — wrap `json.loads()` in try/except per line so one malformed line doesn't crash the whole load.

**Not recommended for now:**
- Dynamic state checkpoint (too much risk of inconsistency)
- Real probe execution paths
- Any change to `execution_allowed` defaults
- Handler re-ordering without test coverage

---

*Scan completed: 2026-04-27*
*Interpretation.py: 1971 lines | 11 trigger groups | 1 monolith*
*ISS subsystem: 4 files, clean separation, all non-executing*
*Data files: 3 JSONL, append-only, no schema validation, no size limits*