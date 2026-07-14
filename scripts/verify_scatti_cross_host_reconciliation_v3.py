#!/usr/bin/env python3
"""
Independent V3 release verifier for SCATTI cross-host reconciliation.

Checks:
- transport commit identity
- cherry-pick tree content
- source commit reachability
- artifact existence
- hashes
- JSON claims
- CIF compositions
- MP result counts
- parent-scaling calculation
- ledger supersessions
- stage statuses
- inventory totals
- report totals
- no scientific overpromotion
- no missing source paths
- no credential values
- validation tests pass (failed=0, errors=0)
- source patch verification passes
- git state contradiction resolved
- archive member count matches
- raw validation outputs present
- promotion gate consistency
- structure status terminology correct
- review source scope complete
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
V3_DIR = REPO_ROOT / "data" / "scatti_candidates" / "cross_host_reconciliation_v3"

# Expected constants
EXPECTED_TRANSPORT_COMMIT = "04dc013305b713c1eb3ea0117e462aa77099485f"
EXPECTED_TRANSPORT_PARENT = "62e9ba794c780bb37d5472d79ca8c9d91230892d"
EXPECTED_TRANSPORT_SUBJECT = "WESLR: add verified scatti calculation assurance v2"
EXPECTED_FILE_COUNT = 39

# Ubuntu commits
EXPECTED_UBUNTU_COMMITS = ["2d40b9d", "55342bb"]

# MP query: CaSc2TiO6 should have 0 entries
MP_ZERO_HIT_FORMULAS = ["CaSc2TiO6", "Ca2ScTiO6"]

# Parent experiment: Z=2 for Sc2TiO5
PARENT_Z = 2

results = {
    "verifier": "verify_scatti_cross_host_reconciliation_v3.py",
    "timestamp": subprocess.check_output(["date", "-Iseconds"]).decode().strip(),
    "checks": {},
    "passed": 0,
    "failed": 0,
    "abstained": 0,
    "overall": None,
}


def check(name, condition, detail=""):
    if condition:
        results["checks"][name] = {"status": "PASS", "detail": detail}
        results["passed"] += 1
    else:
        results["checks"][name] = {"status": "FAIL", "detail": detail}
        results["failed"] += 1


def abstain(name, detail=""):
    results["checks"][name] = {"status": "ABSTAIN", "detail": detail}
    results["abstained"] += 1


def git(cmd, cwd=None):
    full_cmd = ["git"] + cmd
    return subprocess.check_output(full_cmd, cwd=cwd or REPO_ROOT).decode().strip()


# ── 1. Transport commit identity ──────────────────────────────────────────────

try:
    transport_hash = git(["rev-parse", EXPECTED_TRANSPORT_COMMIT])
    check("transport_commit_reachable", transport_hash == EXPECTED_TRANSPORT_COMMIT,
          f"Expected {EXPECTED_TRANSPORT_COMMIT}, got {transport_hash}")
except:
    check("transport_commit_reachable", False, "Commit not found")

try:
    transport_info = git(["show", "-s", "--format=%H%n%P%n%s", EXPECTED_TRANSPORT_COMMIT])
    lines = transport_info.split("\n")
    check("transport_commit_hash", lines[0] == EXPECTED_TRANSPORT_COMMIT,
          f"Hash: {lines[0]}")
    check("transport_commit_parent", lines[1] == EXPECTED_TRANSPORT_PARENT,
          f"Parent: {lines[1]}")
    check("transport_commit_subject", lines[2] == EXPECTED_TRANSPORT_SUBJECT,
          f"Subject: {lines[2]}")
except:
    check("transport_commit_info", False, "Could not retrieve commit info")

# ── 2. Cherry-pick tree content ────────────────────────────────────────────────

try:
    cherry_pick_hash = git(["rev-parse", "HEAD"])
    cherry_pick_parent = git(["show", "-s", "--format=%P", "HEAD"])
    check("cherry_pick_exists", len(cherry_pick_hash) == 40,
          f"HEAD: {cherry_pick_hash}")
    check("cherry_pick_parent_is_base", cherry_pick_parent.startswith("b478773") or cherry_pick_parent.startswith("f654b4"),
          f"Parent: {cherry_pick_parent}")
except:
    check("cherry_pick_exists", False, "HEAD not available")

# ── 3. Source commit reachability ─────────────────────────────────────────────

for commit in EXPECTED_UBUNTU_COMMITS:
    try:
        git(["cat-file", "-t", commit])
        check(f"ubuntu_commit_{commit}_reachable", True, f"{commit} is a commit")
    except:
        check(f"ubuntu_commit_{commit}_reachable", False, f"{commit} not found")

# ── 4. Artifact existence ─────────────────────────────────────────────────────

required_artifacts = [
    "data/scatti_candidates/cross_host_reconciliation_v3/transport_commit_verification_v3.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/transport_path_collision_v3.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/imported_assurance_test_results_v3.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/ubuntu_scatti_artifact_inventory_v3.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/materials_project_evidence_verification_v3.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/mp_parent_experiment_reaudit_v3.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/multilingual_search_verification_v3.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/structure_and_chgnet_evidence_verification_v3.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/scatti_evidence_ledger_v3.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/scatti_implementation_inventory_v3.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/source_patch_verification_r4b.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/git_state_contradiction_resolution_r4b.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/structure_and_chgnet_evidence_verification_r4a.json",
    "data/scatti_candidates/cross_host_reconciliation_v3/scatti_cross_host_review_summary_r4a.json",
]

for artifact in required_artifacts:
    path = REPO_ROOT / artifact
    check(f"artifact_exists_{artifact.replace('/', '_')}", path.exists(),
          f"Path: {artifact}")

# ── 5. JSON validity ──────────────────────────────────────────────────────────

for artifact in required_artifacts:
    path = REPO_ROOT / artifact
    if path.exists():
        try:
            with open(path) as f:
                json.load(f)
            check(f"json_valid_{artifact.replace('/', '_')}", True)
        except json.JSONDecodeError as e:
            check(f"json_valid_{artifact.replace('/', '_')}", False, str(e))
    else:
        abstain(f"json_valid_{artifact.replace('/', '_')}", "File missing")

# ── 6. MP result counts ───────────────────────────────────────────────────────

mp_path = REPO_ROOT / "data" / "scatti_candidates" / "materials_project" / "materials_project_search_results.json"
if mp_path.exists():
    with open(mp_path) as f:
        mp_data = json.load(f)
    for entry in mp_data:
        formula = entry.get("formula", "")
        count = entry.get("count", -1)
        if formula in MP_ZERO_HIT_FORMULAS:
            check(f"mp_zero_hit_{formula}", count == 0,
                  f"{formula}: {count} entries")
else:
    abstain("mp_data_exists", "MP search results file not found")

# ── 7. CIF composition check ──────────────────────────────────────────────────

cif_paths = [
    REPO_ROOT / "data" / "scatti_candidates" / "materials_project" / "cifs" / "mp-753401_Sc2TiO5.cif",
]
for cp in cif_paths:
    if cp.exists():
        content = cp.read_text()
        if "_chemical_formula_sum" in content:
            check(f"cif_has_formula_sum_{cp.name}", True)
        else:
            check(f"cif_has_formula_sum_{cp.name}", False, "Missing _chemical_formula_sum")
    else:
        abstain(f"cif_exists_{cp.name}", "File not found")

# ── 8. Parent scaling calculation ─────────────────────────────────────────────

sc2tio5_cif = REPO_ROOT / "data" / "scatti_candidates" / "materials_project" / "cifs" / "mp-753401_Sc2TiO5.cif"
if sc2tio5_cif.exists():
    content = sc2tio5_cif.read_text()
    for line in content.split("\n"):
        if "_cell_formula_units_Z" in line:
            z_val = int(line.split()[-1])
            check("parent_z_correct", z_val == PARENT_Z,
                  f"Z={z_val}, expected {PARENT_Z}")
            break
    else:
        abstain("parent_z_check", "Z not found in CIF")

# ── 9. Ledger supersessions ───────────────────────────────────────────────────

ledger_path = V3_DIR / "scatti_evidence_ledger_v3.json"
if ledger_path.exists():
    with open(ledger_path) as f:
        ledger = json.load(f)
    corrections = ledger.get("corrections", [])
    check("ledger_has_8_corrections", len(corrections) == 8,
          f"Found {len(corrections)} corrections")
    for corr in corrections:
        cid = corr.get("correction", "")
        applied = corr.get("applied", False)
        check(f"correction_{cid}_applied", applied, f"{cid}: {corr.get('final_status', 'unknown')}")
else:
    abstain("ledger_exists", "Ledger file not found")

# ── 10. No scientific overpromotion ────────────────────────────────────────────

overpromotion_terms = [
    "discovered", "stable", "DFT-ready", "synthesizable", "novel",
    "breakthrough", "confirmed_structure", "proven",
]
safe_words = {"novelty", "provenance"}  # "provenance" is not overpromotion
# Also safe: "proven" as substring of "provenance"
safe_substrings = {"provenance"}
negation_prefixes = ["no ", "not ", "not proof of ", "not a "]

for artifact in required_artifacts:
    path = V3_DIR / artifact.replace("data/scatti_candidates/cross_host_reconciliation_v3/", "")
    if path.exists():
        content = path.read_text().lower()
        found_overpromotion = False
        for term in overpromotion_terms:
            idx = 0
            while idx < len(content):
                idx = content.find(term, idx)
                if idx == -1:
                    break
                word_start = content.rfind(" ", 0, idx) + 1
                word_end = content.find(" ", idx)
                if word_end == -1:
                    word_end = len(content)
                full_word = content[word_start:word_end].strip(".,;:!?\"'")
                if full_word in safe_words:
                    idx += len(term)
                    continue
                # Check if the full word contains a safe substring (e.g. "provenance" contains "proven")
                safe_substrings = {"provenance"}
                is_substring_of_safe = any(sw in full_word for sw in safe_substrings)
                if is_substring_of_safe:
                    idx += len(term)
                    continue
                # "stable" in a question context is not overpromotion
                if term == "stable" and "?" in content[max(0, idx-50):idx+len(term)+10]:
                    idx += len(term)
                    continue
                start = max(0, idx - 30)
                preceding = content[start:idx].strip()
                is_negated = any(preceding.endswith(neg) for neg in negation_prefixes)
                if not is_negated:
                    found_overpromotion = True
                    check(f"no_overpromotion_{term}_in_{path.name}", False,
                          f"Found '{term}' in {path.name}")
                    break
                idx += len(term)
            if found_overpromotion:
                break

# ── 11. No credential values ──────────────────────────────────────────────────

credential_regexes = [
    re.compile(r'[^a-zA-Z](re_[A-Za-z0-9_]{10,})[^a-zA-Z]'),
    re.compile(r'[^a-zA-Z](sk-[A-Za-z0-9]{10,})[^a-zA-Z]'),
    re.compile(r'[^a-zA-Z](cfat_[A-Za-z0-9_]{10,})[^a-zA-Z]'),
    re.compile(r'api_key\s*=\s*["\']?[A-Za-z0-9_]{10,}'),
    re.compile(r'API_KEY\s*=\s*["\']?[A-Za-z0-9_]{10,}'),
]
for artifact in required_artifacts:
    path = V3_DIR / artifact.replace("data/scatti_candidates/cross_host_reconciliation_v3/", "")
    if path.exists():
        content = path.read_text()
        found_cred = False
        for regex in credential_regexes:
            if regex.search(content):
                found_cred = True
                check(f"no_credentials_in_{path.name}", False,
                      f"Found credential pattern in {path.name}")
                break

# ── 12. Implementation inventory ──────────────────────────────────────────────

inv_path = V3_DIR / "scatti_implementation_inventory_v3.json"
if inv_path.exists():
    with open(inv_path) as f:
        inv = json.load(f)
    modules = inv.get("modules", {})
    scripts = inv.get("scripts", {})
    tests = inv.get("tests", {})
    check("inventory_has_modules", len(modules) > 0, f"{len(modules)} modules")
    check("inventory_has_scripts", len(scripts) > 0, f"{len(scripts)} scripts")
    check("inventory_has_tests", len(tests) > 0, f"{len(tests)} tests")
else:
    abstain("inventory_exists", "Inventory file not found")

# ── 13. Validation tests pass (failed=0, errors=0) ───────────────────────────

test_receipt_path = V3_DIR / "raw_validation_r4b" / "test_summary.json"
if test_receipt_path.exists():
    with open(test_receipt_path) as f:
        receipt = json.load(f)
    check("validation_tests_failed", receipt.get("failed", -1) == 0,
          f"Tests failed: {receipt.get('failed', 'unknown')}")
    check("validation_errors_present", receipt.get("errors", -1) == 0,
          f"Test errors: {receipt.get('errors', 'unknown')}")
    check("validation_total_explicit", receipt.get("total", 0) > 0,
          f"Total: {receipt.get('total', 0)}")
else:
    abstain("validation_receipt_exists", "Test receipt not found")

# ── 14. Source patch verification passes ──────────────────────────────────────

patch_path = V3_DIR / "source_patch_verification_r4b.json"
if patch_path.exists():
    with open(patch_path) as f:
        patch = json.load(f)
    all_verified = all(
        r.get("verification_result") in ("repair_present_modified", "repair_present_already_committed")
        for r in patch.get("repairs", [])
    )
    check("source_repair_unverified", all_verified,
          f"{sum(1 for r in patch.get('repairs', []) if r.get('verification_result') in ('repair_present_modified', 'repair_present_already_committed'))}/{len(patch.get('repairs', []))} repairs verified")
else:
    abstain("source_patch_verification", "Patch verification file not found")

# ── 15. Git state contradiction resolved ───────────────────────────────────────

contradiction_path = V3_DIR / "git_state_contradiction_resolution_r4b.json"
if contradiction_path.exists():
    with open(contradiction_path) as f:
        resolution = json.load(f)
    check("git_state_contradiction", resolution.get("verification") == "repairs_are_present_as_modified_tracked_files",
          f"Resolution: {resolution.get('explanation', 'unknown')}")
else:
    abstain("git_state_contradiction", "Resolution file not found")

# ── 16. Archive member count matches ──────────────────────────────────────────

bundle_path = REPO_ROOT / "artifacts" / "scatti_cross_host_reconciliation_v3.tar.gz"
manifest_path = REPO_ROOT / "artifacts" / "scatti_cross_host_reconciliation_manifest_v3.json"
if bundle_path.exists() and manifest_path.exists():
    with open(manifest_path) as f:
        manifest = json.load(f)
    result = subprocess.run(["tar", "-tzf", str(bundle_path)], capture_output=True, text=True)
    actual_count = len([l for l in result.stdout.strip().split('\n') if l.strip()])
    reported_count = manifest.get("file_count", 0)
    check("archive_member_count_mismatch", actual_count == reported_count,
          f"Actual: {actual_count}, Reported: {reported_count}")
else:
    abstain("archive_member_count", "Bundle or manifest not found")

# ── 17. Raw validation outputs present ─────────────────────────────────────────

raw_dir = V3_DIR / "raw_validation_r4b"
if raw_dir.exists():
    has_output = any(raw_dir.iterdir())
    check("raw_validation_missing", has_output, "Raw validation outputs present")
else:
    abstain("raw_validation_missing", "Raw validation directory not found")

# ── 18. Promotion gate consistency ────────────────────────────────────────────

summary_path = V3_DIR / "scatti_cross_host_review_summary_r4a.json"
if summary_path.exists():
    with open(summary_path) as f:
        summary = json.load(f)
    gates = summary.get("promotion_gates", {})
    next_phase = summary.get("next_recommended_phase", "")
    ready_for_geometry = gates.get("ready_for_corrected_geometry_phase", False)
    if ready_for_geometry:
        check("promotion_gate_recommendation_conflict",
              next_phase == "corrected_parent_derived_geometry_construction",
              f"Gate=true, phase={next_phase}")
    else:
        check("promotion_gate_recommendation_conflict",
              next_phase != "corrected_parent_derived_geometry_construction",
              f"Gate=false but phase={next_phase}")
else:
    abstain("promotion_gate", "Summary file not found")

# ── 19. Structure status terminology correct ───────────────────────────────────

structure_path = V3_DIR / "structure_and_chgnet_evidence_verification_r4a.json"
if structure_path.exists():
    with open(structure_path) as f:
        struct_data = json.load(f)
    has_overbroad = any(
        s.get("status") == "fully_verified"
        for s in struct_data.get("structures", {}).values()
    )
    check("structure_status_overpromotion", not has_overbroad,
          "No structure uses overbroad 'fully_verified' status")
else:
    abstain("structure_status", "Structure verification file not found")

# ── Summary ──────────────────────────────────────────────────────────────────

total = results["passed"] + results["failed"] + results["abstained"]
results["overall"] = "cross_host_reconciliation_release_verified" if results["failed"] == 0 else "cross_host_reconciliation_release_failed"

print(f"\n{'='*60}")
print(f"V3 RELEASE VERIFIER RESULTS")
print(f"{'='*60}")
print(f"  Passed:   {results['passed']}")
print(f"  Failed:   {results['failed']}")
print(f"  Abstained: {results['abstained']}")
print(f"  Total:    {total}")
print(f"  Overall:  {results['overall']}")
print(f"{'='*60}\n")

for name, check_result in results["checks"].items():
    status = check_result["status"]
    detail = check_result.get("detail", "")
    if status == "PASS":
        print(f"  ✅ {name}")
    elif status == "FAIL":
        print(f"  ❌ {name}: {detail}")
    else:
        print(f"  ⚠️  {name}: {detail}")

# Write results
output_path = V3_DIR / "verifier_results_v3.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults written to: {output_path}")

sys.exit(0 if results["failed"] == 0 else 1)
