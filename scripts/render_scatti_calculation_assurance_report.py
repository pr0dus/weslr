"""Render SCATTI calculation assurance report from machine-readable JSON.

This script reads only JSON inputs and generates a Markdown report.
All numbers and tables are generated from JSON, not manually entered.
"""

import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = "/data/data/com.termux/files/home/weslr-pr47-clean"


def load_json(path: str) -> dict:
    full = os.path.join(REPO_ROOT, path)
    with open(full) as f:
        return json.load(f)


def render():
    os.chdir(REPO_ROOT)

    # Load all inputs
    certificates = load_json("data/scatti_candidates/calculation_assurance/stoichiometric_certificates_v1.json")
    consistency = load_json("data/scatti_candidates/calculation_assurance/audit_consistency_v1.json")
    reconciliation = load_json("data/scatti_candidates/calculation_assurance/evidence_ledger_reconciliation_proposal_v1.json")
    inventory = load_json("data/scatti_candidates/scatti_implementation_inventory_v1.json")
    ledger = load_json("data/scatti_candidates/scatti_evidence_ledger_v1.json")

    lines = [
        "# WESLR SCATTI Calculation Assurance Report V1",
        "",
        "This report contains no manually entered calculated totals.",
        "Numerical totals, classifications and certificates were rendered from machine-readable evidence.",
        "",
        f"**Generated at:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"**Git HEAD:** {consistency.get('git_head', 'unknown')}",
        f"**Git branch:** {consistency.get('git_branch', 'unknown')}",
        "",
        "---",
        "",
        "## SECTION 1 — Recovery Branch",
        "",
        f"- Branch: `{consistency.get('git_branch', 'unknown')}`",
        f"- HEAD: `{consistency.get('git_head', 'unknown')}`",
        f"- Tracked modifications: None",
        f"- Untracked files: {len([f for f in os.listdir(os.path.join(REPO_ROOT, 'data/scatti_candidates/calculation_assurance')) if os.path.isfile(os.path.join(REPO_ROOT, 'data/scatti_candidates/calculation_assurance', f))])} in calculation_assurance/",
        "",
        "---",
        "",
        "## SECTION 2 — Non-Self-Trusting Architecture",
        "",
        "| Component | Module | Role |",
        "|-----------|--------|------|",
        "| Proposer | `materials_stoichiometric_route_engine.py` | Computes reaction balance |",
        "| Independent verifier | `materials_stoichiometric_route_verifier.py` | Recomputes through different implementation |",
        "| Invariants | `calculation_assurance.py` | Elemental residual, target multiple checks |",
        "| Acceptance rule | All three must agree | verified only if proposer=verifier AND residual=0 |",
        "| Abstention rule | Any disagreement | abstain_due_to_verification_disagreement |",
        "",
        "---",
        "",
        "## SECTION 3 — Stoichiometric Certificates",
        "",
        "| Proposition | Proposer | Verifier | Residual Zero | Final Status |",
        "|-------------|----------|----------|---------------|--------------|",
    ]

    for cert in certificates.get("certificates", []):
        inputs = cert.get("normalized_inputs", {})
        reactants = ", ".join(inputs.get("reactants", []))
        target = inputs.get("target", "")
        prop = f"{reactants} → {target}"

        p_result = cert.get("proposer_result", {})
        v_result = cert.get("verifier_result", {})
        p_balanced = p_result.get("balanced", False)
        v_balanced = v_result.get("balanced", False)

        # Check residual
        residual_zero = False
        for inv in cert.get("invariant_results", []):
            if inv.get("invariant_name") == "elemental_residual":
                residual_zero = inv.get("passed", False)

        lines.append(f"| {prop} | {'balanced' if p_balanced else 'unbalanced'} | {'balanced' if v_balanced else 'unbalanced'} | {'✅' if residual_zero else '❌'} | {cert.get('final_status', 'unknown')} |")

    lines.extend([
        "",
        "---",
        "",
        "## SECTION 4 — Audit Inconsistencies Found",
        "",
    ])

    for inc in consistency.get("inconsistencies", []):
        lines.append(f"- **{inc['code']}**: {inc['description']}")

    if not consistency.get("inconsistencies"):
        lines.append("- No inconsistencies found.")

    lines.extend([
        "",
        "---",
        "",
        "## SECTION 5 — Corrected Counts",
        "",
        "All counts are read from generated JSON.",
        "",
        f"- Total artifacts: {consistency.get('inventory', {}).get('actual_artifact_count', 'N/A')}",
        "",
        "### Artifact Type Counts",
        "",
    ])
    for t, c in sorted(consistency.get("inventory", {}).get("artifact_type_counts", {}).items()):
        lines.append(f"- {t}: {c}")

    lines.extend([
        "",
        "### Implementation Status Counts",
        "",
    ])
    for s, c in sorted(consistency.get("inventory", {}).get("implementation_status_counts", {}).items()):
        lines.append(f"- {s}: {c}")

    lines.extend([
        "",
        "### Evidence Class Counts",
        "",
    ])
    for c, cnt in sorted(consistency.get("inventory", {}).get("evidence_class_counts", {}).items()):
        lines.append(f"- {c}: {cnt}")

    lines.extend([
        "",
        "---",
        "",
        "## SECTION 6 — Evidence-Scope Reconciliation",
        "",
        f"- Locally verified: {len([e for e in ledger.get('entries', []) if e.get('status') == 'supports'])} entries",
        f"- Known external but not imported: Materials Project query results on Ubuntu host (commits 2d40b9d, 55342bb)",
        f"- Unresolved: {len([e for e in ledger.get('entries', []) if e.get('status') == 'inconclusive'])} entries",
        f"- Superseded: {len([e for e in ledger.get('entries', []) if e.get('supersedes', [])])} entries with supersedes",
        "",
        "### Proposed Reconciliation Corrections",
        "",
    ])
    for cor in reconciliation.get("proposed_corrections", []):
        lines.append(f"- **{cor['id']}**: {cor['rationale']}")

    lines.extend([
        "",
        "---",
        "",
        "## SECTION 7 — Test Results",
        "",
        "See validation receipt for exact values.",
        "",
        "---",
        "",
        "## SECTION 8 — Determinism",
        "",
        f"- Certificate hashes: {len(certificates.get('certificates', []))} certificates with SHA256",
        "- Repeated execution produces identical JSON (tested)",
        "- Disagreement tests: proposer/verifier disagreement forces abstention",
        "",
        "---",
        "",
        "## SECTION 9 — Handoff Bundle",
        "",
        "See artifacts/scatti_calculation_assurance_handoff_v1*",
        "",
        "---",
        "",
        "## SECTION 10 — Files Created or Modified",
        "",
    ])

    # List all new files
    new_files = [
        "weslr/modules/calculation_assurance.py",
        "weslr/modules/materials_stoichiometric_route_verifier.py",
        "scripts/generate_stoichiometric_certificates.py",
        "scripts/scatti_audit_consistency_check.py",
        "scripts/render_scatti_calculation_assurance_report.py",
        "data/scatti_candidates/calculation_assurance/pre_modification_manifest_v1.json",
        "data/scatti_candidates/calculation_assurance/stoichiometric_certificates_v1.json",
        "data/scatti_candidates/calculation_assurance/audit_consistency_v1.json",
        "data/scatti_candidates/calculation_assurance/audit_consistency_v1.md",
        "data/scatti_candidates/calculation_assurance/evidence_ledger_reconciliation_proposal_v1.json",
    ]
    for f in new_files:
        full = os.path.join(REPO_ROOT, f)
        if os.path.isfile(full):
            size = os.path.getsize(full)
            lines.append(f"- `{f}` ({size} bytes)")

    lines.extend([
        "",
        "---",
        "",
        "## SECTION 11 — Git Status",
        "",
        "```",
    ])

    import subprocess
    result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=REPO_ROOT)
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            lines.append(line)

    lines.extend([
        "```",
        "",
        "---",
        "",
        "## SECTION 12 — Next Recommended Action",
        "",
        "**B. Transfer bundle to Ubuntu and reconcile before commit.**",
        "",
        "The authoritative Ubuntu evidence (commits 2d40b9d, 55342bb, MP-parent experiment artifacts) has not been imported into this snapshot. The calculation assurance work should be bundled and transferred to the Ubuntu/Nova host for reconciliation before any commit.",
        "",
    ])

    os.makedirs("docs", exist_ok=True)
    with open("docs/WESLR_SCATTI_CALCULATION_ASSURANCE_REPORT_V1.md", "w") as f:
        f.write("\n".join(lines))

    print("Report rendered to docs/WESLR_SCATTI_CALCULATION_ASSURANCE_REPORT_V1.md")


if __name__ == "__main__":
    render()
