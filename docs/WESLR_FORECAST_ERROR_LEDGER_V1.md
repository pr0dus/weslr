# WESLR Forecast Error Ledger V1

## 1. Executive doctrine

Forecasting becomes useful only when WESLR tracks forecast errors.

This ledger records differences between:
- expected outcome
- observed outcome
- assumptions
- signals used
- signal quality
- conflicts
- recommendations
- actual owner action
- resulting error or success

It is not proof of intelligence.
It is not public certification.
It is not autonomous learning authority.

## 2. Boundary position

Pipeline:

forecast packet
→ scenario simulation
→ recommendation
→ owner / operator decision
→ observed outcome
→ forecast error ledger
→ friction case / behavior-pack candidate later

This design covers only the ledger structure and policy.

## 3. Ledger record shape

Required fields:
- `forecast_error_record_id`
- `source_forecast_id`
- `source_scenario_simulation_id`
- `source_energy_intelligence_id`
- `subject`
- `domain`
- `forecast_horizon`
- `created_timestamp`
- `observation_timestamp`
- `expected_outcome`
- `observed_outcome`
- `outcome_match_status`
- `error_type`
- `error_severity`
- `confidence_before`
- `confidence_after`
- `assumptions_used`
- `assumptions_failed`
- `signals_used`
- `stale_signals`
- `missing_signals`
- `conflicting_signals`
- `wrong_region_or_grid_zone`
- `wrong_unit`
- `poisoned_or_quarantined_signal`
- `bad_causal_hypothesis`
- `wrong_owner_priority`
- `overconfidence_detected`
- `underconfidence_detected`
- `recommendation_taken`
- `owner_action_taken`
- `action_authority_used`
- `resulting_effect`
- `corrective_lesson`
- `recommended_model_update`
- `behavior_pack_candidate`
- `requires_owner_review`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 4. Outcome match statuses

Defined statuses:
- `matched`
- `partially_matched`
- `missed`
- `opposite_outcome`
- `unobserved`
- `observation_incomplete`
- `blocked_no_observation`
- `unknown`

## 5. Error types

Defined error types:
- `stale_signal`
- `missing_signal`
- `wrong_signal`
- `wrong_region_or_grid_zone`
- `wrong_unit`
- `signal_conflict_unresolved`
- `bad_causal_hypothesis`
- `wrong_assumption`
- `wrong_owner_priority`
- `overconfidence`
- `underconfidence`
- `poisoned_signal`
- `authority_gap`
- `privacy_gap`
- `scenario_branch_missing`
- `invalidation_trigger_missed`
- `observation_missing`
- `unknown_error`

## 6. Error severity

Defined severities:
- `none`
- `minor`
- `moderate`
- `major`
- `critical`
- `unknown`

Rules:
- critical means high consequence or safety / privacy impact, not disaster theatrics
- severity should consider reversibility, safety, privacy, cost, comfort, and public-claim impact

## 7. Domains

Supported domains:
- `weslr_project_forecast`
- `artifact_build_forecast`
- `energy_home_forecast`
- `grid_signal_forecast`
- `scenario_simulation`
- `operator_workflow_forecast`
- `product_market_forecast`
- `wifi_rf_sensing_forecast`
- `research_to_prototype_forecast`
- `unknown_domain`

## 8. Energy / grid examples

1. PV surplus forecast missed because weather signal became stale.
2. Battery reserve forecast wrong because SOC source was wrong.
3. Heat pump preheat recommendation wrong because comfort priority was missing.
4. EV charging scenario wrong because departure deadline changed.
5. Carbon-aware recommendation wrong because grid zone was unresolved.
6. Price-aware recommendation partially matched but owner priority favored comfort.
7. Import/export macro signal over-weighted for household decision.
8. Good forecast matched because fresh local signals and clear owner priority.

## 9. WESLR project examples

1. Next-lane forecast wrong because hidden dependency appeared.
2. Implementation-risk forecast correct because missing validation runner was identified.
3. Public readiness forecast blocked correctly due claim lifecycle missing.
4. LLM wiring forecast postponed correctly due Poison Shield/provenance dependencies.
5. Scenario simulation overconfident because rollback path was incomplete.

## 10. Learning boundary

The ledger may propose corrective lessons.

But:
- it does not update runtime behavior automatically
- it does not update memory automatically
- it does not promote behavior packs automatically
- it does not claim WESLR learned until approved friction / behavior-pack process captures it
- owner / operator review may be required

## 11. Behavior-pack relationship

Forecast errors may later feed:
- friction cases
- replay suites
- behavior-pack candidates
- update proposals
- forecast calibration proposals

But only through existing governed promotion policy.

## 12. Forecast calibration doctrine

V1 uses qualitative confidence only.

Numeric calibration requires a separate design.

Track:
- high-confidence misses
- low-confidence hits
- repeated stale-signal errors
- repeated missing-signal errors
- repeated wrong-region errors
- repeated owner-priority errors

## 13. Observation policy

Observed outcome may come from:
- owner report
- validation result
- future Home Assistant read-only signal
- future artifact validation result
- future public metric
- future manual note

Rules:
- observation source must be scoped
- observation is evidence, not authority
- external observation text must pass Poison Shield
- no raw private dump
- no memory write by default

## 14. Invalidation triggers

Ledger should record whether forecast invalidation triggers were:
- defined
- triggered
- ignored
- missed
- absent
- unknown

## 15. Future helper design

Recommended future helper:

`weslr/forecast_error_ledger.py`

Future APIs:
- `build_forecast_error_record_v1(...)`
- `validate_forecast_error_record_v1(record)`
- `summarize_forecast_error_record_v1(record)`
- `build_forecast_error_ledger_v1(records)`
- `summarize_forecast_error_ledger_v1(ledger)`
- `to_forecast_error_json_safe_v1(value)`
- `build_initial_forecast_error_examples_v1()`

## 16. Future implementation strategy

Recommended phases:
1. metadata-only record builder
2. synthetic examples
3. validation helper
4. ledger builder
5. summary renderer
6. repeated-error pattern summary
7. friction-case bridge
8. behavior-pack candidate bridge
9. Home Assistant read-only observation integration later
10. energy/grid helper integration later

## 17. Boundaries and non-claims

This design does not implement a ledger.
It does not write memory.
It does not write `.weslr`.
It does not call APIs.
It does not connect Home Assistant.
It does not control devices.
It does not execute tools.
It does not automatically learn.
It does not change runtime behavior.
It does not claim prediction certainty.
It does not claim AGI, consciousness, sentience, Turing success, certification, public readiness, energy savings guarantee, or security certification.

## 18. Recommended next lane

Recommended next lane:
`DESIGN_WESLR_CAPABILITY_MATURITY_REGISTRY_V1`

Reason:
The whole-system audit identified over-fragmentation, and a maturity registry is the cleanest bridge to consolidate the many design-only and metadata-helper lanes.

## 19. Final judgment

Recommended judgment:
`forecast_error_ledger_design_ready_for_capability_maturity_registry`
