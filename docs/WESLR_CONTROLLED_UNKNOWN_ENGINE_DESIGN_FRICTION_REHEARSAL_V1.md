# WESLR Controlled UNKNOWN ENGINE Design Friction Rehearsal V1

## 1. Executive summary

The recent design stack is **coherent with minor gaps**.

It is ready for the next Energy/Grid Signal Intelligence design pass, but a few boundary models should be tightened first if the goal is a clean downstream implementation path:
- signal provenance and freshness modeling are underdefined
- forecast-error tracking is implied but not yet named as a first-class boundary
- signal conflict resolution is not yet explicit enough for mixed HA / grid / weather / manual-owner inputs
- country / region / grid-zone mapping needs a dedicated normalization lane

## 2. UNKNOWN ENGINE role boundary

Confirmed: UNKNOWN ENGINE is metadata-only and friction-only.

It is **not**:
- answer authority
- forecast authority
- runtime authority
- model judge
- implementation approval
- certification mechanism

It is only a rehearsal surface for blind spots, contradictions, and sequencing risk.

## 3. Design stack under rehearsal

Reviewed stack:
- Future Capability Portfolio
- Future-State Forecasting Engine
- Scenario Simulation Engine
- Home Assistant Signal Intake Boundary
- Poison Shield
- Artifact Provenance Boundary
- Artifact Writer Boundary
- Sandbox Writer Dry-Run
- Safe Memory Retrieval chain

Overall shape is consistent:
- provenance and Poison Shield exist before future reasoning
- forecasting sits before scenario comparison
- Home Assistant is read-only at the boundary
- artifact writing and sandboxing remain governed
- memory retrieval remains scoped and safe

## 4. Blind-spot discovery

Main missing / underdefined items:
- **signal provenance for forecasts and scenarios**: forecasts need a first-class link to the exact signals used
- **forecast-error ledger**: outcome comparison is referenced, but not yet isolated as a design boundary
- **signal conflict resolution**: stale vs fresh, manual vs automatic, and contradictory sources need explicit policy
- **timezone / region normalization**: especially for energy and grid signals
- **country / grid-zone mapping**: required before cross-border grid reasoning
- **Home Assistant entity trust model**: read-only is clear, but entity text / automation text trust levels need clearer handling
- **control-capable entity escalation**: more explicit policy for entities that can affect physical systems
- **energy comfort / safety tradeoffs**: forecasting and simulation should surface comfort and safety as first-class constraints
- **WiFi/RF false positives / false negatives**: prototype pressure is high enough that a detection-quality model will be needed early
- **consent and privacy leakage paths**: especially from occupancy / presence / routine inference
- **public-claim leakage**: forecasting language could drift into readiness or certainty claims
- **authority drift**: recommendations may start sounding like decisions unless a recommendation boundary stays explicit
- **poisoned signal propagation**: external text, dashboard text, and manual notes still need quarantine-aware flow control

## 5. Contradiction and boundary conflicts

Detected conflicts are mostly manageable, but real:
- scenario simulation can recommend an action while Home Assistant intake stays read-only; that means the recommendation boundary must be separate and explicit
- forecasting may use external signals as evidence, but Poison Shield correctly blocks them from becoming authority
- artifact provenance captures source lineage, but forecast/scenario layers still need their own source lineage references
- energy optimization can conflict with comfort / safety / operator preference; this should be modeled as a tradeoff, not collapsed away
- WiFi/RF sensing competes with privacy-sensitive boundaries; it cannot be treated like a normal telemetry lane
- public roadmap language must avoid implying implementation, readiness, or guarantees

## 6. Hidden authority escalation paths

Potential escalation paths to watch:
- external grid data being treated as operational truth instead of evidence
- Home Assistant entity text being treated as trusted intent
- dashboard text being treated as policy
- retrieved documents becoming implicit commands
- LLM/provider output later being treated as authoritative suggestions
- memory summaries gaining more weight than their provenance supports
- scenario recommendations drifting into action authority
- forecast recommendations becoming a proxy for approval
- generated artifacts implying runtime authority
- fake owner/operator approval claims entering the chain

## 7. Energy/Grid readiness analysis

Before `DESIGN_WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1`, these design elements should exist:
- signal source taxonomy
- freshness model
- unit normalization
- region / country / grid-zone mapping
- import/export interpretation limits
- electricity price vs carbon vs comfort tradeoff policy
- PV / battery / heat pump / EV dependency model
- recommendation-only boundary
- no direct control
- no energy-savings guarantee

## 8. WiFi/RF sensing pressure test

Required boundaries are clear but should be explicit in the next dedicated lane:
- consent model
- local-first pipeline
- false inference model
- privacy-sensitive signal processing
- no covert tracking
- no diagnosis / treatment
- no emergency reliability claim
- signal quality model
- synthetic-data-first design

## 9. Forecasting/scenario pressure test

The forecasting and simulation docs are structurally sound, but they still need stronger named boundaries around:
- no false precision
- no fake probabilities
- invalidation triggers
- wait / observe option
- reversibility
- outcome tracking
- low-probability high-impact paths
- no automatic action

## 10. Recommended new lanes

Recommended additions before or alongside Energy/Grid intelligence:
- `DESIGN_WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1`
- `DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1`
- `DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1`
- `DESIGN_WESLR_PRIVACY_SENSITIVE_SIGNAL_PROCESSING_BOUNDARY_V1`
- `DESIGN_WESLR_WIFI_RF_SENSING_RESEARCH_TO_PROTOTYPE_PROGRAM_V1`
- `DESIGN_WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1`

## 11. Implementation sequencing recommendation

Recommendation: **do one boundary pass before Energy/Grid intelligence**.

Best next lane is not the full energy-grid design yet; first add a small boundary/metadata layer for:
- signal provenance
- source freshness
- conflict resolution
- forecast-error tracking

After that, Energy/Grid Signal Intelligence can land much cleaner.

## 12. Boundaries and non-claims

This is report only.

It does not:
- implement anything
- call APIs
- connect Home Assistant
- use live data
- inspect hostile content
- touch `.weslr`
- touch protected files
- claim public readiness, security certification, AGI, consciousness, or product guarantees

## 13. Final judgment

`unknown_engine_design_friction_rehearsal_minor_gaps_ready_with_followups`
