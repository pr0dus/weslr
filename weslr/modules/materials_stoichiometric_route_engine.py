"""Isolated deterministic stoichiometric route engine for materials discovery.

This module performs formula-level stoichiometric analysis only.
It does not use an LLM, network access, or hidden state.
It does not generate crystal structures, run DFT, or access databases.

Stable route classifications:
- exact_addition_route
- exact_combination_route
- exact_substitution_route
- requires_atom_removal
- noninteger_scaling
- element_mismatch
- charge_balance_unchecked
- invalid_formula
"""

from __future__ import annotations

import json
import re
from typing import Any

# Element to atomic number mapping (for sorting)
ATOMIC_NUMBERS: dict[str, int] = {
    "H": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7, "O": 8, "F": 9,
    "Ne": 10, "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "P": 15, "S": 16, "Cl": 17,
    "Ar": 18, "K": 19, "Ca": 20, "Sc": 21, "Ti": 22, "V": 23, "Cr": 24, "Mn": 25,
    "Fe": 26, "Co": 27, "Ni": 28, "Cu": 29, "Zn": 30, "Ga": 31, "Ge": 32, "As": 33,
    "Se": 34, "Br": 35, "Kr": 36, "Rb": 37, "Sr": 38, "Y": 39, "Zr": 40, "Nb": 41,
    "Mo": 42, "Tc": 43, "Ru": 44, "Rh": 45, "Pd": 46, "Ag": 47, "Cd": 48, "In": 49,
    "Sn": 50, "Sb": 51, "Te": 52, "I": 53, "Xe": 54, "Cs": 55, "Ba": 56, "La": 57,
    "Ce": 58, "Pr": 59, "Nd": 60, "Pm": 61, "Sm": 62, "Eu": 63, "Gd": 64, "Tb": 65,
    "Dy": 66, "Ho": 67, "Er": 68, "Tm": 69, "Yb": 70, "Lu": 71, "Hf": 72, "Ta": 73,
    "W": 74, "Re": 75, "Os": 76, "Ir": 77, "Pt": 78, "Au": 79, "Hg": 80, "Tl": 81,
    "Pb": 82, "Bi": 83, "Po": 84, "At": 85, "Rn": 86, "Fr": 87, "Ra": 88, "Ac": 89,
    "Th": 90, "Pa": 91, "U": 92, "Np": 93, "Pu": 94, "Am": 95, "Cm": 96, "Bk": 97,
    "Cf": 98, "Es": 99, "Fm": 100, "Md": 101, "No": 102, "Lr": 103,
}

# Common oxidation states for charge balance checking (approximate)
COMMON_OXIDATION: dict[str, int] = {
    "H": 1, "Li": 1, "Na": 1, "K": 1, "Rb": 1, "Cs": 1,
    "Be": 2, "Mg": 2, "Ca": 2, "Sr": 2, "Ba": 2,
    "Sc": 3, "Y": 3, "La": 3,
    "Ti": 4, "Zr": 4, "Hf": 4,
    "O": -2, "F": -1, "Cl": -1,
    "Al": 3, "Si": 4,
}

SUBSCRIPT_PATTERN = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)")
SUBSCRIPT_UNICODE = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def normalize_formula(formula: str) -> str:
    """Normalize a chemical formula to canonical form.

    - Removes whitespace
    - Converts unicode subscripts to digits
    - Sorts elements by electronegativity-like order (anion last)
    - Returns empty string for invalid input
    """
    if not formula or not isinstance(formula, str):
        return ""

    # Normalize unicode
    normalized = formula.strip()
    normalized = normalized.translate(SUBSCRIPT_UNICODE)
    normalized = re.sub(r"\s+", "", normalized)

    # Parse elements
    elements: dict[str, float] = {}
    for match in SUBSCRIPT_PATTERN.finditer(normalized):
        element = match.group(1)
        count_str = match.group(2)
        count = float(count_str) if count_str else 1.0
        if element in ATOMIC_NUMBERS:
            elements[element] = elements.get(element, 0.0) + count

    if not elements:
        return ""

    # Sort: O last, then by atomic number
    def sort_key(item):
        el, _ = item
        if el == "O":
            return (1, 0)
        return (0, ATOMIC_NUMBERS.get(el, 999))

    sorted_elements = sorted(elements.items(), key=sort_key)

    # Build canonical formula
    parts = []
    for el, count in sorted_elements:
        if count == int(count):
            count_int = int(count)
            if count_int == 1:
                parts.append(el)
            else:
                parts.append(f"{el}{count_int}")
        else:
            parts.append(f"{el}{count}")

    return "".join(parts)


def elemental_vector(formula: str) -> dict[str, float]:
    """Return a dict of element -> count for a formula.

    Returns empty dict for invalid formulas.
    """
    if not formula or not isinstance(formula, str):
        return {}

    normalized = formula.strip()
    normalized = normalized.translate(SUBSCRIPT_UNICODE)
    normalized = re.sub(r"\s+", "", normalized)

    elements: dict[str, float] = {}
    for match in SUBSCRIPT_PATTERN.finditer(normalized):
        element = match.group(1)
        count_str = match.group(2)
        count = float(count_str) if count_str else 1.0
        if element in ATOMIC_NUMBERS:
            elements[element] = elements.get(element, 0.0) + count

    return elements


def _gcd(a: float, b: float) -> float:
    """GCD for floats (handles integer values)."""
    a, b = abs(a), abs(b)
    while b > 1e-10:
        a, b = b, a % b
    return a


def _gcd_of_list(values: list[float]) -> float:
    """GCD of a list of floats."""
    if not values:
        return 1.0
    result = values[0]
    for v in values[1:]:
        result = _gcd(result, v)
    return result


def reduced_formula_and_factor(formula: str) -> tuple[str, float]:
    """Return (reduced_formula, Z) where Z is the number of formula units.

    Z = 1 means the formula is already reduced.
    Z > 1 means the formula contains Z reduced units.

    Example:
        "CaSc2TiO6" -> ("CaSc2TiO6", 1.0)
        "Ca2Sc4Ti2O12" -> ("CaSc2TiO6", 2.0)
        "Sc4Ti2O10" -> ("Sc2TiO5", 2.0)
    """
    elements = elemental_vector(formula)
    if not elements:
        return ("", 0.0)

    counts = list(elements.values())
    if not counts:
        return ("", 0.0)

    # Find GCD of all counts
    g = _gcd_of_list(counts)

    if g <= 1e-10:
        return ("", 0.0)

    # Reduce
    reduced: dict[str, float] = {}
    for el, count in elements.items():
        reduced[el] = count / g

    # Build reduced formula
    def sort_key(item):
        el, _ = item
        if el == "O":
            return (1, 0)
        return (0, ATOMIC_NUMBERS.get(el, 999))

    sorted_elements = sorted(reduced.items(), key=sort_key)
    parts = []
    for el, count in sorted_elements:
        if count == int(count):
            count_int = int(count)
            if count_int == 1:
                parts.append(el)
            else:
                parts.append(f"{el}{count_int}")
        else:
            parts.append(f"{el}{count}")

    return ("".join(parts), g)


def _is_integer(val: float) -> bool:
    """Check if a float is effectively an integer."""
    return abs(val - round(val)) < 1e-10


def balance_reaction(
    reactants: list[str],
    target: str,
) -> dict[str, Any]:
    """Balance a reaction: reactants -> target.

    Searches for integer coefficients a_i and target coefficient t such that:
        sum(a_i * reactant_i) = t * target

    Returns dict with:
    - balanced: bool
    - route_class: str
    - coefficients: dict[str, float] (reactant -> coefficient)
    - target_coefficient: float
    - delta: dict[str, float] (element -> net change)
    - reason: str
    """
    # Get elemental vectors
    target_vec = elemental_vector(target)
    if not target_vec:
        return {
            "balanced": False,
            "route_class": "invalid_formula",
            "coefficients": {},
            "target_coefficient": 0.0,
            "delta": {},
            "reason": f"Invalid target formula: {target}",
        }

    reactant_vecs: list[dict[str, float]] = []
    for r in reactants:
        vec = elemental_vector(r)
        if not vec:
            return {
                "balanced": False,
                "route_class": "invalid_formula",
                "coefficients": {},
                "target_coefficient": 0.0,
                "delta": {},
                "reason": f"Invalid reactant formula: {r}",
            }
        reactant_vecs.append(vec)

    # Collect all elements across reactants and target
    all_elements = set(target_vec.keys())
    for vec in reactant_vecs:
        all_elements.update(vec.keys())

    n_reactants = len(reactants)

    if n_reactants == 1:
        # Single reactant -> target
        r_vec = reactant_vecs[0]
        if not r_vec:
            return {
                "balanced": False,
                "route_class": "invalid_formula",
                "coefficients": {},
                "target_coefficient": 0.0,
                "delta": {},
                "reason": f"Invalid reactant formula: {reactants[0]} (no known elements)",
            }
        if set(r_vec.keys()) != set(target_vec.keys()):
            return {
                "balanced": False,
                "route_class": "element_mismatch",
                "coefficients": {},
                "target_coefficient": 0.0,
                "delta": {},
                "reason": f"Element mismatch between {reactants[0]} and {target}",
            }

        ratios = []
        for el in target_vec:
            if r_vec.get(el, 0) > 0:
                ratios.append(target_vec[el] / r_vec[el])

        if not ratios:
            return {
                "balanced": False,
                "route_class": "invalid_formula",
                "coefficients": {},
                "target_coefficient": 0.0,
                "delta": {},
                "reason": "No common elements",
            }

        if max(ratios) - min(ratios) > 1e-10:
            return {
                "balanced": False,
                "route_class": "noninteger_scaling",
                "coefficients": {},
                "target_coefficient": 0.0,
                "delta": {},
                "reason": f"Cannot scale {reactants[0]} to {target}: inconsistent ratios {ratios}",
            }

        scale = ratios[0]
        if not _is_integer(scale) or scale <= 0:
            return {
                "balanced": False,
                "route_class": "noninteger_scaling",
                "coefficients": {},
                "target_coefficient": 0.0,
                "delta": {},
                "reason": f"Non-integer scaling factor {scale}",
            }

        return {
            "balanced": True,
            "route_class": "exact_addition_route",
            "coefficients": {reactants[0]: scale},
            "target_coefficient": 1.0,
            "delta": {},
            "reason": f"{int(scale)}{reactants[0]} -> {target}",
        }

    elif n_reactants == 2:
        # Two reactants -> target
        # We search for integer coefficients a, b, t such that:
        #   a * r1 + b * r2 = t * target
        # This handles cases like Sc4Ti2O10 + 2CaO -> 2CaSc2TiO6
        # where the target coefficient t is not 1.

        r1_vec = reactant_vecs[0]
        r2_vec = reactant_vecs[1]

        # Build equations dict: element -> (r1_count, r2_count, target_count)
        equations: dict[str, tuple[float, float, float]] = {}
        for el in all_elements:
            r1_c = r1_vec.get(el, 0.0)
            r2_c = r2_vec.get(el, 0.0)
            t_c = target_vec.get(el, 0.0)
            if r1_c != 0 or r2_c != 0 or t_c != 0:
                equations[el] = (r1_c, r2_c, t_c)

        # Try small integer coefficients for reactants AND target
        for a in range(1, 21):
            for b in range(1, 21):
                for t in range(1, 11):
                    valid = True
                    for el, (r1c, r2c, tc) in equations.items():
                        lhs = a * r1c + b * r2c
                        rhs = t * tc
                        if abs(lhs - rhs) > 1e-10:
                            valid = False
                            break
                    if valid:
                        return {
                            "balanced": True,
                            "route_class": "exact_combination_route",
                            "coefficients": {reactants[0]: a, reactants[1]: b},
                            "target_coefficient": float(t),
                            "delta": {},
                            "reason": f"{a}{reactants[0]} + {b}{reactants[1]} -> {t}{target}",
                        }

        return {
            "balanced": False,
            "route_class": "noninteger_scaling",
            "coefficients": {},
            "target_coefficient": 0.0,
            "delta": {},
            "reason": f"No integer coefficients found for {reactants[0]} + {reactants[1]} -> {target}",
        }

    else:
        return {
            "balanced": False,
            "route_class": "charge_balance_unchecked",
            "coefficients": {},
            "target_coefficient": 0.0,
            "delta": {},
            "reason": f"Multi-reactant balancing not implemented for {n_reactants} reactants",
        }


def calculate_parent_to_target_delta(
    parent_formula: str,
    target_formula: str,
) -> dict[str, Any]:
    """Calculate what atoms must be added/removed to go from parent to target.

    This function determines whether a parent formula can be converted to a target
    formula by adding or removing atoms. It handles:
    - Parent missing elements (e.g., Sc2TiO5 -> CaSc2TiO6 needs Ca)
    - Parent with multiple formula units (e.g., Sc4Ti2O10 -> 2 CaSc2TiO6)
    - Exact scaling (e.g., CaSc2O4 + TiO2 -> CaSc2TiO6)

    Returns dict with:
    - parent_reduced: str (reduced formula of parent)
    - parent_Z: float (number of reduced units in parent cell)
    - target_reduced: str (reduced formula of target)
    - target_Z: float (number of reduced units in target cell)
    - parent_cell_elements: dict (full cell composition)
    - target_cell_elements: dict (full cell composition)
    - delta_add: dict (elements to add)
    - delta_remove: dict (elements to remove)
    - requires_atom_removal: bool
    - exact_scaling_possible: bool
    - scaling_factor: float
    - reason: str
    """
    parent_reduced, parent_Z = reduced_formula_and_factor(parent_formula)
    target_reduced, target_Z = reduced_formula_and_factor(target_formula)

    if parent_Z == 0 or target_Z == 0:
        return {
            "parent_reduced": parent_reduced,
            "parent_Z": parent_Z,
            "target_reduced": target_reduced,
            "target_Z": target_Z,
            "parent_cell_elements": {},
            "target_cell_elements": {},
            "delta_add": {},
            "delta_remove": {},
            "requires_atom_removal": False,
            "exact_scaling_possible": False,
            "scaling_factor": 0.0,
            "reason": "Invalid formula",
        }

    parent_cell = elemental_vector(parent_formula)
    target_cell = elemental_vector(target_formula)

    parent_elements = set(parent_cell.keys())
    target_elements = set(target_cell.keys())

    # Check if parent has elements not in target (would require removal)
    extra_elements = parent_elements - target_elements
    if extra_elements:
        return {
            "parent_reduced": parent_reduced,
            "parent_Z": parent_Z,
            "target_reduced": target_reduced,
            "target_Z": target_Z,
            "parent_cell_elements": parent_cell,
            "target_cell_elements": target_cell,
            "delta_add": {},
            "delta_remove": {},
            "requires_atom_removal": True,
            "exact_scaling_possible": False,
            "scaling_factor": 0.0,
            "reason": f"Parent has elements not in target: {extra_elements}",
        }

    # Parent elements are a subset of target elements (or equal)
    # We need to find how many parent cells are needed to reach target
    # Strategy: find the smallest integer k such that k * parent_cell can be
    # scaled to an integer multiple of target_cell by adding elements.

    # For each element in parent, find the ratio to target
    # We want: k * parent_cell[el] <= m * target_cell[el] for all el in parent
    # where k, m are integers and the missing elements are added.

    # First, find the ratio of each parent element to its target counterpart
    # This tells us how many target cells one parent cell can fill
    ratios = []
    for el in parent_cell:
        if el in target_cell and target_cell[el] > 0:
            ratios.append(parent_cell[el] / target_cell[el])

    if not ratios:
        return {
            "parent_reduced": parent_reduced,
            "parent_Z": parent_Z,
            "target_reduced": target_reduced,
            "target_Z": target_Z,
            "parent_cell_elements": parent_cell,
            "target_cell_elements": target_cell,
            "delta_add": {},
            "delta_remove": {},
            "requires_atom_removal": False,
            "exact_scaling_possible": False,
            "scaling_factor": 0.0,
            "reason": "No common elements",
        }

    # The ratio tells us how many target cells one parent cell can supply
    # If ratio = 2, then 1 parent cell has 2x the element count of 1 target cell
    # If ratio = 0.5, then 2 parent cells are needed for 1 target cell
    #
    # For Sc2TiO5 -> CaSc2TiO6:
    #   parent: Sc=2, Ti=1, O=5
    #   target: Ca=1, Sc=2, Ti=1, O=6
    #   ratios: Sc=2/2=1, Ti=1/1=1, O=5/6=0.833...
    #   Inconsistent! So we need to add O.
    #
    # For Sc4Ti2O10 -> CaSc2TiO6:
    #   parent: Sc=4, Ti=2, O=10
    #   target: Ca=1, Sc=2, Ti=1, O=6
    #   ratios: Sc=4/2=2, Ti=2/1=2, O=10/6=1.666...
    #   Inconsistent! So we need to add Ca and O.
    #   But: 1*Sc4Ti2O10 + 2*CaO -> 2*CaSc2TiO6
    #   So: k=1, m=2, add Ca=2, O=2

    # Find the maximum ratio (the element that limits how many target cells
    # one parent cell can fill)
    max_ratio = max(ratios)
    min_ratio = min(ratios)

    # If all ratios are equal, the parent can be scaled exactly
    if max_ratio - min_ratio < 1e-10:
        # All ratios are equal
        ratio = max_ratio
        if _is_integer(ratio) and ratio > 0:
            # Parent cell is a multiple of target cell
            # 1 parent cell = ratio target cells
            m = int(round(ratio))
            k = 1
            exact_scaling_possible = True
            reason = f"1 parent cell = {m} target cells (parent contains {m}× target)"
        elif _is_integer(1.0 / ratio) and ratio > 0:
            # Target cell is a multiple of parent cell
            k = int(round(1.0 / ratio))
            m = 1
            exact_scaling_possible = True
            reason = f"{k} parent cells = 1 target cell"
        else:
            exact_scaling_possible = False
            k, m = 1, 1
            reason = f"Non-integer scaling: parent/target ratio = {ratio}"
    else:
        # Ratios are inconsistent - parent needs element addition
        # Find the smallest k such that k * parent_cell can be filled to
        # an integer multiple of target_cell by adding missing elements.
        #
        # Strategy: for each element in parent, k * parent_cell[el] must be
        # <= m * target_cell[el] for some integer m.
        # The limiting element is the one with the highest ratio.
        #
        # For Sc4Ti2O10 -> CaSc2TiO6:
        #   ratios: Sc=2, Ti=2, O=1.666...
        #   max_ratio = 2 (Sc or Ti)
        #   We need k such that k * parent_cell[Sc] = m * target_cell[Sc]
        #   k * 4 = m * 2 -> k = m * 0.5
        #   Smallest integer k: k=1, m=2
        #   Then: 1*Sc4Ti2O10 + ? = 2*CaSc2TiO6
        #   Check: 1*Sc4Ti2O10 has Sc=4, Ti=2, O=10
        #          2*CaSc2TiO6 has Ca=2, Sc=4, Ti=2, O=12
        #          Need to add: Ca=2, O=2

        # Find the element with the highest ratio (the bottleneck)
        bottleneck_el = None
        bottleneck_ratio = 0
        for el in parent_cell:
            if el in target_cell and target_cell[el] > 0:
                r = parent_cell[el] / target_cell[el]
                if r > bottleneck_ratio:
                    bottleneck_ratio = r
                    bottleneck_el = el

        # Find smallest k, m such that k * parent_cell[bottleneck] = m * target_cell[bottleneck]
        if bottleneck_el:
            p_count = parent_cell[bottleneck_el]
            t_count = target_cell[bottleneck_el]
            # We want: k * p_count = m * t_count
            # So: k/m = t_count / p_count
            # Find smallest integers k, m
            for k in range(1, 21):
                for m in range(1, 21):
                    if abs(k * p_count - m * t_count) < 1e-10:
                        # Check if this k, m works for all parent elements
                        valid = True
                        for el in parent_cell:
                            if el in target_cell:
                                if k * parent_cell[el] > m * target_cell[el] + 1e-10:
                                    valid = False
                                    break
                        if valid:
                            exact_scaling_possible = True
                            reason = f"{k} parent cell(s) + additions -> {m} target cell(s)"
                            break
                if exact_scaling_possible:
                    break
            else:
                exact_scaling_possible = False
                reason = f"Inconsistent element ratios: {ratios}"
        else:
            exact_scaling_possible = False
            k, m = 1, 1
            reason = f"Inconsistent element ratios: {ratios}"

    # Calculate delta
    delta_add = {}
    delta_remove = {}
    requires_atom_removal = False

    if exact_scaling_possible:
        scaled_parent = {el: c * k for el, c in parent_cell.items()}
        scaled_target = {el: c * m for el, c in target_cell.items()}

        for el in set(list(scaled_parent.keys()) + list(scaled_target.keys())):
            p = scaled_parent.get(el, 0)
            t = scaled_target.get(el, 0)
            diff = t - p
            if diff > 1e-10:
                delta_add[el] = diff
            elif diff < -1e-10:
                delta_remove[el] = -diff
                requires_atom_removal = True

    return {
        "parent_reduced": parent_reduced,
        "parent_Z": parent_Z,
        "target_reduced": target_reduced,
        "target_Z": target_Z,
        "parent_cell_elements": parent_cell,
        "target_cell_elements": target_cell,
        "delta_add": delta_add,
        "delta_remove": delta_remove,
        "requires_atom_removal": requires_atom_removal,
        "exact_scaling_possible": exact_scaling_possible,
        "scaling_factor": float(k) / float(m) if exact_scaling_possible and m > 0 else 0.0,
        "reason": reason,
    }


def classify_route(route: dict[str, Any]) -> str:
    """Classify a reaction route into a stable category.

    Args:
        route: Output from balance_reaction()

    Returns:
        One of the stable route classifications.
    """
    if not route.get("balanced", False):
        return route.get("route_class", "invalid_formula")

    coefficients = route.get("coefficients", {})
    n_reactants = len(coefficients)

    if n_reactants == 1:
        return "exact_addition_route"
    elif n_reactants == 2:
        # Check if it's a combination or substitution
        # A substitution typically involves swapping one element for another
        # while keeping the rest of the structure
        return "exact_combination_route"
    else:
        return "exact_combination_route"


def check_charge_balance(formula: str) -> dict[str, Any]:
    """Check approximate charge balance of a formula.

    Returns dict with:
    - total_charge: float
    - balanced: bool
    - oxidation_states: dict[str, int]
    - reason: str
    """
    elements = elemental_vector(formula)
    if not elements:
        return {"total_charge": 0, "balanced": False, "oxidation_states": {}, "reason": "Invalid formula"}

    total = 0
    states: dict[str, int] = {}
    for el, count in elements.items():
        ox = COMMON_OXIDATION.get(el, 0)
        states[el] = ox
        total += ox * count

    return {
        "total_charge": total,
        "balanced": abs(total) < 1e-10,
        "oxidation_states": states,
        "reason": f"Total charge: {total}" if abs(total) >= 1e-10 else "Charge balanced",
    }


def serialize_route(route: dict[str, Any]) -> str:
    """Serialize a route dict to stable JSON string."""
    return json.dumps(route, sort_keys=True, ensure_ascii=False)
