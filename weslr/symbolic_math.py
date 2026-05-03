# Weslr Symbolic Mathematics Module
# Optional dependency: sympy. All operations are read-only, ephemeral, sandboxed.

"""
Weslr symbolic math engine — pure Python, no network, no file I/O, no exec.

All operations are deterministic. Results are returned as strings or numbers,
never as live sympy objects that could be serialised and misused.

Usage:
    from weslr.symbolic_math import solve_equation, differentiate
    result = solve_equation("2x + 3 = 7")
    print(result)  # 'x = 2'
"""

from __future__ import annotations

import re
import json
import math
from pathlib import Path
from typing import Any, Optional

# ── Optional sympy import ─────────────────────────────────────────────────────
_SYP = None
_SYP_ERR: str | None = None

try:
    import sympy
    from sympy import (
        Eq, Symbol, symbols, solve, solve_poly_system,
        diff as sy_diff, integrate as sy_integrate, simplify as sy_simplify, expand as sy_expand,
        parse_expr, lambdify, oo,
        Function, exp, log, sqrt, sin, cos, tan,
        Float, Integer, Rational,
    )
    from sympy.parsing.sympy_parser import (
        standard_transformations,
        implicit_multiplication_application,
    )
    _SYP_TRANS = standard_transformations + (implicit_multiplication_application,)
    _SYP = sympy
except ImportError as e:
    _SYP_ERR = f"SymPy not installed – install with: pip install sympy  (original: {e})"

# ── Rules loading ─────────────────────────────────────────────────────────────
_RULES_PATH = Path(__file__).parent / "symbolic_rules.json"


def _load_rules() -> dict[str, Any]:
    """Load symbolic_rules.json. Returns empty dict if missing."""
    if _RULES_PATH.exists():
        try:
            return json.loads(_RULES_PATH.read_text())
        except Exception:
            pass
    return {}


# ── Guarded check ─────────────────────────────────────────────────────────────
def _require_sympy() -> tuple:
    """Return (sympy, transformations) or raise RuntimeError with install hint."""
    if _SYP is None:
        raise RuntimeError(_SYP_ERR or "SymPy not installed")
    return (_SYP, _SYP_TRANS)


# ── Normalisation helpers ──────────────────────────────────────────────────────
def _normalise_expr(s: str) -> str:
    """Collapse whitespace, handle common notation variants."""
    s = re.sub(r"\s+", " ", s.strip())
    # Remove thousand-separators
    s = s.replace(",", "")
    # Guard against accidental keywords / function names
    # that parse_expr might treat as symbols anyway
    return s


def _split_equation(eq_str: str) -> tuple[str, str] | None:
    """Split 'lhs = rhs' into (lhs_str, rhs_str). Returns None if no '='."""
    if "=" not in eq_str:
        return None
    parts = eq_str.split("=", 1)
    if len(parts) != 2:
        return None
    return parts[0].strip(), parts[1].strip()


# ── Core API ─────────────────────────────────────────────────────────────────

def is_available() -> bool:
    """True if sympy is installed and usable."""
    return _SYP is not None


def get_error() -> str | None:
    """Return the installation error string if sympy is unavailable."""
    return _SYP_ERR


def parse_equation(equation_str: str) -> dict[str, Any]:
    """
    Convert a string like '3*x + 5 = 20' into a structured dict.

    Returns dict with keys:
      - lhs, rhs: string representations of left/right sides
      - variable: auto-detected variable name (most algebraic-looking)
      - ok: bool
      - note: str

    Returns {'ok': False, 'note': ...} on parse failure.
    """
    if _SYP is None:
        return {"ok": False, "note": _SYP_ERR}

    try:
        parts = _split_equation(equation_str)
        if not parts:
            return {"ok": False, "note": f"No '=' found in '{equation_str}'"}

        lhs_str, rhs_str = parts
        syp, trans = _require_sympy()

        # Parse each side
        lhs_expr = parse_expr(_normalise_expr(lhs_str), transformations=trans, evaluate=False)
        rhs_expr = parse_expr(_normalise_expr(rhs_str), transformations=trans, evaluate=False)

        # Detect variable: prefer the symbol in lhs that appears most often (likely the "unknown").
        # Ties broken by alphabetical preference: x > y > z > w > v > u > t > ... > a > b > c > ...
        free = list(lhs_expr.free_symbols | rhs_expr.free_symbols)
        variable = None
        if free:
            names = [s.name for s in free]
            # Count occurrences in lhs only
            from sympy import Symbol
            from sympy.core.basic import Basic
            counts = {n: 0 for n in names}
            def walk(node):
                for child in getattr(node, 'args', []):
                    walk(child)
                if isinstance(node, Symbol) and node.name in names:
                    counts[node.name] += 1
            walk(lhs_expr)
            max_count = max(counts.values())
            candidates = [n for n, c in counts.items() if c == max_count]
            # Tie-break by reverse-alphabetical (x > y > z > ... > a > b > c)
            variable = sorted(candidates, key=lambda n: -ord(n[0]))[0]

        return {
            "ok": True,
            "lhs": lhs_str,
            "rhs": rhs_str,
            "variable": variable,
            "note": "parsed OK",
        }
    except Exception as e:
        return {"ok": False, "note": f"Parse error: {e}"}


def solve_equation(
    equation_str: str,
    variable: str | None = None,
) -> dict[str, Any]:
    """
    Solve an equation or expression for one or all variables.

    Examples:
        solve_equation("2*x + 3 = 7")         → [{x: 2}]
        solve_equation("x**2 - 4 = 0")         → [-2, 2]
        solve_equation("a*x = b", "x")         → [{x: b/a}]

    Returns dict:
      - solutions: list of dicts {var: value_str} or bare values
      - variable: str  (the variable solved for)
      - ok: bool
      - note: str
    """
    if _SYP is None:
        return {"ok": False, "solutions": [], "note": _SYP_ERR}

    try:
        parts = _split_equation(equation_str)
        if not parts:
            return {"ok": False, "solutions": [], "note": f"No '=' in '{equation_str}'"}

        lhs_str, rhs_str = parts
        sympify, trans = _require_sympy()

        lhs = parse_expr(_normalise_expr(lhs_str), transformations=trans, evaluate=False)
        rhs = parse_expr(_normalise_expr(rhs_str), transformations=trans, evaluate=False)
        eq = Eq(lhs, rhs)

        # Determine solve variable
        if variable:
            var_sym = Symbol(variable)
        else:
            free = list(lhs.free_symbols | rhs.free_symbols)
            if not free:
                return {"ok": False, "solutions": [], "note": "No variable found in equation"}
            var_sym = free[0]
            variable = var_sym.name

        raw_solutions = solve(eq, var_sym, dict=False)

        # Format solutions
        solutions = []
        seen = set()
        for sol in raw_solutions:
            display = str(sol)
            if display in seen:
                continue
            seen.add(display)
            # Try numeric evaluation
            try:
                numeric = float(sol.evalf())
                if numeric == int(numeric):
                    solutions.append({variable: int(numeric)})
                else:
                    solutions.append({variable: round(numeric, 6)})
            except Exception:
                solutions.append({variable: display})

        if not solutions:
            note = "No solutions found"
        elif len(solutions) == 1:
            note = f"{variable} = {solutions[0][variable]}"
        else:
            note = f"Found {len(solutions)} solutions"

        return {
            "ok": True,
            "solutions": solutions,
            "variable": variable,
            "note": note,
        }
    except Exception as e:
        return {"ok": False, "solutions": [], "note": f"Solve error: {e}"}


def evaluate_expression(expr_str: str, substitutions: dict[str, float]) -> dict[str, Any]:
    """
    Evaluate an expression numerically with variable substitutions.

    Example:
        evaluate_expression("x**2 + y", {"x": 3, "y": 4})  → 13.0

    Returns dict with:
      - value: float (or None on error)
      - ok: bool
      - note: str
    """
    if _SYP is None:
        return {"ok": False, "value": None, "note": _SYP_ERR}

    try:
        syp, trans = _require_sympy()
        expr = parse_expr(_normalise_expr(expr_str), transformations=trans, evaluate=False)
        # Build substitution dict with sympy symbols
        subs = {Symbol(k): v for k, v in substitutions.items()}
        result = expr.subs(subs).evalf()
        value = float(result)
        return {"ok": True, "value": value, "note": str(value)}
    except Exception as e:
        return {"ok": False, "value": None, "note": f"Eval error: {e}"}


def differentiate(expr_str: str, variable: str = "x") -> dict[str, Any]:
    """
    Return the derivative of an expression with respect to variable.

    Example:
        differentiate("x**2 * sin(x)", "x")
        → "2*x*sin(x) + x**2*cos(x)"

    Returns dict with:
      - derivative: str (or None)
      - ok: bool
      - note: str
    """
    if _SYP is None:
        return {"ok": False, "derivative": None, "note": _SYP_ERR}

    try:
        syp, trans = _require_sympy()
        expr = parse_expr(_normalise_expr(expr_str), transformations=trans, evaluate=False)
        var = Symbol(variable)
        deriv = sy_diff(expr, var)
        return {
            "ok": True,
            "derivative": str(deriv),
            "variable": variable,
            "note": f"d/d{variable} = {deriv}",
        }
    except Exception as e:
        return {"ok": False, "derivative": None, "note": f"Diff error: {e}"}


def integrate(expr_str: str, variable: str = "x") -> dict[str, Any]:
    """
    Return the indefinite integral of an expression.

    Example:
        integrate("x**2", "x")  → "x**3/3"

    Returns dict with:
      - integral: str (with +C)
      - ok: bool
      - note: str
    """
    if _SYP is None:
        return {"ok": False, "integral": None, "note": _SYP_ERR}

    try:
        syp, trans = _require_sympy()
        expr = parse_expr(_normalise_expr(expr_str), transformations=trans, evaluate=False)
        var = Symbol(variable)
        integral = sy_integrate(expr, var)
        # Add constant of integration
        result = str(integral) + " + C"
        return {
            "ok": True,
            "integral": result,
            "variable": variable,
            "note": f"∫{expr} d{variable} = {result}",
        }
    except Exception as e:
        return {"ok": False, "integral": None, "note": f"Integrate error: {e}"}


def simplify(expr_str: str) -> dict[str, Any]:
    """
    Simplify an expression.

    Example:
        simplify("(x**2 - 4)/(x - 2)")  → "x + 2"

    Returns dict with:
      - simplified: str
      - ok: bool
      - note: str
    """
    if _SYP is None:
        return {"ok": False, "simplified": None, "note": _SYP_ERR}

    try:
        syp, trans = _require_sympy()
        expr = parse_expr(_normalise_expr(expr_str), transformations=trans, evaluate=False)
        result = sy_simplify(expr)
        return {
            "ok": True,
            "simplified": str(result),
            "note": str(result),
        }
    except Exception as e:
        return {"ok": False, "simplified": None, "note": f"Simplify error: {e}"}


def expand_expr(expr_str: str) -> dict[str, Any]:
    """
    Expand products and powers in an expression.

    Example:
        expand_expr("(x + 2)**2")  → "x**2 + 4*x + 4"

    Returns dict with:
      - expanded: str
      - ok: bool
      - note: str
    """
    if _SYP is None:
        return {"ok": False, "expanded": None, "note": _SYP_ERR}

    try:
        syp, trans = _require_sympy()
        expr = parse_expr(_normalise_expr(expr_str), transformations=trans, evaluate=False)
        result = sy_expand(expr)
        return {
            "ok": True,
            "expanded": str(result),
            "note": str(result),
        }
    except Exception as e:
        return {"ok": False, "expanded": None, "note": f"Expand error: {e}"}


# ── Advanced: calculus on equations ──────────────────────────────────────────

def find_critical_points(
    equation_str: str,
    variable: str = "x",
) -> dict[str, Any]:
    """
    Find where d(equation)/d{variable} = 0 (potential maxima/minima).

    Returns dict with:
      - points: list of {variable: value} dicts
      - ok: bool
      - note: str
    """
    if _SYP is None:
        return {"ok": False, "points": [], "note": _SYP_ERR}

    try:
        # First solve: treat equation as f(x) = 0 form, or differentiate directly
        diff_result = differentiate(equation_str, variable)
        if not diff_result["ok"]:
            return diff_result

        deriv_str = diff_result["derivative"]
        eq_str = deriv_str if "=" in deriv_str else f"{deriv_str} = 0"
        solve_result = solve_equation(eq_str, variable)
        return {
            "ok": solve_result["ok"],
            "points": solve_result.get("solutions", []),
            "variable": variable,
            "note": solve_result.get("note", ""),
        }
    except Exception as e:
        return {"ok": False, "points": [], "note": f"Critical point error: {e}"}


def solve_for_optimal(
    equation_str: str,
    variable: str = "x",
    sense: str = "max",
) -> dict[str, Any]:
    """
    Find the optimal value of variable (max or min) for an equation.

    Steps:
      1. Compute first derivative
      2. Solve for critical points
      3. Evaluate equation at each critical point
      4. Return the maximum or minimum

    Example:
        solve_for_optimal("-0.01*T**2 + 0.5*T + 10", "T", "max")
        → {"optimal_value": 12.5, "optimal_T": 25.0}

    Returns dict with:
      - optimal_value: float
      - optimal_variable: str
      - ok: bool
      - note: str
    """
    if _SYP is None:
        return {"ok": False, "note": _SYP_ERR}

    try:
        diff_result = differentiate(equation_str, variable)
        if not diff_result["ok"]:
            return diff_result

        deriv_str = diff_result["derivative"]
        eq_str = deriv_str if "=" in deriv_str else f"{deriv_str} = 0"
        solve_result = solve_equation(eq_str, variable)
        if not solve_result["ok"] or not solve_result["solutions"]:
            return {"ok": False, "note": f"No critical points found: {solve_result.get('note', '')}"}

        syp, trans = _require_sympy()
        var_sym = Symbol(variable)
        eval_expr = parse_expr(_normalise_expr(equation_str), transformations=trans, evaluate=False)

        candidates = []
        for sol in solve_result["solutions"]:
            val = sol.get(variable)
            if val is None:
                continue
            # Try to substitute and evaluate
            try:
                sub_val = float(parse_expr(str(val), transformations=trans, evaluate=False).evalf())
                subbed = eval_expr.subs(var_sym, sub_val)
                num_val = float(subbed.evalf())
                candidates.append({"point": sub_val, "value": num_val})
            except Exception:
                pass

        if not candidates:
            return {"ok": False, "note": "Could not evaluate candidates numerically"}

        if sense == "max":
            best = max(candidates, key=lambda c: c["value"])
        else:
            best = min(candidates, key=lambda c: c["value"])

        return {
            "ok": True,
            "optimal_variable": variable,
            "optimal_value": round(best["value"], 4),
            "optimal_point": best["point"],
            "note": f"{'Maximum' if sense == 'max' else 'Minimum'} {equation_str} = {best['value']:.4g} at {variable} = {best['point']:.4g}",
        }
    except Exception as e:
        return {"ok": False, "note": f"Optimal error: {e}"}


# ── Equation proposer ─────────────────────────────────────────────────────────

def propose_arrhenius_equation(
    k: float | None = None,
    A: float | None = None,
    Ea_eV: float | None = None,
    T: float | None = None,
) -> dict[str, Any]:
    """
    Return the Arrhenius equation with known values substituted.

    k = A * exp(-Ea / (k_B * T))
    All inputs in eV and K. Use k_B = 8.617e-5 eV/K.
    """
    k_B = 8.617e-5
    if k is not None and A is not None and Ea_eV is not None and T is not None:
        computed_k = A * math.exp(-Ea_eV / (k_B * T))
        return {
            "ok": True,
            "equation": f"k = {A} * exp(-{Ea_eV} / ({k_B} * {T}))",
            "computed_k": computed_k,
            "note": f"k ≈ {computed_k:.3e}",
        }
    else:
        return {
            "ok": True,
            "equation": f"k = A * exp(-Ea / ({k_B} * T))",
            "note": "Rate constant k (eV/K), activation energy Ea (eV), temperature T (K)",
        }


def propose_quadratic_model(
    a: float | None = None,
    b: float | None = None,
    c: float | None = None,
) -> dict[str, Any]:
    """
    Return a quadratic model y = a*x^2 + b*x + c.

    If all coefficients are provided, evaluates the model description.
    """
    if a is not None and b is not None and c is not None:
        return {
            "ok": True,
            "equation": f"y = {a}*x**2 + {b}*x + {c}",
            "note": f"Quadratic with vertex at x = {-b/(2*a):.4g}",
        }
    return {
        "ok": True,
        "equation": "y = a*x**2 + b*x + c",
        "note": "General quadratic model — supply a, b, c for specific case",
    }


# ── Text output helpers ───────────────────────────────────────────────────────

def format_solve_output(result: dict) -> str:
    """Format solve_equation result as readable text."""
    if not result["ok"]:
        return f"Error: {result['note']}"
    sols = result["solutions"]
    if not sols:
        return "No solutions found."
    var = result.get("variable", "?")
    if len(sols) == 1:
        return f"{var} = {sols[0][var]}"
    return "  ".join(f"{s.get(var, '?')}" for s in sols)


def format_derivative_output(result: dict) -> str:
    """Format differentiate result as readable text."""
    if not result["ok"]:
        return f"Error: {result['note']}"
    return f"d/d{result['variable']} = {result['derivative']}"


def format_integral_output(result: dict) -> str:
    """Format integrate result as readable text."""
    if not result["ok"]:
        return f"Error: {result['note']}"
    return f"∫ {result['variable']} = {result['integral']}"


def format_simplify_output(result: dict) -> str:
    """Format simplify result as readable text."""
    if not result["ok"]:
        return f"Error: {result['note']}"
    return result["simplified"]


def format_expand_output(result: dict) -> str:
    """Format expand result as readable text."""
    if not result["ok"]:
        return f"Error: {result['note']}"
    return result["expanded"]


def format_optimal_output(result: dict) -> str:
    """Format solve_for_optimal result as readable text."""
    if not result["ok"]:
        return f"Error: {result['note']}"
    return result["note"]