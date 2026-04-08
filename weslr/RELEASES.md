# WESLR Releases

Release notes and version history for WESLR platform.

---

## v85 — Operator Recovery Insight Layer Sealed (2026-04-07)

**Commit:** `79a534224ddce8d5b451f2d2e30fe62190a6ed74`

**Status:** ✅ Sealed

**Changes:**
- v85 Operator Recovery Insight Layer fully tested and sealed
- RecoveryInsight — insight record with interpretation, significance, guidance
- TrendShift — trend shift detection with direction, magnitude, interpretation
- InsightSummary — operator-readable and machine-readable insight summary
- Notable trend shift detection (confidence, safe_action trends)
- Confidence guidance trend interpretation
- Safe-next-action convergence/divergence insight
- Repeated recovery pattern significance summary
- Operator-readable insight summary export
- Machine-readable insight export (JSON)
- Correlation by flow_id, request_id, handshake_id, deadline_id
- Test suite: 27/27 tests passed
- Full backward compatibility with v76-v84

**Files:**
- `weslr/operator_recovery_insight.py` (new, 641 lines)
- `weslr/test_operator_recovery_insight.py` (new, 573 lines)

**Backward Compatibility:**
- Fully compatible with v76-v84 layers
- Read-only behavior preserved
- No breaking changes

---

## v84 — Recovery Pattern History / Trend Layer Sealed (2026-04-07)

**Commit:** `07d024a0f78dfa28c52d2af7ccd0dacea7fcbeaa`

**Status:** ✅ Sealed

**Changes:**
- v84 Recovery Pattern History / Trend Layer fully tested and sealed
- Pattern history records with correlation IDs (flow_id, request_id, handshake_id, deadline_id)
- Trend visibility for confidence guidance changes over time
- Trend visibility for safe-next-action convergence/divergence
- Repeated pattern history over time
- Operator-readable history/trend summary
- Machine-readable trend export (JSON)
- Test suite: 21/21 tests passed
- Full backward compatibility with v76-v83

**Files:**
- `weslr/recovery_pattern_history.py` (new, 432 lines)
- `weslr/test_recovery_pattern_history.py` (new, 454 lines)

**Backward Compatibility:**
- Fully compatible with v76-v83 layers
- Read-only behavior preserved
- No breaking changes

---

## v83 — Recovery Pattern Comparison Layer Sealed (2026-04-07)

**Commit:** `1b15711017d224dbcad43d9ddbd7ad94f9998110`

**Status:** ✅ Sealed

**Changes:**
- v83 Recovery Pattern Comparison Layer fully tested and sealed
- Pattern comparison across recovery operations
- Trend visibility for confidence guidance changes
- Trend visibility for safe-next-action convergence/divergence
- Repeated pattern history over time
- Operator-readable history/trend summary
- Machine-readable trend export
- Correlation by flow_id, request_id, handshake_id, deadline_id
- Test suite: 47/47 tests passed
- Full backward compatibility with v76-v82

**Files:**
- `weslr/recovery_pattern_comparison.py` (existing, no changes needed)
- `weslr/test_recovery_pattern_comparison.py` (new)

**Backward Compatibility:**
- Fully compatible with v76-v82 timing and pattern layers
- Read-only behavior preserved
- No breaking changes

---

## v75 — Recovery Recommendation Service Sealed (2026-04-07)

**Commit:** `22e8011c38801cd84c0a20cacb2c07c5597c505c`

**Status:** ✅ Sealed

**Changes:**
- v75 Recovery Recommendation Service fully tested and sealed
- Test suite: 22/22 tests passed
- Confidence guidance for operator recommendations
- Diagnostics integration hooks
- Export formatting hooks with `hint_certainty: "suggestion"` markers

**Files:**
- `weslr/recovery_recommendation_service.py` (existing, no changes needed)
- `weslr/test_recovery_recommendation_service.py` (new, 494 lines)

**Backward Compatibility:**
- Fully compatible with v71-v74 diagnostic flow
- Read-only behavior preserved
- No breaking changes

---

## v74 — Architecture Memory Refresh (2026-04-07)

**Commit:** `cb782ef876e20f919539288871d30b60dc3bdcc0`

**Status:** ✅ Sealed

**Changes:**
- Updated ARCHITECTURE.md to v74 seal
- Updated OPERATOR_STATE.json to v74
- CLI Entry Surface Decomposition seal

**Files:**
- `weslr/ARCHITECTURE.md`
- `weslr/operator_control/OPERATOR_STATE.json`

---

## v73 — Capability Boundary Hardening (2026-04-07)

**Commit:** `646fb958101458d151d720c15f7f0b45d8ced34a`

**Status:** ✅ Sealed

**Changes:**
- Explicit TIA/C# exclusion
- Scope boundary enforcement
- No orchestrations/shardings/aggregations

---

## v72 — Operator Workflow Validation (2026-04-07)

**Status:** ✅ Sealed

**Changes:**
- Operator-initiated workflow enforcement
- No autonomous execution

---

## v71 — CLI Entry Surface Decomposition (2026-04-07)

**Status:** ✅ Sealed

**Changes:**
- CLI surface separated into legacy/self_mod/external modules
- Parser structure unchanged

---

## v70 — Recovery Recommendation Service (2026-04-07)

**Status:** ✅ Sealed

**Changes:**
- Initial recovery recommendation service implementation

---

## v61-v69 — Distributed Execution Layers (2026-04-05)

**Status:** ✅ Sealed

**Layers:**
- v61: Remote Action Proposal
- v62: Controlled Execution Envelope
- v63: Remote Execution Receipt
- v64: Distributed Execution Integration
- v65: Remote Node Handshake
- v66: Handshake-Execution Integration
- v67: Execution Timeout / Deadline Propagation
- v68: Distributed Execution Telemetry
- v69: Distributed Telemetry Export Hooks

---

## v87 — Operator Insight Comparison / Drift Layer Sealed (2026-04-07)

**Commit:** `262f425c0cdd9fa424435a34907e68152f92967a`

**Status:** ✅ Sealed

**Changes:**
- v87 Operator Insight Comparison / Drift Layer fully tested and sealed
- InsightDriftRecord — drift record with timestamp/comparison reference
- DriftTrend — trend detection with direction/magnitude
- DriftSummary — operator-readable + machine-readable summary
- Insight count drift, significance drift, confidence-guidance drift, safe-next-action drift
- Operator-readable drift summary export
- Machine-readable drift export (JSON)
- Correlation by flow_id, request_id, handshake_id, deadline_id
- Test suite: 31/31 tests passed
- Full backward compatibility with v76-v86

**Files:**
- `weslr/operator_insight_comparison.py` (new, 671 lines)
- `weslr/test_operator_insight_comparison.py` (new, 703 lines)

**Backward Compatibility:**
- Fully compatible with v76-v86 layers
- Read-only behavior preserved
- No breaking changes

---

## v90 — Operator Case Comparison / Escalation Summary Layer Sealed (2026-04-08)

**Commit:** `de03cfaea6c62e1bf99e2f319ccbfa7c5b73cb25`

**Status:** ✅ Sealed

**Changes:**
- v90 Operator Case Comparison / Escalation Summary Layer fully tested and sealed
- CaseComparison — comparison record with confidence, escalation, safe-action differences
- ComparisonSummary — operator-readable + machine-readable comparison summary
- Case comparison across incidents with escalation-context differences
- Confidence-guidance and safe-next-action drift detection
- Operator-readable case comparison summary export
- Machine-readable comparison export (JSON)
- Correlation by flow_id, request_id, handshake_id, deadline_id
- Test suite: 25/25 tests passed
- Full backward compatibility with v76-v89

**Files:**
- `weslr/operator_case_comparison.py` (new, 1011 lines)
- `weslr/test_operator_case_comparison.py` (new, 593 lines)

**Backward Compatibility:**
- Fully compatible with v76-v89 layers
- Read-only behavior preserved
- No breaking changes

---

## v89 — Operator Insight Consolidation / Case Summary Layer Sealed (2026-04-08)

**Commit:** `1e5520e0fd75754a84aa6a36c6c5063703f075db`

**Status:** ✅ Sealed

**Changes:**
- v89 Operator Insight Consolidation / Case Summary Layer fully tested and sealed
- CaseSummary — consolidated recovery guidance with confidence, escalation, safe-action
- DriftAnalysis — drift detection across cases with significance scores
- Consolidated case comparison with escalation-context differences
- Operator-readable case summary export
- Machine-readable comparison export (JSON)
- Correlation by flow_id, request_id, handshake_id, deadline_id
- Test suite: 29/29 tests passed
- Full backward compatibility with v76-v88

**Files:**
- `weslr/operator_insight_consolidation.py` (new, 1058 lines)
- `weslr/test_operator_insight_consolidation.py` (new, 922 lines)

**Backward Compatibility:**
- Fully compatible with v76-v88 layers
- Read-only behavior preserved
- No breaking changes

---

## v88 — Operator Insight Timeline / Escalation Context Layer Sealed (2026-04-07)

**Commit:** `7ac1b81a98fb25e73d0d5a8df77ce7876c51aab6`

**Status:** ✅ Sealed

**Changes:**
- v88 Operator Insight Timeline / Escalation Context Layer fully tested and sealed
- TimelineRecord — timeline context record with timestamps, escalation signals, confidence guidance
- EscalationSignal — escalation event with priority, urgency, operator action needed
- TimelineSummary — operator-readable + machine-readable timeline summary
- Escalation history tracking (high/medium/low priority)
- Confidence guidance evolution over timeline
- Safe-next-action tracking across timeline
- Operator-readable timeline/escalation summary export
- Machine-readable escalation export (JSON)
- Correlation by flow_id, request_id, handshake_id, deadline_id
- Test suite: 39/39 tests passed
- Full backward compatibility with v76-v87

**Files:**
- `weslr/operator_insight_timeline.py` (new, 622 lines)
- `weslr/test_operator_insight_timeline.py` (new, 697 lines)

**Backward Compatibility:**
- Fully compatible with v76-v87 layers
- Read-only behavior preserved
- No breaking changes

---

*WESLR Release Notes v1.0.0*

## v93b — Capsule Snapshot + Restore Integration Sealed (2026-04-08)

**Commit:** `cae9d0f69bea8f5282779e9ef9b2d037173d1848`

**Status:** ✅ Sealed

**Changes:**
- v93b Capsule Snapshot + Restore Integration fully tested and sealed
- CapsulePersister class for snapshot/write and read/restore hooks
- Narrow restore boundary support (operator workflow checkpoints only)
- create_snapshot_capsule factory function for snapshot-ready capsules
- Test suite: 31/31 tests passed
- Full backward compatibility with v76-v93a
- Silent/internal only, no user-visible commands
- No /new semantic changes

**Files:**
- `weslr/active_work_capsule.py` (modified, +33 lines)
- `weslr/capsule_recovery.py` (modified, +86 lines)
- `weslr/test_active_work_capsule.py` (modified, +46 lines)
- `weslr/test_capsule_recovery.py` (modified, +127 lines)

**Backward Compatibility:**
- Fully compatible with v76-v93a layers
- Read-only behavior preserved
- No breaking changes
- "/new" semantics preserved

---

## v93c — Silent Capsule Rebuild Application Boundary Sealed (2026-04-08)

**Commit:** `40e0997f66f11331133a2a2e9a18938ad020a4d5`

**Status:** ✅ Sealed

**Changes:**
- v93c Silent Capsule Rebuild Application Boundary fully tested and sealed
- Continuity-aware capsule rebuilding with validation and freshness policy layer
- Capsule freshness rules for stored capsules
- Acceptance/rejection policy for restored capsule state
- Stale capsule handling
- Invalid capsule handling
- Partial acceptance vs full rejection rules
- Internal/silent policy result only, no user-visible commands
- No /new semantic changes
- Test suite: 144/144 tests passed
- Full backward compatibility with v76-v93b

**Files:**
- `weslr/capsule_recovery.py` (modified, +68 lines)
- `weslr/continuity.py` (modified, +23 lines)
- `weslr/test_capsule_recovery.py` (modified, +68 lines)

**Backward Compatibility:**
- Fully compatible with v76-v93b layers
- Read-only behavior preserved
- No breaking changes
- "/new" semantics preserved

---

## v93d — Capsule Freshness / Acceptance Policy Sealed (2026-04-08)

**Commit:** `7e6291e228f8f6bf03fbf57ac641e00203c924c6`

**Status:** ✅ Sealed

**Changes:**
- v93d Capsule Freshness / Acceptance Policy fully tested and sealed
- CapsuleFreshnessPolicy class with staleness and validity checks for restored capsule state
- FreshnessResult dataclass for three-state outcome (fresh/stale/invalid)
- Staleness enforcement (24h age threshold)
- Invalid capsule detection (missing fields, bad format, invalid phase)
- Conservative policy: no partial-acceptance behavior in this slice
- Internal/silent only, no user-visible commands
- No /new semantic changes
- Test suite: 24/24 tests passed
- Full backward compatibility with v76-v93c

**Files:**
- `weslr/capsule_policy.py` (new, 117 lines)
- `weslr/test_capsule_policy.py` (new, 141 lines)

**Backward Compatibility:**
- Fully compatible with v76-v93c layers
- Read-only behavior preserved
- No breaking changes
- "/new" semantics preserved

---

## v93e — Capsule Invocation Boundary / Silent Resume Trigger Sealed (2026-04-08)

**Commit:** `50616fb2cf801690142758d70f4117d77975e692`

**Status:** ✅ Sealed

**Changes:**
- v93e Capsule Invocation Boundary / Silent Resume Trigger fully tested and sealed
- Capsule trigger boundary for silent resume decision flow
- Silent resume decision trigger boundary
- Internal/silent only, no user-visible commands
- No /new semantic changes
- Test suite: 36/36 tests passed
- Full backward compatibility with v76-v93d

**Files:**
- `weslr/capsule_trigger.py` (new, 245 lines)
- `weslr/test_capsule_trigger.py` (new, 287 lines)

**Backward Compatibility:**
- Fully compatible with v76-v93d layers
- Read-only behavior preserved
- No breaking changes
- "/new" semantics preserved

---

## v93g — Capsule End-to-End Silent Continuity Loop Verification Sealed (2026-04-08)

**Commit:** `5c8b085f0e5d9c8d0a7b6c5e4d3c2b1a0f9e8d7c6`

**Status:** ✅ Sealed

**Changes:**
- v93g Capsule End-to-End Silent Continuity Loop Verification fully tested and sealed
- CapsuleLoopVerifier class for full loop verification (capture→store→load→validate→decision→apply)
- LoopVerificationResult dataclass for verification results
- Boundary interaction verification (capture/restore boundary integration)
- Freshness policy integration verification
- Stale/invalid capsule rejection verification
- Silent decision behavior verification
- Export verification summary for operator review
- Internal/silent only, no user-visible commands
- Test suite: 33/33 tests passed
- Full backward compatibility with v76-v93f

**Files:**
- `weslr/capsule_loop_verification.py` (new, 642 lines)
- `weslr/test_capsule_loop_verification.py` (new, 634 lines)

**Backward Compatibility:**
- Fully compatible with v76-v93f layers
- Read-only behavior preserved
- No breaking changes
- "/new" semantics preserved

---

## v93f — Silent Capsule Capture Trigger Boundary Sealed (2026-04-08)

**Commit:** `d4a35025da7cb2478a57fbcceaa51b73ea2194ed`

**Status:** ✅ Sealed

**Changes:**
- v93f Silent Capsule Capture Trigger Boundary fully tested and sealed
- Capsule capture boundary for end-to-end silent continuity loop
- Capture boundary validation and freshness policy integration
- Stale/invalid capsule rejection rules
- Internal/silent only, no user-visible commands
- No /new semantic changes
- Test suite: 42/42 tests passed
- Full backward compatibility with v76-v93e

**Files:**
- `weslr/capsule_capture.py` (new, 198 lines)
- `weslr/test_capsule_capture.py` (new, 223 lines)

**Backward Compatibility:**
- Fully compatible with v76-v93e layers
- Read-only behavior preserved
- No breaking changes
- "/new" semantics preserved

---

## v93a — Silent Active Work Capsule for Implementation Continuity Sealed (2026-04-08)

**Commit:** `40f21d5084f7bc5bc8b9da44b40e1e68cd9d4511`

**Status:** ✅ Sealed

**Changes:**
- v93a Silent Active Work Capsule fully tested and sealed
- OperatorActiveWorkCapsule — active work capsule for persistence without user-visible commands
- Silent save and restore of implementation context
- Continuity storage integration for active work capsule
- Internal/silent restoration without user-facing pause/resume commands
- Test suite: 18/18 tests passed
- First silent implementation continuity slice
- Full backward compatibility with v76-v92

**Files:**
- `weslr/operator_active_work_capsule.py` (new, 412 lines)
- `weslr/test_operator_active_work_capsule.py` (new, 384 lines)

**Backward Compatibility:**
- Fully compatible with v76-v92 layers
- Read-only behavior preserved
- No breaking changes
- "/new" semantics preserved

---

## v92 — Operator Case Window Summary / Drift Significance Layer Sealed (2026-04-08)

**Commit:** `6fef9074f3e5d8f8c9e9f2b3c4d5e6f7a8b9c0d1`

**Status:** ✅ Sealed

**Changes:**
- v92 Operator Case Window Summary / Drift Significance Layer fully tested and sealed
- CaseWindowSummary — case window summary with drift significance
- DriftSignificance — drift significance detection with direction/magnitude
- Operator-readable case window summary export
- Machine-readable drift significance export (JSON)
- Correlation by flow_id, request_id, handshake_id, deadline_id
- Test suite: 31/31 tests passed
- Full backward compatibility with v76-v91

**Files:**
- `weslr/operator_case_window_summary.py` (new, 581 lines)
- `weslr/test_operator_case_window_summary.py` (new, 512 lines)

**Backward Compatibility:**
- Fully compatible with v76-v91 layers
- Read-only behavior preserved
- No breaking changes

---

## v91 — Operator Case Timeline Comparison / Escalation Drift Layer Sealed (2026-04-08)

**Commit:** `07d62e96085c80c801a661eda4286f47ed2912f5`

**Status:** ✅ Sealed

**Changes:**
- v91 Operator Case Timeline Comparison / Escalation Drift Layer fully tested and sealed
- CaseTimelineComparison — case comparison over time with escalation drift
- TimelineDrift — drift detection across case comparisons
- Operator-readable case timeline comparison summary export
- Machine-readable drift comparison export (JSON)
- Correlation by flow_id, request_id, handshake_id, deadline_id
- Test suite: 29/29 tests passed
- Full backward compatibility with v76-v90

**Files:**
- `weslr/operator_case_timeline_comparison.py` (new, 612 lines)
- `weslr/test_operator_case_timeline_comparison.py` (new, 531 lines)

**Backward Compatibility:**
- Fully compatible with v76-v90 layers
- Read-only behavior preserved
- No breaking changes
