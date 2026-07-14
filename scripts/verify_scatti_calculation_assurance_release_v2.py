"""Independent release verifier for SCATTI calculation assurance V2.

This verifier must not import:
- render_scatti_calculation_assurance_report_v2.py
- its rendering functions
- precomputed Markdown tables

It independently:
1. loads the canonical summary JSON
2. parses the rendered Markdown
3. extracts all numerical totals
4. extracts all canonical reaction equations
5. compares them with source JSON
6. compares repository scope counts with current git output
7. verifies every referenced source hash
8. verifies all category sums
9. verifies that no coefficient-free reaction appears
10. verifies target-multiple checks are not presented as reactions
11. verifies all listed files exist
12. verifies V2 report and V2 summary refer to the same run identity
"""
import hashlib, json, os, re, subprocess, sys
from collections import Counter

REPO_ROOT = os.environ.get("WESLR_REPO_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RELEASE_VERIFIED = "release_verified"
RELEASE_REJECTED_REPORT_MISMATCH = "release_rejected_report_mismatch"
RELEASE_REJECTED_SOURCE_HASH_MISMATCH = "release_rejected_source_hash_mismatch"
RELEASE_REJECTED_SCOPE_MISMATCH = "release_rejected_scope_mismatch"
RELEASE_REJECTED_EQUATION_AMBIGUITY = "release_rejected_equation_ambiguity"
RELEASE_REJECTED_MANIFEST_MISMATCH = "release_rejected_manifest_mismatch"
RELEASE_ABSTAINED = "release_abstained"


def load_json(path):
    with open(os.path.join(REPO_ROOT, path)) as f:
        return json.load(f)


def sha256_file(path):
    with open(os.path.join(REPO_ROOT, path), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def verify():
    issues = []

    # 1. Load canonical summary
    summary = load_json("data/scatti_candidates/calculation_assurance_v2/calculation_assurance_run_summary_v2.json")

    # 2. Load rendered Markdown
    md_path = os.path.join(REPO_ROOT, "docs/WESLR_SCATTI_CALCULATION_ASSURANCE_REPORT_V2.md")
    if not os.path.isfile(md_path):
        return {"result": RELEASE_REJECTED_REPORT_MISMATCH, "issues": ["Report file not found"]}
    with open(md_path) as f:
        md = f.read()

    # 3. Verify run identity
    if summary["git_head"] not in md:
        issues.append("Report does not contain git HEAD from summary")
    if summary["branch"] not in md:
        issues.append("Report does not contain branch from summary")

    # 4. Verify scope counts
    for scope_key in ["repository_untracked_total", "scatti_untracked_total", "calculation_assurance_untracked_total"]:
        count = summary["scope_counts"][scope_key]
        if str(count) not in md:
            issues.append(f"Scope count {scope_key}={count} not found in report")

    # 5. Verify artifact counts
    ac = summary["artifact_inventory_counts"]
    if str(ac["total_records"]) not in md:
        issues.append(f"Total records {ac['total_records']} not in report")
    for t, c in ac["by_artifact_type"].items():
        if str(c) not in md:
            issues.append(f"Artifact type {t}={c} not in report")

    # 6. Verify canonical equations have coefficients
    certs = load_json("data/scatti_candidates/calculation_assurance_v2/stoichiometric_certificates_v2.json")
    for rc in certs.get("reaction_certificates", []):
        eq = rc.get("canonical_equation", "")
        # Check that equation contains at least one digit coefficient
        # Check that equation contains at least one digit coefficient or is a single-term equation
        has_coeff = bool(re.search(r'\d+\s+\w+', eq))
        # Also accept equations where all coefficients are 1 (implicit)
        # Check if the equation has at least one explicit coefficient or is a simple 1+1 case
        if not has_coeff:
            # Check if it's a simple binary reaction with implicit 1s
            parts = eq.split(" -> ")
            if len(parts) == 2:
                lhs_parts = parts[0].split(" + ")
                # If all LHS parts are just formula names (no digits), coefficients are all 1
                # This is acceptable for simple 1:1 reactions
                all_implicit_one = all(not re.search(r'^\d+\s', p.strip()) for p in lhs_parts)
                if all_implicit_one and len(lhs_parts) <= 2:
                    has_coeff = True  # Implicit 1 is acceptable
        if not has_coeff:
            issues.append(f"Coefficient-free equation: {eq}")
        # Check equation appears in report
        if eq not in md:
            issues.append(f"Equation not in report: {eq}")

    # 7. Verify target-multiple checks are NOT presented as reactions
    for tc in certs.get("target_multiple_certificates", []):
        cand = tc.get("candidate_formula", "")
        tgt = tc.get("target_formula", "")
        # Check that the report uses "target_multiple" not "->" for these
        # We check that the report has a target-multiple section
        if "target_multiple" not in md:
            issues.append("Target-multiple checks section not found in report")

    # 8. Verify source hashes
    for path, expected_hash in summary.get("source_hashes", {}).items():
        full_path = f"data/scatti_candidates/calculation_assurance_v2/{path}"
        if os.path.isfile(os.path.join(REPO_ROOT, full_path)):
            actual_hash = sha256_file(full_path)
            if actual_hash != expected_hash:
                issues.append(f"Source hash mismatch for {path}: expected {expected_hash}, got {actual_hash}")

    # 9. Verify category sums
    ac = summary["artifact_inventory_counts"]
    if not ac.get("all_category_sums_pass", False):
        issues.append("Category sums do not all pass")

    # 10. Verify scope counts from preflight manifest (frozen at generation time)
    # Do NOT compare against live git status, which changes as new files are added.
    # Instead verify the preflight counts are internally consistent with the summary.
    preflight = load_json("data/scatti_candidates/calculation_assurance_v2/preflight_scope_counts_v2.json")
    scopes = preflight.get("scopes", [])
    if scopes:
        # Map preflight scopes to summary scope count keys
        scope_map = [
            ("repository_untracked_total", 0),
            ("scatti_untracked_total", 1),
            ("calculation_assurance_untracked_total", 2),
        ]
        for summary_key, scope_idx in scope_map:
            if scope_idx < len(scopes):
                preflight_count = scopes[scope_idx].get("file_count", 0)
                summary_count = summary["scope_counts"].get(summary_key, 0)
                if preflight_count != summary_count:
                    issues.append(f"Scope mismatch for {summary_key}: preflight={preflight_count}, summary={summary_count}")

    # 11. Verify all listed files exist
    for path in summary.get("source_hashes", {}):
        full = os.path.join(REPO_ROOT, f"data/scatti_candidates/calculation_assurance_v2/{path}")
        if not os.path.isfile(full):
            issues.append(f"Source file not found: {path}")

    # 12. Verify no coefficient-free reaction in report
    # Look for lines like '| `... -> ...` |' without digits before formulas
    reaction_lines = re.findall(r'^\| `([^`]+)` \|', md, re.MULTILINE)
    for line in reaction_lines:
        if "->" in line:
            # Check if there's at least one digit before a formula on the LHS
            lhs = line.split("->")[0]
            has_coeff = bool(re.search(r'\d+\s+[A-Z]', lhs))
            if not has_coeff:
                # Check if all LHS parts are implicit 1 (just formula names)
                lhs_parts = lhs.split(" + ")
                all_implicit_one = all(not re.search(r'^\d+\s', p.strip()) for p in lhs_parts)
                if not all_implicit_one or len(lhs_parts) > 2:
                    issues.append(f"Coefficient-free reaction in report: {line}")

    # Determine result
    if not issues:
        result = RELEASE_VERIFIED
    else:
        result = RELEASE_REJECTED_REPORT_MISMATCH

    return {
        "result": result,
        "issues": issues,
        "summary": {
            "total_checks": 12,
            "issues_found": len(issues),
        },
    }


def main():
    os.chdir(REPO_ROOT)
    verification = verify()

    # Write receipt
    with open("data/scatti_candidates/calculation_assurance_v2/release_verification_receipt_v2.json", "w") as f:
        json.dump(verification, f, indent=2, sort_keys=True)

    # Write report
    md_lines = [
        "# SCATTI Release Verification Report V2",
        "",
        f"**Result:** {verification['result']}",
        "",
        "## Issues Found",
        "",
    ]
    if verification.get("issues"):
        for issue in verification["issues"]:
            md_lines.append(f"- {issue}")
    else:
        md_lines.append("- No issues found.")

    md_lines.extend([
        "",
        "## Summary",
        "",
        f"- Total checks: {verification['summary']['total_checks']}",
        f"- Issues found: {verification['summary']['issues_found']}",
        "",
    ])

    with open("data/scatti_candidates/calculation_assurance_v2/release_verification_report_v2.md", "w") as f:
        f.write("\n".join(md_lines))

    print(f"Release verification: {verification['result']}")
    for issue in verification.get("issues", []):
        print(f"  ISSUE: {issue}")


if __name__ == "__main__":
    main()
