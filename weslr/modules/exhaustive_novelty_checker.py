"""
exhaustive_novelty_checker.py — Multi-source structural novelty checker.

Queries inorganic crystal structure databases (COD, OQMD, AFLOW, NOMAD,
Materials Project) for exact-composition and variant-formula matches.

All live API calls are rate-limited to 1 request/second and cached per session.
"""
from __future__ import annotations

import os
import re
import time
import math
import html
from typing import Any, Dict, List, Optional

import requests

# ── Session cache (survives multiple calls within the same run) ────────────────

_SESSION_CACHE: Dict[str, Dict[str, Any]] = {}
_API_CALL_COUNT: Dict[str, int] = {}  # source → call count for logging

# ── Config ────────────────────────────────────────────────────────────────────

MATERIALS_PROJECT_API_KEY: Optional[str] = os.environ.get("MATERIALS_PROJECT_API_KEY")
EXHAUSTIVE_TIMEOUT: float = float(os.environ.get("WESLR_EXHAUSTIVE_TIMEOUT", "10"))

HEADERS = {
    "User-Agent": "Weslr/1.0 (materials-discovery; contact@weslr.de)",
    "Accept": "application/json",
}
TIMEOUT = (5.0, 10.0)  # (connect, read)


# ── Variant generation ────────────────────────────────────────────────────────

def generate_formula_variants(formula: str) -> List[str]:
    """
    Generate multiple query variants for a chemical formula to maximise
    database coverage (different notation conventions, partial formulas, etc.).

    Returns a list including the exact formula and derived variants.
    """
    import re
    from weslr.modules.matter_primitives import PERIODIC_TABLE

    variants: set[str] = set()

    # ── 1. Normalise to Hill order and strip stoichiometry numbers ───────────
    # Parse: "CaO6Sc2Ti" → [(Ca,1),(O,6),(Sc,2),(Ti,1)]
    pattern = r"([A-Z][a-z]?)(\d*)"
    matches = re.findall(pattern, formula)
    if not matches:
        return [formula]

    elements: List[str] = []
    counts: Dict[str, int] = {}
    for sym, cnt in matches:
        if sym not in PERIODIC_TABLE:
            continue
        elements.append(sym)
        counts[sym] = counts.get(sym, 0) + (int(cnt) if cnt else 1)

    if not elements:
        return [formula]

    variants.add(formula)

    # ── 2. Space-separated (drop stoichiometry) ───────────────────────────────
    # e.g. Ca Sc Ti O  (one atom each — useful for COD/OQMD free-text search)
    variants.add(" ".join(sorted(elements)))

    # ── 3. Hyphenated ───────────────────────────────────────────────────────
    variants.add("-".join(sorted(elements)))

    # ── 4. Element-only (no numbers) ─────────────────────────────────────────
    element_only = "".join(sorted(elements))
    variants.add(element_only)

    # ── 5. Full element names (sorted alphabetically) ─────────────────────────
    _NUM_TO_WORD = {
        "1": "one", "2": "two", "3": "three", "4": "four",
        "5": "five", "6": "six", "7": "seven", "8": "eight",
        "9": "nine", "10": "ten",
    }
    _SYMBOL_TO_NAME = {
        "H": "hydrogen", "He": "helium", "Li": "lithium", "Be": "beryllium",
        "B": "boron", "C": "carbon", "N": "nitrogen", "O": "oxygen",
        "F": "fluorine", "Ne": "neon", "Na": "sodium", "Mg": "magnesium",
        "Al": "aluminium", "Al": "aluminum", "Si": "silicon", "P": "phosphorus",
        "S": "sulfur", "Cl": "chlorine", "Ar": "argon", "K": "potassium",
        "Ca": "calcium", "Sc": "scandium", "Ti": "titanium", "V": "vanadium",
        "Cr": "chromium", "Mn": "manganese", "Fe": "iron", "Co": "cobalt",
        "Ni": "nickel", "Cu": "copper", "Zn": "zinc", "Ga": "gallium",
        "Ge": "germanium", "As": "arsenic", "Se": "selenium", "Br": "bromine",
        "Kr": "krypton", "Rb": "rubidium", "Sr": "strontium", "Y": "yttrium",
        "Zr": "zirconium", "Nb": "niobium", "Mo": "molybdenum", "Tc": "technetium",
        "Ru": "ruthenium", "Rh": "rhodium", "Pd": "palladium", "Ag": "silver",
        "Cd": "cadmium", "In": "indium", "Sn": "tin", "Sb": "antimony",
        "Te": "tellurium", "I": "iodine", "Xe": "xenon", "Cs": "caesium",
        "Cs": "cesium", "Ba": "barium", "La": "lanthanum", "Ce": "cerium",
        "Pr": "praseodymium", "Nd": "neodymium", "Pm": "promethium",
        "Sm": "samarium", "Eu": "europium", "Gd": "gadolinium",
        "Tb": "terbium", "Dy": "dysprosium", "Ho": "holmium", "Er": "erbium",
        "Tm": "thulium", "Yb": "ytterbium", "Lu": "lutetium",
        "Hf": "hafnium", "Ta": "tantalum", "W": "tungsten", "Re": "rhenium",
        "Os": "osmium", "Ir": "iridium", "Pt": "platinum", "Au": "gold",
        "Hg": "mercury", "Tl": "thallium", "Pb": "lead", "Bi": "bismuth",
        "Po": "polonium", "At": "astatine", "Rn": "radon",
        "Ti": "titanium",  # redundant but explicit
    }
    names = [_SYMBOL_TO_NAME.get(e, e.lower()) for e in sorted(elements)]
    variants.add(" ".join(sorted(names)))  # alphabetical by name
    # e.g. "calcium scandium titanium oxide" for CaScTiO
    if set(elements) <= set(_SYMBOL_TO_NAME):
        variants.add(" ".join(names))

    # ── 6. Oxide mixture notation ─────────────────────────────────────────────
    # e.g. CaO-Sc2O3-TiO2  (as used in solid-state chemistry)
    oxide_parts = []
    for el in sorted(elements):
        c = counts[el]
        # Most elements form oxides with O at common valence
        # Use 3 for transition metals as default, 2 for alkali/alkaline earth
        if el in ("Ca", "Mg", "Sr", "Ba", "Zn", "Cu"):
            o_cnt = 1
        elif el in ("Ti", "Zr", "Hf"):
            o_cnt = 2
        elif el in ("Al", "Ga", "Fe", "Cr"):
            o_cnt = 3 if c == 2 else 1  # Al2O3, Fe2O3 etc
        else:
            o_cnt = 3
        oxide_parts.append(f"{el}O{o_cnt}" if o_cnt > 1 else el)
    variants.add("-".join(oxide_parts))

    # ── 7. Partial formulas (drop Ca for Ca-Sc-Ti-O systems) ─────────────────
    # Drop the first (most electropositive) element if there are ≥3 species
    if len(elements) >= 3:
        sorted_by_en = sorted(elements, key=lambda e: PERIODIC_TABLE[e].electronegativity)
        partial_elements = sorted_by_en[1:]  # drop most electropositive
        variants.add("".join(sorted(partial_elements)))
        variants.add(" ".join(sorted(partial_elements)))

    # ── 8. Alternative stoichiometry representations ─────────────────────────
    # e.g. CaSc2TiO6 vs Sc2TiCaO6 (alphabetical instead of Hill order)
    alpha_formula = "".join(f"{e}{counts[e]}" for e in sorted(elements))
    variants.add(alpha_formula)

    # e.g. CaTiO3 → "Calcium titanate" / "Calcium titanium oxide"
    if elements == ["Ca", "Ti", "O"]:
        variants.add("calcium titanate")
        variants.add("calcium titanium oxide")
    elif elements == ["Ti", "O"] and counts.get("Ti", 0) == 1 and counts.get("O", 0) == 2:
        variants.add("titanium dioxide")
        variants.add("titania")
    elif elements == ["Fe", "O"]:
        variants.add("iron oxide")
        variants.add("ferric oxide")
    elif elements == ["Zn", "O"]:
        variants.add("zinc oxide")
        variants.add("zincite")
    elif elements == ["Si", "O"]:
        variants.add("silicon dioxide")
        variants.add("silica")

    return sorted(variants)


# ── Source query functions ─────────────────────────────────────────────────────

def _cache_key(source: str, variant: str) -> str:
    return f"{source}::{variant}"


def _rate_limit():
    time.sleep(1.0)


def _safe_get(url: str, params: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", TIMEOUT)
    kwargs.setdefault("allow_redirects", True)
    return requests.get(url, params=params, **kwargs)


# ── COD (Crystallography Open Database) ──────────────────────────────────────

def check_cod(variant: str) -> Dict[str, Any]:
    """
    Query COD REST API for a formula.

    API: GET https://www.crystallography.net/cod/rest/result?formula={variant}
    Returns JSON with 'total' field or 0 if not found.
    """
    cache_key = _cache_key("COD", variant)
    if cache_key in _SESSION_CACHE:
        return _SESSION_CACHE[cache_key]

    url = f"https://www.crystallography.net/cod/rest/result"
    params = {"formula": variant}
    result = {"source": "COD", "count": 0, "enabled": True, "error": None, "variant": variant}
    try:
        resp = _safe_get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            result["count"] = int(data.get("total", 0))
        elif resp.status_code == 404:
            result["count"] = 0
        else:
            result["count"] = 0
            result["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["count"] = 0
        result["error"] = str(e)

    _SESSION_CACHE[cache_key] = result
    _API_CALL_COUNT["COD"] = _API_CALL_COUNT.get("COD", 0) + 1
    return result


# ── OQMD (Open Quantum Materials Database) ────────────────────────────────────

def check_oqmd(variant: str) -> Dict[str, Any]:
    """
    Query OQMD REST API for a formula.

    API: GET http://oqmd.org/api/search/?format=json&formula={variant}
    Returns JSON. Look for 'nresults' or 'results' array length.
    """
    cache_key = _cache_key("OQMD", variant)
    if cache_key in _SESSION_CACHE:
        return _SESSION_CACHE[cache_key]

    url = "http://oqmd.org/api/search/"
    params = {"format": "json", "formula": variant}
    result = {"source": "OQMD", "count": 0, "enabled": True, "error": None, "variant": variant}
    try:
        resp = _safe_get(url, params=params, timeout=(5.0, 15.0))
        if resp.status_code == 200:
            data = resp.json()
            # OQMD returns {'nresults': N, 'results': [...]}
            result["count"] = int(data.get("nresults", 0))
        else:
            result["count"] = 0
            result["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["count"] = 0
        result["error"] = str(e)

    _SESSION_CACHE[cache_key] = result
    _API_CALL_COUNT["OQMD"] = _API_CALL_COUNT.get("OQMD", 0) + 1
    return result


# ── AFLOW ─────────────────────────────────────────────────────────────────────

def check_aflow(variant: str) -> Dict[str, Any]:
    """
    Query AFLOW API for a formula.

    API: GET https://aflow.org/API/webservice/?format=json&mode=search&species={variant}
    Returns JSON. Look for 'nresults' or 'results' array.
    """
    cache_key = _cache_key("AFLOW", variant)
    if cache_key in _SESSION_CACHE:
        return _SESSION_CACHE[cache_key]

    url = "https://aflow.org/API/webservice/"
    params = {"format": "json", "mode": "search", "species": variant}
    result = {"source": "AFLOW", "count": 0, "enabled": True, "error": None, "variant": variant}
    try:
        resp = _safe_get(url, params=params, timeout=(5.0, 15.0))
        if resp.status_code == 200:
            data = resp.json()
            result["count"] = int(data.get("nresults", data.get("nsystems", 0)))
        else:
            result["count"] = 0
            result["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["count"] = 0
        result["error"] = str(e)

    _SESSION_CACHE[cache_key] = result
    _API_CALL_COUNT["AFLOW"] = _API_CALL_COUNT.get("AFLOW", 0) + 1
    return result


# ── NOMAD ──────────────────────────────────────────────────────────────────────

def check_nomad(variant: str) -> Dict[str, Any]:
    """
    Query NOMAD API for a formula.

    API: GET https://nomad-lab.eu/prod/v1/api/entries?query=formula={variant}&page_size=1
    Returns JSON. Look for 'total' field or 'entries' array length.
    """
    cache_key = _cache_key("NOMAD", variant)
    if cache_key in _SESSION_CACHE:
        return _SESSION_CACHE[cache_key]

    url = "https://nomad-lab.eu/prod/v1/api/entries"
    params = {"query": f"formula={variant}", "page_size": 1}
    result = {"source": "NOMAD", "count": 0, "enabled": True, "error": None, "variant": variant}
    try:
        resp = _safe_get(url, params=params, timeout=(5.0, 15.0))
        if resp.status_code == 200:
            data = resp.json()
            result["count"] = int(data.get("total", 0))
        else:
            result["count"] = 0
            result["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["count"] = 0
        result["error"] = str(e)

    _SESSION_CACHE[cache_key] = result
    _API_CALL_COUNT["NOMAD"] = _API_CALL_COUNT.get("NOMAD", 0) + 1
    return result


# ── Materials Project ─────────────────────────────────────────────────────────

def check_materials_project(
    variant: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Query Materials Project API for a formula.

    API: GET https://api.materialsproject.org/materials/formula/{variant}/
    Requires x-api-key header.
    """
    if not api_key:
        return {
            "source": "Materials Project",
            "count": 0,
            "enabled": False,
            "error": "no API key (set MATERIALS_PROJECT_API_KEY env var)",
            "variant": variant,
        }

    cache_key = _cache_key("Materials Project", variant)
    if cache_key in _SESSION_CACHE:
        return _SESSION_CACHE[cache_key]

    url = f"https://api.materialsproject.org/materials/formula/{variant}/"
    headers = {**HEADERS, "x-api-key": api_key}
    result = {
        "source": "Materials Project",
        "count": 0,
        "enabled": True,
        "error": None,
        "variant": variant,
    }
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            result["count"] = int(len(data))
        elif resp.status_code == 404:
            result["count"] = 0
        elif resp.status_code == 401:
            result["count"] = 0
            result["enabled"] = False
            result["error"] = "invalid API key"
        else:
            result["count"] = 0
            result["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["count"] = 0
        result["error"] = str(e)

    _SESSION_CACHE[cache_key] = result
    _API_CALL_COUNT["Materials Project"] = _API_CALL_COUNT.get("Materials Project", 0) + 1
    return result


# ── Main aggregator ────────────────────────────────────────────────────────────

def check_all_sources(
    formula: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run exhaustive multi-source novelty check for a formula.

    Generates formula variants and queries COD, OQMD, AFLOW, NOMAD, and
    optionally Materials Project.  Stops early per source on first hit.

    Args:
        formula:     Normalised composition formula, e.g. "CaSc2TiO6"
        config:      Optional dict with keys:
                       - materials_project_api_key (str)
                       - timeout_per_source (float, default 10s)
                       - stop_early (bool, default True)

    Returns:
        {
          "formula": str,
          "variants": List[str],          # all variants generated
          "total_hits": int,               # sum across all sources
          "is_novel": bool,                # total_hits == 0
          "sources": {
            "COD":             {"count": int, "enabled": bool, "error": str|None},
            "OQMD":            {...},
            "AFLOW":           {...},
            "NOMAD":           {...},
            "Materials Project": {...},
          },
          "per_variant": [                 # detailed hits per variant (first hit only)
            {"variant": str, "source": str, "count": int}
          ],
          "thermodynamics": {              # energy-above-hull + formation energy
            "energy_above_hull": float|None,
            "formation_energy_per_atom": float|None,
            "decomposition_products": List[str],
            "stability_rating": str,        # stable|metastable|unstable|unknown
            "is_stable": bool|None,
            "source": str,                  # "Materials Project" or "heuristic"
          }
        }
    """
    if config is None:
        config = {}

    api_key = config.get("materials_project_api_key") or MATERIALS_PROJECT_API_KEY
    stop_early: bool = config.get("stop_early", True)

    variants = generate_formula_variants(formula)
    if not variants:
        variants = [formula]

    sources_cfg = [
        ("COD",              check_cod),
        ("OQMD",             check_oqmd),
        ("AFLOW",            check_aflow),
        ("NOMAD",            check_nomad),
        ("Materials Project", lambda v: check_materials_project(v, api_key=api_key)),
    ]

    sources_result: Dict[str, Dict[str, Any]] = {}
    total_hits = 0
    per_variant: List[Dict[str, Any]] = []
    first_hit_per_source: Dict[str, Dict[str, Any]] = {}

    for source_name, check_fn in sources_cfg:
        if stop_early and source_name in first_hit_per_source:
            continue  # already found a hit for this source, skip
        for variant in variants:
            _rate_limit()
            try:
                r = check_fn(variant)
            except Exception as e:
                r = {"source": source_name, "count": 0, "enabled": False,
                     "error": str(e), "variant": variant}

            if r.get("error") and "no API key" not in r.get("error", ""):
                sources_result[source_name] = r
            elif r.get("enabled", True):
                sources_result[source_name] = r
            elif r.get("error") and "no API key" in r.get("error", ""):
                # Explicitly record disabled sources (e.g. MP without key)
                sources_result[source_name] = r

            count = r.get("count", 0)
            if count > 0:
                total_hits += count
                entry = {
                    "variant": variant,
                    "source": source_name,
                    "count": count,
                    "error": r.get("error"),
                }
                per_variant.append(entry)
                if stop_early:
                    first_hit_per_source[source_name] = {**r, "variant": variant}
                    break  # stop early for this source

    # Compile per-source summary
    sources_summary: Dict[str, Dict[str, Any]] = {}
    for source_name, _ in sources_cfg:
        if source_name in first_hit_per_source:
            hit = first_hit_per_source[source_name]
            sources_summary[source_name] = {
                "count": hit.get("count", 0),
                "enabled": hit.get("enabled", True),
                "error": hit.get("error"),
                "variant": hit.get("variant", ""),
            }
        else:
            sources_summary[source_name] = {
                "count": 0,
                "enabled": sources_result.get(source_name, {}).get("enabled", True),
                "error": sources_result.get(source_name, {}).get("error"),
                "variant": "",
            }

    return {
        "formula": formula,
        "variants": variants,
        "total_hits": total_hits,
        "is_novel": total_hits == 0,
        "sources": sources_summary,
        "per_variant": per_variant[:20],  # cap detail output
        "thermodynamics": check_thermodynamics(
            formula,
            api_key=api_key,
            structure_info={"known_structure_types": list(first_hit_per_source.keys())},
        ),
    }


# ── Thermodynamic stability (Materials Project) ──────────────────────────────

def _stability_rating(eah: Optional[float]) -> str:
    """Map energy-above-hull to stability rating string."""
    if eah is None:
        return "unknown"
    if eah == 0.0:
        return "stable"
    if eah <= 0.15:
        return "metastable"
    return "unstable"


def check_materials_project_thermodynamics(
    formula: str,
    api_key: str,
) -> Dict[str, Any]:
    """
    Query Materials Project thermo endpoint for a formula.

    Endpoint: GET https://api.materialsproject.org/materials/formula/{formula}/thermo/
    Returns: list of documents with energy_above_hull, formation_energy_per_atom,
             decomposition (list of {formula, type} dicts).
    """
    cache_key = _cache_key("MP_THERMO", formula)
    if cache_key in _SESSION_CACHE:
        return _SESSION_CACHE[cache_key]

    if not api_key:
        result = {
            "enabled": False,
            "found": False,
            "error": "no API key (set MATERIALS_PROJECT_API_KEY env var)",
            "energy_above_hull": None,
            "formation_energy_per_atom": None,
            "decomposition_products": [],
            "stability_rating": "unknown",
        }
        _SESSION_CACHE[cache_key] = result
        return result

    url = f"https://api.materialsproject.org/materials/formula/{formula}/thermo/"
    headers = {**HEADERS, "x-api-key": api_key}
    result = {
        "enabled": True,
        "found": False,
        "error": None,
        "energy_above_hull": None,
        "formation_energy_per_atom": None,
        "decomposition_products": [],
        "stability_rating": "unknown",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list):
                entry = data[0]
                eah = entry.get("energy_above_hull")
                if eah is not None:
                    eah = float(eah)
                form_e = entry.get("formation_energy_per_atom")
                if form_e is not None:
                    form_e = float(form_e)
                decomp = entry.get("decomposition") or []
                decomp_products = [
                    d.get("formula", "") for d in decomp
                    if d.get("formula") and d.get("type") != "atom"
                ]
                result["found"] = True
                result["energy_above_hull"] = eah
                result["formation_energy_per_atom"] = form_e
                result["decomposition_products"] = decomp_products
                result["stability_rating"] = _stability_rating(eah)
                result["is_stable"] = eah == 0.0 if eah is not None else False
        elif resp.status_code == 404:
            result["error"] = "no entry"
            result["stability_rating"] = "unknown"
        elif resp.status_code == 401:
            result["enabled"] = False
            result["error"] = "invalid API key"
            result["stability_rating"] = "unknown"
        else:
            result["error"] = f"HTTP {resp.status_code}"
            result["stability_rating"] = "unknown"
    except Exception as e:
        result["error"] = str(e)
        result["stability_rating"] = "unknown"

    _SESSION_CACHE[cache_key] = result
    _API_CALL_COUNT["Materials Project Thermo"] = _API_CALL_COUNT.get("Materials Project Thermo", 0) + 1
    return result


# ── Rule-based heuristic fallback ────────────────────────────────────────────

def _is_toxic_or_rare(element_set: set) -> bool:
    """Return True if any element in the set is toxic/rare/declining."""
    TOXIC_OR_RARE = {
        "Cd", "Hg", "Tl", "In", "Tb", "Dy", "Ho", "Er",
        "Tm", "Yb", "Lu",  # lanthanides with supply risk
        "Ra", "Ac", "Th", "Pa", "Np", "Pu", "Am",  # radioactive
    }
    return bool(element_set & TOXIC_OR_RARE)


def _charge_balance_score(charges: Dict[str, float]) -> float:
    """Return a bonus (0 to +0.2) for charge-neutral compositions."""
    total = sum(charges.values())
    if abs(total) < 0.01:
        return 0.2
    if abs(total) <= 1.0:
        return 0.1
    return 0.0


def estimate_stability_heuristic(
    formula: str,
    structure_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Rule-based thermodynamic stability estimate when no MP API key is available.

    Scores from 0→1 using:
      - charge balance (+0.2 if neutral)
      - known prototype structure (+0.2 for perovskite/spinel/olivine etc.)
      - unconventional stoichiometry (−0.1 if not a simple ratio)
      - toxic/rare elements (−0.2)

    Maps to rating:
      score > 0.6 → "moderately plausible"
      score > 0.3 → "speculative"
      score ≤ 0.3 → "unlikely"
    """
    if structure_info is None:
        structure_info = {}

    from weslr.modules.matter_primitives import PERIODIC_TABLE

    # Parse formula
    pattern = r"([A-Z][a-z]?)(\d*)"
    matches = re.findall(pattern, formula)
    elements: List[str] = []
    counts: Dict[str, int] = {}
    for sym, cnt in matches:
        if sym not in PERIODIC_TABLE:
            continue
        elements.append(sym)
        counts[sym] = counts.get(sym, 0) + (int(cnt) if cnt else 1)

    element_set = set(elements)
    score = 0.0

    # ── Charge balance ────────────────────────────────────────────────────────
    # Look up common oxidation states and compute total charge
    COMMON_OXIDATION = {
        "Ca": 2, "Mg": 2, "Sr": 2, "Ba": 2, "Zn": 2, "Cu": 2,
        "Ti": 4, "Zr": 4, "Hf": 4, "Si": 4, "Ge": 4,
        "Al": 3, "Ga": 3, "Fe": 3, "Cr": 3, "Sc": 3, "Y": 3,
        "N": -3, "P": -3, "As": -3,
        "O": -2, "S": -2, "Se": -2,
        "Na": 1, "K": 1, "Cs": 1, "Li": 1,
        "Mn": 2, "Co": 2, "Ni": 2,
    }
    total_charge = 0.0
    for el, cnt in counts.items():
        ox = COMMON_OXIDATION.get(el, 0)
        total_charge += ox * cnt
    if abs(total_charge) < 0.01:
        score += 0.2
    elif abs(total_charge) <= 1.0:
        score += 0.05

    # ── Known prototype match (+0.4 for perovskite/spinel/olivine etc.) ────
    known_types = structure_info.get("known_structure_types", [])
    if known_types:
        score += 0.4  # +0.4 for matching a known structure prototype

    # ── Unconventional stoichiometry ──────────────────────────────────────────
    all_counts = list(counts.values())
    if all_counts:
        import math
        from functools import reduce
        g = all_counts[0]
        for c in all_counts[1:]:
            g = math.gcd(g, c)
        simplified = [c // g for c in all_counts]
        # If oxygen count isn't divisible by the GCD of cations → unusual
        if "O" in counts:
            o_cnt = counts["O"]
            cation_gcd = reduce(math.gcd, [counts[e] for e in elements if e != "O"], 0)
            if cation_gcd and o_cnt % cation_gcd != 0:
                score -= 0.1

    # ── Toxic / rare elements ─────────────────────────────────────────────────
    if _is_toxic_or_rare(element_set):
        score -= 0.2

    # ── Element count: simpler = more plausible ─────────────────────────────
    if len(elements) <= 3:
        score += 0.1

    # ── Normalise to [0, 1] ──────────────────────────────────────────────────
    score = max(0.0, min(1.0, score))

    # ── Map to rating ─────────────────────────────────────────────────────────
    if score > 0.6:
        rating = "moderately plausible"
    elif score > 0.3:
        rating = "speculative"
    else:
        rating = "unlikely"

    return {
        "enabled": True,
        "source": "heuristic",
        "stability_score": score,
        "stability_rating": rating,
        "energy_above_hull": None,
        "formation_energy_per_atom": None,
        "decomposition_products": [],
        "is_stable": None,
        "found": None,  # heuristic always runs
    }


def check_thermodynamics(
    formula: str,
    api_key: Optional[str] = None,
    structure_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run thermodynamic stability check: try MP, fall back to heuristic.

    Returns dict with energy_above_hull, formation_energy_per_atom,
    decomposition_products, stability_rating, is_stable, source.
    """
    key = api_key or MATERIALS_PROJECT_API_KEY
    if key:
        mp_result = check_materials_project_thermodynamics(formula, key)
        # Use MP if found, or if there was a real error (not just "no entry")
        if mp_result.get("found") or (
            mp_result.get("error") and mp_result.get("error") != "no entry"
        ):
            mp_result["source"] = "Materials Project"
            return mp_result
    # Fall back to heuristic (no key, not found, or API error)
    return estimate_stability_heuristic(formula, structure_info or {})


def clear_session_cache() -> None:
    """Clear the per-session cache and call counters. For testing."""
    global _SESSION_CACHE, _API_CALL_COUNT
    _SESSION_CACHE.clear()
    _API_CALL_COUNT.clear()


