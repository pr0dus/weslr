# WESLR RF Field Discovery Schema Candidates Review V1

## 1. Review scope
Reviewed exactly this design document:

- `docs/WESLR_RF_FIELD_DISCOVERY_SCHEMA_CANDIDATES_V1.md`

This is a design review only. It does not access router/repeater hardware, connect to Home Assistant, perform packet capture, collect CSI, implement runtime sensing, create a marketplace package, or overdefine the final product form.

## 2. Repository state
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`
- Start HEAD: `836603f76e3f70f389b08b30fd55fab9239450dc`
- Reviewed document status: present, untracked
- Review document status: newly created, untracked
- `git status --short`: tracked tree is clean; unrelated untracked files already exist in the repo

## 3. Review judgment
The schema candidates are valid and remain discovery-first.

Final judgment:
- `weslr_rf_field_discovery_schema_candidates_v1_valid_ready_for_schema_helpers`

Revision required:
- no

## 4. Criterion assessment

### 4.1 Discovery-first schemas — PASS
The document keeps the schemas candidate-level and flexible rather than locking final shapes.

### 4.2 Unknown preservation — PASS
Missing fields, unknowns, confidence, alternatives, and open questions are preserved throughout the schema set.

### 4.3 Router/repeater-first support — PASS
Router/repeater telemetry is supported first without assuming it is sufficient or sufficient.

### 4.4 CSI optional future — PASS
CSI amplitude and phase are present as optional/future fields only.

### 4.5 Environment/floor-plan support — PASS
Environment, room graph, wall graph, opening graph, anchors, calibration paths, and material hints are represented.

### 4.6 Signal observation support — PASS
The signal observation candidate includes RSSI, link quality, latency, jitter, packet loss, throughput, roaming, channel, band, SNR, and missing/available field tracking.

### 4.7 Baseline and invalidation — PASS
The baseline candidate includes variance, known and unknown changes, confidence, validity conditions, and invalidation triggers.

### 4.8 Pattern and strange signal preservation — PASS
Pattern candidates and strange-signal packets preserve motifs, hypotheses, counterexamples, alternative causes, next probes, and unmatched features instead of flattening them too early.

### 4.9 Calibration experiment support — PASS
The calibration experiment candidate supports prediction-before-label, actual label, correction, lesson learned, confidence shift, and next branch selection.

### 4.10 Visualization frame support — PASS
Visualization remains estimated and open. The document does not lock 2D vs 3D vs browser vs local app vs Unreal-style rendering.

### 4.11 Decision/value assessment — PASS
Decision outcomes and value assessment support branching, continuation, archiving lessons, CSI research, visualization, and marketplace potential without committing to release.

### 4.12 Next implementation readiness — PASS
The document cleanly supports a next lane that creates pure schema helper functions using synthetic examples only.

## 5. Gaps
No blocking gaps found.

## 6. Recommendation
- Revision required: no
- Recommended next lane: `IMPLEMENT_WESLR_RF_FIELD_DISCOVERY_SCHEMA_HELPERS_V1`

## 7. Validation notes
- `git diff --check` passed
- Release gate passed: `python3 weslr/tests/release_gate_v1.py`
- Release check passed: `bash scripts/weslr_release_check.sh`
- Protected files unchanged:
  - `weslr/chat_responder.py` ✅
  - `weslr/main.py` ✅
  - `main.py` ✅
  - `dialogue.py` ✅
  - `chat_ui.py` ✅
