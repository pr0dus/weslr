from __future__ import annotations
from typing import Dict, Any
from .cognitive_adequacy import evaluate
from .cognitive_reflection import run_reflection


def run_post_proposal_adequacy(proposal: Dict[str, Any], *, evidence: Dict[str, Any] | None = None, reflection_enabled: bool = False) -> Dict[str, Any]:
    """Guarded post-proposal adequacy hook.

    - Inputs: proposal record (id, conf, optional family/fix/action/evidence/actionable), optional evidence bundle.
    - Behavior: calls adequacy evaluator and returns a proposal-only adequacy finding.
    - Optional bounded reflection pass (proposal-only) when enabled.
    - No mutation of proposal or routing/execution path.
    """
    proposals = []
    operator_requested = False
    exploratory_window = False

    if evidence:
        operator_requested = evidence.get("operator_requested_repetition", False)
        exploratory_window = evidence.get("exploratory_window", False)
        if evidence.get("similar_proposals"):
            proposals.extend(evidence.get("similar_proposals"))

    proposals.append(
        {
            "id": proposal.get("proposal_id") or proposal.get("id"),
            "conf": proposal.get("confidence", proposal.get("conf", 0.0)),
            "family": proposal.get("family"),
            "action": proposal.get("action"),
            "fix": proposal.get("fix"),
            "evidence": proposal.get("evidence"),
            "actionable": proposal.get("actionable"),
        }
    )

    if evidence:
        proposals[-1].update({
            "source_loop_id": evidence.get("source_loop_id"),
            "workspace_id": evidence.get("workspace_id"),
            "user_id": evidence.get("user_id"),
            "trigger_reason": evidence.get("trigger_reason"),
            "originating_evidence_signal": evidence.get("originating_evidence_signal"),
        })

    result = evaluate(
        proposals,
        operator_requested_repetition=operator_requested,
        exploratory_window=exploratory_window,
    )

    if reflection_enabled and result.get("inadequate"):
        result["reflection"] = run_reflection(proposal, evidence)

    return result
