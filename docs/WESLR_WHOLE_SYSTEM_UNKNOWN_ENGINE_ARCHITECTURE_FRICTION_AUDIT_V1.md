# WESLR Whole-System UNKNOWN ENGINE Architecture Friction Audit V1

## 1. Executive summary

WESLR’s current design is **coherent but needs architecture consolidation**.

The direction is strong: the system now has a credible governed stack for memory, provenance, Poison Shield, forecasting, scenario simulation, and read-only signal intake.

Main issue: the design is starting to grow faster than the bridge layers that connect the pieces.

Top 5 risks:
1. missing bridge layers between provenance, forecasting, scenarioing, and future action boundaries
2. authority drift from recommendations into implied runtime power
3. over-fragmentation into many adjacent design docs without a single maturity registry
4. no explicit forecast-error ledger yet
5. energy/grid and WiFi/RF domains are close to being ready, but still need a few normalization and privacy boundaries

Top 5 opportunities:
1. future-state forecasting
2. scenario simulation
3. energy/grid intelligence
4. provenance-aware signal processing
5. governed LLM candidate generation later

Recommended status: **`whole_system_coherent_but_needs_architecture_consolidation`**

## 2. UNKNOWN ENGINE role boundary

Confirmed: UNKNOWN ENGINE is only a metadata/friction/blind-spot rehearsal helper.

It is not:
- answer authority
- forecast authority
- runtime authority
- model judge
- implementation approval
- certification mechanism
- public claim source

## 3. Architecture map

### 1) Owner/operator intent layer
Existing: human goals, lane approvals, workflow direction.
Design-only: operator workflow engine, approval packets.
Missing bridges: maturity registry, handover formatting.
Authority: highest human authority.
Next lane: capability maturity / operator workflow.

### 2) Time/context/memory layer
Existing: time anchor, temporal retrieval, source scope registry, safe memory retrieval executor.
Design-only: memory answer formation, memory ranker.
Missing bridges: memory answer boundary, final answer assembly.
Authority: scoped and read-only.
Next lane: memory ranker or answer formation.

### 3) Source scope and trust layer
Existing: source scope registry, safe retrieval executor, signal provenance model, Home Assistant signal boundary, Poison Shield.
Design-only: signal freshness, conflict policy, energy signal conflict resolution.
Missing bridges: explicit source-evidence graph.
Authority: evidence-only, fail closed.
Next lane: energy signal conflict policy.

### 4) Poison Shield / authority firewall layer
Existing: poison shield helpers, adversarial quarantine, authority firewall.
Design-only: source trust registry, LLM provider quarantine, document/image/OCR poison boundaries.
Missing bridges: signal provenance hook across all evidence-bearing flows.
Authority: deny-by-default for external authority.
Next lane: energy signal conflict policy or source evidence graph.

### 5) Reasoning/planning layer
Existing: project brief, architecture, stack helper family.
Design-only: future capability portfolio.
Missing bridges: capability maturity registry.
Authority: advisory only.
Next lane: maturity registry.

### 6) Forecasting/scenario layer
Existing: future-state forecasting, scenario simulation.
Design-only: forecast-error ledger, signal conflict resolution.
Missing bridges: provenance-to-forecast linkage, invalidation ledger.
Authority: recommend only.
Next lane: energy signal conflict policy.

### 7) Artifact/code generation layer
Existing: code scaffold generator, file manifest builder, artifact writer boundary, sandbox writer dry-run executor, artifact provenance boundary.
Design-only: validation runner, patch feedback loop, exporter, real sandbox create executor.
Missing bridges: code validation runner and patch loop.
Authority: no runtime authority yet.
Next lane: code validation runner.

### 8) Writer/provenance/validation layer
Existing: artifact provenance boundary.
Design-only: artifact export bundle, generated-only edit executor, validation strategy.
Missing bridges: full validation runner and export pipeline.
Authority: metadata / traceability only.
Next lane: code validation runner.

### 9) Tool/action/device boundary layer
Existing: none as a real executor boundary yet, only design intent.
Design-only: tool-use firewall, Home Assistant read-only connector, real sandbox create executor, future tool executor.
Missing bridges: explicit action executor boundary and policy mapping.
Authority: should remain blocked until approved.
Next lane: Home Assistant read-only connector or tool-use boundary, depending roadmap.

### 10) Public/product/pilot boundary layer
Existing: public claim boundaries in docs, but no full lifecycle system.
Design-only: claim lifecycle tracker, public pilot readiness gates.
Missing bridges: public claim lifecycle, deletion/export/consent boundary.
Authority: currently blocked from public authority.
Next lane: public claim lifecycle or operator workflow.

### 11) Friction/behavior-pack improvement layer
Existing: controlled rehearsal docs, friction style audits.
Design-only: forecast-error ledger, behavior-pack refinement pipeline.
Missing bridges: explicit ledgers for repeated failures.
Authority: non-authoritative improvement only.
Next lane: forecast-error ledger.

## 4. Maturity audit

| Capability | Current maturity | Current authority | Missing prerequisite | Risk if too early | Next lane |
|---|---|---|---|---|---|
| Time anchor / temporal retrieval | validated | read-only evidence | memory answer boundary | fabricated memory use | memory ranker |
| Safe memory retrieval | validated | scoped read-only | answer formation boundary | over-returning fragments | memory answer boundary |
| Project brief / architecture / stack | validated-ish design | planning only | maturity registry | fragmented lanes | capability maturity registry |
| Code scaffold / file manifest | validated | artifact metadata | validation runner | scaffolds without quality path | code validation runner |
| Artifact writer boundary | validated | deny-by-default write policy | export / patch loop | write path without quality control | code validation runner |
| Sandbox writer dry-run | validated | dry-run only | real sandbox create design | stuck in simulation | real sandbox create executor later |
| Artifact provenance | validated | traceability only | source-evidence graph | provenance not reused upstream | source-evidence graph |
| Poison Shield | validated | deny external authority | cross-layer signal hooks | false confidence in hostile text | signal provenance / conflict policy |
| Future-state forecasting | design_only | recommendation only | provenance/freshness/conflict model | false precision | energy signal conflict policy |
| Scenario simulation | design_only | recommendation only | conflict / reversibility ledger | recommendation without action mapping | energy signal conflict policy |
| Home Assistant signal intake | design_only | read-only planned | signal provenance/freshness | control leakage | read-only connector boundary |
| Energy / grid intelligence | idea/design_only | advisory only | conflict policy + region normalization | wrong-zone reasoning | conflict policy |
| WiFi/RF sensing | idea/design_only | research-only | privacy-sensitive boundary | covert tracking risk | privacy-sensitive signal boundary |
| LLM/provider candidate generation | idea/design_only | no authority | poison shield + provenance + validation | model output becomes authority | governed candidate boundary |
| Public pilot | blocked_or_deferred | none | deletion/export/privacy/legal | public claim leakage | claim lifecycle / pilot gates |

## 5. Dependency graph audit

Correct dependencies:
- LLM provider boundary should wait for Poison Shield + provenance + artifact writer boundary
- real sandbox writes should wait for provenance + sandbox dry-run + validation strategy
- energy/grid intelligence should wait for Home Assistant intake + provenance/freshness + conflict policy
- WiFi/RF should wait for privacy-sensitive boundary + consent model + Poison Shield
- memory answer formation should wait for time anchor + safe retrieval + ranker

Missing dependencies:
- forecast-error ledger
- signal conflict resolution policy
- source-evidence graph
- capability maturity registry
- final answer assembly boundary

Unnecessary blockers:
- some implementation lanes are held back by policy concerns that could be solved with metadata-only helpers first

Wrong sequencing risk:
- moving to Energy/Grid intelligence before conflict resolution and freshness rules are explicit

## 6. Authority surface audit

- external documents: protected by Poison Shield, but still need provenance-to-forecast linkage
- uploaded files: bounded, but citation/claim lifecycle still missing
- retrieved content: evidence-only, but authority drift risk remains
- Home Assistant entity text: read-only boundary exists, but trust model is underdefined
- LLM/provider output: not wired yet, but candidate quarantine boundary needed later
- memory summaries: safe retrieval exists, but answer formation is missing
- forecast recommendations: advisory only, but could sound authoritative without a recommendation boundary
- scenario recommendations: useful, but should remain non-authoritative
- generated artifacts: provenance exists, but validation runner still missing
- owner approval packets: powerful; need strict scoped authority
- tool-use plans: should stay plans until explicit executor boundaries exist
- public website content: public-claim lifecycle missing
- `.weslr` state: correctly treated as sensitive/blocked
- runtime/chat routes: should remain outside this stack

## 7. Capability preservation audit

Mostly good:
- boundaries preserve planning
- metadata helpers preserve dry-run capability
- provenance preserves traceability
- Poison Shield preserves evidence use while denying authority

Potential over-restriction:
- dry-run can become a long-term holding pen if real sandbox / validation lanes lag
- review gates may accumulate without a maturity registry
- some design docs are ready for implementation, but the system lacks a single normalized implementation-priority surface

Overall: the current boundaries mostly preserve capability; they do not yet fully preserve the path from metadata helper → dry-run → sandboxed → validated → owner-approved runtime.

## 8. Missing core bridges

- Memory Retrieval Result Ranker: needed for better answer selection; before final answer work
- Memory Answer Formation Boundary: needed before any answer assembly surface
- Final Answer Assembly Boundary: needed before public/live response shaping
- Code Validation Runner: needed before patch loops and exporter quality
- Patch Feedback Loop: needed after validation runner, before sustained coding assistance
- Artifact Exporter: needed before reproducible bundles and public-safe artifacts
- Real Sandbox Create Executor: needed only after validation + provenance + approvals
- Energy Signal Conflict Resolution Policy: needed before Energy/Grid intelligence
- Forecast Error Ledger: needed before any serious learning from forecasts
- Signal Region/Grid-Zone Normalization Helper: needed before energy reasoning
- Source Evidence Graph: needed to unify provenance across docs, signals, forecasts, and claims
- Public Claim Lifecycle Tracker: needed before any public pilot or website claim work
- Governed LLM Provider Candidate Boundary: needed before any provider-generated artifact path
- Tool-Use Executor Boundary: needed before any action path
- Owner Operator Workflow Engine: needed to reduce approval drag
- Capability Maturity Registry: needed to stop the stack from fragmenting

## 9. Contradiction audit

No fatal contradiction found, but there are recurring tensions:
- scenario simulation can recommend actions, but the action executor boundary is still absent
- forecasts depend on signal freshness, but freshness policy is not yet connected to all signal domains
- provenance exists for artifacts, but not yet for all signals and forecast inputs
- Poison Shield blocks authority, but the HA and energy domain boundaries still need explicit trust semantics
- memory retrieval exists, but answer formation is still missing
- public website and pilot ambitions exist, but claim lifecycle is missing
- WiFi/RF research is envisioned, but privacy boundary is not yet a first-class program doc
- LLM/provider future is envisioned, but candidate quarantine is not yet a bridge layer

## 10. Forecasting / scenario / signals pressure test

Current state is usable, but the next steps require:
- freshness
- conflicts
- region / grid-zone normalization
- forecast-error learning
- no false precision
- no automatic action
- recommendation-only boundary
- source provenance
- owner approval requirements

This is why the signal provenance/freshness model was the right follow-up before energy-grid intelligence.

## 11. Energy/Grid readiness decision

Best next lane: **`DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1`**

Reason: Energy/Grid intelligence now has the signal provenance/freshness base, but it still needs the policy that resolves stale/conflicting multi-source signals before any deeper energy reasoning.

## 12. WiFi/RF sensing readiness decision

WiFi/RF should proceed later, after:
- privacy-sensitive signal processing boundary
- consent model
- synthetic-data-first policy
- false positive / false negative model
- evidence map
- non-claim policy

Recommended timing: **later, not immediate**.

## 13. LLM/provider readiness decision

LLM/provider boundary should be postponed until more bridge layers exist.

Sequence should be:
- Poison Shield
- provenance
- artifact writer boundary
- validation runner
- final answer / answer formation boundaries
- then governed candidate generation

LLM should never become direct authority.

## 14. Public pilot readiness decision

WESLR is **not public-pilot ready**.

Missing items include:
- public claim lifecycle
- deletion / export / retention / consent boundaries
- support/contact workflow
- abuse/security boundary
- stable runtime monitoring
- no public AGI / certification claims

## 15. Operator burden audit

Essential approvals:
- runtime wiring
- real writes
- device control
- public claims
- public pilot
- LLM/provider authority
- any Home Assistant automation

Can later become policy-based / dry-run automatic:
- some metadata helper reviews
- some internal validation steps
- some repetitive low-risk lane confirmations

Must stay manual:
- public release claims
- automation enabling
- safety-sensitive device control
- source-approval authority

Need to reduce burden by adding:
- capability maturity registry
- owner/operator workflow engine
- clearer “next best lane” summaries

## 16. Recommended system-level roadmap

Immediate next:
1. `DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1`
2. `DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1`
3. `DESIGN_WESLR_CAPABILITY_MATURITY_REGISTRY_V1`
4. `DESIGN_WESLR_OWNER_OPERATOR_WORKFLOW_ENGINE_V1`

Before Energy/Grid implementation:
5. `DESIGN_WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1`
6. `DESIGN_WESLR_HOME_ASSISTANT_READ_ONLY_CONNECTOR_BOUNDARY_V1`

Before WiFi/RF prototype:
7. `DESIGN_WESLR_PRIVACY_SENSITIVE_SIGNAL_PROCESSING_BOUNDARY_V1`
8. `DESIGN_WESLR_WIFI_RF_SENSING_RESEARCH_TO_PROTOTYPE_PROGRAM_V1`

Before LLM/provider:
9. `DESIGN_WESLR_GOVERNED_LLM_PROVIDER_ARTIFACT_GENERATION_BOUNDARY_V1`
10. `DESIGN_WESLR_FINAL_ANSWER_ASSEMBLY_BOUNDARY_V1`

Before real sandbox writes:
11. `DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1`
12. `DESIGN_WESLR_PATCH_FEEDBACK_LOOP_V1`
13. `DESIGN_WESLR_ARTIFACT_EXPORTER_V1`
14. `DESIGN_WESLR_REAL_SANDBOX_CREATE_EXECUTOR_V1`

Before public pilot:
15. `DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1`
16. `DESIGN_WESLR_PUBLIC_CLAIM_LIFECYCLE_TRACKER_V1`
17. `DESIGN_WESLR_PUBLIC_PILOT_GUARDRAILS_V1`

Later experimental:
18. document intelligence expansion
19. voice / ambient presence boundary
20. governed runtime action executors

## 17. What should NOT be done yet

- public pilot
- direct LLM runtime wiring
- real Home Assistant control
- real sandbox writes outside approved boundary
- OCR hostile images
- memory writes / promotions
- tool-use executor
- public security / AGI / certification claims
- WiFi/RF real sensing without consent / privacy boundary

## 18. Positive capability opportunities

Strongest opportunity areas:
- future-state forecasting
- scenario simulation
- energy/grid intelligence
- WiFi/RF sensing
- artifact/code generation
- Poison Shield / AI antivirus
- evidence graph / claim lifecycle
- operator workflow engine
- governed LLM candidate generation
- document intelligence
- internal review panel
- behavior-pack growth

## 19. Final recommended next lane

Recommended next lane: **`DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1`**

Reason: it is the smallest high-leverage bridge between the current signal-provenance work and the next major Energy/Grid intelligence layer.

## 20. Boundaries and non-claims

This is report only.

It does not implement anything.
It does not change runtime behavior.
It does not call APIs.
It does not connect Home Assistant.
It does not use model/provider/search/advisor calls.
It does not write memory.
It does not access `.weslr`.
It does not touch protected files.
It does not claim public readiness, security certification, AGI, consciousness, or Turing success.

## 21. Final judgment

`whole_system_unknown_engine_audit_minor_gaps_continue_with_prioritized_followups`
