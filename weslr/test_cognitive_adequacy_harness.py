import pytest

# Doctrine thresholds
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


def evaluate_case(case):
    proposals = case["proposals"]
    # Guards
    if case.get("operator_requested_repetition"):
        return {"inadequate": False, "reason": "operator_requested", "evidence": []}
    if len(proposals) < THRESHOLDS["min_sample"]:
        return {"inadequate": False, "reason": "low_sample", "evidence": []}
    if case.get("exploratory_window"):
        confs = [p["conf"] for p in proposals]
        improving = all((confs[i+1] - confs[i]) >= THRESHOLDS["explore_improve_step"] for i in range(len(confs)-1))
        if improving:
            return {"inadequate": False, "reason": "exploratory_improving", "evidence": []}

    evidence = []

    # Repetition/shallow (family id or fix repeated)
    family_ids = [p.get("family") for p in proposals if p.get("family")]
    if family_ids:
        top_family = max(set(family_ids), key=family_ids.count)
        if family_ids.count(top_family) >= THRESHOLDS["repetition_count"]:
            evidence = [p["id"] for p in proposals]
            return {"inadequate": True, "reason": "repetition_shallow", "evidence": evidence}

    # Reject/ignore ratio
    actions = [p.get("action") for p in proposals]
    rej_ign = sum(1 for a in actions if a in {"rejected", "ignored"})
    if len(proposals) >= THRESHOLDS["reject_ignore_window"]:
        ratio = rej_ign / len(proposals)
        if ratio >= THRESHOLDS["reject_ignore_ratio"]:
            evidence = [p["id"] for p in proposals]
            return {"inadequate": True, "reason": "low_usefulness", "evidence": evidence}

    # Low confidence streak
    confs = [p["conf"] for p in proposals]
    streak = 0
    for c in confs:
        if c < THRESHOLDS["low_conf_threshold"]:
            streak += 1
            if streak >= THRESHOLDS["low_conf_streak"]:
                evidence = [p["id"] for p in proposals[:THRESHOLDS["low_conf_streak"]]]
                return {"inadequate": True, "reason": "low_confidence_streak", "evidence": evidence}
        else:
            streak = 0

    # Same fix loops
    fixes = [p.get("fix") for p in proposals if p.get("fix")]
    if fixes:
        top_fix = max(set(fixes), key=fixes.count)
        if fixes.count(top_fix) >= THRESHOLDS["same_fix_count"]:
            evidence = [p["id"] for p in proposals]
            return {"inadequate": True, "reason": "same_fix_loop", "evidence": evidence}

    # No improvement across windows
    window = THRESHOLDS["no_improve_window_size"]
    windows = [confs[i:i+window] for i in range(0, len(confs), window)]
    if len(windows) >= THRESHOLDS["no_improve_windows"]:
        avg1 = sum(windows[0]) / len(windows[0])
        avg2 = sum(windows[1]) / len(windows[1])
        if avg2 <= avg1:
            evidence = [p["id"] for p in proposals[:window*2]]
            return {"inadequate": True, "reason": "no_improvement", "evidence": evidence}

    # Evidence-to-action failure
    window_size = THRESHOLDS["e2a_window_size"]
    window_props = proposals[:window_size]
    e2a_fail = sum(1 for p in window_props if p.get("evidence") and not p.get("actionable"))
    if e2a_fail >= THRESHOLDS["e2a_fail_count"]:
        evidence = [p["id"] for p in window_props if p.get("evidence") and not p.get("actionable")]
        return {"inadequate": True, "reason": "evidence_to_action_failure", "evidence": evidence}

    return {"inadequate": False, "reason": None, "evidence": []}


# Fixtures (synthetic per doctrine)
FIXTURES = {
    "CA-REP-SHALLOW-1": {
        "proposals": [
            {"id": "p1", "conf": 0.38, "status": "pending", "family": "shallowA", "chk": "c1"},
            {"id": "p2", "conf": 0.39, "status": "pending", "family": "shallowA", "chk": "c2"},
            {"id": "p3", "conf": 0.37, "status": "pending", "family": "shallowA", "chk": "c3"},
        ],
    },
    "CA-REJECT-1": {
        "proposals": [
            {"id": "p4", "conf": 0.55, "action": "rejected"},
            {"id": "p5", "conf": 0.52, "action": "ignored"},
            {"id": "p6", "conf": 0.48, "action": "rejected"},
            {"id": "p7", "conf": 0.50, "action": "ignored"},
            {"id": "p8", "conf": 0.53, "action": "rejected"},
        ],
    },
    "CA-LOWCONF-1": {
        "proposals": [
            {"id": "p9", "conf": 0.35},
            {"id": "p10", "conf": 0.30},
            {"id": "p11", "conf": 0.32},
        ],
    },
    "CA-SAMEFIX-1": {
        "proposals": [
            {"id": "p12", "conf": 0.45, "fix": "reinstall deps"},
            {"id": "p13", "conf": 0.47, "fix": "reinstall deps"},
            {"id": "p14", "conf": 0.46, "fix": "reinstall deps"},
        ],
    },
    "CA-NO-IMPROVE-1": {
        "proposals": [
            {"id": "p15", "conf": 0.41},
            {"id": "p16", "conf": 0.43},
            {"id": "p17", "conf": 0.42},
            {"id": "p18", "conf": 0.44},
            {"id": "p19", "conf": 0.40},
            {"id": "p20", "conf": 0.42},
            {"id": "p21", "conf": 0.41},
            {"id": "p22", "conf": 0.43},
        ],
    },
    "CA-E2A-1": {
        "proposals": [
            {"id": "p23", "conf": 0.55, "evidence": True, "actionable": False},
            {"id": "p24", "conf": 0.56, "evidence": True, "actionable": False},
            {"id": "p25", "conf": 0.58, "evidence": False, "actionable": True},
            {"id": "p26", "conf": 0.57, "evidence": False, "actionable": True},
        ],
    },
    "CA-GUARD-OP-1": {
        "operator_requested_repetition": True,
        "proposals": [
            {"id": "p27", "conf": 0.55, "family": "repeat_by_request"},
            {"id": "p28", "conf": 0.56, "family": "repeat_by_request"},
            {"id": "p29", "conf": 0.57, "family": "repeat_by_request"},
        ],
    },
    "CA-GUARD-LOW-SAMPLE-1": {
        "proposals": [
            {"id": "p30", "conf": 0.35},
            {"id": "p31", "conf": 0.33},
        ],
    },
    "CA-GUARD-EXPLORE-1": {
        "exploratory_window": True,
        "proposals": [
            {"id": "p32", "conf": 0.30},
            {"id": "p33", "conf": 0.36},
            {"id": "p34", "conf": 0.42},
        ],
    },
}


@pytest.mark.parametrize("case_id", [
    "CA-REP-SHALLOW-1",
    "CA-REJECT-1",
    "CA-LOWCONF-1",
    "CA-SAMEFIX-1",
    "CA-NO-IMPROVE-1",
    "CA-E2A-1",
])
def test_inadequacy_cases_emit_proposal(case_id):
    result = evaluate_case(FIXTURES[case_id])
    assert result["inadequate"] is True
    assert result["reason"] is not None
    assert result["evidence"]


@pytest.mark.parametrize("case_id", [
    "CA-GUARD-OP-1",
    "CA-GUARD-LOW-SAMPLE-1",
    "CA-GUARD-EXPLORE-1",
])
def test_guard_cases_do_not_emit(case_id):
    result = evaluate_case(FIXTURES[case_id])
    assert result["inadequate"] is False


def test_low_confidence_evidence_ids():
    result = evaluate_case(FIXTURES["CA-LOWCONF-1"])
    assert set(result["evidence"]) == {"p9", "p10", "p11"}


def test_e2a_failure_references_only_failures():
    result = evaluate_case(FIXTURES["CA-E2A-1"])
    assert result["inadequate"]
    assert set(result["evidence"]) == {"p23", "p24"}
