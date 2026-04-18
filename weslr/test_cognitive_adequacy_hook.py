import pytest
from weslr.cognitive_adequacy_hook import run_post_proposal_adequacy
from weslr.test_cognitive_adequacy_harness import FIXTURES


def test_post_proposal_hook_emits_for_repetition_with_context():
    fixture = FIXTURES["CA-REP-SHALLOW-1"]
    evidence = {"similar_proposals": fixture["proposals"]}
    proposal = {"proposal_id": fixture["proposals"][0]["id"], "conf": fixture["proposals"][0]["conf"], "family": "shallowA"}
    res = run_post_proposal_adequacy(proposal, evidence=evidence)
    assert res["proposal"]["emit"] is True
    assert res["inadequate"] is True


def test_post_proposal_hook_guard_low_sample_without_context():
    proposal = {"proposal_id": "pX", "conf": 0.5}
    res = run_post_proposal_adequacy(proposal)
    assert res["inadequate"] is False
    assert res["proposal"]["emit"] is False


def test_post_proposal_hook_proposal_only_output():
    proposal = {"proposal_id": "pY", "conf": 0.2}
    res = run_post_proposal_adequacy(proposal)
    assert "proposal" in res
    assert res["proposal"]["class"] in ("cognitive_improvement", None)
    assert "route" not in res and "execute" not in res


def test_post_proposal_hook_guard_operator_request():
    evidence = {
        "operator_requested_repetition": True,
        "similar_proposals": FIXTURES["CA-GUARD-OP-1"]["proposals"],
    }
    proposal = {"proposal_id": "pG", "conf": 0.55, "family": "repeat_by_request"}
    res = run_post_proposal_adequacy(proposal, evidence=evidence)
    assert res["inadequate"] is False
    assert res["proposal"]["emit"] is False


def test_post_proposal_hook_guard_exploratory():
    evidence = {
        "exploratory_window": True,
        "similar_proposals": FIXTURES["CA-GUARD-EXPLORE-1"]["proposals"],
    }
    proposal = {"proposal_id": "pE", "conf": 0.30}
    res = run_post_proposal_adequacy(proposal, evidence=evidence)
    assert res["inadequate"] is False
    assert res["proposal"]["emit"] is False


def test_post_proposal_reflection_optional_and_off_by_default():
    fixture = FIXTURES["CA-LOWCONF-1"]
    evidence = {"similar_proposals": fixture["proposals"]}
    proposal = fixture["proposals"][0]
    res = run_post_proposal_adequacy(proposal, evidence=evidence)
    assert "reflection" not in res


def test_post_proposal_reflection_when_enabled():
    fixture = FIXTURES["CA-E2A-1"]
    evidence = {"similar_proposals": fixture["proposals"], "coverage_gap": True}
    proposal = fixture["proposals"][0]
    res = run_post_proposal_adequacy(proposal, evidence=evidence, reflection_enabled=True)
    assert res.get("reflection", {}).get("reflection_added") is True
    assert isinstance(res.get("reflection", {}).get("consistency_notes"), list)
