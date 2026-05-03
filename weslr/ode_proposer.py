# Weslr ODE Proposer Module
# Phase 6.3 – Differential Equation Proposer
# Rule-based template system, no LLM. All operations read-only and ephemeral.

"""
ODE proposer: takes natural-language descriptions and returns candidate
ordinary differential equation models.

No LLM is used. Pattern matching is purely keyword-based against
operator-editable templates in ode_templates.json.

Usage:
    from weslr.ode_proposer import propose_ode, solve_ode, parse_description
    results = propose_ode("tumor growth with chemotherapy")
    for r in results:
        print(r["equation_str"], r["confidence"])
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Optional

# ── Template loading ─────────────────────────────────────────────────────────
_TEMPLATES_PATH = Path(__file__).parent / "ode_templates.json"
_TEMPLATES: list[dict[str, Any]] = []
_TEMPLATE_NAMES: set[str] = set()
_MAX_PER_DESCRIPTION = 3


def _load_templates() -> None:
    """Load ODE templates from JSON file. Called once at module init."""
    global _TEMPLATES, _TEMPLATE_NAMES, _MAX_PER_DESCRIPTION
    if not _TEMPLATES and _TEMPLATES_PATH.exists():
        try:
            data = json.loads(_TEMPLATES_PATH.read_text())
            _TEMPLATES = data.get("templates", [])
            _MAX_PER_DESCRIPTION = data.get("max_odes_per_description", 3)
            _TEMPLATE_NAMES = {t["name"] for t in _TEMPLATES}
        except Exception:
            _TEMPLATES = []
            _TEMPLATE_NAMES = set()


_load_templates()


# ── Keyword extraction ────────────────────────────────────────────────────────
def _tokenize(text: str) -> list[str]:
    """Lower-case, strip punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return text.split()


def _get_ngrams(tokens: list[str], n: int = 2) -> list[str]:
    """Return list of n-grams from tokens."""
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _score_keywords(tokens: list[str], keywords: list[str]) -> float:
    """
    Score how many keywords appear in tokens.
    Returns fraction of keywords found (0.0–1.0).
    """
    if not keywords:
        return 0.0
    # Also check bigrams
    ngrams = set(_get_ngrams(tokens, 2))
    text_set = set(tokens) | ngrams
    found = sum(1 for kw in keywords if kw.lower() in text_set)
    # Bonus: check for partial matches within words
    for token in tokens:
        for kw in keywords:
            if kw.lower() in token and kw.lower() not in text_set:
                found += 0.5
                break
    return min(1.0, found / len(keywords))


# ── Parse description ────────────────────────────────────────────────────────
def parse_description(description: str) -> dict[str, Any]:
    """
    Extract entities, processes, and model hints from a natural-language
    description.

    Returns dict:
      - tokens: list[str] (tokenized description)
      - entities: list[str] (identified noun-like entities)
      - processes: list[str] (identified dynamic processes)
      - model_hints: list[str] (matched template names)
      - matched_keywords: dict[str, list[str]] (template → keywords found)
      - description: str (original)
    """
    tokens = _tokenize(description)
    ngrams = _get_ngrams(tokens, 2)

    # Entities: capitalized or numeric-adjacent words (heuristic)
    # We look for specific domain terms
    entities: list[str] = []
    entity_keywords = [
        "population", "tumor", "cell", "drug", "concentration", "temperature",
        "species", "host", "parasite", "bacteria", "virus", "prey", "predator",
        "substrate", "enzyme", "product", "reactant", "gene", "protein",
        "molecule", "hormone", "antibody", "antigen", "species", "individual",
    ]
    for tok in tokens:
        if any(tok.startswith(e) or e in tok for e in entity_keywords):
            entities.append(tok)

    # Processes: dynamic/action keywords
    process_keywords = [
        "growth", "decay", "spread", "decay", "increase", "decrease",
        "diffuse", "absorb", "eliminate", "clear", "interact", "compete",
        "predate", "infect", "recover", "die", "born", "divide", "mutate",
        "catalyze", "inhibit", "activate", "degrade", "transport", "diffuse",
        "cool", "heat", "dissolve", "precipitate", "react", "oscillate",
    ]
    processes = [t for t in tokens if any(p in t for p in process_keywords)]

    # Model hints: score each template
    matched_keywords: dict[str, list[str]] = {}
    model_hints: list[tuple[str, float]] = []  # (name, score)

    for template in _TEMPLATES:
        t_keywords = template.get("keywords", [])
        score = _score_keywords(tokens, t_keywords)
        if score > 0:
            # Record which keywords matched
            found_kws = [kw for kw in t_keywords if kw.lower() in set(tokens) | set(ngrams)]
            matched_keywords[template["name"]] = found_kws
            model_hints.append((template["name"], score))

    # Sort by score descending
    model_hints.sort(key=lambda x: x[1], reverse=True)

    return {
        "tokens": tokens,
        "entities": entities,
        "processes": processes,
        "model_hints": model_hints,  # list of (name, score) tuples
        "matched_keywords": matched_keywords,
        "description": description,
    }


# ── ODE proposer ─────────────────────────────────────────────────────────────
def propose_ode(
    description: str,
    variables: dict[str, str] | None = None,
    max_candidates: int | None = None,
) -> list[dict[str, Any]]:
    """
    Propose one or more candidate ODEs for a natural-language description.

    Args:
        description: natural-language description of dynamics
        variables: optional dict of variable overrides {var: description}
                   e.g., {"T": "tumor size", "C": "drug concentration"}
        max_candidates: override max number of candidates (default from template)

    Returns list of candidate dicts, each with:
      - template_name: str
      - equation_str: str (or list of str for multi-equation systems)
      - variables: dict {var: description}
      - confidence: float (0.0–1.0)
      - provenance: {template_name, matched_keywords, score}
      - analytical_solution: str (if available)
    """
    if max_candidates is None:
        max_candidates = _MAX_PER_DESCRIPTION

    parsed = parse_description(description)
    candidates: list[dict[str, Any]] = []

    # Collect candidates from matched templates (in priority order)
    for model_name, score in parsed["model_hints"][:max_candidates]:
        template = next((t for t in _TEMPLATES if t["name"] == model_name), None)
        if not template:
            continue

        # Adjust confidence by keyword match score
        confidence = round(template["confidence"] * score, 3)

        # Apply variable overrides if provided
        all_vars = dict(template.get("variables", {}))
        if variables:
            all_vars.update(variables)

        # Get equation(s)
        eq_str = template.get("equation") or template.get("equations", [])
        if isinstance(eq_str, list):
            equations = eq_str
        else:
            equations = [eq_str]

        candidate = {
            "template_name": model_name,
            "equation_str": equations if len(equations) > 1 else equations[0],
            "variables": all_vars,
            "confidence": confidence,
            "provenance": {
                "template": model_name,
                "keywords_matched": parsed["matched_keywords"].get(model_name, []),
                "match_score": round(score, 3),
                "description_tokens": parsed["tokens"],
            },
            "analytical_solution": template.get("analytical_solution", ""),
        }
        candidates.append(candidate)

    # If no templates matched, try generic fallback based on process keywords
    if not candidates:
        fallback = _propose_fallback(parsed, variables)
        candidates.extend(fallback)

    return candidates


def _propose_fallback(parsed: dict, variables: dict | None) -> list[dict]:
    """Generate fallback ODEs when no template matches well."""
    processes = set(parsed["processes"])
    candidates = []

    # Determine direction from process keywords
    growth_kw = {"growth", "increase", "multiply", "divide", "reproduce", "expand"}
    decay_kw = {"decay", "decrease", "degrade", "eliminate", "die", "clear", "remove"}
    interact_kw = {"interact", "compete", "predate", "infect", "attack", "bind"}

    has_growth = any(p in processes for p in growth_kw)
    has_decay = any(p in processes for p in decay_kw)
    has_interact = any(p in processes for p in interact_kw)

    if has_interact and len(parsed["entities"]) >= 2:
        # Two-species interaction
        X = parsed["entities"][0] if len(parsed["entities"]) > 0 else "X"
        Y = parsed["entities"][1] if len(parsed["entities"]) > 1 else "Y"
        candidates.append({
            "template_name": "two_species_interaction",
            "equation_str": [f"d{X}/dt = r1*{X} - beta*{X}*{Y}", f"d{Y}/dt = beta*{X}*{Y} - r2*{Y}"],
            "variables": {
                X: parsed["entities"][0] if parsed["entities"] else "species 1",
                Y: parsed["entities"][1] if len(parsed["entities"]) > 1 else "species 2",
                "r1": "growth rate of X",
                "r2": "decay rate of Y",
                "beta": "interaction rate",
            },
            "confidence": 0.5,
            "provenance": {
                "template": "two_species_interaction",
                "keywords_matched": list(processes & interact_kw),
                "match_score": 1.0,
                "description_tokens": parsed["tokens"],
            },
            "analytical_solution": "No closed-form analytical solution for general interaction",
        })
    elif has_growth and not has_decay:
        entity = parsed["entities"][0] if parsed["entities"] else "X"
        candidates.append({
            "template_name": "exponential_growth",
            "equation_str": f"d{entity}/dt = r*{entity}",
            "variables": {
                entity: parsed["entities"][0] if parsed["entities"] else "quantity",
                "r": "growth rate",
            },
            "confidence": 0.4,
            "provenance": {
                "template": "exponential_growth",
                "keywords_matched": list(processes & growth_kw),
                "match_score": 1.0,
                "description_tokens": parsed["tokens"],
            },
            "analytical_solution": f"{entity}(t) = {entity}0 * exp(r*t)",
        })
    elif has_decay and not has_growth:
        entity = parsed["entities"][0] if parsed["entities"] else "X"
        candidates.append({
            "template_name": "exponential_decay",
            "equation_str": f"d{entity}/dt = -k*{entity}",
            "variables": {
                entity: parsed["entities"][0] if parsed["entities"] else "quantity",
                "k": "decay rate",
            },
            "confidence": 0.4,
            "provenance": {
                "template": "exponential_decay",
                "keywords_matched": list(processes & decay_kw),
                "match_score": 1.0,
                "description_tokens": parsed["tokens"],
            },
            "analytical_solution": f"{entity}(t) = {entity}0 * exp(-k*t)",
        })

    return candidates[:_MAX_PER_DESCRIPTION]


# ── ODE solver ───────────────────────────────────────────────────────────────
def solve_ode(
    ode_str: str,
    initial_conditions: dict[str, float] | None = None,
    time_range: tuple[float, float] | None = None,
    method: str = "sympy",
) -> dict[str, Any]:
    """
    Attempt to solve an ODE symbolically using sympy.

    Args:
        ode_str: ODE string, e.g. "dX/dt = r*X*(1 - X/K)"
                 Can also be a list of equations for systems.
        initial_conditions: dict of {var: value}, e.g. {"X": 0.1}
        time_range: (t0, t1) tuple for future numerical use
        method: "sympy" only for now

    Returns dict with:
      - ok: bool
      - solution: str (equation or "Analytical solution not available...")
      - method: str
      - note: str
    """
    from weslr.symbolic_math import is_available

    if not is_available():
        return {
            "ok": False,
            "solution": "",
            "method": method,
            "note": "SymPy not available – install with: pip install sympy",
        }

    if method != "sympy":
        return {
            "ok": False,
            "solution": "",
            "method": method,
            "note": f"Method '{method}' not supported. Only 'sympy' is available in V1.",
        }

    # Import sympy
    try:
        from sympy import (
            Eq, Symbol, symbols, Function, dsolve, parse_expr, solve,
        )
        from sympy.parsing.sympy_parser import (
            standard_transformations, implicit_multiplication_application,
            parse_expr as sympy_parse,
        )
    except ImportError:
        return {
            "ok": False,
            "solution": "",
            "method": method,
            "note": "SymPy import failed",
        }

    trans = standard_transformations + (implicit_multiplication_application,)
    t = Symbol("t")

    try:
        # Normalize ode_str to a list
        if isinstance(ode_str, str):
            equations = [ode_str]
        else:
            equations = list(ode_str)

        sympy_eqs = []
        sympy_funcs = []  # list of Function(t) for each equation
        for eq in equations:
            if "=" in eq:
                parts = eq.split("=", 1)
                lhs_str = parts[0].strip()
                rhs_str = parts[1].strip()
                lhs_parsed, func = _parse_derivative(lhs_str, trans)
                rhs_parsed = sympy_parse(rhs_str, transformations=trans, evaluate=False)
                # Substitute bare symbol (e.g. X) with function (e.g. X(t))
                # so that RHS matches the derivative form X(t).diff(t)
                rhs_sub = rhs_parsed.subs(Symbol(func.func.name), func)
                # Express ODE as: func.diff(t) = rhs_parsed (substituted)
                sympy_eqs.append(Eq(func.diff(t), rhs_sub))
                sympy_funcs.append(func)
            else:
                parsed = sympy_parse(eq, transformations=trans, evaluate=False)
                sympy_eqs.append(Eq(parsed, 0))

        if len(sympy_eqs) == 1:
            # Single ODE – use func.diff(t) form directly
            func = sympy_funcs[0] if sympy_funcs else None
            if func is None:
                return {"ok": False, "solution": "", "method": method, "note": "Could not identify function variable"}
            # Build solution expression: f.diff(t) - rhs = 0
            rhs_expr = sympy_eqs[0].rhs
            ode_for_dsolve = func.diff(t) - rhs_expr
            sol = dsolve(ode_for_dsolve, func)
            sol_str = str(sol)
            # Try to apply initial conditions: X(0) = X0
            if initial_conditions:
                for var_name, val in initial_conditions.items():
                    if var_name == str(func.func):
                        try:
                            ic_expr = func.subs(t, 0)
                            const = [s for s in sol.free_symbols if s.name.startswith('C')]
                            if const:
                                test_sol = sol.subs(ic_expr, val)
                                for c in const:
                                    try:
                                        c_val = solve(test_sol.subs(t, 0), c)
                                        if c_val:
                                            sol = sol.subs(c, c_val[0])
                                            sol_str = str(sol)
                                            break
                                    except Exception:
                                        pass
                        except Exception:
                            pass
            return {
                "ok": True,
                "solution": sol_str,
                "method": "sympy",
                "note": f"Analytical solution: {sol_str}",
            }
        else:
            # System of ODEs
            funcs = [f.diff(t) for f in sympy_funcs]
            rhs_exprs = [eq.rhs for eq in sympy_eqs]
            ode_system = [f - r for f, r in zip(funcs, rhs_exprs)]
            sol = dsolve(ode_system, funcs)
            if sol:
                sol_strs = [str(s) for s in sol]
                return {
                    "ok": True,
                    "solution": sol_strs,
                    "method": "sympy",
                    "note": f"System of {len(sol)} equations solved analytically",
                }
            else:
                return {
                    "ok": False,
                    "solution": "",
                    "method": "sympy",
                    "note": "Analytical solution not available for this system",
                }
    except Exception as e:
        return {
            "ok": False,
            "solution": "",
            "method": method,
            "note": f"ODE solving error: {e}",
        }


def _parse_derivative(expr_str: str, trans) -> tuple:
    """
    Parse derivative notation like 'dX/dt' into (Derivative, Function(t)) tuple.
    Also handles 'd^2X/dt^2'.
    Returns (lhs_parsed, func) where func is the Function(t) for use in dsolve.
    """
    from sympy import Symbol, Function, Derivative

    t = Symbol("t")
    # Pattern: d^nX/dt^n or dX/dt (with optional spaces around /)
    m = re.match(r"d\^?(\d+)?([A-Za-z]+)\s*/\s*dt(?:\^\{(\d+)\})?", expr_str.replace(" ", ""))
    if m:
        order_deriv = int(m.group(1) or 1)
        var_name = m.group(2)
        func = Function(var_name)(t)
        deriv = Derivative(func, t, order_deriv)
        return (deriv, func)

    # Fallback: try to parse as a simple expression
    from sympy.parsing.sympy_parser import parse_expr
    parsed = parse_expr(expr_str, transformations=trans, evaluate=False)
    return (parsed, None)


# ── Parameter estimation (stub) ──────────────────────────────────────────────
def estimate_parameters(
    ode_str: str,
    data_points: list[dict[str, float]],
) -> dict[str, Any]:
    """
    Stub for V1 – parameter estimation from data is not yet implemented.

    Returns a dict with ok=False and a note.
    """
    return {
        "ok": False,
        "note": (
            "Parameter estimation not yet implemented in V1. "
            "To estimate parameters, provide known values for rate constants, "
            "initial conditions, or carrying capacities based on domain knowledge."
        ),
        "suggestion": (
            "Provide known parameter values when calling propose_ode() "
            "via the variables dict, or specify them manually after review."
        ),
    }


# ── Template listing ─────────────────────────────────────────────────────────
def list_templates() -> list[dict[str, Any]]:
    """Return all template names and their equations (no keywords)."""
    return [
        {
            "name": t["name"],
            "equation": t.get("equation") or " / ".join(t.get("equations", [])),
            "variables": t.get("variables", {}),
            "confidence": t.get("confidence", 0.0),
            "domain": t.get("domain", []),
        }
        for t in _TEMPLATES
    ]


# ── Text formatting helpers ──────────────────────────────────────────────────
def format_ode_candidate(candidate: dict[str, Any], include_solution: bool = False) -> str:
    """Format a single ODE candidate as readable text."""
    eq = candidate["equation_str"]
    if isinstance(eq, list):
        eq_lines = eq
    else:
        eq_lines = [eq]

    confidence = candidate["confidence"]
    template = candidate["template_name"]
    vars_dict = candidate["variables"]
    provenance = candidate.get("provenance", {})
    matched = provenance.get("keywords_matched", [])

    lines = []
    lines.append(f"[{template.upper()}]  confidence: {confidence:.0%}")
    for e in eq_lines:
        lines.append(f"  {e}")
    if matched:
        lines.append(f"  keywords matched: {', '.join(matched)}")
    lines.append(f"  variables:")
    for var, desc in vars_dict.items():
        lines.append(f"    {var}: {desc}")
    if include_solution and candidate.get("analytical_solution"):
        lines.append(f"  solution: {candidate['analytical_solution']}")

    return "\n".join(lines)


def format_ode_proposal(description: str, candidates: list[dict[str, Any]]) -> str:
    """Format a full ODE proposal output."""
    if not candidates:
        return (
            f"No ODE template matched '{description}'.\n"
            "Try a more specific description or one of the supported keywords:\n"
            "  growth, decay, logistic, epidemic, SIR, predator-prey, drug, tumor, cooling..."
        )

    lines = [f"ODE Proposal for: \"{description}\"", ""]
    for i, c in enumerate(candidates, 1):
        lines.append(format_ode_candidate(c, include_solution=True))
        lines.append("")
    return "\n".join(lines)


# ── Internal helpers for handlers ──────────────────────────────────────────
def _parse_initial_conditions(ic_str: str | None) -> dict[str, float]:
    """Parse 'var=value, var2=value2' into dict."""
    if not ic_str:
        return {}
    result = {}
    for pair in ic_str.replace(",", " ").split():
        if "=" in pair:
            k, v = pair.split("=", 1)
            try:
                result[k.strip()] = float(v.strip())
            except ValueError:
                pass
    return result


def _parse_time_range(time_str: str | None) -> tuple[float, float] | None:
    """Parse 't0,t1' into tuple."""
    if not time_str:
        return None
    try:
        parts = time_str.split(",")
        return (float(parts[0].strip()), float(parts[1].strip()))
    except (ValueError, IndexError):
        return None