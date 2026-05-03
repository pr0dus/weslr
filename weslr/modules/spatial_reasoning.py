"""
weslr/modules/spatial_reasoning.py
==================================
Phase 6.7 — Spatial reasoning / molecular geometry for Weslr.

Capabilities:
- Parse XYZ molecular coordinate files
- Compute Euclidean distances, bond angles, dihedral angles
- Detect tetrahedral chirality centers via volume determinant
- Assign VSEPR molecular shapes from coordination + bond angles
- Pre-defined idealized coordinates for common demo molecules

Deterministic (no stochastic components). Read-only (no coordinate modification).
Multi-tenant: caller passes data; no cross-tenant state.

Author: OCC (WESLR governed intelligence) — Phase 6.7
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import numpy as np


# ── Covalent radii (Å) for bond detection ────────────────────────────────────

_COVALENT_RADII: dict[str, float] = {
    "H": 0.32,
    "C": 0.77,
    "N": 0.75,
    "O": 0.73,
    "F": 0.71,
    "P": 1.06,
    "S": 1.02,
    "Cl": 0.99,
    "Br": 1.14,
    "I": 1.33,
    "Si": 1.11,
    "B": 0.84,
    "Na": 1.54,
    "K": 1.96,
    "Ca": 1.74,
    "Fe": 1.24,
    "Mg": 1.36,
    "Zn": 1.25,
}

# BOND_DISTANCE_FACTOR × (r_i + r_j) = max bonded distance
_BOND_DISTANCE_FACTOR = 1.2

# ── VSEPR shape map ────────────────────────────────────────────────────────────

_VSEPR_SHAPES: dict[str, dict] = {
    2: {0: "linear", 1: "bent / V-shaped", 2: "linear"},
    3: {
        0: "trigonal planar",
        1: "trigonal pyramidal",
        2: "T-shaped",
        3: "linear",
    },
    4: {
        0: "tetrahedral",
        1: "seesaw",
        2: "square planar",
        3: "T-shaped",
        4: "tetrahedral",
    },
    5: {
        0: "trigonal bipyramidal",
        1: "square pyramidal",
        2: "see-saw",
        3: "T-shaped",
        4: "linear",
        5: "trigonal bipyramidal",
    },
    6: {
        0: "octahedral",
        1: "square pyramidal",
        2: "square planar",
        3: "T-shaped",
        4: "linear",
        5: "octahedral",
    },
}


# ── Demo molecule coordinates (pre-defined XYZ as lists) ────────────────────


@dataclass
class DemoMolecule:
    name: str
    atoms: list[str]  # element symbols
    coords: np.ndarray  # shape (N, 3), float64, Å


_DEMO_MOLECULES: dict[str, DemoMolecule] = {
    "water": DemoMolecule(
        name="Water",
        atoms=["O", "H", "H"],
        coords=np.array(
            [
                [0.0000, 0.0000, 0.0000],
                [0.7572, 0.5862, 0.0000],
                [-0.7572, 0.5862, 0.0000],
            ],
            dtype=np.float64,
        ),
    ),
    "methane": DemoMolecule(
        name="Methane",
        atoms=["C", "H", "H", "H", "H"],
        coords=np.array(
            [
                [0.0000, 0.0000, 0.0000],
                [0.6292, 0.6292, 0.6292],
                [-0.6292, -0.6292, 0.6292],
                [-0.6292, 0.6292, -0.6292],
                [0.6292, -0.6292, -0.6292],
            ],
            dtype=np.float64,
        ),
    ),
    "ammonia": DemoMolecule(
        name="Ammonia",
        atoms=["N", "H", "H", "H"],
        coords=np.array(
            [
                [0.0000, 0.0000, 0.0000],
                [0.9400, 0.0000, 0.3130],
                [-0.4700, 0.8138, 0.3130],
                [-0.4700, -0.8138, 0.3130],
            ],
            dtype=np.float64,
        ),
    ),
    "ethanol": DemoMolecule(
        name="Ethanol",
        atoms=["C", "C", "O", "H", "H", "H", "H", "H", "H"],
        coords=np.array(
            [
                [0.0000, 0.0000, 0.0000],
                [1.5200, 0.0000, 0.0000],
                [2.0270, 1.3528, 0.0000],
                [0.5073, 0.8785, 0.9396],
                [-0.5064, 0.0000, 0.9396],
                [-0.5064, -0.8785, -0.9396],
                [1.9000, -0.5073, 0.9396],
                [2.0270, -0.5073, -0.9396],
                [3.0267, 1.3528, 0.0000],
            ],
            dtype=np.float64,
        ),
    ),
    "benzene": DemoMolecule(
        name="Benzene",
        atoms=["C", "C", "C", "C", "C", "C", "H", "H", "H", "H", "H", "H"],
        coords=np.array(
            [
                [1.4000, 0.0000, 0.0000],
                [0.7000, 1.2124, 0.0000],
                [-0.7000, 1.2124, 0.0000],
                [-1.4000, 0.0000, 0.0000],
                [-0.7000, -1.2124, 0.0000],
                [0.7000, -1.2124, 0.0000],
                [2.4840, 0.0000, 0.0000],
                [1.2420, 2.1513, 0.0000],
                [-1.2420, 2.1513, 0.0000],
                [-2.4840, 0.0000, 0.0000],
                [-1.2420, -2.1513, 0.0000],
                [1.2420, -2.1513, 0.0000],
            ],
            dtype=np.float64,
        ),
    ),
    "formaldehyde": DemoMolecule(
        name="Formaldehyde",
        atoms=["C", "O", "H", "H"],
        coords=np.array(
            [
                [0.0000, 0.0000, 0.0000],
                [1.2100, 0.0000, 0.0000],
                [-0.5425, 0.9391, 0.0000],
                [-0.5425, -0.9391, 0.0000],
            ],
            dtype=np.float64,
        ),
    ),
    "acetylene": DemoMolecule(
        name="Acetylene",
        atoms=["C", "C", "H", "H"],
        coords=np.array(
            [
                [-0.6020, 0.0000, 0.0000],
                [0.6020, 0.0000, 0.0000],
                [-1.6640, 0.0000, 0.0000],
                [1.6640, 0.0000, 0.0000],
            ],
            dtype=np.float64,
        ),
    ),
}


# ── MolecularStructure class ─────────────────────────────────────────────────


@dataclass
class Bond:
    i: int
    j: int
    order: float = 1.0  # default single bond


class MolecularStructure:
    """Molecular structure with 3D coordinates and geometric analysis."""

    def __init__(
        self,
        atoms: list[str],
        coords: np.ndarray,
        bonds: Optional[list[Bond]] = None,
        name: str = "",
    ):
        """Initialize with atom list and coordinates.

        Args:
            atoms: list of element symbols, length N
            coords: numpy array shape (N, 3), float64, Å
            bonds: optional list of Bond(i, j, order) tuples
        """
        if len(atoms) != coords.shape[0]:
            raise ValueError(
                f"Atom count ({len(atoms)}) != coordinate rows ({coords.shape[0]})"
            )
        self.atoms = list(atoms)
        self.coords = np.asarray(coords, dtype=np.float64)
        self.name = name
        object.__setattr__(self, "bonds", bonds if bonds is not None else [])
        object.__setattr__(self, "_bonds_computed", bonds is not None)

    # ── XYZ parsing ─────────────────────────────────────────────────────────

    @classmethod
    def from_xyz(cls, text: str) -> "MolecularStructure":
        """Parse XYZ format string into MolecularStructure.

        XYZ format:
          N
          comment line
          Element  X  Y  Z
          ...
        """
        lines = text.strip().split("\n")
        if len(lines) < 3:
            raise ValueError("XYZ file must have at least 3 lines")

        n_atoms = int(lines[0].strip())
        if len(lines) < 2 + n_atoms:
            raise ValueError(
                f"XYZ header says {n_atoms} atoms but file only has "
                f"{len(lines) - 2} coordinate lines"
            )
        atoms: list[str] = []
        coords_list: list[list[float]] = []

        for line in lines[2 : 2 + n_atoms]:
            parts = line.strip().split()
            if len(parts) < 4:
                raise ValueError(f"Malformed XYZ line: {line}")
            atoms.append(parts[0])
            coords_list.append([float(parts[1]), float(parts[2]), float(parts[3])])

        coords = np.array(coords_list, dtype=np.float64)
        return cls(atoms=atoms, coords=coords)

    @classmethod
    def from_xyz_file(cls, filepath: str) -> "MolecularStructure":
        """Load XYZ from a file path."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"XYZ file not found: {filepath}")
        return cls.from_xyz(path.read_text())

    @classmethod
    def from_demo(cls, name: str) -> "MolecularStructure":
        """Load a pre-defined demo molecule."""
        key = name.lower()
        if key not in _DEMO_MOLECULES:
            available = ", ".join(sorted(_DEMO_MOLECULES.keys()))
            raise ValueError(
                f"Unknown demo molecule '{name}'. Available: {available}"
            )
        demo = _DEMO_MOLECULES[key]
        return cls(atoms=list(demo.atoms), coords=demo.coords.copy(), name=demo.name)

    # ── Coordinate generation ──────────────────────────────────────────────

    @classmethod
    def from_smiles(cls, smiles: str) -> "MolecularStructure":
        """Attempt to generate 3D coordinates from a SMILES string.

        Uses RDKit if available (optional dependency).
        Otherwise raises an informative error directing user to use XYZ or demo.
        """
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError(f"Could not parse SMILES: {smiles}")

            # Add hydrogens and embed 3D coordinates
            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, randomSeed=42)
            AllChem.MMFFOptimizeMolecule(mol)

            # Extract coordinates and atoms
            conf = mol.GetConformer()
            atoms = [a.GetSymbol() for a in mol.GetAtoms()]
            coords = np.array(
                [[conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y, conf.GetAtomPosition(i).z]
                 for i in range(mol.GetNumAtoms())],
                dtype=np.float64,
            )
            return cls(atoms=atoms, coords=coords)
        except ImportError:
            raise ImportError(
                "RDKit is not installed. SMILES→3D conversion requires:\n"
                "  pip install rdkit-pypi\n"
                "Alternatively, load an XYZ file via:\n"
                "  /molecule load file.xyz\n"
                "Or use a demo molecule:\n"
                "  /molecule demo water"
            )

    # ── Bond detection ──────────────────────────────────────────────────────

    def _detect_bonds(self) -> list[Bond]:
        """Detect bonds from distances and covalent radii."""
        n = self.n_atoms
        bonds: list[Bond] = []
        for i in range(n):
            for j in range(i + 1, n):
                r_i = _COVALENT_RADII.get(self.atoms[i], 0.8)
                r_j = _COVALENT_RADII.get(self.atoms[j], 0.8)
                max_dist = _BOND_DISTANCE_FACTOR * (r_i + r_j)
                d = float(np.linalg.norm(self.coords[i] - self.coords[j]))
                if d < max_dist:
                    bonds.append(Bond(i=i, j=j))
        return bonds

    @property
    def bonds(self) -> list[Bond]:
        if not self._bonds_computed:
            object.__setattr__(self, "_bonds_list", self._detect_bonds())
            object.__setattr__(self, "_bonds_computed", True)
        return self._bonds_list

    @bonds.setter
    def bonds(self, value):
        object.__setattr__(self, "_bonds_list", value)
        object.__setattr__(self, "_bonds_computed", True)

    # ── Geometric properties ────────────────────────────────────────────────

    @property
    def n_atoms(self) -> int:
        return len(self.atoms)

    def distance(self, i: int, j: int) -> float:
        """Euclidean distance between atoms i and j in Å."""
        return float(np.linalg.norm(self.coords[i] - self.coords[j]))

    def angle(self, i: int, j: int, k: int, degrees: bool = True) -> float:
        """Angle ∠ijk in degrees (default) or radians."""
        vi = self.coords[i] - self.coords[j]
        vk = self.coords[k] - self.coords[j]
        cos_angle = float(np.clip(np.dot(vi, vk) / (np.linalg.norm(vi) * np.linalg.norm(vk) + 1e-12), -1.0, 1.0))
        angle_rad = math.acos(cos_angle)
        return float(math.degrees(angle_rad)) if degrees else angle_rad

    def dihedral(self, i: int, j: int, k: int, l: int, degrees: bool = True) -> float:
        """Dihedral angle ∠ijkl (torsion) in degrees (default) or radians.

        Uses the AT&T formula (four points, two dihedral planes).
        """
        b_ij = self.coords[j] - self.coords[i]
        b_jk = self.coords[k] - self.coords[j]
        b_kl = self.coords[l] - self.coords[k]

        # Normalized bisectors for stable computation
        def _norm(v: np.ndarray) -> np.ndarray:
            n = np.linalg.norm(v)
            return v / (n + 1e-12)

        n1 = _norm(np.cross(b_ij, b_jk))
        n2 = _norm(np.cross(b_jk, b_kl))

        m1 = np.cross(n1, _norm(b_jk))
        x = float(np.dot(m1, n2))
        y = float(np.dot(n1, n2))

        dihe = math.atan2(x, y)
        return float(math.degrees(dihe)) if degrees else dihe

    # ── Bond lengths / angles tables ────────────────────────────────────────

    def all_distances(self, threshold: float = 2.5) -> dict[tuple[int, int], float]:
        """Return all pairwise distances below threshold (Å)."""
        n = self.n_atoms
        result = {}
        for i in range(n):
            for j in range(i + 1, n):
                d = self.distance(i, j)
                if d < threshold:
                    result[(i, j)] = d
        return result

    def all_angles(self) -> list[dict]:
        """Return all bond angles (i-j-k where j is the central atom bonded to both i and k)."""
        bond_map: dict[int, set[int]] = {i: set() for i in range(self.n_atoms)}
        for b in self.bonds:
            bond_map[b.i].add(b.j)
            bond_map[b.j].add(b.i)
        angles = []
        for j in range(self.n_atoms):
            neighbors = sorted(bond_map[j])
            for ii in range(len(neighbors)):
                for kk in range(ii + 1, len(neighbors)):
                    i, k = neighbors[ii], neighbors[kk]
                    ang = self.angle(i, j, k)
                    angles.append({"atoms": (i, j, k), "angle": round(ang, 2)})
        return angles

    def all_dihedrals(self) -> list[dict]:
        """Return all proper dihedral angles (i-j-k-l where each consecutive pair is bonded)."""
        bond_map: dict[int, set[int]] = {i: set() for i in range(self.n_atoms)}
        for b in self.bonds:
            bond_map[b.i].add(b.j)
            bond_map[b.j].add(b.i)

        dihedrals = []
        for j in range(self.n_atoms):
            for k in bond_map[j]:
                if k <= j:
                    continue
                for i in bond_map[j]:
                    if i == k:
                        continue
                    for l in bond_map[k]:
                        if l == j:
                            continue
                        # Avoid duplicates by requiring i < l or canonical ordering
                        dihe = self.dihedral(i, j, k, l)
                        dihedrals.append(
                            {"atoms": (i, j, k, l), "dihedral": round(dihe, 2)}
                        )
        return dihedrals

    def _neighbors(self, atom_idx: int) -> list[tuple[int, str, float]]:
        """Return list of (neighbor_idx, atom_symbol, bond_length)."""
        neighbors = []
        for b in self.bonds:
            if b.i == atom_idx:
                neighbors.append((b.j, self.atoms[b.j], self.distance(atom_idx, b.j)))
            elif b.j == atom_idx:
                neighbors.append((b.i, self.atoms[b.i], self.distance(atom_idx, b.i)))
        return neighbors

    # ── Chirality ───────────────────────────────────────────────────────────

    def is_chiral_center(self, atom_idx: int) -> bool:
        """Detect if atom is a tetrahedral chiral center.

        Criteria:
        1. Atom has exactly 4 neighbors
        2. All 4 neighbors are distinct atomic numbers
        3. Tetrahedral volume (determinant of 3 bond vectors from central atom) ≠ 0

        Returns True if all criteria are met.
        """
        neighbors = self._neighbors(atom_idx)
        if len(neighbors) != 4:
            return False

        # All four neighbors must be distinct
        atomic_numbers = [self._atomic_number(self.atoms[n[0]]) for n in neighbors]
        if len(set(atomic_numbers)) != 4:
            return False

        # Tetrahedral volume: determinant of vectors from central atom to neighbors
        # Non-zero determinant → non-planar (tetrahedral)
        center = self.coords[atom_idx]
        vectors = np.array(
            [self.coordinates[n[0]] - center for n in neighbors],
            dtype=np.float64,
        )
        det = float(np.linalg.det(vectors))
        return abs(det) > 1e-6

    def chirality_centers(self) -> list[int]:
        """Return list of atom indices that are chiral centers."""
        return [i for i in range(self.n_atoms) if self.is_chiral_center(i)]

    # ── VSEPR shape ────────────────────────────────────────────────────────

    def vsepr_shape(self, center_idx: int) -> str:
        """Infer VSEPR molecular shape for a central atom.

        Based on coordination number and bond angles.
        Lone pairs are inferred from total valence electrons if electron_config available,
        otherwise derived from the observed bond angles vs ideal values.

        Returns shape name or "unknown".
        """
        neighbors = self._neighbors(center_idx)
        n = len(neighbors)

        if n < 2:
            return "atomic" if n == 0 else "monocoordinate"

        # Compute bond angles around the center
        angles_to_neighbor = []
        neighbor_indices = [nb[0] for nb in neighbors]
        for ii in range(n):
            for kk in range(ii + 1, n):
                ang = self.angle(neighbor_indices[ii], center_idx, neighbor_indices[kk])
                angles_to_neighbor.append(ang)

        avg_angle = sum(angles_to_neighbor) / len(angles_to_neighbor) if angles_to_neighbor else 120.0

        # Infer lone pairs from angle vs ideal
        # Ideal tetrahedral: 109.5°, ideal trigonal planar: 120°, linear: 180°
        lone_pairs = 0
        if n == 2:
            if abs(avg_angle - 180.0) < 15.0:
                return "linear"
            elif abs(avg_angle - 109.5) < 15.0:
                return "bent"  # 2 atoms + 2 lone pairs typical
            else:
                return "bent"  # compressed by lone pairs
        elif n == 3:
            if abs(avg_angle - 109.5) < abs(avg_angle - 120.0):
                # 3 bonds + 1 lone pair → trigonal pyramidal (e.g. NH3)
                return "trigonal pyramidal"
            else:
                # 3 bonding pairs, no lone pairs → trigonal planar (e.g. BF3)
                return "trigonal planar"
        elif n == 4:
            if abs(avg_angle - 109.5) < 10.0:
                return "tetrahedral"
            else:
                return "tetrahedral"
        elif n == 5:
            return "trigonal bipyramidal"
        elif n == 6:
            return "octahedral"
        else:
            return "unknown"

    def vsepr_shapes(self) -> dict[int, str]:
        """Return VSEPR shapes for all non-H centers."""
        shapes = {}
        for i, atom in enumerate(self.atoms):
            if atom != "H":
                shapes[i] = self.vsepr_shape(i)
        return shapes

    # ── Utilities ──────────────────────────────────────────────────────────

    @staticmethod
    def _atomic_number(symbol: str) -> int:
        """Map element symbol to atomic number."""
        AN = {"H": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7, "O": 8,
              "F": 9, "Ne": 10, "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "P": 15,
              "S": 16, "Cl": 17, "Ar": 18, "K": 19, "Ca": 20, "Fe": 26, "Zn": 30}
        return AN.get(symbol, 0)

    def to_xyz_string(self, comment: str = "") -> str:
        """Serialize to XYZ format string."""
        lines = [str(self.n_atoms), comment]
        for atom, coord in zip(self.atoms, self.coords):
            lines.append(f"{atom:2s}  {coord[0]:10.5f}  {coord[1]:10.5f}  {coord[2]:10.5f}")
        return "\n".join(lines)

    @property
    def coordinates(self) -> np.ndarray:
        """Alias for coords."""
        return self.coords

    # ── Formatting helpers ─────────────────────────────────────────────────

    def format_geometry_summary(self) -> str:
        """Format a full geometry summary (suitable for /molecule geometry output)."""
        lines = []
        lines.append(f"Atoms ({self.n_atoms}): {', '.join(self.atoms)}")
        lines.append("")

        # Bond distances
        lines.append("Bond distances:")
        all_bonds = sorted(self.bonds, key=lambda b: (b.i, b.j))
        if all_bonds:
            for b in all_bonds:
                d = self.distance(b.i, b.j)
                ai, aj = self.atoms[b.i], self.atoms[b.j]
                lines.append(f"  {ai}{b.i+1}-{aj}{b.j+1}: {d:.3f} Å")
        else:
            lines.append("  (none detected)")

        # Angles
        lines.append("")
        lines.append("Bond angles:")
        all_angles = self.all_angles()
        if all_angles:
            for ang in sorted(all_angles, key=lambda a: a["atoms"]):
                i, j, k = ang["atoms"]
                lines.append(
                    f"  {self.atoms[i]}{i+1}-{self.atoms[j]}{j+1}-{self.atoms[k]}{k+1}: "
                    f"{ang['angle']:.2f}°"
                )
        else:
            lines.append("  (none detected)")

        # Dihedrals
        lines.append("")
        lines.append("Dihedral angles:")
        all_dihe = self.all_dihedrals()
        if all_dihe:
            for di in sorted(all_dihe[:10], key=lambda d: d["atoms"]):
                i, j, k, l = di["atoms"]
                lines.append(
                    f"  {self.atoms[i]}{i+1}-{self.atoms[j]}{j+1}-"
                    f"{self.atoms[k]}{k+1}-{self.atoms[l]}{l+1}: "
                    f"{di['dihedral']:.2f}°"
                )
            if len(all_dihe) > 10:
                lines.append(f"  ... and {len(all_dihe) - 10} more dihedrals")
        else:
            lines.append("  (none detected)")

        # VSEPR shapes
        lines.append("")
        lines.append("VSEPR shapes:")
        shapes = self.vsepr_shapes()
        if shapes:
            for idx, shape in shapes.items():
                lines.append(f"  {self.atoms[idx]}{idx+1}: {shape}")
        else:
            lines.append("  (none)")

        # Chirality
        lines.append("")
        chiral = self.chirality_centers()
        if chiral:
            chiral_names = [f"{self.atoms[i]}{i+1}" for i in chiral]
            lines.append(f"Chiral centers: {', '.join(chiral_names)}")
        else:
            lines.append("Chiral centers: None")

        return "\n".join(lines)

    def propose_shape(self, center_idx: int) -> str:
        """Generate a VSEPR-based shape hypothesis for a central atom."""
        shape = self.vsepr_shape(center_idx)
        neighbors = self._neighbors(center_idx)
        n = len(neighbors)

        ideal_angles = {
            "linear": "180°",
            "bent": "≤109.5° (compressed by lone pairs)",
            "trigonal planar": "120°",
            "trigonal pyramidal": "109.5°",
            "tetrahedral": "109.5°",
            "square planar": "90°",
            "trigonal bipyramidal": "90° / 120°",
            "octahedral": "90°",
            "see-saw": "90° / 120°",
            "T-shaped": "90°",
            "square pyramidal": "90°",
        }

        ideal = ideal_angles.get(shape, "unknown")
        atom = self.atoms[center_idx]

        # Compute observed angle if possible
        observed_angle = ""
        if n >= 2:
            angles_obs = []
            for ii in range(n):
                for kk in range(ii + 1, n):
                    ang = self.angle(neighbors[ii][0], center_idx, neighbors[kk][0])
                    angles_obs.append(ang)
            if angles_obs:
                avg_obs = sum(angles_obs) / len(angles_obs)
                observed_angle = f" (observed avg: {avg_obs:.1f}°)"

        lines = [
            f"Central atom: {atom}{center_idx+1}",
            f"Coordination number: {n}",
            f"Predicted VSEPR shape: {shape}",
            f"Ideal bond angle: {ideal}{observed_angle}",
        ]

        # Add a functional note
        functional_notes = {
            "bent": (
                "Bent geometry creates a permanent dipole moment. "
                "Enables hydrogen bonding and high solvent surface tension. "
                "Common in H₂O, H₂S, SO₂."
            ),
            "linear": (
                "Linear geometry is non-polar if substituents are identical. "
                "Examples: CO₂, acetylene (C₂H₂), HgCl₂."
            ),
            "trigonal planar": (
                "Trigonal planar geometry is typically non-polar. "
                "Common in boranes (BH₃), carbonyls (R₂C=O), nitrate (NO₃⁻)."
            ),
            "tetrahedral": (
                "Tetrahedral geometry enables sp³ hybridization. "
                "Non-polar if all substituents identical (CH₄). "
                "Polar if substituents differ (CH₃Cl). "
                "Foundation for chiral centers when 4 substituents differ."
            ),
            "trigonal pyramidal": (
                "Trigonal pyramidal geometry gives a molecular dipole. "
                "Lone pair on central atom compresses bond angles. "
                "Common in ammonia (NH₃), phosphine (PH₃)."
            ),
        }

        if shape in functional_notes:
            lines.append("")
            lines.append(f"Note: {functional_notes[shape]}")

        return "\n".join(lines)


# ── Public helper: available demo molecules ─────────────────────────────────


def get_available_demos() -> list[str]:
    """Return sorted list of available demo molecule names."""
    return sorted(_DEMO_MOLECULES.keys())


def get_demo_molecule(name: str) -> MolecularStructure:
    """Convenience: load a demo molecule by name."""
    return MolecularStructure.from_demo(name)
