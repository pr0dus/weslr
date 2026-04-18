import types

import pytest

import weslr.decision_layer as dl_mod
from weslr.decision_layer import DecisionLayer


def _patched_layer(monkeypatch):
    layer = DecisionLayer()
    def mk_item(title):
        return dl_mod.DecisionItem(
            title=title,
            reason=title,
            source_modules=["test"],
            confidence=0.8,
            recommended_action="review",
            item_id=title,
            urgency_level="normal",
        )
    monkeypatch.setattr(layer, "_synthesize_what_matters_now", lambda: [mk_item("wm")])
    monkeypatch.setattr(layer, "_synthesize_blocked_items", lambda: [mk_item("block")])
    monkeypatch.setattr(layer, "_synthesize_next_actions", lambda: [mk_item("run task")])
    monkeypatch.setattr(layer, "_synthesize_approval_queue", lambda: [mk_item("approve")])
    return layer


def test_decision_layer_active(monkeypatch):
    monkeypatch.setattr(dl_mod, "DECISION_LAYER_PHASE3_ACTIVE", True)
    layer = _patched_layer(monkeypatch)
    out = layer.compute().to_dict()
    assert out["synthesis_version"] == "v2"
    assert out["what_matters_now"] and out["blocked_items"] and out["next_actions"] and out["approval_queue"]


def test_decision_layer_rollback(monkeypatch):
    monkeypatch.setattr(dl_mod, "DECISION_LAYER_PHASE3_ACTIVE", False)
    layer = _patched_layer(monkeypatch)
    out = layer.compute().to_dict()
    assert out["synthesis_version"] == "rollback-disabled"
    assert out["what_matters_now"] == []
    assert out["blocked_items"] == []
    assert out["next_actions"] == []
    assert out["approval_queue"] == []
    # Governance/identity unaffected: toggle only changes decision output, not cache or external state


def test_decision_layer_reenable(monkeypatch):
    # ensure re-enable restores synthesized output
    monkeypatch.setattr(dl_mod, "DECISION_LAYER_PHASE3_ACTIVE", True)
    layer = _patched_layer(monkeypatch)
    out = layer.compute().to_dict()
    assert out["synthesis_version"] == "v2"
    assert out["what_matters_now"]
