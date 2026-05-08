#!/usr/bin/env python3
"""
SCATTI MP Parent Experiment — Phase 1Q

Try to construct ONE exact CaSc2TiO6 candidate from MP parent CIFs.
Does not modify main screening script.
Does not run full screening.
"""

from pathlib import Path
from pymatgen.core import Structure, Lattice, Species, Composition
import json
from datetime import datetime, timezone

# Parent CIF paths
parent_dir = Path("/home/pr0/projects/weslr/data/scatti_candidates/materials_project/cifs")

# Load parent CIFs
print("Loading MP parent CIFs...")
parents = {}
for cif in parent_dir.glob("*.cif"):
    name = cif.stem
    s = Structure.from_file(str(cif))
    parents[name] = s
    print(f"  {name}: {s.composition.reduced_formula}, {len(s)} sites")

# Target formula
target_formula = "CaSc2TiO6"
target_comp = Composition(target_formula)
print(f"\nTarget: {target_formula}")

# Try building from each parent
results = []

for name, s in parents.items():
    parent_comp = s.composition
    print(f"\n--- Trying {name} ---")
    print(f"  Parent: {parent_comp}")
    
    # Calculate what we need to add to get target
    # Target = CaSc2TiO6
    # Parent = Sc2TiO5 or Sc2Ti2O7 or CaSc2O4
    
    # For Sc2TiO5 (Sc4Ti2O10): need to add Ca + O
    # For Sc2Ti2O7 (Sc2Ti2O7): need to add Ca + Sc + O
    # For CaSc2O4 (CaSc2O4): need to add Ti + 2O
    
    # Strategy: copy parent, add missing elements
    
    species = [Species(site.specie.symbol) for site in s]
    coords = [site.coords.tolist() for site in s]
    
    added = []
    
    if name == "mp-753401_Sc2TiO5":
        # Sc2TiO5 -> need CaSc2TiO6
        # Sc2TiO5 has 2 Sc, 1 Ti, 5 O
        # Need: 1 Ca, 2 Sc, 1 Ti, 6 O
        # Add: 1 Ca, 1 O
        species.append(Species("Ca"))
        coords.append([0.5, 0.5, 0.5])
        added.append("Ca")
        
        species.append(Species("O"))
        coords.append([0.5, 0.5, 0.75])
        added.append("O")
        print(f"  Adding: {', '.join(added)}")
    
    elif name == "mp-753802_Sc2Ti2O7":
        # Sc2Ti2O7 -> need CaSc2TiO6
        # Sc2Ti2O7 has 2 Sc, 2 Ti, 7 O
        # Need: 1 Ca, 2 Sc, 1 Ti, 6 O
        # Add: 1 Ca, remove 1 Ti, remove 1 O (dishonest - skip)
        print(f"  Dishonest: Would need to remove atoms")
        continue
    
    elif name == "mp-780402_Sc2Ti2O7":
        # Same as above
        print(f"  Dishonest: Would need to remove atoms")
        continue
    
    elif name == "mp-4056_CaSc2O4":
        # CaSc2O4 -> need CaSc2TiO6
        # CaSc2O4 has 1 Ca, 2 Sc, 4 O
        # Need: 1 Ca, 2 Sc, 1 Ti, 6 O
        # Add: 1 Ti, 2 O
        species.append(Species("Ti"))
        coords.append([0.5, 0.5, 0.5])
        added.append("Ti")
        
        species.append(Species("O"))
        coords.append([0.5, 0.5, 0.75])
        added.append("O")
        
        species.append(Species("O"))
        coords.append([0.5, 0.75, 0.5])
        added.append("O")
        print(f"  Adding: {', '.join(added)}")
    
    # Create new structure
    new_lattice = s.lattice.copy()
    structure = Structure(new_lattice, species, coords)
    
    formula = structure.composition.reduced_formula
    print(f"  Built formula: {formula}")
    
    if formula == target_formula:
        print(f"  ✓ EXACT FORMULA MATCH!")
        
        result = {
            "id": "SCATTI-MP-PARENT-001",
            "name": f"MP Parent Derived ({name})",
            "formula": formula,
            "candidate_type": "scatti_candidate",
            "structure_family": "mp_parent_derived_sc_ti_o_framework",
            "prototype_source": "Materials Project parent CIFs",
            "experimental_structure": False,
            "requires_relaxation": True,
            "dft_ready": False,
            "reason": "geometry check pending...",
            "parent_cif": name,
            "added_atoms": added,
            "pymatgen": structure,
            "metadata": {"description": f"Built from {name}"}
        }
        results.append(result)
        break  # Stop after first successful exact formula build
    else:
        print(f"  ✗ Wrong formula")

# Output directory
output_dir = Path("/home/pr0/projects/weslr/data/scatti_candidates/mp_parent_experiment")
output_dir.mkdir(parents=True, exist_ok=True)

# Write summary JSON
summary = {
    "experiment": "scatti_mp_parent_experiment",
    "date": datetime.now(timezone.utc).isoformat(),
    "target_formula": target_formula,
    "parents_loaded": list(parents.keys()),
    "results": results
}

with open(output_dir / "mp_parent_experiment_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

# Write markdown report
with open(output_dir / "mp_parent_experiment_report.md", "w") as f:
    f.write("# SCATTI MP Parent Experiment Report\n\n")
    f.write(f"**Date:** {summary['date']}\n")
    f.write(f"**Target Formula:** {target_formula}\n\n")
    
    f.write("## Parents Loaded\n\n")
    for name, s in parents.items():
        f.write(f"- **{name}**: {s.composition.reduced_formula}, {len(s)} sites\n")
    
    f.write("\n## Results\n\n")
    if results:
        r = results[0]
        f.write("## SUCCESS\n\n")
        f.write(f"**Candidate ID:** {r['id']}\n\n")
        f.write(f"**Formula:** {r['formula']}\n\n")
        f.write(f"**Parent:** {r['parent_cif']}\n\n")
        f.write(f"**Added atoms:** {', '.join(r['added_atoms'])}\n\n")
        f.write(f"**Structure family:** {r['structure_family']}\n\n")
        
        # Export CIF and POSCAR if pymatgen structure exists
        pymat = r.get("pymatgen")
        if pymat:
            pymat.to(filename=str(output_dir / "SCATTI-MP-PARENT-001.cif"))
            pymat.to(filename=str(output_dir / "SCATTI-MP-PARENT-001.POSCAR"))
            f.write("\n**CIF/POSCAR exported:** Yes\n")
    else:
        f.write("## FAILURE\n\n")
        f.write("No exact formula construction achieved.\n\n")
        f.write("Reason: The parent CIFs could not be combined to produce exact CaSc2TiO6\n")
        f.write("without dishonest transformations (removing atoms, partial occupancy, etc.)\n")

print(f"\nOutput written to: {output_dir}/")
print(f"- mp_parent_experiment_summary.json")
print(f"- mp_parent_experiment_report.md")

# Report result
if results:
    r = results[0]
    print(f"\nRESULT: SUCCESS - {r['formula']}")
else:
    print(f"\nRESULT: FAILURE - No exact formula construction achieved")
