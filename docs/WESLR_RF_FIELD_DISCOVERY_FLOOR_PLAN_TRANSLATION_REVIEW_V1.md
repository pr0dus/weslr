# WESLR RF Field Discovery Floor Plan Translation Review V1

## 1. Review scope
Reviewed exactly this document:

- `docs/WESLR_RF_FIELD_DISCOVERY_FLOOR_PLAN_TRANSLATION_V1.md`

This is a design review only. It does not import owner files, request the owner’s actual PDFs/screenshots, access router/repeater hardware, connect to Home Assistant, perform packet capture, collect CSI, implement OCR/PDF/image parsing, create a marketplace package, or add runtime wiring.

## 2. Repository state
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`
- Start HEAD: `3c2f79bffd9bea5d5e58bb2f9b1165a94e8b6cc7`
- Reviewed document: present
- Review document: newly created, untracked
- `git status --short`: tracked tree is clean; unrelated untracked files already exist in the repo

## 3. Review judgment
The floor-plan translation design is valid and ready for the local import boundary design step.

Final judgment:
- `weslr_rf_field_discovery_floor_plan_translation_v1_valid_ready_for_local_import_boundary`

Revision required:
- no

## 4. Criterion assessment

### 4.1 Input type coverage — PASS
The design supports vector PDF, scanned/image PDF, screenshots, owner-marked plans, hand-marked plans, and multi-floor plans.

### 4.2 Annotation convention — PASS
The design defines `R1`, `REP1`, `P1`, `PATH_A`, `SIT1`, `DOOR1`, `UNKNOWN_MATERIAL`, and `EXCLUDE`.

### 4.3 Translation pipeline — PASS
The pipeline includes PDF/page intake, floor/page separation, scale handling, coordinate frame creation, room extraction, wall extraction, opening/door/window extraction, semantic labels, anchor placement, calibration paths, uncertainty marking, environment packet generation, RF path hypothesis graph generation, and visualization base-layer generation.

### 4.4 Multi-layer vector method — PASS
The design is explicitly multi-layer and not a single embedding. It includes geometry, topology, RF anchor, obstruction/material, calibration, uncertainty, and visualization base vectors.

### 4.5 Existing schema mapping — PASS
The design maps outputs cleanly to:
- `RFDiscoveryEnvironmentCandidate`
- `RFDiscoveryAnchorCandidate`
- `RFDiscoveryVisualizationFrameCandidate`
- `RFDiscoveryCalibrationExperimentCandidate`
- `RFDiscoveryDecisionOutcomeCandidate`

### 4.6 RF path hypothesis correctness — PASS
The RF path graph is clearly hypothesis-only and does not claim propagation accuracy.

### 4.7 Quality levels — PASS
Q0–Q5 are defined and useful for progressive translation quality.

### 4.8 Owner PDF timing — PASS
Real owner PDFs/screenshots are delayed until translation design review, local import boundary design, owner approval of controlled sample import, redaction/annotation convention, and known target fields.

### 4.9 PDF before router access — PASS
The design states the PDF/sample protocol comes before router access.

### 4.10 Minimal first owner upload package — PASS
The design defines a future minimal package including the primary plan, router/repeater marks, scale/dimension if available, room labels, calibration points, and optional material notes.

### 4.11 Failure modes — PASS
The design includes failure modes and mitigations.

### 4.12 Capability honesty — PASS
The design does not assume OCC/OpenClaw can directly understand architectural PDFs by model vision alone. It stays hybrid/manual/deterministic-assisted and uncertainty-preserving.

## 5. Gaps
No blocking gaps found.

## 6. Recommendation
- Revision required: no
- Recommended next lane: `DESIGN_WESLR_RF_FIELD_DISCOVERY_LOCAL_IMPORT_BOUNDARY_V1`

## 7. Validation notes
- `git diff --check` passed
- `python3 weslr/tests/release_gate_v1.py` passed
- `bash scripts/weslr_release_check.sh` passed
- Protected files unchanged:
  - `weslr/chat_responder.py` ✅
  - `weslr/main.py` ✅
  - `main.py` ✅
  - `dialogue.py` ✅
  - `chat_ui.py` ✅
