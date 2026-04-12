from __future__ import annotations
from typing import List, Dict, Any

# Thresholds aligned with doctrine/harness
THRESHOLDS = {
    "repetition_count": 3,
    "reject_ignore_ratio": 0.60,
    "reject_ignore_window": 5,
    "low_conf_threshold": 0.4,
    "low_conf_streak": 3,
    "same_fix_count": 3,
    "no_improve_windows": 2,
    "no_improve_window_size": 4,
    "e2a_fail_count": 2,
    "e2a_window_size": 4,
    "min_sample": 3,
    "explore_improve_step": 0.05,
}


def evaluate(proposals: List[Dict[str, Any]], *, operator_requested_repetition: bool = False, exploratory_window: bool = False) -> Dict[str, Any]:
    """Proposal-only adequacy evaluator.

    Inputs: proposals with keys id, conf, optional: family, action, fix, evidence, actionable.
    Returns: dict with adequacy assessment and proposal-only output.
    """
    # Guards
    if operator_requested_repetition:
        return _result(False, "operator_requested", [])
    if len(proposals) < THRESHOLDS["min_sample"]:
        return _result(False, "low_sample", [])
    if exploratory_window:
        confs = [p.get("conf", 0.0) for p in proposals]
        improving = all((confs[i+1] - confs[i]) >= THRESHOLDS["explore_improve_step"] for i in range(len(confs)-1))
        if improving:
            return _result(False, "exploratory_improving", [])

    # Repetition/shallow
    families = [p.get("family") for p in proposals if p.get("family")]
    if families:
        top = max(set(families), key=families.count)
        if families.count(top) >= THRESHOLDS["repetition_count"]:
            return _result(True, "repetition_shallow", [p["id"] for p in proposals])

    # Reject/ignore ratio
    actions = [p.get("action") for p in proposals]
    rej_ign = sum(1 for a in actions if a in {"rejected", "ignored"})
    if len(proposals) >= THRESHOLDS["reject_ignore_window"]:
        ratio = rej_ign / len(proposals)
        if ratio >= THRESHOLDS["reject_ignore_ratio"]:
            return _result(True, "low_usefulness", [p["id"] for p in proposals])

    # Low confidence streak
    confs = [p.get("conf", 0.0) for p in proposals]
    streak = 0
    for i, c in enumerate(confs):
        if c < THRESHOLDS["low_conf_threshold"]:
            streak += 1
            if streak >= THRESHOLDS["low_conf_streak"]:
                return _result(True, "low_confidence_streak", [p["id"] for p in proposals[i-THRESHOLDS["low_conf_streak"]+1:i+1]])
        else:
            streak = 0

    # Same fix loops
    fixes = [p.get("fix") for p in proposals if p.get("fix")]
    if fixes:
        top_fix = max(set(fixes), key=fixes.count)
        if fixes.count(top_fix) >= THRESHOLDS["same_fix_count"]:
            return _result(True, "same_fix_loop", [p["id"] for p in proposals])

    # No improvement across windows
    window = THRESHOLDS["no_improve_window_size"]
    windows = [confs[i:i+window] for i in range(0, len(confs), window)]
    if len(windows) >= THRESHOLDS["no_improve_windows"]:
        avg1 = sum(windows[0]) / len(windows[0])
        avg2 = sum(windows[1]) / len(windows[1])
        if avg2 <= avg1:
            return _result(True, "no_improvement", [p["id"] for p in proposals[:window*2]])

    # Evidence-to-action failure
    window_size = THRESHOLDS["e2a_window_size"]
    window_props = proposals[:window_size]
    e2a_fail = [p["id"] for p in window_props if p.get("evidence") and not p.get("actionable")]
    if len(e2a_fail) >= THRESHOLDS["e2a_fail_count"]:
        return _result(True, "evidence_to_action_failure", e2a_fail)

    return _result(False, None, [])


def _result(inadequate: bool, reason: str | None, evidence_ids: List[str]):
    return {
        "inadequate": inadequate,
        "reason": reason,
        "evidence_refs": evidence_ids,
        "proposal": {
            "emit": inadequate,
            "class": "cognitive_improvement" if inadequate else None,
            "approval_needed": inadequate,
        },
    }
