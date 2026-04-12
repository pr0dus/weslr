from weslr.background_observability import BackgroundObservability
from weslr.adequacy_lineage_view import build_proposal_view


def test_background_observability_includes_lineage_and_adequacy():
    obs = BackgroundObservability()
    obs.register_loop("loop1", workspace_id="ws1", user_id="u1", budget_cap=10.0)
    lineage_ref = {"proposal_id": "p1", "linked_checkpoint": "c1"}
    adequacy = {"reason": "repetition_shallow", "inadequate": True}
    obs.record_proposal("loop1", "p1", lineage_ref=lineage_ref, adequacy=adequacy)
    view = obs.view()
    assert view[0]["proposals_recent"][0]["proposal_lineage"] == lineage_ref
    assert view[0]["proposals_recent"][0]["adequacy"] == adequacy


def test_build_proposal_view_handles_missing_refs():
    entry = build_proposal_view("p2")
    assert entry["proposal_id"] == "p2"
    assert "proposal_lineage" not in entry
    assert "adequacy" not in entry
