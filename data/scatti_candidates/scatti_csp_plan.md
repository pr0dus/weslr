# SCATTI CSP Plan

**Date:** 2026-05-08  
**Target Formula:** CaSc2TiO6  
**Phase:** 1S (planning) → Phase 1T (execution)

## Current Blocker

CaSc2TiO6 remains an unvalidated computational candidate. No exact external structure confirmed:
- Materials Project: no entry
- SearxNG: no exact hit in tested multilingual queries
- Manual construction: failed or not QE-ready
- CHGNet relaxation: ml_relaxed_but_not_qe_ready

**Path forward:** Generate plausible candidates via formal CSP.

## CSP Tool Options

| Tool | Installability | Pros | Cons | Recommended |
|------|----------------|------|------|-------------|
| PyXtal | ✅ pip install pyxtal (v1.1.3) | Space-group sampling, Python API, easy constraints | Additional dependency | ✅ **RECOMMENDED** |
| AIRSS | ⚠️ External binaries | Physics-based, mature | Complex setup, binary requirements | ❌ Not recommended |
| pymatgen/ASE | ✅ Already available | No new deps | Manual generation, less systematic | ⚠️ Fallback if PyXtal fails |

## Recommended Tool: PyXtal

**Rationale:**
- Purpose-built for crystal structure prediction
- Space-group sampling and constraint handling
- Python API, easy integration with pymatgen/CHGNet
- 600+ GitHub stars, active maintenance
- Lightweight dependency (pymatgen, numpy already available)

**Installation:**
```bash
cd /home/pr0/projects/weslr
. .venv-scatti/bin/activate
pip install pyxtal
```

## Candidate Acceptance Criteria

A CaSc2TiO6 CSP candidate advances only if:
- **Exact formula:** CaSc2TiO6
- **No defects:** No partial occupancies, no hidden vacancies
- **Density:** 2.5–6.5 g/cm³ preferred
- **Geometry:**
  - O-O ≥ 1.8 Å
  - Ti-O ≥ 1.7 Å
  - Sc-O ≥ 1.8 Å
  - Ca-O ≥ 2.0 Å
  - Cation-cation ≥ 2.3 Å
- **Coordination:**
  - Ti: ≥ 4 O neighbors
  - Sc: ≥ 4 O neighbors
  - Ca: ≥ 4 O neighbors
- **CHGNet:** Single-point succeeds, no collapse
- **DFT-ready:** Passes all above for later QE template

## Phase 1T Pilot Design

**Generate:** 50 CaSc2TiO6 candidate structures  
**Method:** PyXtal random structure generation  
**Constraints:** 
- Space groups 1-230 (all possible)
- Minimum interatomic distances
- Target density 2.5–6.5 g/cm³

**Filter:** Apply hard geometry criteria  
**Screen:** CHGNet single-point on survivors  
**Relax:** Top 5 with CHGNet  
**Rank by:**
- Geometry sanity (distance checks)
- Density
- Coordination numbers
- CHGNet force reduction
- No volume collapse

**Output:**
- Candidates with CIF/POSCAR
- Validation report
- Ranking with scores

**DFT Gate:**
Only candidates passing all acceptance criteria advance to QE template generation.

## DFT Gate

**No DFT in Phase 1T.**  
CSP candidates must pass all acceptance criteria before:
- CHGNet relaxation
- QE template generation
- DFT calculation

## Claim Boundary

CSP-generated structures are hypothetical candidates only. They do not prove CaSc2TiO6 exists, is stable, or is synthesizable.  
CSP is a computational screening tool, not experimental evidence.

## Next Step

**Phase 1T — install/use selected CSP tool and generate a small candidate batch, no DFT.**
