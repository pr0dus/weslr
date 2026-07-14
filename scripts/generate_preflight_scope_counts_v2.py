"""Generate preflight scope counts V2."""
import hashlib, json, os, subprocess, sys

REPO_ROOT = os.environ.get("WESLR_REPO_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(REPO_ROOT)

# Get git status
result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
untracked_paths = []
for line in result.stdout.strip().split("\n"):
    line = line.strip()
    if line.startswith("??"):
        path = line[2:].strip()
        untracked_paths.append(path)

# Scope 1: repository_untracked_total
repo_untracked = sorted(untracked_paths)

# Scope 2: scatti_untracked_total - SCATTI/calculation-assurance paths
scatti_keywords = ["scatti", "calculation_assurance", "stoichiometric", "materials_stoichiometric"]
scatti_untracked = sorted([p for p in repo_untracked if any(k in p.lower() for k in scatti_keywords)])

# Scope 3: calculation_assurance_untracked_total - explicit allowlist
ca_allowlist = [
    "data/scatti_candidates/calculation_assurance/",
    "data/scatti_candidates/calculation_assurance_v2/",
    "docs/WESLR_SCATTI_CALCULATION_ASSURANCE_REPORT_V1.md",
    "docs/WESLR_SCATTI_IMPLEMENTATION_AND_EVIDENCE_AUDIT_V1.md",
    "scripts/generate_stoichiometric_certificates.py",
    "scripts/render_scatti_calculation_assurance_report.py",
    "scripts/scatti_audit_consistency_check.py",
    "weslr/modules/calculation_assurance.py",
    "weslr/modules/materials_stoichiometric_route_engine.py",
    "weslr/modules/materials_stoichiometric_route_verifier.py",
    "weslr/tests/test_calculation_assurance.py",
    "weslr/tests/test_materials_stoichiometric_route_engine.py",
    "weslr/tests/test_materials_stoichiometric_route_verifier.py",
    "weslr/tests/test_scatti_audit_consistency.py",
    "data/scatti_candidates/scatti_evidence_ledger_v1.json",
    "data/scatti_candidates/scatti_implementation_inventory_v1.json",
    "data/scatti_candidates/scatti_parent_route_stoichiometry_repair_v1.json",
    "data/scatti_candidates/scatti_parent_route_stoichiometry_repair_v1.md",
    "artifacts/",
]

def is_in_allowlist(path, allowlist):
    for a in allowlist:
        if a.endswith("/"):
            if path.startswith(a) or path == a.rstrip("/"):
                return True
        elif path == a:
            return True
    return False

ca_untracked = sorted([p for p in repo_untracked if is_in_allowlist(p, ca_allowlist)])

def file_info(path):
    full = os.path.join(REPO_ROOT, path)
    if not os.path.isfile(full):
        return {"size_bytes": 0, "sha256": ""}
    size = os.path.getsize(full)
    with open(full, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    return {"size_bytes": size, "sha256": sha}

scopes = [
    {
        "scope_name": "repository_untracked_total",
        "inclusion_rules": "All paths with git status '??'",
        "exclusion_rules": "None",
        "file_count": len(repo_untracked),
        "paths": repo_untracked,
        "total_size_bytes": sum(file_info(p)["size_bytes"] for p in repo_untracked if os.path.isfile(os.path.join(REPO_ROOT, p))),
        "per_file_sha256": {p: file_info(p)["sha256"] for p in repo_untracked if os.path.isfile(os.path.join(REPO_ROOT, p))},
    },
    {
        "scope_name": "scatti_untracked_total",
        "inclusion_rules": "Untracked paths containing 'scatti', 'calculation_assurance', 'stoichiometric', or 'materials_stoichiometric'",
        "exclusion_rules": "Unrelated untracked files (ARC, experiment results, etc.)",
        "file_count": len(scatti_untracked),
        "paths": scatti_untracked,
        "total_size_bytes": sum(file_info(p)["size_bytes"] for p in scatti_untracked if os.path.isfile(os.path.join(REPO_ROOT, p))),
        "per_file_sha256": {p: file_info(p)["sha256"] for p in scatti_untracked if os.path.isfile(os.path.join(REPO_ROOT, p))},
    },
    {
        "scope_name": "calculation_assurance_untracked_total",
        "inclusion_rules": "Explicit allowlist of calculation-assurance implementation and output files",
        "exclusion_rules": "Unrelated untracked files, ARC files, experiment results, run_five_task_pilot.py, test_arc_agi2_*",
        "file_count": len(ca_untracked),
        "paths": ca_untracked,
        "total_size_bytes": sum(file_info(p)["size_bytes"] for p in ca_untracked if os.path.isfile(os.path.join(REPO_ROOT, p))),
        "per_file_sha256": {p: file_info(p)["sha256"] for p in ca_untracked if os.path.isfile(os.path.join(REPO_ROOT, p))},
    },
]

output = {
    "schema_version": 2,
    "generated_at": "2026-07-14T16:00:00Z",
    "git_head": "62e9ba794c780bb37d5472d79ca8c9d91230892d",
    "branch": "scatti-calculation-assurance-recovery-20260714",
    "scopes": scopes,
}

with open("data/scatti_candidates/calculation_assurance_v2/preflight_scope_counts_v2.json", "w") as f:
    json.dump(output, f, indent=2, sort_keys=True)

print(f"Scope counts generated:")
for s in scopes:
    print(f"  {s['scope_name']}: {s['file_count']} files, {s['total_size_bytes']} bytes")
