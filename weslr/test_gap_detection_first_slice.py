import pytest

# Minimal harness for gap detection first-slice (proposals only, no activation)

REQUIRED_FIELDS = {
    "title",
    "why",
    "existing_vs_new",
    "risk_level",
    "doctrine_first",
    "activation_vs_new",
    "approval_needed",
}


def generate_proposals(signals: dict) -> list:
    """Pure harness function to simulate proposal generation.
    Signals keys: blocks (int), approvals (int), confidence (float), friction_same_capability (int).
    Bounded: max 1 proposal per scenario.
    """
    proposals = []
    # Blocked capability scenario
    if signals.get("blocks", 0) > 0:
        proposals.append({
            "title": "Harden blocked capability path",
            "why": "Repeated capability blocks require operator intervention",
            "existing_vs_new": "existing",
            "risk_level": "high",
            "doctrine_first": False,
            "activation_vs_new": "activation",
            "approval_needed": True,
        })
    # Evidence insufficiency / confidence dip
    elif signals.get("confidence", 1.0) < 0.5 or signals.get("evidence_gap", False):
        proposals.append({
            "title": "Address evidence insufficiency",
            "why": "Low confidence blocks decision progress",
            "existing_vs_new": "existing",
            "risk_level": "medium",
            "doctrine_first": False,
            "activation_vs_new": "activation",
            "approval_needed": True,
        })
    # Repeated friction same capability
    elif signals.get("friction_same_capability", 0) >= 2 or signals.get("approvals", 0) >= 2:
        proposals.append({
            "title": "Reduce friction on repeated capability",
            "why": "Repeated approvals/blocks indicate workflow bottleneck",
            "existing_vs_new": "existing",
            "risk_level": "medium",
            "doctrine_first": False,
            "activation_vs_new": "activation",
            "approval_needed": True,
        })
    # Normal path: no proposal
    return proposals[:1]  # bounded


def assert_proposal_shape(proposals: list, expect_count: int):
    assert len(proposals) == expect_count, f"expected {expect_count} proposals, got {len(proposals)}"
    for p in proposals:
        assert REQUIRED_FIELDS.issubset(p.keys()), f"missing fields: {REQUIRED_FIELDS - set(p.keys())}"
        assert p["existing_vs_new"] == "existing"
        assert p["activation_vs_new"] == "activation"
        assert isinstance(p["approval_needed"], bool)


def test_blocked_capability_scenario():
    proposals = generate_proposals({"blocks": 1, "approvals": 1, "confidence": 0.8})
    assert_proposal_shape(proposals, 1)
    assert proposals[0]["risk_level"] == "high"


def test_evidence_insufficiency_scenario():
    proposals = generate_proposals({"blocks": 0, "approvals": 0, "confidence": 0.45, "evidence_gap": True})
    assert_proposal_shape(proposals, 1)
    assert proposals[0]["risk_level"] == "medium"


def test_repeated_friction_same_capability():
    proposals = generate_proposals({"blocks": 0, "approvals": 3, "confidence": 0.7, "friction_same_capability": 3})
    assert_proposal_shape(proposals, 1)
    assert proposals[0]["risk_level"] == "medium"


def test_normal_low_risk_path_no_proposal():
    proposals = generate_proposals({"blocks": 0, "approvals": 0, "confidence": 0.8})
    assert len(proposals) == 0
