import pytest
from weslr.cognitive_dialogue_integration import build_cdi_bundle


def test_requires_adequacy_finding():
    assert build_cdi_bundle(None) is None


def test_builds_bundle_with_lineage_and_gate():
    finding = {
        "response_text": "weak",
        "findings": ["low confidence"],
        "evidence": ["log: missing context"],
        "lineage_ref": {"proposal_id": "p1"},
        "improvement": "add reflection",
    }
    bundle = build_cdi_bundle(finding, operator_action="approve")
    assert bundle["explanation"]["lineage_ref"]["proposal_id"] == "p1"
    assert bundle["proposal"]["requires_approval"] is True
    assert bundle["operator_outcome"]["approved"] is True
    assert bundle["operator_outcome"]["risk"] == bundle["proposal"].get("risk")
    assert bundle["operator_outcome"]["rollback"] == bundle["proposal"].get("rollback")


def test_operator_outcome_not_required():
    finding = {"response_text": "weak", "findings": ["low confidence"], "evidence": [], "lineage_ref": {}}
    bundle = build_cdi_bundle(finding, operator_action=None)
    assert bundle["operator_outcome"] is None
