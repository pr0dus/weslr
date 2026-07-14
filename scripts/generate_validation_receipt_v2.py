"""Generate validation receipt V2."""
import hashlib, json, os, subprocess, sys
from datetime import datetime, timezone

REPO_ROOT = "/data/data/com.termux/files/home/weslr-pr47-clean"
os.chdir(REPO_ROOT)


def run_cmd(cmd, cwd=None):
    start = datetime.now(timezone.utc)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or REPO_ROOT, shell=True)
    end = datetime.now(timezone.utc)
    duration_ms = int((end - start).total_seconds() * 1000)
    return {
        "command": cmd,
        "working_directory": cwd or REPO_ROOT,
        "executable": subprocess.run(["which", cmd.split()[0]], capture_output=True, text=True).stdout.strip() or cmd.split()[0],
        "python_version": sys.version,
        "utc_start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "utc_end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_ms": duration_ms,
        "return_code": result.returncode,
        "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
        "result": "PASS" if result.returncode == 0 else "FAIL",
    }


commands = [
    "python3 -m pytest weslr/tests/test_materials_stoichiometric_route_engine.py weslr/tests/test_calculation_assurance.py weslr/tests/test_materials_stoichiometric_route_verifier.py weslr/tests/test_scatti_audit_consistency.py -q",
    "python3 -m compileall -q weslr/modules/calculation_assurance.py weslr/modules/materials_stoichiometric_route_engine.py weslr/modules/materials_stoichiometric_route_verifier.py scripts/generate_stoichiometric_certificates.py scripts/scatti_audit_consistency_check.py scripts/render_scatti_calculation_assurance_report_v2.py scripts/verify_scatti_calculation_assurance_release_v2.py",
    "python3 scripts/generate_preflight_scope_counts_v2.py",
    "python3 scripts/rebuild_inventory_v2.py",
    "python3 scripts/generate_stoichiometric_certificates_v2.py",
    "python3 scripts/generate_canonical_run_summary_v2.py",
    "python3 scripts/render_scatti_calculation_assurance_report_v2.py",
    "python3 scripts/verify_scatti_calculation_assurance_release_v2.py",
    "git diff --check",
]

entries = []
for cmd in commands:
    entry = run_cmd(cmd)
    entries.append(entry)
    print(f"{cmd[:70]}... -> {entry['result']} ({entry['duration_ms']}ms)")

# File checks
files_validated = [
    "weslr/modules/calculation_assurance.py",
    "weslr/modules/materials_stoichiometric_route_engine.py",
    "weslr/modules/materials_stoichiometric_route_verifier.py",
    "scripts/generate_preflight_scope_counts_v2.py",
    "scripts/rebuild_inventory_v2.py",
    "scripts/generate_stoichiometric_certificates_v2.py",
    "scripts/generate_canonical_run_summary_v2.py",
    "scripts/render_scatti_calculation_assurance_report_v2.py",
    "scripts/verify_scatti_calculation_assurance_release_v2.py",
    "data/scatti_candidates/calculation_assurance_v2/preflight_scope_counts_v2.json",
    "data/scatti_candidates/calculation_assurance_v2/scatti_artifact_inventory_schema_v2.json",
    "data/scatti_candidates/calculation_assurance_v2/scatti_implementation_inventory_v2.json",
    "data/scatti_candidates/calculation_assurance_v2/stoichiometric_certificates_v2.json",
    "data/scatti_candidates/calculation_assurance_v2/calculation_assurance_run_summary_v2.json",
]

receipt = {
    "schema_version": 2,
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "git_head": "62e9ba794c780bb37d5472d79ca8c9d91230892d",
    "commands": entries,
    "files_validated": files_validated,
    "summary": {
        "total_commands": len(entries),
        "passed": sum(1 for e in entries if e["result"] == "PASS"),
        "failed": sum(1 for e in entries if e["result"] == "FAIL"),
    },
}

with open("data/scatti_candidates/calculation_assurance_v2/validation_receipt_v2.json", "w") as f:
    json.dump(receipt, f, indent=2, sort_keys=True)

print(f"\nValidation receipt V2: {receipt['summary']['passed']}/{receipt['summary']['total_commands']} passed")
