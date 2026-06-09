# SCATTI ML/CSP Tool Assessment

**Date:** 2026-05-08  
**Target Formula:** CaSc2TiO6  
**Assessment Status:** Assessment only - no long calculations performed

## Current Environment

- **Python:** 3.12.3
- **CPU:** 18 cores
- **RAM:** 46 GiB
- **GPU:** NVIDIA GeForce GTX 1060 6GB (CUDA 12.2)
- **Current venv:** `.venv-scatti` with ase, pymatgen, spglib, numpy, scipy, scipy

## Installed / Missing Tools

| Tool | Status | Notes |
|------|--------|-------|
| numpy | ✅ Installed | |
| scipy | ✅ Installed | |
| ase | ✅ Installed | 3.28.0 |
| pymatgen | ✅ Installed | 2026.5.4 |
| spglib | ✅ Installed | 2.7.0 |
| seekpath | ❌ Missing | Optional |
| torch | ❌ Missing | Required for CHGNet/MatGL/M3GNet |
| chgnet | ❌ Missing | Latest 0.4.2 |
| matgl | ❌ Missing | Latest 3.0.2 |
| m3gnet | ❌ Missing | Latest 0.2.4 |
| alignn | ❌ Missing | |
| phonopy | ❌ Missing | Latest 3.5.1 |

## ML/CSP Options Assessment

### A. CHGNet (Recommended)
- **Usefulness:** High - specifically designed for geometry relaxation
- **Ca/Sc/Ti/O support:** ✅ Yes
- **CPU-only feasibility:** ✅ Yes
- **GPU feasibility (GTX 1060 6GB):** ✅ Yes - most models < 50MB
- **Install risk:** Low - single pip install
- **Models:** chgnet, chgnet-latest, chgnet-v0.4.2
- **Estimated size:** < 100MB

### B. MatGL / M3GNet
- **Usefulness:** High - structure relaxation with graph neural networks
- **Ca/Sc/Ti/O support:** ✅ Yes
- **CPU-only feasibility:** ✅ Yes
- **GPU feasibility (GTX 1060 6GB):** ✅ Yes - models moderate size
- **Install risk:** Low - single pip install
- **Models:** matgl, m3gnet
- **Estimated size:** ~100-200MB

### C. ASE-only classical/geometry cleanup
- **Usefulness:** Medium - requires reliable force field
- **Ca/Sc/Ti/O support:** ⚠️ Limited - few oxide force fields available
- **CPU-only feasibility:** ✅ Yes
- **Install risk:** None - uses existing ASE
- **Limitations:** Classical potentials may be inaccurate for complex oxides

### D. Phonopy
- **Usefulness:** Low - dynamics only, requires relaxed structure first
- **CPU-only feasibility:** ✅ Yes
- **Install risk:** Low - single pip install
- **Note:** Not useful until after relaxation

### E. CSP Tools
- **PyXtal:** ✅ Feasible - random structure generation with pymatgen support
- **AIRSS:** ⚠️ Feasible - requires NWChem or similar backend
- **USPEX/CALYPSO:** ⚠️ Not open/easy for this assessment
- **Random search with pymatgen/ASE:** ✅ Feasible - already available

## Recommended Next Step

**Option A: Install CHGNet in `.venv-scatti` and test import only.**

**Rationale:**
1. CHGNet is specifically designed for geometry relaxation
2. Supports Ca/Sc/Ti/O elements
3. CPU-only operation available if GPU is tight
4. 6GB GPU is sufficient for most CHGNet models
5. Least risk - single pip install
6. Can test relaxation on pre-relaxation candidates (SCATTI-LAYERED-001, SCATTI-RANDOM-02)

## Risks

- **Torch dependency:** CHGNet requires torch; ~200MB download
- **GPU memory:** If running on GPU, monitor 6GB limit
- **Python version:** CHGNet 0.4.2 requires Python ≥ 3.8, compatible with 3.12

## Explicit No-Calculation Statement

**No ML/CSP calculations have been performed in this assessment.**
Only environment inventory and tool availability were checked.
No structures were relaxed.
No long calculations were run.

## Next Phase Recommendation

If CHGNet installation succeeds and imports cleanly:
- Test CHGNet relaxation on SCATTI-LAYERED-001 or SCATTI-RANDOM-02
- Compare relaxed geometry to original
- If improvement sufficient, consider generating additional candidates with CHGNet

If CHGNet installation fails or tests inconclusive:
- Try MatGL as alternative
- Or proceed to PyXtal-based CSP random structure generation
- Or seek external CIF from literature/Materials Project (requires API key)

---

## Phase 1L (2026-05-08) — CHGNet Install/Test Results

| Check | Result | Notes |
|-------|--------|-------|
| CHGNet installed | ✅ Yes | 0.4.2 via pip in `.venv-scatti` |
| torch installed | ✅ Yes | 2.11.0+cu130 |
| CUDA available | ❌ No | NVIDIA driver 12.2 vs expected 13.x |
| Model load | ✅ Yes | CHGNet v0.3.0 (412,525 params) |
| CPU execution | ✅ Yes | Running on CPU as fallback |

**Install details:**
- `chgnet 0.4.2` + dependencies installed in `.venv-scatti`
- torch 2.11.0 installed with CUDA 13 support
- GPU unavailable due to driver version mismatch
- All models load and run on CPU

**No relaxation run performed.**
**No structures modified.**

## Next Recommended Step

**Phase 1M — dry-run CHGNet evaluation on one pre-relaxation candidate, no geometry write-back yet.**

Since CHGNet model loads successfully:
1. Load SCATTI-LAYERED-001 or SCATTI-RANDOM-02 (from phase 1E)
2. Run CHGNet energy/force prediction
3. Verify output structure geometry looks reasonable
4. Compare original vs CHGNet-predicted properties
5. If successful, proceed to Phase 1N with actual relaxation

If Phase 1M succeeds, CHGNet can be used for geometry cleanup before DFT.

If Phase 1M fails or results poor:
- Try MatGL as alternative relaxer
- Or proceed to PyXtal-based CSP random structure generation
- Or seek external CIF from literature/Materials Project (requires API key)

---

## Phase 1M (2026-05-08) — CHGNet Dry-Run Evaluation

**Candidate evaluated:** SCATTI-LAYERED-001.cif  
**Formula:** CaSc2TiO6  
**Sites:** 10  
**Volume:** 540.0 Å³  

| Metric | Value | Notes |
|--------|-------|-------|
| energy | -5.879 eV | |
| energy_per_atom | -0.588 eV/atom | |
| max_force | 4.72 eV/Å | High — expected for unrelaxed |
| mean_force | 2.60 eV/Å | |
| stress | Tensor | GPa units |
| prediction | ✅ Success | CPU mode |

**Evaluation mode:** CPU only (CUDA unavailable due to driver version mismatch)

**Interpretation:**
- CHGNet successfully evaluated the structure
- Forces are high (max 4.72 eV/Å) — indicates geometry needs relaxation
- No stability claim is made
- No relaxation was performed
- No geometry was modified

**This is a model evaluation only, not relaxation, DFT, or proof of stability.**

## Next Recommended Step

**Phase 1N — CHGNet relaxation trial on a copy of the selected candidate, with strict output separation.**

If CHGNet relaxation produces reasonable output (lower forces, stable energy):
- Proceed to Phase 1O with DFT preparation
- Or export relaxed structure to separate folder for review

If relaxation fails or produces unphysical results:
- Try MatGL as alternative relaxer
- Or assess ASE-based classical force field cleanup

---

## Phase 1N (2026-05-08) — CHGNet Relaxation Trial on SCATTI-LAYERED-001

**Input candidate:** SCATTI-LAYERED-001.cif  
**Output directory:** `data/scatti_candidates/chgnet_relaxation/SCATTI-LAYERED-001/`

### Relaxation Summary

| Metric | Value |
|--------|-------|
| success | ✅ |
| final_formula | CaSc2TiO6 |
| initial_volume | 540.0 Å³ |
| final_volume | 411.1 Å³ |
| volume_change | -23.9% |

### Output Files Created

- `SCATTI-LAYERED-001_chgnet_relaxed.cif`
- `SCATTI-LAYERED-001_chgnet_relaxed.POSCAR`
- `relaxation_summary.json`

### Post-Relaxation Audit

| Check | Result |
|-------|--------|
| formula | CaSc2TiO6 ✅ |
| sites | 10 |
| volume | 411.1 Å³ |
| shortest_distance | 1.483 Å (O-O) |
| Ti-O coordination | 4 ✅ |
| Sc-O coordination | 2 each (1, 2) ⚠️ |
| Ca-O coordination | 2 ✅ |

### Interpretation

- CHGNet relaxation completed successfully
- Volume collapsed by ~24% (may indicate over-relaxation or force field bias)
- Ti-O coordination preserved (4 neighbors) ✅
- Sc-O coordination reduced to 2 neighbors each (below expected 4 for Sc³⁺) ⚠️
- No DFT performed; no stability claim made

**This is ML pre-relaxation only. It is not DFT, not experimental evidence, and not proof of stability.**

## Next Recommended Step

**Decision:** RELAXATION SUCCEEDED BUT GEOMETRY NEEDS AUDIT

**CHGNet relaxation succeeded technically but the relaxed structure is NOT QE-ready.**

**Classification:** `ml_relaxed_but_not_qe_ready`

**Reasons:**
- O-O shortest distance 1.483 Å is suspicious/too short (< 1.80 Å threshold)
- Sc-O coordination only 2 for each Sc (expected ~4 for Sc³⁺)
- Ca-O coordination only 2 (expected ~6-8 for Ca²⁺)
- Volume collapsed by 23.9% (possible force field bias or over-relaxation)

**Not QE-ready because:**
- Forces did not converge to fmax<0.2 eV/Å (max=0.596 eV/Å after 50 steps)
- Short O-O contact suggests structural instability
- Low Sc/Ca coordination numbers indicate force field bias

**Next recommended steps:**
- **Option A:** Try CHGNet dry-run + limited relaxation on SCATTI-RANDOM-02
- **Option B:** Build a less sparse/high-volume starting geometry and relax again
- **Option C:** Stop ML and prioritize external CIF/API route (Materials Project, COD, OQMD)

If Option A selected:
- Phase 1N-bis: CHGNet relaxation on SCATTI-RANDOM-02 (same strict output separation)

If Option B selected:
- Phase 1E-bis: Manual builder with larger cell volume, higher O-O separation

If Option C selected:
- Phase 1P: External CIF/API search (requires Materials Project API key)
