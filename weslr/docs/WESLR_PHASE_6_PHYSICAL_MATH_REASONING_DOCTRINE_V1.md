# WESLR Phase 6 — Physical & Mathematical Reasoning Doctrine

**Version:** 1.0
**Date:** 2026-05-03
**Phase:** 6.1

---

## Purpose

Define how Weslr acquires physical intuition, performs mathematical derivation, and proposes experiments — without violating the deterministic anchor or governance boundaries.

---

## Core Principles (unchanged)

- **Deterministic authority** over all state changes.
- **Probabilistic assistance** allowed only as per P11.
- **No hidden learning** — all rules are explicit and operator-editable.
- New reasoning modules are **read-only or proposal-only** — they never execute code that changes system state or controls hardware.
- **Operator approval required** for adding new physical rules or mathematical axioms.

---

## Phase 6.1 — Physical Constraints Checker

### What it does

`weslr/physics_constraints.py` provides `validate_hypothesis()`, which runs a suite of physical consistency checks against any hypothesis dict. It reads from the operator-editable `weslr/physics_rules.json`.

### Check categories

| Check | Severity | Description |
|-------|----------|-------------|
| Forbidden patterns | Hard | Rejects claims like "efficiency > 100%" (perpetual motion) |
| Charge balance | Hard | Uses oxidation-state heuristics; net charge ≠ 0 for neutral compounds |
| Positive stoichiometry | Hard | Coefficients must be > 0 and < 1000 |
| Bandgap ≥ 0 eV | Hard | PV absorber bandgap cannot be negative |
| Efficiency [0,1] | Hard | Efficiency must be in physically realizable range |
| Dose window | Soft | Biological dose 0.01–500 mg/kg; warns if exceeded |
| Operator unit checks | Configurable | Fields checked against `physics_rules.json` ranges |

### Hard vs Soft

- **Hard violation** → hypothesis is flagged `passed=False` and **rejected** (or marked with `_rejected=True`)
- **Soft warning** → `warnings` list populated; hypothesis proceeds with caution note

### Operator-editable rules

`weslr/physics_rules.json` controls:
- Which conservation rules apply to which domains
- Unit ranges for typed fields (bandgap in eV, efficiency as fraction, dose in mg/kg)
- Forbidden transformation patterns (scanned against hypothesis text)
- Whether each rule is `hard` or `soft`

---

## Phase 6.2+ (future)

| Phase | Capability | Status |
|-------|-----------|--------|
| 6.2 | Symbolic mathematics (sympy) — read-only equation manipulation | future |
| 6.3 | ODE proposer — from natural language propose ODE form, don't solve | future |
| 6.4 | Quantum logic awareness — superposition, circuit proposals only | future |
| 6.5 | Basic causality detection — temporal order + intervention proxy | future |
| 6.6 | Enhanced temporal reasoning — timestamps, cycle detection | future |
| 6.7 | Spatial reasoning (RDKit read-only) — 3D conformers, docking scores | future |
| 6.8 | Experiment simulation stub — mocked ODE integration, prediction output | future |

---

## Integration with /explore

The `explore_engine.py` `generate_hypotheses()` function can call `validate_hypothesis()` after generating raw hypotheses:

```python
# Integration point (not auto-executed)
for hyp in raw_hypotheses:
    v = validate_hypothesis(hyp, domain=detected_domain)
    if not v["passed"]:
        hyp["_rejected"] = True
        hyp["_rejection_reasons"] = v["hard_violations"]
    if v["warnings"]:
        hyp["_warnings"] = v["warnings"]
```

This step is **gated behind an operator decision** before being activated.

---

## Boundaries (non-negotiable)

- ❌ No automatic execution of generated code
- ❌ No hidden learning — all rules are explicit, operator-reviewed
- ❌ No real-time hardware control from these modules
- ❌ No network from reasoning libraries (sympy, rdkit) — isolated only
- ✅ New physical theories / axioms → experiment proposal queue → operator approval

---

## Relation to existing doctrine

- **P11** (probabilistic assistance): symbolic math via sympy is deterministic — no probability, so permitted.
- **No-hidden-learning rule** remains: new rules added by operator only, not learned from data.
- **Deterministic anchor** still holds: reasoning is deterministic or probabilistic-as-advisory only.
---

## 6.4 Quantum logic awareness

### Purpose

Enable Weslr to represent and manipulate simple quantum states — superposition, interference, and simple circuits — as part of hypothesis proposal and analysis. This is a *simulation* layer, not a connection to real quantum hardware.

### What is modeled

- **Quantum state vectors**: normalized complex amplitude vectors for 1–3 qubits
- **Single-qubit gates**: H (Hadamard), X (Pauli-X / NOT), Z (Pauli-Z / phase flip)
- **Two-qubit gates**: CNOT (controlled-NOT, qubit 0 = control, qubit 1 = target for 2-qubit states; generalized to arbitrary indices for N-qubit)
- **Measurement**: probabilistic collapse with deterministic pseudorandom (seed derived from state vector hash — reproducible per input, no user-controllable seed in commands)
- **State notation**: Dirac ket strings (`|0⟩`, `|1⟩`, |+⟩, |−⟩, `|00⟩`, `|01⟩`, …), superposition via `a|0⟩ + b|1⟩`

### Constraints (non-negotiable)

- **No real quantum hardware** — all operations are simulation only
- **No external API calls** — all gate matrices are hardcoded, no network access
- **Read-only** — no hardware control, no modification of external systems
- **Deterministic measurement** — seed derived from the state vector itself (hash); same state always produces the same measurement outcome; no logging of outcomes for learning (doctrine P11 — public learning boundary)
- **Multi-tenant isolation** — per-user quantum state stored under a session-derived key
- **Maximum circuit depth**: 3 gates, maximum 3 qubits (Phase 6.4 scope)
- **No sympy required** for Phase 6.4 — explicit complex-number matrices suffice

### Interfaces

| Command | Description |
|---|---|
| `/quantum state \|0>` | Parse Dirac notation, normalize, create QuantumState |
| `/quantum state a\|0> + b\|1>` | Create superposition from numeric coefficients |
| `/quantum apply H 0` | Apply Hadamard to qubit 0 |
| `/quantum apply CNOT 0,1` | Apply CNOT: control=0, target=1 |
| `/quantum measure [qubit=0]` | Measure qubit, show outcome + probability + collapsed state |
| `/quantum reset` | Clear current quantum state |

### Integration with discovery engine

When `/explore` or `/propose` receives a query whose domain overlaps quantum keywords:

```
superposition, interference, quantum gate, qubit,
photochemistry, molecular orbital, electron transfer,
entanglement, decoherence
```

Weslr may propose a quantum circuit as part of the hypothesis. The proposal includes:

- `quantum_circuit: true` flag in the hypothesis JSON
- Circuit diagram (text, max depth 3)
- Initial state (e.g. |00⟩)
- Gate sequence (e.g. H(0) → CNOT(0,1))
- Measurement basis
- Outcome probabilities (from the quantum module simulation)

This is an *advisory proposal* — the operator reviews before any downstream use.

### Safety & reproducibility

- All gate matrices are hardcoded `numpy.ndarray` of complex numbers (or pure-Python lists as fallback)
- Measurement uses `random.Random(seed)` where `seed = sha256(state_bytes + str(qubit_index)) % 2**30`
- No measurement outcomes are logged or used for learning
- No external hardware or API calls

### Boundaries (non-negotiable)

- ❌ No connection to real quantum hardware (IBM Q, Rigetti, etc.)
- ❌ No network calls from the quantum module
- ❌ No user-controllable measurement seed (seed is deterministic from state)
- ❌ No logging of quantum measurement outcomes
- ✅ Proposals are advisory only — operator approval required before downstream use

---

## 6.5 Causality detection

### Purpose

Enable Weslr to distinguish correlation from causation, detect candidate causal relationships from observational data or literature, annotate them with causal confidence scores, and suggest interventions — all as advisory hypothesis generation (no causal claims without statistical support).

### What is modeled

- **Correlation tests**: Pearson r (continuous), Spearman ρ (rank), chi-square (categorical 2×2)
- **Temporal precedence heuristic**: event timelines → +1 (A→B), -1 (B→A), 0 (ambiguous/missing)
- **Confounder detection**: simplified back-door criterion — partial correlation via residual method (continuous) or Mantel-Haenszel stratified chi-square (categorical); flags confounder if correlation drops > 0.3 after conditioning
- **Causal confidence scoring**: weighted combination of correlation significance (0.30), temporal precedence (0.40), no confounding (0.30), literature support (0.20); low/medium/high thresholds at 0.4 and 0.7
- **Intervention simulation**: do(A=v) via linear regression on data — read-only, advisory only
- **Dataset registry**: in-memory named datasets with variable arrays; 3 built-in examples

### Interfaces

| Command | Description |
|---|---|
| `/propose cause <A> <B> [dataset_id]` | Full causal analysis with correlation, temporal, confounder, confidence, intervention |
| `/refine cause confounder <X> for <A> <B>` | User adds known confounder; confidence recalculated |
| `/causal graph` | Display current session's causal graph edges |
| `/causal intervene <A>=<value>` | Simulate do(A=value) on most correlated variable |

### Discovery engine integration

When `/explore` finds strong correlations, it may flag "potential causal relationship" if:
- Temporal precedence is consistent (temporal_score ≠ 0)
- User has not flagged a known confounder

The `is_causal_topic()` function checks for keywords: cause, effect, correlation, confounder, intervention, causal graph, dag, backdoor, etc.

### Constraints (non-negotiable)

- **No black-box causal libraries** — all matrix operations are explicit and auditable
- **No causal claims without statistical support** — always include p-values, effect sizes, confidence
- **Deterministic random seeds** — any resampling uses seeded random (seed parameter)
- **Do not simulate interventions on real patients** — only on internal data subsets
- **No learning from measurement outcomes** — doctrine P11 (public learning boundary)
- **Multi-tenant isolation** — causal state stored per session key

### Safety & reproducibility

- All p-values computed via scipy.stats if available; pure-Python fallback uses conservative thresholds
- No external API calls from causality module
- Random seed = 42 (fixed) for all internal tests and simulations
- Intervention simulation is linear regression approximation; causal assumptions apply

### Boundaries (non-negotiable)

- ❌ No causal discovery from time series without temporal data
- ❌ No automatic confounder addition — operator or user must specify via `/refine cause`
- ❌ No downstream causal inference without operator review
- ✅ All outputs include p-values and explicit caveats
