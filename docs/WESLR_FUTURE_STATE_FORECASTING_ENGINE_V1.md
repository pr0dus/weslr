# WESLR Future-State Forecasting Engine V1

## 1. Executive doctrine

**WESLR Future-State Forecasting Engine V1** is a governed forecasting and foresight engine.

It is not prophecy.
It is not certainty.
It is not magic prediction.
It is not a claim of AGI, consciousness, or superintelligence.

It produces structured possible futures from:
- signals
- constraints
- historical patterns
- current state
- assumptions
- uncertainty
- scenario comparisons

Core doctrine: forecasting is useful only when uncertainty, assumptions, missing data, reversibility, and failure modes remain visible.

## 2. Core capability

The engine is:

`current state + signal stream + constraints + causal hypotheses + history + uncertainty → forecast packet`

A forecast packet should expose:
- possible futures
- likelihood labels
- confidence level
- assumptions
- missing signals
- early warning indicators
- scenario branches
- recommended actions
- reversible next steps
- wait / observe option
- forecast invalidation triggers

## 3. Forecasting is not authority

A forecast cannot grant action authority.

Forecasts may:
- recommend
- warn
- prioritize
- request more data

Forecasts must not:
- execute tools
- write files
- trigger automations
- modify Home Assistant
- control devices
- change memory
- deploy or publish
- override owner/operator decisions

## 4. Engine position in WESLR

Pipeline:

signal intake
→ source scope / Poison Shield
→ current state model
→ historical context
→ constraint model
→ forecast engine
→ scenario simulator
→ recommendation boundary
→ owner/operator decision
→ action executor later if approved
→ outcome tracking
→ friction / forecast-error learning

This design covers only the forecast engine.

## 5. Forecast packet shape

Required fields:
- `forecast_id`
- `forecast_subject`
- `forecast_domain`
- `forecast_horizon`
- `created_timestamp`
- `current_state_summary`
- `signal_inputs`
- `signal_quality`
- `source_scope_summary`
- `poison_shield_status`
- `historical_context_summary`
- `constraints`
- `assumptions`
- `unknowns`
- `possible_futures`
- `most_likely_path`
- `alternative_paths`
- `low_probability_high_impact_paths`
- `early_warning_indicators`
- `decision_points`
- `recommended_actions`
- `wait_or_observe_option`
- `reversibility_assessment`
- `risk_labels`
- `confidence_level`
- `uncertainty_level`
- `invalidation_triggers`
- `needed_next_signals`
- `outcome_tracking_plan`
- `no_action_authority`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 6. Forecast domains

Supported / future domains:

1. `weslr_project_forecast`
- next lane readiness
- implementation risk
- blocked dependency
- public launch readiness
- runtime wiring risk

2. `artifact_build_forecast`
- likely validation failures
- missing tests
- dependency risk
- patch complexity
- export readiness

3. `energy_home_forecast`
- PV production
- battery SOC
- house load
- heat pump demand
- EV charging
- grid import/export
- price windows
- carbon intensity

4. `grid_signal_forecast`
- grid carbon / fossil percentage
- country import/export flows
- grid stress
- curtailment risk
- price / carbon action windows

5. `operator_workflow_forecast`
- owner time constraints
- likely bottlenecks
- review backlog
- best next work packet

6. `product_market_forecast`
- public launch timing
- tester onboarding
- claim risk
- audience response
- roadmap prioritization

7. `wifi_rf_sensing_forecast`
- signal quality expectations
- privacy risk
- prototype feasibility
- routine/anomaly detection confidence
- safety boundary risk

8. `research_to_prototype_forecast`
- evidence sufficiency
- prototype path risk
- validation difficulty
- unknown unknowns

## 7. Signal taxonomy

Signal classes:
- `internal_project_signal`
- `commit_history_signal`
- `validation_result_signal`
- `friction_case_signal`
- `artifact_provenance_signal`
- `poison_shield_signal`
- `memory_retrieval_signal`
- `home_assistant_signal`
- `pv_signal`
- `battery_signal`
- `grid_import_export_signal`
- `electricity_price_signal`
- `carbon_intensity_signal`
- `weather_forecast_signal`
- `calendar_routine_signal`
- `wifi_rf_signal`
- `market_signal`
- `manual_owner_signal`
- `unknown_signal`

Each signal should carry:
- source class
- freshness
- reliability
- scope
- authority
- privacy sensitivity
- update cadence
- missing-data behavior

## 8. Signal quality model

Quality labels:
- `high_quality`
- `medium_quality`
- `low_quality`
- `stale`
- `missing`
- `conflicting`
- `poison_risk`
- `unknown_quality`

Rules:
- stale signals reduce confidence
- conflicting signals create scenario branches
- missing signals must be named
- poison-risk signals cannot directly influence action without quarantine / evidence extraction
- owner-provided signal is scoped owner context, not universal truth

## 9. Time horizon model

Horizons:
- `immediate`
- `today`
- `tomorrow`
- `this_week`
- `this_month`
- `quarter`
- `long_term`
- `unknown_horizon`

Examples:
- battery / heat pump forecast: immediate, today, tomorrow
- public launch readiness: this_week, this_month
- WESLR capability growth: quarter, long_term
- WiFi/RF prototype: this_month, quarter
- market/product: month, quarter

## 10. Likelihood and uncertainty doctrine

Use qualitative labels first, not fake precision.

Likelihood labels:
- `very_likely`
- `likely`
- `plausible`
- `uncertain`
- `unlikely`
- `unknown`

Confidence labels:
- `high`
- `medium`
- `low`
- `blocked`
- `unresolved`

Rules:
- no false exact probabilities in V1
- numeric probabilities require calibrated data and separate design
- always expose assumptions
- always expose missing signals
- low confidence can still be useful if it identifies what to observe next

## 11. Causal hypothesis layer

Track causal hypotheses, not just correlations.

Examples:
- if weather forecast predicts low sun, PV production likely lower
- if battery SOC is low and evening load is high, grid import risk rises
- if validation failures cluster around path rules, artifact writer policy may be too strict
- if public claim lacks source evidence, website publishing risk rises
- if WiFi/RF signal quality is unstable, routine inference confidence falls

Fields:
- `hypothesis_id`
- `cause_signal`
- `effect_signal`
- `confidence`
- `evidence_summary`
- `counter_evidence`
- `testable_prediction`
- `invalidation_trigger`

## 12. Scenario branch generation

Every forecast should generate at least:
- baseline path
- optimistic path
- conservative path
- failure path
- wait / observe path

Each path includes:
- assumptions
- expected outcome
- benefits
- risks
- early indicators
- reversibility
- recommended action
- what would change the recommendation

## 13. Low-probability high-impact tracking

Track low-likelihood but high-impact paths:
- public launch failure
- unsafe runtime wiring
- data / privacy incident
- energy price spike
- grid outage / curtailment
- heat pump overload
- battery reserve depletion
- false WiFi/RF inference
- poisoning / source-trust attack
- artifact write mistake

These should not dominate every answer, but must be visible when relevant.

## 14. Forecast invalidation

Every forecast should include invalidation triggers.

Examples:
- weather forecast changes
- battery SOC differs from expected
- validation test fails
- user goal changes
- source becomes stale
- new constraint appears
- Poison Shield flags source
- external API unavailable
- Home Assistant signal missing
- WiFi/RF signal becomes noisy

## 15. Recommendation doctrine

Recommendations should be:
- bounded
- reversible when possible
- owner-approval aware
- risk-ranked
- uncertainty-aware
- action / no-action balanced

Output should include:
- best next action
- safest next action
- high-upside option
- wait / observe option
- data to collect next
- action not authorized if applicable

## 16. Energy / grid / Home Assistant forecasting

Future use cases:
- battery charge/discharge forecast
- heat pump preheat forecast
- EV charging window forecast
- PV surplus forecast
- grid import/export forecast
- carbon-aware action window
- price-aware action window
- grid stress awareness
- anomaly detection
- Home Assistant dashboard recommendation

Possible future external signals:
- Electricity Maps-style carbon/fossil/grid forecast
- Energy-Charts-style import/export flow
- weather provider
- electricity tariff provider
- grid operator public data
- inverter / battery / EV / heat pump local APIs through Home Assistant

Boundaries:
- design only
- no API calls now
- no Home Assistant connection now
- read-only first later
- recommendation-only first later
- no direct control without owner-approved automation boundary

## 17. WiFi / RF sensing forecasting

Future use cases:
- routine detection confidence forecast
- occupancy inference confidence forecast
- anomaly likelihood forecast
- energy optimization support
- self-care reminder support
- signal quality forecast
- privacy risk forecast

Boundaries:
- consent-based only
- local-first
- no covert tracking
- no diagnosis / treatment claims
- no emergency reliability claims
- no action without validation
- Poison Shield and privacy-sensitive signal boundary apply

## 18. Product / project forecasting

Future use cases:
- WESLR public readiness forecast
- website claim risk forecast
- legal / policy readiness forecast
- pilot tester readiness forecast
- capability bottleneck forecast
- implementation-risk forecast
- next-lane forecast

## 19. Forecast error learning

Future engine should compare forecast with outcome.

Fields:
- `forecast_id`
- `expected_outcome`
- `observed_outcome`
- `error_type`
- `missed_signal`
- `wrong_assumption`
- `stale_signal`
- `bad_causal_hypothesis`
- `overconfidence`
- `underconfidence`
- `corrective_lesson`
- `behavior_pack_candidate`

No learning claim until approved friction / behavior-pack process captures it.

## 20. Relationship to scenario simulator

Forecasting answers:
"What futures are likely from current signals?"

Scenario simulation answers:
"What happens if we choose action A, B, or C?"

They should be separate but connected.

Recommended next lane after this:
`DESIGN_WESLR_SCENARIO_SIMULATION_ENGINE_V1`

## 21. Relationship to Poison Shield

Poison Shield must scan external / retrieved signals before they influence forecasts.

External content can be evidence, not authority.

Forecast engine must not:
- let external content command WESLR
- treat source self-claims as authority
- accept poisoned memory as truth
- trigger tools from retrieved text

## 22. Relationship to provenance and memory

Forecasts should cite:
- signal provenance
- source scope
- memory source
- timestamp / freshness
- validation lineage
- artifact provenance where relevant

Memory retrieval can supply context, but the forecast engine must not fabricate memory.

## 23. Future helper design

Recommended future helper:

`weslr/future_state_forecasting_engine.py`

Future APIs:
- `build_future_state_forecast_request_v1(...)`
- `build_future_state_forecast_v1(...)`
- `validate_future_state_forecast_v1(forecast)`
- `summarize_future_state_forecast_v1(forecast)`
- `to_future_state_forecast_json_safe_v1(value)`
- `build_initial_future_state_forecast_examples_v1()`

## 24. Future examples

Include examples:
1. WESLR next-lane forecast
2. public launch readiness forecast
3. artifact validation risk forecast
4. battery / heat pump / PV forecast
5. grid import/export / carbon-aware action forecast
6. WiFi/RF sensing prototype feasibility forecast
7. market/product timing forecast
8. poisoned-signal forecast blocked by Poison Shield
9. low-confidence forecast requesting more data
10. wait / observe recommendation

## 25. Implementation strategy

Recommended phases:
1. metadata-only forecast packet builder
2. synthetic example forecasts
3. validation helper
4. signal quality model
5. scenario branch builder
6. forecast summary renderer
7. forecast error record design
8. integration with scenario simulator
9. read-only Home Assistant signal boundary later
10. external grid/weather provider boundary later

## 26. Boundaries and non-claims

This design does not implement forecasting.
It does not call APIs.
It does not connect Home Assistant.
It does not use live weather/grid/electricity data.
It does not implement WiFi/RF sensing.
It does not authorize automations.
It does not authorize device control.
It does not authorize runtime wiring.
It does not claim prediction certainty.
It does not claim AGI, consciousness, sentience, Turing success, certification, public readiness, energy savings guarantee, medical reliability, or security certification.

## 27. Final judgment

Recommended judgment:
`future_state_forecasting_engine_design_ready_for_scenario_simulation_design`
