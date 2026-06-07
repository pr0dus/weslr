# WESLR RF Field Discovery Local Import Boundary V1

## 1. Purpose
This document defines the boundary for future private local sample imports for RF Field Discovery.

It is designed to support:
- owner-provided PDF plans
- owner-marked screenshots
- owner text notes
- private local-only import
- extracted structured packets
- no repo commit of private source files
- no marketplace/public use

This lane does **not** import private files.
It only designs the controlled import boundary for later use.

## 2. Allowed private input directory
Future private inputs should live in a controlled local path such as:

`/data/data/com.termux/files/home/weslr_private_inputs/rf_field_discovery/`

Allowed future files may include:
- `EG_DG_13072024.pdf`
- `Ansichten_13072024.pdf`
- `Schnitt_13072024.pdf`
- `EG_R1_marked.png`
- `DG_REP1_marked.png`
- `owner_anchor_notes.md`

Exact filenames may be confirmed later.

This directory must remain outside:
- the WESLR repo
- `docs/`
- `tests/`
- artifacts intended for marketplace use
- `.weslr` runtime state unless separately approved

## 3. Forbidden locations
Private owner files must not be placed in:
- `docs/`
- `weslr/tests/`
- `artifacts/`
- committed repo paths
- public website repo paths
- marketplace package paths
- release-gate test fixtures
- generated public examples

## 4. Import permission model
Import state is tracked explicitly:
- `not_requested`
- `owner_notes_only`
- `owner_files_available_private_path`
- `controlled_sample_import_approved`
- `translation_packet_generated`
- `reviewed_packet_only`
- `raw_files_removed_or_retained_private`

Current state:
- `owner_notes_only`

## 5. Allowed actions before sample approval
Allowed before explicit sample approval:
- record owner notes in design/review docs
- design schemas and packet structure
- design import protocol
- define expected filenames
- define target extracted fields

Not allowed before sample approval:
- read files
- parse PDF
- render screenshots
- OCR
- copy files
- commit files
- use the real plan as a test fixture
- create a marketplace demo from a private file

## 6. Controlled sample import rules
After explicit owner approval, controlled sample import may allow:
- read files from the private path
- extract page metadata
- extract owner-marked anchor facts
- create a local structured translation packet
- summarize extraction quality
- keep uncertainty and missing fields
- create a redacted metadata summary

Still forbidden:
- commit source PDFs/images
- commit full screenshots
- commit private floor-plan geometry unless explicitly approved
- create public examples from a private plan
- upload or private-sync outside the local machine
- use as a marketplace demo
- infer unrelated private details

## 7. Output packet policy
Allowed future outputs:
- `RFDiscoveryEnvironmentCandidate`
- `RFDiscoveryAnchorCandidate`
- `RFDiscoveryVisualizationFrameCandidate`
- `RFDiscoveryCalibrationExperimentCandidate`
- `RFDiscoveryDecisionOutcomeCandidate`

Output levels:
- `private_full_packet`
- `redacted_review_summary`
- `synthetic_demo_packet`

Only redacted summaries may go into docs by default.
Private full packets stay in the private path unless separately approved.

## 8. Owner file manifest
Future private imports may use:

`owner_rf_field_import_manifest_v1.json`

Fields:
- `import_id`
- `created_at`
- `owner_approval`
- `source_files`
- `file_roles`
- `private_input_directory`
- `allowed_outputs`
- `forbidden_outputs`
- `anchor_notes`
- `redaction_required`
- `commit_raw_files_allowed: false`
- `marketplace_use_allowed: false`
- `router_access_allowed: false`
- `home_assistant_access_allowed: false`
- `packet_capture_allowed: false`
- `csi_collection_allowed: false`

## 9. Anchor note handling
Known owner notes may be preserved as example notes, but they are **not imported artifacts yet**.

Example note: R1
- floor: EG
- room: HAR
- reference: near Wasserzähler
- marked with red point on the EG screenshot
- approx. 25 cm from each adjacent wall
- height_from_floor_m: 1.10
- owner confidence: very high

Example note: REP1
- floor: DG
- zone: Flur / near Treppe
- reference: before entrance to main bath
- marked with red point on the DG screenshot
- height_from_floor_m: 1.20
- owner confidence: very high
- total house/ceiling height not formalized yet

Do not include actual screenshots in this boundary.

## 10. PDF before router access
Floor-plan/sample import comes before router access.

Router access should only be considered after:
- the local import boundary exists
- the owner sample protocol exists
- a floor-plan packet is generated and reviewed
- a router/repeater research plan exists
- the owner approves controlled local read

## 11. Failure modes
Track these failure modes with mitigation:

- private file accidentally committed
  - mitigation: keep private inputs outside the repo and exclude them from staging rules
- raw PDF copied into docs
  - mitigation: only allow redacted summaries in docs by default
- screenshot used as a test fixture
  - mitigation: forbid private screenshots in `weslr/tests/`
- OCR invents labels
  - mitigation: preserve uncertainty and require owner confirmation for labels
- owner notes diverge from plan
  - mitigation: keep notes and geometry separate; record conflicts explicitly
- filename/path confusion
  - mitigation: use one private input directory and an explicit manifest
- marketplace package accidentally includes private files
  - mitigation: forbid marketplace paths and keep private files outside packaging roots
- model overinterprets the floor plan
  - mitigation: preserve unknowns, confidence, and alternative interpretations
- router access requested too early
  - mitigation: gate router work behind local import boundary review and owner approval

## 12. Future lanes
Recommended next lanes:
1. `REVIEW_WESLR_RF_FIELD_DISCOVERY_LOCAL_IMPORT_BOUNDARY_V1`
2. `DESIGN_WESLR_RF_FIELD_DISCOVERY_OWNER_PDF_SAMPLE_PROTOCOL_V1`
3. `IMPLEMENT_WESLR_RF_FIELD_DISCOVERY_IMPORT_MANIFEST_HELPERS_V1`
4. `DESIGN_WESLR_RF_FIELD_DISCOVERY_FLOOR_PLAN_PACKET_HELPERS_V1`
5. `DESIGN_WESLR_RF_FIELD_DISCOVERY_ROUTER_REPEATER_RESEARCH_PLAN_V1`

## OCC Final Report

1. Handshake result
- PASS

2. Repo root
- `/data/data/com.termux/files/home/weslr-pr47-clean`

3. Branch
- `master`

4. Start HEAD
- `4505cef5f3c389863f789b6155b372f6c6349e4e`

5. End HEAD
- pending commit

6. Commit hash
- pending commit

7. Changed files
- `docs/WESLR_RF_FIELD_DISCOVERY_LOCAL_IMPORT_BOUNDARY_V1.md`
- `weslr/tests/release_gate_v1.py` (only if narrow allowance is required)

8. Release gate edit status
- updated with exact-path allowance for `docs/WESLR_RF_FIELD_DISCOVERY_LOCAL_IMPORT_BOUNDARY_V1.md`

9. Validation results
- `git diff --check`: PASS
- `python3 weslr/tests/release_gate_v1.py`: PASS
- `bash scripts/weslr_release_check.sh`: PASS

10. Protected file status
- `weslr/chat_responder.py` unchanged
- `weslr/main.py` unchanged
- `main.py` unchanged
- `dialogue.py` unchanged
- `chat_ui.py` unchanged

11. Final judgment
- `weslr_rf_field_discovery_local_import_boundary_v1_design_ready_for_review`

12. Recommended next lane
- `REVIEW_WESLR_RF_FIELD_DISCOVERY_LOCAL_IMPORT_BOUNDARY_V1`
