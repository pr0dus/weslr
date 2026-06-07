# WESLR RF Field Discovery Artifact V1

## Executive summary
This is a local, exploratory WESLR artifact for discovering whether WiFi/RF signal behavior can be translated into useful spatial, temporal, and vector-based representations.
It is intentionally open-ended.
It may later become an RF sensing artifact, a motion disturbance mapper, a home RF simulation artifact, a calibration tool, a signal anomaly analyzer, a visual RF-field projection system, a WESLR marketplace artifact, or something else discovered during testing.

## 1. Discovery artifact definition
This artifact defines a discovery-first path for investigating whether WiFi/RF signal changes inside an owner-controlled home can be translated into useful vectors, spatial hypotheses, calibration patterns, and eventually a visual RF-field projection.

It does not force a final category now.
It preserves unknowns, competing hypotheses, and exploratory branches.

## 2. Unknowns to preserve
The artifact must explicitly preserve these unknowns:
- Can router/repeater telemetry alone provide useful signal?
- Is RSSI enough?
- Is ping/jitter/link-quality enough?
- Is CSI required?
- Can a repeater create useful path diversity?
- Can movement be separated from normal WiFi traffic?
- Can static objects be mapped?
- Can moving objects be detected only as disturbance, not as shape?
- Can the owner’s floor plan improve inference?
- Can WESLR learn useful baselines?
- Can WESLR discover repeated signal motifs?
- Can WESLR generate useful vector formats from incomplete data?
- Can a game-like visualization be useful even if approximate?
- What hardware is worth adding later?
- What should never be claimed as certainty?

## 3. Discovery stages
These are exploratory stages, not fixed product levels.

### Stage 0 — Concept and schemas only
- no hardware
- no real signal data
- define possible data shapes
- define unknowns
- define synthetic examples

### Stage 1 — Existing router + existing WLAN repeater
- investigate what data may be available
- possible telemetry: RSSI, connected clients, link quality, jitter, latency, channel, packet loss, throughput, device roaming
- expected result unknown
- output should be hypothesis only

### Stage 2 — Local manual calibration
- owner performs controlled movement examples
- examples:
  - empty baseline
  - owner walks known path
  - door opens/closes
  - person sits still
  - appliance activity
  - repeater moved
- goal is not accuracy yet
- goal is to see if patterns repeat

### Stage 3 — Optional CSI research
- investigate CSI-capable devices only after design/review
- possible future sources:
  - ESP32 CSI
  - Linux-compatible CSI adapters
  - research-grade tools
- no commitment yet

### Stage 4 — Visualization experiment
- convert uncertain RF changes into visual fields
- floor plan first
- possible future 3D/game-style view
- blue/green/gray concept allowed as visual metaphor
- must show uncertainty

### Stage 5 — Artifact hardening
- only if earlier stages show value
- define package structure
- define local install
- define marketplace-readiness path
- synthetic examples only for marketplace candidate

## 4. Possible data translation forms
These translations are design candidates only; they are not claims that they already work.

### 4.1 Floor plan → spatial graph
Possible fields:
- room_id
- wall boundaries
- doors/openings
- approximate coordinates
- room labels
- excluded zones
- unknown material areas

### 4.2 Router/repeater → RF anchor graph
Possible fields:
- anchor_id
- anchor_type
- approximate position
- WiFi band
- channel
- data available
- trust level
- unknown fields

### 4.3 Signal observation → possible vector packet
Possible fields:
- timestamp
- source
- receiver/client if known
- RSSI
- link quality
- jitter
- latency
- packet loss
- throughput
- roaming event
- CSI amplitude if available later
- CSI phase if available later
- derived disturbance score
- derived stability score
- missing fields
- confidence
- alternative explanations

### 4.4 Time window → pattern candidate
Possible fields:
- start time
- end time
- affected signal paths
- repeated motif yes/no/unknown
- baseline deviation
- possible movement
- possible traffic artifact
- possible appliance artifact
- confidence
- notes

### 4.5 Visualization frame → uncertain RF projection
Possible fields:
- timestamp
- coordinate frame
- stable estimated areas
- disturbed estimated areas
- unknown areas
- confidence overlay
- explanation
- warnings

## 5. WESLR capability mapping
Map this artifact to WESLR capabilities as follows:

- **Broad Topic Domain Intake**
  - classify as: technical_research, privacy_sensitive_technology, home_environment_modeling, signal_analysis, artifact_discovery

- **UNKNOWN_ENGINE**
  - used to preserve unknowns, generate hypotheses, mutate possible vector formats, and identify unexpected signal behavior

- **RAW_SIGNAL_CARTOGRAPHER**
  - used to map strange or unintelligible signal patterns without flattening them too early

- **SIGNAL_VS_NOISE_ENGINE**
  - used to compare real movement patterns against WiFi traffic, appliance noise, interference, multipath drift, and random noise

- **BLINDSPOT_ENGINE**
  - used to ask what hidden variables may affect the signal:
    - wall material
    - furniture
    - humidity
    - people/pets
    - router position
    - repeater position
    - WiFi channel changes
    - device roaming
    - traffic load
    - HVAC
    - appliances

- **CALIBRATION_LEDGER**
  - used to track prediction, confidence, actual calibration label, correction, and whether WESLR becomes better calibrated over time

- **INVARIANT_MINER**
  - used to extract principles that remain true across experiments, such as:
    - router movement invalidates baseline
    - missing CSI lowers confidence
    - traffic can mimic disturbance
    - house-plan geometry helps only if anchor positions are known

- **GOVERNANCE_BOUNDARY_ENGINE**
  - used only to prevent unsafe misuse, public overclaiming, accidental marketplace release with private data, or certainty claims

## 6. Owner experiment model
The artifact should later support owner-controlled experiments such as:

- Experiment A: router + repeater baseline with no movement
- Experiment B: owner walks from known room to known room
- Experiment C: door opens/closes
- Experiment D: repeater moved slightly
- Experiment E: phone/client moves between rooms
- Experiment F: high WiFi traffic but no physical movement
- Experiment G: physical movement but low WiFi traffic
- Experiment H: furniture change
- Experiment I: static person sitting still
- Experiment J: unknown disturbance

For each experiment, the artifact should later be able to store:
- hypothesis
- signal changes
- expected result
- observed result
- confidence
- correction
- lesson learned

## 7. Visualization direction
The intended visual direction is exploratory.

Owner target idea:
- a game-like or Unreal-style visual projection where WiFi/RF propagation is represented across the home

Early version:
- 2D floor plan
- RF anchors shown
- signal paths shown as lines
- stable baseline shown conceptually blue
- disturbance/motion energy shown conceptually green
- unknown/no-data shown gray
- confidence shown separately
- explanation panel included

Later possible version:
- 3D space
- wave propagation metaphor
- moving disturbance field
- time slider
- calibration playback
- comparison between expected and observed field

Important:
Visualization must be treated as estimated signal interpretation, not literal vision.

## 8. Artifact package concept
Future package concept only:

`artifacts/rf_field_discovery_v1/`

Possible future files:
- `artifact_manifest.json`
- `unknowns_registry.json`
- `floor_plan_schema.json`
- `rf_anchor_schema.json`
- `signal_observation_schema.json`
- `pattern_candidate_schema.json`
- `visualization_frame_schema.json`
- `calibration_protocol.md`
- `synthetic_examples/`
- `marketplace_readiness.md`

This lane only defines the design document.
It does not implement the package.

## 9. Marketplace path without committing too early
Marketplace is a possible later outcome, not a current goal.

### M0 — Private owner experiment
- local only
- exploratory
- no public release

### M1 — Synthetic demo artifact
- no real home data
- no private floor plans
- no real RF logs
- no identity/occupancy history

### M2 — Local advanced-user artifact
- only if useful
- privacy warnings required
- local-only mode required
- no cloud requirement

### M3 — Marketplace candidate
- only after separate review
- clear limitations
- synthetic examples
- no surveillance language
- no medical/security certainty claims

### M4 — Public marketplace release
- only after explicit owner approval
- not part of this lane

## 10. Success criteria for this lane
This lane succeeds if:
- the discovery artifact is defined
- unknowns are preserved
- possible data translations are defined
- router/repeater-first path is included
- CSI is treated as optional future research
- WESLR capability mapping is clear
- visualization direction is included
- marketplace path is included but not activated
- no live sensing is implemented
- no private data is used
- no final product claim is made

## 11. Failure modes to track
Failure modes should be tracked, not used to kill the project.

- router/repeater data too weak
  - mitigation: keep Stage 0/1 hypotheses separate and compare telemetry sources before overcommitting
- RSSI too noisy
  - mitigation: preserve confidence and alternative explanations; test with manual calibration
- WiFi traffic mimics movement
  - mitigation: compare physical-movement runs against traffic-only runs
- movement not visible
  - mitigation: test repeatable path baselines and hardware variation later
- static presence invisible
  - mitigation: treat static presence as a separate hypothesis class, not as guaranteed detection
- multipath too ambiguous
  - mitigation: preserve uncertainty and add floor-plan context only when anchor positions are known
- floor plan not enough
  - mitigation: keep layout as one input, not the only source of truth
- anchor positions inaccurate
  - mitigation: track anchor trust level and unknown fields explicitly
- visualization looks more certain than it is
  - mitigation: show confidence separately and keep unknown areas visible
- WESLR invents patterns from noise
  - mitigation: require calibration ledger entries and alternative explanations
- marketplace path starts too early
  - mitigation: hold M3/M4 behind separate review
- private home data accidentally becomes artifact demo data
  - mitigation: use synthetic examples for demos and keep local-only boundaries strict

## 12. Future lanes
Propose these future lanes:
1. `REVIEW_WESLR_RF_FIELD_DISCOVERY_ARTIFACT_V1`
2. `DESIGN_WESLR_RF_FIELD_DISCOVERY_SCHEMAS_V1`
3. `IMPLEMENT_WESLR_RF_FIELD_DISCOVERY_SCHEMA_HELPERS_V1`
4. `DESIGN_WESLR_RF_FIELD_DISCOVERY_SYNTHETIC_EXAMPLES_V1`
5. `IMPLEMENT_WESLR_RF_FIELD_DISCOVERY_SYNTHETIC_EXAMPLE_BUILDER_V1`
6. `DESIGN_WESLR_RF_FIELD_DISCOVERY_VISUALIZATION_FRAME_SCHEMA_V1`
7. `IMPLEMENT_WESLR_RF_FIELD_DISCOVERY_VISUALIZATION_FRAME_HELPERS_V1`
8. `DESIGN_WESLR_RF_FIELD_DISCOVERY_ROUTER_REPEATER_RESEARCH_PLAN_V1`
9. `DESIGN_WESLR_RF_FIELD_DISCOVERY_CSI_RESEARCH_PLAN_V1`
10. `DESIGN_WESLR_RF_FIELD_DISCOVERY_LOCAL_IMPORT_BOUNDARY_V1`
11. `DESIGN_WESLR_RF_FIELD_DISCOVERY_MARKETPLACE_CANDIDATE_BOUNDARY_V1`

## OCC Final Report

1. Handshake result
- PASS

2. Start HEAD
- `0e3cff0a20d85809f871d575da738d69919bc794`

3. Target design lane
- `DESIGN_WESLR_RF_FIELD_DISCOVERY_ARTIFACT_V1`

4. WESLR repo root and branch
- Root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`

5. Files changed
- `docs/WESLR_RF_FIELD_DISCOVERY_ARTIFACT_V1.md`

6. Validation criteria
- Design-only artifact created
- Unknowns preserved
- Possible data translations defined
- Router/repeater-first path included
- CSI treated as optional future research
- WESLR capability mapping included
- Visualization direction included
- Marketplace path included but not activated
- No live sensing implemented
- No private data used
- No final product claim made

7. Final judgment
- `weslr_rf_field_discovery_artifact_v1_design_ready_for_review`
