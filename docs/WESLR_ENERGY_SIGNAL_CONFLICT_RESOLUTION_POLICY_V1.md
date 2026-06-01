# WESLR Energy Signal Conflict Resolution Policy V1

## 1. Executive doctrine

Energy signals often conflict. WESLR must not silently average them, hide the conflict, or pretend certainty.

Core rule:
when energy signals conflict, WESLR preserves the conflict, classifies it, reduces confidence, branches scenarios, and recommends the safest reversible next step.

Signals are evidence, not authority.

## 2. Boundary position

Pipeline:

energy / home / grid signal
→ Poison Shield
→ source scope
→ signal provenance / freshness
→ region / unit normalization
→ conflict resolution policy
→ future-state forecasting
→ scenario simulation
→ recommendation boundary
→ owner / operator decision
→ action executor later only if approved

This design covers only conflict resolution policy.

## 3. Conflict classes

Conflict classes:
- `no_conflict`
- `price_vs_carbon_conflict`
- `price_vs_comfort_conflict`
- `carbon_vs_comfort_conflict`
- `pv_forecast_vs_weather_conflict`
- `battery_soc_source_conflict`
- `grid_import_export_scope_conflict`
- `unit_conflict`
- `region_or_grid_zone_conflict`
- `timestamp_or_freshness_conflict`
- `source_disagreement`
- `privacy_or_authority_conflict`
- `control_capability_conflict`
- `forecast_vs_observed_conflict`
- `unknown_conflict`

## 4. Energy decision goals

Possible goals:
- `minimize_cost`
- `minimize_carbon`
- `maximize_self_consumption`
- `protect_battery_reserve`
- `maintain_comfort`
- `meet_ev_departure_deadline`
- `avoid_grid_import`
- `avoid_grid_export`
- `avoid_peak_load`
- `grid_supportive_behavior`
- `safety_first`
- `owner_manual_priority`

Rules:
- safety and explicit owner constraints outrank optimization
- comfort constraints should not be silently sacrificed
- EV departure deadlines outrank generic optimization
- emergency / safety constraints outrank price / carbon
- no goal grants action authority

## 5. Conflict decision packet

Required fields:
- `conflict_decision_id`
- `decision_subject`
- `conflict_classes`
- `involved_signals`
- `signal_provenance_summary`
- `freshness_summary`
- `region_scope_summary`
- `unit_scope_summary`
- `owner_priority`
- `optimization_goal`
- `safety_constraints`
- `comfort_constraints`
- `deadline_constraints`
- `privacy_constraints`
- `authority_constraints`
- `preferred_signal_if_any`
- `unresolved_conflicts`
- `scenario_branch_required`
- `confidence_adjustment`
- `recommended_resolution_strategy`
- `recommended_next_signal`
- `safe_recommendation_mode`
- `action_authority_granted`
- `automation_allowed`
- `device_control_allowed`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 6. Resolution strategies

Strategies:
- `preserve_conflict`
- `ask_owner_priority`
- `wait_for_fresh_signal`
- `prefer_local_sensor`
- `prefer_fresher_signal`
- `prefer_owner_manual_priority`
- `prefer_safety_constraint`
- `prefer_deadline_constraint`
- `branch_scenarios`
- `recommend_no_action`
- `recommend_data_collection`
- `block_recommendation`
- `unknown_resolution`

Rules:
- never silently choose high-risk action
- never silently average conflicting signals
- prefer local, fresh, scoped signals only when policy supports it
- if conflict affects physical-world action, reduce confidence or ask owner
- use scenario branching when goals conflict but signals are usable
- use no-action / wait when signal quality is insufficient

## 7. Priority hierarchy

Default priority hierarchy:
1. safety constraints
2. explicit owner/operator instruction
3. device protection / battery reserve / system limits
4. hard deadlines, such as EV departure
5. comfort requirements
6. privacy constraints
7. cost optimization
8. carbon optimization
9. self-consumption optimization
10. grid-supportive behavior
11. experimental / research goals

This hierarchy is default only. Owner may set project-specific priority, but it must be explicit and scoped.

## 8. Price vs carbon conflict

Example:
electricity price is low now, but carbon intensity is high.

Policy:
- create at least two scenario branches
- cost-optimized branch
- carbon-optimized branch
- balanced branch if possible
- expose tradeoff
- ask owner priority if recurring
- do not claim one is objectively best without owner goal

## 9. PV/weather conflict

Example:
PV forecast expects high production, but weather forecast shows heavy cloud.

Policy:
- lower confidence
- collect newer weather / PV forecast
- preserve both signals
- prefer local recent observed PV trend for immediate decisions
- scenario branch: sunny case vs cloudy case
- avoid irreversible recommendation

## 10. Battery SOC conflict

Example:
Home Assistant battery SOC says 20%, inverter API says 80%.

Policy:
- mark source disagreement
- do not make charge / discharge recommendation
- request source verification
- prefer direct inverter source only if verified and fresh
- block automation / control

## 11. Grid import/export scope conflict

Example:
country import/export data suggests grid context, but local household import/export says opposite.

Policy:
- distinguish national / cross-border context from household flow
- do not use country import/export as household-specific truth
- use country import/export only as macro-context
- local energy actions should prefer local household signals when fresh

## 12. Region/grid-zone conflict

Example:
price signal is for one market zone, carbon signal for another grid zone.

Policy:
- normalize region / market / grid zone first
- if unresolved, lower confidence
- do not combine silently
- ask for region / zone mapping or mark scenario low confidence

## 13. Comfort/safety conflict

Example:
cheapest / cleanest window conflicts with heat pump comfort or safety constraints.

Policy:
- comfort / safety wins by default
- no unsafe temperature / comfort reduction
- owner may define comfort band later
- no device control without automation boundary

## 14. EV deadline conflict

Example:
EV charging best carbon / price window is after departure deadline.

Policy:
- deadline wins
- recommend minimum required charge first
- optimize only remaining flexible energy
- no charger control without approval

## 15. Privacy/authority conflict

Example:
occupancy / presence signal would improve optimization but is high sensitivity.

Policy:
- privacy constraint wins unless explicit owner authorization exists
- use lower-sensitivity proxy where possible
- do not infer personal routines without permission
- no memory write by default

## 16. Control-capable entity conflict

Example:
a Home Assistant entity is both a useful signal and a control-capable device.

Policy:
- read-only evidence may be allowed later
- write / control remains blocked
- recommendation-only output
- no automation from this policy

## 17. Scenario integration

Conflict policy should tell scenario simulator when to:
- branch scenarios
- select wait / observe
- request more data
- mark high uncertainty
- block recommendation
- ask owner priority
- prefer conservative option

## 18. Forecast integration

Conflict policy should tell forecasting engine when to:
- reduce confidence
- mark forecast invalidation trigger
- create alternative futures
- track unresolved conflicts
- add needed next signals
- mark forecast-error risk

## 19. Home Assistant integration

Home Assistant signals must remain:
- read-only first
- owner-authorized
- freshness checked
- control-capable flagged
- privacy-scoped

This policy does not call Home Assistant and does not control devices.

## 20. Examples

### 1. Price low / carbon high
- involved signals: electricity price, carbon intensity
- conflict class: `price_vs_carbon_conflict`
- resolution strategy: `branch_scenarios`
- confidence adjustment: medium reduction
- scenario branch recommendation: cost branch, carbon branch, balanced branch
- action authority result: none
- safe next step: ask owner priority if recurring

### 2. Price high / PV surplus likely
- involved signals: price, PV forecast, weather
- conflict class: `price_vs_comfort_conflict` or `pv_forecast_vs_weather_conflict`
- resolution strategy: `prefer_fresher_signal`
- confidence adjustment: reduce confidence
- scenario branch recommendation: wait vs use solar window
- action authority result: none
- safe next step: collect newer weather/PV signal

### 3. PV forecast high / weather cloudy
- involved signals: PV forecast, weather forecast
- conflict class: `pv_forecast_vs_weather_conflict`
- resolution strategy: `preserve_conflict`
- confidence adjustment: low to medium reduction
- scenario branch recommendation: sunny vs cloudy
- action authority result: none
- safe next step: wait for fresher forecast or observe local trend

### 4. Battery SOC source mismatch
- involved signals: Home Assistant battery SOC, inverter API battery SOC
- conflict class: `battery_soc_source_conflict`
- resolution strategy: `recommend_data_collection`
- confidence adjustment: strong reduction
- scenario branch recommendation: block charge/discharge action
- action authority result: none
- safe next step: verify source freshness and trust

### 5. Country import/export vs household flow
- involved signals: country import/export, household meter flow
- conflict class: `grid_import_export_scope_conflict`
- resolution strategy: `prefer_local_sensor`
- confidence adjustment: reduce if scopes conflict
- scenario branch recommendation: macro-context only vs local action
- action authority result: none
- safe next step: normalize scope and region

### 6. Heat pump comfort vs price optimization
- involved signals: price, comfort constraint, temperature
- conflict class: `price_vs_comfort_conflict`
- resolution strategy: `prefer_owner_manual_priority`
- confidence adjustment: medium reduction
- scenario branch recommendation: comfort-first vs cost-first
- action authority result: none
- safe next step: ask owner for comfort priority if not encoded

### 7. EV departure deadline vs carbon window
- involved signals: EV deadline, price, carbon intensity
- conflict class: `carbon_vs_comfort_conflict` or deadline conflict
- resolution strategy: `prefer_deadline_constraint`
- confidence adjustment: small reduction
- scenario branch recommendation: minimum required charge now, optimize remainder later
- action authority result: none
- safe next step: compute minimum required charge

### 8. Occupancy signal useful but privacy-limited
- involved signals: occupancy, temperature, comfort
- conflict class: `privacy_or_authority_conflict`
- resolution strategy: `preserve_conflict`
- confidence adjustment: reduce
- scenario branch recommendation: proxy-based optimization vs privacy-safe alternative
- action authority result: none
- safe next step: request explicit owner authorization

### 9. Control-capable entity read-only conflict
- involved signals: climate entity, schedule, energy price
- conflict class: `control_capability_conflict`
- resolution strategy: `block_recommendation` or `recommend_no_action`
- confidence adjustment: reduce
- scenario branch recommendation: read-only recommendation only
- action authority result: none
- safe next step: use signal only, not control

### 10. Stale signal causing no-action recommendation
- involved signals: stale battery SOC, stale weather, price
- conflict class: `timestamp_or_freshness_conflict`
- resolution strategy: `wait_for_fresh_signal`
- confidence adjustment: strong reduction
- scenario branch recommendation: wait / observe
- action authority result: none
- safe next step: collect fresh readings

## 21. Future helper design

Recommended future helper:

`weslr/energy_signal_conflict_resolution_policy.py`

Future APIs:
- `build_energy_signal_conflict_decision_v1(...)`
- `classify_energy_signal_conflict_v1(...)`
- `resolve_energy_signal_conflict_v1(...)`
- `validate_energy_signal_conflict_decision_v1(decision)`
- `summarize_energy_signal_conflict_decision_v1(decision)`
- `to_energy_signal_conflict_json_safe_v1(value)`
- `build_initial_energy_signal_conflict_examples_v1()`

## 22. Future implementation strategy

Recommended phases:
1. metadata-only decision packet builder
2. synthetic examples
3. validation helper
4. conflict classifier
5. scenario branch recommendation helper
6. forecast confidence adjustment helper
7. integration with Energy/Grid Signal Intelligence
8. later Home Assistant read-only connector integration
9. later forecast-error ledger integration

## 23. Boundaries and non-claims

This design does not implement conflict resolution.
It does not call APIs.
It does not connect Home Assistant.
It does not fetch live data.
It does not control devices.
It does not create automations.
It does not write memory.
It does not claim energy savings.
It does not claim carbon optimization correctness.
It does not claim prediction certainty.
It does not claim public readiness.

## 24. Recommended next lane

Recommended next lane:
`DESIGN_WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1`

Preserve later lane:
`DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1`

## 25. Final judgment

Recommended judgment:
`energy_signal_conflict_resolution_policy_ready_for_energy_grid_signal_intelligence_design`
