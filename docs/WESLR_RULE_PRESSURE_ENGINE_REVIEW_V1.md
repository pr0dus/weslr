# WESLR Rule Pressure Engine V1 Review

## Repo
- Root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`
- Start HEAD: `6b757a1e5b2c1e41ef94df23cd88d01fe2315488`
- End HEAD: `6b757a1e5b2c1e41ef94df23cd88d01fe2315488`

## Files reviewed
- `weslr/rule_pressure_engine.py`
- `weslr/tests/test_rule_pressure_engine_v1.py`
- `weslr/cognitive_research_protocol.py`
- `weslr/tests/test_cognitive_research_protocol_v1.py`
- `weslr/unknown_engine_adapter.py`
- `weslr/nonlinear_inspiration_resonance_engine.py`
- `weslr/raw_signal_cartographer.py`
- `weslr/unintelligible_output_analyzer.py`
- `weslr/forecast_calibration_bridge.py`

## Files changed by review
- `docs/WESLR_RULE_PRESSURE_ENGINE_REVIEW_V1.md`

## Findings
- The helper is metadata-only, deterministic, JSON-safe, and side-effect-free.
- Shared protocol shape usage is aligned with `CognitiveResearchRunV1`.
- Engine name and family wiring are correct.
- Calibration bridge compatibility is present and the neighboring engine relationships are sensible.

### Repair-required gaps
1. **Research mode allowlist is broader than the requested approved set.**
   - The implementation normalizes against the shared protocol allowlist, which still accepts additional modes beyond:
     - `internal_exploration`
     - `synthetic_test`
     - `calibration_replay`
     - `frontier_mapping`
   - This does not strictly match the review requirement to use only approved research modes.

2. **Target public-claim validation is too narrow.**
   - `RulePressureTargetV1` validation currently only accepts `not_public_claim`.
   - That rejects `internal_candidate_only`, even though the review scope explicitly preserves blocked/internal statuses and only wants public-safe/export-safe states to fail close.

## Validation results
- `python -m py_compile weslr/rule_pressure_engine.py weslr/tests/test_rule_pressure_engine_v1.py` ✅
- `python -m pytest -q weslr/tests/test_rule_pressure_engine_v1.py` ✅
- `python -m pytest -q weslr/tests/test_nonlinear_inspiration_resonance_engine_v1.py` ✅
- `python -m pytest -q weslr/tests/test_unknown_engine_adapter_v1.py` ✅
- `python -m pytest -q weslr/tests/test_forecast_calibration_bridge_v1.py` ✅
- `python -m pytest -q weslr/tests/test_unintelligible_output_analyzer_v1.py` ✅
- `python -m pytest -q weslr/tests/test_raw_signal_cartographer_v1.py` ✅
- `python -m pytest -q weslr/tests/test_cognitive_research_protocol_v1.py` ✅
- `python -m pytest -q weslr/tests/test_entity_graph_import_guard_v1.py` ✅
- `python weslr/tests/release_gate_v1.py` ✅
- `bash scripts/weslr_release_check.sh` ✅
- `git diff --check` ✅

## Test count
- 314 collected tests across the validated suites.

## Release gate status
- PASS

## Protected files
- Unchanged: `weslr/chat_responder.py`, `weslr/main.py`, `main.py`, `dialogue.py`, `chat_ui.py`

## Gaps / deferred work
- Tighten rule-pressure research-mode handling to the approved set.
- Relax target public-claim validation so internal-only statuses are preserved while public-safe/export-safe states still fail closed.

## Final judgment
- `weslr_rule_pressure_engine_v1_needs_repair`
