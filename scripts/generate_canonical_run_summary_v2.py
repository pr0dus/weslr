"""Generate the canonical calculation assurance run summary V2.

This is the single source of truth for the V2 Markdown report.
All values are read from generated JSON, not manually entered.
"""
import hashlib, json, os, subprocess, sys
from collections import Counter
from datetime import datetime, timezone

REPO_ROOT = os.environ.get("WESLR_REPO_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(REPO_ROOT)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# Load all V2 inputs
scope_counts = load_json("data/scatti_candidates/calculation_assurance_v2/preflight_scope_counts_v2.json")
inventory = load_json("data/scatti_candidates/calculation_assurance_v2/scatti_implementation_inventory_v2.json")
certificates = load_json("data/scatti_candidates/calculation_assurance_v2/stoichiometric_certificates_v2.json")

# Load V1 inputs for reference
v1_inventory = load_json("data/scatti_candidates/scatti_implementation_inventory_v1.json")
v1_ledger = load_json("data/scatti_candidates/scatti_evidence_ledger_v1.json")

# Get git state
branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

# --- Artifact inventory counts ---
records = inventory.get("records", [])
total_records = len(records)
type_counts = Counter(r["artifact_type"] for r in records)
impl_counts = Counter(r["implementation_status"] for r in records)
exec_counts = Counter(r["execution_status"] for r in records)
evidence_counts = Counter(r["evidence_class"] for r in records)
repro_counts = Counter(r["reproducibility_status"] for r in records)
tracked_count = sum(1 for r in records if r["tracked"])
untracked_count = sum(1 for r in records if not r["tracked"])
existing_count = sum(1 for r in records if r["exists"])
missing_count = sum(1 for r in records if not r["exists"])

# --- Certificate counts ---
reaction_certs = certificates.get("reaction_certificates", [])
target_certs = certificates.get("target_multiple_certificates", [])
verified_reactions = sum(1 for c in reaction_certs if c["final_status"] == "verified")
rejected_reactions = sum(1 for c in reaction_certs if c["final_status"] != "verified")
verified_targets = sum(1 for c in target_certs if c["final_status"] == "verified")
rejected_targets = sum(1 for c in target_certs if c["final_status"] != "verified")

# --- Evidence scope counts ---
entries = v1_ledger.get("entries", [])
supports = sum(1 for e in entries if e.get("status") == "supports")
weakens = sum(1 for e in entries if e.get("status") == "weakens")
contradicts = sum(1 for e in entries if e.get("status") == "contradicts")
inconclusive = sum(1 for e in entries if e.get("status") == "inconclusive")
executed_negative = sum(1 for e in entries if e.get("status") == "executed_negative")
executed_inconclusive = sum(1 for e in entries if e.get("status") == "executed_inconclusive")
not_started = sum(1 for e in entries if e.get("status") == "not_started")
partial = sum(1 for e in entries if e.get("status") == "partial")
supersedes_count = sum(1 for e in entries if e.get("supersedes", []))
contradictions = v1_ledger.get("contradictions", [])
resolved_contradictions = sum(1 for c in contradictions if c.get("resolved", False))
open_questions = len(v1_ledger.get("open_questions", []))

# --- Inconsistency counts ---
# From the consistency checker
consistency = load_json("data/scatti_candidates/calculation_assurance/audit_consistency_v1.json")
inconsistencies = consistency.get("inconsistencies", [])
inconsistency_codes = Counter(inc["code"] for inc in inconsistencies)

# --- Test results ---
# Read from validation receipt
validation = load_json("data/scatti_candidates/calculation_assurance/validation_receipt_v1.json")
test_commands = [c for c in validation.get("commands", []) if "pytest" in c["command"]]
test_passed = sum(1 for c in test_commands if c["result"] == "PASS")
test_failed = sum(1 for c in test_commands if c["result"] == "FAIL")

# --- Bundle info ---
bundle_path = "artifacts/scatti_calculation_assurance_handoff_v1.tar.gz"
bundle_exists = os.path.isfile(bundle_path)
bundle_sha256 = sha256_file(bundle_path) if bundle_exists else ""
bundle_size = os.path.getsize(bundle_path) if bundle_exists else 0

# --- Source hashes ---
source_hashes = {
    "preflight_scope_counts_v2.json": sha256_file("data/scatti_candidates/calculation_assurance_v2/preflight_scope_counts_v2.json"),
    "scatti_implementation_inventory_v2.json": sha256_file("data/scatti_candidates/calculation_assurance_v2/scatti_implementation_inventory_v2.json"),
    "stoichiometric_certificates_v2.json": sha256_file("data/scatti_candidates/calculation_assurance_v2/stoichiometric_certificates_v2.json"),
    "scatti_artifact_inventory_schema_v2.json": sha256_file("data/scatti_candidates/calculation_assurance_v2/scatti_artifact_inventory_schema_v2.json"),
}

summary = {
    "schema_version": 2,
    "generator_version": "generate_canonical_run_summary_v2.py",
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "git_head": head,
    "branch": branch,
    "source_hashes": source_hashes,
    "scope_counts": {
        "repository_untracked_total": scope_counts["scopes"][0]["file_count"],
        "scatti_untracked_total": scope_counts["scopes"][1]["file_count"],
        "calculation_assurance_untracked_total": scope_counts["scopes"][2]["file_count"],
    },
    "artifact_inventory_counts": {
        "total_records": total_records,
        "by_artifact_type": dict(type_counts),
        "by_implementation_status": dict(impl_counts),
        "by_execution_status": dict(exec_counts),
        "by_evidence_class": dict(evidence_counts),
        "by_reproducibility_status": dict(repro_counts),
        "tracked_count": tracked_count,
        "untracked_count": untracked_count,
        "existing_count": existing_count,
        "missing_count": missing_count,
        "all_category_sums_pass": inventory.get("all_sums_pass", False),
    },
    "stoichiometric_certificate_counts": {
        "total_reaction_certificates": len(reaction_certs),
        "verified_reactions": verified_reactions,
        "rejected_reactions": rejected_reactions,
        "total_target_multiple_certificates": len(target_certs),
        "verified_target_multiples": verified_targets,
        "rejected_target_multiples": rejected_targets,
    },
    "verification_status_counts": {
        "verified": verified_reactions + verified_targets,
        "rejected_by_invariant": rejected_reactions + rejected_targets,
    },
    "inconsistency_counts": {
        "total_inconsistencies_found": len(inconsistencies),
        "by_code": dict(inconsistency_codes),
    },
    "evidence_scope_counts": {
        "total_entries": len(entries),
        "supports": supports,
        "weakens": weakens,
        "contradicts": contradicts,
        "inconclusive": inconclusive,
        "executed_negative": executed_negative,
        "executed_inconclusive": executed_inconclusive,
        "not_started": not_started,
        "partial": partial,
        "entries_with_supersedes": supersedes_count,
        "contradictions_total": len(contradictions),
        "resolved_contradictions": resolved_contradictions,
        "open_questions": open_questions,
    },
    "test_results": {
        "pytest_commands": len(test_commands),
        "passed": test_passed,
        "failed": test_failed,
    },
    "bundle_results": {
        "v1_bundle_exists": bundle_exists,
        "v1_bundle_sha256": bundle_sha256,
        "v1_bundle_size_bytes": bundle_size,
    },
    "unresolved_issues": [
        "Commits 2d40b9d and 55342bb not reachable in this snapshot",
        "Materials Project evidence on Ubuntu host not imported",
        "V1 inventory summary counts disagree with artifact-level counts (category_sum_mismatch)",
        "V1 inventory reports 0 superseded but evidence ledger has 2 entries with supersedes",
    ],
}

with open("data/scatti_candidates/calculation_assurance_v2/calculation_assurance_run_summary_v2.json", "w") as f:
    json.dump(summary, f, indent=2, sort_keys=True)

print("Canonical run summary V2 generated:")
for k, v in summary["scope_counts"].items():
    print(f"  {k}: {v}")
print(f"  total_records: {summary['artifact_inventory_counts']['total_records']}")
print(f"  verified_reactions: {summary['stoichiometric_certificate_counts']['verified_reactions']}")
print(f"  inconsistencies: {summary['inconsistency_counts']['total_inconsistencies_found']}")
