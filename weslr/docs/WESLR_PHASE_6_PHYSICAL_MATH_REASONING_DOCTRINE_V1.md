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