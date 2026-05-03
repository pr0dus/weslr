# WESLR Phase 7 — Unified Hypothesis & Experiment Workflow

## Purpose
Phase 7 provides a unified interface to manage hypotheses from discovery, causality, simulation, and reasoning modules. It enables chaining of operations: discover correlation → propose cause → simulate intervention → forecast outcome → generate report. All stored hypotheses are per-tenant, deterministic, and mock-only.

## Core Components

### 1. HypothesisRepository (`hypothesis_repository.py`)
Per-tenant in-memory store for Hypothesis objects. Deterministic IDs via UUID v5 from `tenant_id + title + timestamp_hour`.

**Hypothesis dataclass fields:**
- `id` — UUID v5 (deterministic for same tenant+title+timestamp_hour)
- `title`, `description`, `domain` — descriptive
- `confidence` — float 0–1
- `status` — draft | active | deprecated
- `provenance` — list of `{source, timestamp, action, parameters}`
- `created_at`, `updated_at` — ISO timestamps
- `metadata` — dict for module-specific data (causal graph, simulation params, forecast horizon)

**Key methods:**
- `add(hypothesis)` → stores with tenant isolation
- `get(id)` → returns hypothesis or None
- `list(status)` → filtered list
- `update(id, changes)` → merges changes
- `compare(id1, id2)` → diff dict with confidence delta, keyword overlap (Jaccard), status differences

### 2. ExperimentSuggester (`experiment_suggester.py`)
Rule-based suggestion engine. Analyzes active hypothesis metadata to identify gaps.

**Suggests when:**
- Causal confidence medium/low → intervention experiment with variable + value range
- Simulation uncertainty high (wide prediction intervals) → parameter refinement
- Temporal forecast missing calibration → more time points
- Spatial geometry unknown → X-ray crystallography stub (no execution)

**Returns `ExperimentSuggestion`:**
- `description`, `rationale`, `estimated_impact` (low/med/high), `required_resources` (simulation only | in silico | lab experiment), `parameters`

### 3. ScenarioExplorer (`scenario_explorer.py`)
Orchestrates multi-module calls for what-if exploration:

```
scenario_parameters → {dose, time_horizon, ...}
  ├── causality.suggest_intervention()  → predicted causal effect
  ├── experiment_simulation.predict()   → dose-response outcome
  ├── temporal_reasoning.forecast()     → time-series projection
  └── quantum_logic.apply_gate()         → quantum circuit (if quantum hypothesis)
```

Returns `ScenarioResult`:
- `narrative` — human-readable description
- `predictions` — dict of numeric outcomes
- `confidence_intervals` — dict of (lower, upper) tuples
- `modules_used` — list of module names that contributed
- `warning` — simulation disclaimer

All calls deterministic via `seed = hash((tenant_id, scenario_params)) % 2**31`.

### 4. ReportGenerator (`report_generator.py`)
Produces summaries from any hypothesis.

**Text format sections:**
1. Header (id, title, status, confidence)
2. Provenance trail (formatted list)
3. Key evidence (from metadata — correlations, causal links, simulation results)
4. Suggested next experiments
5. Scenario quick-commands
6. Footer disclaimer

**JSON format** — same fields as structured dict for export.

---

## Interfaces

| Command | Description |
|---|---|
| `/hypothesis new [title] [description]` | Manually create hypothesis |
| `/hypothesis list [status]` | List hypotheses with IDs |
| `/hypothesis show <id>` | Full details |
| `/hypothesis compare <id1> <id2>` | Comparison table |
| `/hypothesis promote <id>` | Set status=active (one active per tenant) |
| `/hypothesis delete <id>` | Remove (with confirmation) |
| `/experiment suggest` | Based on active hypothesis |
| `/scenario explore <param>=<value> ...` | What-if exploration |
| `/report generate [id] [format=text]` | Generate report |

---

## Constraints
- **Per-tenant isolation** — all storage keyed by `tenant_id`; no cross-tenant leakage
- **Deterministic IDs** — UUID v5 from `tenant_id:title:timestamp_hour`
- **No external APIs** — purely in-memory + deterministic computation
- **Mock only** — all simulation outputs labeled `[SIMULATION MODE – Not real data]`
- **No ML** — rule-based heuristics only for suggestion
- **Graceful degradation** — scenario explorer skips unavailable modules

---

## Integration
- **discovery_engine** — auto-creates draft hypothesis on `/explore` candidate generation
- **causality_commands** — `/propose cause` optionally attaches causal evidence to hypothesis
- **simulation_commands** — `/simulate` results can be attached to active hypothesis metadata
- **Multi-module provenance** — each contributing module calls `hypothesis.update_provenance()`

---

## Determinism
- Hypothesis IDs: UUID v5 of `f"{tenant_id}:{title}:{hour_iso}"` — same content within same UTC hour → same ID
- Scenario seeds: `hash((tenant_id, frozenset(params.items()))) % 2**31`
- All simulation calls use seeded RNG (seed=42 default, overridden by scenario seed)