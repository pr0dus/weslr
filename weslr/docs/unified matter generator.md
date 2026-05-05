# Weslr × Unified Matter Generator — Integration Proposal

## 1. What existing modules could constrain or enrich candidate generation?

| Module | How it enriches generation |
|--------|--------------------------|
| **`hypothesis_repository.py`** | Stores prior hypotheses per tenant. The generator could check the repo before emitting a candidate — if the same composition was investigated before, skip or flag as "previously considered." |
| **`fact_extractor.py`** | Builds a fact store of subject-predicate-object triples from sessions. Triples like `TiO2 → has_bandgap → 3.0 eV` could be parsed into a property lookup table the generator queries instead of estimating blindly. |
| **`causality.py`** | Encodes causal graphs (e.g., composition changes → property changes). Could be used to trace *why* a candidate was generated — what substitution chain led to it — providing a causal narrative for the proposal's provenance. |
| **`temporal_reasoning.py`** | Tracks patterns over time (e.g., "interest in halide perovskites peaked in 2022"). Could bias generation toward underexplored stoichiometries or away from over-reported systems. |
| **`spatial_reasoning.py`** | Encodes crystallographic geometry relationships. Could suggest which prototype structures are geometrically compatible with a given ionic radii combination before the generator attempts to build it. |
| **`domain_ontology.py`** | Defines hierarchical relationships between material classes (e.g., perovskite ⊂ oxide ⊂ inorganic). Could map generated candidates into the ontology, enabling structured queries like "find all oxide perovskites." |

**Example:** Before emitting a perovskite candidate, query `fact_extractor` for known bandgap values of the same A/B-site combination. If the fact store already has it, apply a novelty penalty.

---

## 2. How the graph improves candidate generation

**Current novelty check is PubMed-only (slow, rate-limited).**

A materials knowledge graph would be faster and local:

```
Node: CaO3Ti (perovskite)
  property: bandgap = 2.19 eV
  property: conductivity = 0.64
  related: CaTiO3 (same composition, different stoichiometry rep)
  substituted_A: SrTiO3, BaTiO3  ← from causal graph
  missing_edge → SrTiO3           ← gap detection
```

**Three concrete uses:**

1. **Duplicate suppression** — Before generating, check graph for exact composition. If it exists with measured properties, mark candidate as "known in literature" rather than generating a PubMed call.

2. **Gap detection** — Traverse substitution edges (A-site cations that are structurally similar). If SrTiO₃ and BaTiO₃ both exist but LaTiO₃ does not, flag LaTiO₃ as a high-value gap. The generator can be directed to fill specific gaps.

3. **Substitution rules (rule-based, not ML):**
   - If `Ti ↔ Zr` is a common B-site substitution in perovskites, the generator can propose `CaZrO₃` when `CaTiO₃` appears.
   - If `F ↔ Cl` is a common anion substitution, propose fluoride analogs of chloride candidates.

**Minimal implementation:** A `material_graph.json` (adjacency list) with known compositions, their measured properties, and substitution edges. Grows incrementally from `fact_extractor` and user feedback.

---

## 3. Self-improvement daemon uses for candidate generation

The **`proactive_daemon.py`** currently generates suggestions and writes them to a queue. It is read-only (no execution). To use it for frontier proposals:

**What it can do (within current constraints):**
- Periodically run `generate_candidates()` with different seeds/modes and write high-strangeness candidates to the pending messages queue for operator review.
- Re-check novelty for candidates that previously had `count > 0` (ambiguous) by writing a reminder to retry in N hours.

**What it cannot do (architectural gap):**
- The daemon has no access to external Ollama APIs, so it can't run the generator itself with model inference. It can only use deterministic modules.
- **Proposed extension:** A lightweight `frontier_daemon.py` that runs in the same process, imports `MatterGenerator`, calls `generate_candidates()` (no model needed — deterministic), and enqueues the top proposals via `enqueue()`. Feasibility: ~150 LOC.

**Specific capabilities:**
```
Schedule: every 24h
  1. Run: MatterGenerator(seed=random).generate_candidates(mode="strangeness", max=5)
  2. For each candidate: compute_breakthrough_potential()
  3. If breakthrough > 0.7 → enqueue(f"🔮 High-breakthrough candidate: {formula}")

Schedule: retry queue
  - For candidates with status="novelty_ambiguous":
    enqueue reminder to re-check in 48h
```

---

## 4. User workflow extension for iterative proposal refinement

The **`mission_store.py`** already has `status` tracking and per-tenant missions. The **`reminder_handler.py`** already supports deferred reminders with `/remind`.

**Proposed workflow for "Find a novel p-type transparent conductor":**

```
User: /mission new "Find novel p-type transparent conductor"
  → Mission created with status="active", domain_filter="transparent conducting oxide"

Daemon (frontier_daemon):
  1. generate_candidates(mode="plausible", constraints={domain: "TCO", min_transparency: 0.8})
  2. Run novelty check on top 5
  3. /frontier generate --mode plausible --domain materials --max 5
  4. Present top 3 to user via pending queue message

User picks: "In₂O₃:Sn (ITO variant with F substitution)"
  → /mission update <id> status="under_review", selected_candidate="InO2F"

Iteration step:
  → User: /frontier refine <proposal_id> --constraint "make it p-type by doping with Cu"
  → Refined proposal generated
  → Experiment summary updated
  → Mission status → "experiment_planned"
```

**Status lifecycle managed by mission_store:**
`new → generating → under_review → refining → experiment_planned → completed | discarded`

**Reminder integration:** At "experiment_planned" state, set a reminder in 30 days to check for published results.

---

## 5. Recommended top-two integrations (minimal changes)

### Priority 1: Knowledge graph duplicate suppression (~80 LOC + data file)

**What:** A `material_graph.json` adjacency list + a `graph_check()` function in `unified_matter_generator.py`.

**Why:** Immediately reduces redundant PubMed calls, surfaces gap compositions, and provides substitution rules without any ML.

**Changes:**
- New file: `weslr/data/material_graph.json` (adjacency list, ~50 known compositions initially)
- New function: `MatterGenerator._check_graph(formula)` — returns `{"known": bool, "properties": dict, "gaps": [str]}`
- Modify `generate_candidates()`: before emitting, check graph. If `known`, skip or reduce strangeness score.
- Modify `strangeness_score()`: boost score for compositions that fill a graph gap.

**LOC:** ~80 new lines + graph data file.

---

### Priority 2: Persistent frontier proposal store (~120 LOC)

**What:** Persist proposals to `.weslr/frontier_proposals.jsonl` instead of in-memory only. Extend mission store schema to support `frontier_proposal` as a first-class entity.

**Why:** Proposals currently vanish on restart. A persistent store enables the daemon to retry ambiguous candidates, track status across sessions, and support the iterative refinement workflow.

**Changes:**
- New class `FrontierProposalStore` in `frontier_proposer.py` (JSONL, per-tenant, add/update/list ops)
- Add fields to `FrontierProposal`: `status` (new/under_review/refining/experiment_planned/discarded), `retry_count`, `last_novelty_check`
- Add `update_proposal_status(id, status)` and `list_proposals(status_filter)` functions
- Extend `frontier_commands.py`: add `/frontier status <id> <status>` command

**LOC:** ~120 lines.

---

## 6. Architectural obstacles

| Obstacle | Severity | Mitigation |
|----------|----------|------------|
| **`proactive_daemon.py` is read-only** — cannot call generator or enqueue structured proposals | High | Create a separate `frontier_daemon.py` that imports the deterministic generator module directly; runs in same process, uses same `enqueue()` |
| **No graph store query interface** — `fact_extractor.py` builds triples but has no indexed lookup by subject or predicate | Medium | Build `material_graph.json` as a separate static file (simpler than retrofitting `fact_extractor`); query with plain dict lookups |
| **`hypothesis_repository.py` has no property fields** — stores title/description/confidence but not bandgap, composition, geometry type | Medium | Extend `Hypothesis` dataclass with an optional `properties: dict` field; backward-compatible addition |
| **`mission_store.py` mission schema is fixed** — adding `proposal_id` reference requires schema update | Low | Add `proposal_ids: list[str]` field to `Mission` dataclass; no migration needed (append-only JSONL) |
| **`FrontierProposal` dataclass not persisted** — all storage is in-memory `defaultdict` | High | Addressed by Priority 2 above |

---

**Bottom line:** The two highest-value, lowest-risk integrations are (1) a static material graph for duplicate/gap-aware generation, and (2) a persistent proposal store with status tracking. Both are feasible within the current architecture without modifying any sealed contracts. The daemon extension requires a new module but stays within the existing envelope design.