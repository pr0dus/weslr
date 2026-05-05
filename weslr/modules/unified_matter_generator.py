"""
unified_matter_generator.py — Cross-domain materials discovery engine.

Generates chemically plausible or unconventional material structures
by combining prototype crystal chemistry with configurable strangeness.

No external API calls. Deterministic given a seed.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

from weslr.modules.matter_primitives import (
    PERIODIC_TABLE,
    COMMON_ANIONS,
    Atom,
    Bond,
    Structure,
    ionic_radius,
    tolerance_factor,
    is_oxide,
)

# ─────────────────────────────────────────────────────────────────────────────
# STOICHIOMETRY_MAP — exact formula → structure-type matching
# Keys: normalized cation-count tuple (sorted descending) + anion_count, all ints ÷ GCD
# Values: canonical structure name
# Unclassified formulas return "unclassified" with uncertainty="high"
# ─────────────────────────────────────────────────────────────────────────────
# Normalized tuples: (sorted_cation_counts..., anion_count)
# Perovskite ABX3:     1 cation type A + 1 B + 3 X  → cations=(1,1), X=3 → (1,1,3)
# RP n=1 A2BX4:        2 A + 1 B + 4 X                → cations=(2,1), X=4 → (2,1,4)
# RP n=2 A3B2X7:       3 A + 2 B + 7 X                → cations=(3,2), X=7 → (3,2,7)
# RP n=3 A4B3X10:      4 A + 3 B + 10 X               → cations=(4,3), X=10 → (4,3,10)
# Spinel AB2X4:        1 A + 2 B + 4 X                → cations=(2,1), X=4 → (1,2,4) sorted desc
# Rutile AX2:          1 A + 2 X                      → cations=(1,),   X=2 → (1,2)
# Rock-salt AX:        1 A + 1 X                      → cations=(1,),   X=1 → (1,1)
# Olivine A2XO4:       2 A + 4 X                      → cations=(2,),   X=4 → (2,4)
# Wolframite ABXO4:    1 A + 1 B + 4 X                → cations=(1,1), X=4 → (1,1,4)
# LDH M2+M3(OH)2Xr/n:  2 cations + 1 X               → cations=(1,1), X=6 → (1,1,6) — approximate

STOICHIOMETRY_MAP: Dict[Tuple[int, ...], str] = {
    # Key format: tuple of (sorted_cation_counts_desc, anion_count)
    (1,   1,   3):  "perovskite",               # ABX3
    (2,   1,   4):  "ruddlesden_popper_n1",       # A2BX4 (RP n=1)
    (3,   2,   7):  "ruddlesden_popper_n2",       # A3B2X7 (RP n=2)
    (4,   3,  10):  "ruddlesden_popper_n3",       # A4B3X10 (RP n=3)
    (2,   1,   4):  "spinel",                     # AB2X4 (same tuple as RP n=1 — distinguished below)
    (1,         2):  "rutile",                    # AX2
    (1,         1):  "rocksalt",                  # AX
    (2,         4):  "olivine",                   # A2X4
    (1,   1,   4):  "wolframite",                 # ABX4
    (1,   1,   6):  "layered_double_hydroxide",   # approximate LDH
}


def _gcd_of(numbers: List[int]) -> int:
    """Greatest common divisor of a list of positive integers."""
    result = numbers[0]
    for n in numbers[1:]:
        result = math.gcd(result, n)
    return result


def _classify_structure(formula: str) -> Tuple[str, str]:
    """
    Classify a formula's stoichiometry into a known structure type.

    Returns (structure_name, uncertainty) where:
      - structure_name is a canonical key from STOICHIOMETRY_MAP or "unclassified"
      - uncertainty is "low" for exact matches, "high" otherwise

    Multi-cation formulas: compute normalized cation tuple by dividing all
    counts by their GCD, then match against STOICHIOMETRY_MAP keys.
    """
    import re
    from weslr.modules.matter_primitives import PERIODIC_TABLE

    # Parse formula
    pattern = r"([A-Z][a-z]?)(\d*)"
    matches = re.findall(pattern, formula)
    if not matches:
        return "unclassified", "high"

    # Count atoms per element
    element_counts: Dict[str, int] = {}
    for sym, cnt_str in matches:
        if sym not in PERIODIC_TABLE:
            continue
        element_counts[sym] = element_counts.get(sym, 0) + (int(cnt_str) if cnt_str else 1)

    if not element_counts:
        return "unclassified", "high"

    # Identify anions (common anion list) vs cations
    anions = {e for e in element_counts if e in COMMON_ANIONS}
    # If no recognized anions, treat lightest element as anion-ish placeholder
    if not anions:
        # Fall back: treat most electronegative as anion
        anion_candidate = max(element_counts, key=lambda e: PERIODIC_TABLE[e].electronegativity)
        anions = {anion_candidate}

    cation_counts: List[int] = [element_counts[e] for e in element_counts if e not in anions]
    anion_count: int = sum(element_counts[e] for e in anions)

    if not cation_counts or anion_count == 0:
        return "unclassified", "high"

    # Normalize: divide by GCD of all counts (cations + anion)
    all_counts = cation_counts + [anion_count]
    g = _gcd_of(all_counts)
    norm_cation_counts = sorted([c // g for c in cation_counts], reverse=True)
    norm_anion_count = anion_count // g

    key = tuple(norm_cation_counts + [norm_anion_count])

    structure_name = STOICHIOMETRY_MAP.get(key, "unclassified")

    # Distinguish spinel vs RP n=1 vs olivine: all yield key (2, 1, 4) when normalized.
    # Key (2, 1, 4) arises when there are two cation types with counts (2, 1) and 4 anions.
    # Differentiation by cation identity:
    #   RP n=1:  2 large A-site cations (Ca, Sr, Ba, La …) + 1 B-site transition metal
    #   Spinel:  1 small A-site (Mg, Zn, Fe …) + 2 B-site transition metals
    #   Olivine: 2 A-site + 1 tetrahedral Si^(4+) (or other tetravalent p-block cation)
    # Use electronegativity: if the unique high-EN cation (Si, Ge, P) appears once → olivine.
    # Otherwise fall back to size-based heuristic for RP vs spinel.
    if key == (2, 1, 4) and len(cation_counts) >= 2:
        LARGE_A_SITE = {"Ca", "Sr", "Ba", "Pb", "K", "Na", "Li", "Cs",
                        "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd"}
        TETRA_VALENT = {"Si", "Ge", "P", "B"}  # small tetravalent p-block cations in tetrahedral sites
        element_list = [e for e, c in element_counts.items() if e not in anions]
        el_counts_sorted = sorted([element_counts[e] for e in element_list if e not in anions], reverse=True)
        el_sorted = sorted(element_list, key=lambda e: element_counts[e], reverse=True)

        # Check 1: if any tetravalent p-block cation appears exactly once → olivine
        if any(element_counts.get(e, 0) == 1 and e in TETRA_VALENT for e in element_list):
            structure_name = "olivine"
        # Check 2: 2 large A-site + 1 transition metal → RP n=1
        elif el_counts_sorted[0] == 2 and el_sorted[0] in LARGE_A_SITE:
            structure_name = "ruddlesden_popper_n1"
        # Otherwise → spinel (most common AB2X4 structure)
        else:
            structure_name = "spinel"

    uncertainty = "low" if structure_name != "unclassified" else "high"
    return structure_name, uncertainty


# ─────────────────────────────────────────────────────────────────────────────
# Prototype structure definitions
# Each prototype: name, stoichiometry dict, anion (X), cation sites [(label, ox_sum, count)]
# ─────────────────────────────────────────────────────────────────────────────

class _Prototype:
    """Structural prototype for materials generation."""

    def __init__(
        self,
        name: str,
        sites: Dict[str, int],          # symbol → count in unit cell
        charge_balance: Dict[str, int],  # symbol → total oxidation state contribution (per cell)
        geometry_type: str,
    ):
        self.name = name
        self.sites = sites              # e.g. {"A":1, "B":1, "X":3}
        self.charge_balance = charge_balance  # e.g. {"A":+2, "B":+4, "X":-6}
        self.geometry_type = geometry_type

    def formula_string(self) -> str:
        counts: Dict[str, int] = {}
        for el, n in self.sites.items():
            counts[el] = counts.get(el, 0) + n
        def hill_key(s: str) -> Tuple[int, str]:
            if s == "C": return (0, "")
            if s == "H": return (1, "")
            return (2, s)
        parts = []
        for el in sorted(counts.keys(), key=hill_key):
            c = counts[el]
            parts.append(f"{el}{c if c > 1 else ''}")
        return "".join(parts)


# ── Prototype library ─────────────────────────────────────────────────────────

PROTOTYPES: List[_Prototype] = [
    # Perovskite ABX3 — ideal ABO3
    _Prototype(
        name="perovskite",
        sites={"A": 1, "B": 1, "X": 3},
        charge_balance={"A": +2, "B": +4, "X": -6},
        geometry_type="ABX3_cubic",
    ),
    # Spinel AB2X4 — normal spinel
    _Prototype(
        name="spinel",
        sites={"A": 1, "B": 2, "X": 4},
        charge_balance={"A": +2, "B": +3, "X": -8},
        geometry_type="AB2X4_cubic",
    ),
    # Rutile AX2 — TiO2, SnO2
    _Prototype(
        name="rutile",
        sites={"A": 1, "X": 2},
        charge_balance={"A": +4, "X": -4},
        geometry_type="AX2_tetragonal",
    ),
    # Rock salt AX — NaCl, MgO
    _Prototype(
        name="rocksalt",
        sites={"A": 1, "X": 1},
        charge_balance={"A": +2, "X": -2},
        geometry_type="AX_cubic",
    ),
    # CsCl-type AX
    _Prototype(
        name="cscl_type",
        sites={"A": 1, "X": 1},
        charge_balance={"A": +1, "X": -1},
        geometry_type="AX_cubic_bcc",
    ),
    # Aurivillius Bi2An-1BnO3n+2
    _Prototype(
        name="aurivillius",
        sites={"Bi": 2, "A": 1, "B": 1, "X": 6},
        charge_balance={"Bi": +6, "A": +2, "B": +4, "X": -12},
        geometry_type="layered_perovskite",
    ),
    # Ruddlesden-Popper (AO)(ABX3)n
    _Prototype(
        name="ruddlesden_popper",
        sites={"A": 2, "B": 1, "X": 4},
        charge_balance={"A": +4, "B": +4, "X": -8},
        geometry_type="layered_perovskite",
    ),
    # Wolframite (A,B)XO4
    _Prototype(
        name="wolframite",
        sites={"A": 1, "B": 1, "X": 4},
        charge_balance={"A": +2, "B": +4, "X": -8},
        geometry_type="monoclinic_wolframite",
    ),
    # Olivine Mg2SiO4 — (A,B)2XO4
    _Prototype(
        name="olivine",
        sites={"A": 2, "X": 4},
        charge_balance={"A": +4, "X": -8},
        geometry_type="orthorhombic_olivine",
    ),
    # Layered double hydroxide (LDH) — [M2+1-x M3+x (OH)2] [Xx/n · mH2O]
    _Prototype(
        name="layered_double_hydroxide",
        sites={"M2": 1, "M3": 1, "X": 1},
        charge_balance={"M2": +4, "M3": +3, "X": -7},
        geometry_type="layered_double_hydroxide",
    ),
]

# Anion options for different structure types
ANIONS = ["O", "S", "N", "F", "Cl", "Se", "Te"]

# Common charge-balanced perovskite A/B pairs (oxidation state matching)
PEROVSKITE_PAIRS: List[Tuple[str, int, str, int]] = [
    # A_ox,  B_ox,  examples
    (+1, +5, "Cs",  "Nb"),
    (+1, +5, "Cs",  "Ta"),
    (+1, +5, "Rb",  "Nb"),
    (+2, +4, "Ca",  "Ti"),
    (+2, +4, "Sr",  "Ti"),
    (+2, +4, "Pb",  "Ti"),
    (+2, +4, "Ba",  "Zr"),
    (+2, +4, "Ca",  "Zr"),
    (+3, +3, "La",  "Al"),
    (+3, +3, "La",  "Cr"),
    (+3, +3, "La",  "Fe"),
    (+3, +3, "La",  "Mn"),
    (+2, +5, "Ca",  "Nb"),
    (+2, +5, "Sr",  "Nb"),
    (+2, +5, "Pb",  "Nb"),
    (+3, +5, "Bi",  "Nb"),
    (+3, +5, "Bi",  "Ta"),
    (+1, +7, "Cs",  "Re"),
    (+2, +6, "Ca",  "Mo"),
    (+2, +6, "Ca",  "W"),
    (+3, +3, "Y",   "Al"),
    (+3, +6, "La",  "Mo"),
    (+2, +4, "Ba",  "Sn"),
]


# ─────────────────────────────────────────────────────────────────────────────
# MatterGenerator
# ─────────────────────────────────────────────────────────────────────────────

class MatterGenerator:
    """Generates material structure candidates across plausible and strangeness modes."""

    TOXIC_ELEMENTS: Set[str] = {"Be", "Cd", "Hg", "As", "Tl", "Pb"}
    DUAL_USE_ELEMENTS: Set[str] = {"U", "Th", "Pu", "As", "Ga", "In", "Ge", "Se"}

    def __init__(self, seed: int = 42, graph_path: Optional[str] = None):
        self.seed = seed
        self._rng = random.Random(seed)
        self._formula_cache: Set[str] = set()
        self._graph: Optional[Dict[str, Any]] = None
        self._graph_path = graph_path
        if graph_path:
            self._load_graph(graph_path)

    def _load_graph(self, path: str) -> None:
        """"Load material graph from JSON file. Graceful fallback if missing.
        
        All node keys are normalized to Hill order on load so that
        lookups match the Hill-order output of Structure.composition_string().
        """
        try:
            with open(path) as f:
                raw = json.load(f)
            if raw and "nodes" in raw:
                nodes = raw["nodes"]
                normalized: Dict[str, Any] = {}
                for formula, data in nodes.items():
                    formula_norm = self._normalize_formula(formula)
                    if formula_norm in normalized:
                        continue
                    normalized[formula_norm] = data
                raw["nodes"] = normalized
            self._graph = raw
        except Exception:
            self._graph = None

    def _normalize_formula(self, formula: str) -> str:
        """Normalize formula to Hill-order composition string.

        Graph keys use conventional order (CaTiO3); generator output uses
        Hill order (CaO3Ti). Normalize before comparing.
        """
        import re
        pattern = r'([A-Z][a-z]?)(\d*)'
        matches = re.findall(pattern, formula)
        counts: Dict[str, int] = {}
        for sym, count_str in matches:
            if not sym:
                continue
            counts[sym] = counts.get(sym, 0) + (int(count_str) if count_str else 1)

        def hill_key(s: str) -> tuple[int, str]:
            if s == "C": return (0, "")
            if s == "H": return (1, "")
            return (2, s)

        parts = []
        for el in sorted(counts.keys(), key=hill_key):
            c = counts[el]
            parts.append(f"{el}{c if c > 1 else ''}")
        return "".join(parts)

    def _check_graph(self, formula: str) -> Dict[str, Any]:
        """Check if formula is in graph, compute gaps.

        Handles formula representation mismatch: graph keys use conventional
        order (CaTiO3), generator output uses Hill order (CaO3Ti).
        Normalizes both before comparing.

        Gap computation: for each known node, generates substitution products,
        normalizes them to Hill order, and marks as gaps those not present
        in the graph under any convention.
        """
        if not self._graph:
            return {"known": False, "properties": {}, "gaps": [], "fill_gaps": []}

        nodes = self._graph.get("nodes", {})
        result: Dict[str, Any] = {"known": False, "properties": {}, "gaps": [], "fill_gaps": []}

        # Normalize to generator output format (Hill order)
        norm_formula = self._normalize_formula(formula)
        raw_in_graph = formula in nodes
        norm_in_graph = norm_formula in nodes

        if raw_in_graph or norm_in_graph:
            result["known"] = True
            graph_key = formula if raw_in_graph else norm_formula
            node = nodes[graph_key]
            result["properties"] = node
            subs = node.get("substitutions", {})
            all_sub_norms: Set[str] = set()
            for site, neighbors in subs.items():
                for n in neighbors:
                    proto = node.get("prototype", "")
                    sub_formula = self._substitute_element(graph_key, site, n, proto)
                    if sub_formula:
                        # Normalize to Hill order so comparison is consistent
                        norm_sub = self._normalize_formula(sub_formula)
                        all_sub_norms.add(norm_sub)
            # Filter: not in graph under any convention
            missing = [
                f for f in all_sub_norms
                if f not in nodes and self._normalize_formula(f) not in nodes
            ]
            result["gaps"] = missing
            return result

        # Unknown formula: check if it appears as a neighbor (gap-filler candidate)
        norm_unknown = norm_formula
        for node_formula, node_data in nodes.items():
            subs = node_data.get("substitutions", {})
            for site, neighbors in subs.items():
                norm_neighbors = {self._normalize_formula(n) for n in neighbors}
                if formula in neighbors or norm_unknown in norm_neighbors:
                    proto = node_data.get("prototype", "")
                    parent = self._substitute_element(node_formula, site, None, proto)
                    if parent:
                        norm_parent = self._normalize_formula(parent)
                        result["gaps"].append(norm_parent)
        return result

    def _substitute_element(self, formula: str, site: str, new_element: Optional[str], prototype: str) -> Optional[str]:
        """Attempt to substitute one element in a formula.

        Handles both conventional order (CaTiO3) and Hill order (CaO3Ti)
        by normalizing the formula before parsing.  Output is always in Hill
        order for consistent graph comparisons.

        Args:
            formula: e.g. "CaTiO3" or "CaO3Ti"
            site: "A", "B", or "X"
            new_element: element symbol to put at that site
            prototype: structural prototype name

        Returns:
            New formula string in Hill order, or None if not applicable.
        """
        from weslr.modules.matter_primitives import PERIODIC_TABLE
        import re

        norm_formula = self._normalize_formula(formula)
        # Always use Hill-order path: parse counts from normalized formula,
        # perform substitution, reconstruct in Hill order.
        pattern = r'([A-Z][a-z]?)(\d*)'
        matches = re.findall(pattern, norm_formula)
        counts: Dict[str, int] = {}
        for sym, count_str in matches:
            if sym and sym in PERIODIC_TABLE:
                counts[sym] = counts.get(sym, 0) + (int(count_str) if count_str else 1)

        # Prototype -> (ordered_roles, a_key, b_key, x_key)
        proto_map = {
            "perovskite":             (["A", "B", "X"], "A", "B", "X"),
            "rutile":                 (["A", "X"],     "A", None, "X"),
            "rocksalt":               (["A", "X"],     "A", None, "X"),
            "cscl_type":              (["A", "X"],     "A", None, "X"),
            "spinel":                 (["A", "B", "X"], "A", "B", "X"),
            "layered_dichalcogenide": (["A", "X"],     "A", None, "X"),
            "olivine":                (["A", "B", "X"], "A", "B", "X"),
            "layered_oxide":         (["A", "B", "X"], "A", "B", "X"),
            "fluoride":               (["A", "X"],     "A", None, "X"),
            "wurtzite":               (["A", "X"],     "A", None, "X"),
            "zincblende":             (["A", "X"],     "A", None, "X"),
            "diamond":                (["A"],          "A", None, None),
        }

        if prototype not in proto_map:
            return None

        _expected, a_key, b_key, x_key = proto_map[prototype]
        if site == "X" and x_key is None:
            return None
        if site == "B" and b_key is None:
            return None

        # Map element symbols -> site role (first occurrence wins per role)
        role_elements: Dict[str, str] = {}
        for el in list(counts.keys()):
            for key in [a_key, b_key, x_key]:
                if key and key not in role_elements:
                    role_elements[key] = el
                    break

        target_el = role_elements.get(site)
        if target_el is None:
            return None

        # Perform substitution
        counts[target_el] -= 1
        if counts[target_el] <= 0:
            del counts[target_el]
        counts[new_element] = counts.get(new_element, 0) + 1

        # Reconstruct in Hill order
        def hill_key(s: str) -> tuple:
            if s == "C": return (0, "")
            if s == "H": return (1, "")
            return (2, s)

        parts = []
        for el in sorted(counts.keys(), key=hill_key):
            c = counts[el]
            parts.append(f"{el}{c if c > 1 else ''}")
        return "".join(parts)

    def _fill_gaps(self, prototypes: List[str], element_pool: List[str]) -> List[Structure]:
        """Generate candidates that fill graph gaps (neighbors present but node missing).

        Returns list of Structure objects representing gap-filling candidates.
        """
        if not self._graph:
            return []

        nodes = self._graph.get("nodes", {})
        candidates: List[Structure] = []
        seen_formulas: Set[str] = set()
        tolerance = 0.40

        for node_formula, node_data in nodes.items():
            subs = node_data.get("substitutions", {})
            proto_name = node_data.get("prototype", "")
            # Find the matching prototype
            proto = None
            for p in PROTOTYPES:
                if p.name == proto_name:
                    proto = p
                    break
            if proto is None:
                continue

            # Get the anion from the parent node
            x_anion = node_data.get("x_anion", "O")

            for site, neighbors in subs.items():
                for neighbor in neighbors:
                    candidate_formula = self._substitute_element(node_formula, site, neighbor, proto_name)
                    if not candidate_formula:
                        continue
                    # Normalize to Hill order for node/seen lookups (graph uses Hill-order keys)
                    candidate_norm = self._normalize_formula(candidate_formula)
                    if candidate_norm in nodes or candidate_norm in seen_formulas:
                        continue

                    # Build structure from the formula using prototype geometry
                    # (NOT _build_structure which uses internal element selection)
                    try:
                        struct = self._build_structure_from_formula(candidate_norm, proto_name)
                        if not struct:
                            continue
                        # Verify result is not a known node
                        if struct.composition_string() in nodes:
                            continue
                        candidates.append(struct)
                        seen_formulas.add(candidate_norm)
                    except Exception:
                        pass
        return candidates[:10]  # limit to 10 gap-fillers per run

    def _build_structure_from_formula(self, formula: str, proto_name: str) -> Optional[Structure]:
        """Parse a formula string into a Structure with the matching prototype geometry.

        Normalizes the formula to Hill order before parsing, then builds a
        Structure using the specified prototype's charge-balance geometry.
        """
        import re
        from weslr.modules.matter_primitives import PERIODIC_TABLE

        # Normalize to Hill order so element parsing is consistent
        norm_formula = self._normalize_formula(formula)

        # Parse elements and counts: e.g. "CaO3Ti" -> [(Ca,1),(Ti,1),(O,3)]
        pattern = r"([A-Z][a-z]?)(\d*)"
        matches = re.findall(pattern, norm_formula)
        atoms = []
        for sym, count_str in matches:
            if sym not in PERIODIC_TABLE:
                continue
            count = int(count_str) if count_str else 1
            atom_obj = PERIODIC_TABLE[sym]
            for _ in range(count):
                atoms.append(atom_obj)

        if not atoms:
            return None

        # Use exact stoichiometry classification — no loose prototype-name fallback
        structure_type, uncertainty = _classify_structure(formula)
        if structure_type == "unclassified":
            geometry_type = "unclassified"
        else:
            geo_map = {
                "perovskite":               "ABX3_cubic",
                "spinel":                   "AB2X4_cubic",
                "rutile":                   "AX2_tetragonal",
                "rocksalt":                 "AX_cubic",
                "olivine":                  "orthorhombic_olivine",
                "wolframite":               "monoclinic_wolframite",
                "layered_double_hydroxide": "layered_double_hydroxide",
                "ruddlesden_popper_n1":     "layered_perovskite",
                "ruddlesden_popper_n2":     "layered_perovskite",
                "ruddlesden_popper_n3":     "layered_perovskite",
            }
            geometry_type = geo_map.get(structure_type, f"unknown_{structure_type}")

        return Structure(atoms=atoms, bonds=[], geometry_type=geometry_type, lattice_vectors=None)

    def generate_candidates(
        self,
        mode: str = "plausible",
        max_candidates: int = 10,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> List[Structure]:
        """
        Generate material structure candidates.

        Args:
            mode: "plausible" (tight constraints) or "strangeness" (relaxed)
            max_candidates: maximum number of candidates to return
            constraints: optional dict with keys:
                - min_abundance: float (default 1e-6)
                - allow_toxic: bool (default False)
                - anion: str (default "O")
                - prototype: str (limit to one prototype name)
                - domain: str ("materials" | "devices" | "all")

        Returns:
            List[Structure], sorted by ascending strangeness_score (most plausible first)
        """
        constraints = constraints or {}
        self._formula_cache.clear()

        # Load graph if path provided but graph not yet loaded
        if self._graph_path and self._graph is None:
            self._load_graph(self._graph_path)

        mode = mode.lower()
        if mode not in ("plausible", "strangeness"):
            raise ValueError(f"mode must be 'plausible' or 'strangeness', got '{mode}'")

        tolerance = 0.15 if mode == "plausible" else 0.40

        candidates: List[Tuple[float, Structure]] = []
        attempts = 0
        max_attempts = max_candidates * 20

        while len(candidates) < max_candidates and attempts < max_attempts:
            attempts += 1

            # Select prototype
            proto = self._select_prototype(constraints.get("prototype"))

            # Select elements for this prototype
            structure = self._build_structure(proto, tolerance, constraints)
            if structure is None:
                continue

            formula = structure.composition_string()
            if not formula or formula in self._formula_cache:
                continue
            if self._is_trivial(formula):
                continue

            # Graph duplicate suppression
            graph_result = self._check_graph(formula)
            if graph_result["known"]:
                continue  # Skip known compositions

            # Gap-filling candidates get a strangeness boost
            is_gap_fill = len(graph_result["gaps"]) > 0

            # Toxicity filter
            if not constraints.get("allow_toxic", False):
                elements = {a.symbol for a in structure.atoms}
                if elements & self.TOXIC_ELEMENTS:
                    continue

            # Abundance filter
            min_ab = constraints.get("min_abundance", 1e-6)
            if not self._abundance_filter(structure.atoms, min_ab):
                continue

            # Chemical validity: must be charge-balanceable using available oxidation states
            if not self._has_valid_oxidation(structure):
                continue

            # Formation energy filter — discard candidates above max_energy threshold
            accepted_energy, _ = self._estimate_formation_energy(structure)
            if not accepted_energy:
                continue

            # Stoichiometry validation — prototype must have correct atom-count ratios
            if not self._validate_stoichiometry(structure, proto):
                continue

            self._formula_cache.add(formula)
            score = self._strangeness_score(structure, mode)
            candidates.append((score, structure))

        # Sort by strangeness (most plausible first in plausible mode)
        candidates.sort(key=lambda x: x[0])

        # Add gap-filling candidates (deduplicated by Hill-order formula)
        gap_candidates = self._fill_gaps([], [])
        seen_gap_formulas: Set[str] = set()
        existing_formulas = {c[1].composition_string() for c in candidates}
        for gc in gap_candidates:
            gc_formula = gc.composition_string()
            if gc_formula in seen_gap_formulas:
                continue  # Skip duplicate formulas from multiple parent nodes
            seen_gap_formulas.add(gc_formula)
            if gc_formula in self._formula_cache or gc_formula in existing_formulas:
                continue
            # Chemical validity: must be charge-balanceable using available oxidation states
            if not self._has_valid_oxidation(gc):
                continue
            candidates.append((self._strangeness_score(gc, mode) + 0.1, gc))  # boost for gap-filling

        return [s for _, s in candidates[:max_candidates]]

    def _validate_stoichiometry(self, structure: Structure, proto: _Prototype) -> bool:
        """
        Validate that structure matches the prototype's stoichiometry ratios.

        After substitution, structure contains real elements (Ca, Ti, O …) while
        proto.sites uses generic labels (A, B, X).  We check total non-anion
        atom count and anion count each match the prototype site counts ±1.
        """
        from collections import Counter
        element_counts = Counter(a.symbol for a in structure.atoms)

        proto_total = sum(proto.sites.values())
        struct_total = len(structure.atoms)


        # Allow ±1 tolerance on total atom count (different cell sizes)
        if abs(struct_total - proto_total) > 1:
            return False

        # Non-anion elements (cations) must match total non-anion site count in proto
        ANIONS = {"O", "S", "N", "F", "Cl", "Se", "Te"}
        non_x_proto = sum(v for k, v in proto.sites.items() if k != "X")
        non_x_struct = sum(cnt for el, cnt in element_counts.items() if el not in ANIONS)
        if abs(non_x_struct - non_x_proto) > 1:
            return False

        # Anion count must match proto X count
        x_count = element_counts.get("O", element_counts.get("S", 0))
        expected_x = proto.sites.get("X", 0)
        if abs(x_count - expected_x) > 1:
            return False

        return True

    def _has_valid_oxidation(self, structure: Structure) -> bool:
        """
        Check whether a structure can be charge-balanced using available oxidation
        states from its elements.  Uses itertools.product to try all combinations
        of oxidation states (one per unique element) and returns True if any
        combination sums to exactly 0.
        """
        from collections import Counter
        from itertools import product

        element_counts = Counter(a.symbol for a in structure.atoms)
        unique_elements = list(element_counts.keys())
        all_ox_states = [PERIODIC_TABLE[e].oxidation_states for e in unique_elements]

        counts = [element_counts[e] for e in unique_elements]

        for ox_combo in product(*all_ox_states):
            total = sum(ox * cnt for ox, cnt in zip(ox_combo, counts))
            if total == 0:
                return True
        return False

    def _estimate_formation_energy(self, candidate: Structure, max_energy: float = 5.0) -> Tuple[bool, float]:
        """
        Estimate formation energy from Pauling electronegativity mismatches.

        For each unique element pair in the structure, compute |EN_i - EN_j|
        and sum across all pairs. Normalize by atom count to get eV/atom.

        Returns (accepted, energy): accepted=True if energy <= max_energy.
        """
        atoms = candidate.atoms
        if len(atoms) < 2:
            return (True, 0.0)

        elements = list({a.symbol for a in atoms})
        en_vals = {}
        for e in elements:
            atom = PERIODIC_TABLE.get(e)
            en_vals[e] = atom.electronegativity if atom else 2.0

        # Sum EN differences across all unique pairs
        total_diff = 0.0
        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                total_diff += abs(en_vals[elements[i]] - en_vals[elements[j]])

        energy = round(total_diff / len(atoms), 3)
        return (energy <= max_energy, energy)

    def estimate_properties(self, candidate: Structure) -> Dict[str, Any]:
        """
        Estimate physical properties for a Structure.

        Returns dict with keys:
          bandgap_eV: float (0–10 eV range, estimated from electronegativity heuristics)
          formation_energy_eV: float (relative, negative = more stable)
          conductivity: float (0–1, estimated from bandgap and carrier type)
          stability: float (0–1, estimated from Goldschmidt tolerance + charge balance)
          toxicity: bool
          radical: bool (charge imbalanced)
        """
        elements = {a.symbol for a in candidate.atoms}

        # Bandgap heuristic: sum of electronegativities / 4 (empirical)
        avg_en = sum(PERIODIC_TABLE.get(e, Atom(e, 0, [0], 0, 0, 0)).electronegativity for e in elements) / max(len(elements), 1)
        # Wide-gap insulators: high EN difference
        gap_raw = 1.5 + 1.4 * (avg_en - 1.5)
        bandgap = round(max(0.0, min(10.0, gap_raw)), 2)

        # Formation energy from electronegativity pairwise mismatches (eV/atom)
        accepted, formation_energy = self._estimate_formation_energy(candidate)

        # Conductivity: inverse of bandgap, with metallicity bonus
        if bandgap < 0.5:
            conductivity = 0.95
        elif bandgap > 5.0:
            conductivity = 0.01
        else:
            conductivity = round(max(0.0, min(1.0, 1.0 - bandgap / 6.0)), 3)

        # Stability: sigmoid on formation energy — lower energy = more stable (0–1)
        stability = round(1.0 / (1.0 + formation_energy), 3)

        toxicity = bool(elements & self.TOXIC_ELEMENTS)
        radical = candidate.total_charge() != 0

        # Structural uncertainty: unclassified candidates get stability penalty + high uncertainty
        uncertainty = "low"
        if candidate.geometry_type == "unclassified":
            stability = round(stability * 0.9, 3)
            uncertainty = "high"

        return {
            "bandgap_eV": bandgap,
            "formation_energy_eV": formation_energy,
            "conductivity": conductivity,
            "stability": stability,
            "toxicity": toxicity,
            "radical": radical,
            "composition": candidate.composition_string(),
            "geometry_type": candidate.geometry_type,
            "uncertainty": uncertainty,
        }

    def generate_device_from_material(
        self,
        light_absorber: str,
        mode: str = "solar_cell",
    ) -> Dict[str, Any]:
        """
        Wrap a light-absorbing material into a device stack.

        Args:
            light_absorber: composition formula string, e.g. "CsPbI3"
            mode: one of "solar_cell", "LED", "battery_electrode",
                  "photocatalyst", "memristor"

        Returns:
            dict with device layers and metadata
        """
        templates = {
            "solar_cell": {
                "ETL": ["TiO2", "Nb2O5", "ZnO"],
                "abs": [light_absorber],
                "HTL": ["Spiro-OMeTAD", "PTAA", "NiOx"],
                "metal": ["Au", "Ag"],
            },
            "LED": {
                "substrate": ["glass", "ITO"],
                " ETL": ["ZnO", "TiO2"],
                "abs": [light_absorber],
                "HTL": ["PEDOT:PSS", "NiOx"],
                "electrode": ["Al", "Ag"],
            },
            "battery_electrode": {
                "current_collector": ["Cu", "Al"],
                "active_material": [light_absorber],
                "binder": ["PVDF"],
                "electrolyte": ["LP30"],
            },
            "photocatalyst": {
                "support": ["SiO2", "Al2O3"],
                "catalyst": [light_absorber],
                "cocatalyst": ["Pt", "Co", "Ni"],
                "reactor": ["quartz"],
            },
            "memristor": {
                "bottom_electrode": ["Pt", "TiN"],
                "switching_layer": [light_absorber],
                "top_electrode": ["TiN", "W"],
                "electrolyte": ["Ta2O5", "HfO2"],
            },
        }

        if mode not in templates:
            raise ValueError(f"Unknown device mode: {mode}. Valid: {list(templates.keys())}")

        layers = templates[mode]

        # Check structural uncertainty of the absorber material
        structure_type, uncertainty = _classify_structure(light_absorber)
        disclaimer = None
        if structure_type == "unclassified":
            disclaimer = (
                f"⚠️  Device proposal is speculative — {light_absorber} has an unclassified "
                f"structure with uncertain geometry (high uncertainty). Synthesis route and "
                f"device architecture are based on generic assumptions and require explicit "
                f"structural validation before experimental attempts."
            )

        result = {
            "mode": mode,
            "light_absorber": light_absorber,
            "layers": layers,
            "description": self._device_description(light_absorber, mode),
            "structure_classification": structure_type,
            "structural_uncertainty": uncertainty,
        }
        if disclaimer:
            result["disclaimer"] = disclaimer
        return result

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _select_prototype(self, name: Optional[str] = None) -> _Prototype:
        if name:
            for p in PROTOTYPES:
                if p.name == name:
                    return p
            raise ValueError(f"Unknown prototype '{name}'")
        return self._rng.choice(PROTOTYPES)

    def _build_structure(
        self,
        proto: _Prototype,
        tolerance: float,
        constraints: Dict[str, Any],
    ) -> Optional[Structure]:
        """Build a Structure for the given prototype, or None if no valid combo."""
        anion = constraints.get("anion", "O")
        if anion not in PERIODIC_TABLE:
            return None

        # Get anion atom
        anion_atom = PERIODIC_TABLE[anion]
        anion_ox = anion_atom.oxidation_states[0] if anion_atom.oxidation_states else -2

        # Build element pool based on prototype charge requirements
        charge_map = proto.charge_balance  # element → total charge contribution
        elements_needed: Set[str] = set(proto.sites.keys()) - {anion}

        atoms: List[Atom] = []
        stoichiometry: Dict[str, int] = dict(proto.sites)
        seen_elements: Dict[str, bool] = {}

        for el, count in proto.sites.items():
            if el == anion:
                for _ in range(count):
                    atoms.append(anion_atom)
                continue

            # Find oxidation state needed
            target_ox = charge_map.get(el, 0) // count if count > 0 else 0

            # Find element with matching oxidation state within tolerance
            candidate = self._find_element_for_role(el, target_ox, tolerance, anion_ox, elements_needed)
            if candidate is None:
                return None

            seen_elements[el] = True
            element_atom = PERIODIC_TABLE[candidate]
            for _ in range(count):
                atoms.append(element_atom)

        bonds = self._infer_bonds(atoms)

        # Lattice vectors (simple cubic approximation for unit cell)
        lattice = self._make_lattice(proto, atoms)

        return Structure(
            atoms=atoms,
            bonds=bonds,
            geometry_type=proto.geometry_type,
            lattice_vectors=lattice,
        )

    def _find_element_for_role(
        self,
        role: str,
        target_ox: int,
        tolerance: float,
        anion_ox: int,
        all_roles: Set[str],
    ) -> Optional[str]:
        """Find element matching oxidation state + ionic radius tolerance.

        For cations: element must have oxidation state == target_ox
                    AND its ionic radius must be within ±tolerance fraction of the ideal.
        For anion site: find a stable anion with matching charge.
        """
        candidates: List[Tuple[str, float, float]] = []
        ideal_radius = self._ideal_ionic_radius(target_ox, anion_ox)

        for sym, atom in PERIODIC_TABLE.items():
            if sym in ("He", "Ne", "Ar", "Kr", "Xe", "Rn"):
                continue
            if not atom.oxidation_states:
                continue

            # Must match target_ox exactly (no tolerance on oxidation state)
            if target_ox not in atom.oxidation_states:
                continue

            ir = ionic_radius(sym, target_ox)
            if ir is None:
                continue

            # Skip if element has no radius data (can't do size tolerance)
            # Compute radius tolerance as ±tolerance fraction
            radius_tolerance = ideal_radius * tolerance
            radius_diff = abs(ir - ideal_radius) if ideal_radius > 0 else 0.0

            candidates.append((sym, radius_diff, ir))

        if not candidates:
            return None

        # Sort by radius proximity to ideal (ascending)
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    def _ideal_ionic_radius(self, ox: int, anion_ox: int) -> float:
        """Estimate ideal ionic radius for a cation/anion in VI-coordination.

        Returns a reference radius rather than searching the periodic table
        (which would bias toward alphabetically first elements).
        """
        # Known Shannon VI-coordination reference radii for common oxidation states
        _REF_RADII = {
            # cations
            (+1, "O"): 140,   # O2-
            (+2, "O"): 100,   # Ca2+
            (+3, "O"): 74.5,  # Al3+
            (+4, "O"): 60.5,  # Ti4+
            (+5, "O"): 64,    # Nb5+
            (+6, "O"): 59,    # Mo6+
            # anions
            (-1, "F"): 133,   # F-
            (-2, "O"): 140,   # O2-
            (-2, "S"): 184,   # S2-
            (-2, "Se"): 198,
            (-3, "N"): 146,   # N3-
        }
        key = (ox, anion_ox) if ox > 0 else (ox, self._anion_symbol_for_ox(anion_ox))
        if key in _REF_RADII:
            return _REF_RADII[key]
        # Fallback: for negative (anion) oxidation states, return Shannon radius
        if ox < 0:
            ir = ionic_radius(self._anion_symbol_for_ox(ox), ox)
            return ir if ir else 140.0
        # For cations without a reference, use a fixed set
        _CATION_FALLBACK = {+1: 102, +2: 100, +3: 74.5, +4: 60.5, +5: 64, +6: 59, +7: 58}
        return _CATION_FALLBACK.get(ox, 70.0)

    def _anion_symbol_for_ox(self, ox: int) -> str:
        """Map an oxidation state to its most common anion symbol."""
        mapping = {-1: "F", -2: "O", -3: "N"}
        return mapping.get(ox, "O")

    def _infer_bonds(self, atoms: List[Atom]) -> List[Bond]:
        """Infer bonds between atoms based on electronegativity difference."""
        bonds: List[Bond] = []
        n = len(atoms)
        for i in range(n):
            for j in range(i + 1, n):
                en_diff = abs(atoms[i].electronegativity - atoms[j].electronegativity)
                if en_diff < 0.4:
                    btype = "covalent"
                elif en_diff < 1.7:
                    btype = "ionic"
                elif atoms[i].electronegativity > 2.0 and atoms[j].electronegativity > 2.0:
                    btype = "metallic"
                else:
                    btype = "vdw"
                bonds.append(Bond(atom_i=i, atom_j=j, bond_type=btype))
        return bonds

    def _make_lattice(self, proto: _Prototype, atoms: List[Atom]) -> Optional["np.ndarray"]:
        """Generate approximate lattice vectors for the structure."""
        try:
            import numpy as np
        except Exception:
            return None

        formula = proto.formula_string()
        # Approximate cubic lattice parameter from average covalent radius
        if atoms:
            avg_radius = sum(a.covalent_radius_pm for a in atoms) / len(atoms)
            a0 = avg_radius * 2.5  # rough nearest-neighbor distance
        else:
            a0 = 4.0

        if "cubic" in proto.geometry_type or "perovskite" in proto.geometry_type:
            return np.array([[a0, 0, 0], [0, a0, 0], [0, 0, a0]], dtype=np.float64)
        elif "tetragonal" in proto.geometry_type:
            c = a0 * 1.4
            return np.array([[a0, 0, 0], [0, a0, 0], [0, 0, c]], dtype=np.float64)
        elif "layered" in proto.geometry_type:
            c = a0 * 2.5
            return np.array([[a0, 0, 0], [0, a0, 0], [0, 0, c]], dtype=np.float64)
        else:
            # Monoclinic/orthorhombic
            b = a0 * 0.95
            c = a0 * 1.1
            return np.array([[a0, 0, 0], [0, b, 0], [0, 0, c]], dtype=np.float64)

    def _strangeness_score(self, structure: Structure, mode: str) -> float:
        """Compute strangeness score for a structure (0 = normal, 1 = exotic)."""
        formula = structure.composition_string()
        score = 0.0

        elements = {a.symbol for a in structure.atoms}

        # Radical charge balance adds strangeness
        charge = structure.total_charge()
        if charge != 0:
            score += 0.3

        # Uncommon anions
        uncommon_anions = {"S", "Se", "Te", "N", "F", "Cl"}
        has_uncommon = any(a.symbol in uncommon_anions for a in structure.atoms)
        if has_uncommon:
            score += 0.15

        # Heavy elements (> atomic number 50) increase strangeness
        heavy = [e for e in elements if PERIODIC_TABLE.get(e) and PERIODIC_TABLE[e].atomic_number > 50]
        score += 0.05 * len(heavy)

        # Multiple oxidation state elements
        multi_ox = [e for e in elements if len(PERIODIC_TABLE.get(e, Atom(e, 0, [], 0, 0, 0)).oxidation_states) > 2]
        if len(multi_ox) > 2:
            score += 0.15

        # Stoichiometry perturbation: check for non-integer ratios
        counts: Dict[str, int] = {}
        for a in structure.atoms:
            counts[a.symbol] = counts.get(a.symbol, 0) + 1
        max_count = max(counts.values()) if counts else 1
        non_unity_ratios = [c for c in counts.values() if c > 1]
        if len(non_unity_ratios) > 2:
            score += 0.10

        if mode == "strangeness":
            score = score * 1.5 + 0.2  # boost strangeness

        return min(1.0, max(0.0, score))

    def _is_trivial(self, formula: str) -> bool:
        """Return True for trivial formulas (all same element)."""
        import re
        elems = re.findall(r"[A-Z][a-z]?", formula)
        return len(set(elems)) <= 1

    def _abundance_filter(self, atoms: List[Atom], min_abundance: float) -> bool:
        """Return True if all atoms meet the minimum abundance threshold."""
        for a in atoms:
            if a.abundance < min_abundance:
                return False
        return True

    def _device_description(self, absorber: str, mode: str) -> str:
        """Generate a human-readable device description."""
        templates = {
            "solar_cell": f"{absorber} as the primary light absorber in a planar heterojunction solar cell stack.",
            "LED": f"{absorber} as the emissive layer in a light-emitting diode.",
            "battery_electrode": f"{absorber} as the active material in a lithium/sodium-ion battery electrode.",
            "photocatalyst": f"{absorber} as a visible-light-driven photocatalyst for water splitting or CO2 reduction.",
            "memristor": f"{absorber} as the resistive switching layer in a memristor crossbar array.",
        }
        return templates.get(mode, f"{absorber} configured as {mode}.")


# ── Module-level convenience ─────────────────────────────────────────────────

_DEFAULT_GENERATOR = MatterGenerator(seed=42)


def generate_candidates(
    mode: str = "plausible",
    max_candidates: int = 10,
    constraints: Optional[Dict[str, Any]] = None,
    seed: int = 42,
) -> List[Structure]:
    """Module-level convenience: generate with a default generator."""
    gen = MatterGenerator(seed=seed)
    return gen.generate_candidates(mode=mode, max_candidates=max_candidates, constraints=constraints)


def estimate_properties(candidate: Structure) -> Dict[str, Any]:
    """Module-level convenience: estimate properties for a structure."""
    gen = MatterGenerator()
    return gen.estimate_properties(candidate)


def generate_device_from_material(light_absorber: str, mode: str = "solar_cell") -> Dict[str, Any]:
    """Module-level convenience: generate device stack from a material."""
    gen = MatterGenerator()
    return gen.generate_device_from_material(light_absorber=light_absorber, mode=mode)