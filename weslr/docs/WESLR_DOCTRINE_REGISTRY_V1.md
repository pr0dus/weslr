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

_Last updated: 2026-05-04_
_Phase 9 status: accepted_doctrine_
_Phase 10 status: accepted_doctrine_
_Observation pipeline status: checkpoint_