"""
weslr/commands/spatial_commands.py
===================================
Phase 6.7 — Command handlers for molecular geometry commands.

Commands:
- /molecule load <file.xyz> — load XYZ file into current session
- /molecule demo <name>    — load predefined demo molecule
- /molecule geometry       — print full geometry summary
- /molecule measure distance <i> <j>
- /molecule measure angle <i> <j> <k>
- /molecule measure dihedral <i> <j> <k> <l>
- /molecule chirality <atom_idx>
- /propose shape <molecule> — VSEPR shape hypothesis
"""

from __future__ import annotations

import re
from typing import Optional

from weslr.modules.spatial_reasoning import (
    MolecularStructure,
    get_available_demos,
)


# ── Session-level molecule state ────────────────────────────────────────────

_CURRENT_MOLECULE: Optional[MolecularStructure] = None


def set_current_molecule(mol: MolecularStructure) -> None:
    global _CURRENT_MOLECULE
    _CURRENT_MOLECULE = mol


def get_current_molecule() -> Optional[MolecularStructure]:
    return _CURRENT_MOLECULE


def clear_current_molecule() -> None:
    global _CURRENT_MOLECULE
    _CURRENT_MOLECULE = None


# ── Command handlers ─────────────────────────────────────────────────────────


def handle_molecule_load(message: str, lowered: str) -> str:
    """Handle /molecule load <path|smiles>."""
    body = lowered
    for prefix in ("/molecule load ", "molecule load "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    target = body.strip().strip('"').strip("'")

    if not target:
        return "Usage: /molecule load <file.xyz>\n  or: /molecule load <smiles> (requires RDKit)"

    # Detect if it's a file path or SMILES
    is_smiles = not ("/" in target or "\\" in target or target.endswith(".xyz"))

    if is_smiles:
        try:
            mol = MolecularStructure.from_smiles(target)
            set_current_molecule(mol)
            return f"Loaded molecule from SMILES: {target}\n  Atoms: {', '.join(mol.atoms)}\n  Use /molecule geometry to see details."
        except ImportError as e:
            return str(e)

    # File path
    try:
        mol = MolecularStructure.from_xyz_file(target)
        set_current_molecule(mol)
        return f"Loaded XYZ file: {target}\n  Atoms: {', '.join(mol.atoms)}\n  Use /molecule geometry to see details."
    except FileNotFoundError:
        return f"File not found: {target}"
    except Exception as e:
        return f"Error parsing XYZ file: {e}"


def handle_molecule_demo(message: str, lowered: str) -> str:
    """Handle /molecule demo <name>."""
    body = lowered
    for prefix in ("/molecule demo ", "molecule demo "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    name = body.strip()
    if not name:
        available = ", ".join(get_available_demos())
        return f"Usage: /molecule demo <name>\nAvailable demos: {available}"

    try:
        mol = MolecularStructure.from_demo(name)
        set_current_molecule(mol)
        return (
            f"Loaded demo molecule: {mol.name} ({name})\n"
            f"  Formula: {''.join(mol.atoms)}\n"
            f"  Atoms: {mol.n_atoms}\n"
            f"  Use /molecule geometry for full analysis."
        )
    except ValueError as e:
        available = ", ".join(get_available_demos())
        return f"{e}\nAvailable demos: {available}"


def handle_molecule_geometry(message: str, lowered: str) -> str:
    """Handle /molecule geometry."""
    mol = get_current_molecule()
    if mol is None:
        return (
            "No molecule loaded.\n"
            "  Load an XYZ file: /molecule load file.xyz\n"
            "  Or use a demo:     /molecule demo water"
        )
    return mol.format_geometry_summary()


def handle_molecule_measure(message: str, lowered: str) -> str:
    """Handle /molecule measure distance|angle|dihedral ..."""
    mol = get_current_molecule()
    if mol is None:
        return "No molecule loaded. Use /molecule load file.xyz or /molecule demo water."

    body = lowered
    for prefix in ("/molecule measure ", "molecule measure "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    parts = body.strip().split()
    if not parts:
        return (
            "Usage:\n"
            "  /molecule measure distance <i> <j>\n"
            "  /molecule measure angle <i> <j> <k>\n"
            "  /molecule measure dihedral <i> <j> <k> <l>\n"
            "(atom indices are 1-based)"
        )

    measure_type = parts[0]
    indices: list[int] = []
    try:
        indices = [int(p) - 1 for p in parts[1:5]]  # 1-based → 0-based
    except ValueError:
        return f"Invalid atom index. Atom indices are 1-based integers."

    def bad_n(n_expected: int) -> str:
        return f"Expected {n_expected} atom indices, got {len(indices)}."

    if measure_type == "distance":
        if len(indices) != 2:
            return bad_n(2)
        i, j = indices
        if not (0 <= i < mol.n_atoms and 0 <= j < mol.n_atoms):
            return f"Atom index out of range (1–{mol.n_atoms})."
        d = mol.distance(i, j)
        return f"{mol.atoms[i]}{i+1}–{mol.atoms[j]}{j+1}: {d:.4f} Å"

    elif measure_type == "angle":
        if len(indices) != 3:
            return bad_n(3)
        i, j, k = indices
        if not all(0 <= x < mol.n_atoms for x in [i, j, k]):
            return f"Atom index out of range (1–{mol.n_atoms})."
        ang = mol.angle(i, j, k)
        return f"{mol.atoms[i]}{i+1}–{mol.atoms[j]}{j+1}–{mol.atoms[k]}{k+1}: {ang:.2f}°"

    elif measure_type == "dihedral":
        if len(indices) != 4:
            return bad_n(4)
        i, j, k, l = indices
        if not all(0 <= x < mol.n_atoms for x in [i, j, k, l]):
            return f"Atom index out of range (1–{mol.n_atoms})."
        dihe = mol.dihedral(i, j, k, l)
        return f"{mol.atoms[i]}{i+1}–{mol.atoms[j]}{j+1}–{mol.atoms[k]}{k+1}–{mol.atoms[l]}{l+1}: {dihe:.2f}°"

    else:
        return (
            f"Unknown measure type '{measure_type}'.\n"
            "  Use: distance | angle | dihedral"
        )


def handle_molecule_chirality(message: str, lowered: str) -> str:
    """Handle /molecule chirality <atom_idx>."""
    mol = get_current_molecule()
    if mol is None:
        return "No molecule loaded."

    body = lowered
    for prefix in ("/molecule chirality ", "molecule chirality "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    else:
        # Exact match (no trailing content) — treat as list-all request
        if body.strip() in ("/molecule chirality", "molecule chirality"):
            body = ""


    if not body.strip():
        # List all chiral centers
        chiral = mol.chirality_centers()
        if not chiral:
            return "No chiral centers detected."
        lines = [f"Chiral centers ({len(chiral)}):"]
        for idx in chiral:
            lines.append(f"  {mol.atoms[idx]}{idx+1}")
        return "\n".join(lines)

    try:
        atom_idx = int(body.strip()) - 1  # 1-based → 0-based
    except ValueError:
        return "Usage: /molecule chirality <atom_idx (1-based)>\n  Or: /molecule chirality (to list all)"

    if not (0 <= atom_idx < mol.n_atoms):
        return f"Atom index out of range (1–{mol.n_atoms})."

    is_chiral = mol.is_chiral_center(atom_idx)
    atom = mol.atoms[atom_idx]
    if is_chiral:
        neighbors = mol._neighbors(atom_idx)
        neighbor_names = [mol.atoms[n[0]] for n in neighbors]
        return (
            f"{atom}{atom_idx+1} is a chiral center.\n"
            f"  Neighbors: {', '.join(neighbor_names)}\n"
            f"  Stereochemistry: Cannot determine R/S without CIP priority ordering.\n"
            f"  (Phase 6.7 provides sign-based detection; CIP ranking is future work.)"
        )
    else:
        return f"{atom}{atom_idx+1} is not a chiral center."


def handle_propose_shape(message: str, lowered: str) -> str:
    """Handle /propose shape <molecule>. Uses currently loaded molecule."""
    mol = get_current_molecule()
    if mol is None:
        return "No molecule loaded. Use /molecule demo water or /molecule load file.xyz."

    body = lowered
    for prefix in ("/propose shape ", "propose shape "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    # If molecule name given and differs from loaded, try to load it
    target = body.strip()
    if target and target != "current" and target != "loaded":
        # Try demo first
        try:
            mol = MolecularStructure.from_demo(target)
            set_current_molecule(mol)
        except ValueError:
            return f"Unknown molecule '{target}'. Use /molecule demo water first, or /molecule demo to see available."

    if mol.n_atoms == 0:
        return "No molecule loaded."

    # Propose shapes for all non-H centers
    lines = [f"Shape analysis for {mol.name or 'loaded molecule'}:", ""]
    shapes = mol.vsepr_shapes()
    for idx, shape in shapes.items():
        atom = mol.atoms[idx]
        proposal = mol.propose_shape(idx)
        lines.append(proposal)
        lines.append("")

    return "\n".join(lines[:-1]) if lines else ""


def handle_molecule_command(message: str, lowered: str) -> str:
    """Route /molecule commands to appropriate handler."""
    if lowered.startswith("/molecule load") or lowered.startswith("molecule load"):
        return handle_molecule_load(message, lowered)
    elif lowered.startswith("/molecule demo") or lowered.startswith("molecule demo"):
        return handle_molecule_demo(message, lowered)
    elif lowered.startswith("/molecule geometry") or lowered.startswith("molecule geometry"):
        return handle_molecule_geometry(message, lowered)
    elif lowered.startswith("/molecule measure") or lowered.startswith("molecule measure"):
        return handle_molecule_measure(message, lowered)
    elif lowered.startswith("/molecule chirality") or lowered.startswith("molecule chirality"):
        return handle_molecule_chirality(message, lowered)
    elif lowered.startswith("/propose shape") or lowered.startswith("propose shape"):
        return handle_propose_shape(message, lowered)
    elif lowered.startswith("/molecule") or lowered.startswith("molecule"):
        # Generic → usage
        return (
            "Molecular geometry commands:\n"
            "  /molecule load <file.xyz>          — load XYZ file\n"
            "  /molecule load <smiles>            — load from SMILES (requires RDKit)\n"
            "  /molecule demo <name>              — load demo (water, methane, ammonia, ethanol, benzene, formaldehyde, acetylene)\n"
            "  /molecule geometry                 — full geometry summary\n"
            "  /molecule measure distance <i> <j>\n"
            "  /molecule measure angle <i> <j> <k>\n"
            "  /molecule measure dihedral <i> <j> <k> <l>\n"
            "  /molecule chirality <atom_idx>     — check R/S\n"
            "  /molecule chirality               — list all chiral centers\n"
            "  /propose shape [molecule]          — VSEPR shape analysis\n"
            "Atom indices are 1-based."
        )
    return "Unknown command."
