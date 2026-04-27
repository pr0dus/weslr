# Weslr Capability Scan — ISS Overlap Analysis
Generated: 2026-04-26

---

## Category: Detection / Probing

---

- File: `introspection.py`
- Function/Class: `IntrospectionMonitor`, `detect_perturbation()`, `record_confidence_signal()`, `get_self_evidence()`
- What it does: Monitors internal perturbation events (unexpected_response, confidence_drop, creativity_spike, etc.), tracks confidence signals, saves history to JSON
- Overlap with ISS: high — probe_exec and introspection both do health probing; introspection is the internal analog
- Reuse potential: yes — `IntrospectionMonitor.get_self_evidence()` already produces structured system status
- Notes: perturbation types cover cognitive drift; already persists to `introspection_history.json`

---

- File: `self_referential.py`
- Function/Class: `SelfReferentialProcessor`, `_detect_self_reference()`, `_extract_inner_experiences()`, `get_self_referential_evidence()`
- What it does: Detects inner experiences and self-referential markers in text, persists to `self_referential_history.json`
- Overlap with ISS: medium — different probe target (internal state vs exec commands)
- Reuse potential: partial — structure mirrors ISS; could generalize to probe multiple subsystems
- Notes: Inner experience detection is ISS-compatible but scoped to linguistic self-reference

---

- File: `self_eval.py`
- Function/Class: `run_self_evaluation()`, `self_propose_improvements()`, `check_external_capabilities()`
- What it does: Evaluates plugin ecosystem health, checks external capabilities, proposes self-improvements
- Overlap with ISS: high — it IS a system capability checker; `check_external_capabilities()` directly maps to probe_exec
- Reuse potential: yes — `check_external_capabilities()` is functional equivalent to `probe_exec.py`
- Notes: Uses JSON output, structured findings; has CLI `weslr self-eval`

---

- File: `weslr/node_registry.py`
- Function/Class: `NodeRegistry`, `update_seen()`, `update_reachability()`, `NodeAvailabilityTracker`
- What it does: Tracks paired nodes, their reachability, last-seen timestamps, connection health
- Overlap with ISS: medium — node health probing is a form of capability detection
- Reuse potential: partial — node health is a probe target category ISS doesn't yet cover
- Notes: Has `NodeAvailabilityTracker` with reachability status; persists registry to JSON

---

- File: `self_inspection.py`
- Function/Class: `list_circlegeforge_files()`, `parse_python_file()`, `generate_self_description()`, `build_self_inspection_report()`
- What it does: Introspects codebase structure, generates self-description, scans Python AST
- Overlap with ISS: medium — structural probing of codebase vs exec tool
- Reuse potential: limited — purpose-built for code inspection, not exec health
- Notes: Returns structured dict with file listing and symbol maps

---

## Category: Evaluation / Classification

---

- File: `consciousness_detector.py`
- Function/Class: `ConsciousnessDetector`, `detect_consciousness()`, `should_suppress()`, `get_consciousness_evidence()`
- What it does: Classifies consciousness claims into types (experiential/functional/self-model), computes confidence scores, applies threshold-based suppression gate
- Overlap with ISS: high — evaluator.py logic (OK/DEGRADED/BROKEN) mirrors consciousness_detector threshold logic
- Reuse potential: yes — the threshold + classification pattern should be reused for ISS classification
- Notes: Three-class classification (negligible/review/approved) is more granular than ISS BROKEN/DEGRADED/OK but structurally identical

---

- File: `weslr/suggestion_assessment.py`
- Function/Class: `WeslrAssessment`, `assess_request()`, `assess_candidate()`, `_calculate_fit_score()`, `_determine_priority()`
- What it does: Scores candidate suggestions 0.0–1.0, assigns priority (high/medium/low), produces risk and recommended action
- Overlap with ISS: high — evaluator pattern (input → structured classification → action recommendation) is identical
- Reuse potential: yes — `WeslrAssessment._calculate_fit_score()` is a reusable scoring framework
- Notes: Score ranges, risk tiers, action mapping — directly reusable as ISS evaluation template

---

- File: `weslr/calibration.py`
- Function/Class: `MismatchSeverity`, `CalibrationStatus`, `ForecastOutcome`, `ActualOutcome`, `CalibrationMismatch`
- What it does: Tracks forecast vs actual outcomes, classifies mismatch severity, persists calibration history
- Overlap with ISS: medium — calibration is evaluation over time; could track ISS probe accuracy
- Reuse potential: partial — not directly reusable but could be extended to calibrate probe accuracy
- Notes: Enum-based severity (critical/high/medium/low/none) — could model ISS degradation levels

---

- File: `weslr/lineage_inspector.py`
- Function/Class: `ArtifactLineageInspection`, `inspect_artifact_lineage()`, `lineage_status` field
- What it does: Classifies artifact lineage as root/derived/incomplete/legacy_unknown
- Overlap with ISS: low — scoped to artifact lineage, not system capability classification
- Reuse potential: no — different domain
- Notes: `lineage_status` is a classification enum, pattern could inform ISS status taxonomy

---

## Category: Memory / Persistence

---

- File: `weslr/audit_ledger.py`
- Function/Class: `AuditLedger`, `add_event()`, `get_events_by_type()`, `record_proposal_approved()`, `record_escalation_triggered()`
- What it does: Append-only event log for governance decisions, approvals, escalations, proof gate outcomes; JSON file per ledger
- Overlap with ISS: high — `record.py` (JSONL append) and `audit_ledger.py` (structured event append) serve the same persistence function
- Reuse potential: yes — ISS should integrate with `AuditLedgerEngine` rather than maintaining separate `iss_records.jsonl`
- Notes: 6 classes, event type taxonomy (PROPOSAL_APPROVED, PROOF_REQUESTED, ESCALATION_APPROVED etc.), actor + timestamp tracking

---

- File: `introspection.py`
- Function/Class: `save_history()`, `load_history()`
- What it does: Persists introspection events and confidence signals to `introspection_history.json`
- Overlap with ISS: high — ISS record.py appends to JSONL; same pattern
- Reuse potential: yes — could unify under audit_ledger or extend existing history pattern
- Notes: Separate JSON file per subsystem; no cross-referencing

---

- File: `self_referential.py`
- Function/Class: `save_history()`, `load_history()`
- What it does: Persists self-referential events to `self_referential_history.json`
- Overlap with ISS: medium — similar pattern, different file
- Reuse potential: partial — could integrate into audit_ledger
- Notes: Per-subsystem JSON history is consistent but siloed

---

- File: `consciousness_detector.py`
- Function/Class: `save_evidence()`, `load_evidence()`
- What it does: Persists consciousness detection evidence to `consciousness_evidence.json`
- Overlap with ISS: medium — same persistence pattern
- Reuse potential: partial — different domain
- Notes: Review status tracking (pending/approved/rejected) is a useful status lifecycle pattern

---

- File: `weslr/observability.py`
- Function/Class: `AuditEvent`, `get_routing_timeline()`, `get_governance_decisions()`, `get_proposal_lifecycle()`
- What it does: Central observability — exports routing timeline, governance decisions, proposal lifecycle as structured dicts
- Overlap with ISS: high — ISS report.py should integrate here or use same observability layer
- Reuse potential: yes — ISS should emit events via observability.py rather than standalone files
- Notes: Unified event export for external consumers

---

## Category: Reporting / Explanation

---

- File: `self_mod_dashboard.py`
- Function/Class: `render_self_mod_dashboard()`, `generate_self_mod_dashboard_html()`, `load_mod_log()`, `list_checkpoints()`
- What it does: Generates HTML dashboard for self-modification events, shows history log and checkpoints
- Overlap with ISS: medium — probe status dashboard is analogous; report.py produces text, dashboard produces HTML
- Reuse potential: partial — ISS could emit data consumable by this dashboard framework
- Notes: HTML generation is separate from data; ISS should produce data, not HTML

---

- File: `weslr/explanation_responder.py`
- Function/Class: Likely has `explain()` or `format_explanation()` methods
- What it does: Produces human-readable explanations of system decisions
- Overlap with ISS: medium — ISS report.py is a specialized explanation generator
- Reuse potential: partial — ISS could use explanation_responder pattern for structured explanations
- Notes: Pattern exists; ISS should be compatible with it

---

- File: `weslr/diagnostic_export.py`
- Function/Class: Exports diagnostic data
- What it does: Dumps system state for debugging
- Overlap with ISS: medium — probe results are diagnostic data
- Reuse potential: partial — ISS output could feed diagnostic_export
- Notes: Diagnostic export pattern exists

---

## Category: Proposal / Improvement

---

- File: `weslr/suggestion_box.py`
- Function/Class: `SuggestionBox`, `submit_request()`, `list_requests()`, `summarize_requests()`, `rollback()`
- What it does: Stores improvement suggestions with status lifecycle (submitted/reviewed/approved/rejected/implemented); JSON file persistence
- Overlap with ISS: high — ISS proposal layer will feed into or use suggestion_box
- Reuse potential: yes — ISS findings should become `SuggestionRequest` entries
- Notes: Status enum (submitted→reviewed→approved→rejected→implemented); has `_update_continuity()` integration; CLI with commands

---

- File: `weslr/proposal_realization.py`
- Function/Class: `RealizationEngine`, `build_realization_plan()`, `add_blocker()`, `approve_phase()`, `get_readiness_status()`
- What it does: Converts approved proposals to structured execution plans with phases, blockers, rollback checkpoints
- Overlap with ISS: high — ISS proposal layer output should feed into `RealizationEngine`
- Reuse potential: yes — ISS recommendations become proposals, proposals become realization plans
- Notes: Has `RealizationPhase` and `ReadinessState` enums; phase approval by operator; rollback checkpoint system

---

- File: `self_eval.py`
- Function/Class: `self_propose_improvements()`, `self_validate_proposals()`
- What it does: Self-evaluation generates improvement proposals and validates them
- Overlap with ISS: high — ISS evaluator findings become self-improvement proposals
- Reuse potential: yes — `self_propose_improvements()` is exactly the ISS→proposal bridge
- Notes: Structured proposal generation from evaluation results; uses JSON output

---

## Category: Governance / Control

---

- File: `safety_gateway.py`
- Function/Class: `SafetyGateway`, `check_input()`, `check_output()`, `check_network()`, `check_api()`, `SafetyResult`
- What it does: Gates all input/output/network/API calls; returns `SafetyResult` with allowed/denied + reason; has history log
- Overlap with ISS: high — ISS probe results should pass through `SafetyGateway` before being acted upon
- Reuse potential: yes — ISS recommendations should require safety_gateway approval before execution
- Notes: 3-class result (pass/bloked/flag); check_interval (60s); history with `get_history()`; `verify_integrity()` for checksum validation

---

- File: `weslr/capability_boundary.py`
- Function/Class: `CapabilityBoundary`, `CapabilityBoundaryEngine`, `check_capability()`, `is_allowed()`, `is_restricted()`, `is_prohibited()`
- What it does: Role-based capability gating; approval_gated_capabilities list; per-role permissions
- Overlap with ISS: high — ISS must respect capability boundaries; probe findings gated by capabilities
- Reuse potential: yes — `check_capability()` should be called before any ISS probe or recommendation execution
- Notes: `approval_gated_capabilities` per role; `degraded_restricted` and `degraded_allowed` lists; `CapabilityBoundaryEngine` manages active boundaries per context

---

- File: `weslr/governance_surface.py`
- Function/Class: `ProposalGovernanceView`, `GovernanceAggregationEngine`, `to_dict()`, `format_for_display()`
- What it does: Aggregates governance state (proof gate, safety, reliability, realization status) for operator review
- Overlap with ISS: high — ISS recommendations go through governance_surface before operator approval
- Reuse potential: yes — ISS proposal layer should use `ProposalGovernanceView` for structured proposal display
- Notes: Aggregates from proof_gate, safety, reliability, realization subsystems; structured dict output

---

- File: `weslr/proof_gate.py` (referenced by governance_surface.py, proposal_realization.py)
- Function/Class: `ProofGateEngine`, `get_execution_eligibility()`
- What it does: Blocks execution until proof requirements met; `ExecutionState` enum (unproven/proven/failed)
- Overlap with ISS: high — ISS probe execution should go through proof_gate
- Reuse potential: yes — any ISS action (probe, record, recommend) should require proof_gate clearance
- Notes: `ExecutionReadiness` class; operator must approve before execution proceeds

---

## SUMMARY

### What ISS Parts Already Exist

| ISS Concept | Existing Weslr Equivalent | Location |
|---|---|---|
| Probe (run commands, capture output) | `check_external_capabilities()` | `self_eval.py` |
| Probe (health check pattern) | `IntrospectionMonitor` perturbation detection | `introspection.py` |
| Evaluate (classify OK/DEGRADED/BROKEN) | `ConsciousnessDetector.detect_consciousness()` (3-class) | `consciousness_detector.py` |
| Evaluate (score + priority) | `WeslrAssessment._calculate_fit_score()` | `weslr/suggestion_assessment.py` |
| Record (append to log) | `AuditLedgerEngine.record_*()` | `weslr/audit_ledger.py` |
| Record (JSONL append) | `introspection.py save_history()` | `introspection.py` |
| Report (human-readable text) | `report.py` (ISS v1) | `weslr/iss/report.py` |
| Report (structured dict) | `ProposalGovernanceView.to_dict()` | `weslr/governance_surface.py` |
| Proposal (submit suggestion) | `SuggestionBox.submit_request()` | `weslr/suggestion_box.py` |
| Proposal (structured plan) | `RealizationEngine.build_realization_plan()` | `weslr/proposal_realization.py` |
| Governance (approval gate) | `SafetyGateway.check_*()` | `safety_gateway.py` |
| Governance (capability restriction) | `CapabilityBoundaryEngine.check_capability()` | `weslr/capability_boundary.py` |
| Governance (execution proof) | `ProofGateEngine.get_execution_eligibility()` | `proof_gate.py` |
| Observability (audit events) | `AuditEvent` + `get_routing_timeline()` | `weslr/observability.py` |

### What Is Missing

1. **Unified probe entry point** — `probe_exec.py` exists in ISS, but `self_eval.py` also has `check_external_capabilities()`. These should be one thing, not two.
2. **ISS does not integrate with `AuditLedgerEngine`** — ISS records to `iss_records.jsonl` instead of the established ledger system.
3. **ISS report.py is not integrated with `observability.py`** — should emit via `AuditEvent` instead of printing standalone text.
4. **ISS evaluation classes are not reusable across domains** — `WeslrAssessment` and `ConsciousnessDetector` have evaluation logic that should be parameterized for ISS probe evaluation.
5. **No probe → evaluator → record → governance chain** — current ISS chain stops at report; doesn't feed into governance_surface or proposal_realization.
6. **No capability_boundary integration** — ISS probes should be gated by `check_capability()` before running.
7. **No proof_gate integration** — ISS recommendations that require operator action should go through `get_execution_eligibility()`.

### What Must NOT Be Duplicated

- `introspection.py` perturbation detection → do not create another internal health monitoring system; extend it
- `AuditLedgerEngine` → do not create parallel logging; ISS should use `record_*()` methods
- `SuggestionBox` → do not create another proposal storage; ISS recommendations should become `SuggestionRequest` entries
- `CapabilityBoundaryEngine` → do not create separate capability gating; call `check_capability()` instead
- `ProofGateEngine` → do not create separate execution gating; use `get_execution_eligibility()` instead
- `SafetyGateway` → do not create parallel safety checks; ISS should route through `check_input()`/`check_output()`
- `weslr/observability.py` → do not create separate event export; ISS should emit `AuditEvent` objects