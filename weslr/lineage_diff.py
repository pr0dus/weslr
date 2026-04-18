from __future__ import annotations
from typing import Dict, Any, List, Tuple


def diff_lineage(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Compute a diff between two lineage records (dict form). Read-only.

    Expected fields: proposal_id, confidence, current_status, linked_checkpoint,
    status_history (list of dict), audit_log (list of dict), adequacy (optional).
    """
    summary = {
        "proposal_id": a.get("proposal_id") or a.get("origin", {}).get("proposal_id"),
        "same_workspace": _same(a, b, "workspace_id"),
        "same_user": _same(a, b, "user_id"),
    }

    field_diffs = {}
    field_diffs["confidence"] = _scalar_change(a, b, "confidence")
    field_diffs["current_status"] = _scalar_change(a, b, "current_status")
    field_diffs["linked_checkpoint"] = _scalar_change(a, b, "linked_checkpoint")
    if a.get("adequacy") or b.get("adequacy"):
        field_diffs["adequacy"] = _scalar_change(a, b, "adequacy")

    status_history_diff = _list_diff(a.get("status_history", []), b.get("status_history", []))
    audit_diff = _list_diff(a.get("audit_log", []), b.get("audit_log", []))

    flags = []
    conf_change = field_diffs["confidence"]
    if conf_change and conf_change.get("delta") is not None and conf_change.get("delta") < 0:
        flags.append("confidence_regression")
    status_change = field_diffs["current_status"]
    if status_change and status_change.get("from") != status_change.get("to"):
        flags.append("status_change")
    chk_change = field_diffs["linked_checkpoint"]
    if chk_change and chk_change.get("from") != chk_change.get("to"):
        flags.append("checkpoint_change")

    return {
        "summary": summary,
        "field_diffs": field_diffs,
        "status_history_diff": status_history_diff,
        "audit_diff": audit_diff,
        "flags": flags,
    }


def _same(a: Dict[str, Any], b: Dict[str, Any], field: str) -> bool | None:
    va = a.get(field) or a.get("origin", {}).get(field)
    vb = b.get(field) or b.get("origin", {}).get(field)
    if va is None or vb is None:
        return None
    return va == vb


def _scalar_change(a: Dict[str, Any], b: Dict[str, Any], field: str) -> Dict[str, Any] | None:
    va = a.get(field) or a.get("origin", {}).get(field)
    vb = b.get(field) or b.get("origin", {}).get(field)
    if va is None and vb is None:
        return None
    delta = None
    try:
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            delta = vb - va
    except Exception:
        delta = None
    return {"from": va, "to": vb, "delta": delta}


def _list_diff(a_list: List[Dict[str, Any]], b_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    a_set = {(str(item), idx) for idx, item in enumerate(a_list)}
    b_set = {(str(item), idx) for idx, item in enumerate(b_list)}
    added = [b_list[idx] for (s, idx) in b_set if (s, idx) not in a_set]
    removed = [a_list[idx] for (s, idx) in a_set if (s, idx) not in b_set]
    return {"added": added, "removed": removed}
