"""
matter_primitives.py — Atomic data structures and periodic table.

Factual data sourced from IUPAC values (2024).
Only used for scientific computation; no external API calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    import numpy as np
    _NP = np
except Exception:
    _NP = None


@dataclass(frozen=True, slots=True)
class Atom:
    symbol: str
    atomic_number: int
    oxidation_states: List[int]
    electronegativity: float  # Pauling scale
    covalent_radius_pm: float  # picometers
    abundance: float  # 0–1 (relative abundance in Earth's crust / solar system)


@dataclass(frozen=True, slots=True)
class Bond:
    atom_i: int  # index into Structure.atoms
    atom_j: int  # index into Structure.atoms
    bond_type: str  # "covalent" | "ionic" | "metallic" | "vdw"


@dataclass
class Structure:
    atoms: List[Atom]
    bonds: List[Bond]
    geometry_type: str
    lattice_vectors: Optional["np.ndarray"] = None  # shape (3, 3) — only when periodic

    def composition_string(self) -> str:
        """Compact formula string like 'ABX3'."""
        counts: Dict[str, int] = {}
        for a in self.atoms:
            counts[a.symbol] = counts.get(a.symbol, 0) + 1
        # Hill order: C then H then alphabetical
        def hill_key(symbol: str) -> tuple[int, str]:
            if symbol == "C":
                return (0, "")
            if symbol == "H":
                return (1, "")
            return (2, symbol)

        symbols = sorted(counts.keys(), key=hill_key)
        parts = []
        for s in symbols:
            n = counts[s]
            parts.append(f"{s}{n if n > 1 else ''}")
        return "".join(parts)

    def total_charge(self) -> int:
        """Sum of oxidation states for the first occurrence of each element."""
        seen: Dict[str, int] = {}
        charge = 0
        for a in self.atoms:
            if a.symbol not in seen:
                seen[a.symbol] = len(seen)
            # Use the first oxidation state for each element
            ox = a.oxidation_states[0] if a.oxidation_states else 0
            charge += ox
        return charge


# ─────────────────────────────────────────────────────────────────────────────
# PERIODIC_TABLE — 60+ elements with factual IUPAC data
# Key: element symbol → Atom
# References:
#   EN: Pauling electronegativity (IUPAC 2024)
#   Radius: Covalent radius (Alvarez, CRC Handbook, 2024)
#   Abundance: Solar system / Earth's crust (IUPAC Trace Element Geochemistry)
# ─────────────────────────────────────────────────────────────────────────────

PERIODIC_TABLE: Dict[str, Atom] = {
    # Period 1
    "H":  Atom("H",   1,  [1, -1],     2.20, 31,  7.6e-4),
    "He": Atom("He",  2,  [0],          0.00, 28,  2.4e-5),
    # Period 2
    "Li": Atom("Li",  3,  [1],          0.98, 128, 1.7e-5),
    "Be": Atom("Be",  4,  [2],          1.57, 96,  1.0e-6),
    "B":  Atom("B",   5,  [3],           2.04, 84,  3.0e-6),
    "C":  Atom("C",   6,  [4, 2, -4],   2.55, 77,  3.0e-3),
    "N":  Atom("N",   7,  [5, 4, 3, 2, 1, -1, -2, -3], 3.04, 71,  9.6e-5),
    "O":  Atom("O",   8,  [-2, -1],    3.44, 66,  4.9e-3),
    "F":  Atom("F",   9,  [-1],         3.98, 64,  3.7e-5),
    "Ne": Atom("Ne", 10,  [0],          0.00, 58,  7.0e-7),
    # Period 3
    "Na": Atom("Na", 11,  [1],          0.93, 166, 2.3e-3),
    "Mg": Atom("Mg", 12,  [2],          1.31, 141, 2.3e-3),
    "Al": Atom("Al", 13,  [3],          1.61, 121, 4.3e-3),
    "Si": Atom("Si", 14,  [4, 2, -4],  1.90, 111, 2.1e-3),
    "P":  Atom("P",  15,  [5, 3, -3],  2.19, 107, 5.0e-4),
    "S":  Atom("S",  16,  [6, 4, 2, -2], 2.58, 105, 1.7e-4),
    "Cl": Atom("Cl", 17,  [-1, 1, 3, 5, 7], 3.16, 102, 1.3e-4),
    "Ar": Atom("Ar", 18,  [0],          0.00, 106, 3.5e-6),
    # Period 4
    "K":  Atom("K",  19,  [1],          0.82, 203, 1.4e-3),
    "Ca": Atom("Ca", 20,  [2],          1.00, 176, 2.3e-3),
    "Sc": Atom("Sc", 21,  [3],          1.36, 170, 1.1e-5),
    "Ti": Atom("Ti", 22,  [4, 3, 2],   1.54, 160, 2.2e-3),
    "V":  Atom("V",  23,  [5, 4, 3, 2], 1.63, 153, 7.8e-4),
    "Cr": Atom("Cr", 24,  [6, 3, 2],   1.66, 139, 4.4e-4),
    "Mn": Atom("Mn", 25,  [7, 4, 3, 2], 1.55, 161, 3.6e-4),
    "Fe": Atom("Fe", 26,  [3, 2],       1.83, 152, 2.5e-3),
    "Co": Atom("Co", 27,  [3, 2],       1.88, 126, 8.6e-5),
    "Ni": Atom("Ni", 28,  [2, 3],       1.91, 124, 2.7e-4),
    "Cu": Atom("Cu", 29,  [2, 1],       1.90, 132, 2.7e-5),
    "Zn": Atom("Zn", 30,  [2],          1.65, 122, 3.2e-5),
    "Ga": Atom("Ga", 31,  [3],          1.81, 122, 8.1e-5),
    "Ge": Atom("Ge", 32,  [4, 2],       2.01, 120, 6.6e-5),
    "As": Atom("As", 33,  [5, 3, -3],  2.18, 119, 1.4e-5),
    "Se": Atom("Se", 34,  [6, 4, -2],  2.55, 120, 2.6e-6),
    "Br": Atom("Br", 35,  [-1, 1, 3, 5], 2.96, 120, 3.0e-6),
    "Kr": Atom("Kr", 36,  [0, 2],       3.00, 116, 1.9e-7),
    # Period 5
    "Rb": Atom("Rb", 37,  [1],          0.82, 220, 5.4e-5),
    "Sr": Atom("Sr", 38,  [2],          0.95, 195, 1.7e-4),
    "Y":  Atom("Y",  39,  [3],          1.22, 190, 8.8e-05),
    "Zr": Atom("Zr", 40,  [4],          1.33, 175, 9.6e-04),
    "Nb": Atom("Nb", 41,  [5],          1.60, 164, 4.6e-05),
    "Mo": Atom("Mo", 42,  [6, 5, 4, 3, 2], 2.16, 154, 5.6e-05),
    "Tc": Atom("Tc", 43,  [7, 6, 4],    1.90, 147, 0.0),
    "Ru": Atom("Ru", 44,  [8, 6, 4, 3, 2], 2.20, 146, 4.0e-06),
    "Rh": Atom("Rh", 45,  [3, 4],       2.28, 142, 1.0e-06),
    "Pd": Atom("Pd", 46,  [4, 2],       2.20, 139, 3.0e-06),
    "Ag": Atom("Ag", 47,  [1],          1.93, 145, 2.1e-06),
    "Cd": Atom("Cd", 48,  [2],          1.69, 144, 6.5e-06),
    "In": Atom("In", 49,  [3],          1.78, 142, 6.2e-06),
    "Sn": Atom("Sn", 50,  [4, 2],       1.96, 139, 1.1e-04),
    "Sb": Atom("Sb", 51,  [5, 3, -3],  2.05, 139, 6.0e-07),
    "Te": Atom("Te", 52,  [6, 4, -2],  2.10, 135, 9.0e-07),
    "I":  Atom("I",  53,  [-1, 1, 5, 7], 2.66, 139, 2.3e-07),
    "Xe": Atom("Xe", 54,  [0, 2, 4, 6], 2.60, 131, 4.0e-08),
    # Period 6
    "Cs": Atom("Cs", 55,  [1],          0.79, 244, 1.0e-06),
    "Ba": Atom("Ba", 56,  [2],          0.89, 215, 1.7e-04),
    "La": Atom("La", 57,  [3],          1.10, 207, 1.3e-05),
    "Ce": Atom("Ce", 58,  [4, 3],       1.12, 204, 2.2e-05),
    "Pr": Atom("Pr", 59,  [4, 3],       1.13, 203, 2.7e-06),
    "Nd": Atom("Nd", 60,  [3],          1.14, 201, 1.1e-05),
    "Pm": Atom("Pm", 61,  [3],          1.13, 199, 0.0),
    "Sm": Atom("Sm", 62,  [3, 2],       1.17, 198, 2.6e-06),
    "Eu": Atom("Eu", 63,  [3, 2],       1.20, 198, 7.0e-08),
    "Gd": Atom("Gd", 64,  [3],          1.20, 196, 2.6e-06),
    "Tb": Atom("Tb", 65,  [4, 3],       1.20, 194, 3.0e-07),
    "Dy": Atom("Dy", 66,  [3],          1.22, 192, 2.7e-06),
    "Ho": Atom("Ho", 67,  [3],          1.23, 192, 6.2e-07),
    "Er": Atom("Er", 68,  [3],          1.24, 189, 2.5e-06),
    "Tm": Atom("Tm", 69,  [3],          1.25, 190, 1.6e-07),
    "Yb": Atom("Yb", 70,  [3, 2],       1.10, 187, 8.0e-07),
    "Lu": Atom("Lu", 71,  [3],          1.27, 175, 5.9e-07),
    "Hf": Atom("Hf", 72,  [4],          1.30, 175, 8.0e-06),
    "Ta": Atom("Ta", 73,  [5],          1.50, 170, 7.0e-07),
    "W":  Atom("W",  74,  [6, 5, 4, 3, 2], 2.36, 162, 4.0e-06),
    "Re": Atom("Re", 75,  [7, 6, 4, 2, -1], 1.90, 151, 1.0e-07),
    "Os": Atom("Os", 76,  [8, 6, 4, 3, 2], 2.20, 144, 1.5e-06),
    "Ir": Atom("Ir", 77,  [6, 4, 3],   2.20, 141, 1.9e-06),
    "Pt": Atom("Pt", 78,  [4, 2],       2.28, 136, 4.8e-06),
    "Au": Atom("Au", 79,  [3, 1],       2.54, 136, 5.5e-07),
    "Hg": Atom("Hg", 80,  [2, 1],       2.00, 132, 1.8e-06),
    "Tl": Atom("Tl", 81,  [3, 1],       1.62, 145, 3.0e-06),
    "Pb": Atom("Pb", 82,  [4, 2],       2.33, 146, 5.6e-05),
    "Bi": Atom("Bi", 83,  [5, 3],       2.02, 148, 6.0e-07),
    # Period 7
    "Th": Atom("Th", 90,  [4],          1.11, 206, 2.4e-06),
    "Pa": Atom("Pa", 91,  [5, 4],       1.50, 200, 2.0e-11),
    "U":  Atom("U",  92,  [6, 5, 4, 3], 1.38, 196, 9.0e-07),
}

# Common anions for crystal chemistry
COMMON_ANIONS: Dict[str, Atom] = {
    "O":  PERIODIC_TABLE["O"],
    "S":  PERIODIC_TABLE["S"],
    "N":  PERIODIC_TABLE["N"],
    "F":  PERIODIC_TABLE["F"],
    "Cl": PERIODIC_TABLE["Cl"],
    "Se": PERIODIC_TABLE["Se"],
    "Te": PERIODIC_TABLE["Te"],
}

# Goldschmidt ionic radii (Shannon radii, VI-coordination) in pm
# Key: (symbol, oxidation_state) → radius_pm
# Source: Shannon (1976), effective ionic radii in PM of the elements
_IONIC_RADII: Dict[tuple[str, int], float] = {
    # cations (VI-coordination unless noted)
    ("Li", 1): 76,  ("Na", 1): 102,  ("K", 1): 138,  ("Rb", 1): 152,
    ("Cs", 1): 167,  ("Be", 2): 45,   ("Mg", 2): 72,   ("Ca", 2): 100,
    ("Sr", 2): 118,  ("Ba", 2): 135,  ("Sc", 3): 74.5, ("Y", 3): 90,
    ("Ti", 4): 60.5, ("Ti", 3): 67,   ("V", 5): 54,    ("Cr", 3): 61.5,
    ("Mn", 4): 53,   ("Mn", 3): 64.5, ("Mn", 2): 83,   ("Fe", 3): 55,
    ("Fe", 2): 78,   ("Co", 2): 74.5, ("Co", 3): 61,   ("Ni", 2): 69,
    ("Ni", 3): 56,   ("Cu", 1): 77,   ("Cu", 2): 73,   ("Zn", 2): 74,
    ("Al", 3): 53.5, ("Ga", 3): 62,   ("In", 3): 80,   ("Sn", 4): 69,
    ("Sn", 2): 118,  ("Pb", 4): 77.5, ("Pb", 2): 119,  ("Bi", 3): 103,
    ("Si", 4): 40,   ("P", 5): 38,    ("S", 6): 29,    ("N", 5): 13,
    ("La", 3): 103.2, ("Ce", 3): 101,  ("Ce", 4): 87,   ("Nd", 3): 98.3,
    ("Zr", 4): 72,   ("Hf", 4): 71,   ("Nb", 5): 64,   ("Ta", 5): 64,
    ("Mo", 6): 59,   ("W", 6): 60,    ("U", 4): 97,    ("U", 6): 73,
    # anions (VI-coordination)
    ("O", -2): 140,  ("S", -2): 184,  ("N", -3): 146,  ("F", -1): 133,
    ("Cl", -1): 181,  ("Se", -2): 198, ("Te", -2): 221,
}


def ionic_radius(symbol: str, oxidation: int) -> float | None:
    """Return ionic radius in pm for an element/oxidation pair (Shannon, VI-coord)."""
    return _IONIC_RADII.get((symbol, oxidation))


def tolerance_factor(ra: float, rc: float) -> float:
    """ Goldschmidt tolerance factor t = (ra + rc) / (sqrt(2) * (rc + ro)).
    Ideal t ≈ 1.0 for perovskite. Typical range 0.8–1.0 for stable.
    """
    ro = _IONIC_RADII.get(("O", -2), 140.0)
    import math
    return (ra + rc) / (math.sqrt(2) * (rc + ro))


def is_oxide(element: str) -> bool:
    """Return True if the element is a known oxide-forming element."""
    return element in (
        "Li", "Na", "K", "Mg", "Ca", "Sr", "Ba", "Al", "Ga", "In", "Sn",
        "Ti", "Zr", "Hf", "V", "Nb", "Ta", "W", "Mo", "Mn", "Fe", "Co",
        "Ni", "Cu", "Zn", "Si", "P", "S", "La", "Ce", "Nd", "Bi", "Pb", "U",
    )