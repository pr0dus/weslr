import pytest

# Pure test harness for Phase 4 dry-run (proposals only, no outbound effects)

REQUIRED_FIELDS = {
    "title",
    "why",
    "proposal_only",
    "risk_level",
    "requires_approval",
    "blocked",
    "rollback_mode",
}


def generate_acquisition_proposals(confidence: float, coverage_gaps: bool, risk_level: str = "low", enabled: bool = True):
    """Return proposals for proactive acquisition, proposal-only, bounded to 1.
    - If not enabled (rollback), returns empty list with rollback flag.
    - If evidence sufficient (confidence >= 0.6 and no gap): no proposals.
    - If gap exists: emit proposal; high risk -> blocked until approval.
    """
    proposals = []
    if not enabled:
        return proposals, True
    if confidence >= 0.6 and not coverage_gaps:
        return proposals, False
    # insufficient evidence
    blocked = risk_level == "high"
    proposals.append({
        "title": "Proactive acquisition",
        "why": "Evidence insufficiency detected",
        "proposal_only": True,
        "risk_level": risk_level,
        "requires_approval": True,
        "blocked": blocked,
        "rollback_mode": False,
    })
    return proposals[:1], False


def assert_shape(proposals, expect_count, expect_blocked=None):
    assert len(proposals) == expect_count, f"expected {expect_count}, got {len(proposals)}"
    for p in proposals:
        assert REQUIRED_FIELDS.issubset(p.keys()), f"missing fields: {REQUIRED_FIELDS - set(p.keys())}"
        assert p["proposal_only"] is True
        if expect_blocked is not None:
            assert p["blocked"] is expect_blocked


def test_sufficient_evidence_no_proposal():
    proposals, rollback = generate_acquisition_proposals(confidence=0.75, coverage_gaps=False, risk_level="low", enabled=True)
    assert rollback is False
    assert_shape(proposals, 0)


def test_insufficient_evidence_low_risk_proposal():
    proposals, rollback = generate_acquisition_proposals(confidence=0.4, coverage_gaps=True, risk_level="low", enabled=True)
    assert rollback is False
    assert_shape(proposals, 1, expect_blocked=False)


def test_high_risk_acquisition_blocked():
    proposals, rollback = generate_acquisition_proposals(confidence=0.45, coverage_gaps=True, risk_level="high", enabled=True)
    assert rollback is False
    assert_shape(proposals, 1, expect_blocked=True)


def test_rollback_to_assessment_only():
    proposals, rollback = generate_acquisition_proposals(confidence=0.3, coverage_gaps=True, risk_level="high", enabled=False)
    assert rollback is True
    assert_shape(proposals, 0)
