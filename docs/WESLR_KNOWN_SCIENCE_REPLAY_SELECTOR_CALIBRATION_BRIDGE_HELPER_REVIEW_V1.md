# WESLR Known-Science Replay Selector Calibration Bridge Helper V1 Review

## 1. Repo / run context
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`
- Start HEAD: `83e08fe96662909eb29f2b979ca9c1e0012d636e`
- End HEAD: `83e08fe96662909eb29f2b979ca9c1e0012d636e` (review-only snapshot)
- Files reviewed:
  - `weslr/known_science_replay_selector_calibration_bridge.py`
  - `weslr/tests/test_known_science_replay_selector_calibration_bridge_v1.py`
  - `weslr/tests/release_gate_v1.py`
- Reference docs reviewed:
  - `docs/WESLR_KNOWN_SCIENCE_REPLAY_SELECTOR_CALIBRATION_BRIDGE_V1.md`
  - `docs/WESLR_KNOWN_SCIENCE_REPLAY_SELECTOR_CALIBRATION_BRIDGE_REVIEW_V1.md`
  - `docs/WESLR_KNOWN_SCIENCE_REPLAY_SAMPLE_OUTPUT_REVIEW_V1.md`
  - `docs/WESLR_KNOWN_SCIENCE_REPLAY_HELPERS_REVIEW_V1.md`
  - `docs/WESLR_SCENARIO_SENSITIVE_NEXT_STEP_SELECTOR_REVIEW_V1.md`

## 2. Helper safety assessment
- Deterministic: yes.
- Metadata-only: yes.
- Side-effect-free: yes.
- No recursive research executor: yes.
- No selector runtime execution: yes.
- No Suggestion Store update: yes.
- No behavior-pack promotion: yes.
- No answer-formation change: yes.
- No ChatResponder modification: yes.
- No public output generation: yes.
- No provider/model/tool/retrieval/web calls: yes.
- No `.weslr` IO: yes.
- No persistence/database writes: yes.
- No memory/project mutation: yes.
- No benchmark/score/proof/discovery/AGI/public-science/final-answer authority: yes.

## 3. Design conformance assessment
- Public API surface is present and matches the lane design.
- Required packet fields are present.
- Alignment/mismatch behavior is bounded and useful.
- Canonical pulsar bridge examples exist and validate.
- Optional replay stubs exist and validate.
- JSON-safe export is implemented.
- Fail-closed validation is implemented for required fields, enums, authority, runtime/tool implications, `.weslr`, and non-JSON-safe values.

## 4. Public API assessment
Present:
- `build_known_science_replay_selector_bridge_input_v1`
- `build_known_science_replay_selector_bridge_packet_v1`
- `compare_known_science_replay_selector_step_v1`
- `validate_known_science_replay_selector_bridge_packet_v1`
- `summarize_known_science_replay_selector_bridge_packet_v1`
- `to_known_science_replay_selector_bridge_json_safe_v1`
- `build_initial_known_science_replay_selector_bridge_examples_v1`

## 5. Packet-field assessment
Implemented fields are present:
- `schema_version`
- `bridge_id`
- `source_replay_case_id`
- `source_known_outcome`
- `source_case_domain`
- `replay_phase_id`
- `replay_phase_summary`
- `expected_internal_next_step`
- `selector_input_metadata`
- `selector_selected_next_step`
- `selector_selection_reason`
- `alignment_status`
- `alignment_notes`
- `mismatch_type`
- `calibration_observation`
- `recommended_followup`
- `forbidden_interpretations`
- `authority_status`
- `safe_metadata`

## 6. Alignment / mismatch logic assessment
- Exact match → `aligned` / `none`: yes.
- Multi-step expected match → `aligned` / `none`: yes.
- Unsafe public-claim block → `blocked_by_safety`: yes.
- Invalid/missing metadata → `needs_repair` / `invalid_metadata`: yes.
- `probe` → `calibrate` → `premature_calibration`: yes.
- `probe` → `archive` → `premature_archive`: yes.
- `pressure_test` with a different non-blocked step → `missed_pressure_test`: yes.
- Unknown case/phase → `not_applicable` / `unknown_case`: yes.

## 7. Canonical pulsar example assessment
The canonical pulsar bridge examples exist and validate:
- `initial_strange_signal`
- `repeated_precise_signal`
- `ordinary_explanations_weakened`
- `external_confirmation`
- `unsafe_public_claim_attempt`

## 8. Optional examples assessment
The optional replay stubs exist and validate:
- `continental_drift_replay`
- `penicillin_contamination_replay`
- `cosmic_microwave_background_replay`
- `helicobacter_pylori_ulcer_replay`

## 9. Claim-language context-awareness assessment
This is the blocking issue.

The helper does **not** yet fully satisfy the requested context-aware claim-language boundary.

Observed behavior:
- It correctly blocks overt unsafe claim language in runtime-style fields.
- It correctly allows neutral historical/discovery-replay packets in the current canonical examples.
- But it still scans `selector_input_metadata` recursively for claim markers.

That means a neutral packet can be rejected if `selector_input_metadata` contains historically legitimate wording such as a discovery-era title or explanatory metadata containing the word `discovery`.

Directly observed reproduction:
- A packet using neutral internal metadata with `selector_input_metadata = {"case_title": "historical discovery replay", ...}` was rejected with `forbidden_claim_language`.

This is too broad for the requirement that neutral/internal/historical uses of discovery-like language must remain allowed.

## 10. JSON-safe / fail-closed assessment
- JSON-safe export works.
- Missing required fields fail closed.
- Invalid enum values fail closed.
- Unsafe authority flags fail closed.
- Provider/model/tool/retrieval/web implications fail closed.
- `.weslr` implications fail closed.
- Hidden/private/protected markers fail closed.
- Non-JSON-safe nested values fail closed or sanitize through the JSON-safe helper.

## 11. Validation results
Passed:
- `python -m py_compile weslr/known_science_replay_selector_calibration_bridge.py weslr/tests/test_known_science_replay_selector_calibration_bridge_v1.py`
- `python -m pytest -q weslr/tests/test_known_science_replay_selector_calibration_bridge_v1.py`
- `python -m pytest -q weslr/tests/test_known_science_replay_helpers_v1.py`
- `python -m pytest -q weslr/tests/test_scenario_sensitive_next_step_selector_v1.py`
- `python -m pytest -q weslr/tests/test_recursive_research_loop_findings_digest_v1.py`
- `python -m pytest -q weslr/tests/test_recursive_research_loop_scenario_set_v1.py`
- `python -m pytest -q weslr/tests/test_minimal_recursive_research_loop_dry_run_executor_v1.py`
- `python -m pytest -q weslr/tests/test_cognitive_research_protocol_v1.py`
- `python weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`
- `git diff --check`
- protected-file checks for:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `main.py`
  - `dialogue.py`
  - `chat_ui.py`

## 12. Test count
- 7 pytest suites + py_compile + release gate + release check + diff check + protected-file checks

## 13. Release gate status
- PASS after exact-path allowlist handling for this review doc.

## 14. Protected files unchanged status
- Confirmed unchanged.

## 15. Unrelated files untouched status
- Confirmed untouched; numerous unrelated untracked docs/scripts remain present.

## 16. Gaps or repair needs
Required repair:
- Narrow claim-language validation so neutral historical/discovery metadata in `selector_input_metadata` is not treated as forbidden claim escalation.
- Add tests covering the allowed `discovery`-in-neutral-metadata case.

## 17. Final judgment
`weslr_known_science_replay_selector_calibration_bridge_helper_v1_needs_repair`
