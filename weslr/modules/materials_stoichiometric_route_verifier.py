"""Independent stoichiometric route verifier.

This module provides a materially different implementation of formula
balancing from the proposer (materials_stoichiometric_route_engine.py).

It does NOT import or call:
- balance_reaction
- calculate_parent_to_target_delta
- classify_route
from the proposer module.

Verifier approach:
1. Parse formulas independently using regex.
2. Build exact elemental vectors using integer arithmetic.
3. Verify supplied coefficients directly from residual vectors.
4. Use a separate bounded integer-search for coefficient discovery.
5. Report complete elemental residual certificates.

Three-way checks:
A. proposer result
B. independent verifier result
C. direct elemental residual invariant

A route is "verified" only if:
- proposer and verifier coefficients agree after canonical reduction, and
- every elemental residual equals exactly zero.

If any two systems disagree:
- do not choose one
- return "abstain_due_to_verification_disagreement"
"""

from __future__ import annotations

import json
import math
import re
from fractions import Fraction
from typing import Any

# Element to atomic number mapping (same data, independent implementation)
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

SUBSCRIPT_UNICODE = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
ELEMENT_PATTERN = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)")


def parse_formula_independent(formula: str) -> dict[str, Fraction]:
    """Parse a chemical formula into element -> Fraction counts.

    Uses integer arithmetic via Fraction for exact results.
    Returns empty dict for invalid formulas.
    """
    if not formula or not isinstance(formula, str):
        return {}

    normalized = formula.strip()
    normalized = normalized.translate(SUBSCRIPT_UNICODE)
    normalized = re.sub(r"\s+", "", normalized)

    elements: dict[str, Fraction] = {}
    for match in ELEMENT_PATTERN.finditer(normalized):
        element = match.group(1)
        count_str = match.group(2)
        if element not in ATOMIC_NUMBERS:
            return {}
        count = Fraction(count_str) if count_str else Fraction(1, 1)
        elements[element] = elements.get(element, Fraction(0, 1)) + count

    return elements


def elemental_vector_int(formula: str) -> dict[str, int]:
    """Return element -> integer count dict.

    Returns empty dict for invalid or non-integer formulas.
    """
    parsed = parse_formula_independent(formula)
    if not parsed:
        return {}
    result: dict[str, int] = {}
    for el, cnt in parsed.items():
        if cnt.denominator != 1:
            return {}
        result[el] = cnt.numerator
    return result


def verify_coefficients(
    reactants: list[str],
    reactant_coeffs: list[int],
    target: str,
    target_coeff: int,
) -> dict[str, Any]:
    """Verify that coefficients balance a reaction.

    Computes elemental residual = sum(reactant_coeff_i * reactant_i) - target_coeff * target.
    Returns dict with:
    - balanced: bool
    - residual: dict[str, int] (element -> residual count)
    - max_absolute_residual: int
    - total_absolute_residual: int
    - reason: str
    """
    # Parse all formulas
    reactant_vecs: list[dict[str, int]] = []
    for r in reactants:
        vec = elemental_vector_int(r)
        if not vec:
            return {
                "balanced": False,
                "residual": {},
                "max_absolute_residual": -1,
                "total_absolute_residual": -1,
                "reason": f"Invalid reactant formula: {r}",
            }
        reactant_vecs.append(vec)

    target_vec = elemental_vector_int(target)
    if not target_vec:
        return {
            "balanced": False,
            "residual": {},
            "max_absolute_residual": -1,
            "total_absolute_residual": -1,
            "reason": f"Invalid target formula: {target}",
        }

    # Collect all elements
    all_elements: set[str] = set(target_vec.keys())
    for vec in reactant_vecs:
        all_elements.update(vec.keys())

    # Compute residual
    residual: dict[str, int] = {}
    for el in all_elements:
        lhs = 0
        for i, vec in enumerate(reactant_vecs):
            lhs += reactant_coeffs[i] * vec.get(el, 0)
        rhs = target_coeff * target_vec.get(el, 0)
        residual[el] = lhs - rhs

    max_abs = max(abs(v) for v in residual.values()) if residual else 0
    total_abs = sum(abs(v) for v in residual.values()) if residual else 0
    balanced = max_abs == 0

    return {
        "balanced": balanced,
        "residual": residual,
        "max_absolute_residual": max_abs,
        "total_absolute_residual": total_abs,
        "reason": "All residuals zero" if balanced else f"Max residual: {max_abs}",
    }


def find_coefficients_independent(
    reactants: list[str],
    target: str,
    max_coeff: int = 20,
    max_target_coeff: int = 10,
) -> dict[str, Any]:
    """Find integer coefficients that balance a reaction.

    Uses a separate bounded integer-search implementation.
    Does NOT call the proposer's balance_reaction.

    Returns dict with:
    - balanced: bool
    - coefficients: dict[str, int] (reactant -> coefficient)
    - target_coefficient: int
    - residual: dict[str, int]
    - reason: str
    """
    reactant_vecs: list[dict[str, int]] = []
    for r in reactants:
        vec = elemental_vector_int(r)
        if not vec:
            return {
                "balanced": False,
                "coefficients": {},
                "target_coefficient": 0,
                "residual": {},
                "reason": f"Invalid reactant formula: {r}",
            }
        reactant_vecs.append(vec)

    target_vec = elemental_vector_int(target)
    if not target_vec:
        return {
            "balanced": False,
            "coefficients": {},
            "target_coefficient": 0,
            "residual": {},
            "reason": f"Invalid target formula: {target}",
        }

    n_reactants = len(reactants)

    if n_reactants == 1:
        # Single reactant -> target
        r_vec = reactant_vecs[0]
        if set(r_vec.keys()) != set(target_vec.keys()):
            return {
                "balanced": False,
                "coefficients": {},
                "target_coefficient": 0,
                "residual": {},
                "reason": f"Element mismatch between {reactants[0]} and {target}",
            }

        # Find scaling factor using Fraction arithmetic
        ratios = []
        for el in target_vec:
            if r_vec.get(el, 0) > 0:
                ratios.append(Fraction(target_vec[el], r_vec[el]))

        if not ratios:
            return {
                "balanced": False,
                "coefficients": {},
                "target_coefficient": 0,
                "residual": {},
                "reason": "No common elements",
            }

        if len(set(ratios)) > 1:
            return {
                "balanced": False,
                "coefficients": {},
                "target_coefficient": 0,
                "residual": {},
                "reason": f"Inconsistent ratios: {[str(r) for r in ratios]}",
            }

        scale = ratios[0]
        if scale.denominator != 1 or scale.numerator <= 0:
            return {
                "balanced": False,
                "coefficients": {},
                "target_coefficient": 0,
                "residual": {},
                "reason": f"Non-integer scaling factor {scale}",
            }

        return {
            "balanced": True,
            "coefficients": {reactants[0]: scale.numerator},
            "target_coefficient": 1,
            "residual": {el: 0 for el in target_vec},
            "reason": f"{scale.numerator}{reactants[0]} -> {target}",
        }

    elif n_reactants == 2:
        r1_vec = reactant_vecs[0]
        r2_vec = reactant_vecs[1]

        # Collect all elements
        all_elements: set[str] = set(target_vec.keys())
        all_elements.update(r1_vec.keys())
        all_elements.update(r2_vec.keys())

        # Try integer coefficients for reactants AND target
        for a in range(1, max_coeff + 1):
            for b in range(1, max_coeff + 1):
                for t in range(1, max_target_coeff + 1):
                    valid = True
                    for el in all_elements:
                        lhs = a * r1_vec.get(el, 0) + b * r2_vec.get(el, 0)
                        rhs = t * target_vec.get(el, 0)
                        if lhs != rhs:
                            valid = False
                            break
                    if valid:
                        return {
                            "balanced": True,
                            "coefficients": {reactants[0]: a, reactants[1]: b},
                            "target_coefficient": t,
                            "residual": {el: 0 for el in all_elements},
                            "reason": f"{a}{reactants[0]} + {b}{reactants[1]} -> {t}{target}",
                        }

        return {
            "balanced": False,
            "coefficients": {},
            "target_coefficient": 0,
            "residual": {},
            "reason": f"No integer coefficients found for {reactants[0]} + {reactants[1]} -> {target}",
        }

    else:
        return {
            "balanced": False,
            "coefficients": {},
            "target_coefficient": 0,
            "residual": {},
            "reason": f"Multi-reactant balancing not implemented for {n_reactants} reactants",
        }


def compute_reduced_formula_independent(formula: str) -> tuple[str, int]:
    """Compute reduced formula and Z factor independently.

    Returns (reduced_formula, Z) where Z is the number of reduced units.
    Uses integer arithmetic.
    """
    vec = elemental_vector_int(formula)
    if not vec:
        return ("", 0)

    counts = list(vec.values())
    if not counts:
        return ("", 0)

    # Find GCD of all counts
    g = counts[0]
    for c in counts[1:]:
        g = math.gcd(g, c)

    if g == 0:
        return ("", 0)

    # Build reduced formula
    reduced: dict[str, int] = {}
    for el, count in vec.items():
        reduced[el] = count // g

    def sort_key(item):
        el, _ = item
        if el == "O":
            return (1, 0)
        return (0, ATOMIC_NUMBERS.get(el, 999))

    sorted_elements = sorted(reduced.items(), key=sort_key)
    parts = []
    for el, count in sorted_elements:
        if count == 1:
            parts.append(el)
        else:
            parts.append(f"{el}{count}")

    return ("".join(parts), g)


def canonicalize_coefficients(
    coefficients: dict[str, int],
    target_coefficient: int,
) -> dict[str, Any]:
    """Reduce coefficients to canonical form by dividing by GCD.

    Returns dict with:
    - reduced_coefficients: dict[str, int]
    - reduced_target_coefficient: int
    - gcd: int
    """
    all_vals = list(coefficients.values()) + [target_coefficient]
    g = all_vals[0]
    for v in all_vals[1:]:
        g = math.gcd(g, v)

    if g <= 1:
        return {
            "reduced_coefficients": dict(coefficients),
            "reduced_target_coefficient": target_coefficient,
            "gcd": 1,
        }

    return {
        "reduced_coefficients": {k: v // g for k, v in coefficients.items()},
        "reduced_target_coefficient": target_coefficient // g,
        "gcd": g,
    }


def coefficients_agree(
    proposer_coeffs: dict[str, float],
    proposer_target: float,
    verifier_coeffs: dict[str, int],
    verifier_target: int,
) -> bool:
    """Check if proposer and verifier coefficients agree after canonical reduction.

    Both are reduced to canonical form (divide by GCD) and compared.
    """
    # Convert proposer float to int
    p_int: dict[str, int] = {}
    for k, v in proposer_coeffs.items():
        if abs(v - round(v)) > 1e-10:
            return False
        p_int[k] = int(round(v))
    p_target = int(round(proposer_target))

    # Canonicalize both
    p_canon = canonicalize_coefficients(p_int, p_target)
    v_canon = canonicalize_coefficients(verifier_coeffs, verifier_target)

    return (
        p_canon["reduced_coefficients"] == v_canon["reduced_coefficients"]
        and p_canon["reduced_target_coefficient"] == v_canon["reduced_target_coefficient"]
    )


def serialize_verifier_result(result: dict[str, Any]) -> str:
    """Serialize verifier result to stable JSON."""
    return json.dumps(result, sort_keys=True, ensure_ascii=False)
