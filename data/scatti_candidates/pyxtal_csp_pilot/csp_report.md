# WESLR SCATTI Phase 1T — PyXtal CSP Report

**Generated:** 2026-05-11T02:11:42.296585

## Summary

| Metric | Value |
|--------|-------|
| Formula | CaSc2TiO6 |
| Max candidates | 50 |
| Generated | 50 |
| Exact formula | 50 |
| Geometry pass | 0 |
| Geometry warning | 0 |
| Rejected | 50 |
| Exported | 0 |

## Best Candidates (Geometry Pass)

| ID | Density (g/cm³) | Min Distance (Å) | Classification |
|----|-----------------|------------------|----------------|


## Files Created

- `/home/pr0/projects/weslr/data/scatti_candidates/pyxtal_csp_pilot/csp_summary.json`
- `/home/pr0/projects/weslr/data/scatti_candidates/pyxtal_csp_pilot/candidates/candidate_XXX.cif`
- `/home/pr0/projects/weslr/data/scatti_candidates/pyxtal_csp_pilot/candidates/candidate_XXX.POSCAR`

## Next Steps

If geometry_pass candidates exist and CHGNet evaluation is acceptable:
- Phase 1U: CHGNet relaxation on top candidate copy

If no geometry_pass candidates:
- Adjust CSP constraints or try pymatgen custom CSP

If PyXtal fails:
- Fallback to pymatgen/ASE custom generator
