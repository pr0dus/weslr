from weslr.cognitive_reflection import run_reflection

def test_reflection_adds_notes_for_non_actionable():
    proposal = {"proposal_id": "p1", "conf": 0.3, "actionable": False}
    res = run_reflection(proposal)
    assert res["reflection_added"] is True
    assert "missing_actionable_step" in res["consistency_notes"]

def test_reflection_handles_coverage_gap():
    proposal = {"proposal_id": "p2", "conf": 0.5, "actionable": True}
    evidence = {"coverage_gap": True, "originating_evidence_signal": "sigA"}
    res = run_reflection(proposal, evidence=evidence)
    assert "coverage_gap_flag" in res["consistency_notes"]
