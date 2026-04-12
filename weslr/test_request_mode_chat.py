import builtins
from types import SimpleNamespace

import sys
from types import SimpleNamespace

from weslr.chat_responder import handle_request


def test_chat_mode_skips_status(monkeypatch):
    # Inject a fake DecisionLayer module; it should not be used in chat mode.
    fake_module = SimpleNamespace(DecisionLayer=SimpleNamespace(compute_with_signals=lambda req: (_ for _ in ()).throw(AssertionError("should not be called"))))
    monkeypatch.setitem(sys.modules, "weslr.decision_layer", fake_module)

    resp = handle_request({"message": "hi", "request_mode": "chat"})
    assert "what matters now" not in resp.content.lower()
    assert "status" not in resp.content.lower()


def test_status_mode_uses_decision(monkeypatch):
    called = {"seen": False}

    class FakeDL:
        @staticmethod
        def compute_with_signals(req):
            called["seen"] = True
            return {
                "what_matters_now": [{"title": "X", "reason": "test"}],
                "blocked_items": [],
                "approval_queue": [],
                "next_actions": [],
                "confidence": 0.5,
                "evidence_gaps": None,
            }

    fake_module = SimpleNamespace(DecisionLayer=FakeDL)
    monkeypatch.setitem(sys.modules, "weslr.decision_layer", fake_module)

    resp = handle_request({"message": "status", "request_mode": "status"})
    assert called["seen"] is True
    assert "what matters now" in resp.content.lower()
