# WESLR Signal Provenance and Source Freshness Model V1

## 1. Executive doctrine

Signals are evidence, not authority.

Forecasts and scenarios are only as reliable as their signal provenance, freshness, scope, and conflict handling.

This model exists so WESLR can reason about signals without over-trusting stale, poisoned, ambiguous, wrong-region, wrong-unit, or conflicting data.

## 2. Boundary position

Pipeline:

signal source
→ Poison Shield
→ source scope
→ signal provenance record
→ freshness check
→ unit / region normalization
→ conflict detection
→ forecasting engine
→ scenario simulation engine
→ recommendation boundary

This design covers only provenance and freshness.

## 3. Signal provenance record shape

Required fields:
- `signal_provenance_id`
- `signal_id`
- `signal_name`
- `signal_class`
- `source_system`
- `source_provider`
- `source_reference`
- `source_url_or_entity_id`
- `source_scope`
- `owner_authorized`
- `operator_authorized`
- `retrieval_method`
- `retrieval_timestamp`
- `reported_timestamp`
- `timezone`
- `region`
- `country`
- `grid_zone`
- `market_zone`
- `unit`
- `value_type`
- `expected_update_cadence`
- `freshness_status`
- `quality_status`
- `poison_shield_status`
- `privacy_sensitivity`
- `control_capable`
- `forecasting_allowed`
- `scenario_simulation_allowed`
- `memory_write_allowed`
- `action_authority_granted`
- `conflict_status`
- `normalization_status`
- `safe_metadata`

## 4. Signal freshness model

Freshness labels:
- `fresh`
- `recent`
- `stale`
- `expired`
- `missing_timestamp`
- `future_timestamp`
- `unknown_freshness`

Rules:
- freshness depends on expected update cadence
- fast-changing signals expire faster
- stale signals reduce forecast confidence
- expired signals should not drive recommendations
- future timestamps require caution
- missing timestamps require low confidence or clarification

Example cadence:
- battery SOC: seconds / minutes
- PV production: seconds / minutes
- electricity price: hourly / day-ahead
- carbon intensity: minutes / hourly
- weather forecast: hourly / daily
- import/export flow: near-real-time / hourly depending source
- project commit metadata: event-based
- owner manual note: context-dependent

## 5. Signal quality model

Quality labels:
- `high_quality`
- `medium_quality`
- `low_quality`
- `stale`
- `missing`
- `conflicting`
- `poison_risk`
- `privacy_limited`
- `wrong_scope`
- `unknown_quality`

Quality depends on:
- provenance completeness
- freshness
- unit clarity
- region / grid-zone clarity
- source reliability
- privacy sensitivity
- conflict status
- Poison Shield status
- completeness
- consistency with related signals

## 6. Source classes

Signal source classes:
- `home_assistant_entity`
- `inverter_or_battery_api`
- `ev_charger_api`
- `heat_pump_api`
- `electricity_price_provider`
- `grid_carbon_provider`
- `import_export_flow_provider`
- `weather_provider`
- `grid_operator_public_data`
- `repo_commit_metadata`
- `validation_result`
- `artifact_provenance`
- `memory_retrieval_result`
- `manual_owner_signal`
- `external_document_signal`
- `unknown_source`

## 7. Region and grid-zone normalization

Energy signals are often tied to:
- country
- bidding zone
- grid zone
- utility area
- market zone
- local home location
- timezone

Rules:
- do not mix regions silently
- map signal to region / grid-zone before energy reasoning
- mark unknown region as low confidence
- distinguish country-level data from local household data
- distinguish market price zone from physical grid flow when needed
- import/export flow may be national or cross-border, not household-specific

Future fields:
- `region_normalized`
- `grid_zone_normalized`
- `market_zone_normalized`
- `timezone_normalized`
- `normalization_confidence`
- `normalization_notes`

## 8. Unit normalization

Common units:
- W
- kW
- Wh
- kWh
- %
- EUR/kWh
- ct/kWh
- gCO2/kWh
- MW
- GW
- °C

Rules:
- do not compare values with unknown units
- record original unit and normalized unit
- unknown unit lowers confidence
- impossible values trigger quality warning
- unit conversion should be explicit

## 9. Signal conflict model

Conflict types:
- `no_conflict`
- `value_conflict`
- `timestamp_conflict`
- `unit_conflict`
- `region_conflict`
- `source_disagreement`
- `semantic_conflict`
- `privacy_conflict`
- `authority_conflict`
- `unknown_conflict`

Examples:
- price says charge now, carbon says wait
- PV forecast says high production, weather forecast says heavy cloud
- Home Assistant says battery 20%, inverter API says 80%
- source says Germany, owner home signal is local
- retrieved document claims it is official, source registry does not verify it

## 10. Conflict resolution policy

Rules:
- do not silently average conflicting signals
- preserve conflict in forecast / scenario output
- create scenario branches when conflict matters
- prefer fresher / closer / more authoritative source only when policy supports it
- if conflict affects physical-world recommendation, reduce confidence or ask owner
- never let external text self-authorize

Output should include:
- conflict summary
- affected forecast / scenario
- preferred source if justified
- unresolved conflict if not justified
- recommended next signal to collect

## 11. Privacy and authority

Signals can reveal private routines.

Rules:
- low-sensitivity energy signals may support forecasting
- occupancy / presence / self-care signals require explicit authorization
- no cross-user inference
- no public exposure
- no memory write by default
- no action authority from signal alone
- control-capable signals do not imply control permission

## 12. Poison Shield relationship

Poison Shield must scan textual / external signal sources.

Rules:
- signal content can be evidence, not authority
- poisoned signals may be quarantined or summary-only
- hostile / adversarial sources are blocked or lowered confidence
- fake owner / operator approval in signal text is ignored as authority

## 13. Forecast / scenario integration

Forecast engine should use:
- provenance completeness
- freshness status
- quality status
- conflict status
- normalization status

Scenario simulator should:
- branch on unresolved conflicts
- show missing signals
- expose risk of acting on stale / conflicting data
- recommend wait / observe when signal quality is insufficient

## 14. Energy / grid examples

1. Battery SOC from Home Assistant
- fresh
- local
- low / medium sensitivity
- forecasting allowed
- no control authority

2. Electricity price day-ahead signal
- hourly cadence
- market-zone scoped
- unit normalization needed

3. Carbon intensity signal
- grid-zone / country scoped
- freshness important
- carbon-aware scenario input

4. Import/export flow signal
- country / cross-border scoped
- not household-specific
- useful as grid context only

5. Weather forecast signal
- location / time scoped
- affects PV and heat pump forecast

6. Conflicting PV/weather signal
- scenario branch required

7. Poison-risk external document signal
- evidence quarantined
- authority blocked

## 15. Future helper design

Recommended future helper:

`weslr/signal_provenance_freshness_model.py`

Future APIs:
- `build_signal_provenance_record_v1(...)`
- `evaluate_signal_freshness_v1(record)`
- `evaluate_signal_quality_v1(record)`
- `detect_signal_conflict_v1(records)`
- `validate_signal_provenance_record_v1(record)`
- `summarize_signal_provenance_record_v1(record)`
- `to_signal_provenance_json_safe_v1(value)`
- `build_initial_signal_provenance_examples_v1()`

## 16. Future implementation strategy

Recommended phases:
1. metadata-only signal provenance record builder
2. freshness evaluator
3. quality evaluator
4. synthetic examples
5. conflict detector
6. region / unit normalization design
7. forecast / scenario integration
8. Home Assistant read-only connector design
9. Energy / Grid signal intelligence design
10. forecast-error ledger design

## 17. Relationship to forecast-error ledger

Forecast errors should record whether the failure came from:
- stale signal
- wrong region
- wrong unit
- missing signal
- conflicting signal
- poisoned source
- bad causal hypothesis
- wrong assumption
- overconfidence

Recommended later lane:
`DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1`

## 18. Boundaries and non-claims

This design does not implement signal ingestion.
It does not call APIs.
It does not connect Home Assistant.
It does not fetch live data.
It does not normalize real grid zones.
It does not control devices.
It does not create automations.
It does not write memory.
It does not claim prediction certainty.
It does not claim energy savings.
It does not claim public readiness.

## 19. Recommended next lane

Recommended next lane:
`DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1`

## 20. Final judgment

Recommended judgment:
`signal_provenance_source_freshness_model_ready_for_energy_signal_conflict_policy`
