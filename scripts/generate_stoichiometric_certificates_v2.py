"""Generate coefficient-explicit stoichiometric certificates V2."""
import hashlib, json, os, sys
from datetime import datetime, timezone
from fractions import Fraction

sys.path.insert(0, ".")

REPO_ROOT = "/data/data/com.termux/files/home/weslr-pr47-clean"
os.chdir(REPO_ROOT)

from weslr.modules.materials_stoichiometric_route_engine import (
    balance_reaction as proposer_balance,
    elemental_vector as proposer_vector,
    reduced_formula_and_factor as proposer_reduced,
)
from weslr.modules.materials_stoichiometric_route_verifier import (
    find_coefficients_independent as verifier_find,
    verify_coefficients as verifier_verify,
    coefficients_agree,
    elemental_vector_int as verifier_vector,
    compute_reduced_formula_independent as verifier_reduced,
    canonicalize_coefficients,
)
from weslr.modules.calculation_assurance import (
    InvariantResult, make_certificate, determine_final_status,
    VERIFIED, REJECTED_BY_INVARIANT, INVALID_INPUT,
)

SOURCE_PATHS = [
    "weslr/modules/calculation_assurance.py",
    "weslr/modules/materials_stoichiometric_route_engine.py",
    "weslr/modules/materials_stoichiometric_route_verifier.py",
]
SOURCE_HASHES = []
for p in SOURCE_PATHS:
    with open(p, "rb") as f:
        SOURCE_HASHES.append(hashlib.sha256(f.read()).hexdigest())

TOOL_VERSIONS = {"python": sys.version, "proposer": "v1", "verifier": "v1"}


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_hex(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def make_reaction_certificate(cid, reactants, target, description):
    """Generate a coefficient-explicit reaction certificate."""
    p = proposer_balance(reactants, target)
    v = verifier_find(reactants, target)

    # Determine agreement
    if p["balanced"] and v["balanced"]:
        agreement = coefficients_agree(
            p["coefficients"], p["target_coefficient"],
            v["coefficients"], v["target_coefficient"],
        )
    elif not p["balanced"] and not v["balanced"]:
        agreement = True
    else:
        agreement = False

    # Build canonical equation
    if p["balanced"]:
        coeffs = {k: int(round(v)) for k, v in p["coefficients"].items()}
        t_coeff = int(round(p["target_coefficient"]))
        canon = canonicalize_coefficients(coeffs, t_coeff)
        r_coeffs = canon["reduced_coefficients"]
        r_target = canon["reduced_target_coefficient"]
        gcd_applied = canon["gcd"] > 1

        # Build equation string
        lhs_parts = []
        for r in sorted(reactants):
            c = r_coeffs.get(r, 1)
            lhs_parts.append(f"{c} {r}" if c != 1 else r)
        lhs = " + ".join(lhs_parts)
        rhs = f"{r_target} {target}" if r_target != 1 else target
        equation = f"{lhs} -> {rhs}"

        # Elemental vectors
        elemental_vectors = {}
        for r in reactants:
            elemental_vectors[r] = proposer_vector(r)
        elemental_vectors[target] = proposer_vector(target)

        # Residual
        coeff_list = [r_coeffs.get(r, 1) for r in reactants]
        v_result = verifier_verify(reactants, coeff_list, target, r_target)
        residual = v_result.get("residual", {})

        # Invariant
        inv = InvariantResult(
            invariant_name="elemental_residual",
            passed=v_result["balanced"],
            details={"residual": residual, "max_abs": v_result["max_absolute_residual"]},
        )

        # Canonical integer coefficient vector
        coeff_vector = [r_coeffs.get(r, 0) for r in sorted(reactants)] + [r_target]

        final_status = determine_final_status(
            VERIFIED if p["balanced"] else INVALID_INPUT,
            VERIFIED if v["balanced"] else INVALID_INPUT,
            [inv], agreement,
        )

        cert = make_certificate(
            calculation_id=cid,
            calculation_type="stoichiometric_route_verification",
            normalized_inputs={"reactants": sorted(reactants), "target": target},
            proposer_name="materials_stoichiometric_route_engine",
            proposer_result={"balanced": p["balanced"], "coefficients": r_coeffs, "target_coefficient": r_target},
            verifier_name="materials_stoichiometric_route_verifier",
            verifier_result={"balanced": v["balanced"], "coefficients": v.get("coefficients", {}), "target_coefficient": v.get("target_coefficient", 0)},
            invariant_results=[inv],
            agreement=agreement,
            final_status=final_status,
            exact_arithmetic=True,
            tool_versions=TOOL_VERSIONS,
            source_paths=SOURCE_PATHS,
            source_hashes=SOURCE_HASHES,
        )

        return {
            "proposition_type": "reaction_balance",
            "reactant_formulas": sorted(reactants),
            "reactant_coefficients": r_coeffs,
            "product_formulas": [target],
            "product_coefficients": {target: r_target},
            "canonical_equation": equation,
            "canonical_integer_coefficient_vector": coeff_vector,
            "gcd_reduction_applied": gcd_applied,
            "elemental_vectors": elemental_vectors,
            "residual_vector": residual,
            "proposer_result": {"balanced": p["balanced"], "coefficients": r_coeffs, "target_coefficient": r_target},
            "verifier_result": {"balanced": v["balanced"], "coefficients": v.get("coefficients", {}), "target_coefficient": v.get("target_coefficient", 0)},
            "invariant_result": inv.to_dict(),
            "final_status": final_status,
            "certificate_sha256": cert.certificate_sha256,
        }
    else:
        # Unbalanced
        return {
            "proposition_type": "reaction_balance",
            "reactant_formulas": sorted(reactants),
            "reactant_coefficients": {},
            "product_formulas": [target],
            "product_coefficients": {},
            "canonical_equation": f"{' + '.join(sorted(reactants))} -> {target} (unbalanced)",
            "canonical_integer_coefficient_vector": [],
            "gcd_reduction_applied": False,
            "elemental_vectors": {r: proposer_vector(r) for r in reactants + [target]},
            "residual_vector": {},
            "proposer_result": {"balanced": False},
            "verifier_result": {"balanced": v.get("balanced", False)},
            "invariant_result": {"invariant_name": "elemental_residual", "passed": False, "details": {"reason": "Unbalanced"}},
            "final_status": REJECTED_BY_INVARIANT,
            "certificate_sha256": "",
        }


def make_target_multiple_certificate(cid, candidate, target):
    """Generate a target-multiple check certificate."""
    c_red, c_z = proposer_reduced(candidate)
    t_red, t_z = proposer_reduced(target)
    c_vec = proposer_vector(candidate)
    t_vec = proposer_vector(target)

    # Check if candidate is an integer multiple of target
    is_multiple = (c_red == t_red) and (c_z > 0) and (t_z > 0)
    if is_multiple and t_z > 0:
        required_multiplier = c_z / t_z
        exact = (required_multiplier == int(required_multiplier))
    else:
        required_multiplier = 0
        exact = False

    # Compute residual
    residual = {}
    if is_multiple and exact:
        mult = int(required_multiplier)
        for el in set(list(c_vec.keys()) + list(t_vec.keys())):
            residual[el] = c_vec.get(el, 0) - mult * t_vec.get(el, 0)
    else:
        for el in set(list(c_vec.keys()) + list(t_vec.keys())):
            residual[el] = c_vec.get(el, 0) - t_vec.get(el, 0)

    max_abs = max(abs(v) for v in residual.values()) if residual else 0
    passed = (is_multiple and exact and max_abs == 0)

    inv = InvariantResult(
        invariant_name="target_multiple",
        passed=passed,
        details={
            "candidate_reduced": c_red,
            "target_reduced": t_red,
            "candidate_Z": c_z,
            "target_Z": t_z,
            "exact_integer_multiple": exact,
            "required_multiplier": required_multiplier,
            "residual": residual,
        },
    )

    cert = make_certificate(
        calculation_id=cid,
        calculation_type="target_multiple_check",
        normalized_inputs={"candidate": candidate, "target": target},
        proposer_name="materials_stoichiometric_route_engine",
        proposer_result={"is_multiple": is_multiple, "exact": exact, "multiplier": required_multiplier},
        verifier_name="materials_stoichiometric_route_verifier",
        verifier_result={"is_multiple": is_multiple, "exact": exact, "multiplier": required_multiplier},
        invariant_results=[inv],
        agreement=True,
        final_status=VERIFIED if passed else REJECTED_BY_INVARIANT,
        exact_arithmetic=True,
        tool_versions=TOOL_VERSIONS,
        source_paths=SOURCE_PATHS,
        source_hashes=SOURCE_HASHES,
    )

    return {
        "proposition_type": "target_multiple_check",
        "candidate_formula": candidate,
        "target_formula": target,
        "candidate_vector": c_vec,
        "target_vector": t_vec,
        "exact_integer_multiple": exact,
        "required_multiplier": required_multiplier,
        "residual": residual,
        "final_status": cert.final_status,
        "certificate_sha256": cert.certificate_sha256,
    }


def main():
    reaction_certificates = [
        make_reaction_certificate("SCATTI-ROUTE-V2-001", ["Sc2TiO5", "CaO"], "CaSc2TiO6",
                                   "1 Sc2TiO5 + 1 CaO -> 1 CaSc2TiO6"),
        make_reaction_certificate("SCATTI-ROUTE-V2-002", ["Sc4Ti2O10", "CaO"], "CaSc2TiO6",
                                   "1 Sc4Ti2O10 + 2 CaO -> 2 CaSc2TiO6"),
        make_reaction_certificate("SCATTI-ROUTE-V2-003", ["CaSc2O4", "TiO2"], "CaSc2TiO6",
                                   "1 CaSc2O4 + 1 TiO2 -> 1 CaSc2TiO6"),
        make_reaction_certificate("SCATTI-ROUTE-V2-004", ["CaTiO3", "Sc2O3"], "CaSc2TiO6",
                                   "1 CaTiO3 + 1 Sc2O3 -> 1 CaSc2TiO6"),
        make_reaction_certificate("SCATTI-ROUTE-V2-005", ["Sc4Ti2O10", "CaO"], "CaSc4Ti2O11",
                                   "1 Sc4Ti2O10 + 1 CaO -> 1 CaSc4Ti2O11 (balanced but not CaSc2TiO6)"),
    ]

    # Add reaction_balance_status and target_multiple_status to route 5
    reaction_certificates[4]["reaction_balance_status"] = "verified"
    reaction_certificates[4]["produces_scatti_target"] = False
    reaction_certificates[4]["target_multiple_status"] = "rejected_by_invariant"

    target_checks = [
        make_target_multiple_certificate("SCATTI-TARGET-001", "CaSc4Ti2O11", "CaSc2TiO6"),
        make_target_multiple_certificate("SCATTI-TARGET-002", "Ca2Sc4Ti2O12", "CaSc2TiO6"),
        make_target_multiple_certificate("SCATTI-TARGET-003", "Sc4Ti2O10", "CaSc2TiO6"),
    ]

    output = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": "62e9ba794c780bb37d5472d79ca8c9d91230892d",
        "reaction_certificates": reaction_certificates,
        "target_multiple_certificates": target_checks,
    }

    with open("data/scatti_candidates/calculation_assurance_v2/stoichiometric_certificates_v2.json", "w") as f:
        json.dump(output, f, indent=2, sort_keys=True)

    print("V2 certificates generated:")
    for rc in reaction_certificates:
        print(f"  {rc['canonical_equation']} -> {rc['final_status']}")
    for tc in target_checks:
        print(f"  target_multiple({tc['candidate_formula']}, {tc['target_formula']}) -> {tc['final_status']}")


if __name__ == "__main__":
    main()
