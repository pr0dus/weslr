#!/usr/bin/env python3
"""Phase 6.2 Symbolic Mathematics — test suite."""
import sys
sys.path.insert(0, ".")

from weslr.symbolic_math import (
    is_available, parse_equation, solve_equation, evaluate_expression,
    differentiate, integrate, simplify, expand_expr,
    find_critical_points, solve_for_optimal,
    propose_arrhenius_equation, propose_quadratic_model,
    format_solve_output, format_derivative_output,
    format_integral_output, format_simplify_output,
    format_expand_output, format_optimal_output,
)

SKIP_IF_UNAVAILABLE = not is_available()


def test_is_available():
    assert is_available() is True, "sympy should be available after pip install"


def test_parse_equation():
    r = parse_equation("3*x + 5 = 20")
    assert r["ok"] is True
    assert r["lhs"] == "3*x + 5"
    assert r["rhs"] == "20"
    assert r["variable"] == "x"

    r2 = parse_equation("a*x + b = c")
    assert r2["ok"] is True
    assert r2["variable"] == "x"  # first free symbol found (auto-detected)

    r3 = parse_equation("no equals")
    assert r3["ok"] is False


def test_solve_linear():
    tests = [
        ("2*x + 3 = 7", "x", 2),
        ("3*x - 9 = 0", "x", 3),
        ("x/2 + 1 = 3", "x", 4),
        ("x**2 - 4 = 0", None, [-2, 2]),  # quadratic, two solutions
    ]
    for eq, var, expected in tests:
        r = solve_equation(eq, var)
        assert r["ok"], f"solve({eq}) failed: {r['note']}"
        if isinstance(expected, list):
            assert len(r["solutions"]) == len(expected), f"Expected {len(expected)} solutions for {eq}"
        else:
            val = r["solutions"][0].get(var if var else r["variable"])
            assert val == expected, f"solve({eq}): expected {expected}, got {val}"


def test_solve_explicit_variable():
    r = solve_equation("a*x = b", "x")
    assert r["ok"]
    assert r["variable"] == "x"


def test_evaluate_basic():
    r = evaluate_expression("x**2 + y", {"x": 3, "y": 4})
    assert r["ok"] and r["value"] == 13.0

    r2 = evaluate_expression("sin(pi/2)", {})
    assert r2["ok"]  # pi ≈ 3.14, sin ≈ 1


def test_evaluate_errors():
    r = evaluate_expression("x**2", {"x": "not_a_number"})
    assert r["ok"] is False

    r2 = evaluate_expression("1/0", {})
    assert r2["ok"] is False


def test_differentiate_basic():
    tests = [
        ("x**2", "x", "2*x"),
        ("x**3", "x", "3*x**2"),
        ("sin(x)", "x", "cos(x)"),
        ("cos(x)", "x", "-sin(x)"),
        ("exp(x)", "x", "exp(x)"),
        ("exp(-0.5*x)", "x", "-0.5*exp(-0.5*x)"),
        ("x**2*sin(x)", "x", "x**2*cos(x) + 2*x*sin(x)"),
        ("log(x)", "x", "1/x"),
    ]
    for expr, var, expected in tests:
        r = differentiate(expr, var)
        assert r["ok"], f"differentiate({expr}, {var}) failed: {r['note']}"
        assert expected in r["derivative"], f"differentiate({expr}): expected {expected}, got {r['derivative']}"


def test_integrate_basic():
    tests = [
        ("x**2", "x", "x**3/3"),
        ("x**3", "x", "x**4/4"),
        ("sin(x)", "x", "-cos(x)"),
        ("cos(x)", "x", "sin(x)"),
        ("exp(x)", "x", "exp(x)"),
        ("1/x", "x", "log(x)"),
        ("exp(-x)", "x", "-exp(-x)"),
    ]
    for expr, var, expected_pat in tests:
        r = integrate(expr, var)
        assert r["ok"], f"integrate({expr}, {var}) failed: {r['note']}"
        assert expected_pat in r["integral"], f"integrate({expr}): expected {expected_pat} in {r['integral']}"


def test_simplify_basic():
    tests = [
        ("(x**2 - 4)/(x - 2)", "x + 2"),
        ("(x+y)**2 - x**2 - 2*x*y", "y**2"),
        ("sin(x)**2 + cos(x)**2", "1"),
        ("(x**2 - 1)/(x - 1)", "x + 1"),
        ("x + x", "2*x"),
        ("x*0", "0"),
    ]
    for expr, expected in tests:
        r = simplify(expr)
        assert r["ok"], f"simplify({expr}) failed: {r['note']}"
        assert r["simplified"] == expected, f"simplify({expr}): expected {expected}, got {r['simplified']}"


def test_expand_basic():
    tests = [
        ("(x+2)**2", "x**2 + 4*x + 4"),
        ("(x+y)**2", "x**2 + 2*x*y + y**2"),
        ("(x+1)*(x-1)", "x**2 - 1"),
        ("2*(x+3)", "2*x + 6"),
    ]
    for expr, expected in tests:
        r = expand_expr(expr)
        assert r["ok"], f"expand({expr}) failed: {r['note']}"
        got = " ".join(r["expanded"].split())
        exp = " ".join(expected.split())
        assert got == exp, f"expand({expr}): expected {expected}, got {r['expanded']}"
    # 3-variable: check all terms present (order varies)
    r3 = expand_expr("(x+y+z)**2")
    exp3 = r3["expanded"]
    for term in ["x**2", "y**2", "z**2", "2*x*y", "2*x*z", "2*y*z"]:
        assert term in exp3, f"expand((x+y+z)**2): missing {term} in {exp3}"


def test_find_critical_points():
    r = find_critical_points("-0.01*x**2 + 0.5*x + 10", "x")
    assert r["ok"]
    # Solutions should include x=25
    pts = r["points"]
    assert any(abs(float(p.get("x", 0)) - 25) < 0.1 for p in pts), f"No critical point near 25: {pts}"


def test_solve_for_optimal():
    tests = [
        ("-0.01*x**2 + 0.5*x + 10", "x", "max", 16.25, 25.0),
        ("2*x**2 - 8*x + 6", "x", "min", -2.0, 2.0),
    ]
    for eq, var, sense, exp_val, exp_pt in tests:
        r = solve_for_optimal(eq, var, sense)
        assert r["ok"], f"solve_for_optimal({eq}, {var}, {sense}) failed: {r['note']}"
        assert abs(r["optimal_value"] - exp_val) < 0.01, f"optimal value for {eq}: expected {exp_val}, got {r['optimal_value']}"
        assert abs(r["optimal_point"] - exp_pt) < 0.01, f"optimal point for {eq}: expected {exp_pt}, got {r['optimal_point']}"


def test_format_functions():
    r = solve_equation("2*x + 3 = 7")
    text = format_solve_output(r)
    assert "x = 2" in text

    r2 = differentiate("x**2", "x")
    text2 = format_derivative_output(r2)
    assert "2*x" in text2

    r3 = integrate("x**2", "x")
    text3 = format_integral_output(r3)
    assert "x**3/3" in text3

    r4 = simplify("(x**2 - 4)/(x - 2)")
    text4 = format_simplify_output(r4)
    assert text4 == "x + 2"

    r5 = expand_expr("(x+2)**2")
    text5 = format_expand_output(r5)
    assert text5 == "x**2 + 4*x + 4"

    r6 = solve_for_optimal("-0.01*x**2 + 0.5*x + 10", "x", "max")
    text6 = format_optimal_output(r6)
    assert "Maximum" in text6


def test_propose_arrhenius():
    r = propose_arrhenius_equation(k=1.0, A=1e10, Ea_eV=0.5, T=300)
    assert r["ok"]
    assert "k =" in r["equation"]

    r2 = propose_arrhenius_equation()  # general form
    assert r2["ok"]
    assert "k = A * exp" in r2["equation"]


def test_propose_quadratic():
    r = propose_quadratic_model(a=-0.01, b=0.5, c=10)
    assert r["ok"]
    assert "vertex" in r["note"]


def test_error_handling_invalid_expr():
    # @ operator is invalid in sympy expressions
    r = differentiate("x @ y", "x")
    assert r["ok"] is False, f"expected differentiate to fail on 'x @ y', got ok={r['ok']}"

    r2 = integrate("x @ y", "x")
    assert r2["ok"] is False, f"expected integrate to fail on 'x @ y', got ok={r2['ok']}"

    r3 = expand_expr("(x @ y)**2")
    assert r3["ok"] is False


def test_evaluate_scientific_notation():
    r = evaluate_expression("1e-5 * x**2", {"x": 3})
    assert r["ok"]
    assert r["value"] == 9e-5


# ── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        test_is_available, test_parse_equation, test_solve_linear,
        test_solve_explicit_variable, test_evaluate_basic, test_evaluate_errors,
        test_differentiate_basic, test_integrate_basic, test_simplify_basic,
        test_expand_basic, test_find_critical_points, test_solve_for_optimal,
        test_format_functions, test_propose_arrhenius, test_propose_quadratic,
        test_error_handling_invalid_expr, test_evaluate_scientific_notation,
    ]
    n_ok = 0
    n_fail = 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
            n_ok += 1
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}")
            n_fail += 1
        except Exception as e:
            print(f"ERR  {t.__name__}: {type(e).__name__}: {e}")
            n_fail += 1
    print(f"\n{n_ok}/{len(tests)} tests passed")
    if n_fail:
        sys.exit(1)