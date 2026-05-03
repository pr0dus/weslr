#!/usr/bin/env python3
"""Test physics_constraints.py"""
import sys
sys.path.insert(0, '.')
from weslr.physics_constraints import check_charge_balance, validate_hypothesis, check_forbidden_patterns, _load_rules

print("=== check_charge_balance ===")
charge_tests = [
    ("H2O", True), ("NaCl", True), ("Fe2O3", True), ("Cu2ZnSnSe4", True),
    ("C6H12O6", True), ("H999", False), ("NaCl2", False),
    ("Ca(OH)2", True), ("Na2SO4", True), ("H2SO4", True), ("CaCO3", True),
    ("CuSO4", True), ("(NH4)2SO4", True), ("NH4Cl", True),
    ("SO4", True), ("NO3", True), ("Fe3O4", True),
]
n_ok = 0
for f, want in charge_tests:
    r = check_charge_balance(f)
    ok = "OK" if r.get("feasible") == want else "FAIL"
    if r.get("feasible") == want: n_ok += 1
    print(f"  {ok} {f}: feasible={r.get('feasible','?')} net={r.get('net_charge')} note={r['feasibility_note'][:40]}")
print(f"  → {n_ok}/{len(charge_tests)} charge balance tests passed\n")

print("=== Forbidden patterns ===")
rules = _load_rules()
forbidden_tests = [
    ("efficiency 150%", False), ("150% efficiency from nothing", False),
    ("negative mass density", False), ("efficiency over unity with no energy input", True),
    ("may improve efficiency to 85%", True), ("efficiency > 100%", False),
    ("efficiency > 1.0", False), ("efficiency 85%", True),
    ("perpetual motion machine has 300% efficiency", False),
    ("efficiency 0.85", True), ("efficiency 50%", True),
    ("gains energy with 150% efficiency from nothing", False),
    ("efficiency 99%", True), ("efficiency 120%", False),
    ("negative density material", False),
]
n_ok = 0
for text, want in forbidden_tests:
    r = check_forbidden_patterns(text, rules.get("forbidden_transformations", []))
    ok = "OK" if r["passes"] == want else "FAIL"
    if r["passes"] == want: n_ok += 1
    print(f"  {ok} {text[:45]}: passes={r['passes']}")
print(f"  → {n_ok}/{len(forbidden_tests)} forbidden pattern tests passed\n")

print("=== Hypothesis validation ===")
hyps = [
    ({"name": "Kesterite alloy", "formula": "Cu2ZnSnSe4", "bandgap": 1.5, "domain": "materials_science"}, True),
    ({"name": "Sulfuric acid", "formula": "H2SO4"}, True),
    ({"name": "Glucose", "formula": "C6H12O6"}, True),
    ({"name": "Ca(OH)2 supplement", "formula": "Ca(OH)2", "dose": 50, "domain": "biology"}, True),
    ({"name": "Neg bandgap", "bandgap": -0.5, "domain": "materials_science"}, False),
    ({"name": "Perpetual motion", "predicted_effect": "gains energy with 150% efficiency from nothing"}, False),
    ({"name": "H999 formula", "formula": "H999"}, False),
    ({"name": "Toxic dose", "dose": 5000, "domain": "biology"}, True),
    ({"name": "Efficiency 120%", "efficiency": 120, "domain": "materials_science"}, False),
    ({"name": "Efficiency 85%", "efficiency": 85, "domain": "materials_science"}, True),
]
n_ok = 0
for h, want in hyps:
    v = validate_hypothesis(h, domain=h.get("domain", "chemistry"))
    ok = "OK" if v["passed"] == want else "FAIL"
    if v["passed"] == want: n_ok += 1
    print(f"  {ok} {h['name']}: passed={v['passed']} (want {want})")
    if v["hard_violations"]:
        for viol in v["hard_violations"][:1]:
            print(f"      -> {viol[:80]}")
print(f"  → {n_ok}/{len(hyps)} hypothesis validation tests passed\n")

print("All done.")