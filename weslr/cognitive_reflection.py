from __future__ import annotations
from typing import Dict, Any, List


def run_reflection(proposal: Dict[str, Any], evidence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Bounded reflection/consistency pass.

    - Proposal-only metadata enrichment.
    - No routing or execution changes.
    - Returns notes/flags to attach to an adequacy proposal payload.
    """
    notes: List[str] = []
    if proposal.get("actionable") is False:
        notes.append("missing_actionable_step")
    if evidence:
        if evidence.get("coverage_gap"):
            notes.append("coverage_gap_flag")
        if evidence.get("originating_evidence_signal") and not proposal.get("evidence"):
            notes.append("evidence_not_carried")
    return {
        "reflection_added": True,
        "consistency_notes": notes,
    }
