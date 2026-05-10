"""Weslr Scientific Structure Inspection (v1A)

Safe, read-only inspection of common scientific structure files.
Supported formats:
  - XYZ
  - CIF
  - POSCAR / CONTCAR / .vasp

Safety Boundaries:
  - stdlib only
  - no simulation, no structure generation, no external lookups
  - bounded summary output only
  - path traversal protection
"""

from __future__ import annotations

import math
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

__all__ = [
    "ScientificStructureInspectionError",
    "inspect_scientific_structure_file",
]


SCIENTIFIC_EXTENSIONS = {".xyz", ".cif", ".vasp"}
SCIENTIFIC_FILENAMES = {"POSCAR", "CONTCAR"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_WARNINGS = 10


class ScientificStructureInspectionError(Exception):
    """Raised when scientific structure inspection fails."""


def _is_safe_path(filepath: str, workspace_dir: str) -> bool:
    try:
        workspace = Path(workspace_dir).resolve()
        path = Path(filepath).resolve()
        return str(path).startswith(str(workspace) + os.sep) or path == workspace
    except Exception:
        return False


def _safe_float(value: str) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _format_formula(species_counts: Dict[str, int]) -> str:
    if not species_counts:
        return ""
    parts = []
    for species in sorted(species_counts.keys()):
        count = species_counts[species]
        parts.append(species if count == 1 else f"{species}{count}")
    return "".join(parts)


def _vector_length(v: List[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _angle_deg(a: List[float], b: List[float]) -> float | None:
    la = _vector_length(a)
    lb = _vector_length(b)
    if la == 0 or lb == 0:
        return None
    dot = sum(x * y for x, y in zip(a, b))
    ratio = max(-1.0, min(1.0, dot / (la * lb)))
    return math.degrees(math.acos(ratio))


def _lattice_summary(vectors: List[List[float]]) -> Dict[str, float] | None:
    if len(vectors) != 3 or any(len(v) != 3 for v in vectors):
        return None
    a = _vector_length(vectors[0])
    b = _vector_length(vectors[1])
    c = _vector_length(vectors[2])
    alpha = _angle_deg(vectors[1], vectors[2])
    beta = _angle_deg(vectors[0], vectors[2])
    gamma = _angle_deg(vectors[0], vectors[1])
    return {
        "a": round(a, 6),
        "b": round(b, 6),
        "c": round(c, 6),
        "alpha": round(alpha, 6) if alpha is not None else None,
        "beta": round(beta, 6) if beta is not None else None,
        "gamma": round(gamma, 6) if gamma is not None else None,
    }


def _format_cell_parameters(cell: Dict[str, Any] | None) -> str:
    if not cell:
        return ""
    parts = []
    for key in ("a", "b", "c", "alpha", "beta", "gamma"):
        if cell.get(key) is not None:
            parts.append(f"{key}={cell[key]}")
    return ", ".join(parts)


def _base_result(path: Path, type_name: str) -> Dict[str, Any]:
    return {
        "type": type_name,
        "read_only": True,
        "atom_count": 0,
        "species_counts": {},
        "formula": "",
        "cell_parameters": None,
        "warnings": [],
        "metadata": {
            "source_file": path.name,
            "parsed_successfully": False,
            "parse_error": None,
        },
    }


def _finalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    lines = [
        f"[{result.get('type', 'scientific_structure').upper()}] atoms={result.get('atom_count', 0)}",
        "read_only: true",
    ]
    if result.get("formula"):
        lines.append(f"formula: {result['formula']}")
    if result.get("species_counts"):
        species = ", ".join(
            f"{k}:{v}" for k, v in sorted(result["species_counts"].items())
        )
        lines.append(f"species: {species}")
    cell = _format_cell_parameters(result.get("cell_parameters"))
    if cell:
        lines.append(f"cell: {cell}")
    warnings = result.get("warnings", [])
    if warnings:
        lines.append("warnings:")
        for warning in warnings[:MAX_WARNINGS]:
            lines.append(f"- {warning}")
    result["summary"] = "\n".join(lines)
    result["structured_output"] = result["summary"]
    return result


def _inspect_xyz(path: Path) -> Dict[str, Any]:
    result = _base_result(path, "xyz_structure")
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = [line.rstrip() for line in text.splitlines()]
        if len(lines) < 2:
            result["warnings"].append("XYZ file is shorter than expected")
            return _finalize_result(result)

        declared_count = int(lines[0].strip())
        species: List[str] = []
        for raw_line in lines[2:]:
            parts = raw_line.split()
            if len(parts) < 4:
                continue
            symbol = parts[0]
            coords = [_safe_float(parts[1]), _safe_float(parts[2]), _safe_float(parts[3])]
            if any(value is None for value in coords):
                continue
            species.append(symbol)

        result["atom_count"] = len(species)
        result["species_counts"] = dict(Counter(species))
        result["formula"] = _format_formula(result["species_counts"])
        if declared_count != len(species):
            result["warnings"].append(
                f"Declared atom count {declared_count} does not match parsed count {len(species)}"
            )
        result["metadata"]["parsed_successfully"] = True
    except Exception as e:
        result["warnings"].append(f"XYZ parse warning: {e}")
        result["metadata"]["parse_error"] = str(e)
    return _finalize_result(result)


def _inspect_cif(path: Path) -> Dict[str, Any]:
    result = _base_result(path, "cif_structure")
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        cell: Dict[str, float | None] = {
            "a": None,
            "b": None,
            "c": None,
            "alpha": None,
            "beta": None,
            "gamma": None,
        }
        formula = ""
        species: List[str] = []

        loop_headers: List[str] = []
        in_loop = False
        atom_type_index = None
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("_cell_length_a"):
                cell["a"] = _safe_float(line.split()[-1])
            elif line.startswith("_cell_length_b"):
                cell["b"] = _safe_float(line.split()[-1])
            elif line.startswith("_cell_length_c"):
                cell["c"] = _safe_float(line.split()[-1])
            elif line.startswith("_cell_angle_alpha"):
                cell["alpha"] = _safe_float(line.split()[-1])
            elif line.startswith("_cell_angle_beta"):
                cell["beta"] = _safe_float(line.split()[-1])
            elif line.startswith("_cell_angle_gamma"):
                cell["gamma"] = _safe_float(line.split()[-1])
            elif line.startswith("_chemical_formula_sum"):
                formula = line.split(None, 1)[1].strip().strip("'\"") if len(line.split(None, 1)) > 1 else ""
            elif line == "loop_":
                in_loop = True
                loop_headers = []
                atom_type_index = None
            elif in_loop and line.startswith("_"):
                loop_headers.append(line)
                if line in ("_atom_site_type_symbol", "_atom_site_label"):
                    atom_type_index = len(loop_headers) - 1
            elif in_loop:
                if atom_type_index is not None and loop_headers:
                    parts = line.split()
                    if len(parts) > atom_type_index:
                        token = parts[atom_type_index]
                        token = "".join(ch for ch in token if ch.isalpha()) or token
                        if token:
                            species.append(token)
                else:
                    in_loop = False

        species_counts = dict(Counter(species))
        result["species_counts"] = species_counts
        result["atom_count"] = sum(species_counts.values())
        result["formula"] = formula or _format_formula(species_counts)
        if any(value is not None for value in cell.values()):
            result["cell_parameters"] = cell
        if not result["formula"]:
            result["warnings"].append("No formula metadata found")
        if result["atom_count"] == 0:
            result["warnings"].append("No atom sites parsed from CIF loop")
        result["metadata"]["parsed_successfully"] = True
    except Exception as e:
        result["warnings"].append(f"CIF parse warning: {e}")
        result["metadata"]["parse_error"] = str(e)
    return _finalize_result(result)


def _inspect_poscar(path: Path) -> Dict[str, Any]:
    result = _base_result(path, "poscar_structure")
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
        if len(lines) < 8:
            result["warnings"].append("POSCAR file is shorter than expected")
            return _finalize_result(result)

        scale = _safe_float(lines[1])
        scale = scale if scale is not None else 1.0

        lattice: List[List[float]] = []
        for idx in range(2, 5):
            vec = [_safe_float(x) for x in lines[idx].split()[:3]]
            if len(vec) < 3 or any(v is None for v in vec):
                result["warnings"].append("Invalid lattice vector in POSCAR")
                return _finalize_result(result)
            lattice.append([float(v) * scale for v in vec])

        species_line = lines[5].split()
        counts_line = lines[6].split() if len(lines) > 6 else []

        if all(token.replace("-", "").isdigit() for token in species_line):
            counts_tokens = species_line
            species = [f"X{i+1}" for i in range(len(counts_tokens))]
        else:
            species = species_line
            counts_tokens = counts_line

        counts = []
        for token in counts_tokens:
            try:
                counts.append(int(float(token)))
            except Exception:
                break

        if not counts:
            result["warnings"].append("Could not parse POSCAR species counts")
            return _finalize_result(result)

        species_counts = {species[i] if i < len(species) else f"X{i+1}": counts[i] for i in range(len(counts))}
        result["species_counts"] = species_counts
        result["atom_count"] = sum(counts)
        result["formula"] = _format_formula(species_counts)
        result["cell_parameters"] = _lattice_summary(lattice)
        result["metadata"]["parsed_successfully"] = True
    except Exception as e:
        result["warnings"].append(f"POSCAR parse warning: {e}")
        result["metadata"]["parse_error"] = str(e)
    return _finalize_result(result)


def inspect_scientific_structure_file(filepath: str, workspace_dir: str | None = None) -> Dict[str, Any]:
    workspace = workspace_dir or str(Path(__file__).resolve().parent.parent)
    if not _is_safe_path(filepath, workspace):
        raise ScientificStructureInspectionError(
            f"Path traversal attempt: {filepath} is outside workspace"
        )

    path = Path(filepath)
    if not path.exists():
        raise ScientificStructureInspectionError(f"File not found: {filepath}")
    if path.is_dir():
        raise ScientificStructureInspectionError(f"Is a directory, not a file: {filepath}")

    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        raise ScientificStructureInspectionError(
            f"File too large: {size} bytes (max {MAX_FILE_SIZE})"
        )

    name = path.name
    ext = path.suffix.lower()
    if ext == ".xyz":
        return _inspect_xyz(path)
    if ext == ".cif":
        return _inspect_cif(path)
    if name in SCIENTIFIC_FILENAMES or ext == ".vasp":
        return _inspect_poscar(path)

    raise ScientificStructureInspectionError(
        f"Unsupported scientific structure file: {filepath}"
    )
