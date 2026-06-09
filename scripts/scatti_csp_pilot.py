#!/usr/bin/env python3
"""
SCATTI CSP Pilot - Phase 1T

Generate CaSc2TiO6 candidates using pymatgen random generation.
Apply geometry filters.
Export candidates for later CHGNet evaluation.

No DFT/QE execution.
"""

from pathlib import Path
from datetime import datetime, timezone
import json
import numpy as np

from pymatgen.core import Structure, Lattice, Species

output_dir = Path("/home/pr0/projects/weslr/data/scatti_candidates/csp_pilot")
output_dir.mkdir(parents=True, exist_ok=True)
candidates_dir = output_dir / "candidates"
candidates_dir.mkdir(parents=True, exist_ok=True)

target_formula = "CaSc2TiO6"
n_candidates = 50

print(f"CSP Pilot - Phase 1T")
print(f"Target: {target_formula}")

results = []
exact_formula = 0
geometry_pass = 0
geometry_warning = 0
rejected = 0
generated = 0

def check_constraints(s):
    warnings = []
    fatal = False
    min_d = float('inf')
    
    for i, si in enumerate(s):
        for j, sj in enumerate(s):
            if j <= i:
                continue
            d = s.get_distance(i, j)
            if d < min_d:
                min_d = d
            
            si_s, sj_s = si.specie.symbol, sj.specie.symbol
            
            # Cation-cation
            if si_s in ["Ca", "Sc", "Ti"] and sj_s in ["Ca", "Sc", "Ti"]:
                if d < 2.3:
                    warnings.append(f"fatal: {si_s}-{sj_s} {d:.2f}")
                    fatal = True
            
            # O-O
            if si_s == "O" and sj_s == "O":
                if d < 1.8:
                    warnings.append(f"fatal: O-O {d:.2f}")
                    fatal = True
            
            # Cation-O
            if si_s == "O" and sj_s in ["Ti", "Sc", "Ca"]:
                if sj_s == "Ti" and d < 1.7:
                    warnings.append(f"warning: Ti-O {d:.2f}")
                if sj_s == "Sc" and d < 1.8:
                    warnings.append(f"warning: Sc-O {d:.2f}")
                if sj_s == "Ca" and d < 2.0:
                    warnings.append(f"warning: Ca-O {d:.2f}")
            
            if sj_s == "O" and si_s in ["Ti", "Sc", "Ca"]:
                if si_s == "Ti" and d < 1.7:
                    warnings.append(f"warning: Ti-O {d:.2f}")
                if si_s == "Sc" and d < 1.8:
                    warnings.append(f"warning: Sc-O {d:.2f}")
                if si_s == "Ca" and d < 2.0:
                    warnings.append(f"warning: Ca-O {d:.2f}")
    
    return fatal, warnings, min_d

for i in range(n_candidates):
    # Larger lattice to avoid close contacts
    a = 6.0 + (i % 5) * 0.3
    lattice = Lattice.cubic(a)
    
    species = [Species("Ca"), Species("Sc"), Species("Sc"), Species("Ti")]
    species.extend([Species("O") for _ in range(6)])
    
    # Better initial coords
    coords = [
        [0.0, 0.0, 0.0],
        [0.3, 0.3, 0.3],
        [0.7, 0.7, 0.3],
        [0.5, 0.5, 0.5],
        [0.1, 0.1, 0.4],
        [0.9, 0.9, 0.4],
        [0.1, 0.5, 0.1],
        [0.9, 0.5, 0.9],
        [0.5, 0.1, 0.1],
        [0.5, 0.9, 0.9],
    ]
    
    # Random perturbation
    np.random.seed(42 + i * 10)
    for c in coords:
        for j in range(3):
            c[j] = (c[j] + np.random.uniform(-0.1, 0.1)) % 1.0
    
    try:
        structure = Structure(lattice, species, coords)
        formula = structure.composition.reduced_formula
        
        if formula != target_formula:
            continue
        
        exact_formula += 1
        
        fatal, warnings, min_d = check_constraints(structure)
        
        if fatal:
            rejected += 1
            results.append({
                "id": f"SCATTI-CSP-{generated:03d}",
                "formula": formula,
                "density": structure.density,
                "min_distance": min_d,
                "geometry_status": "rejected_geometry",
                "reason": "; ".join(warnings[:5]),
                "candidates_dir": None
            })
            continue
        
        if warnings:
            geometry_warning += 1
            results.append({
                "id": f"SCATTI-CSP-{generated:03d}",
                "formula": formula,
                "density": structure.density,
                "min_distance": min_d,
                "geometry_status": "geometry_warning",
                "reason": "; ".join(warnings[:5]),
                "candidates_dir": None
            })
            continue
        
        geometry_pass += 1
        generated += 1
        
        cid = f"SCATTI-CSP-{generated:03d}"
        structure.to(filename=str(candidates_dir / f"{cid}.cif"))
        structure.to(filename=str(candidates_dir / f"{cid}.POSCAR"))
        
        results.append({
            "id": cid,
            "formula": formula,
            "density": structure.density,
            "min_distance": min_d,
            "geometry_status": "geometry_pass",
            "reason": "passed",
            "candidates_dir": str(candidates_dir / f"{cid}.cif")
        })
        print(f"  PASS: {cid} density={structure.density:.2f}, min_d={min_d:.2f}")
        
    except Exception as e:
        print(f"  ERROR: {e}")

# Summary
summary = {
    "experiment": "scatti_csp_pilot",
    "date": datetime.now(timezone.utc).isoformat(),
    "target_formula": target_formula,
    "n_attempts": n_candidates,
    "exact_formula": exact_formula,
    "geometry_pass": geometry_pass,
    "geometry_warning": geometry_warning,
    "rejected": rejected,
    "results": results
}

with open(output_dir / "csp_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

with open(output_dir / "csp_report.md", "w") as f:
    f.write("# SCATTI CSP Pilot Report\n\n")
    f.write(f"**Date:** {summary['date']}\n")
    f.write(f"**Target:** {target_formula}\n\n")
    f.write("## Summary\n\n")
    f.write(f"- Attempted: {n_candidates}\n")
    f.write(f"- Exact formula: {exact_formula}\n")
    f.write(f"- Geometry pass: {geometry_pass}\n")
    f.write(f"- Geometry warning: {geometry_warning}\n")
    f.write(f"- Rejected: {rejected}\n\n")
    
    if geometry_pass > 0:
        f.write("## Pass Candidates\n\n")
        f.write("| ID | Density | MinDist | Status |\n")
        f.write("|---|---|---|---|\n")
        for r in results:
            if r["geometry_status"] == "geometry_pass":
                f.write(f"| {r['id']} | {r['density']:.2f} | {r['min_distance']:.2f} | {r['geometry_status']} |\n")
    else:
        f.write("No geometry-pass candidates.\n")

print(f"\nResult: {geometry_pass} pass, {geometry_warning} warn, {rejected} rejected")
print(f"Output: {output_dir}/")
