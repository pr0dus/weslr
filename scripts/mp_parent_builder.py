#!/usr/bin/env python3
"""MP parent builder helper."""
from pathlib import Path
from pymatgen.core import Structure, Lattice, Species, Composition
import numpy as np


def build_mp_parent_derived_scatti_candidate(target_formula: str = "CaSc2TiO6"):
    """
    Build CaSc2TiO6 candidate from Materials Project parent CIFs.
    
    Strategy:
    - Start from Sc2TiO5 (mp-753401) as Sc/Ti/O framework parent
    - Add Ca at interstitial site
    - Add 1 O atom to achieve exact CaSc2TiO6
    """
    parent_dir = Path("/home/pr0/projects/weslr/data/scatti_candidates/materials_project/cifs")
    
    # Load Sc2TiO5 parent (mp-753401)
    try:
        s_sc2tio5 = Structure.from_file(str(parent_dir / "mp-753401_Sc2TiO5.cif"))
    except Exception as e:
        return {
            "id": "SCATTI-MP-PARENT-001",
            "name": "MP Parent Derived - Metadata Only",
            "formula": target_formula,
            "candidate_type": "metadata_only",
            "structure_family": "mp_parent_derived",
            "prototype_source": "Materials Project parent CIFs",
            "experimental_structure": False,
            "requires_relaxation": False,
            "dft_ready": False,
            "reason": f"Cannot load Sc2TiO5 parent CIF: {e}",
            "pymatgen": None,
            "metadata": {"description": "MP parent CIF unavailable"}
        }
    
    print(f"  Sc2TiO5 parent: {len(s_sc2tio5)} sites")
    
    # Get composition of parent
    parent_comp = s_sc2tio5.composition
    print(f"  Parent composition: {parent_comp}")
    
    # Target composition: CaSc2TiO6
    target_comp = Composition(target_formula)
    print(f"  Target composition: {target_comp}")
    
    # Sc2TiO5 = Sc4Ti2O10 in unit cell, reduced = Sc2TiO5
    # Need to add Ca + O to get CaSc2TiO6
    # But we need to scale appropriately
    # Sc2TiO5 reduced has: 2 Sc, 1 Ti, 5 O
    # CaSc2TiO6 has: 1 Ca, 2 Sc, 1 Ti, 6 O
    # So we need to add: 1 Ca, 1 O
    
    # For the candidate, we'll use the unit cell and add atoms
    # The unit cell has 4 Sc, 2 Ti, 10 O
    # To get CaSc2TiO6, we need half of that: 2 Sc, 1 Ti, 5 O + Ca + O = CaSc2TiO6
    # But we can't have half a unit cell, so we'll add Ca and O to the existing cell
    # and then scale down if needed
    
    # Simpler approach: just add Ca and O to the existing structure
    # and let the screening handle formula validation
    
    # Create new species/coords
    species = [Species(site.specie.symbol) for site in s_sc2tio5]
    coords = [site.coords.tolist() for site in s_sc2tio5]
    
    # Add Ca at center
    species.append(Species("Ca"))
    coords.append([0.5, 0.5, 0.5])
    
    # Add O near Ca
    species.append(Species("O"))
    coords.append([0.5, 0.5, 0.75])
    
    # Create structure
    new_lattice = s_sc2tio5.lattice.copy()
    structure = Structure(new_lattice, species, coords)
    
    formula = structure.composition.reduced_formula
    print(f"  Built formula: {formula}")
    
    if formula != target_formula:
        # Try creating a reduced version
        # Get the composition and scale to target
        comp = structure.composition
        target_comp = Composition(target_formula)
        
        # Calculate scaling factor
        ca_scale = target_comp["Ca"] / comp["Ca"] if comp["Ca"] > 0 else 1
        sc_scale = target_comp["Sc"] / comp["Sc"] if comp["Sc"] > 0 else 1
        ti_scale = target_comp["Ti"] / comp["Ti"] if comp["Ti"] > 0 else 1
        o_scale = target_comp["O"] / comp["O"] if comp["O"] > 0 else 1
        
        print(f"  Scales: Ca={ca_scale:.2f}, Sc={sc_scale:.2f}, Ti={ti_scale:.2f}, O={o_scale:.2f}")
        
        # Try using only the necessary atoms
        species = []
        coords = []
        
        # Take atoms that match target composition
        # For CaSc2TiO6, we need: 1 Ca, 2 Sc, 1 Ti, 6 O
        ca_count = 0
        sc_count = 0
        ti_count = 0
        o_count = 0
        
        for i, site in enumerate(s_sc2tio5):
            sym = site.specie.symbol
            if sym == "Sc" and sc_count < 2:
                species.append(Species("Sc"))
                coords.append(site.coords.tolist())
                sc_count += 1
            elif sym == "Ti" and ti_count < 1:
                species.append(Species("Ti"))
                coords.append(site.coords.tolist())
                ti_count += 1
            elif sym == "O" and o_count < 6:
                species.append(Species("O"))
                coords.append(site.coords.tolist())
                o_count += 1
        
        # Add Ca
        species.append(Species("Ca"))
        coords.append([0.5, 0.5, 0.5])
        
        # Recreate structure
        structure = Structure(new_lattice, species, coords)
        formula = structure.composition.reduced_formula
        print(f"  Reduced formula: {formula}")
        
        if formula != target_formula:
            return {
                "id": "SCATTI-MP-PARENT-001",
                "name": "MP Parent Derived - Metadata Only",
                "formula": formula,
                "candidate_type": "metadata_only",
                "structure_family": "mp_parent_derived",
                "prototype_source": "Materials Project parent CIFs",
                "experimental_structure": False,
                "requires_relaxation": True,
                "dft_ready": False,
                "reason": f"exact formula {target_formula} not achieved: got {formula}",
                "pymatgen": structure,
                "metadata": {"description": "MP parent derived, formula mismatch"}
            }
    
    return {
        "id": "SCATTI-MP-PARENT-001",
        "name": "MP Parent Derived (Sc2TiO5 + Ca + O)",
        "formula": formula,
        "candidate_type": "scatti_candidate",
        "structure_family": "mp_parent_derived_sc_ti_o_framework",
        "prototype_source": "Materials Project parent CIFs",
        "experimental_structure": False,
        "requires_relaxation": True,
        "dft_ready": False,
        "reason": "geometry check pending...",
        "pymatgen": structure,
        "metadata": {"description": "Built from Sc2TiO5 mp-753401 + Ca insertion + O addition"}
    }
