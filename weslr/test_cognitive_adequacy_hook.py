import pytest
from weslr.cognitive_adequacy_hook import run_post_proposal_adequacy
from weslr.test_cognitive_adequacy_harness import FIXTURES


def test_post_proposal_hook_emits_for_repetition_with_context():
    fixture = FIXTURES["CA-REP-SHALLOW-1"]
    # pass prior similar proposals as evidence context
    evidence = {"similar_proposals": fixture["proposals"]}
    proposal = {"proposal_id": fixture["proposals"][0]["id"], "conf": fixture["proposals"][0]["conf"], "family": "shallowA"}
    res = run_post_proposal_adequacy(proposal, evidence=evidence)
    assert res["proposal"]["emit"] is True
    assert res["inadequate"] is True


def test_post_proposal_hook_guard_low_sample_without_context():
    proposal = {"proposal_id": "pX", "conf": 0.5}
    # low sample (single proposal) should not trigger; evaluator has min_sample=3
    res = run_post_proposal_adequacy(proposal)
    assert res["inadequate"] is False
    assert res["proposal"]["emit"] is False


def test_post_proposal_hook_proposal_only_output():
    proposal = {"proposal_id": "pY", "conf": 0.2}
    res = run_post_proposal_adequacy(proposal)
    assert "proposal" in res
    assert res["proposal"]["class"] in ("cognitive_improvement", None)
    # ensure no execution path fields present
    assert "route" not in res and "execute" not in res
