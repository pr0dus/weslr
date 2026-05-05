# WESLR — Frontier Exhaustion + Thermodynamic Screening Doctrine

**Status:** Active | **Applies to:** `exhaustive_novelty_checker.py`, `frontier_commands.py` | **Effective:** 2026-05-05

---

## 1. What This Layer Does

The exhaustive novelty checker and thermodynamic stability estimator form a **candidate pre-screening layer**. They process formulas produced by the unified matter generator and return:

- Hit counts from inorganic crystal structure databases (COD, OQMD, AFLOW, NOMAD, Materials Project)
- Thermodynamic stability indicators from Materials Project API or rule-based heuristic fallback
- Stability ratings: `stable`, `metastable`, `unstable`, `unknown`, or heuristic equivalents

**This layer does not make discovery claims.** It produces screening signals for human evaluation.

---

## 2. Structural Novelty — What Zero Hits Means

| Condition | Meaning |
|---|---|
| `total_hits == 0` across all enabled sources | Formula was **not found** in any queried enabled database — **not that it does not exist** |
| `is_novel: True` | No record found in COD, OQMD, AFLOW, NOMAD, or Materials Project — **a research opportunity**, not a confirmed novel compound |
| `is_novel: False` | Record(s) found — the composition or a structural variant is known |

**Limitations:**
- Databases are incomplete snapshots. Absence of hits is not absolute proof of novelty.
- Variant generation (oxide mixture notation, partial formulas, common names) increases coverage but does not guarantee completeness.
- COD, OQMD, AFLOW, NOMAD, and Materials Project each have their own entry criteria and may not index the same materials.

**Appropriate language:** "not found in enabled structural databases" or "candidate for experimental validation."

---

## 3. Thermodynamic Stability — What MP Data Means

When `MATERIALS_PROJECT_API_KEY` is set, the checker queries the Materials Project `/thermo/` endpoint and returns:

- `energy_above_hull` (eV/atom): energy above the convex hull of stable phases. Zero = on the hull.
- `formation_energy_per_atom` (eV/atom): negative values indicate thermodynamic driving force for formation.
- `decomposition_products`: stable phases the material decomposes to at equilibrium.
- `stability_rating`: `stable` (EAH = 0), `metastable` (EAH ≤ 0.15), `unstable` (EAH > 0.15), or `unknown`.

**These are computational DFT predictions.** They are not experimental measurements. A metastable material may persist indefinitely under synthesis conditions; a stable computational prediction may be kinetically inaccessible.

**Appropriate language:** "computationally predicted stable by DFT" or "thermodynamically favorable based on Materials Project calculations."

---

## 4. Heuristic Thermodynamic Fallback

When no MP API key is available, or when a formula is not found in MP, the system falls back to `estimate_stability_heuristic()` — a rule-based scoring model:

- **+0.2** charge-balanced compositions
- **+0.4** known structure prototype match (perovskite, spinel, olivine, etc.)
- **−0.1** unconventional stoichiometry
- **−0.2** presence of toxic or very rare elements (Cd, Hg, Tl)
- **+0.1** fewer than 4 elements

Output ratings: `moderately plausible` (>0.6), `speculative` (>0.3), `unlikely` (≤0.3).

**Heuristic scores are not DFT.** They carry no quantum-chemical fidelity. Use only as a rough triage filter.

---

## 5. Formula-Based Structure Classification — What It Is Not

`unified_matter_generator._classify_structure()` maps normalized stoichiometry tuples to canonical structure family names (perovskite, spinel, rutile, olivine, etc.).

**This is not crystallographic proof.** It is stoichiometric pattern matching:

- Two compounds with the same normalized formula key (e.g., `(1, 1, 3)` for ABX₃) may adopt different actual crystal structures depending on synthesis conditions, pressure, temperature, and doping.
- The distinction between spinel and Ruddlesden-Popper n=1 (both yield `(2, 1, 4)`) uses electronegativity heuristics, not diffraction data.

**Appropriate language:** "stoichiometry matches perovskite family" or "consistent with ABX₃ perovskite-type structure."

---

## 6. PubMed and arXiv — Not Sufficient for Inorganic Materials

The `/frontier generate --novelty-check` and `/frontier discover --real` commands query PubMed and arXiv for literature novelty. These databases are oriented toward life sciences, chemistry, and materials science publications — but:

- Inorganic compounds may not have associated publications even when well-known.
- Novel structural predictions often appear first in arXiv physics/chemistry, which is indexed with delay.
- Formula-level search misses doped variants, solid solutions, and polymorphs.

**PubMed/arXiv novelty scores are one signal among many, not a definitive novelty verdict.**

---

## 7. Output Language Requirements

All public-facing command outputs (`/frontier generate`, `/frontier novelty-exhaustive`, exports) must use **candidate language**:

| Instead of | Use |
|---|---|
| "novel compound" | "candidate not found in structural databases" |
| "stable compound" | "computationally predicted stable (DFT, Materials Project)" |
| "thermodynamically stable" | "thermodynamic stability rating: metastable" |
| "confirmed structure" | "stoichiometry matches [structure type] family" |
| "proven not to exist" | "no record in queried databases" |
| "discovered" | "proposed as candidate for validation" |

---

## 8. Change Log

| Date | Change |
|---|---|
| 2026-05-05 | Initial canon. Structural novelty meaning, MP computational limits, heuristic fallback scope, formula-based classification limits, PubMed/arXiv coverage limits, output language requirements established. |
