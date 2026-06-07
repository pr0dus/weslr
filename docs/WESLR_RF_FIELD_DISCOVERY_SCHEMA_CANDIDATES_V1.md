# WESLR RF Field Discovery Schema Candidates V1

## 1. Purpose
This document defines candidate schemas for discovery, not final locked schemas.

The schemas are meant to help WESLR explore:
- what signal data exists
- what patterns repeat
- what vectors are useful
- whether floor plans help
- whether visualization is meaningful
- whether extra hardware is worth adding
- whether the artifact has future value

## 2. Schema design principles
- flexible before final
- unknowns preserved
- missing fields allowed and explicit
- confidence separated from observation
- raw observation separated from derived interpretation
- alternatives preserved
- strange patterns not discarded
- router/repeater path supported first
- CSI optional later
- visualization is estimated, not assumed literal
- marketplace fields are future-readiness only

## 3. Environment schema candidate

### `RFDiscoveryEnvironmentCandidate`
Fields:
- `environment_id`
- `label`
- `coordinate_frame`
- `room_graph`
- `wall_graph`
- `opening_graph`
- `floor_count`
- `anchor_positions`
- `unknown_regions`
- `material_hints`
- `calibration_paths`
- `source_artifact_ref`
- `missing_fields`
- `confidence`
- `notes`

Open questions:
- how precise must floor plan geometry be?
- are material hints needed?
- can rough room graph work before exact coordinates?
- does floor plan improve signal interpretation?

## 4. RF anchor schema candidate

### `RFDiscoveryAnchorCandidate`
Fields:
- `anchor_id`
- `anchor_type`:
  - `router`
  - `repeater`
  - `client`
  - `future_csi_node`
  - `future_sensor`
  - `unknown`
- `approximate_position`
- `position_confidence`
- `band`
- `channel`
- `observable_data_types`
- `sampling_mode`
- `mobility_state`
- `trust_level`
- `notes`
- `missing_fields`

Open questions:
- can repeater create enough path diversity?
- does client movement help or confuse?
- which anchor data is accessible from normal WLAN infrastructure?

## 5. Signal observation schema candidate

### `RFDiscoverySignalObservationCandidate`
Fields:
- `observation_id`
- `timestamp`
- `time_window`
- `source_anchor_id`
- `target_anchor_or_client_id`
- `path_id`
- `rssi`
- `link_quality`
- `latency`
- `jitter`
- `packet_loss`
- `throughput`
- `roaming_event`
- `channel`
- `band`
- `csi_amplitude`
- `csi_phase`
- `snr`
- `raw_or_derived`
- `available_fields`
- `missing_fields`
- `collection_context`
- `notes`

Notes:
- CSI fields are optional/future.
- Router/repeater telemetry is represented without assuming it is enough.

## 6. Baseline schema candidate

### `RFDiscoveryBaselineCandidate`
Fields:
- `baseline_id`
- `environment_id`
- `anchor_set`
- `time_window`
- `conditions`
- `expected_stability`
- `observed_variance`
- `signal_summary`
- `known_changes`
- `unknown_changes`
- `valid_until_condition`
- `confidence`
- `notes`

Invalidation triggers:
- router moved
- repeater moved
- furniture changed
- channel changed
- major device changes
- environment changed
- unknown drift

## 7. Pattern candidate schema

### `RFDiscoveryPatternCandidate`
Fields:
- `pattern_id`
- `time_window`
- `affected_paths`
- `baseline_deviation`
- `repeated_motif`
- `possible_causes`
- `alternative_causes`
- `disturbance_score`
- `stability_score`
- `confidence`
- `unknowns`
- `next_test_suggested`
- `raw_signal_refs`
- `notes`

Possible causes:
- physical movement
- WiFi traffic
- device roaming
- door movement
- appliance activity
- router/repeater change
- interference
- unknown

## 8. Strange signal packet schema

### `RFDiscoveryStrangeSignalCandidate`
Purpose:
Preserve weird or unintelligible signal behavior without forcing early explanation.

Fields:
- `strange_signal_id`
- `time_window`
- `observed_features`
- `why_strange`
- `matched_known_pattern`
- `unmatched_features`
- `compression_attempt`
- `candidate_grammar`
- `hypotheses`
- `counterexamples_needed`
- `next_probe`
- `confidence`
- `notes`

Mapped WESLR capabilities:
- `RAW_SIGNAL_CARTOGRAPHER`
- `UNKNOWN_ENGINE`
- `SIGNAL_VS_NOISE_ENGINE`

## 9. Calibration experiment schema

### `RFDiscoveryCalibrationExperimentCandidate`
Fields:
- `experiment_id`
- `experiment_type`
- `setup`
- `expected_unknown`
- `data_needed`
- `owner_label`
- `time_window`
- `observed_signal_changes`
- `prediction_before_label`
- `actual_label`
- `confidence_before`
- `confidence_after`
- `correction`
- `lesson_learned`
- `next_branch`

Experiment types:
- `empty_baseline`
- `known_walk`
- `door_movement`
- `sitting_still`
- `client_movement`
- `traffic_only`
- `movement_low_traffic`
- `router_repeater_position_change`
- `furniture_change`
- `unknown_disturbance`
- `router_only`
- `router_plus_repeater`
- `future_csi_comparison`

## 10. Visualization frame schema

### `RFDiscoveryVisualizationFrameCandidate`
Fields:
- `frame_id`
- `timestamp`
- `environment_ref`
- `anchor_refs`
- `signal_path_estimates`
- `stable_field_estimate`
- `disturbed_field_estimate`
- `unknown_field_estimate`
- `confidence_overlay`
- `visual_metaphor`
- `explanation_panel`
- `next_calibration_need`
- `warnings`
- `notes`

Visual metaphors may include:
- blue stable areas
- green disturbance areas
- gray unknown areas
- path lines
- field intensity
- time playback

Do not decide whether this is 2D, 3D, Unreal-style, browser-based, local app, or marketplace demo.

## 11. Decision outcome schema

### `RFDiscoveryDecisionOutcomeCandidate`
Fields:
- `decision_id`
- `input_evidence`
- `branch`
- `reason`
- `confidence`
- `next_lane`
- `archive_lesson`
- `open_questions`
- `value_signal`

Branches:
- `continue_router_repeater`
- `research_csi`
- `prioritize_floor_plan_graph`
- `prioritize_signal_only_learning`
- `prioritize_visualization`
- `become_anomaly_motif_analyzer`
- `archive_lessons`
- `evaluate_marketplace_potential`

## 12. Artifact value assessment schema

### `RFDiscoveryValueAssessmentCandidate`
Fields:
- `assessment_id`
- `usefulness_signals`
- `repeatability`
- `hardware_complexity`
- `visualization_value`
- `calibration_cost`
- `marketplace_potential`
- `synthetic_demo_possible`
- `private_data_dependency`
- `next_investment_recommendation`
- `confidence`
- `notes`

## 13. Candidate relationships
- Environment contains anchors.
- Anchors produce observations.
- Observations compare against baselines.
- Baseline deviations produce pattern candidates.
- Strange patterns are preserved separately.
- Calibration experiments update confidence.
- Visualization frames render estimates.
- Decision outcomes choose next branch.
- Value assessment decides whether to continue.

## 14. Open questions registry
Future lanes must answer at least:
- What data can normal router/repeater expose?
- What is the minimum useful sampling rate?
- Is RSSI enough for anything useful?
- Does repeater path diversity help?
- Can movement be separated from traffic?
- Can static presence be detected?
- Can floor plan geometry improve interpretation?
- When is CSI required?
- What is the simplest useful visualization?
- What makes this artifact valuable?

## 15. Future implementation notes
The next implementation lane should only create pure schema helper functions with synthetic examples.

No real sensing.
No router access.
No packet capture.
No CSI collection.
No Home Assistant connection.
No runtime wiring.

Recommended future lanes:
1. `REVIEW_WESLR_RF_FIELD_DISCOVERY_SCHEMA_CANDIDATES_V1`
2. `IMPLEMENT_WESLR_RF_FIELD_DISCOVERY_SCHEMA_HELPERS_V1`
3. `DESIGN_WESLR_RF_FIELD_DISCOVERY_EXPERIMENT_LIBRARY_V1`
4. `IMPLEMENT_WESLR_RF_FIELD_DISCOVERY_SYNTHETIC_EXAMPLES_V1`
5. `DESIGN_WESLR_RF_FIELD_DISCOVERY_ROUTER_REPEATER_RESEARCH_PLAN_V1`
6. `DESIGN_WESLR_RF_FIELD_DISCOVERY_FLOOR_PLAN_TRANSLATION_V1`
7. `DESIGN_WESLR_RF_FIELD_DISCOVERY_VISUALIZATION_DIRECTION_V1`
8. `DESIGN_WESLR_RF_FIELD_DISCOVERY_VALUE_ASSESSMENT_V1`

## OCC Final Report

1. Handshake result
- PASS

2. Start HEAD
- `0e3cff0a20d85809f871d575da738d69919bc794`

3. Target design lane
- `DESIGN_WESLR_RF_FIELD_DISCOVERY_SCHEMA_CANDIDATES_V1`

4. WESLR repo root and branch
- Root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`

5. Files changed
- `docs/WESLR_RF_FIELD_DISCOVERY_SCHEMA_CANDIDATES_V1.md`

6. Validation criteria
- Design-only artifact created
- Candidate schemas remain flexible
- Discovery-first framing preserved
- Router/repeater-first path supported
- CSI optional later
- Visualization remains estimated, not literal
- Marketplace fields remain future-readiness only
- No live sensing implemented
- No router access or packet capture
- No Home Assistant connection
- No runtime wiring

7. Final judgment
- `weslr_rf_field_discovery_schema_candidates_v1_design_ready_for_review`
