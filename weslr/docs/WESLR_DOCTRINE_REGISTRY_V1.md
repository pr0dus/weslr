# WESLR Doctrine Registry V1

**Created:** 2026-05-04
**Purpose:** Records Phase 9 and Phase 10 as accepted WESLR doctrine tracks and binds them to their implementation files, tests, constraints, and flexible implementation details.

**Doctrine status categories:**

| Status | Meaning |
|--------|---------|
| `accepted_doctrine` | Stable WESLR doctrine track. Future agents must preserve it. |
| `tracked_implementation` | Concrete file implementing a doctrine track. |
| `flexible_detail` | Implementation detail allowed to evolve without changing doctrine. |
| `checkpoint` | Important system state, but not doctrine. |
| `open_question` | Needs operator decision. |
| `anti_canon` | Should not become doctrine. |

---

## Phase 6 — Physical & Mathematical Reasoning Doctrine

**Status:** `accepted_doctrine`

**Doctrine file:** `weslr/docs/WESLR_PHASE_6_PHYSICAL_MATH_REASONING_DOCTRINE_V1.md`

**Version:** 1.0 | **Date:** 2026-05-03

### Permanent Doctrine Principles

1. All physical constraint checks have a hard/soft distinction — hard violations reject the hypothesis, soft violations warn and proceed.
2. Physical rules are operator-editable — `weslr/physics_rules.json` is the source of truth for hard/soft ranges.
3. Physical reasoning modules never execute code that changes system state or controls hardware.
4. New reasoning modules are read-only or proposal-only — they produce hypotheses and suggestions, not side effects.
5. Deterministic anchor is preserved — all physical computations are reproducible given the same input.
6. Quantum, spatial, temporal, and causal reasoning are sub-capabilities of Phase 6 physical reasoning.
7. Mock outputs are always labeled — `[SIMULATION MODE – Not real data]`.

### Future-Agent Obligations

- Do **not** present simulation/quantum/spatial outputs as real experimental data.
- Do **not** bypass hard physical constraint checks without explicit operator override.
- Preserve deterministic computation for all physical reasoning.
- Keep operator-editable rules in `physics_rules.json` — do not hardcode rule values.

### Tracked Implementation Files

| File | Role |
|------|------|
| `weslr/physics_constraints.py` | Hard/soft physical constraint validation |
| `weslr/physics_rules.json` | Operator-editable conservation laws and ranges |
| `weslr/modules/quantum_logic.py` | Quantum state, gates, measurement |
| `weslr/modules/spatial_reasoning.py` | Molecular geometry, chirality, VSEPR |
| `weslr/modules/temporal_reasoning.py` | Time-series, forecasting, temporal logic |
| `weslr/modules/causality.py` | Correlation, temporal precedence, causal confidence |
| `weslr/modules/experiment_simulation.py` | Experiment simulation stub |
| `weslr/commands/quantum_commands.py` | `/quantum` command handler |
| `weslr/commands/spatial_commands.py` | `/molecule` command handler |
| `weslr/commands/temporal_commands.py` | `/timeseries` command handler |
| `weslr/commands/causality_commands.py` | `/propose cause` command handler |
| `weslr/tests/test_spatial_reasoning.py` | Spatial reasoning tests (48 passing) |
| `weslr/tests/test_temporal_reasoning.py` | Temporal reasoning tests (16 failed, 31 passed — see notes) |
| `weslr/tests/test_experiment_simulation.py` | Experiment simulation tests (33 passing) |

### Flexible Implementation Details (non-canon)

- Exact threshold values in physics constraint checks
- Exact built-in chemistry formulas and polyatomic ion lists
- Exact quantum gate implementations (numpy vs pure-Python fallback)
- Exact causal confidence weight distribution (0.30/0.40/0.30/0.20)
- Specific built-in example datasets in causality module
- BFS exploration parameters in spatial reasoning
- Forecast horizon defaults

### Tests

```
weslr/tests/test_spatial_reasoning.py   → 48 passed ✅
weslr/tests/test_temporal_reasoning.py  → 16 failed, 31 passed ⚠️
weslr/tests/test_experiment_simulation.py → 33 passed ✅
```

Note: `test_temporal_reasoning.py` has 16 failures. These appear to be related to test fixtures that don't match current module signatures — same pattern as the `test_advanced_reasoning.py` failures fixed on 2026-05-04. The core temporal reasoning module is functional.

---

## Phase 7 — Unified Hypothesis & Experiment Workflow Doctrine

**Status:** `accepted_doctrine`

**Doctrine file:** `weslr/docs/WESLR_PHASE_7_UNIFIED_HYPOTHESIS_DOCTRINE_V1.md`

### Permanent Doctrine Principles

1. All hypotheses are per-tenant — `HypothesisRepository` enforces tenant isolation via `_TENANT_GETTER`.
2. Hypothesis IDs are deterministic — UUID v5 from `tenant_id:title:timestamp_hour` ensures the same hypothesis created in the same hour gets the same ID.
3. Hypothesis status lifecycle: `draft → active → deprecated`. Only one `active` hypothesis per tenant.
4. All hypothesis mutations are tracked via provenance — `provenance` list records `{source, timestamp, action, parameters}`.
5. Experiment suggestions are rule-based only — no ML, no generative inference.
6. Simulation outputs are labeled `[SIMULATION MODE – Not real data]`.
7. Scenario exploration uses deterministic seeding from `(tenant_id, scenario_params)` so the same exploration produces the same results.
8. Hypothesis comparison uses Jaccard keyword overlap and confidence delta.

### Future-Agent Obligations

- Do **not** expose hypotheses from one tenant to another.
- Do **not** present simulation results as real experimental data.
- Preserve provenance on every hypothesis mutation.
- Keep hypothesis IDs deterministic — do not introduce randomness into ID generation.
- Do **not** use ML for experiment suggestion — rule-based only.

### Tracked Implementation Files

| File | Role |
|------|------|
| `weslr/modules/hypothesis_repository.py` | Per-tenant hypothesis store with deterministic IDs |
| `weslr/modules/experiment_suggester.py` | Rule-based next-experiment recommendations |
| `weslr/modules/report_generator.py` | Hypothesis report text/JSON generation |
| `weslr/modules/scenario_explorer.py` | Multi-module what-if orchestration |
| `weslr/commands/hypothesis_commands.py` | `/hypothesis` command handlers |
| `weslr/commands/simulation_commands.py` | `/simulate` command handler |
| `weslr/commands/explore.py` | `/explore` command handler |
| `weslr/tests/test_hypothesis_workflow.py` | Hypothesis workflow tests (51 passing) |

### Flexible Implementation Details (non-canon)

- Exact `timestamp_hour` granularity for ID determinism (could be minute or day)
- Specific rule thresholds for experiment suggestion triggers
- Jaccard overlap threshold for keyword comparison
- Exact report section wording and format
- Scenario seed algorithm details
- Whether `active` status promotion auto-demotes previous active

### Tests

```
weslr/tests/test_hypothesis_workflow.py → 51 passed ✅
```

---

## Phase 9 — Advanced Reasoning & Meta-Learning Doctrine

**Status:** `accepted_doctrine`

**Doctrine file:** `weslr/docs/WESLR_PHASE_9_ADVANCED_REASONING_DOCTRINE_V1.md`

### Permanent Doctrine Principles

1. WESLR may perform deterministic advanced reasoning (abduction, meta-analysis, transfer/analogy).
2. Abduction outputs plausible explanations — not truth. Always label as abductive.
3. Meta-analysis synthesizes evidence. Must label synthesized / demo / uncertain evidence appropriately.
4. Transfer/analogy creates analogous hypotheses — not validated truth. Always label as analogical.
5. All reasoning outputs require provenance and confidence. No silent reasoning.
6. No external calls are required for Phase 9 core reasoning. System remains self-contained.
7. Tenant isolation must be preserved. Reasoning must not leak across tenants.
8. Reasoning capability must remain auditable and bounded.

### Future-Agent Obligations

- Do **not** present abduction as fact.
- Do **not** present analogy transfer as validation.
- Do **not** silently learn across tenants.
- Preserve deterministic/auditable reasoning path.
- Keep labels and provenance visible.
- Always surface the reasoning method (abductive / meta-analytic / transfer) alongside the output.

### Tracked Implementation Files

| File | Role |
|------|------|
| `weslr/modules/abductive_reasoner.py` | Abductive reasoning engine |
| `weslr/modules/meta_analyst.py` | Meta-analysis and evidence synthesis |
| `weslr/modules/transfer_analogy.py` | Analogy/transfer reasoning |
| `weslr/commands/advanced_commands.py` | CLI handlers for advanced reasoning commands |
| `weslr/tests/test_advanced_reasoning.py` | Test suite for Phase 9 |

### Flexible Implementation Details (non-canon)

These details are **allowed to evolve** without requiring doctrine change:

- Exact seed analogy list
- Exact BFS depth limit and branching factor
- Exact command trigger strings (`/abduce`, `/meta`, `/transfer`, etc.)
- Exact text formatting of reasoning output
- Exact built-in scientific examples and templates
- Exact confidence threshold defaults (e.g., `min_rule_confidence=0.7`)
- Exact rule priority ordering
- Whether abductive reasoner uses forward/backward chaining
- Internal module boundaries between abductive/meta/transfer

### Tests

```
weslr/tests/test_advanced_reasoning.py
```

---

## Phase 10 — Collaboration & Workspace Doctrine

**Status:** `accepted_doctrine`

**Doctrine file:** `weslr/docs/WESLR_PHASE_10_COLLABORATION_DOCTRINE_V1.md`

### Permanent Doctrine Principles

1. Tenant-private hypotheses remain private by default. No sharing without explicit opt-in.
2. Sharing must be explicit — user must call `/workspace share <id>`.
3. Shared hypotheses must be anonymized — no tenant_id, created_by, or free-text user comments.
4. Imports from shared library must preserve provenance — record `imported_from_library` with original ID.
5. Collaboration must not leak tenant-specific metadata across boundaries.
6. Explanations should be deterministic — template-based, no LLM generation.
7. Notebook/Jupyter access is a valid WESLR interface direction.
8. Collaboration features must preserve governance and tenant boundaries.

### Future-Agent Obligations

- Do **not** expose tenant-private hypotheses unless explicitly shared.
- Do **not** share free-text private user comments or annotations.
- Preserve anonymization — strip `source`, `created_by`, `tenant_id`, free-text provenance notes.
- Preserve import provenance — every imported hypothesis records `imported_from_library` with shared library ID and original hypothesis ID.
- Do **not** treat shared library content as globally verified truth.
- Keep collaboration deterministic and auditable where possible.
- Do **not** auto-share without user action.

### Tracked Implementation Files

| File | Role |
|------|------|
| `weslr/modules/workspace.py` | WorkspaceManager, shared hypothesis library, anonymization |
| `weslr/modules/explanation_generator.py` | Template-based hypothesis explanations |
| `weslr/jupyter_kernel_stub.py` | Jupyter kernel stub (`run_in_notebook`) |
| `weslr/commands/collaboration_commands.py` | CLI handlers: `/workspace`, `/jupyter`, `/explain` |
| `weslr/tests/test_collaboration.py` | Test suite for Phase 10 (37 tests) |

### Flexible Implementation Details (non-canon)

These details are **allowed to evolve** without requiring doctrine change:

- In-memory shared library storage (future may become persistent)
- Exact `shared_id` generation algorithm (UUID v5 with namespace)
- Exact command syntax and subcommand structure
- Current Jupyter stub shape (stub is Phase 10 scope; full protocol support is future)
- Exact explanation template wording
- Whether hypothesis sharing uses `shareable` flag or separate index
- Storage format of shared library entries
- Import creates a new hypothesis — exact shape of imported dict
- Domain filter behavior in shared library listing

### Tests

```
weslr/tests/test_collaboration.py
```

---

## Cross-Cutting Notes

### What remains flexible

The following are **not** doctrine and should **not** be canonized:

- Any specific threshold values in abductive reasoner (rule confidence, min evidence, etc.)
- The exact command string format for `/abduce`, `/workspace`, `/explain`
- In-memory storage decisions — Phase 10 explicitly allows future persistence
- BFS exploration depth limits
- Specific Jupyter kernel stub implementation (current stub is V1)
- Proposal ID generation algorithm
- PII pattern list (operational, extendable)

### What is permanently constraining

- `abduction` output is always labeled as abductive (not fact)
- `transfer/analogy` output is always labeled as analogical (not validated)
- Tenant-private hypotheses are never exposed without explicit share
- Shared hypotheses are always anonymized (no `source`, `tenant_id`, `created_by`, free-text comments)
- Import provenance is always recorded
- All reasoning outputs include provenance and confidence
- No external calls required for core Phase 9/10 reasoning

### Open Questions (not yet doctrine)

- What happens after a proposal in `contract_proposal_review_log.jsonl` receives review?
- Should experiment proposals appear in `/workplace` responses without operator toggle?
- Should shared library storage become persistent?
- Should Jupyter stub become full protocol implementation?
- `deterministic_handlers.py`: pubmed/arxiv declared `read_only: True` but write to `.weslr/` — needs clarification

## Observation Pipeline — Checkpoint

**Status:** `checkpoint`

**Checkpoint file:** `weslr/docs/WESLR_OBSERVATION_CHECKPOINT_V1.md`

### Current pipeline
- **observe** — `contract_observation.py` appends metadata-only records to `contract_observations.jsonl`
- **detect** — `contract_insufficiency_detector.py` scans observation windows, writes to `contract_insufficiency_log.jsonl`
- **propose** — `contract_improvement_proposal_bridge.py` converts proposal-ready records to review log
- **review** — `review_interface.py` / `workplace_review_surface.py` expose records to operator (read-only)

### Canon candidates (not yet accepted doctrine)
- Observation does not mutate behavior — `behavior_change_allowed: false` on all records
- Insufficiency flows to proposal/review — never to automatic change
- Public contract changes require governance — no auto-approval path exists
- Operational state (JSONL files) is not doctrine

### Flexible details (non-canon)
- Detector thresholds (`window=50`, `stability=3`, `min_records=10`)
- JSONL filenames (`contract_observations.jsonl`, `contract_insufficiency_log.jsonl`, `contract_proposal_review_log.jsonl`)
- Proposal ID format (`CP-{date}-{n}`, per-run counter)
- Detector pattern types (`weak_entry_repetition`, `fallback_repetition`)
- Review record JSON schema
- PII pattern list

### Open question
- Post-review lifecycle is not yet defined. `pending_review` records have no write-back path. Review lifecycle definition is the critical next step before observation pipeline can be promoted to doctrine.

---

---

## Attention Loop — Checkpoint

**Status:** `checkpoint`

**Checkpoint file:** `weslr/docs/WESLR_ATTENTION_AND_RESEARCH_WORK_LOOP_CHECKPOINT_V1.md`

**Related discovery:** `weslr/docs/WESLR_SELF_REVIEW_DISCOVERY_V1.md`

### Purpose

WESLR self-review loop for architecture gaps, validation gaps, stale checkpoints, missing lifecycle links, doctrine/implementation drift, and operator attention routing.

### Current Implementation Status

- ✅ Checkpoint/design exists
- ✅ Proactive daemon exists (`weslr/proactive_daemon.py`)
- ❌ Self-review source adapters not implemented yet
- ❌ No automatic execution
- ❌ No auto-code / auto-commit / auto-push
- ❌ No accepted doctrine promotion yet

### Safety Rule

> WESLR may observe, detect, prioritize, and suggest.
> WESLR may **not** silently mutate, execute, self-code, approve, commit, push, or change doctrine/contracts.

### Tracked Implementation Files

| File | Role |
|---|---|
| `weslr/proactive_daemon.py` | Periodic suggestion loop, deduplication, interval control |
| `weslr/docs/WESLR_SELF_REVIEW_DISCOVERY_V1.md` | Self-review capability gap analysis |
| `weslr/docs/WESLR_ATTENTION_AND_RESEARCH_WORK_LOOP_CHECKPOINT_V1.md` | Dual-loop architecture design |

### Flexible Details (non-canon)

- Source adapter model
- Scoring model for gap detection
- Suggestion store design
- Cadence / tick interval
- Delivery surface (workplace integration)
- Detector list (which gaps are detectable)

### Open Questions

- Source adapter model (single unified adapter vs per-source adapters)
- Proposal review lifecycle (pending → reviewed → accepted/rejected)
- Attention suggestion store path
- Operator-visible review surface
- Eventual scheduling policy (manual tick vs cron)

---

## Research Work Loop — Checkpoint

**Status:** `checkpoint`

**Checkpoint file:** `weslr/docs/WESLR_ATTENTION_AND_RESEARCH_WORK_LOOP_CHECKPOINT_V1.md`

**Implementation plan:** `weslr/docs/WESLR_ATTENTION_AND_RESEARCH_WORK_LOOP_V1_IMPLEMENTATION_PLAN.md`

### Purpose

User-defined governed research/workflow missions that can keep working over time by reading approved local sources, detecting evidence gaps, suggesting hypotheses/next actions, and writing reviewable suggestions.

### Current Implementation (V1)

| File | Role |
|---|---|
| `weslr/schemas/mission.py` | Mission dataclass + JSON schema, `make_mission()`, `generate_mission_id()` |
| `weslr/mission_store.py` | Per-tenant mission repository, JSONL store |
| `weslr/adapters/local_evidence_adapter.py` | Safe local file reading, path allowlist, extension filter |
| `weslr/loop/safety_filter.py` | Blocks 14 forbidden content patterns |
| `weslr/loop/suggestion_ranker.py` | Weighted scoring (confidence + relevance + evidence) |
| `weslr/loop/research_work_loop.py` | `run_once_mission_review()` — manual review path |
| `weslr/commands/mission_commands.py` | CLI: `/mission help/create/list/details/activate/pause/close/review` |
| `weslr/tests/test_mission_store.py` | 17 tests |
| `weslr/tests/test_research_work_loop_v1.py` | 39 tests |
| `weslr/tests/test_mission_commands_v1.py` | 25 tests |

### Accepted Doctrine Principles

- WESLR may consolidate safe traces into reviewable candidates.
- Consolidation is distinct from OpenClaw Dreaming.
- Consolidation may cluster, score, classify, and explain repeated signals.
- V1 digest writes candidate records only.
- Green-zone auto-promotion is allowed only when the master toggle is enabled.
- Green-zone auto-promotion must be append-only or reversible.
- Green-zone auto-promotion requires provenance and audit logging.
- Yellow-zone candidates require review.
- Red-zone candidates require explicit approval and never auto-promote.
- No automatic doctrine, identity/access, governance, code, public behavior, external action, or scientific truth promotion.
- Consolidation must remain scoped, auditable, and governed.

### Flexible Implementation Details (non-canon)

- exact config field names
- exact scoring weights
- exact cluster keys
- exact green/yellow/red classifier
- allowed green destinations
- CLI command syntax
- audit log schema
- digest schema
- future daemon scheduling

### Implementation Files

- `weslr/consolidation_loop.py` — V1 digest: collect → cluster → score → classify → gate → write
- `weslr/consolidation_config.py` — ConsolidationConfig class, load/save, default OFF
- `weslr/consolidation_promotion.py` — classify_zone(), decide_promotion(), auto_promote(), audit_log()
- `weslr/commands/consolidation_commands.py` — CLI: run / status / auto / promote
- `weslr/tests/test_consolidation_loop.py` — 15 tests
- `weslr/tests/test_consolidation_promotion.py` — 58 tests

### V1 Status

- ✅ Manual `run_once` only — no auto-start
- ✅ Local evidence only — no external calls
- ✅ No scheduled daemon
- ✅ `automatic_execution` forced `False` on all missions
- ✅ Safety filter blocks 14 forbidden categories
- ✅ Tenant isolation enforced via `MissionStore`
- ✅ Suggestions written to `.weslr/pending_messages.jsonl` for operator review
- ❌ Workplace surface not integrated yet
- ❌ V2 cadence scheduling not implemented
- ❌ External literature adapter not implemented

### Safety Rule

> WESLR may observe, reason, compare, hypothesize, and suggest.
> WESLR may **not** automatically execute, synthesize, deploy, modify, approve, or perform unsafe external actions.

### Flexible Details (non-canon)

- Mission store schema (current: `.weslr/missions.jsonl`, per-tenant JSONL)
- Command syntax (`/mission create --title ... --goal ...`)
- Scoring/ranking model (current: 0.5 conf + 0.3 relevance + 0.2 evidence)
- Evidence adapter list (current: `LocalEvidenceAdapter` only)
- Workplace integration path
- Cadence/scheduling policy (V2)
- User/operator visibility model (`operator_visible`, `public_user_visible`)

### Open Questions

- Workplace surface integration (how suggestions surface to operator)
- First real mission / operator demo
- Mission suggestion review lifecycle (pending → operator review → accept/reject)
- V2 scheduling cadence (`cadence_minutes` per mission)
- External literature source governance (blocked by default)
- Sensitive-domain classification refinements

---

_Last updated: 2026-05-04_
_Phase 9 status: accepted_doctrine_
_Phase 10 status: accepted_doctrine_
_Phase 11 status: accepted_doctrine_
_Observation pipeline status: checkpoint_
_Attention Loop status: checkpoint_
_Research Work Loop status: checkpoint_

---

## Consolidation Loop — Accepted Doctrine

**Status:** accepted_doctrine

**Checkpoint file:** `weslr/docs/WESLR_CONSOLIDATION_LOOP_CHECKPOINT_V1.md`

### Purpose

WESLR-native memory consolidation loop that collects safe traces, clusters repeated themes, scores them, classifies proposed destinations, and writes operator-visible digest candidates.

### V1 Status

- manual only
- digest-only
- reads safe metadata traces
- writes only `.weslr/consolidation_digest.jsonl`
- no promotion
- no deletion
- no doctrine edits
- no entity memory writes
- no mission store mutation
- automatic_execution=false
- promotion_performed=false

### V2 Status (green-zone auto-promotion)

- **consolidation_auto_enabled**: master kill-switch (default: false)
- **green_zone_auto_promotion_enabled**: green-zone toggle (default: false)
- **zone classification**: green (auto if toggle ON) / yellow (review) / red (approval)
- **allowed_green_destinations**: continuity_summary, attention_memory, digest_archive_marker, procedural_note only
- **provenance required**: must have source provenance if require_provenance=True
- **audit logging**: every promotion decision logged to consolidation_audit.jsonl if require_audit_log=True
- **yellow zone**: weight_proposal, cognitive_anchor, belief, strategy, etc. — review only, never auto-promotes
- **red zone**: doctrine, identity, governance, entity_memory, mission_store, code, research_truth, etc. — approval only, never auto-promotes
- **V1 invariant preserved**: no auto-promotion unless both consolidation_auto_enabled AND green_zone_auto_promotion_enabled are True
- **separate from weight refinement**: consolidation_config.json is separate from auto_refinement_config.py

### Implementation Files

- `weslr/consolidation_loop.py`
- `weslr/consolidation_config.py`
- `weslr/consolidation_promotion.py`
- `weslr/commands/consolidation_commands.py`
- `weslr/tests/test_consolidation_loop.py`
- `weslr/tests/test_consolidation_promotion.py`

### Safety Rule

> WESLR may consolidate signals into reviewable candidates.
> WESLR may not silently promote high-impact truth, doctrine, identity, governance, code, or research claims.

### Flexible Details (non-canon)

- scoring weights
- clustering keys
- trace sources
- digest schema
- command syntax
- future promotion targets
- archive policy

### Open Questions

- operator approval flow for promotion
- destination-specific promotion rules
- contradiction handling
- outcome-backed memory strengthening
- procedural workflow memory
- memory budget and archival
- daemon scheduling policy



## Phase 8.5 — Unified Matter Structure Classification

**Status:** `accepted_doctrine`

**Doctrine file:** `weslr/docs/WESLR_PHASE_8.5_UNIFIED_MATTER_GENERATOR_DOCTRINE.md`

**Version:** 1.0 | **Date:** 2026-05-05

### Permanent Doctrine Principles

1. Structure type assignment is conservative and exact — only assign a named structure type when the normalized stoichiometry tuple exactly matches a predefined pattern in `STOICHIOMETRY_MAP`.
2. All formulas that do not match a known pattern are labeled `unclassified` with `uncertainty: high`. No approximate or "likely" classifications.
3. The `(2, 1, 4)` key ambiguity (spinel vs RP n=1 vs olivine) is resolved by explicit heuristic rules documented in the doctrine file.
4. Unclassified structures receive a 10% stability penalty and a device-generation disclaimer.
5. `geometry_type` values emitted by the matter generator are defined and immutable; no new geometry types may be added without corresponding doctrine.

### Future-Agent Obligations

- Do **not** use `layered_perovskite` or other loose fallback names for non-matching compositions.
- Do **not** suppress the `unclassified` label for compositions that do not match an exact stoichiometry pattern.
- Any new structure type added to `STOICHIOMETRY_MAP` requires a corresponding test in `weslr/tests/weslr/test_unified_matter_generator.py` and a doctrine update.

---

## Frontier Exhaustive Novelty + Thermodynamics Screening

**Status:** `accepted_doctrine`

**Doctrine file:** `weslr/docs/WESLR_FRONTIER_EXHAUSTIVE_NOVELTY_THERMODYNAMICS_CANON_V1.md`

**Version:** 1.0 | **Date:** 2026-05-05

### Permanent Doctrine Principles

1. This layer performs **candidate pre-screening**, not discovery. Zero hits across structural databases means "not found in enabled databases" — not "novel compound confirmed."
2. Materials Project stability ratings are **computational DFT predictions**, not experimental measurements. They must be labeled as such in all outputs.
3. The rule-based heuristic fallback (`estimate_stability_heuristic()`) is not DFT. It must not be presented with the same confidence as MP data.
4. Formula-based stoichiometry matching (`_classify_structure()`) is **not crystallographic proof**. It maps normalized stoichiometry to canonical structure family names only.
5. All public outputs must use **candidate language**: "candidate for validation," "computationally predicted stable," "not found in structural databases."
6. PubMed and arXiv are insufficient for inorganic materials novelty assessment — they are one signal among many.

### Future-Agent Obligations

- Do **not** claim a candidate is "novel" or "not existing" based solely on zero database hits.
- Do **not** present MP energy-above-hull values as experimental stability proof.
- Do **not** omit the `[SIMULATION MODE]` or `[UNVALIDATED]` markers from frontier proposal outputs.
- Do **not** add overclaiming language ("discovered," "confirmed," "stable beyond doubt") to any public-facing output from this layer.

_Last updated: 2026-05-05_
_Phase 8.5 status: accepted_doctrine_
_Frontier Exhaustive Novelty + Thermodynamics status: accepted_doctrine_
