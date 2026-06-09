#!/usr/bin/env python3
"""
Materials Project API Query for SCATTI CaSc2TiO6 project.
Run with: MATERIALS_PROJECT_API_KEY=your_api_key here python -c "..." or export the env var first.
"""
import os
import json
from pathlib import Path

from mp_api.client import MPRester
from pymatgen.core import Structure

# Materials to query
formulas = [
    "CaSc2TiO6",
    "Ca2ScTiO6",
    "Sc2TiO5",
    "Sc2Ti2O7",
    "CaSc2O4",
    "CaTiO3",
    "Sc2O3",
    "TiO2",
    "CaO",
]

def serialize_entry(doc):
    """Convert a SummaryDoc to a JSON-serializable dict."""
    return {
        "material_id": doc.material_id,
        "formula_pretty": doc.formula_pretty,
        "energy_above_hull": float(doc.energy_above_hull) if hasattr(doc, 'energy_above_hull') and doc.energy_above_hull is not None else None,
        "formation_energy_per_atom": float(doc.formation_energy_per_atom) if hasattr(doc, 'formation_energy_per_atom') and doc.formation_energy_per_atom is not None else None,
        "spacegroup_symbol": str(doc.spacegroup_symbol) if hasattr(doc, 'spacegroup_symbol') else None,
        "symmetry": str(doc.symmetry) if hasattr(doc, 'symmetry') else None,
        "theoretical": bool(doc.theoretical) if hasattr(doc, 'theoretical') else None,
        "experimental": bool(doc.experimental) if hasattr(doc, 'experimental') else None,
        "has_structure": bool(doc.structure) if hasattr(doc, 'structure') else True,
    }

def query_mp_for_formula(formula):
    """Query Materials Project for a formula and return results."""
    try:
        api_key = os.environ.get("MATERIALS_PROJECT_API_KEY")
        if not api_key:
            return {"error": "API key not set"}
        
        with MPRester(api_key) as mpr:
            # Query all entries for formula (no field filter to avoid API version issues)
            docs = mpr.materials.summary.search(formula=formula)
            
            results = []
            for doc in docs:
                entry = serialize_entry(doc)
                results.append(entry)
            
            return {"formula": formula, "entries": results, "count": len(results)}
    
    except Exception as e:
        return {"formula": formula, "error": repr(e), "entries": [], "count": 0}

def main():
    outdir = Path("data/scatti_candidates/materials_project")
    outdir.mkdir(parents=True, exist_ok=True)
    cifs_dir = outdir / "cifs"
    cifs_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    for formula in formulas:
        print(f"Querying {formula}...", end=" ")
        result = query_mp_for_formula(formula)
        results.append(result)
        print(f"found {result.get('count', 0)} entries")
    
    # Save results JSON
    with open(outdir / "materials_project_search_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Save results markdown
    with open(outdir / "materials_project_search_results.md", "w") as f:
        f.write("# Materials Project Search Results\n\n")
        f.write("**Date:** 2026-05-08\n")
        f.write("**Target:** CaSc2TiO6 / scatti\n\n")
        f.write("## Summary\n\n")
        f.write("| Formula | Entries | Status |\n")
        f.write("|---------|---------|--------|\n")
        for r in results:
            formula = r.get("formula", "unknown")
            count = r.get("count", 0)
            status = "OK" if count > 0 else ("ERROR" if "error" in r else "no_hit")
            f.write(f"| {formula} | {count} | {status} |\n")
        
        f.write("\n## Detailed Results\n\n")
        for r in results:
            formula = r.get("formula", "unknown")
            f.write(f"### {formula}\n\n")
            if "error" in r:
                f.write(f"**Error:** {r['error']}\n\n")
            elif r.get("count", 0) == 0:
                f.write("No entries found.\n\n")
            else:
                f.write("| material_id | formula | e_above_hull | symmetry | type |\n")
                f.write("|-------------|---------|--------------|----------|------|\n")
                for entry in r.get("entries", []):
                    mid = entry.get("material_id", "?")
                    fp = entry.get("formula_pretty", "?")
                    eah = entry.get("e_above_hull")
                    sg = entry.get("spacegroup_symbol", "?")
                    theo = entry.get("theoretical", "?")
                    exp = entry.get("experimental", "?")
                    f.write(f"| {mid} | {fp} | {eah} | {sg} | {'theoretical' if theo else ('experimental' if exp else 'unknown')} |\n")
                f.write("\n")
    
    print(f"\nResults saved to: {outdir}/")
    print(f"- materials_project_search_results.json")
    print(f"- materials_project_search_results.md")
    
    # List entries for potential CIF export
    print("\n## Potential CIF Exports ##")
    for r in results:
        if r.get("count", 0) > 0:
            for entry in r.get("entries", []):
                mid = entry.get("material_id", "?")
                fp = entry.get("formula_pretty", "?")
                print(f"- {mid} ({fp})")

if __name__ == "__main__":
    main()
