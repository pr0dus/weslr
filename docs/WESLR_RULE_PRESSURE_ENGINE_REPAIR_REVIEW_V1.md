# WESLR Rule Pressure Engine V1 Repair Followup Review

## Repo
- Root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`
- Start HEAD: `f487384748820e418a569c88293d7f0123a0016f`
- End HEAD: `f487384748820e418a569c88293d7f0123a0016f`

## Files reviewed
- `weslr/rule_pressure_engine.py`
- `weslr/tests/test_rule_pressure_engine_v1.py`
- `weslr/cognitive_research_protocol.py`
- `weslr/tests/test_cognitive_research_protocol_v1.py`
- `weslr/nonlinear_inspiration_resonance_engine.py`
- `weslr/unknown_engine_adapter.py`
- `weslr/forecast_calibration_bridge.py`
- `weslr/raw_signal_cartographer.py`
- `weslr/unintelligible_output_analyzer.py`

## Files changed by review
- `docs/WESLR_RULE_PRESSURE_ENGINE_REPAIR_REVIEW_V1.md`

## Repair followup findings
- The local Rule Pressure research-mode allowlist is now narrow and matches only the approved set:
  - `internal_exploration`
  - `synthetic_test`
  - `calibration_replay`
  - `frontier_mapping`
- Extra shared-protocol modes are rejected by Rule Pressure even when the shared protocol accepts them elsewhere.
- `RulePressureTargetV1` now allows `not_public_claim` and `internal_candidate_only`.
- Public-safe/export-safe target statuses still fail closed.
- Packet-level `public_export_blocked` is preserved as blocked/internal packet status while the target is normalized to internal-only.
- Shared `CognitiveResearchRunV1` validation remains unchanged.
- Neighboring engine compatibility is preserved.
- No runtime wiring, provider/model calls, retrieval/tool execution, persistence, `.weslr` IO, public claims, memory/project mutation, or behavior-pack promotion were introduced.

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
- 323 collected tests across the validated suites.

## Release gate status
- PASS

## Protected files
- Unchanged: `weslr/chat_responder.py`, `weslr/main.py`, `main.py`, `dialogue.py`, `chat_ui.py`

## Unrelated untracked files
- Left untouched.

## Final judgment
- `weslr_rule_pressure_engine_v1_repair_valid_ready_for_dialectic_generator_loop`
