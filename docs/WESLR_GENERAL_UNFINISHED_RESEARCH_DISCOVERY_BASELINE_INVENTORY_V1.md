# WESLR General Unfinished Research Discovery Baseline Inventory V1

## 1. Purpose
Baseline inventory for the governed unfinished-research discovery chain before any coding.

## 2. Repo / branch / HEAD
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- HEAD: `3a950267`

## 3. Source artifacts reviewed
- `docs/WESLR_GENERAL_UNFINISHED_RESEARCH_DISCOVERY_IMPLEMENTATION_SEQUENCE_V1.md`
- `docs/WESLR_GENERAL_UNFINISHED_RESEARCH_DISCOVERY_IMPLEMENTATION_SEQUENCE_REVIEW_V1.md`
- `docs/WESLR_ONTOLOGY_EXPANSION_PROTOCOL_V1.md`
- `docs/WESLR_ONTOLOGY_EXPANSION_PROTOCOL_REVIEW_V1.md`
- `docs/WESLR_DISCOVERY_DOCTRINE_ADDENDUM_FOR_GENERAL_UNFINISHED_RESEARCH_SIGNAL_ONTOLOGY_V1.md`

## 4. Module inventory

### Core chain modules

#### `weslr/mlcf_routing_from_live_searxng_metadata_result.py`
- Public APIs: allowed route/status/next-step getters; request validation; packet validation; route packet builder; summary; JSON-safe conversion; initial example builder.
- Packet fields: `schema_version`, `route_id`, `source_result_packet_reference`, `query`, `operator_role`, `routing_posture`, `route_status`, `kept_locator_route_entries`, `blocked_overflow_summary`, `operator_review_requirements`, `denied_authority_flags`, `validation_status`, `safe_metadata_summary`, `next_safe_step`.
- Validation / summary / JSON-safe: yes.
- Denied authority handling: yes, all false by default.
- Blocked labels: yes, e.g. unsafe authority / claim, forbidden content key/text, invalid rank/score, unsafe URL/domain, missing query / missing locator id.
- Routes: metadata-only locator routing to operator review / blocked routing.
- Source-class handling: via source-class hints and source-class posture mapping.
- Evidence-role handling: via evidence-role guesses/postures.
- Disconfirming-evidence handling: present in blocked/kept structure and next-step logic.
- Operator-review fields: yes.
- No-IO / no-provider / no-runtime assumptions: yes.

#### `weslr/cross_domain_open_problem_discovery_scout.py`
- Public APIs: allowed signal type / next-step getters; request validation; packet validation; packet builder; summary; JSON-safe conversion; example builder.
- Packet fields: `schema_version`, `scout_id`, `signal_items`, `candidate_lists`, `signal_type_counts`, `domain_families`, `cross_domain_bridges`, `pressure_test_questions`, `probe_suggestions`, `missing_evidence`, `disconfirming_evidence`, `operator_review_reasons`, `blocked_reasons`, `denied_authority_flags`, `validation_status`, `safe_metadata_summary`, `next_safe_step`.
- Validation / summary / JSON-safe: yes.
- Denied authority handling: yes.
- Blocked labels: yes, including forbidden content / claim / unsafe authority / private-hidden-protected markers.
- Routes: operator review, source-selection evidence plan, cross-domain candidate, metadata-only source locator route, cognitive research run packet, repair, blocked-by-safety, archive-low-value-signal.
- Source-class handling: yes, via source-class labels and bridge logic.
- Evidence-role handling: yes, via candidate buckets and missing/disconfirming evidence maps.
- Disconfirming-evidence handling: yes.
- Operator-review fields: yes.
- No-IO / no-provider / no-runtime assumptions: yes.

#### `weslr/cross_domain_scout_to_mlcf_integration.py`
- Public APIs: allowed route / next-step getters; request validation; packet validation; integration packet builder; summary; JSON-safe conversion; example builder.
- Packet fields: `schema_version`, `integration_id`, `source_scout_packet_ref`, `source_scout_summary`, `route_decisions`, `selected_route`, `route_reason`, `candidate_signal_refs`, `mlcf_candidate_payload_preview`, `source_selection_plan_payload_preview`, `metadata_locator_route_payload_preview`, `operator_review_reasons`, `blocked_reasons`, `denied_authority_flags`, `next_safe_step`, `validation_status`, `safe_metadata_summary`.
- Validation / summary / JSON-safe: yes.
- Denied authority handling: yes.
- Blocked labels: yes, including invalid source-scout packet, unsafe claim language, denied authority flags true, unsafe source-content fields, private/hidden/protected markers, non-json-safe request.
- Routes: source-selection evidence plan, cross-domain candidate, metadata-only source locator route, cognitive research run packet, operator review, archive low-value signal, blocked by safety.
- Source-class handling: yes, via candidate signal refs and route analysis.
- Evidence-role handling: yes, via source-selection / candidate preview routing.
- Disconfirming-evidence handling: yes, via route decisions and blocked reasons.
- Operator-review fields: yes.
- No-IO / no-provider / no-runtime assumptions: yes.

#### `weslr/cross_domain_scout_to_mlcf_candidate_preparation.py`
- Public APIs: allowed statuses/readiness/next-step getters; request validation; packet validation; packet builder; summary; JSON-safe conversion; example builder.
- Packet fields: `schema_version`, `candidate_preparation_id`, `source_integration_packet_ref`, `source_selected_route`, `preparation_status`, `candidate_readiness_label`, `domain_summaries`, `relation_type_hints`, `candidate_bridge_refs`, `missing_evidence`, `disconfirming_signals`, `source_classes_needed`, `pressure_test_questions`, `probe_suggestions`, `operator_review_reasons`, `mlcf_cross_domain_candidate_helper_payload_preview`, `source_selection_followup_preview`, `blocked_reasons`, `denied_authority_flags`, `next_safe_step`, `validation_status`, `safe_metadata_summary`.
- Validation / summary / JSON-safe: yes.
- Denied authority handling: yes.
- Blocked labels: yes, including invalid integration packet, unsafe source-content / authority markers, denied authority flags true, non-json-safe request.
- Routes: candidate-preparation ready / needs source selection / excluded wrong route / needs repair / blocked by safety / operator review.
- Source-class handling: yes.
- Evidence-role handling: yes.
- Disconfirming-evidence handling: yes, via `disconfirming_signals` and `missing_evidence`.
- Operator-review fields: yes.
- No-IO / no-provider / no-runtime assumptions: yes.

### Adjacent chain helpers inventoried
- `weslr/mlcf_source_selection_evidence_plan.py`
- `weslr/mlcf_metadata_only_source_locator_record.py`
- `weslr/mlcf_evidence_intake_packet_from_metadata_summary.py`
- `weslr/mlcf_normalized_evidence_packet_from_intake_preparation.py`
- `weslr/mlcf_searxng_source_locator_adapter_boundary.py`
- `weslr/mlcf_source_locator_organization_review_packet.py`
- `weslr/mlcf_cross_domain_science_direction_candidate.py`
- `weslr/mlcf_authorized_metadata_only_source_summary.py`
- `weslr/mlcf_ledger_registry.py`
- `weslr/evidence_ontology.py`
- `weslr/domain_ontology.py`
- `weslr/evidence_needed_detector.py`
- `weslr/evidence_sufficiency_gate.py`
- `weslr/real_findings_evidence_intake.py`
- `weslr/broad_topic_domain_intake.py`
- `weslr/capability_intake.py`
- `weslr/user_signal_intake.py`

## 5. Public API inventory
- Core chain modules expose builder / validate / summarize / JSON-safe / example-builder APIs.
- Adjacent helpers expose domain intake, evidence intake, source-locator, evidence-plan, and review-packet APIs with the same metadata-only pattern.
- Public APIs are intentionally metadata-first and fail-closed.

## 6. Test inventory

### Core chain tests
- `weslr/tests/test_mlcf_routing_from_live_searxng_metadata_result_v1.py`
- `weslr/tests/test_cross_domain_open_problem_discovery_scout_v1.py`
- `weslr/tests/test_cross_domain_scout_to_mlcf_integration_v1.py`
- `weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py`

### Neighboring tests inventoried
- `weslr/tests/test_mlcf_source_selection_evidence_plan_v1.py`
- `weslr/tests/test_mlcf_metadata_only_source_locator_record_v1.py`
- `weslr/tests/test_mlcf_evidence_intake_packet_from_metadata_summary_v1.py`
- `weslr/tests/test_mlcf_normalized_evidence_packet_from_intake_preparation_v1.py`
- `weslr/tests/test_mlcf_searxng_source_locator_adapter_boundary_v1.py`
- `weslr/tests/test_mlcf_source_locator_organization_review_packet_v1.py`
- `weslr/tests/test_mlcf_cross_domain_science_direction_candidate_v1.py`
- `weslr/tests/test_mlcf_authorized_metadata_only_source_summary_v1.py`
- `weslr/tests/test_mlcf_ledger_registry_v1.py`
- `weslr/tests/test_evidence_ontology.py`
- `weslr/tests/test_domain_ontology.py`
- `weslr/tests/test_evidence_sufficiency_gate_v1.py`
- `weslr/tests/test_real_findings_evidence_intake_v1.py`
- `weslr/tests/test_broad_topic_domain_intake_v1.py`
- `weslr/tests/test_broad_topic_domain_intake_ontology_integration_v1.py`

### Coverage already present
- exact API existence checks
- exact allowed enums / stability checks
- valid packet construction and validation
- negative safety tests for forbidden content / claim language / unsafe authority flags
- JSON-safe serialization tests
- no network / no filesystem / no provider / no model / no runtime checks in the core chain tests
- protected-file unchanged assertions

### Missing for ontology-expansion work
- ontology-insufficient trigger tests
- expansion request packet tests
- operator-token tests for ontology expansion
- extraordinary-claim quarantine tests at the new expansion layer
- language/protocol expansion claim-blocking tests at the new expansion layer
- future-work/job-transformation hype-blocking tests at the new expansion layer
- artifact-proposal packet tests
- registry/constants helper tests
- dedicated rollout/rollback packet tests

## 7. Enum / constant inventory summary

### `mlcf_routing_from_live_searxng_metadata_result.py`
- Route actions: `route_to_locator_metadata_candidate`, `hold_for_operator_review`, `block_from_routing`
- Statuses: `ready_for_operator_review`, `blocked`
- Next steps: `operator_review`, `blocked_by_safety`, `no_next_step`
- Operator roles: `owner`, `operator`, `reviewer`, `analyst`
- Source-class hints: `github_repository`, `public_lab_or_university_artifact`, `unknown_authority`, `candidate_signal`, `official_standard`, `public_research_paper`, `public_dataset`, `public_benchmark_or_test_suite`, `official_vendor_documentation`, `official_government_or_agency_data`, `blocked_private_or_hidden_source`
- Authority guesses: `community_signal`, `implementation_evidence`, `public_secondary`, `public_primary`, `official_primary`, `owner_context`, `internal_context`, `unknown_authority`, `blocked`
- Evidence-role guesses: `definition_or_standard`, `measurement_data`, `implementation_reference`, `prior_art`, `candidate_signal`, `counterexample_source`, `replication_target`, `constraint_source`, `domain_context`, `safety_boundary_context`, `not_authoritative_context`
- Denied authority flags: 23 false flags including source ingestion / raw retention / final answer / public claim / discovery claim / proof claim / benchmark claim / AGI / consciousness / sentience / runtime execution / memory mutation / `.weslr` / autonomous routing / external action / provider / model / HTTP / web / GitHub / source-summary / source-access.
- Blocked labels: unsafe authority / claim, forbidden content key/text, invalid rank/score, unsafe URL/domain, missing query, missing locator id.

### `cross_domain_open_problem_discovery_scout.py`
- Signal types: `open_problem_signal`, `unsolved_theory_signal`, `unresolved_mechanism_signal`, `unexplained_anomaly_signal`, `future_work_signal`, `limitation_signal`, `failed_model_signal`, `contradiction_signal`, `underexplored_dataset_signal`, `missing_measurement_signal`, `weak_signal`, `replication_gap_signal`, `incomplete_benchmark_signal`, `survey_gap_signal`, `calibration_gap_signal`, `cross_domain_transfer_signal`, `adjacent_science_analogy_signal`, `not_fully_understood_signal`, `unknown_mechanism_signal`, `requires_further_research_signal`, `blocked_or_unsafe_signal`, `unknown_signal`
- Next steps: `operator_review`, `prepare_source_selection_evidence_plan`, `prepare_mlcf_cross_domain_candidate`, `prepare_metadata_only_source_locator_route`, `prepare_cognitive_research_run_packet`, `needs_repair`, `blocked_by_safety`, `archive_low_value_signal`
- Search governance modes: `metadata_only_owner_review`, `metadata_only_review`, `metadata_only_archive`
- Confidence labels: `low`, `medium`, `high`, `unknown`
- Source-class labels: owner-supplied observation, public benchmark/test suite, internal project artifact, community discussion, official government/agency, official vendor docs, public dataset, public patent, blocked private/hidden source, official API docs, github repository, official standard, unknown source, software release/changelog, public lab/university artifact, public research paper.
- Denied authority flags: 22 false flags.
- Forbidden claim markers: discovery / proof / public science / official benchmark / solved / solution / truth / accepted evidence / trusted evidence / final answer.

### `cross_domain_scout_to_mlcf_integration.py`
- Routes: `scout_to_source_selection_evidence_plan`, `scout_to_mlcf_cross_domain_candidate`, `scout_to_metadata_only_source_locator_route`, `scout_to_cognitive_research_run_packet`, `scout_to_operator_review`, `scout_to_archive_low_value_signal`, `scout_blocked_by_safety`
- Next steps: `operator_review`, `prepare_source_selection_evidence_plan`, `prepare_mlcf_cross_domain_candidate`, `prepare_metadata_only_source_locator_route`, `prepare_cognitive_research_run_packet`, `archive_low_value_signal`, `blocked_by_safety`, `needs_repair`
- Denied authority flags: same 22 false flags across source access / ingestion / raw retention / final answer / public claim / discovery claim / proof claim / benchmark claim / AGI / consciousness / sentience / runtime / memory / project / `.weslr` / autonomous routing / external / provider/model / HTTP / web search / behavior-pack promotion.
- Safe metadata fields: metadata only, json safe, non public, no source access/fetching/ingestion, no raw retention, no runtime wiring, no model/provider/web calls, no `.weslr`, no memory/project mutation, no behavior-pack promotion, no public claims, no discovery/proof claims, operator review required.

### `cross_domain_scout_to_mlcf_candidate_preparation.py`
- Statuses: `candidate_preparation_ready_for_operator_review`, `candidate_preparation_needs_source_selection_plan`, `candidate_preparation_excluded_wrong_route`, `candidate_preparation_needs_repair`, `candidate_preparation_blocked_by_safety`
- Readiness labels: `metadata_candidate_ready_for_review`, `metadata_candidate_needs_evidence_plan`, `metadata_candidate_needs_disconfirming_review`, `metadata_candidate_low_value_or_weak`, `metadata_candidate_blocked`
- Next steps: `operator_review`, `prepare_source_selection_evidence_plan`, `prepare_mlcf_cross_domain_candidate`, `blocked_by_safety`, `needs_repair`, `exclude_wrong_route`
- Denied authority flags: same 22 plus accepted candidate / proposal payload / proposal submission / proposal application authorities, all false.
- Safe metadata flags: metadata only, json safe, non public, operator review required, no source access/fetching/ingestion, no raw retention, no runtime wiring, no model/provider/web calls, no `.weslr`, no memory/project mutation, no behavior-pack promotion, no public claims, no discovery/proof claims.

### Adjacent helpers
- `mlcf_authorized_metadata_only_source_summary.py`: allowed statuses/next steps/exclusion reasons; safe metadata summary with blocked/excluded/duplicate buckets.
- `mlcf_source_selection_evidence_plan.py`: source-class, authority-level, evidence-role, next-step, ledger-id constants; source-selection plan and calibration axes.
- `mlcf_metadata_only_source_locator_record.py`: source classes, authority levels, evidence roles, freshness/access/privacy statuses, next steps.
- `mlcf_evidence_intake_packet_from_metadata_summary.py`: source kind, preparation role, status, next-step, source-class-to-role mappings.
- `mlcf_normalized_evidence_packet_from_intake_preparation.py`: preparation types, confidence postures, source kind / role mappings.
- `mlcf_searxng_source_locator_adapter_boundary.py`: allowed input/result fields, source hints, blocked hints, safe non-claim / explicit-claim markers.
- `mlcf_source_locator_organization_review_packet.py`: review buckets, next steps, decision reasons, ready/nonready classes.
- `evidence_ontology.py`, `domain_ontology.py`, `evidence_sufficiency_gate.py`, `real_findings_evidence_intake.py`, `broad_topic_domain_intake.py`: adjacent governed evidence/intake/ontology surfaces already exist, but they do not yet implement the ontology-expansion protocol.

## 8. Packet-field inventory
- Core chain packet fields are already metadata-only and JSON-safe.
- Expansion-layer packet fields do not yet exist; missing fields include `expansion_request_id`, `source_locator_ids`, `triggering_signal_summary`, `why_current_ontology_failed`, `current_signal_type_attempted`, `current_route_attempted`, `sufficient_power`, `recommended_expansion_actions`, `operator_review_required`, `operator_confirmation_token_required`, `rollback_plan`, `blocked_authorities`, `forbidden_claims`, `safe_next_step`.

## 9. Safety-invariant inventory
Already covered in the chain:
- no source ingestion by default
- no accepted evidence
- no accepted candidate
- no proposal payload promotion
- no final answer authority
- no public claims
- no runtime/chat/UI/voice wiring in the reviewed chain
- no `.weslr` IO
- no provider/model calls
- JSON-safe serialization checks
- fail-closed validation

Not yet covered at the new expansion layer:
- ontology-insufficient packet creation
- operator-token enforcement for ontology expansion
- expansion rollback packet shape
- extraordinary-claim quarantine at expansion-request level
- language/protocol claim blocking at expansion-request level
- future-work hype blocking at expansion-request level

## 10. Denied-authority / blocked-label inventory
- Denied-authority handling is broad and consistently false across the chain.
- Blocked labels already exist for unsafe authority, forbidden content, unsafe claim language, invalid packet shape, unsafe URL/domain, missing query / locator, and non-json-safe requests.
- New ontology-expansion labels are missing.

## 11. Current gaps against doctrine / protocol
Confirmed gaps before Stage 0 / Stage 1:
- No shared unfinished-research discovery registry/constants helper yet.
- No ontology-insufficient signal / route / `sufficient_power` packet fields in code yet.
- No `ONTOLOGY_EXPANSION_REQUEST_CONFIRMED` token in code yet.
- No expansion-request packet builder or validator yet.
- No dedicated ontology-expansion request packet tests yet.
- No dedicated extraordinary-claim / language-protocol / future-work expansion quarantine tests yet.
- No artifact-proposal packet helper at the unfinished-research expansion layer yet.
- No stage-specific registry helper for domain families / signal types / route expansion.
- Existing source-class and evidence-role enums are duplicated across helper families and will need harmonization in later stages.

## 12. Likely files to create
Probable first implementation files:
- `weslr/unfinished_research_discovery_registry.py`
- `weslr/unfinished_research_discovery_constants.py`
- `weslr/ontology_expansion_protocol.py`
- `weslr/ontology_expansion_request_builder.py`
- `weslr/unfinished_research_discovery_sequence_helpers.py`
- `weslr/tests/test_unfinished_research_discovery_registry_v1.py`
- `weslr/tests/test_ontology_expansion_protocol_v1.py`
- `weslr/tests/test_ontology_expansion_request_builder_v1.py`
- `weslr/tests/test_unfinished_research_discovery_sequence_helpers_v1.py`

## 13. Likely files to modify
- Stage-specific new helper files and matching tests.
- `weslr/tests/release_gate_v1.py` only if an exact-file allowance ever becomes necessary.
- No protected runtime files should be modified for Stage 0 / Stage 1.

## 14. Tests to create / modify
Likely new tests:
- registry enum consistency
- ontology-insufficient detection
- expansion request packet creation
- extraordinary-claim quarantine
- language/protocol claim blocking
- future-work hype blocking
- artifact proposal packet shape
- disconfirmation-first blocking
- JSON-safe serialization
- no `.weslr` IO
- no runtime/chat/UI/voice edits
- release-gate regression

## 15. Protected-file status
- No diffs in `weslr/chat_responder.py`
- No diffs in `main.py`
- No diffs in `dialogue.py`
- No diffs in `chat_ui.py`
- No diffs in `weslr/main.py` or N/A if absent

## 16. Release-gate impact
- No release-gate change required for the inventory lane.
- Keep exact-file allowance strategy reserved for future implementation only if needed.

## 17. Implementation risk assessment
- Medium risk from enum drift across current helper families.
- Medium risk from accidentally widening candidate-preparation eligibility later.
- Low risk in Stage 0 because it is read-only.
- Lowest-risk first coding path is registry/constants design with paired tests.

## 18. Recommended first coding lane
`IMPLEMENT_WESLR_DISCOVERY_ONTOLOGY_REGISTRY_AND_CONSTANTS_V1`

## 19. Validation results
- `git diff --check` — pass
- `python3 weslr/tests/release_gate_v1.py` — pass
- `bash scripts/weslr_release_check.sh` — pass

## 20. Final judgment
`unfinished_research_discovery_baseline_inventory_ready_for_registry_constants_implementation`
