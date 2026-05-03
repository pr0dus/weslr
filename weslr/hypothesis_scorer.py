"""Hypothesis Scorer — score, rank, and format hypotheses from /explore."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

# ──────────────────────────────────────────────────────────────────────────────
# Chemical Formula Feasibility Heuristics
# ──────────────────────────────────────────────────────────────────────────────

# Common oxidation states for rule-based charge balance checking
_OXIDATION_STATES: dict[str, list[int]] = {
    "H": [1, -1], "Li": [1], "Na": [1], "K": [1], "Rb": [1], "Cs": [1],
    "Mg": [2], "Ca": [2], "Sr": [2], "Ba": [2],
    "Al": [3], "B": [3],
    "C": [4, -4], "Si": [4, -4],
    "N": [5, 4, 3, 2, 1, -1, -2, -3], "P": [5, 3, -3],
    "O": [-2], "S": [6, 4, 2, -2], "Se": [6, 4, 2, -2],
    "Fe": [3, 2], "Co": [3, 2], "Ni": [3, 2, 0],
    "Cu": [2, 1], "Zn": [2], "Ga": [3], "Ge": [4, 2],
    "As": [5, 3, -3], "Ag": [1], "Cd": [2], "In": [3], "Sn": [4, 2],
    "Sb": [5, 3, -3], "Au": [3, 1], "Hg": [2, 1],
    "Ti": [4, 3, 2], "V": [5, 4, 3, 2], "Cr": [6, 3, 2],
    "Mn": [7, 4, 3, 2], "Mo": [6, 5, 4, 3], "W": [6, 5, 4, 3],
    "Cl": [7, 5, 3, 1, -1], "Br": [5, 3, 1, -1], "I": [7, 5, 1, -1],
    "F": [-1],
}


def _parse_formula(formula: str) -> dict[str, int]:
    """Parse a chemical formula into element → count dict.

    Handles simple formulas like H2O, CaSO4, Cu2ZnSnSe4.
    Handles repeated groups like Ca(OH)2.
    """
    formula = formula.strip()
    if not formula:
        return {}

    # Handle groups like (OH)2
    group_pattern = re.compile(r"\(([A-Za-z0-9]+)\)(\d+)")
    while group_pattern.search(formula):
        formula = group_pattern.sub(
            lambda m: "".join(
                f"{el}{cnt * int(m.group(2))}"
                for el, cnt in re.findall(r"([A-Z][a-z]?)(\d*)", m.group(1))
            ),
            formula,
        )

    elements: dict[str, int] = {}
    for match in re.finditer(r"([A-Z][a-z]?)(\d*)", formula):
        el = match.group(1)
        cnt = int(match.group(2)) if match.group(2) else 1
        if el:
            elements[el] = elements.get(el, 0) + cnt
    return elements


def check_charge_balance(formula: str) -> dict[str, Any]:
    """Check if a chemical formula is charge-balanced (net charge = 0).

    Returns dict with:
      - is_balanced: bool
      - net_charge: int (computed)
      - charge_deficit: int (how far from zero)
      - plausible_anions, plausible_cations: lists
      - feasibility_note: str
    """
    elements = _parse_formula(formula)
    if not elements:
        return {"is_balanced": False, "net_charge": 0, "charge_deficit": 0,
                "plausible_anions": [], "plausible_cations": [], "feasibility_note": "unparseable"}

    net = 0
    plausible_anions: list[str] = []
    plausible_cations: list[str] = []

    for el, cnt in elements.items():
        states = _OXIDATION_STATES.get(el, [0])
        # Pick the most common state for each element type
        if el in ("O", "S", "Se", "F", "Cl", "Br", "I"):
            # Anions
            state = min(states)  # most negative
            plausible_anions.append(el)
        elif el in ("H", "Li", "Na", "K", "Mg", "Ca", "Al", "Fe", "Cu", "Zn"):
            # Cations
            state = max(states)  # most positive
            plausible_cations.append(el)
        else:
            state = states[0] if states else 0

        net += cnt * state

    charge_deficit = abs(net) if net != 0 else 0

    # Feasibility heuristic:
    # 0 = perfectly balanced, 1-3 = minor imbalance (often OK), >3 = suspicious
    if net == 0:
        note = "charge balanced"
        feasible = True
    elif charge_deficit <= 3:
        note = f"minor charge imbalance ({net:+d}) — may be compensated by counterions"
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


def check_valence_rules(formula: str) -> dict[str, Any]:
    """Check common valence / bonding heuristics for a formula.

    Returns dict with:
      - passes_valence: bool
      - issues: list[str]
      - feasibility: str ("high", "moderate", "low")
    """
    elements = _parse_formula(formula)
    if not elements:
        return {"passes_valence": False, "issues": ["unparseable"], "feasibility": "low"}

    issues: list[str] = []
    total_anions = 0
    total_cations = 0

    common_anions = {"O", "S", "Se", "F", "Cl", "Br", "I", "N"}
    common_cations = {
        "H", "Li", "Na", "K", "Mg", "Ca", "Sr", "Ba", "Al",
        "Fe", "Co", "Ni", "Cu", "Zn", "Ti", "V", "Mn", "Mo",
    }

    for el, cnt in elements.items():
        if el in common_anions:
            total_anions += cnt
        elif el in common_cations:
            total_cations += cnt

    # Very rough heuristic: anions and cations should be in plausible proportions
    if total_anions > 0 and total_cations > 0:
        ratio = total_cations / total_anions
        if ratio < 0.3 or ratio > 5:
            issues.append(f"unusual cation/anion ratio ({ratio:.2f})")

    # H2O is common and stable — suppress false positives
    # (H-O bonds are well-known; handled by charge balance)

    return {
        "passes_valence": len(issues) == 0,
        "issues": [i for i in issues if i],
        "feasibility": "high" if not issues else "moderate",
    }


def chemical_feasibility(formula: str) -> dict[str, Any]:
    """Combined physicochemical feasibility check for a chemical formula.

    Returns a summary dict:
      - overall_feasible: bool
      - score: 0.0–1.0
      - charge: charge balance result
      - valence: valence check result
      - note: human-readable summary
    """
    if not formula or not re.search(r"^[A-Za-z0-9\(\)\[\]]+$", formula):
        return {"overall_feasible": True, "score": 1.0,
                "charge": {}, "valence": {}, "note": "no formula detected"}

    charge_result = check_charge_balance(formula)
    valence_result = check_valence_rules(formula)

    score = 1.0
    if not charge_result["feasible"]:
        score -= 0.4
    if not valence_result["passes_valence"]:
        score -= 0.2

    charge_ok = charge_result.get("feasible", charge_result["net_charge"] == 0)
    valence_ok = valence_result.get("passes_valence", True)
    overall_feasible = score >= 0.6 and charge_ok and valence_ok

    note = f"Chemical: {charge_result['feasibility_note']}"
    if valence_result["issues"]:
        note += f"; valence: {valence_result['issues'][0]}"

    return {
        "overall_feasible": overall_feasible,
        "score": round(score, 3),
        "charge": charge_result,
        "valence": valence_result,
        "note": note,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Hypothesis Scoring
# ──────────────────────────────────────────────────────────────────────────────

def score_hypothesis(
    hypothesis: dict,
    sources: list[dict],
    novelty_baseline: Optional[dict] = None,
) -> dict:
    """Score a single hypothesis across multiple dimensions.

    Args:
        hypothesis: dict with keys: name, description, components, predicted_effect
        sources: list of source dicts (each with trust_score, title, id, etc.)
        novelty_baseline: dict of known combination → score (to penalize duplicates)

    Returns:
        hypothesis dict augmented with scoring fields:
          - confidence: 0.0–1.0 overall confidence
          - novelty: 0.0–1.0 novelty score
          - feasibility: "high"|"moderate"|"low"
          - source_trust: average trust of supporting sources
          - independent_sources: number of distinct sources
          - component_support: fraction of components with independent evidence
          - scoring_details: breakdown dict
    """
    scoring: dict = {}

    # 1. Source trust (0–1, default 0.5)
    if sources:
        trusts = [s.get("trust_score", s.get("trust", 0.5)) for s in sources]
        source_trust = round(sum(trusts) / len(trusts), 3)
    else:
        source_trust = 0.3
        trusts = []
    scoring["source_trust"] = source_trust

    # 2. Number of independent sources (diversity bonus)
    independent_sources = len(set(s.get("id", "") for s in sources if s.get("id")))
    # Cap at 5 for scoring purposes
    indep_bonus = min(independent_sources / 5, 1.0)
    scoring["independent_sources"] = independent_sources
    scoring["independence_bonus"] = indep_bonus

    # 3. Component support: what fraction of named components have evidence
    components = hypothesis.get("components", [])
    supported_components = sum(
        1 for c in components if any(
            c.lower() in (s.get("title", "") + " " + s.get("abstract", "")).lower()
            for s in sources
        )
    )
    component_support_frac = (
        supported_components / len(components) if components else 0.5
    )
    scoring["component_support_frac"] = component_support_frac
    scoring["supported_components"] = supported_components

    # 4. Novelty: penalize if similar to novelty_baseline
    novelty = 0.8  # default high novelty
    if novelty_baseline:
        hyp_name = hypothesis.get("name", "").lower()
        for known, known_score in novelty_baseline.items():
            # Simple string overlap
            if known in hyp_name or hyp_name in known:
                novelty = max(0.0, known_score - 0.2)
                break
    scoring["novelty"] = novelty

    # 5. Predicted effect grounding (bonus if quantitative effect)
    predicted = hypothesis.get("predicted_effect", "")
    has_quantitative = bool(re.search(r"\d+", predicted))
    grounding_bonus = 0.1 if has_quantitative else 0.0
    scoring["grounding_bonus"] = grounding_bonus

    # 6. Chemical feasibility (if formula present)
    formula = hypothesis.get("formula", "")
    chem_feas = chemical_feasibility(formula) if formula else {"score": 1.0, "overall_feasible": True}
    scoring["chemical_feasibility"] = chem_feas.get("score", 1.0)

    # ── Combine into overall confidence ─────────────────────────────────────
    confidence = (
        source_trust * 0.30
        + indep_bonus * 0.15
        + component_support_frac * 0.20
        + novelty * 0.15
        + grounding_bonus * 0.05
        + chem_feas.get("score", 1.0) * 0.10
    )

    scoring["raw_contributions"] = {
        "source_trust": (source_trust, 0.30),
        "independence": (indep_bonus, 0.15),
        "component_support": (component_support_frac, 0.20),
        "novelty": (novelty, 0.15),
        "grounding": (grounding_bonus, 0.05),
        "chemical_feasibility": (chem_feas.get("score", 1.0), 0.10),
    }

    return {
        **hypothesis,
        "confidence": round(confidence, 3),
        "source_trust": source_trust,
        "independent_sources": independent_sources,
        "component_support": round(component_support_frac, 2),
        "component_count": len(components),
        "novelty": novelty,
        "feasibility": (
            "high" if chem_feas.get("overall_feasible", True) else
            "moderate" if chem_feas.get("score", 1.0) >= 0.6 else "low"
        ),
        "predicted_effect": predicted,
        "scoring_details": scoring,
    }


def rank_hypotheses(
    hypotheses: list[dict],
    novelty_baseline: Optional[dict] = None,
) -> list[dict]:
    """Score and rank a list of hypotheses by confidence (descending)."""
    scored = [
        score_hypothesis(h, h.get("supporting_sources", []), novelty_baseline)
        for h in hypotheses
    ]
    return sorted(scored, key=lambda h: h.get("confidence", 0), reverse=True)


# ──────────────────────────────────────────────────────────────────────────────
# Formatting
# ──────────────────────────────────────────────────────────────────────────────

def format_hypothesis(index: int, h: dict) -> str:
    """Format a single hypothesis for display."""
    conf = h.get("confidence", 0)
    feas = h.get("feasibility", "unknown")
    name = h.get("name", "unnamed hypothesis")
    desc = h.get("description", "")
    effect = h.get("predicted_effect", "")
    sources = h.get("supporting_sources", [])
    next_step = h.get("suggested_next_step", "")
    formula = h.get("formula", "")

    conf_bar = "".join("▓" if i < int(conf * 10) else "░" for i in range(10))
    conf_str = f"{conf:.2f}"
    comp_count = len(h.get("components", []))

    lines = [
        f"{index}. **{name}**",
        f"   Confidence: {conf_str} [{conf_bar}]  Feasibility: {feas}  Components: {comp_count}",
    ]

    if formula:
        chem_note = ""
        cf = h.get("scoring_details", {}).get("chemical_feasibility", 1.0)
        if cf < 0.6:
            chem_note = " ⚠️ charge imbalanced"
        lines.append(f"   Formula: `{formula}`{chem_note}")

    if desc:
        lines.append(f"   {desc}")

    if effect:
        lines.append(f"   Expected effect: {effect}")

    if sources:
        src_lines = []
        for s in sources[:3]:
            sid = s.get("id", s.get("arxiv_id", s.get("pmid", "?")))
            title = (s.get("title", "")[:60]) + ("..." if len(s.get("title", "")) > 60 else "")
            src_lines.append(f"     • [{sid}] {title}")
        lines.append("   Sources:")
        lines.extend(src_lines)

    if next_step:
        lines.append(f"   Suggested next step: {next_step}")

    return "\n".join(lines)


def format_hypothesis_list(
    hypotheses: list[dict],
    goal: str,
    domain: Optional[str] = None,
    limit: int = 5,
) -> str:
    """Format a ranked hypothesis list for the /explore output."""
    if not hypotheses:
        lines = [
            f"🔍 Exploring: {goal}",
            "",
            "No hypotheses generated. Try broadening the goal or checking search adapter availability.",
        ]
        return "\n".join(lines)

    scored = hypotheses[:limit]

    lines = [
        f"🔍 Exploring: {goal}",
        f"   Domain: {domain or 'auto-detected'}  |  Top {len(scored)} hypotheses",
        "",
    ]

    for i, h in enumerate(scored, 1):
        lines.append(format_hypothesis(i, h))
        lines.append("")

    extra = len(hypotheses) - limit
    if extra > 0:
        lines.append(f"({extra} more hypotheses — reply with /explore {goal} --all to see full list)")

    return "\n".join(lines)
