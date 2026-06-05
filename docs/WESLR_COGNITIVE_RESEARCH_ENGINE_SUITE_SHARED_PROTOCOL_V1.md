# WESLR Cognitive Research Engine Suite Shared Protocol V1

## 1. Design status
- `DESIGN_WESLR_COGNITIVE_RESEARCH_ENGINE_SUITE_SHARED_PROTOCOL_V1`
- Design only.
- This protocol defines shared metadata/report shape for future cognitive research engines.
- LLM proposes; WESLR tests.
- Internal creativity is preserved.
- Public/export claims are controlled externally.
- No engine is implemented in this lane.

## 2. Purpose
The protocol exists to provide one shared, validation-bounded, metadata-only report shape for future research engines that explore uncertainty, signal structure, gaps, calibration, invariants, contradictions, and cross-domain transfer patterns.

It must:
- keep engine outputs comparable
- keep authority bounded
- keep public claims external and controlled
- preserve internal hypothesis generation without turning hypotheses into authority
- support future review, replay, and safe comparison

It must not:
- implement any engine
- produce live user-facing answers
- provide prediction authority
- provide answer authority
- provide runtime authority
- provide public-readiness authority

## 3. Shared packet: `CognitiveResearchRunV1`
A future run/report must use the following shared packet shape.

### 3.1 Required fields
- `schema_version`
- `run_id`
- `engine_name`
- `engine_family`
- `research_mode`
- `domain`
- `domain_subtype`
- `system_level`
- `artifact_scale`
- `source_scope`
- `input_artifact_ref`
- `input_artifact_type`
- `input_summary`
- `observations`
- `extracted_signals`
- `motif_candidates`
- `operator_candidates`
- `invariant_candidates`
- `hypotheses`
- `predictions`
- `confidence_map`
- `uncertainty_map`
- `constraint_map`
- `safety_boundary`
- `hazard_flags`
- `validation_route`
- `required_expert_review`
- `source_requirements`
- `experiment_type`
- `simulation_before_real_world`
- `non_actionable_research_only`
- `forbidden_action_notes`
- `cross_domain_analogies`
- `candidate_transfer_patterns`
- `failure_mode_map`
- `measurement_gap_map`
- `operator_gap_map`
- `language_gap_map`
- `unknown_unknowns`
- `probes`
- `mutations`
- `outcomes`
- `corrections`
- `compressed_lesson`
- `next_experiments`
- `llm_helper_role`
- `public_claim_status`
- `boundary_status`
- `denied_authority`
- `safe_metadata`

### 3.2 Required semantics
- `schema_version`: protocol version label.
- `run_id`: stable run identifier.
- `engine_name`: selected engine name from the allowlist.
- `engine_family`: selected engine family from the allowlist.
- `research_mode`: declared mode such as exploratory, calibration, gap discovery, raw-signal, invariant mining, contradiction analysis, or cross-domain transfer.
- `domain`: coarse domain label.
- `domain_subtype`: finer domain label.
- `system_level`: the level under study, such as component, subsystem, workflow, environment, or ecosystem.
- `artifact_scale`: scale of the input artifact or corpus.
- `source_scope`: provenance scope for the artifact(s).
- `input_artifact_ref`: safe reference to an artifact, corpus, or report.
- `input_artifact_type`: type label for the artifact.
- `input_summary`: bounded summary of the input.
- `observations`: safe observations extracted from inputs.
- `extracted_signals`: signal labels or patterns extracted from observations.
- `motif_candidates`: repeatable motif labels, not conclusions.
- `operator_candidates`: possible operators/mechanisms, not authority.
- `invariant_candidates`: candidate invariants or stable constraints.
- `hypotheses`: bounded hypotheses only.
- `predictions`: qualitative predictions or branch labels only where permitted.
- `confidence_map`: confidence metadata, not authority.
- `uncertainty_map`: uncertainty labels and reasons.
- `constraint_map`: constraints that bind the run.
- `safety_boundary`: required safety boundary for sensitive domains.
- `hazard_flags`: hazard or risk flags.
- `validation_route`: how the run may be validated.
- `required_expert_review`: whether expert review is required.
- `source_requirements`: provenance requirements.
- `experiment_type`: simulation, dry-run, thought experiment, controlled review, or other bounded research mode.
- `simulation_before_real_world`: boolean or equivalent flag requiring simulation before any real-world action.
- `non_actionable_research_only`: boolean or equivalent flag that forbids real-world action.
- `forbidden_action_notes`: explicit notes about forbidden actions.
- `cross_domain_analogies`: safe analogical references across domains.
- `candidate_transfer_patterns`: candidate patterns that may transfer across domains.
- `failure_mode_map`: candidate failure modes and signals.
- `measurement_gap_map`: missing measurements or coverage gaps.
- `operator_gap_map`: operator or governance gaps.
- `language_gap_map`: semantic/terminology gaps.
- `unknown_unknowns`: explicit unknown-unknown labels.
- `probes`: safe probes or probe labels.
- `mutations`: controlled mutations or perturbation labels.
- `outcomes`: observed or simulated outcomes.
- `corrections`: correction labels after invalidation or mismatch.
- `compressed_lesson`: short internal lesson.
- `next_experiments`: safe next experimental steps.
- `llm_helper_role`: helper role only; never authority.
- `public_claim_status`: allowed public-claim state.
- `boundary_status`: boundary state for runtime / public / authority limits.
- `denied_authority`: explicit denied authority map.
- `safe_metadata`: final metadata-only payload bucket.

## 4. Engine families
The protocol must support at least these families:
- math
- unknown
- raw-signal
- gap
- calibration
- chemical/material
- biological
- medical-boundary
- energy/infrastructure
- industrial
- robotics
- manufacturing
- RF/signal
- semiconductor
- cyber-resilience
- legal/governance
- market systems
- language/communication
- education/cognition
- environmental
- construction/architecture
- agriculture
- business discovery
- creative invention

### 4.1 Family intent
- `math`: abstract math, axiom mutation, invariant hunting, contradiction analysis.
- `unknown`: uncertainty separation, missing evidence, bounded hypotheses, branch labels.
- `raw-signal`: signal provenance, noise separation, uninterpreted signal cartography.
- `gap`: gap discovery, missing coverage, operator gaps, measurement gaps.
- `calibration`: forecast/error tracking, confidence correction, outcome mismatch, lesson compression.
- Cross-domain families: apply the same metadata discipline to their own domain safety boundaries.

## 5. Engine names
The protocol must recognize the following engine names.

### 5.1 Existing requested engines
- `UNKNOWN_ENGINE`
- `RAW_SIGNAL_CARTOGRAPHER`
- `UNINTELLIGIBLE_OUTPUT_ANALYZER`
- `SIGNAL_VS_NOISE_ENGINE`
- `ALGORITHM_EMERGENCE_ENGINE`
- `MUTABLE_AXIOM_MATH_ENGINE`
- `OPERATOR_FORGE_ENGINE`
- `INVARIANT_MINER`
- `CONTRADICTION_FURNACE`
- `CAUSAL_TRACE_ENGINE`
- `BLINDSPOT_ENGINE`
- `CALIBRATION_LEDGER`
- `FORECAST_ERROR_LEDGER`
- `GAP_CARTOGRAPHER`
- `ASSUMPTION_EXCAVATOR`
- `PROBE_GENERATOR`
- `MEMORY_TRUST_ENGINE`
- `ABSTRACTION_LADDER`
- `GOVERNANCE_BOUNDARY_ENGINE`
- `INTENT_RECONSTRUCTION_ENGINE`

### 5.2 Cross-domain future engines
- `CHEMICAL_SPACE_CARTOGRAPHER`
- `MATERIALS_DISCOVERY_ENGINE`
- `BIOLOGICAL_SYSTEMS_ANALYZER`
- `MEDICAL_REASONING_BOUNDARY_ENGINE`
- `ENERGY_SYSTEMS_DISCOVERY_ENGINE`
- `INDUSTRIAL_PROCESS_MINER`
- `ROBOTICS_EMBODIMENT_ENGINE`
- `MANUFACTURING_PATTERN_ENGINE`
- `RF_SIGNAL_WORLD_MODEL_ENGINE`
- `SEMICONDUCTOR_SYSTEM_ENGINE`
- `CYBER_RESILIENCE_ENGINE`
- `LEGAL_GOVERNANCE_GAP_ENGINE`
- `MARKET_SYSTEM_DYNAMICS_ENGINE`
- `LANGUAGE_PROTOCOL_ENGINE`
- `EDUCATION_COGNITION_ENGINE`
- `ENVIRONMENTAL_SYSTEM_ENGINE`
- `CONSTRUCTION_ARCHITECTURE_ENGINE`
- `AGRICULTURE_SYSTEM_ENGINE`
- `BUSINESS_MODEL_DISCOVERY_ENGINE`
- `CREATIVE_INVENTION_ENGINE`

### 5.3 Engine-family alignment rule
- `UNKNOWN_ENGINE` → `unknown`
- `RAW_SIGNAL_CARTOGRAPHER` → `raw-signal`
- `UNINTELLIGIBLE_OUTPUT_ANALYZER` → `raw-signal` or `gap` depending on the run intent
- `SIGNAL_VS_NOISE_ENGINE` → `raw-signal`
- `ALGORITHM_EMERGENCE_ENGINE` → `gap` or `creative invention`
- `MUTABLE_AXIOM_MATH_ENGINE` → `math`
- `OPERATOR_FORGE_ENGINE` → `math` or `gap`
- `INVARIANT_MINER` → `math`
- `CONTRADICTION_FURNACE` → `math` or `gap`
- `CAUSAL_TRACE_ENGINE` → `gap` or `calibration`
- `BLINDSPOT_ENGINE` → `gap`
- `CALIBRATION_LEDGER` → `calibration`
- `FORECAST_ERROR_LEDGER` → `calibration`
- `GAP_CARTOGRAPHER` → `gap`
- `ASSUMPTION_EXCAVATOR` → `gap` or `unknown`
- `PROBE_GENERATOR` → `gap` or `unknown`
- `MEMORY_TRUST_ENGINE` → `calibration` or `unknown`
- `ABSTRACTION_LADDER` → `math` or `gap`
- `GOVERNANCE_BOUNDARY_ENGINE` → `legal/governance`
- `INTENT_RECONSTRUCTION_ENGINE` → `language/communication` or `education/cognition`
- cross-domain names must map to their obvious family and fail closed on mismatch

## 6. Validation doctrine
The protocol must fail closed when:
- engine name is unknown
- engine family is unknown
- research mode is unknown
- engine/family mismatch exists
- denied authority is missing or incomplete
- public breakthrough / proof / solution / official claim appears
- LLM is treated as authority
- runtime / tool / provider / persistence / `.weslr` authority appears
- raw private text appears
- hidden prompt appears
- secrets appear
- binary blobs appear
- dangerous procedural domain instructions appear
- cross-domain family safety boundary is missing

### 6.1 Public-claim gating
- `public_claim_status` must block public claim language unless a future externally governed lane explicitly permits public export.
- Any breakthrough, proof, solution, official, certified, or public-ready claim must fail closed unless the protocol packet marks it blocked and non-authoritative.
- Radical internal hypotheses are allowed only when public claim output is blocked and the packet is explicitly internal-only.

### 6.2 Denied authority gating
The protocol must carry denied authority fields that remain false/blocked, including at least:
- runtime authority
- tool authority
- provider authority
- search authority
- persistence authority
- `.weslr` authority
- public export authority
- answer authority
- prediction authority
- official evaluation authority
- proof authority
- solution authority
- diagnosis/treatment authority for medical domains
- exploit/malware/credential-theft authority for cyber domains
- investment/trading authority for finance domains
- legal authority for legal domains

## 7. Domain safety boundaries
The protocol must include `safety_boundary` and `non_actionable_research_only` for sensitive domains.

### 7.1 Chemistry / materials
- No synthesis procedures.
- No stepwise lab instructions.
- No reagent optimization instructions that function as executable procedures.
- Only metadata-level analysis, hazard labeling, and safe research framing.

### 7.2 Biology / medicine
- No wetlab instructions.
- No pathogen handling instructions.
- No diagnosis authority.
- No treatment authority.
- No dosage authority.
- No patient-facing medical execution guidance.

### 7.3 Cybersecurity
- No exploit instructions.
- No malware instructions.
- No credential theft.
- No offensive automation.
- No operational attack chains.
- Only defensive, bounded, metadata-only analysis.

### 7.4 Finance
- No investment advice.
- No trading automation.
- No portfolio execution authority.
- No market manipulation guidance.

### 7.5 Legal
- No legal authority.
- No legal advice claim.
- No compliance authority claim.
- Only governance metadata and scoped analysis.

### 7.6 All sensitive domains
- Must carry `safety_boundary`.
- Must carry `non_actionable_research_only = true` or equivalent.
- Must not imply a live-world action path.

## 8. JSON-safe policy
The protocol must be JSON-safe and bounded.

Allowed:
- artifact refs
- short summaries
- motif/operator/hypothesis/prediction labels
- uncertainty maps
- confidence maps
- hazards
- validation routes
- review requirements
- cross-domain analogies
- candidate transfer patterns

Disallowed:
- full massive artifact storage
- raw private text
- `.weslr` content
- live tool instructions
- import-time state dumps
- binary blobs
- provider/model/search output text unless separately authorized and still bounded

## 9. Relationship to existing WESLR modules
The future protocol should reuse the existing metadata helper stack as references only:
- project state helpers
- memory state helpers
- state and continuity helpers
- owner-preview rendering metadata helpers
- private owner-preview render view-model helpers
- forecast/calibration ledgers
- future capability maturity work

Rules:
- do not duplicate project-chat or owner-preview helpers
- do not import runtime/stateful modules
- do not depend on import-time JSON or graph state
- do not turn references into authority
- bridge later through metadata-only adapters only

## 10. Transient JSON/import risk
Recent work surfaced a transient `JSONDecodeError` pattern in release-gate/test-harness context.

Design consequences:
- forbid dependence on import-time JSON loading
- forbid dependence on `entity_graph.json`
- forbid dependence on runtime graph state
- forbid release-gate side effects as input to protocol semantics
- keep protocol evaluation pure, explicit, and file-boundary safe
- require safe failure when inputs are missing or malformed

## 11. Future implementation plan
If separately authorized, the next implementation lane should create:
- helper file: `weslr/cognitive_research_protocol.py`
- test file: `weslr/tests/test_cognitive_research_protocol_v1.py`
- implementation report: `docs/WESLR_COGNITIVE_RESEARCH_PROTOCOL_HELPERS_IMPLEMENTATION_REPORT_V1.md`

### 11.1 Public helper APIs to implement later
- `allowed_cognitive_research_engine_families_v1`
- `allowed_cognitive_research_engine_names_v1`
- `allowed_cognitive_research_modes_v1`
- `allowed_cognitive_research_public_claim_statuses_v1`
- `allowed_cognitive_research_llm_helper_roles_v1`
- `classify_cognitive_research_engine_family_v1`
- `build_default_cognitive_research_denied_authority_v1`
- `build_cognitive_research_run_v1`
- `validate_cognitive_research_run_v1`
- `summarize_cognitive_research_run_v1`
- `to_cognitive_research_json_safe_v1`
- `build_initial_cognitive_research_examples_v1`

### 11.2 Future test intent
Future tests should verify:
- engine/family allowlists
- family classification
- denied authority defaults
- run builder shape
- validation fail-closed behavior
- safe summaries
- JSON-safe conversion
- example safety
- no runtime/import side effects
- protected-file drift absence

## 12. Design summary
This protocol is a shared metadata contract for future cognitive research engines.
It supports unknowns, raw signals, gaps, calibration, invariants, contradictions, probes, and cross-domain transfer while keeping authority blocked and public claims external.
It is intentionally not an engine implementation.

## 13. Review anchor
This design is grounded in:
- the Cognitive Gym shared protocol precedent
- the UNKNOWN ENGINE boundary precedent
- owner-preview and private-view-model metadata safety patterns
- state/memory/project continuity model discipline
- calibration and forecast ledger structure
- the transient JSON/import risk observed during release-gate work
