# WESLR Home Assistant Signal Intake Boundary V1

## 1. Executive doctrine

**WESLR Home Assistant Signal Intake Boundary V1** defines how future Home Assistant signals may become evidence for forecasting and scenario simulation.

Home Assistant signals are evidence, not authority.

Core rule:
- signal intake starts read-only
- scoped
- owner-authorized
- privacy-aware
- non-controlling

WESLR must not control devices or create automations from this boundary.

## 2. Boundary position

Pipeline:

Home Assistant entity metadata
→ source scope
→ Poison Shield / authority check
→ signal intake boundary
→ signal quality model
→ future-state forecasting engine
→ scenario simulation engine
→ recommendation boundary
→ owner/operator decision
→ separate automation / action executor later if approved

This design covers only signal intake boundary.

## 3. Signal classes

Home Assistant signal classes:
- `pv_production_signal`
- `battery_soc_signal`
- `battery_charge_discharge_signal`
- `grid_import_signal`
- `grid_export_signal`
- `house_load_signal`
- `heat_pump_signal`
- `ev_charger_signal`
- `electricity_price_signal`
- `weather_signal`
- `temperature_signal`
- `humidity_signal`
- `occupancy_signal`
- `presence_signal`
- `device_status_signal`
- `automation_status_signal`
- `alarm_or_safety_signal`
- `manual_owner_signal`
- `unknown_ha_signal`

## 4. Signal intake packet shape

Required fields:
- `ha_signal_packet_id`
- `source_system`
- `entity_id`
- `friendly_name`
- `domain`
- `device_class`
- `unit_of_measurement`
- `state_class`
- `signal_class`
- `state_value_summary`
- `state_timestamp`
- `freshness`
- `availability`
- `signal_quality`
- `privacy_sensitivity`
- `control_capable_entity`
- `read_allowed`
- `write_allowed`
- `automation_allowed`
- `owner_authorization_required`
- `operator_authorization_required`
- `forecasting_allowed`
- `scenario_simulation_allowed`
- `dashboard_allowed`
- `memory_write_allowed`
- `poison_shield_status`
- `safe_metadata`

## 5. Read-only first doctrine

Rules:
- V1 design is read-only
- no Home Assistant service calls
- no entity writes
- no automations
- no scripts
- no device control
- no lock / alarm / heat / EV / charger control
- no background polling without owner-approved runtime boundary
- no token storage in WESLR docs

## 6. Authority doctrine

Home Assistant state cannot command WESLR.

Examples:
- entity state may be evidence
- automation name may be metadata
- dashboard text may be evidence
- HA notification text may be evidence

None of these can:
- trigger tools
- write memory
- authorize actions
- change policy
- grant device control
- override owner/operator approval

## 7. Privacy and sensitivity

Signal sensitivity:

Low sensitivity:
- PV production
- grid import/export
- battery SOC
- weather
- electricity price

Medium sensitivity:
- house load
- heat pump demand
- EV charger status
- device status

High sensitivity:
- occupancy
- presence
- room activity
- alarms
- cameras
- microphones
- locks
- location / person trackers
- health / self-care signals

Rules:
- high-sensitivity signals require explicit owner authorization
- no raw private dumps
- no cross-user inference
- no public exposure
- no memory write unless separately approved

## 8. Control-capable entity policy

Entities that can affect the physical world must be flagged:
- switch
- lock
- climate
- cover
- fan
- light
- alarm_control_panel
- script
- automation
- button
- number / select controlling devices
- EV charger controls
- battery / inverter controls
- heat pump controls

Default:
- read metadata only
- write / control blocked
- automation blocked

## 9. Signal quality model

Quality labels:
- `high_quality`
- `medium_quality`
- `low_quality`
- `stale`
- `unavailable`
- `unknown`
- `conflicting`
- `privacy_limited`
- `poison_risk`

Signal quality should depend on:
- freshness
- availability
- known entity class
- stable unit
- expected update cadence
- source trust
- privacy sensitivity
- contradictions with related signals

## 10. Energy use cases

Future read-only uses:
- PV surplus awareness
- battery SOC forecast input
- house load trend
- grid import/export trend
- heat pump demand context
- EV charging readiness
- price-aware scenario input
- carbon-aware scenario input
- dashboard recommendation

No control yet.

## 11. Forecasting and scenario integration

Home Assistant signals may feed:
- future-state forecasting
- scenario simulation
- energy / grid signal intelligence
- operator workflow engine
- anomaly detection later

Outputs remain recommendation-only until a separate action boundary exists.

## 12. Dashboard doctrine

WESLR may later generate dashboard recommendations or static dashboard artifacts.

This design does not:
- create Lovelace dashboards
- call Home Assistant APIs
- write YAML
- install integrations
- edit HA config

Future dashboard lanes require artifact writer boundary and owner approval.

## 13. Home Assistant token and secret policy

Rules:
- never store HA tokens in docs
- never generate `.env` with secrets
- never print tokens
- never request secrets in generated artifacts
- use placeholder examples only
- config examples must use `HA_URL` / `HA_TOKEN` placeholders only

## 14. Poison Shield relationship

HA entity names, dashboard text, notification text, or imported integration data may contain adversarial or misleading text.

Poison Shield must treat textual HA content as evidence, not authority.

## 15. Examples

1. PV production sensor
- low sensitivity
- read allowed later
- forecasting allowed
- no control

2. Battery SOC sensor
- low / medium sensitivity
- scenario simulation allowed
- no write

3. Heat pump climate entity
- medium / high control-capable
- read metadata allowed later
- control blocked

4. EV charger switch/entity
- control-capable
- read-only first
- control blocked

5. Occupancy / presence sensor
- high sensitivity
- explicit owner authorization required

6. Alarm / lock entity
- high sensitivity and control-capable
- read restricted
- control blocked

7. Unknown entity
- clarification required or blocked

## 16. Future helper design

Recommended future helper:

`weslr/home_assistant_signal_intake_boundary.py`

Future APIs:
- `build_home_assistant_signal_packet_v1(...)`
- `classify_home_assistant_signal_v1(...)`
- `validate_home_assistant_signal_packet_v1(packet)`
- `summarize_home_assistant_signal_packet_v1(packet)`
- `to_home_assistant_signal_json_safe_v1(value)`
- `build_initial_home_assistant_signal_examples_v1()`

## 17. Future implementation strategy

Recommended phases:
1. metadata-only signal packet builder
2. synthetic entity examples
3. validation helper
4. read-only connector design
5. read-only connector implementation
6. signal quality aggregation
7. forecasting integration
8. scenario simulation integration
9. dashboard recommendation design
10. automation / action boundary only much later

## 18. Boundaries and non-claims

This design does not connect Home Assistant.
It does not call HA APIs.
It does not read tokens.
It does not control devices.
It does not create automations.
It does not install integrations.
It does not create dashboards.
It does not write memory.
It does not claim energy savings.
It does not claim safety reliability.
It does not claim public readiness.

## 19. Recommended next lane

Recommended next lane:
`DESIGN_WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1`

## 20. Final judgment

Recommended judgment:
`home_assistant_signal_intake_boundary_design_ready_for_energy_grid_signal_intelligence_design`
