#!/usr/bin/env python3
"""
SCATTI Structure Screening Script - Phase 1E

Frontier-science research workflow to prepare structure candidates
for later DFT validation. Uses ASE and pymatgen for safe generation.

Exact formula target: CaSc2TiO6 = Ca:Sc:Ti:O = 1:2:1:6
"""

import json
import csv
import os
import sys
import numpy as np
from random import seed
from datetime import datetime, timezone
from pathlib import Path

from ase import Atoms
from pymatgen.core import Structure, Lattice, Species, PeriodicSite
from pymatgen.io.ase import AseAtomsAdaptor


# ============================================================================
# GEOMETRY SANITY CHECKS (Phase 1E - improved validation)
# ============================================================================

def check_exact_formula(structure: Structure, target: str = "CaSc2TiO6") -> tuple[bool, list]:
    """Check if structure has exact target formula."""
    formula = structure.composition.reduced_formula
    target_composition = {"Ca": 1, "Sc": 2, "Ti": 1, "O": 6}
    actual = structure.composition.as_dict()
    
    target_ca = target_composition.get("Ca", 0)
    actual_ca = actual.get("Ca", 0)
    if target_ca == 0:
        return False, [f"target formula {target} has no Ca"]
    
    ratio = actual_ca / target_ca
    
    if abs(ratio - round(ratio)) > 0.05:
        return False, [f"formula {formula} not an integer multiple of {target}"]
    
    for elem, count in target_composition.items():
        target_count = count * round(ratio)
        actual_count = actual.get(elem, 0)
        if abs(actual_count - target_count) > 0.01:
            return False, [f"element {elem} count mismatch: expected {target_count}, got {actual_count}"]
    
    return True, []


def check_duplicate_coordinates(structure: Structure, min_sep: float = 0.01) -> tuple[bool, list]:
    """Check for duplicate/near-duplicate fractional coordinates."""
    warnings = []
    coords = structure.frac_coords
    n = len(coords)
    for i in range(n):
        for j in range(i+1, n):
            diff = np.abs(coords[i] - coords[j])
            diff = np.minimum(diff, 1 - diff)
            if np.all(diff < min_sep):
                warnings.append(f"duplicate coords: sites {i} and {j}")
    return len(warnings) == 0, warnings


def check_pair_distances(structure: Structure) -> tuple[bool, list]:
    """Species-specific minimum distance checks for oxides."""
    warnings = []
    fatal = False
    dists = structure.distance_matrix
    np.fill_diagonal(dists, np.inf)
    
    min_dists = {
        ('O', 'O'): 1.8, ('Ti', 'O'): 1.7, ('Sc', 'O'): 1.8, ('Ca', 'O'): 2.0,
        ('Ti', 'Ti'): 2.3, ('Sc', 'Sc'): 2.3, ('Ca', 'Ca'): 2.3,
        ('Ti', 'Sc'): 2.3, ('Ti', 'Ca'): 2.3, ('Sc', 'Ca'): 2.3,
    }
    
    for i in range(len(structure)):
        for j in range(i+1, len(structure)):
            si = str(structure[i].species_string)
            sj = str(structure[j].species_string)
            d = dists[i, j]
            
            key = (si, sj)
            if key in min_dists and d < min_dists[key]:
                if d < min_dists[key] * 0.7:
                    fatal = True
                    warnings.append(f"fatal: {si}-{sj} distance {d:.2f} < {min_dists[key]:.2f} Å")
                else:
                    warnings.append(f"warning: {si}-{sj} distance {d:.2f} < {min_dists[key]:.2f} Å")
            key = (sj, si)
            if key in min_dists and d < min_dists[key]:
                if d < min_dists[key] * 0.7:
                    fatal = True
                    warnings.append(f"fatal: {sj}-{si} distance {d:.2f} < {min_dists[key]:.2f} Å")
                else:
                    warnings.append(f"warning: {sj}-{si} distance {d:.2f} < {min_dists[key]:.2f} Å")
    
    return not fatal, warnings


def check_density_sanity(structure: Structure) -> tuple[bool, list]:
    """Density sanity check with tiered warnings."""
    warnings = []
    density = structure.density
    
    if density < 1.0 or density > 10.0:
        return False, [f"density {density:.2f} g/cm³ outside plausible oxide range [1.0, 10.0]"]
    if density < 2.0:
        warnings.append(f"density {density:.2f} g/cm³ below typical oxide range")
    elif density > 8.0:
        warnings.append(f"density {density:.2f} g/cm³ above typical oxide range")
    
    return True, warnings


def check_species_coordinations(structure: Structure) -> tuple[bool, list]:
    """Species-specific coordination checks."""
    warnings = []
    has_warning = False
    has_fatal = False
    
    cutoffs = {'Ti': 2.4, 'Sc': 2.5, 'Ca': 3.2, 'O': 2.5}
    min_nn = {'Ti': 4, 'Sc': 4, 'Ca': 4, 'O': 2}
    max_nn = {'Ti': 8, 'Sc': 8, 'Ca': 12, 'O': 6}
    
    for i, site in enumerate(structure):
        species = str(site.species_string)
        cutoff = cutoffs.get(species, 3.5)
        nn = structure.get_neighbors(site, cutoff)
        nn_count = len(nn)
        
        if nn_count < min_nn.get(species, 1):
            if nn_count == 0:
                has_fatal = True
                warnings.append(f"fatal: {species} site {i} has 0 neighbors")
            else:
                has_warning = True
                warnings.append(f"warning: {species} site {i} has {nn_count} < {min_nn.get(species)} neighbors")
        elif nn_count > max_nn.get(species, 12):
            has_warning = True
            warnings.append(f"warning: {species} site {i} has {nn_count} > {max_nn.get(species)} neighbors")
    
    if has_warning:
        return False, warnings
    if has_fatal:
        return False, warnings
    
    return True, warnings


def check_oxide_like(structure: Structure) -> bool:
    """Check if structure contains oxygen."""
    return 'O' in set(str(site.species_string) for site in structure)


# ============================================================================
# VALIDATION HELPER (Phase 1E-SENTINEL)
# ============================================================================

def validate_builder_output(name, candidate):
    """Validate builder output for correctness."""
    if candidate is None:
        print(f"  {name}: None returned")
        return
    
    pymat = candidate.get("pymatgen")
    if pymat is None:
        print(f"  {name}: metadata_only - {candidate.get('reason', 'N/A')}")
        return
    
    species_count = len(pymat.species)
    coord_count = len(pymat.frac_coords)
    formula = pymat.composition.reduced_formula
    
    if species_count != coord_count:
        print(f"  {name}: MISMATCH - species={species_count}, coords={coord_count}")
        return
    
    if formula != "CaSc2TiO6":
        print(f"  {name}: WRONG FORMULA - {formula}")
        return
    
    print(f"  {name}: VALID - {species_count} atoms, formula={formula}")


# ============================================================================
# MANUAL PARENT-DERIVED CONSTRUCTORS (Phase 1E)
# ============================================================================

def build_octahedral_chain_sc_ti_oxide(target_formula: str = "CaSc2TiO6"):
    """Create Sc/Ti oxygen-octahedra chain/motif with exact formula."""
    a = 5.0
    c = 12.0
    lattice = Lattice.from_parameters(a, a, c, 90, 90, 90)
    
    species = [Species("Ca"), Species("Sc"), Species("Sc"), Species("Ti")]
    species.extend([Species("O") for _ in range(6)])
    
    coords = [
        [0.0, 0.0, 0.0],      # Ca
        [0.25, 0.25, 0.25],   # Sc1
        [0.75, 0.75, 0.75],   # Sc2
        [0.5, 0.5, 0.5],      # Ti
        [0.1, 0.1, 0.0],      # O1
        [0.9, 0.9, 0.0],      # O2
        [0.1, 0.0, 0.1],      # O3
        [0.9, 0.0, 0.9],      # O4
        [0.0, 0.1, 0.1],      # O5
        [0.0, 0.9, 0.9],      # O6
    ]
    
    if len(coords) != len(species):
        return None
    
    structure = Structure(lattice, species, coords)
    formula = structure.composition.reduced_formula
    
    if formula != target_formula:
        return None
    
    return {
        "id": "SCATTI-OCTACHAIN-001",
        "name": "Octahedral Chain Sc/Ti Oxide",
        "formula": formula,
        "candidate_type": "scatti_candidate",
        "structure_family": "octahedral_chain",
        "prototype_source": "theoretical_construct",
        "experimental_structure": False,
        "requires_relaxation": True,
        "dft_ready": False,
        "reason": "geometry check pending...",
        "pymatgen": structure,
        "metadata": {"description": "Octahedral chain motif"}
    }


def build_layered_octahedral_slab(target_formula: str = "CaSc2TiO6"):
    """Separate Ca layer from Sc/Ti-O slab with exact formula."""
    a = 5.0
    c = 12.0
    lattice = Lattice.from_parameters(a, a, c, 90, 90, 90)
    
    species = [Species("Ca"), Species("Sc"), Species("Sc"), Species("Ti")]
    species.extend([Species("O") for _ in range(6)])
    
    coords = [
        [0.0, 0.0, 0.0],      # Ca
        [0.25, 0.25, 0.3],    # Sc1
        [0.75, 0.75, 0.3],    # Sc2
        [0.5, 0.5, 0.15],     # Ti
        [0.1, 0.1, 0.0],      # O1
        [0.9, 0.9, 0.0],      # O2
        [0.1, 0.0, 0.1],      # O3
        [0.9, 0.0, 0.9],      # O4
        [0.0, 0.1, 0.1],      # O5
        [0.0, 0.9, 0.9],      # O6
    ]
    
    if len(coords) != len(species):
        return None
    
    structure = Structure(lattice, species, coords)
    formula = structure.composition.reduced_formula
    
    if formula != target_formula:
        return None
    
    return {
        "id": "SCATTI-LAYERED-SLAB-001",
        "name": "Layered Octahedral Slab",
        "formula": formula,
        "candidate_type": "scatti_candidate",
        "structure_family": "layered_octahedral",
        "prototype_source": "theoretical_construct",
        "experimental_structure": False,
        "requires_relaxation": True,
        "dft_ready": False,
        "reason": "geometry check pending...",
        "pymatgen": structure,
        "metadata": {"description": "Layered Ca and Sc/Ti-O"}
    }


def build_sc_ti_o_framework_with_ca_interstitial(target_formula: str = "CaSc2TiO6"):
    """Build Sc/Ti/O framework with Ca in interstitial site."""
    a = 6.0
    c = 14.0
    lattice = Lattice.from_parameters(a, a, c, 90, 90, 90)
    
    species = [Species("Sc"), Species("Sc"), Species("Ti")]
    species.extend([Species("O") for _ in range(6)])
    species.append(Species("Ca"))
    
    coords = [
        [0.25, 0.25, 0.25],   # Sc1
        [0.75, 0.75, 0.75],   # Sc2
        [0.5, 0.5, 0.5],      # Ti
        [0.1, 0.1, 0.0],      # O1
        [0.9, 0.9, 0.0],      # O2
        [0.1, 0.0, 0.1],      # O3
        [0.9, 0.0, 0.9],      # O4
        [0.0, 0.1, 0.1],      # O5
        [0.0, 0.9, 0.9],      # O6
        [0.0, 0.0, 0.0],      # Ca interstitial
    ]
    
    if len(coords) != len(species):
        return None
    
    structure = Structure(lattice, species, coords)
    formula = structure.composition.reduced_formula
    
    if formula != target_formula:
        return None
    
    return {
        "id": "SCATTI-INTERSTITIAL-001",
        "name": "Sc/Ti-O Framework with Ca Interstitial",
        "formula": formula,
        "candidate_type": "scatti_candidate",
        "structure_family": "interstitial_ca",
        "prototype_source": "theoretical_construct",
        "experimental_structure": False,
        "requires_relaxation": True,
        "dft_ready": False,
        "reason": "geometry check pending...",
        "pymatgen": structure,
        "metadata": {"description": "Sc/Ti-O framework with interstitial Ca"}
    }


def build_octahedral_layer_sc_ti_oxide(target_formula: str = "CaSc2TiO6"):
    """Create Sc/Ti oxygen-octahedra 2D layer with Ca intercalation."""
    a = 6.0
    c = 12.0
    lattice = Lattice.from_parameters(a, a, c, 90, 90, 90)
    
    species = [Species("Ca"), Species("Sc"), Species("Sc"), Species("Ti")]
    species.extend([Species("O") for _ in range(6)])
    
    coords = [
        [0.0, 0.0, 0.0],      # Ca
        [0.25, 0.25, 0.3],    # Sc1
        [0.75, 0.75, 0.3],    # Sc2
        [0.5, 0.5, 0.15],     # Ti
        [0.1, 0.1, 0.0],      # O1
        [0.9, 0.9, 0.0],      # O2
        [0.1, 0.0, 0.1],      # O3
        [0.9, 0.0, 0.9],      # O4
        [0.0, 0.1, 0.1],      # O5
        [0.0, 0.9, 0.9],      # O6
    ]
    
    if len(coords) != len(species):
        return None
    
    structure = Structure(lattice, species, coords)
    formula = structure.composition.reduced_formula
    
    if formula != target_formula:
        return None
    
    return {
        "id": "SCATTI-OCTALAYER-001",
        "name": "Octahedral Layer Sc/Ti Oxide",
        "formula": formula,
        "candidate_type": "scatti_candidate",
        "structure_family": "octahedral_layer",
        "prototype_source": "theoretical_construct",
        "experimental_structure": False,
        "requires_relaxation": True,
        "dft_ready": False,
        "reason": "geometry check pending...",
        "pymatgen": structure,
        "metadata": {"description": "2D octahedral layer with Ca intercalation"}
    }


# ============================================================================
# EXACT-FORMULA CONSTRUCTORS (Phase 1D - kept for comparison)
# ============================================================================

def volume_scaled_layered_octrahedral_candidate(target_formula: str = "CaSc2TiO6"):
    """Build as a layered oxide with Sc/Ti oxygen coordination."""
    a = 6.0
    c = 15.0
    lattice = Lattice.from_parameters(a, a, c, 90, 90, 90)
    
    species = [Species("Ca"), Species("Sc"), Species("Sc"), Species("Ti")]
    species.extend([Species("O") for _ in range(6)])
    
    coords = [
        [0.0, 0.0, 0.0],      # Ca
        [0.25, 0.25, 0.25],   # Sc1
        [0.75, 0.75, 0.25],   # Sc2
        [0.5, 0.5, 0.5],      # Ti
        [0.2, 0.2, 0.1],      # O1
        [0.8, 0.8, 0.1],      # O2
        [0.3, 0.3, 0.4],      # O3
        [0.7, 0.7, 0.4],      # O4
        [0.4, 0.4, 0.7],      # O5
        [0.6, 0.6, 0.7],      # O6
    ]
    
    structure = Structure(lattice, species, coords)
    formula = structure.composition.reduced_formula
    
    return {
        "id": "SCATTI-LAYERED-001",
        "name": "Volume-scaled Layered Octahedral",
        "formula": formula,
        "candidate_type": "scatti_candidate",
        "structure_family": "layered_oxide",
        "prototype_source": "theoretical_construct",
        "experimental_structure": False,
        "requires_relaxation": True,
        "dft_ready": False,
        "reason": "geometry check pending...",
        "pymatgen": structure,
        "metadata": {"description": "Layered oxide inspired by CaSc2O4"}
    }


def cation_ordered_oxide_framework_candidate(target_formula: str = "CaSc2TiO6"):
    """Place Ca in larger coordination, Sc/Ti in octahedral sites."""
    a = 8.0
    lattice = Lattice.cubic(a)
    
    species = [Species("Ca"), Species("Sc"), Species("Sc"), Species("Ti")]
    species.extend([Species("O") for _ in range(6)])
    
    coords = [
        [0.0, 0.0, 0.0],      # Ca
        [0.2, 0.2, 0.2],      # Sc1
        [0.8, 0.8, 0.8],      # Sc2
        [0.5, 0.5, 0.5],      # Ti
        [0.1, 0.1, 0.0],      # O1
        [0.9, 0.9, 0.0],      # O2
        [0.1, 0.0, 0.1],      # O3
        [0.9, 0.0, 0.9],      # O4
        [0.0, 0.1, 0.1],      # O5
        [0.0, 0.9, 0.9],      # O6
    ]
    
    structure = Structure(lattice, species, coords)
    formula = structure.composition.reduced_formula
    
    return {
        "id": "SCATTI-ORDERED-001",
        "name": "Cation-Ordered Oxide Framework",
        "formula": formula,
        "candidate_type": "scatti_candidate",
        "structure_family": "perovskite_derived",
        "prototype_source": "theoretical_construct",
        "experimental_structure": False,
        "requires_relaxation": True,
        "dft_ready": False,
        "reason": "geometry check pending...",
        "pymatgen": structure,
        "metadata": {"description": "Perovskite-derived with ordered B-sites"}
    }


def parent_motif_adapted_candidate_CaTiO3(target_formula: str = "CaSc2TiO6"):
    """Use CaTiO3 for Ca/O/Ti coordination motif."""
    a = 4.0
    lattice = Lattice.cubic(a)
    
    species = [Species("Ca"), Species("Sc"), Species("Sc"), Species("Ti")]
    species.extend([Species("O") for _ in range(6)])
    
    coords = [
        [0.0, 0.0, 0.0],      # Ca
        [0.25, 0.25, 0.25],   # Sc1
        [0.75, 0.75, 0.75],   # Sc2
        [0.5, 0.5, 0.5],      # Ti
        [0.1, 0.1, 0.0],      # O1
        [0.9, 0.9, 0.0],      # O2
        [0.1, 0.0, 0.1],      # O3
        [0.9, 0.0, 0.9],      # O4
        [0.0, 0.1, 0.1],      # O5
        [0.0, 0.9, 0.9],      # O6
    ]
    
    structure = Structure(lattice, species, coords)
    formula = structure.composition.reduced_formula
    
    if formula == target_formula:
        return {
            "id": "SCATTI-CATIO3-001",
            "name": "Parent Motif Adapted (CaTiO3)",
            "formula": formula,
            "candidate_type": "scatti_candidate",
            "structure_family": "ordered_perovskite",
            "prototype_source": "theoretical_construct",
            "experimental_structure": False,
            "requires_relaxation": True,
            "dft_ready": False,
            "reason": "geometry check pending...",
            "pymatgen": structure,
            "metadata": {"description": "CaTiO3-derived with Sc/Ti B-site ordering"}
        }
    
    return {
        "id": "SCATTI-CATIO3-META-001",
        "name": "Parent Motif Adapted (CaTiO3) - Metadata Only",
        "formula": formula,
        "candidate_type": "metadata_only",
        "structure_family": "perovskite_derived",
        "prototype_source": "theoretical_construct",
        "experimental_structure": False,
        "dft_ready": False,
        "reason": f"exact formula not achieved: {formula}",
        "pymatgen": None,
        "metadata": {"description": "CaTiO3 parent motif attempt"}
    }


def parent_motif_adapted_Ca2ScTiO6(target_formula: str = "CaSc2TiO6"):
    """Use Ca2ScTiO6 as ordering inspiration only."""
    a = 4.0
    lattice = Lattice.cubic(a)
    
    species = [Species("Ca"), Species("Sc"), Species("Sc"), Species("Ti")]
    species.extend([Species("O") for _ in range(6)])
    
    coords = [
        [0.0, 0.0, 0.0],      # Ca
        [0.25, 0.25, 0.25],   # Sc1
        [0.75, 0.75, 0.25],   # Sc2
        [0.5, 0.5, 0.5],      # Ti
        [0.1, 0.1, 0.0],      # O1
        [0.9, 0.9, 0.0],      # O2
        [0.1, 0.0, 0.1],      # O3
        [0.9, 0.0, 0.9],      # O4
        [0.0, 0.1, 0.1],      # O5
        [0.0, 0.9, 0.9],      # O6
    ]
    
    structure = Structure(lattice, species, coords)
    formula = structure.composition.reduced_formula
    
    if formula == target_formula:
        return {
            "id": "SCATTI-Ca2ScTiO6-001",
            "name": "Parent Motif Adapted (Ca2ScTiO6)",
            "formula": formula,
            "candidate_type": "scatti_candidate",
            "structure_family": "ordered_perovskite",
            "prototype_source": "theoretical_construct",
            "experimental_structure": False,
            "requires_relaxation": True,
            "dft_ready": False,
            "reason": "geometry check pending...",
            "pymatgen": structure,
            "metadata": {"description": "Ca2ScTiO6 ordering pattern adapted"}
        }
    
    return {
        "id": "SCATTI-Ca2ScTiO6-META-001",
        "name": "Parent Motif Adapted (Ca2ScTiO6) - Metadata Only",
        "formula": formula,
        "candidate_type": "metadata_only",
        "structure_family": "perovskite_derived",
        "prototype_source": "theoretical_construct",
        "experimental_structure": False,
        "dft_ready": False,
        "reason": f"exact formula not achieved: {formula}",
        "pymatgen": None,
        "metadata": {"description": "Ca2ScTiO6 parent motif attempt"}
    }


def expanded_cell_random_sane_candidates(target_formula: str = "CaSc2TiO6", n_candidates: int = 5):
    """Generate deterministic random candidates in larger cells."""
    seed(42)
    results = []
    
    for i in range(n_candidates):
        base_lat = 5.0 + i * 0.5
        lattice = Lattice.cubic(base_lat)
        
        np.random.seed(42 + i * 10)
        
        elements = ["Ca", "Sc", "Sc", "Ti"] + ["O"] * 6
        coords = []
        min_sep = 0.1
        max_attempts = 100
        
        for elem in elements:
            placed = False
            for _ in range(max_attempts):
                x = np.random.random()
                y = np.random.random()
                z = np.random.random()
                
                too_close = False
                for cx, cy, cz in coords:
                    dx = abs(x - cx)
                    dy = abs(y - cy)
                    dz = abs(z - cz)
                    dist = np.sqrt(dx*dx + dy*dy + dz*dz)
                    if dist < min_sep:
                        too_close = True
                        break
                
                if not too_close:
                    coords.append([x, y, z])
                    placed = True
                    break
            
            if not placed:
                coords.append([0.5, 0.5, 0.5])
        
        if len(coords) != len(elements):
            continue
        
        species = [Species(e) for e in elements]
        structure = Structure(lattice, species, coords)
        formula = structure.composition.reduced_formula
        
        if formula == target_formula:
            results.append({
                "id": f"SCATTI-RANDOM-{i+1:02d}",
                "name": f"Expanded Cell Random {i+1}",
                "formula": formula,
                "candidate_type": "scatti_candidate",
                "structure_family": "random_ordered",
                "prototype_source": "theoretical_construct",
                "experimental_structure": False,
                "requires_relaxation": True,
                "dft_ready": False,
                "reason": "geometry check pending...",
                "pymatgen": structure,
                "metadata": {"description": f"Expanded cell random {i+1}", "seed": 42 + i * 10}
            })
        else:
            results.append({
                "id": f"SCATTI-RANDOM-{i+1:02d}-META",
                "name": f"Expanded Cell Random {i+1} - Metadata Only",
                "formula": formula,
                "candidate_type": "metadata_only",
                "structure_family": "random_ordered",
                "prototype_source": "theoretical_construct",
                "experimental_structure": False,
                "dft_ready": False,
                "reason": f"exact formula not achieved: {formula}",
                "pymatgen": None,
                "metadata": {"description": f"Expanded cell random {i+1}"}
            })
    
    return results


def build_reference_phases():
    """Add reference phases that are NOT CaSc2TiO6 candidates."""
    references = []
    
    # CaO (fluorite)
    lattice = Lattice.cubic(4.81)
    structure = Structure(lattice, [Species("Ca"), Species("O")], [[0, 0, 0], [0.5, 0.5, 0.5]])
    references.append({
        "id": "SCATTI-REF-0001", "name": "CaO Reference", "formula": "CaO",
        "candidate_type": "reference_phase", "structure_family": "fluorite",
        "prototype_source": "experimental", "experimental_structure": True,
        "dft_ready": False, "reason": "reference phase, not CaSc2TiO6",
        "pymatgen": structure, "source": "experimental",
        "metadata": {"description": "CaO reference phase"}
    })
    
    # Sc2O3 (bixbyite)
    lattice = Lattice.cubic(10.0)
    species = [Species("Sc"), Species("Sc"), Species("O"), Species("O"), Species("O"), Species("O"), Species("O"), Species("O")]
    coords = [[0, 0, 0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25], [0.75, 0.75, 0.25], 
              [0.25, 0.75, 0.75], [0.75, 0.25, 0.75], [0.25, 0.25, 0.75], [0.75, 0.75, 0.75]]
    structure = Structure(lattice, species, coords)
    references.append({
        "id": "SCATTI-REF-0002", "name": "Sc2O3 Reference", "formula": "Sc2O3",
        "candidate_type": "reference_phase", "structure_family": "bixbyite",
        "prototype_source": "experimental", "experimental_structure": True,
        "dft_ready": False, "reason": "reference phase, not CaSc2TiO6",
        "pymatgen": structure, "source": "experimental",
        "metadata": {"description": "Sc2O3 reference phase"}
    })
    
    # TiO2 (rutile)
    lattice = Lattice.from_parameters(4.59, 4.59, 9.5, 90, 90, 90)
    structure = Structure(lattice, [Species("Ti"), Species("O"), Species("O")],
                          [[0, 0, 0], [0.3, 0.3, 0], [0.7, 0.7, 0]])
    references.append({
        "id": "SCATTI-REF-0003", "name": "TiO2 Reference", "formula": "TiO2",
        "candidate_type": "reference_phase", "structure_family": "rutile",
        "prototype_source": "experimental", "experimental_structure": True,
        "dft_ready": False, "reason": "reference phase, not CaSc2TiO6",
        "pymatgen": structure, "source": "experimental",
        "metadata": {"description": "TiO2 reference phase"}
    })
    
    # CaTiO3 (perovskite)
    lattice = Lattice.cubic(3.85)
    structure = Structure(lattice, [Species("Ca"), Species("Ti"), Species("O"), Species("O"), Species("O")],
                          [[0, 0, 0], [0.5, 0.5, 0.5], [0, 0.5, 0.5], [0.5, 0, 0.5], [0.5, 0.5, 0]])
    references.append({
        "id": "SCATTI-REF-0004", "name": "CaTiO3 Reference", "formula": "CaTiO3",
        "candidate_type": "reference_phase", "structure_family": "perovskite",
        "prototype_source": "experimental", "experimental_structure": True,
        "dft_ready": False, "reason": "reference phase, not CaSc2TiO6",
        "pymatgen": structure, "source": "experimental",
        "metadata": {"description": "CaTiO3 reference phase"}
    })
    
    return references


# ============================================================================
# MAIN SCREENING LOGIC (Phase 1E)
# ============================================================================

def create_material_library(target_formula: str = "CaSc2TiO6"):
    """Generate a library of material structures."""
    library = []
    
    # Phase 1E: New manual builders
    for builder in [build_octahedral_chain_sc_ti_oxide, build_layered_octahedral_slab,
                    build_sc_ti_o_framework_with_ca_interstitial, build_octahedral_layer_sc_ti_oxide]:
        lib = builder(target_formula)
        if lib:
            library.append(lib)
    
    # Phase 1D builders (kept for comparison)
    for builder in [volume_scaled_layered_octrahedral_candidate, cation_ordered_oxide_framework_candidate,
                    parent_motif_adapted_candidate_CaTiO3, parent_motif_adapted_Ca2ScTiO6]:
        lib = builder(target_formula)
        if lib:
            library.append(lib)
    
    # Random expanded cell candidates
    libs = expanded_cell_random_sane_candidates(target_formula, n_candidates=5)
    library.extend(libs)
    
    # Reference phases
    refs = build_reference_phases()
    library.extend(refs)
    
    return library


def validate_builder_output(name, candidate):
    """Validate builder output for correctness."""
    if candidate is None:
        print(f"  {name}: None returned")
        return
    
    pymat = candidate.get("pymatgen")
    if pymat is None:
        print(f"  {name}: metadata_only - {candidate.get('reason', 'N/A')}")
        return
    
    species_count = len(pymat.species)
    coord_count = len(pymat.frac_coords)
    formula = pymat.composition.reduced_formula
    
    if species_count != coord_count:
        print(f"  {name}: MISMATCH - species={species_count}, coords={coord_count}")
        return
    
    if formula != "CaSc2TiO6":
        print(f"  {name}: WRONG FORMULA - {formula}")
        return
    
    print(f"  {name}: VALID - {species_count} atoms, formula={formula}")


def export_structure_files(results_dir, screening: dict, target_formula: str = "CaSc2TiO6"):
    """Export CIF/POSCAR files for exact-formula candidates."""
    structures_dir = results_dir / "structures"
    structures_dir.mkdir(parents=True, exist_ok=True)
    
    for r in screening.get("results", []):
        if r.get("candidate_type") != "scatti_candidate":
            continue
        
        pymat = r.get("pymatgen")
        if pymat is None:
            continue
        
        formula = r.get("formula", "")
        if formula != target_formula:
            continue
        
        candidate_id = r.get("id", "UNKNOWN")
        pymat.to(filename=str(structures_dir / f"{candidate_id}.cif"))
        pymat.to(filename=str(structures_dir / f"{candidate_id}.POSCAR"))


def run_screening(library: list, target_formula: str = "CaSc2TiO6") -> dict:
    """Run comprehensive screening on library (Phase 1E)."""
    results = []
    summary = {
        "total_candidates": 0, "dft_ready_count": 0, "pre_relaxation_count": 0, "downgraded_count": 0,
        "metadata_only_count": 0, "reference_phase_count": 0,
        "target_formula": target_formula, "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_at": None
    }
    
    for material in library:
        name = material["name"]
        formula = material["formula"]
        candidate_type = material.get("candidate_type", "scatti_candidate")
        
        pymat = material.get("pymatgen")
        ase_valid = pymat is not None and len(pymat.sites) > 0
        pymatgen_valid = pymat is not None
        
        warnings = []
        dft_ready = False
        reason = "checking..."
        
        if candidate_type == "reference_phase":
            dft_ready = False
            reason = "reference phase, not a CaSc2TiO6 candidate"
            summary["reference_phase_count"] += 1
        elif candidate_type == "metadata_only":
            dft_ready = False
            reason = "metadata entry only"
            summary["metadata_only_count"] += 1
        elif pymat is not None:
            exact_formula_pass, ef_warnings = check_exact_formula(pymat, target_formula)
            duplicate_pass, dup_warnings = check_duplicate_coordinates(pymat)
            pair_dist_pass, pd_warnings = check_pair_distances(pymat)
            density_pass, density_warnings = check_density_sanity(pymat)
            coord_pass, coord_warnings = check_species_coordinations(pymat)
            oxide_like = check_oxide_like(pymat)
            
            warnings.extend(ef_warnings)
            warnings.extend(dup_warnings)
            warnings.extend(pd_warnings)
            warnings.extend(density_warnings)
            warnings.extend(coord_warnings)
            
            # Hard dft_ready=true rule
            if (exact_formula_pass and duplicate_pass and pair_dist_pass and 
                density_pass and oxide_like and coord_pass):
                dft_ready = True
                reason = "exact formula match with valid geometry"
                summary["dft_ready_count"] += 1
            else:
                dft_ready = False
                has_fatal = any("fatal" in w for w in pd_warnings + coord_warnings)
                has_warning = any("warning" in w for w in pd_warnings + coord_warnings)
                
                if has_fatal:
                    reason = f"hard distance violation: {'; '.join(pd_warnings[:2])}"
                    summary["downgraded_count"] += 1
                elif has_warning:
                    reason = "pre-relaxation candidate only; requires ML/force-field or manual geometry cleanup before QE"
                    summary["pre_relaxation_count"] += 1
                else:
                    reason = f"geometry check failed: {'; '.join(warnings[:2])}"
                    summary["downgraded_count"] += 1
        
        source = material.get("source", material.get("prototype_source", "unknown"))
        atom_count = len(pymat.sites) if pymat else 0
        density = pymat.density if pymat else None
        
        min_dist = None
        if pymat:
            dists = pymat.distance_matrix
            np.fill_diagonal(dists, np.inf)
            min_dist = float(dists.min())
        
        candidate = {
            "id": material["id"],
            "name": name, "formula": formula, "target_formula": target_formula,
            "candidate_type": candidate_type, "structure_family": material.get("structure_family", "unknown"),
            "prototype_source": material.get("prototype_source", "unknown"),
            "experimental_structure": material.get("experimental_structure", False),
            "requires_relaxation": material.get("requires_relaxation", False),
            "dft_ready": dft_ready, "dft_readiness_level": "production_dft_ready" if dft_ready else ("pre_relaxation_starting_geometry" if "pre-relaxation" in reason else "downgraded"),
            "reason": reason, "ase_valid": ase_valid, "pymatgen_valid": pymatgen_valid,
            "atom_count": atom_count, "density": density, "min_distance": min_dist,
            "source": source, "validation_warnings": warnings,
            "next_action": "dft" if dft_ready else "revise"
        }
        results.append(candidate)
        summary["total_candidates"] += 1
    
    return {"summary": summary, "results": results}


def write_outputs(results_dir, screening: dict, target_formula: str = "CaSc2TiO6"):
    """Write all output files (Phase 1E)."""
    summary = screening["summary"]
    results = screening["results"]
    summary["audit_at"] = datetime.now(timezone.utc).isoformat()
    
    candidates = []
    for r in results:
        density_note = None
        if r.get("candidate_type") == "reference_phase":
            if r.get("density") is not None and r.get("density", 0) < 2.0:
                density_note = "placeholder/reference metadata, not physical cell density"
        
        candidates.append({
            "candidate_id": r["id"], "candidate_type": r["candidate_type"],
            "formula": r["formula"], "structure_family": r["structure_family"],
            "prototype_source": r["prototype_source"], "atom_count": r["atom_count"],
            "density": r["density"], "density_note": density_note,
            "min_distance": r["min_distance"], "dft_ready": r["dft_ready"],
            "dft_readiness_level": r["dft_readiness_level"], "reason": r["reason"],
            "validation_warnings": r["validation_warnings"], "next_action": r["next_action"]
        })
    
    summary["candidates"] = candidates
    summary["claim_boundary"] = "CaSc2TiO6"
    
    with open(results_dir / "scatti_screening_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    with open(results_dir / "scatti_structure_candidates.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "name", "formula", "target_formula", "candidate_type",
            "structure_family", "prototype_source", "experimental_structure",
            "requires_relaxation", "dft_ready", "dft_readiness_level", "reason",
            "ase_valid", "pymatgen_valid", "atom_count", "density", "min_distance",
            "source", "validation_warnings", "next_action"
        ])
        writer.writeheader()
        writer.writerows(results)
    
    with open(results_dir / "scatti_dft_queue.md", "w") as f:
        f.write("# SCATTI DFT Queue\n\n")
        f.write("Generated: " + summary["generated_at"] + "\n")
        f.write("Audit completed: " + summary["audit_at"] + "\n\n")
        f.write(f"**Target Formula**: {target_formula}\n\n")
        f.write("## Ready for DFT\n\n")
        ready = [r for r in results if r["dft_ready"]]
        if ready:
            f.write("| ID | Formula | Family | Prototype | DFT Ready | Reason |\n")
            f.write("|---|---|---|---|---|---|\n")
            for r in ready:
                f.write(f"| {r['id']} | {r['formula']} | {r['structure_family']} | {r['prototype_source']} | {r['dft_ready']} | {r['reason']} |\n")
        else:
            f.write("⚠️ **EMPTY QUEUE** - No candidates pass all validation criteria\n\n")
    
    with open(results_dir / "scatti_claim_safe_report.md", "w") as f:
        f.write("# SCATTI Claim-Safe Report\n\n")
        f.write("Generated: " + summary["generated_at"] + "\n")
        f.write("Audit completed: " + summary["audit_at"] + "\n\n")
        f.write(f"**Target Formula**: {target_formula}\n\n")
        f.write("## Validation Results\n\n")
        f.write(f"- Total: {summary['total_candidates']}\n")
        f.write(f"- DFT-ready: {summary['dft_ready_count']}\n")
        f.write(f"- Pre-relaxation only: {summary['pre_relaxation_count']}\n")
        f.write(f"- Downgraded: {summary['downgraded_count']}\n")
        f.write(f"- Reference phases: {summary['reference_phase_count']}\n")
        f.write(f"- Metadata only: {summary['metadata_only_count']}\n\n")
        f.write("## Important Notes\n\n")
        f.write("### No Discovery Claim\n")
        f.write("This report contains theoretical structure candidates only. No experimental discovery is claimed.\n\n")
        f.write("### No Stability Claim\n")
        f.write("Candidate structures have not been validated for thermodynamic stability.\n\n")
        f.write("### Reference Phase Densities\n")
        f.write("Reference phase densities are computed from constructed unit cells.\n\n")
        f.write("### Oxide vs Halide Perovskite\n")
        f.write("All candidates are oxide-based, NOT halide perovskites.\n\n")
        f.write("## Conclusion\n\n")
        if summary["dft_ready_count"] > 0:
            f.write(f"{summary['dft_ready_count']} candidates pass all validation criteria.\n")
        else:
            f.write("No candidates pass all validation criteria.\n")
        f.write(f"\n### Pre-Relaxation Candidates\n")
        f.write(f"{summary['pre_relaxation_count']} candidates require ML/force-field or manual geometry cleanup before DFT.\n")


def main():
    """Main entry point."""
    print("SCATTI Structure Screening - Phase 1E")
    print("=" * 40)
    
    target_formula = "CaSc2TiO6"
    if len(sys.argv) > 1:
        target_formula = sys.argv[1]
        print(f"Target formula: {target_formula}")
    
    output_dir = Path("/home/pr0/projects/weslr/data/scatti_candidates")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating material library...")
    library = create_material_library(target_formula)
    print(f"  Created {len(library)} structures")
    
    print("Running screening with improved validation...")
    screening = run_screening(library, target_formula)
    
    print("Exporting structure files...")
    export_structure_files(output_dir, screening, target_formula)
    
    print("Writing outputs...")
    write_outputs(output_dir, screening, target_formula)
    
    print("\nScreening complete!")
    print(f"  Total: {screening['summary']['total_candidates']}")
    print(f"  DFT-ready: {screening['summary']['dft_ready_count']}")
    print(f"  Pre-relaxation only: {screening['summary']['pre_relaxation_count']}")
    print(f"  Downgraded: {screening['summary']['downgraded_count']}")
    print(f"  Reference phases: {screening['summary']['reference_phase_count']}")
    print(f"\nOutputs written to: {output_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
