from __future__ import annotations
from typing import Dict, Any
from .cognitive_adequacy import evaluate


def run_post_proposal_adequacy(proposal: Dict[str, Any], *, evidence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Guarded post-proposal adequacy hook.

    - Inputs: proposal record (id, conf, optional family/fix/action/evidence/actionable), optional evidence bundle.
    - Behavior: calls adequacy evaluator and returns a proposal-only adequacy finding.
    - No mutation of proposal or routing/execution path.
    - Proposal emission is governed; caller is responsible for recording/surfacing.
    """
    proposals = []
    # Optionally include prior similar proposals for basic context if passed in evidence
    if evidence and evidence.get("similar_proposals"):
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
    return evaluate(proposals)
