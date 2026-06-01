# WESLR Future Capability Portfolio and Signal Intelligence Roadmap V1

## 1. Purpose

This document defines WESLR’s future capability portfolio and signal-intelligence roadmap.

It separates:
- current implementation
- design-only concepts
- experimental research
- future runtime wiring
- public product claims

This is a governance document, not an implementation claim.

## 2. Current baseline

WESLR currently has a governed foundation for:
- broad topic ontology, intake, and planning
- project brief, architecture, stack, and file manifest generation
- code scaffold generation
- artifact writer boundary
- sandbox writer dry-run executor
- artifact provenance boundary
- time anchor, temporal retrieval, source scope, and safe memory retrieval executor
- Poison Shield helpers
- behavior / friction / behavior-pack direction

Current state remains:
- not public-ready
- not AGI
- not certified
- not autonomous self-modifying

## 3. Capability maturity model

Every future capability should be tracked with one maturity stage:
- `idea`
- `design_only`
- `metadata_helper`
- `dry_run`
- `sandboxed`
- `validated`
- `owner_approved_runtime`
- `pilot_limited`
- `public_safe`
- `deprecated_or_blocked`

Every capability record should also include:
- maturity
- authority level
- data sensitivity
- required boundaries
- validation requirements
- owner approval requirements
- public-claim status

## 4. Capability family A: Core cognition and answer formation

Scope:
- memory result ranker
- memory answer formation boundary
- final answer assembly
- uncertainty/confidence explanation
- contradiction handling
- source/evidence citation logic
- concept-boundary model
- context-selection layer

Recommended lanes:
- `DESIGN_WESLR_MEMORY_RETRIEVAL_RESULT_RANKER_V1`
- `DESIGN_WESLR_MEMORY_ANSWER_FORMATION_BOUNDARY_V1`
- `DESIGN_WESLR_FINAL_ANSWER_ASSEMBLY_BOUNDARY_V1`

Dependencies:
- time anchor / temporal retrieval
- source scope registry
- safe memory retrieval executor
- Poison Shield

## 5. Capability family B: Artifact/code generation and validation

Scope:
- code validation runner
- patch feedback loop
- artifact exporter
- real sandbox create executor
- generated-only edit executor
- dependency policy helper
- export bundle packager
- artifact friction cases

Recommended lanes:
- `DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1`
- `DESIGN_WESLR_PATCH_FEEDBACK_LOOP_V1`
- `DESIGN_WESLR_ARTIFACT_EXPORTER_V1`
- `DESIGN_WESLR_REAL_SANDBOX_CREATE_EXECUTOR_V1`

Dependencies:
- artifact provenance boundary
- sandbox writer boundary
- governed validation harnesses

## 6. Capability family C: Poison Shield / trust / authority defense

Scope:
- adversarial content classifier
- authority claim checkpoint
- tool-use firewall
- source-trust registry
- memory promotion quarantine
- document/image/OCR poison boundaries
- LLM-provider output quarantine

Principle:
Poison Shield must gate future external ingestion and provider use.

Dependencies:
- source scope registry
- safe memory retrieval executor
- artifact provenance boundary

## 7. Capability family D: Evidence graph and claim lifecycle

Scope:
- source/evidence graph
- claim lifecycle tracker
- public claim registry
- stale-claim detector
- contradiction tracker
- website/legal/marketing claim review
- provenance-to-claim linkage

Recommended lanes:
- `DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1`
- `DESIGN_WESLR_PUBLIC_CLAIM_LIFECYCLE_TRACKER_V1`

Dependencies:
- provenance records
- poison shield
- source-scope policy

## 8. Capability family E: Future-state forecasting engine

This is high priority.

Definition:
current state + signals + constraints + known patterns + uncertainty → possible futures + risk indicators + recommended actions

This is not prophecy and not certainty.

Potential inputs:
- WESLR project state
- commit / lane history
- validation results
- friction cases
- Home Assistant state
- PV / battery / heat pump / EV data
- electricity price
- grid carbon intensity
- country import/export flow
- weather forecast
- calendar / routine signals
- public market / product signals
- user / operator goals

Potential outputs:
- scenario set
- probability / likelihood labels
- uncertainty
- assumptions
- missing signals
- early warning indicators
- recommended next action
- do-nothing / wait option

Recommended lane:
- `DESIGN_WESLR_FUTURE_STATE_FORECASTING_ENGINE_V1`

Dependencies:
- evidence graph
- signal intake boundaries
- poison shield
- scenario simulation engine

## 9. Capability family F: Scenario simulation engine

Definition:
what happens if we choose path A, B, or C?

Use cases:
- launch public pilot now vs wait
- wire LLM now vs after validation
- allow real sandbox writes vs dry-run only
- energy action: charge battery now vs later
- PV / heat pump / EV schedule changes
- website / public claim changes
- product / business strategy
- WiFi / RF sensing prototype path
- memory / runtime integration choices

Outputs:
- scenario cards
- assumptions
- dependencies
- expected benefits
- failure modes
- risk level
- reversibility
- required approvals
- recommended experiment

Recommended lane:
- `DESIGN_WESLR_SCENARIO_SIMULATION_ENGINE_V1`

Dependencies:
- future-state forecasting engine
- evidence graph
- governed review panel

## 10. Capability family G: Energy / grid / Home Assistant signal intelligence

This is high priority.

Future capability:
WESLR can ingest owner-authorized local/home/grid signals and reason about energy actions.

Potential signals:
- Home Assistant entity states
- PV production
- battery state of charge
- grid import/export
- house load
- heat pump demand
- EV charger state
- electricity prices
- weather forecast
- grid carbon intensity
- fossil-fuel percentage
- country import/export flow
- grid congestion / curtailment signals where available

Possible external sources:
- Electricity Maps-style grid carbon and forecast data
- Energy-Charts-style import/export maps
- grid operator/public data
- weather providers
- local inverter / battery APIs
- Home Assistant integrations

Use cases:
- battery charge/discharge recommendations
- heat pump preheating strategy
- EV charging window suggestions
- PV surplus optimization
- carbon-aware automation
- price-aware automation
- country import/export awareness
- grid stress awareness
- dashboard generation
- anomaly detection

Boundaries:
- recommendation-only first
- Home Assistant read-only first
- no direct control first
- no destructive automation
- owner approval required for automations
- no unsafe electrical advice without domain boundary
- installer/operator mode must be explicit

Recommended lanes:
- `DESIGN_WESLR_HOME_ASSISTANT_SIGNAL_INTAKE_BOUNDARY_V1`
- `DESIGN_WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1`
- `DESIGN_WESLR_ENERGY_SCENARIO_SIMULATOR_V1`

Dependencies:
- source scope registry
- poison shield
- forecasting engine
- scenario simulation engine

## 11. Capability family H: WiFi / RF sensing research-to-prototype

Future capability as research, not surveillance.

Potential uses:
- consent-based occupancy / routine awareness
- non-camera safety support
- elderly / self-care reminders
- anomaly detection
- room activity inference
- energy optimization
- local presence / routine modeling
- assistive prompts

Strict boundaries:
- consent-based only
- local-first
- no covert tracking
- no cross-person surveillance
- no diagnosis / treatment claims
- no emergency reliability claims without validation
- no public claim before evidence
- privacy-sensitive technology boundary applies
- Poison Shield / source-scope / provenance apply

Recommended lanes:
- `DESIGN_WESLR_WIFI_RF_SENSING_RESEARCH_TO_PROTOTYPE_PROGRAM_V1`
- `DESIGN_WESLR_PRIVACY_SENSITIVE_SIGNAL_PROCESSING_BOUNDARY_V1`

Dependencies:
- consent model
- privacy-sensitive signal boundary
- poison shield
- evidence graph

## 12. Capability family I: Document intelligence

Scope:
- contracts / manuals / reports
- legal / privacy drafts
- technical manuals
- warranty docs
- uploaded PDFs
- obligation extraction
- version comparison
- missing clause detection
- owner question generation

Boundaries:
- Poison Shield first
- source scope required
- no legal advice claims
- no raw private dumps
- no untrusted document authority

Dependencies:
- document provenance
- source scope registry
- poison shield
- evidence graph

## 13. Capability family J: Research-to-prototype engine

Scope:
- metamaterials
- medical software pathway
- industrial automation
- robotics
- energy systems
- AI system architecture
- language / vocabulary
- unknown future topics

Flow:
research question → evidence map → boundary check → project brief → prototype architecture → file manifest → scaffold → validation → friction capture

Dependencies:
- evidence graph
- governed internal review
- artifact provenance boundary
- code generation boundaries

## 14. Capability family K: Governed internal review panel

Internal metadata reviewers:
- Builder
- Security Critic
- Evidence Checker
- User Advocate
- Legal / Policy Critic
- Cost / Complexity Critic
- Future-State Analyst
- Failure-Mode Analyst

Rules:
- not autonomous agents
- no hidden tool use
- no runtime chaos
- structured review packets only

Recommended lane:
- `DESIGN_WESLR_GOVERNED_INTERNAL_REVIEW_PANEL_V1`

Dependencies:
- evidence graph
- claim lifecycle
- artifact provenance
- poison shield

## 15. Capability family L: LLM / provider candidate generation

Future LLM use:
- provider drafts candidate content
- WESLR scopes, quarantines, normalizes, validates, and gates
- model cannot grant authority
- provider output must be provenance-recorded
- Poison Shield scans provider output
- artifact writer boundary controls materialization

Recommended lane:
- `DESIGN_WESLR_GOVERNED_LLM_PROVIDER_ARTIFACT_GENERATION_BOUNDARY_V1`

Dependencies:
- poison shield
- artifact provenance boundary
- artifact writer boundary
- claim lifecycle controls

## 16. Capability family M: Operator workflow engine

Scope:
- next-lane recommendation
- blocked-state tracking
- review queue
- commit / lane history
- readiness summary
- what should I do next?
- handover prompt generation
- owner approval packet generation

Recommended lane:
- `DESIGN_WESLR_OWNER_OPERATOR_WORKFLOW_ENGINE_V1`

Dependencies:
- evidence graph
- claim lifecycle tracker
- validation records
- approval workflow metadata

## 17. Capability family N: Voice and ambient presence

Voice comes later, after reasoning / memory / authority are strong.

Owner preference:
voice active / available by default later, with explicit off switch.

Boundaries:
- no always-on surveillance
- consent and local device boundary
- no hidden recording
- no unscoped memory writes
- no tool execution from overheard speech without approval

Dependencies:
- privacy-sensitive signal boundary
- poison shield
- explicit consent model
- owner workflow engine

## 18. Capability dependencies

Selected dependency map:
- LLM provider boundary depends on Poison Shield + provenance + artifact writer boundary
- Real sandbox create depends on artifact writer boundary + provenance + sandbox writer design
- Energy signal intelligence depends on source scope + Poison Shield + Home Assistant signal boundary
- WiFi / RF sensing depends on privacy-sensitive signal boundary + consent model + Poison Shield
- Memory answer formation depends on time anchor + retrieval plan + source registry + safe retrieval executor + ranker
- Public pilot depends on deletion / export / consent / storage / privacy / security boundaries

## 19. Recommended implementation order

Near-term order:
1. `DESIGN_WESLR_FUTURE_CAPABILITY_PORTFOLIO_AND_SIGNAL_INTELLIGENCE_ROADMAP_V1`
2. `DESIGN_WESLR_FUTURE_STATE_FORECASTING_ENGINE_V1`
3. `DESIGN_WESLR_SCENARIO_SIMULATION_ENGINE_V1`
4. `DESIGN_WESLR_HOME_ASSISTANT_SIGNAL_INTAKE_BOUNDARY_V1`
5. `DESIGN_WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1`
6. `DESIGN_WESLR_WIFI_RF_SENSING_RESEARCH_TO_PROTOTYPE_PROGRAM_V1`
7. `DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1`
8. `DESIGN_WESLR_MEMORY_RETRIEVAL_RESULT_RANKER_V1`
9. `DESIGN_WESLR_GOVERNED_LLM_PROVIDER_ARTIFACT_GENERATION_BOUNDARY_V1`

## 20. Non-claims

This roadmap does not claim current implementation of all capabilities.
It does not claim AGI, consciousness, sentience, official Turing result, certification, product readiness, security certification, medical reliability, energy optimization guarantee, or public pilot readiness.

## 21. Final judgment

This roadmap is ready as the design basis for the forecasting engine and downstream capability-family planning.

Final judgment:
`future_capability_portfolio_signal_intelligence_roadmap_ready_for_forecasting_engine_design`
