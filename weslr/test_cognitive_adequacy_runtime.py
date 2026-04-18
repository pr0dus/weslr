import pytest
from weslr import cognitive_adequacy as ca
from weslr.test_cognitive_adequacy_harness import FIXTURES


@pytest.mark.parametrize("case_id", [
    "CA-REP-SHALLOW-1",
    "CA-REJECT-1",
    "CA-LOWCONF-1",
    "CA-SAMEFIX-1",
    "CA-NO-IMPROVE-1",
    "CA-E2A-1",
])
def test_runtime_matches_harness_inadequacy_cases(case_id):
    fixture = FIXTURES[case_id]
    result = ca.evaluate(fixture["proposals"],
                        operator_requested_repetition=fixture.get("operator_requested_repetition", False),
                        exploratory_window=fixture.get("exploratory_window", False))
    assert result["inadequate"] is True
    assert result["proposal"]["emit"] is True
    assert result["proposal"]["approval_needed"] is True
    assert result["reason"] is not None
    assert result["evidence_refs"]


@pytest.mark.parametrize("case_id", [
    "CA-GUARD-OP-1",
    "CA-GUARD-LOW-SAMPLE-1",
    "CA-GUARD-EXPLORE-1",
])
def test_runtime_matches_harness_guard_cases(case_id):
    fixture = FIXTURES[case_id]
    result = ca.evaluate(fixture["proposals"],
                        operator_requested_repetition=fixture.get("operator_requested_repetition", False),
                        exploratory_window=fixture.get("exploratory_window", False))
    assert result["inadequate"] is False
    assert result["proposal"]["emit"] is False


def test_evidence_refs_align_lowconf():
    res = ca.evaluate(FIXTURES["CA-LOWCONF-1"]["proposals"])
    assert set(res["evidence_refs"]) == {"p9", "p10", "p11"}


def test_evidence_refs_align_e2a():
    res = ca.evaluate(FIXTURES["CA-E2A-1"]["proposals"])
    assert set(res["evidence_refs"]) == {"p23", "p24"}
