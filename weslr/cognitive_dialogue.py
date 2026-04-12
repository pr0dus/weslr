from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class DialogueState:
    persona: str
    domain: str
    exchanges: List[Dict[str, Any]] = field(default_factory=list)
    approval_gate_required: bool = True
    lineage_refs: List[Dict[str, Any]] = field(default_factory=list)


def explain_inadequacy(response_text: str, findings: List[str], lineage_ref: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "type": "inadequacy_explanation",
        "response": response_text,
        "findings": findings,
        "lineage_ref": lineage_ref,
    }


def propose_improvement(findings: List[str], proposal_text: str, lineage_ref: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "type": "improvement_proposal",
        "findings": findings,
        "proposal": proposal_text,
        "lineage_ref": lineage_ref,
        "requires_approval": True,
    }


def handle_operator_response(proposal: Dict[str, Any], operator_action: str, refinement: Optional[str] = None) -> Dict[str, Any]:
    operator_action = operator_action.lower()
    if operator_action not in {"approve", "deny", "refine"}:
        raise ValueError("invalid operator action")
    result = {
        "proposal": proposal,
        "operator_action": operator_action,
        "approved": operator_action == "approve",
        "refined": operator_action == "refine",
        "refinement": refinement if operator_action == "refine" else None,
        "requires_activation": False,  # no autonomous activation
    }
    return result


def attach_lineage(state: DialogueState, ref: Dict[str, Any]):
    state.lineage_refs.append(ref)


def record_exchange(state: DialogueState, user_msg: str, system_reply: Dict[str, Any]):
    state.exchanges.append({"user": user_msg, "system": system_reply})
