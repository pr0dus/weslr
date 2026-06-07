# WESLR RF Field Discovery Floor Plan Translation V1

## 1. Purpose
This document designs how WESLR will later translate a floor-plan PDF or image into structured WESLR representations for RF Field Discovery.

The translation should support:
- floor/page identification
- room graph
- wall graph
- opening/door graph
- coordinate frame
- anchor placement
- calibration paths
- uncertainty tracking
- future visualization frames
- future RF path hypotheses

This is a design for interpretation before any real owner floor plan is provided.
It does not assume the plan will be perfect.
It does not assume OCR works.
It does not assume exact dimensions are available.
It does not assume wall material is known.
It does not assume RF sensing will work.
It preserves uncertainty.

## 2. Input types
Possible future inputs may include:
- vector PDF
- scanned/image PDF
- PNG/JPG screenshot
- manually annotated plan
- owner-marked plan with router/repeater labels
- approximate hand-marked plan
- multi-floor plan

Exact architectural CAD is not required.

## 3. Owner annotation convention
A simple owner annotation convention may be used later.

Example labels:
- `R1` = router
- `REP1` = repeater
- `P1`, `P2`, `P3` = calibration points
- `PATH_A` = walking path
- `SIT1` = sitting/static test point
- `DOOR1` = door test
- `UNKNOWN_MATERIAL` = material unknown
- `EXCLUDE` = area not used for experiment

Later owner uploads should ideally include:
- one floor per page if possible
- one known dimension or scale if available
- router position marked
- repeater position marked
- rough room labels
- optional calibration points
- optional wall/material notes

## 4. Translation pipeline
The conceptual translation pipeline is:

1. PDF/page intake
2. floor/page separation
3. scale detection or approximate scale declaration
4. coordinate frame creation
5. room region extraction
6. wall segment extraction
7. opening/door/window extraction
8. semantic room labeling
9. anchor placement extraction
10. calibration path extraction
11. uncertainty/missing-field marking
12. environment candidate packet generation
13. RF path hypothesis graph generation
14. visualization base-layer generation

## 5. Multi-layer vector interpretation
The translation should be multi-layer, not a single embedding.

### 5.1 Geometry vector
- walls
- rooms
- doors/openings
- windows if known
- floor boundaries
- dimensions
- coordinates

### 5.2 Topology vector
- room adjacency
- openings between rooms
- possible movement paths
- connectivity graph

### 5.3 RF anchor vector
- router position
- repeater position
- future node positions
- anchor confidence
- approximate vs exact placement

### 5.4 Obstruction/material vector
- wall material if known
- glass/opening hints
- unknown material areas
- possible high-obstruction areas

### 5.5 Calibration vector
- owner walking paths
- static positions
- door tests
- baseline zones
- future experiment references

### 5.6 Uncertainty vector
- missing scale
- unclear walls
- ambiguous openings
- approximate anchor positions
- unknown materials
- multi-floor ambiguity

### 5.7 Visualization base vector
- 2D floor-plan base
- anchor markers
- possible RF path lines
- unknown regions
- later field overlay support

## 6. Mapping to existing schema helpers
Floor-plan translation outputs should map into the existing RF Discovery packets as follows:

### `RFDiscoveryEnvironmentCandidate`
Filled fields may include:
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

Missing/unknown fields should remain explicit when geometry, scale, material, or labels are uncertain.

### `RFDiscoveryAnchorCandidate`
Filled fields may include:
- `anchor_id`
- `anchor_type`
- `approximate_position`
- `position_confidence`
- `band`
- `channel`
- `observable_data_types`
- `sampling_mode`
- `mobility_state`
- `trust_level`
- `missing_fields`
- `notes`

Unknown anchor position or uncertain labels should remain visible in `missing_fields` and `confidence`.

### `RFDiscoveryVisualizationFrameCandidate`
Filled fields may include:
- `environment_ref`
- `anchor_refs`
- `signal_path_estimates`
- `stable_field_estimate`
- `disturbed_field_estimate`
- `unknown_field_estimate`
- `confidence_overlay`
- `visual_metaphor`
- `explanation_panel`
- `warnings`
- `notes`

### `RFDiscoveryCalibrationExperimentCandidate`
Filled fields may include:
- `setup`
- `time_window`
- `owner_label`
- `experiment_type`
- `observed_signal_changes`
- `prediction_before_label`
- `actual_label`
- `confidence_before`
- `confidence_after`
- `correction`
- `lesson_learned`
- `next_branch`

### `RFDiscoveryDecisionOutcomeCandidate`
Filled fields may include:
- `input_evidence`
- `branch`
- `reason`
- `confidence`
- `next_lane`
- `archive_lesson`
- `open_questions`
- `value_signal`

## 7. RF path hypothesis graph
A future RF path hypothesis graph should be designed as a hypothesis, not a claim of actual propagation accuracy.

Possible fields and concepts:
- `source_anchor`
- `target_anchor/client/future node`
- `direct_path_possible`
- `wall_crossings`
- `openings_near_path`
- `room_sequence`
- `estimated_obstruction`
- `confidence`
- `unknowns`
- `alternative_paths`

This graph should only suggest likely paths and possible obstructions.
It should not assert what the RF field actually is.

## 8. Quality levels
Floor-plan translation quality levels should be tracked as follows:

### Q0 — no plan
- only textual room list or unknown environment

### Q1 — rough sketch
- approximate room graph

### Q2 — marked screenshot/PDF
- router/repeater positions visible
- approximate anchors

### Q3 — scaled architectural plan
- dimensions or scale available

### Q4 — annotated scaled plan
- room labels, anchors, calibration points, material hints

### Q5 — validated plan
- owner confirms geometry, anchors, and calibration points

## 9. When to request the owner’s real PDF
The real owner floor-plan PDF should not be requested during this design lane.

It should be requested only after:
1. this floor-plan translation design is reviewed
2. local import boundary is designed
3. the owner approves a controlled sample import
4. a redaction/annotation convention exists
5. WESLR knows what fields it is trying to extract

The PDF should be requested before router access.

## 10. Minimal first owner upload package
The future minimal package should ideally include:
- floor-plan PDF or image
- one floor per file/page if possible
- router marked `R1`
- repeater marked `REP1`
- at least one known dimension or scale if available
- rough labels for important rooms
- optional calibration points:
  - `P1`, `P2`, `P3`
  - `PATH_A`
  - `SIT1`
  - `DOOR1`
- optional notes:
  - wall material
  - where doors usually stay open/closed
  - where WiFi devices usually are

## 11. Failure modes
Track these failure modes and keep mitigation attached:

- PDF is scanned and hard to parse
  - mitigation: allow rough sketch mode and manual annotation fallback
- scale missing
  - mitigation: use approximate scale declaration or Q1/Q2 quality level
- room labels missing
  - mitigation: preserve unlabeled room regions and ask for owner labels later
- walls unclear
  - mitigation: mark ambiguous walls and keep uncertainty visible
- anchor positions approximate
  - mitigation: record confidence and approximate-vs-exact placement
- multi-floor ambiguity
  - mitigation: separate floor pages and keep floor_count explicit
- furniture not represented
  - mitigation: treat furniture as a later overlay, not a requirement for the first translation
- wall material unknown
  - mitigation: preserve material_hints as unknown rather than inventing it
- plan outdated
  - mitigation: timestamp the plan and surface possible drift
- visualization implies too much certainty
  - mitigation: keep confidence overlays and unknown regions visible
- RF path hypotheses look more accurate than they are
  - mitigation: label them as hypotheses and preserve alternatives

## 12. Future lanes
Recommend these future lanes:
1. `REVIEW_WESLR_RF_FIELD_DISCOVERY_FLOOR_PLAN_TRANSLATION_V1`
2. `DESIGN_WESLR_RF_FIELD_DISCOVERY_LOCAL_IMPORT_BOUNDARY_V1`
3. `IMPLEMENT_WESLR_RF_FIELD_DISCOVERY_FLOOR_PLAN_PACKET_HELPERS_V1`
4. `DESIGN_WESLR_RF_FIELD_DISCOVERY_OWNER_PDF_SAMPLE_PROTOCOL_V1`
5. `DESIGN_WESLR_RF_FIELD_DISCOVERY_ROUTER_REPEATER_RESEARCH_PLAN_V1`
6. `DESIGN_WESLR_RF_FIELD_DISCOVERY_VISUALIZATION_DIRECTION_V1`

## OCC Final Report

1. Handshake result
- PASS

2. Start HEAD
- `d6a04370874c7ae1ad7b329265fec3f74c974ae3`

3. Target design lane
- `DESIGN_WESLR_RF_FIELD_DISCOVERY_FLOOR_PLAN_TRANSLATION_V1`

4. WESLR repo root and branch
- Root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`

5. Files changed
- `docs/WESLR_RF_FIELD_DISCOVERY_FLOOR_PLAN_TRANSLATION_V1.md`

6. Validation criteria
- Design-only artifact created
- Input types defined without requiring CAD
- Owner annotation convention defined
- Translation pipeline defined
- Multi-layer vector interpretation defined
- Existing schema helper mapping defined
- RF path hypothesis graph defined as hypothesis only
- Quality levels defined
- Owner PDF timing delayed appropriately
- Minimal upload package defined
- Failure modes tracked with mitigation
- No live sensing implemented
- No PDF parsing/OCR/image processing implemented
- No router/repeater/Home Assistant/CSI/packet-capture behavior introduced

7. Final judgment
- `weslr_rf_field_discovery_floor_plan_translation_v1_design_ready_for_review`
