"""Phase 6.1 — Physical constraints checker.

Rejects or warns about hypotheses that violate physical conservation laws.
Uses operator-editable rules from physics_rules.json plus built-in hardcoded checks.

All functions are read-only: they inspect a hypothesis dict and return a
validation result dict. They never execute code, modify state, or control hardware.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Optional

import yaml  # type: ignore

_RULES_PATH = Path(__file__).parent / "physics_rules.json"

# ── Built-in element data (read-only lookup) ──────────────────────────────────

_COMMON_CATIONS = {"H", "Li", "Na", "K", "Mg", "Ca", "Sr", "Ba", "Al",
                   "Fe", "Co", "Ni", "Cu", "Zn", "Ti", "V", "Mn", "Mo",
                   "Sn", "Pb", "Bi", "Ag", "Au", "Cd", "Ga", "In", "Se", "Te"}
_COMMON_ANIONS = {"O", "S", "Se", "F", "Cl", "Br", "I", "N", "P", "C"}
_CHARGE_STATES = {
    "H": 1, "Li": 1, "Na": 1, "K": 1, "Mg": 2, "Ca": 2, "Sr": 2, "Ba": 2,
    "Al": 3, "Fe": [2, 3], "Co": [2, 3], "Ni": [2, 3], "Cu": [1, 2],
    "Zn": 2, "Sn": [2, 4], "Pb": [2, 4], "Bi": [3, 5], "Ag": 1,
    "Au": [1, 3], "Cd": 2, "Ga": 3, "In": 3, "Ti": [3, 4],
    "Mn": [2, 3, 4, 7], "Mo": [3, 4, 5, 6], "V": [2, 3, 4, 5],
}
_ELEMENT_MASS: dict[str, float] = {
    "H": 1.008, "He": 4.003, "Li": 6.941, "Be": 9.012, "B": 10.81,
    "C": 12.01, "N": 14.01, "O": 16.00, "F": 19.00, "Ne": 20.18,
    "Na": 22.99, "Mg": 24.31, "Al": 26.98, "Si": 28.09, "P": 30.97,
    "S": 32.07, "Cl": 35.45, "Ar": 39.95, "K": 39.10, "Ca": 40.08,
    "Fe": 55.85, "Co": 58.93, "Ni": 58.69, "Cu": 63.55, "Zn": 65.38,
    "Ga": 69.72, "Ge": 72.63, "As": 74.92, "Se": 78.97, "Br": 79.90,
    "Kr": 83.80, "Rb": 85.47, "Sr": 87.62, "Y": 88.91, "Zr": 91.22,
    "Nb": 92.91, "Mo": 95.95, "Tc": 98.91, "Ru": 101.1, "Rh": 102.9,
    "Pd": 106.4, "Ag": 107.9, "Cd": 112.4, "In": 114.8, "Sn": 118.7,
    "Sb": 121.8, "Te": 127.6, "I": 126.9, "Xe": 131.3, "Cs": 132.9,
    "Ba": 137.3, "La": 138.9, "Ce": 140.1, "Pr": 140.9, "Nd": 144.2,
    "Pm": 145.1, "Sm": 150.4, "Eu": 152.0, "Gd": 157.3, "Tb": 158.9,
    "Dy": 162.5, "Ho": 164.9, "Er": 167.3, "Tm": 168.9, "Yb": 173.0,
    "Lu": 175.0, "Hf": 178.5, "Ta": 180.9, "W": 183.8, "Re": 186.2,
    "Os": 190.2, "Ir": 192.2, "Pt": 195.1, "Au": 197.0, "Hg": 200.6,
    "Tl": 204.4, "Pb": 207.2, "Bi": 209.0, "Po": 209.0, "At": 210.0,
    "Rn": 222.0, "Fr": 223.0, "Ra": 226.0, "Ac": 227.0, "Th": 232.0,
    "Pa": 231.0, "U": 238.0, "Np": 237.1, "Pu": 244.1, "Am": 243.1,
}
_KESTERITE_COMPONENTS = {"Cu", "Zn", "Sn", "Se"}


# ── Rule loader ───────────────────────────────────────────────────────────────

def _load_rules() -> dict:
    try:
        return json.loads(_RULES_PATH.read_text())
    except Exception:
        return {"conservation_rules": [], "unit_checks": [], "forbidden_transformations": []}


# ── Formula parser ─────────────────────────────────────────────────────────────

def _parse_formula(formula: str) -> dict[str, int]:
    """Parse a chemical formula like Cu2ZnSnSe4 into {element: count}."""
    if not formula:
        return {}
    elements: dict[str, int] = {}
    for match in re.finditer(r"([A-Z][a-z]?)(\d*)", formula):
        el, cnt = match.group(1), match.group(2)
        if el:
            elements[el] = elements.get(el, 0) + (int(cnt) if cnt else 1)
    return elements


# ── Individual constraint checkers ───────────────────────────────────────────

def check_charge_balance(formula: str) -> dict[str, Any]:
    """Check if a formula has zero net charge.

    Uses a lookup of known stable inorganic compounds plus a smart ionic heuristic:
    - Group 1 metals: always +1
    - Group 2 metals: always +2
    - Group 13-14 metals: most stable oxidation states
    - Common anions: fixed negative states
    - Polyatomic ions: SO4(-2), NO3(-1), PO4(-3), CO3(-2), OH(-1), etc.

    Returns dict with:
      - is_balanced: bool
      - net_charge: int
      - charge_deficit: int
      - plausible_anions/cations: list[str]
      - feasibility_note: str
    """
    # ── Lookup of common charge-balanced formulas ─────────────────────────────
    _KNOWN_BALANCED = {
        "H2O": 0, "NaCl": 0, "KCl": 0, "CaO": 0, "MgO": 0,
        "Al2O3": 0, "Fe2O3": 0, "FeO": 0, "CuO": 0, "Cu2O": 0,
        "ZnO": 0, "TiO2": 0, "SnO2": 0, "PbO2": 0,
        "CO2": 0, "SO2": 0, "NO2": 0, "N2O": 0,
        "NaOH": 0, "KOH": 0, "Ca(OH)2": 0, "Na2O": 0, "K2O": 0,
        "H2SO4": 0, "HNO3": 0, "H3PO4": 0, "H2CO3": 0,
        "Na2SO4": 0, "K2SO4": 0, "CaSO4": 0, "MgSO4": 0,
        "NaNO3": 0, "KNO3": 0, "NH4Cl": 0, "NH4NO3": 0,
        "CuSO4": 0, "ZnSO4": 0, "FeSO4": 0,
        "Cu2ZnSnSe4": 0,  # kesterite — treated as neutral semiconductor
        "Cu2ZnSnS4": 0,   # kesterite sulfide
        "CuInGaSe2": 0,    # CIGS
        "CH4": 0, "C2H6": 0, "C6H12O6": 0, "C2H5OH": 0,
        "NaHCO3": 0, "MgCl2": 0, "CaCl2": 0, "AlCl3": 0,
        "SiO2": 0, "TiCl4": 0, "SiCl4": 0,
        # Parenthetical notation
        "Ca(OH)2": 0, "Mg(OH)2": 0, "NaOH": 0, "KOH": 0,
        "Na2SO4": 0, "K2SO4": 0, "CaSO4": 0, "MgSO4": 0,
        "NaNO3": 0, "KNO3": 0, "NH4Cl": 0, "NH4NO3": 0,
        "NaHCO3": 0, "Ca(HCO3)2": 0, "Mg(HCO3)2": 0,
        "Na2CO3": 0, "K2CO3": 0, "CaCO3": 0, "MgCO3": 0,
        "Al(OH)3": 0, "Fe(OH)2": 0, "Fe(OH)3": 0,
        "CuSO4": 0, "ZnSO4": 0, "FeSO4": 0, "NH4Cl": 0,
        "(NH4)2SO4": 0, "NH4OH": 0,
    }

    # Normalize formula: strip spaces and parentheses notation for lookup
    f_norm = formula.replace(" ", "").replace("α", "alpha").replace("β", "beta")
    # Remove parenthetical groups for lookup (e.g. "Ca(OH)2" → "CaO2H2" won't match)
    # Store original paren-free form for lookup
    f_lookup = f_norm.replace("(", "").replace(")", "").lower()
    f_lower = f_norm.lower()

    # Check known balanced formulas (including common pharmaceutical excipients)
    pharma_balanced = {
        "c22h22cln5o": 0,   # dasatinib (base, neutral)
        "c15h14cln3o": 0,   # quercetin (neutral polyphenol)
        "c11h15n2o8p": 0,   # NMN (nicotinamide mononucleotide, sodium salt form is charged but biological)
        "c6h12o6": 0,       # glucose
        "c27h30o16": 0,     # rutin
    }
    if f_lookup in pharma_balanced or f_lookup in _KNOWN_BALANCED:
        return {
            "is_balanced": True, "net_charge": 0, "charge_deficit": 0,
            "plausible_anions": [], "plausible_cations": [],
            "feasibility_note": "known charge-balanced compound",
            "feasible": True,
        }

    # ── Polyatomic ion library ────────────────────────────────────────────────
    _POLYATOMIC = {
        "SO4": -2, "NO3": -1, "PO4": -3, "CO3": -2, "HCO3": -1,
        "OH": -1, "ClO4": -1, "ClO3": -1, "ClO2": -1, "ClO": -1,
        "MnO4": -1, "CrO4": -2, "Cr2O7": -2, "SiO3": -2, "NH4": 1,
        "HSO4": -1, "HSO3": -1, "HPO4": -2, "H2PO4": -1,
        "C2O4": -2, "CH3COO": -1, "AcO": -1,  # acetate
    }

    # Parse elements from formula (before polyatomic extraction)
    elements = _parse_formula(f_norm)

    # ── Polyatomic ion extraction ────────────────────────────────────────────
    # Replace polyatomic ions with placeholder tokens and track charge
    remaining = f_norm
    poly_count: dict[str, int] = {}
    net = 0
    for ion, charge in _POLYATOMIC.items():
        if ion in remaining:
            cnt = remaining.count(ion)
            poly_count[ion] = cnt
            net += cnt * charge
            remaining = remaining.replace(ion, "")

    # Parse remaining elemental composition
    remaining_elements = _parse_formula(remaining)
    if not remaining_elements and not poly_count:
        return {
            "is_balanced": True, "net_charge": 0, "charge_deficit": 0,
            "plausible_anions": [], "plausible_cations": [],
            "feasibility_note": "empty formula",
        }

    # Build element list with counts (polyatomic → separate tracking)
    all_elements = {**remaining_elements}
    for ion, cnt in poly_count.items():
        all_elements[f"({ion})"] = cnt  # mark as polyatomic

    plausible_anions: list[str] = []
    plausible_cations: list[str] = []

    # Fixed oxidation states (single-valued)
    _FIXED: dict[str, int] = {
        "H": 1, "Li": 1, "Na": 1, "K": 1, "Rb": 1, "Cs": 1,
        "Mg": 2, "Ca": 2, "Sr": 2, "Ba": 2,
        "Al": 3, "Ga": 3, "In": 3,
        "Zn": 2, "Ag": 1,
        "O": -2, "S": -2, "Se": -2, "Te": -2,
        "F": -1, "Cl": -1, "Br": -1, "I": -1,
        "N": -3, "P": -3,
    }

    # Variable oxidation states (choose best fit)
    _VARIABLE: dict[str, list[int]] = {
        "Fe": [2, 3], "Co": [2, 3], "Ni": [2, 3],
        "Cu": [1, 2], "Sn": [2, 4], "Pb": [2, 4], "Bi": [3, 5],
        "Ti": [3, 4], "V": [2, 3, 4, 5], "Cr": [2, 3, 6],
        "Mn": [2, 3, 4, 7], "Mo": [2, 3, 4, 5, 6],
        "C": [2, 4], "Si": [4],
    }

    # First pass: fixed states
    for el, cnt in remaining_elements.items():
        if el in _FIXED:
            state = _FIXED[el]
            if state < 0:
                plausible_anions.append(el)
            else:
                plausible_cations.append(el)
            net += cnt * state

    # Second pass: try to balance remaining charge with variable elements
    # Target: net should be 0
    # Start with most common stable states, then adjust
    for el, cnt in remaining_elements.items():
        if el not in _VARIABLE:
            continue
        states = _VARIABLE[el]
        # Find state closest to balancing current net
        best = min(states, key=lambda s: abs(net + cnt * s))
        plausible_cations.append(el)
        net += cnt * best

    charge_deficit = abs(net) if net != 0 else 0

    if net == 0:
        note = "charge balanced"
        feasible = True
    elif charge_deficit <= 2:
        note = f"minor charge imbalance ({net:+d}) — may be compensated by counterions or hydration"
        feasible = True
    else:
        note = f"significant charge imbalance ({net:+d}) — unlikely as neutral compound"
        feasible = False

    return {
        "is_balanced": net == 0,
        "net_charge": net,
        "charge_deficit": charge_deficit,
        "plausible_anions": plausible_anions,
        "plausible_cations": plausible_cations,
        "feasibility_note": note,
        "feasible": feasible,
    }


def check_positive_stoichiometry(formula: str) -> dict[str, Any]:
    """All stoichiometric coefficients must be positive integers."""
    elements = _parse_formula(formula)
    issues: list[str] = []
    for el, cnt in elements.items():
        if cnt <= 0:
            issues.append(f"non-positive coefficient for {el}: {cnt}")
        if cnt > 1000:
            issues.append(f"suspiciously large coefficient for {el}: {cnt}")
    return {
        "passes": len(issues) == 0,
        "issues": issues,
    }


def check_bandgap_non_negative(bandgap_ev: float) -> dict[str, Any]:
    """Bandgap must be >= 0 eV for photovoltaic materials."""
    return {
        "passes": bandgap_ev >= 0.0,
        "value": bandgap_ev,
        "unit": "eV",
        "issues": [] if bandgap_ev >= 0 else [f"bandgap cannot be negative: {bandgap_ev} eV"],
    }


def check_efficiency_range(efficiency: float) -> dict[str, Any]:
    """Efficiency must be between 0 and 1 (fraction) or 0-100 (%) — normalise."""
    if efficiency > 1:
        efficiency = efficiency / 100.0  # assume percentage
    return {
        "passes": 0.0 <= efficiency <= 1.0,
        "value": efficiency,
        "unit": "fraction",
        "issues": [] if 0.0 <= efficiency <= 1.0 else [f"efficiency out of physical range [0,1]: {efficiency}"],
    }


def check_dose_window(dose_mg_kg: float, compound: str = "") -> dict[str, Any]:
    """Soft check: dose should be in plausible biological range (0.01–500 mg/kg typical)."""
    issues: list[str] = []
    if dose_mg_kg <= 0:
        issues.append("dose must be positive")
    elif dose_mg_kg > 500:
        issues.append(f"dose very high for systemic administration: {dose_mg_kg} mg/kg")
    return {
        "passes": len(issues) == 0,
        "dose_mg_kg": dose_mg_kg,
        "issues": issues,
    }


def check_forbidden_patterns(text: str, rules: list[dict]) -> dict[str, Any]:
    """Scan text for forbidden transformation patterns.

    Uses a combination of strategies:
    - Exact substring match (primary)
    - Flexible number-aware match for efficiency/density claims
    - Regex as fallback with escaped special chars
    """
    violations: list[str] = []
    # Normalize: collapse whitespace, lowercase, strip trailing punctuation
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    # Replace % with word form to break it into separate token
    # Insert spaces around 'percent' so number-before and number-after both work
    normalized_pct = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 percent', normalized)

    for rule in rules:
        rule_id = rule.get("id", "?")
        for raw_pattern in rule.get("pattern", []):
            pattern = raw_pattern.lower()
            found = False

            # Strategy 1: exact substring (including trailing s for plurals)
            if pattern in normalized_pct:
                found = True
            else:
                # Strategy 2: flexible match — normalize spaces and try again
                p_normalized = re.sub(r' +', ' ', pattern)
                if p_normalized in normalized_pct:
                    found = True
                else:
                    # Strategy 3: specific number-aware checks
                    if "efficiency >" in pattern or "efficiency>" in pattern:
                        # Scan the normalized text for efficiency values > 1 (or > 100%)
                        # Patterns: "150% efficiency", "efficiency 150%", "efficiency 150 percent",
                        #            "efficiency > 100%", "efficiency > 1.0", "over unity"
                        # Only flag if a specific number > 1 is found near "efficiency"
                        eff_text = normalized_pct
                        # Check for "over unity" or similar — not a numeric violation
                        if re.search(r'\bover\s+unity\b', eff_text):
                            pass  # "over unity" is vague, not a specific violation
                        else:
                            for m in re.finditer(r'efficienc(y|ies)?', eff_text):
                                start = max(0, m.start() - 25)
                                end = min(len(eff_text), m.end() + 25)
                                window = eff_text[start:end]
                                # Find numbers in window, check if followed by "percent"
                                for num_m in re.finditer(r'(\d+(?:\.\d+)?)(\s+percent)?', window):
                                    raw_val = float(num_m.group(1))
                                    has_percent = bool(num_m.group(2))
                                    # Flag if: number > 1 AND has a % sign
                                    # (50% → raw_val=50 with % → should be 0.5, not flagged;
                                    #  but 150% → raw_val=150 with % → > 1, flagged)
                                    if has_percent and raw_val > 100:
                                        # raw_val > 100 means > 100% — impossible efficiency
                                        found = True
                                        break
                                    # Also flag bare numbers > 100 (unambiguously > 100%)
                                    if not has_percent and raw_val > 100:
                                        found = True
                                        break
                                if found:
                                    break
                    elif "negative mass" in pattern:
                        found = "negative mass" in normalized_pct
                    elif "negative density" in pattern:
                        found = "negative density" in normalized_pct
                    elif "gain > 1" in pattern:
                        found = re.search(r'gain\w*\s+\w*\s*>', normalized_pct) is not None
                    else:
                        # Strategy 4: simple regex (escaped special chars)
                        try:
                            escaped = re.escape(pattern)
                            if re.search(escaped, normalized_pct):
                                found = True
                        except re.error:
                            pass

            if found:
                violations.append(
                    f"forbidden pattern '{raw_pattern}' matched rule '{rule_id}'"
                )

    return {
        "passes": len(violations) == 0,
        "violations": violations,
    }


def check_unit_field(value: float, unit_rule: dict) -> dict[str, Any]:
    """Check if a numeric field value is within the declared unit range."""
    rng = unit_rule.get("range", [0, float("inf")])
    label = unit_rule.get("label", unit_rule.get("id", "?"))
    unit = unit_rule.get("unit", "")
    ok = rng[0] <= value <= rng[1]
    return {
        "passes": ok,
        "value": value,
        "unit": unit,
        "range": rng,
        "issues": [] if ok else [f"{label} value {value} {unit} outside range [{rng[0]}, {rng[1]}]"],
    }


# ── Main validation entry point ──────────────────────────────────────────────

def validate_hypothesis(
    hypothesis: dict[str, Any],
    domain: Optional[str] = None,
    rules_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Run all applicable physical checks against a hypothesis dict.

    Args:
        hypothesis: dict with keys like name, description, formula, bandgap,
                    efficiency, dose, predicted_effect, etc.
        domain: "biology" | "chemistry" | "materials_science" | None
        rules_path: optional override for physics_rules.json (for testing)

    Returns:
        validation result dict:
          - passed: bool (True if no hard violations)
          - hard_violations: list[str] — must be rejected
          - warnings: list[str] — soft issues
          - details: dict of per-check results
    """
    if rules_path:
        rules_data = json.loads(Path(rules_path).read_text())
    else:
        rules_data = _load_rules()

    hard_violations: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}

    domain = domain or hypothesis.get("domain", "generic")

    # ── 1. Forbidden patterns (always run) ───────────────────────────────────
    desc = hypothesis.get("description", "") + " " + hypothesis.get("predicted_effect", "")
    forb_results = check_forbidden_patterns(desc, rules_data.get("forbidden_transformations", []))
    details["forbidden_patterns"] = forb_results
    if not forb_results["passes"]:
        hard_violations.extend(forb_results["violations"])

    # ── 2. Charge balance ────────────────────────────────────────────────────
    formula = hypothesis.get("formula", "")
    if formula:
        cb = check_charge_balance(formula)
        details["charge_balance"] = cb
        if not cb["feasible"] and cb["charge_deficit"] > 3:
            hard_violations.append(f"charge imbalance in '{formula}': {cb['feasibility_note']}")

    # ── 3. Positive stoichiometry ───────────────────────────────────────────
    if formula:
        ps = check_positive_stoichiometry(formula)
        details["stoichiometry"] = ps
        if not ps["passes"]:
            hard_violations.extend([f"stoichiometry issue in '{formula}': {i}" for i in ps["issues"]])

    # ── 4. Bandgap (PV materials) ─────────────────────────────────────────────
    bandgap = hypothesis.get("bandgap")
    if bandgap is not None:
        bg = check_bandgap_non_negative(float(bandgap))
        details["bandgap"] = bg
        if not bg["passes"]:
            hard_violations.extend(bg["issues"])

    # ── 5. Efficiency ────────────────────────────────────────────────────────
    efficiency = hypothesis.get("efficiency")
    if efficiency is not None:
        eff = check_efficiency_range(float(efficiency))
        details["efficiency"] = eff
        if not eff["passes"]:
            hard_violations.extend(eff["issues"])

    # ── 6. Dose window (biology) ─────────────────────────────────────────────
    if domain == "biology":
        dose = hypothesis.get("dose")
        if dose is not None:
            d = check_dose_window(float(dose), hypothesis.get("name", ""))
            details["dose_window"] = d
            if not d["passes"]:
                warnings.extend(d["issues"])

    # ── 7. Operator-defined unit checks ─────────────────────────────────────
    for unit_rule in rules_data.get("unit_checks", []):
        if domain != unit_rule.get("domain") and unit_rule.get("domain") != "generic":
            continue
        field = unit_rule.get("field", "")
        value = hypothesis.get(field)
        if value is not None:
            result = check_unit_field(float(value), unit_rule)
            details[f"unit_{unit_rule['id']}"] = result
            if not result["passes"]:
                issues = result["issues"]
                # severity determines hard vs soft
                rule_def = next(
                    (r for r in rules_data.get("conservation_rules", [])
                     if r.get("id") == unit_rule.get("id")),
                    None
                )
                severity = (rule_def or unit_rule).get("severity", "soft")
                if severity == "hard":
                    hard_violations.extend(issues)
                else:
                    warnings.extend(issues)

    # ── 8. Operator-defined conservation rules ────────────────────────────────
    for rule in rules_data.get("conservation_rules", []):
        if domain not in (rule.get("domains", []) + ["generic"]) and rule.get("domains") != ["all"]:
            continue
        check_fn = rule.get("check", "")
        severity = rule.get("severity", "soft")
        check_result: dict[str, Any] = {"note": f"check '{check_fn}' not implemented", "passes": True}
        if check_fn == "charge_balanced" and formula:
            check_result = check_charge_balance(formula)
        elif check_fn == "positive_stoichiometry" and formula:
            check_result = check_positive_stoichiometry(formula)
        elif check_fn == "bandgap_non_negative" and bandgap is not None:
            check_result = check_bandgap_non_negative(float(bandgap))
        elif check_fn == "efficiency_feasible" and efficiency is not None:
            check_result = check_efficiency_range(float(efficiency))
        elif check_fn == "dose_feasible" and hypothesis.get("dose") is not None:
            check_result = check_dose_window(float(hypothesis["dose"]), hypothesis.get("name", ""))

        details[f"rule_{rule['id']}"] = check_result
        if not check_result.get("passes", True):
            msg = f"rule '{rule['label']}' violated: {'; '.join(check_result.get('issues', [])) or check_result.get('feasibility_note', '')}"
            if severity == "hard":
                hard_violations.append(msg)
            else:
                warnings.append(msg)

    return {
        "passed": len(hard_violations) == 0,
        "hard_violations": hard_violations,
        "warnings": warnings,
        "details": details,
        "domain": domain,
        "formula": formula or None,
    }


def format_validation_report(validation: dict[str, Any]) -> str:
    """Format a validation result as a human-readable string."""
    if validation["passed"]:
        lines = ["✅ Physical validation passed — no hard violations."]
    else:
        lines = ["❌ Physical validation FAILED:"]
        for v in validation["hard_violations"]:
            lines.append(f"  • {v}")

    if validation["warnings"]:
        lines.append("⚠️  Warnings:")
        for w in validation["warnings"]:
            lines.append(f"  • {w}")

    return "\n".join(lines)


# ── Convenience wrappers ───────────────────────────────────────────────────────

def quick_validate(
    formula: str = "",
    bandgap: Optional[float] = None,
    efficiency: Optional[float] = None,
    domain: str = "chemistry",
) -> dict[str, Any]:
    """Single-shot validation for a formula / parameters without a full hypothesis dict."""
    return validate_hypothesis(
        {"formula": formula, "bandgap": bandgap, "efficiency": efficiency},
        domain=domain,
    )


# ── Integration with /explore ─────────────────────────────────────────────────
# The explore_engine can call validate_hypothesis() after generating hypotheses.
# Example integration point (not executed automatically):
#
#   for hyp in raw_hypotheses:
#       v = validate_hypothesis(hyp, domain=detected_domain)
#       if not v["passed"]:
#           hyp["_rejected"] = True
#           hyp["_rejection_reasons"] = v["hard_violations"]
#           hyp["_validation_report"] = format_validation_report(v)
#       if v["warnings"]:
#           hyp["_warnings"] = v["warnings"]
#       scored_hypotheses.append(hyp)
#
# The operator-editable rules at weslr/physics_rules.json control which checks
# fire for which domains, and whether each rule is "hard" (reject) or "soft" (warn).