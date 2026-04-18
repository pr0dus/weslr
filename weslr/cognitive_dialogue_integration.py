from __future__ import annotations
from typing import Dict, Any, Optional

from .cognitive_dialogue import explain_inadequacy, propose_improvement, handle_operator_response


def build_cdi_bundle(adequacy_finding: Optional[Dict[str, Any]], operator_action: Optional[str] = None, refinement: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Canonical improvement lane (operator-triggered): adequacy → CDI proposal → operator decision.

    - Requires an adequacy finding (proposal-only). Returns None if absent.
    - Attaches lineage/evidence when provided; proposals without lineage/evidence are not canonical core governance.
    - No activation, no routing changes, no autonomous approval.
    """
    if not adequacy_finding:
        return None

    resp_text = adequacy_finding.get("response_text") or "(no response text)"
    findings = adequacy_finding.get("findings", [])
    evidence = adequacy_finding.get("evidence", [])
    lineage_ref = adequacy_finding.get("lineage_ref")

    explanation = explain_inadequacy(resp_text, findings, evidence=evidence, lineage_ref=lineage_ref)
    improvement = propose_improvement(findings, adequacy_finding.get("improvement" ,"Propose a more specific response"), lineage_ref=lineage_ref)

    operator_outcome = None
    if operator_action:
        operator_outcome = handle_operator_response(improvement, operator_action, refinement=refinement)

    return {
        "explanation": explanation,
        "proposal": improvement,
        "operator_outcome": operator_outcome,
        "lineage_ref": lineage_ref,
        "evidence": evidence,
    }
