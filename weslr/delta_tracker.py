from typing import Any, Dict, List, Tuple

Delta = Dict[str, Any]


def _item_key(item: Dict[str, Any]) -> Tuple[str, str]:
    title = str(item.get("title", "")).strip().lower()
    reason = str(item.get("reason", "")).strip().lower()
    return (title, reason)


def _index_items(items: List[Dict[str, Any]]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    index: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for it in items or []:
        index[_item_key(it)] = it
    return index


def _list_delta(prev: List[Dict[str, Any]], curr: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    prev_idx = _index_items(prev)
    curr_idx = _index_items(curr)

    added = [curr_idx[k] for k in curr_idx.keys() - prev_idx.keys()]
    removed = [prev_idx[k] for k in prev_idx.keys() - curr_idx.keys()]
    return {"added": added, "removed": removed}


def diff_decisions(prev: Dict[str, Any], curr: Dict[str, Any]) -> Delta:
    """Compute a minimal delta between two decision snapshots.

    No governance or signal changes; purely structural diff for operator continuity.
    """
    delta: Delta = {
        "added": {},
        "removed": {},
        "unblocked": [],
        "newly_blocked": [],
        "approvals_granted": [],
        "approvals_added": [],
        "confidence_change": None,
        "evidence_gaps_change": {},
        "next_actions_change": {},
    }

    sections = ["what_matters_now", "blocked_items", "approval_queue", "next_actions"]
    for sec in sections:
        sec_delta = _list_delta(prev.get(sec, []), curr.get(sec, []))
        delta["added"][sec] = sec_delta["added"]
        delta["removed"][sec] = sec_delta["removed"]

    # Unblocked / newly blocked
    prev_blocked_keys = set(_index_items(prev.get("blocked_items", [])).keys())
    curr_blocked_keys = set(_index_items(curr.get("blocked_items", [])).keys())
    delta["unblocked"] = list(prev_blocked_keys - curr_blocked_keys)
    delta["newly_blocked"] = list(curr_blocked_keys - prev_blocked_keys)

    # Approvals
    prev_appr_keys = set(_index_items(prev.get("approval_queue", [])).keys())
    curr_appr_keys = set(_index_items(curr.get("approval_queue", [])).keys())
    delta["approvals_granted"] = list(prev_appr_keys - curr_appr_keys)
    delta["approvals_added"] = list(curr_appr_keys - prev_appr_keys)

    # Confidence change
    if prev.get("confidence") is not None or curr.get("confidence") is not None:
        delta["confidence_change"] = {
            "prev": prev.get("confidence"),
            "curr": curr.get("confidence"),
            "delta": None,
        }
        if prev.get("confidence") is not None and curr.get("confidence") is not None:
            delta["confidence_change"]["delta"] = curr.get("confidence") - prev.get("confidence")

    # Evidence gaps
    prev_gaps = set(str(g).strip().lower() for g in prev.get("evidence_gaps", []) if g)
    curr_gaps = set(str(g).strip().lower() for g in curr.get("evidence_gaps", []) if g)
    delta["evidence_gaps_change"] = {
        "added": list(curr_gaps - prev_gaps),
        "removed": list(prev_gaps - curr_gaps),
    }

    # Next actions specific delta
    na_delta = _list_delta(prev.get("next_actions", []), curr.get("next_actions", []))
    delta["next_actions_change"] = {
        "added": na_delta["added"],
        "removed": na_delta["removed"],
    }

    return delta


def delta_is_empty(delta: Delta) -> bool:
    if not delta:
        return True
    checks = [
        any(delta.get("added", {}).values()),
        any(delta.get("removed", {}).values()),
        delta.get("unblocked"),
        delta.get("newly_blocked"),
        delta.get("approvals_granted"),
        delta.get("approvals_added"),
        delta.get("evidence_gaps_change", {}).get("added") or delta.get("evidence_gaps_change", {}).get("removed"),
    ]
    if delta.get("confidence_change"):
        if delta["confidence_change"].get("delta") not in (None, 0):
            checks.append(True)
    return not any(checks)
