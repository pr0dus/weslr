# WESLR Capability Maturity Registry V1

## 1. Executive doctrine

WESLR must distinguish capability existence from capability authority.

A capability being designed does not mean it is implemented.
A helper being implemented does not mean it is runtime-wired.
A dry-run capability does not mean real-world authority.
A validated internal helper does not mean public readiness.

## 2. Maturity levels

- `idea`
- `design_only`
- `reviewed_design`
- `metadata_helper`
- `dry_run`
- `sandboxed`
- `validated`
- `owner_approved_runtime`
- `pilot_limited`
- `public_safe`
- `blocked_or_deprecated`

## 3. Registry record shape

Required fields:
- `capability_id`
- `capability_name`
- `capability_family`
- `current_maturity`
- `current_authority`
- `implemented_files`
- `design_docs`
- `review_docs`
- `test_files`
- `latest_commit`
- `latest_judgment`
- `owner_approval_required`
- `runtime_wiring_allowed`
- `public_claim_allowed`
- `data_sensitivity`
- `action_risk`
- `required_boundaries`
- `missing_prerequisites`
- `blocked_next_steps`
- `recommended_next_lane`
- `rollback_or_reversal_path`
- `safe_metadata`

## 4. Capability families

Families:
- `memory_and_context`
- `artifact_and_code_generation`
- `writer_and_provenance`
- `poison_shield_and_authority`
- `forecasting_and_scenarios`
- `energy_grid_and_home_assistant`
- `wifi_rf_and_privacy_sensitive_signals`
- `llm_provider_candidate_generation`
- `tool_action_and_device_control`
- `public_product_and_claims`
- `operator_workflow`
- `friction_and_behavior_packs`

## 5. Authority states

Authority states:
- `no_authority`
- `metadata_only`
- `dry_run_only`
- `read_only`
- `sandbox_create_only`
- `validation_only`
- `proposal_only`
- `owner_approved_action`
- `operator_approved_runtime`
- `public_release_authority`
- `blocked`

## 6. Initial registry map

| Capability | Family | Current maturity | Current authority | Missing prerequisite | Risk if too early | Next lane |
|---|---|---|---|---|---|---|
| Time Anchor Resolver | memory_and_context | validated | read_only | answer formation boundary | fabricated memory use | memory answer formation |
| Temporal Memory Retrieval Plan | memory_and_context | validated | read_only | answer formation boundary | over-returning fragments | memory ranker / answer boundary |
| Memory Source Scope Registry | memory_and_context | validated | read_only | answer formation boundary | scope confusion | memory ranker |
| Safe Memory Retrieval Executor | memory_and_context | validated | read_only | answer formation boundary | fabricated context use | memory answer formation |
| Poison Shield Helpers | poison_shield_and_authority | validated | deny external authority | source-evidence graph / signal hooks | false confidence in hostile text | source evidence graph |
| Project Brief Builder | artifact_and_code_generation | validated | planning only | maturity registry | fragmented lanes | maturity registry |
| Architecture Planner | artifact_and_code_generation | reviewed_design / validated-ish | planning only | maturity registry | over-fragmentation | maturity registry |
| Stack Decision Helper | artifact_and_code_generation | reviewed_design / validated-ish | planning only | maturity registry | ambiguous readiness language | maturity registry |
| File Manifest Builder | artifact_and_code_generation | validated | artifact metadata | validation runner | scaffolds without quality path | code validation runner |
| Code Scaffold Generator | artifact_and_code_generation | validated | artifact metadata | validation runner | scaffold without execution path | code validation runner |
| Artifact Writer Boundary | writer_and_provenance | validated | deny-by-default write policy | export / patch loop | write path without quality control | code validation runner |
| Sandbox Artifact Writer Dry-Run Executor | writer_and_provenance | validated | dry_run_only | real sandbox create design | stuck in simulation | real sandbox create executor later |
| Artifact Provenance Boundary | writer_and_provenance | validated | metadata_only | source-evidence graph | provenance not reused upstream | source evidence graph |
| Future-State Forecasting Engine | forecasting_and_scenarios | design_only | recommendation only | provenance/freshness/conflict model | false precision | energy signal conflict policy |
| Scenario Simulation Engine | forecasting_and_scenarios | design_only | recommendation only | conflict / reversibility ledger | recommendation without action mapping | energy signal conflict policy |
| Home Assistant Signal Intake Boundary | energy_grid_and_home_assistant | design_only | read_only planned | read-only connector boundary | control leakage | read-only connector boundary |
| Signal Provenance/Freshness Model | energy_grid_and_home_assistant | validated/design-ready | metadata_only | conflict policy | wrong-zone reasoning | energy signal conflict policy |
| Energy Signal Conflict Resolution Policy | energy_grid_and_home_assistant | design_only | recommendation only | maturity registry linkage | unresolved conflicts driving bad recs | energy grid intelligence |
| Energy Grid Signal Intelligence | energy_grid_and_home_assistant | design_only | recommendation only | conflict policy + region normalization | wrong-zone reasoning | forecast error ledger |
| Forecast Error Ledger | friction_and_behavior_packs | design_only | metadata_only | maturity registry linkage | no learning bridge | capability maturity registry |
| WiFi/RF Sensing Program | wifi_rf_and_privacy_sensitive_signals | idea / design_only | research-only | privacy-sensitive boundary | covert tracking risk | privacy-sensitive signal boundary |
| Governed LLM Provider Boundary | llm_provider_candidate_generation | idea / design_only | no authority | poison shield + provenance + validation | model output becomes authority | governed candidate boundary |
| Code Validation Runner | artifact_and_code_generation | idea / design_only | validation only | maturity registry | patch loop without checks | code validation runner |
| Patch Feedback Loop | artifact_and_code_generation | idea / design_only | proposal only | validation runner | noisy iteration | code validation runner |
| Artifact Exporter | artifact_and_code_generation | idea / design_only | metadata_only | validation runner | unverified exports | code validation runner |
| Source Evidence Graph | writer_and_provenance | idea / design_only | metadata_only | maturity registry | provenance fragmentation | source evidence graph |
| Public Claim Lifecycle Tracker | public_product_and_claims | idea / design_only | blocked until review | public claim policy | public overclaiming | claim lifecycle |
| Owner Operator Workflow Engine | operator_workflow | idea / design_only | proposal only | maturity registry | approval drag / ambiguity | workflow engine |

## 7. Anti-confusion rules

- Do not say “implemented” for design-only docs.
- Do not say “ready” without naming ready-for-what.
- Do not say “validated” unless tests/checks passed.
- Do not say “runtime-ready” unless runtime boundary approved.
- Do not say “public-safe” unless public claim/pilot gates passed.
- Do not say “WESLR can do X” without a maturity qualifier.

## 8. Capability preservation

The registry must avoid freezing WESLR.

If a capability is blocked from runtime, it should still preserve:
- planning
- metadata helper path
- dry-run path
- sandbox path
- validation path
- owner-approved runtime path, if appropriate

## 9. Owner/operator workflow use

Registry should help answer:
- what exists now?
- what is only design?
- what can be safely implemented next?
- what is blocked?
- what needs review?
- what can be automated later?
- what still requires manual owner approval?

## 10. Public communication use

Registry should prevent public overclaiming.

Public website / product claims must only reference capabilities that are:
- actually implemented
- correctly scoped
- not runtime-overstated
- not AGI / consciousness / certification claims
- owner-approved for public wording

## 11. Future helper design

Recommended future helper:

`weslr/capability_maturity_registry.py`

Future APIs:
- `build_capability_maturity_record_v1(...)`
- `build_capability_maturity_registry_v1(...)`
- `validate_capability_maturity_record_v1(record)`
- `validate_capability_maturity_registry_v1(registry)`
- `summarize_capability_maturity_registry_v1(registry)`
- `to_capability_maturity_json_safe_v1(value)`
- `build_initial_capability_maturity_examples_v1()`

## 12. Future implementation strategy

Recommended phases:
1. metadata-only record builder
2. initial static registry examples
3. validation helper
4. summary renderer
5. next-lane recommendation helper
6. operator workflow integration
7. public-claim lifecycle integration

## 13. Boundaries and non-claims

This design does not implement the registry.
It does not inspect runtime state.
It does not write `.weslr`.
It does not authorize runtime behavior.
It does not authorize public claims.
It does not call APIs.
It does not connect Home Assistant.
It does not claim public readiness, AGI, consciousness, sentience, Turing success, certification, security certification, or production readiness.

## 14. Recommended next lane

Recommended next lane:
`IMPLEMENT_WESLR_CAPABILITY_MATURITY_REGISTRY_V1`

## 15. Final judgment

Recommended judgment:
`capability_maturity_registry_design_ready_for_metadata_helper_implementation`
