# WESLR Energy Grid Signal Intelligence V1

## 1. Executive doctrine

**WESLR Energy Grid Signal Intelligence V1** is a recommendation and reasoning layer, not a control layer.

Energy signals are evidence, not authority.

WESLR may reason about:
- PV
- battery
- grid import/export
- house load
- heat pump
- EV charging
- electricity price
- carbon intensity
- fossil-fuel percentage
- country import/export flow
- weather
- Home Assistant state

WESLR must not control devices or create automations from this layer.

## 2. Boundary position

Pipeline:

Home Assistant / grid / weather / price signal
→ Poison Shield
→ source scope
→ signal provenance / freshness
→ region / unit normalization
→ energy signal conflict resolution
→ Energy Grid Signal Intelligence
→ future-state forecasting
→ scenario simulation
→ recommendation boundary
→ owner / operator decision
→ future action executor only if approved

## 3. Intelligence goals

Goals:
- understand current home energy state
- understand grid context
- compare cost / carbon / self-consumption / comfort tradeoffs
- support battery / heat pump / EV decisions
- generate scenario inputs
- suggest dashboard needs
- identify missing signals
- detect stale / conflicting data
- recommend safe next observations / actions

## 4. Signal domains

Signal domains:
- `home_energy`
- `pv_generation`
- `battery_storage`
- `grid_import_export`
- `house_load`
- `heat_pump`
- `ev_charging`
- `electricity_price`
- `grid_carbon`
- `fossil_fuel_percentage`
- `country_import_export_flow`
- `weather_forecast`
- `home_assistant_state`
- `manual_owner_context`
- `unknown_energy_signal`

## 5. Energy intelligence packet shape

Required fields:
- `energy_intelligence_id`
- `subject`
- `created_timestamp`
- `location_scope`
- `country`
- `region`
- `grid_zone`
- `market_zone`
- `timezone`
- `home_energy_state_summary`
- `grid_context_summary`
- `signal_inputs`
- `signal_provenance_summary`
- `freshness_summary`
- `conflict_summary`
- `normalization_summary`
- `optimization_goals`
- `owner_priorities`
- `safety_constraints`
- `comfort_constraints`
- `deadline_constraints`
- `privacy_constraints`
- `possible_recommendations`
- `scenario_inputs`
- `forecast_inputs`
- `missing_signals`
- `confidence_level`
- `uncertainty_level`
- `recommended_next_step`
- `recommendation_only`
- `automation_allowed`
- `device_control_allowed`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 6. Home energy model

Home energy concepts:
- PV production
- battery SOC
- battery charge / discharge power
- house load
- grid import
- grid export
- self-consumption
- heat pump demand
- EV charging state
- reserve requirement
- owner comfort band
- owner deadline constraints

## 7. Grid context model

Grid context:
- carbon intensity
- fossil-fuel percentage
- import / export flow
- country-level context
- grid-zone context
- market-zone context
- price signal
- congestion / curtailment signal where available
- weather-driven renewable forecast

Rules:
- country import/export is macro-context, not household truth
- grid carbon signal is contextual, not direct control authority
- price signal is optimization evidence, not command authority

## 8. Recommendation modes

Modes:
- `observe_only`
- `collect_more_data`
- `dashboard_recommendation`
- `forecast_input`
- `scenario_input`
- `owner_decision_support`
- `automation_proposal_only`
- `blocked_control_request`

Default:
- recommendation-only
- no automation
- no device control

## 9. Energy decisions supported

Support reasoning for:
- charge battery now vs wait
- keep battery reserve
- discharge avoidance
- PV surplus usage
- heat pump preheat timing
- EV charge window
- grid import reduction
- carbon-aware scheduling
- price-aware scheduling
- dashboard improvement
- anomaly investigation

## 10. Tradeoff doctrine

Competing goals:
- cost
- carbon
- comfort
- self-consumption
- battery health / reserve
- EV deadline
- grid support
- safety

Rules:
- safety first
- explicit owner priority matters
- comfort / deadlines cannot be silently sacrificed
- conflicts must be exposed
- scenario branches are preferred over fake single answer

## 11. Missing signal doctrine

If important signals are missing, WESLR should say what is missing.

Examples:
- no battery SOC
- no price signal
- no carbon signal
- no weather forecast
- no EV departure deadline
- no owner priority
- no grid-zone mapping
- stale Home Assistant entity

Missing data should reduce confidence or trigger collect-more-data recommendation.

## 12. Dashboard intelligence

WESLR may recommend dashboard components:
- current PV
- battery SOC
- grid import/export
- house load
- heat pump demand
- EV charging
- price window
- carbon intensity
- import/export macro context
- weather / PV forecast
- conflict warnings
- recommended action card

This design does not create dashboards.

## 13. Energy forecast integration

Energy Grid Signal Intelligence should feed:
- Future-State Forecasting Engine
- Scenario Simulation Engine
- Forecast Error Ledger later

Forecast examples:
- evening grid import risk
- next-day PV surplus likelihood
- heat pump load risk
- EV deadline risk
- battery reserve depletion risk
- carbon / price action window

## 14. Scenario integration

Scenario examples:
- charge now vs wait for PV
- preheat now vs later
- EV charge now vs low-price window
- battery reserve vs self-consumption
- carbon-optimized vs price-optimized

## 15. Conflict integration

Use Energy Signal Conflict Resolution Policy for:
- price vs carbon
- PV forecast vs weather
- battery SOC mismatch
- country import/export vs household flow
- comfort vs optimization
- EV deadline vs ideal window
- stale signal vs fresh signal

## 16. Privacy and safety

Rules:
- no public exposure of home data
- no raw private dumps
- no occupancy / presence use without explicit owner authorization
- no device control
- no automation creation
- no safety guarantee
- no energy savings guarantee
- no advice that overrides installer/operator judgment

## 17. Owner/operator modes

Modes:
- `home_owner_mode`
- `installer_operator_mode`
- `research_mode`
- `dashboard_designer_mode`

Installer/operator mode may allow more technical analysis, but does not grant device control automatically.

## 18. Examples

### 1. PV surplus forecast support
- signal inputs: PV, weather, house load
- conflict status: none or low
- confidence: medium/high
- recommendation mode: forecast_input
- safe next step: observe / scenario input
- authority result: none

### 2. Battery reserve recommendation
- signal inputs: battery SOC, house load, grid price
- conflict status: possible price vs reserve
- confidence: medium
- recommendation mode: owner_decision_support
- safe next step: preserve reserve if uncertain
- authority result: none

### 3. EV charging deadline support
- signal inputs: battery SOC, EV state, departure time, price
- conflict status: deadline vs optimization
- confidence: medium/high if deadline known
- recommendation mode: owner_decision_support
- safe next step: minimum required charge planning
- authority result: none

### 4. Heat pump preheat scenario
- signal inputs: weather, price, comfort band
- conflict status: price vs comfort
- confidence: medium
- recommendation mode: scenario_input
- safe next step: branch scenarios
- authority result: none

### 5. Price vs carbon conflict
- signal inputs: price, carbon intensity
- conflict status: conflict present
- confidence: medium reduction
- recommendation mode: owner_decision_support
- safe next step: branch cost and carbon options
- authority result: none

### 6. Country import/export macro context
- signal inputs: country import/export flow, grid context
- conflict status: scope distinction required
- confidence: medium/low if scope unclear
- recommendation mode: forecast_input
- safe next step: treat as macro-context only
- authority result: none

### 7. Stale Home Assistant signal
- signal inputs: stale battery SOC or stale weather
- conflict status: freshness conflict
- confidence: low
- recommendation mode: collect_more_data
- safe next step: wait for fresh readings
- authority result: none

### 8. Missing owner priority
- signal inputs: price, carbon, comfort
- conflict status: optimization ambiguity
- confidence: low to medium
- recommendation mode: owner_decision_support
- safe next step: ask owner for priority
- authority result: none

### 9. Dashboard recommendation
- signal inputs: PV, battery, grid, EV, price, weather
- conflict status: none or low
- confidence: medium
- recommendation mode: dashboard_recommendation
- safe next step: produce dashboard suggestions only
- authority result: none

### 10. Blocked device-control request
- signal inputs: any control-capable entity
- conflict status: control-capability conflict
- confidence: blocked
- recommendation mode: blocked_control_request
- safe next step: read-only analysis only
- authority result: no control

## 19. Future helper design

Recommended future helper:

`weslr/energy_grid_signal_intelligence.py`

Future APIs:
- `build_energy_grid_intelligence_request_v1(...)`
- `build_energy_grid_intelligence_packet_v1(...)`
- `validate_energy_grid_intelligence_packet_v1(packet)`
- `summarize_energy_grid_intelligence_packet_v1(packet)`
- `to_energy_grid_intelligence_json_safe_v1(value)`
- `build_initial_energy_grid_intelligence_examples_v1()`

## 20. Future implementation strategy

Recommended phases:
1. metadata-only packet builder
2. synthetic energy examples
3. validation helper
4. missing-signal detector
5. dashboard recommendation helper
6. forecast / scenario integration
7. Home Assistant read-only connector boundary
8. external grid / weather / price provider boundary
9. forecast-error ledger
10. automation / action boundary much later

## 21. Relationship to forecast-error ledger

Forecast and recommendation errors should later record:
- wrong signal
- stale signal
- missing signal
- wrong region
- wrong unit
- wrong priority
- wrong assumption
- overconfidence
- underconfidence

Recommended later lane:
`DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1`

## 22. Boundaries and non-claims

This design does not implement energy intelligence.
It does not call APIs.
It does not connect Home Assistant.
It does not fetch live grid / weather / price data.
It does not control devices.
It does not create automations.
It does not create dashboards.
It does not write memory.
It does not claim energy savings.
It does not claim carbon optimization correctness.
It does not claim prediction certainty.
It does not claim public readiness.

## 23. Recommended next lane

Recommended next lane:
`DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1`

Also preserve:
`DESIGN_WESLR_HOME_ASSISTANT_READ_ONLY_CONNECTOR_BOUNDARY_V1`

## 24. Final judgment

Recommended judgment:
`energy_grid_signal_intelligence_design_ready_for_forecast_error_ledger`
