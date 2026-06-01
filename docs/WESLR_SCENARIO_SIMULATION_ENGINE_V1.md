# WESLR Scenario Simulation Engine V1

## 1. Executive doctrine

**WESLR Scenario Simulation Engine V1** is a governed decision-simulation engine.

It is not prophecy.
It is not certainty.
It is not automatic action.
It is not runtime authority.
It is not AGI, consciousness, certification, or public readiness.

Core doctrine:
scenario simulation lets WESLR compare possible actions before acting.

It turns:

current state + possible actions + constraints + forecast context + uncertainty
→ scenario cards + tradeoffs + failure modes + recommended experiment.

## 2. Difference from forecasting

Forecasting answers:
"What futures are likely from current signals?"

Scenario simulation answers:
"What happens if we choose path A, B, or C?"

Relationship:
- forecast engine identifies likely future states
- scenario simulator compares possible interventions
- neither grants action authority
- owner/operator chooses action
- executors act only after separate approval

## 3. Scenario packet shape

Required fields:
- `scenario_simulation_id`
- `scenario_subject`
- `scenario_domain`
- `created_timestamp`
- `current_state_summary`
- `forecast_context_id`
- `decision_question`
- `candidate_actions`
- `baseline_no_action`
- `scenario_cards`
- `constraints`
- `assumptions`
- `unknowns`
- `signal_inputs`
- `signal_quality`
- `poison_shield_status`
- `source_scope_summary`
- `risk_labels`
- `recommended_option`
- `safest_option`
- `highest_upside_option`
- `wait_or_observe_option`
- `reversibility_summary`
- `approval_requirements`
- `data_to_collect_next`
- `experiment_design`
- `invalidation_triggers`
- `outcome_tracking_plan`
- `no_action_authority`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 4. Scenario card shape

Each scenario card should include:
- `scenario_id`
- `scenario_name`
- `action_description`
- `action_class`
- `expected_benefits`
- `expected_costs`
- `failure_modes`
- `risk_level`
- `reversibility`
- `time_horizon`
- `dependencies`
- `required_authority`
- `missing_information`
- `early_success_indicators`
- `early_failure_indicators`
- `estimated_effort`
- `confidence_level`
- `uncertainty_level`
- `safe_to_try`
- `recommended_as`
- `why_not_recommended`
- `fallback_plan`
- `safe_metadata`

## 5. Action classes

Action classes:
- `observe_only`
- `wait`
- `collect_more_data`
- `design_lane`
- `review_lane`
- `metadata_helper_implementation`
- `dry_run`
- `sandbox_write`
- `validation_run`
- `owner_approved_patch`
- `public_content_change`
- `runtime_wiring`
- `tool_execution`
- `home_assistant_read`
- `home_assistant_automation`
- `energy_action_recommendation`
- `device_control`
- `llm_provider_wiring`
- `document_ingestion`
- `wifi_rf_research_step`
- `market_test`
- `blocked_action`

## 6. Authority doctrine

Scenario simulation cannot grant authority.

It may recommend:
- observe
- wait
- design
- review
- dry-run
- ask owner approval
- create experiment
- collect data
- choose safer branch

It must not:
- execute tools
- write files
- control Home Assistant
- trigger automations
- change memory
- deploy/publish
- wire runtime
- ingest hostile content
- OCR hostile images
- install dependencies

## 7. Simulation domains

Supported / future domains:

1. `weslr_project_decision`
- implement next helper now vs design missing boundary
- wire runtime now vs wait
- public pilot now vs after more gates

2. `artifact_code_decision`
- real sandbox write vs dry-run
- validate now vs patch first
- export now vs improve docs

3. `llm_provider_decision`
- wire LLM candidate generator now vs after Poison Shield integration
- allow provider output for docs only vs code too

4. `energy_home_decision`
- charge battery now vs wait
- preheat heat pump now vs later
- EV charge now vs solar window
- reduce grid import vs carbon-aware operation

5. `grid_signal_decision`
- act on carbon intensity now vs price signal later
- compare import/export and fossil percentage signals

6. `wifi_rf_sensing_decision`
- simulate signal collection first
- prototype local consent-based routine detection
- postpone due privacy boundary gaps

7. `product_market_decision`
- post publicly now vs prepare claim evidence
- invite testers now vs finish legal/pilot gates

8. `operator_workflow_decision`
- continue implementation vs review
- split lane due time limits
- pause and create handover

## 8. Scenario generation doctrine

For each decision question, generate at least:
- `baseline_no_action`
- `safe_conservative_option`
- `balanced_option`
- `high_upside_option`
- `failure_or_regret_path`
- `wait_or_observe_option`

Rules:
- always include no-action / wait option
- always include safest option
- high-upside option must expose risks
- risky option must name authority requirements
- blocked actions must offer safe alternative where possible

## 9. Reversibility model

Reversibility labels:
- `fully_reversible`
- `mostly_reversible`
- `partially_reversible`
- `hard_to_reverse`
- `irreversible`
- `unknown_reversibility`

Examples:
- design doc: fully reversible
- metadata helper: mostly reversible
- real file write: partially reversible
- public post: hard to reverse
- device control action: depends on device and context
- memory write: hard to reverse unless deletion / suppression exists

## 10. Risk and failure-mode model

Risk levels:
- `low`
- `medium`
- `high`
- `blocked`
- `unknown`

Failure-mode classes:
- `wrong_assumption`
- `missing_signal`
- `stale_signal`
- `poisoned_signal`
- `authority_gap`
- `privacy_gap`
- `validation_gap`
- `runtime_side_effect`
- `public_claim_risk`
- `cost_overrun`
- `time_overrun`
- `hard_to_reverse`
- `unsafe_device_action`
- `legal_or_compliance_risk`
- `medical_or_safety_claim_risk`

## 11. Energy / home scenario simulation

Future examples:

A. Battery action:
- charge now
- wait for PV
- keep reserve
- grid-price optimized
- carbon-optimized

B. Heat pump:
- preheat before expensive / dirty grid window
- wait
- keep comfort priority
- avoid overload

C. EV:
- charge now
- charge during solar forecast
- charge during low price
- charge for departure deadline

D. Home Assistant:
- recommendation-only
- read-only dashboard
- owner-approved automation proposal
- direct automation blocked by default

Boundaries:
- no direct control in V1
- no unsafe electrical advice
- installer/operator context explicit
- owner approval required for automations

## 12. WiFi / RF sensing scenario simulation

Future examples:
- collect synthetic/local test data
- design privacy boundary first
- prototype consent-based routine awareness
- postpone due privacy/signal-quality uncertainty
- compare camera vs non-camera sensing risk
- self-care reminder support without diagnosis claims

Boundaries:
- no covert tracking
- consent-based only
- no diagnosis / treatment
- no emergency reliability claims
- local-first
- Poison Shield and privacy boundary required

## 13. WESLR project scenario simulation

Examples:
- implement helper now vs review design
- real sandbox writing now vs provenance first
- LLM wiring now vs Poison Shield first
- public pilot now vs after deletion / export / privacy gates
- publish website claim now vs evidence graph first

## 14. Scenario simulation and experiments

Scenario simulator should recommend small reversible experiments.

Fields:
- `experiment_id`
- `purpose`
- `hypothesis`
- `minimum_action`
- `success_indicator`
- `failure_indicator`
- `rollback_plan`
- `data_to_collect`
- `authority_required`
- `safe_to_run_now`

## 15. Scenario simulation and forecast error learning

After a scenario choice, future system should track:
- selected scenario
- expected outcome
- observed outcome
- wrong assumption
- missed signal
- overconfidence
- underconfidence
- improvement candidate
- behavior-pack candidate

No learning claim until approved friction / behavior-pack process captures it.

## 16. Relationship to Poison Shield

External / retrieved signals are evidence only, not authority.

Poison Shield must block:
- poisoned scenario suggestions
- fake urgency
- fake owner approval
- retrieved text telling WESLR to act
- tool-trigger manipulation
- memory poisoning

## 17. Relationship to future-state forecasting

Forecasting provides:
- likely future states
- warnings
- missing signals
- invalidation triggers

Scenario simulation provides:
- action branches
- decision tradeoffs
- experiment choices
- safe next action

## 18. Relationship to artifact/code engine

Scenario simulator can compare:
- write now vs dry-run
- validate now vs patch later
- implement full feature vs scaffold first
- use LLM candidate vs deterministic template
- export now vs improve provenance

## 19. Future helper design

Recommended future helper:

`weslr/scenario_simulation_engine.py`

Future APIs:
- `build_scenario_simulation_request_v1(...)`
- `build_scenario_simulation_v1(...)`
- `validate_scenario_simulation_v1(simulation)`
- `summarize_scenario_simulation_v1(simulation)`
- `to_scenario_simulation_json_safe_v1(value)`
- `build_initial_scenario_simulation_examples_v1()`

## 20. Future examples

Include examples:
1. WESLR next-lane scenario
2. public pilot timing scenario
3. real sandbox write vs dry-run scenario
4. LLM provider wiring scenario
5. battery / heat pump / PV scenario
6. EV charging scenario
7. grid import/export carbon-aware scenario
8. WiFi/RF sensing prototype scenario
9. public website claim scenario
10. wait / observe scenario

## 21. Implementation strategy

Recommended phases:
1. metadata-only scenario packet builder
2. synthetic examples
3. validation helper
4. scenario card builder
5. experiment recommendation builder
6. summary renderer
7. outcome tracking design
8. integration with future-state forecasting
9. integration with Home Assistant signal boundary later
10. integration with operator workflow engine later

## 22. Boundaries and non-claims

This design does not implement simulation.
It does not call APIs.
It does not connect Home Assistant.
It does not control devices.
It does not create automations.
It does not execute tools.
It does not wire runtime.
It does not authorize memory writes.
It does not authorize public publishing.
It does not claim certainty, AGI, consciousness, sentience, Turing success, certification, public readiness, medical reliability, energy savings guarantee, or security certification.

## 23. Final judgment

Recommended judgment:
`scenario_simulation_engine_design_ready_for_energy_grid_signal_intelligence_design`
