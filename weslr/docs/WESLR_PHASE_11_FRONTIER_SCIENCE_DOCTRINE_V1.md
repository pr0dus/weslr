# WESLR Phase 11 — Frontier Science Proposer Doctrine V1

**Date:** 2026-05-04
**Purpose:** Enable Weslr to generate genuinely novel scientific hypotheses with multi-axis scoring and difficulty tiers.

---

## 1. Purpose

The Frontier Science Proposer (Phase 11) generates scientifically novel, testable hypotheses across materials science, chemistry, biology, and cross-domain contexts. Each proposal is scored on four axes — novelty, feasibility, risk, and impact — and assigned a difficulty level from ★ Low-hanging fruit to ★★★★ Paradigm shift.

**Goal:** Move Weslr from reactive entity intelligence to proactive science generation, while maintaining safety and governance boundaries.

**What this module is NOT:**
- Not an autonomous experiment executor
- Not a truth store — all proposals are UNVALIDATED until operator review
- Not a peer-reviewer — scoring is deterministic rule-based, not ML

---

## 2. Design Principles

### 2.1 Determinism
All scoring functions are pure rule-based. No machine learning, no probabilistic generation. Same inputs → identical scores. This makes results reproducible and auditable.

### 2.2 Safety by Default
- Live literature searches require explicit user acknowledgment on first use
- Proposals with risk_score > 0.7 are flagged [HIGH RISK – OPERATOR REVIEW REQUIRED]
- No experiment summary shown for high-risk proposals until operator override
- All proposals labeled [FRONTIER PROPOSAL – UNVALIDATED]

### 2.3 Read-Only Operations
- No writes to WESLR fact store, entity graph, or mission store
- Proposals stored only in session memory (per-tenant in-memory dict)
- No automatic truth promotion ever

### 2.4 Literature Novelty Check
- Uses PubMed (NCBI E-utilities) and arXiv public API
- Rate-limited: 3 req/s (PubMed), 1 req/s (arXiv)
- Query built from keyword extraction (chemical formulas, capitalized terms, long words)
- Result deduplicated by paper title

---

## 3. Methods

### 3.1 Candidate Generation

| Domain | Source | Notes |
|--------|--------|-------|
| materials | `combinatorial_materials.build_material_candidates()` | Perovskites, kesterites, oxides |
| chemistry | `combinatorial_chemistry.build_chemistry_candidates()` | Functional group substitution |
| biology | `biology_discovery.handle_propose_biology()` | Ion channels, signaling, bionanoparticles |
| cross_domain | Heuristic re-framing + analogy | Materials→biology, chemistry→energy |

**cross_domain V1:** Simple heuristic — take materials candidates and re-frame with biocompatibility/environmental angle. Chemistry candidates re-framed for energy/catalysis. Full analogy engine (Phase 9) integration planned for V2.

### 3.2 Scoring Axes

#### Novelty Score (0–1)
- Formula: `1 / (1 + paper_count)`
- 0.99 when paper_count == 0 (live search confirmed no results)
- Requires live literature search → user acknowledgment required
- Without ack: defaults to 0.5 (unknown)

#### Feasibility Score (0–1)
- Multiplicative penalties against base 1.0:
  - Rare earth / precious metal elements → ×0.7
  - Toxic elements → ×0.4
  - Temperature > 800°C → ×0.5
  - Pressure > 1e6 Pa → ×0.5
  - Multi-step synthesis (>3 steps) → ×0.7
  - Air/moisture sensitivity → ×0.8

#### Risk Score (0–1)
- Additive model starting at 0.0:
  - Weaponization keywords (nerve agents, select agents) → hard cap 0.8
  - Highly toxic elements (Cd, Hg, As, Pb) → +0.5
  - Explosive gases (H₂, O₂, acetylene) → +0.3
  - Corrosive (HF, conc H₂SO₄) → +0.2
- risk_score > 0.7 → [HIGH RISK – OPERATOR REVIEW REQUIRED]

#### Impact Score (0–1)
- Boost for high-impact keywords (water splitting, CO₂ reduction, superconductor, cancer selectivity) → +0.4
- Boost for breakthrough claims ("record", "unprecedented", "first", "breakthrough") → +0.3
- Base from rarity heuristic: `min(0.2 + 0.5 * (1 - avg(novelty, feasibility)), 1.0)`

### 3.3 Difficulty Levels

| Level | Thresholds | Label |
|-------|-----------|-------|
| ★ Low-hanging fruit | feasibility > 0.7 AND risk < 0.2 AND novelty > 0.8 | easy |
| ★★ Moderate gap | feasibility > 0.4 AND risk < 0.5 AND novelty > 0.6 | moderate |
| ★★★ Hard / high risk | feasibility > 0.2 AND risk < 0.8 | hard |
| ★★★★ Paradigm shift | All other combinations | paradigm |

### 3.4 Refinement
- Users apply constraints via `/frontier refine <id> --constraint "text"`
- Constraint text parsed for keywords (water, air, stable, non-toxic, cheap, scalable, etc.)
- Feasibility re-scored with cumulative penalty per matched keyword
- New difficulty recalculated; proposal updated in session state

---

## 4. Commands

| Command | Description |
|---------|-------------|
| `/frontier propose <domain>` | Generate proposals for domain |
| `/frontier propose <domain> --max N` | Limit to N proposals |
| `/frontier propose <domain> --novelty-threshold X` | Minimum novelty score |
| `/frontier propose <domain> --difficulty {easy,moderate,hard,paradigm}` | Filter by difficulty |
| `/frontier novelty "idea text"` | Check idea novelty via live search |
| `/frontier refine <id> --constraint "text"` | Re-score with constraint |
| `/frontier list` | List stored proposals |
| `/frontier show <id>` | Display full proposal details |

**Acknowledgment flow:** On first live-search command, user sees warning banner. Subsequent commands run live search silently. Acknowledgment state stored per tenant in session memory.

---

## 5. Interfaces

### 5.1 CLI Integration
- Command router in `commands/frontier_commands.py`
- All commands use tenant_id for multi-tenant isolation
- Proposals stored in `_FRONTIER_STATE` (in-memory dict, per tenant)

### 5.2 Module API
```python
from weslr.modules.frontier_proposer import (
    generate_novel_hypotheses,  # main generation
    check_novelty,              # standalone novelty check
    refine_proposal,            # refine with constraints
    get_proposal,               # fetch by ID
    list_proposals,             # list all
    store_proposal,             # store a proposal
    FrontierProposal,           # dataclass
)
```

### 5.3 Integration Points

| Existing Module | Integration | Notes |
|----------------|-------------|-------|
| `combinatorial_materials` | Candidate source | `build_material_candidates()` |
| `combinatorial_chemistry` | Candidate source | `build_chemistry_candidates()` |
| `biology_discovery` | Candidate source | `handle_propose_biology()` |
| `pubmed_adapter` | Novelty check | `search_pubmed()` |
| `arxiv_adapter` | Novelty check | `search_arxiv()` |
| `hypothesis_scorer` | Future integration | `check_charge_balance()` for formula feasibility |

---

## 6. Safety and Governance

### 6.1 Required Gates
- Live PubMed/arXiv search → requires user acknowledgment (one-time per session)
- `risk_score > 0.7` → [HIGH RISK] flag + experiment summary suppressed until override
- No automatic writes to any persistent WESLR store
- No automatic truth promotion — all proposals remain UNVALIDATED

### 6.2 Rate Limiting
- PubMed: `time.sleep(0.34)` between requests (3 req/s limit)
- arXiv: `time.sleep(1.0)` between requests (1 req/s limit)
- Within-session query caching to avoid repeat calls

### 6.3 Labels
- All output prefixed: `[FRONTIER PROPOSAL – UNVALIDATED]`
- High-risk proposals: `[HIGH RISK – OPERATOR REVIEW REQUIRED]`
- Acknowledgment banner on first live search

### 6.4 What Is NOT In Scope
- Autonomous experiment execution (Phase 12+)
- ML-based novelty scoring (future ML layer, not this phase)
- Full Phase 9 analogy engine integration (V2)
- User-facing proposal delivery without operator review

---

## 7. Example Output

```bash
/frontier propose materials --difficulty moderate --max 3
> [⚠️ ACKNOWLEDGMENT: Live literature search will now be performed...]
> [FRONTIER PROPOSAL – UNVALIDATED] domain: materials | difficulty: ★★
>
> 1. ★★ Moderate gap High-entropy alloy FeNiCoCrMn with surface sulfidation for acidic OER
>    Novelty: 0.96 | Feasibility: 0.42 | Risk: 0.35 | Impact: 0.78
>    High-entropy alloy candidate combining Fe, Ni, Co, Cr, Mn with surface sulfidation...
>
> 2. ★★ Moderate gap Perovskite oxynitride LaTiO2N doped with Fe2+ for visible-light water splitting
>    Novelty: 0.98 | Feasibility: 0.55 | Risk: 0.20 | Impact: 0.85
>    Perovskite oxynitride system LaTiO2N with Fe2+ doping targeting visible-light...
```

```bash
/frontier novelty "barium doped lanthanum strontium copper oxide superconductor"
> Novelty check: "barium doped lanthanum strontium copper oxide superconductor"
> Literature hits: 47 | Novelty score: 0.02
> Status: ⚠️ EXISTS — similar work found
> Top matching papers:
>   [PUBMed] Barium doped lanthanum strontium copper oxide...
```

---

## 8. Future Phases

| Phase | Description |
|-------|-------------|
| V2 | Phase 9 analogy engine integration for cross-domain transfer |
| V2 | Full hypothesis scorer integration (charge balance, novelty ranking) |
| V3 | User-facing proposal delivery (separate UI surface) |
| V3 | ML-based novelty scoring layer |
| V4 | Operator approval workflow for experiment summary |
| V4 | Persistent proposal archive (.weslr/frontier_proposals.jsonl) |

---

_Evolves when architecture is sealed, not on impulse. When this file changes, the operator knows._
