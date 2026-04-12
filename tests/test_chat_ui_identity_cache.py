import os
import sys
import types

# Ensure test can import the canonical WESLR core if available for route_request import, otherwise tests
# monkeypatch route_request before use. Prefer env override to stay portable.
import importlib.machinery
import importlib.util

ROOT = "/data/data/com.termux/files/home/.openclaw/workspace"
CORE_ENV = "WESLR_CORE_PATH"
core_path = os.environ.get(CORE_ENV)

sys.path[:] = [p for p in sys.path if p]  # keep defaults but reorder below
if core_path:
    sys.path.insert(0, core_path)
if ROOT not in sys.path:
    sys.path.insert(1, ROOT)

loader = importlib.machinery.SourceFileLoader("host_chat_ui", os.path.join(ROOT, "chat_ui.py"))
spec = importlib.util.spec_from_loader(loader.name, loader)
host_chat_ui = importlib.util.module_from_spec(spec)
loader.exec_module(host_chat_ui)
chat_ui = host_chat_ui

# Ensure compatibility if chat_ui lacks newer helpers.
if not hasattr(chat_ui, "DECISION_CACHE"):
    chat_ui.DECISION_CACHE = {}

if not hasattr(chat_ui, "_compute_identity"):
    def _compute_identity(payload: dict, client_address=None):
        workspace_id = payload.get("workspace_id") or payload.get("org_id") or payload.get("tenant_id")
        operator_id = payload.get("operator_id")
        resolved_user = str(operator_id) if operator_id else None
        resolved_workspace = str(workspace_id) if workspace_id else None
        cache_key = f"{resolved_workspace or 'global'}::{resolved_user}" if resolved_user else None
        return cache_key, resolved_workspace, resolved_user
    chat_ui._compute_identity = _compute_identity

class DummyResp:
    def __init__(self, snapshot=None):
        self.content = "ok"
        self.actions = []
        self.metadata = {"decision_snapshot": snapshot} if snapshot is not None else {}


def test_same_user_workspace_gets_continuity(monkeypatch):
    chat_ui.DECISION_CACHE.clear()

    # Stub route_request to echo back snapshot
    def fake_route(payload):
        # Assert previous_decision passed on second call
        if payload.get("previous_decision"):
            assert payload["previous_decision"].get("from") == "first"
        return DummyResp(snapshot={"from": payload.get("tag", "first")})

    monkeypatch.setattr(chat_ui, "route_request", fake_route)

    # First call seeds cache
    req1 = {
        "workspace_id": "ws1",
        "operator_id": "userA",
        "message": "hi",
        "tag": "first",
    }
    handler = types.SimpleNamespace(client_address=("1.2.3.4", 0))
    cache_key, ws, user = chat_ui._compute_identity(req1, handler.client_address)
    prev = chat_ui.DECISION_CACHE.get(cache_key)
    assert prev is None
    resp1 = chat_ui.route_request(req1)
    snap1 = resp1.metadata.get("decision_snapshot")
    chat_ui.DECISION_CACHE[cache_key] = snap1

    # Second call reuses continuity
    req2 = {
        "workspace_id": "ws1",
        "operator_id": "userA",
        "message": "again",
        "tag": "second",
    }
    cache_key2, _, _ = chat_ui._compute_identity(req2, handler.client_address)
    assert cache_key2 == cache_key
    req2_prev = chat_ui.DECISION_CACHE.get(cache_key2)
    assert req2_prev == {"from": "first"}
    resp2 = chat_ui.route_request({**req2, "previous_decision": req2_prev})
    assert resp2.metadata.get("decision_snapshot") == {"from": "second"}


def test_different_users_do_not_share(monkeypatch):
    chat_ui.DECISION_CACHE.clear()

    def fake_route(payload):
        return DummyResp(snapshot={"from": payload.get("tag")})

    monkeypatch.setattr(chat_ui, "route_request", fake_route)

    handler = types.SimpleNamespace(client_address=("1.2.3.4", 0))

    req_a = {"workspace_id": "ws1", "operator_id": "userA", "message": "hi", "tag": "A"}
    key_a, _, _ = chat_ui._compute_identity(req_a, handler.client_address)
    chat_ui.DECISION_CACHE[key_a] = chat_ui.route_request(req_a).metadata["decision_snapshot"]

    req_b = {"workspace_id": "ws1", "operator_id": "userB", "message": "hi", "tag": "B"}
    key_b, _, _ = chat_ui._compute_identity(req_b, handler.client_address)
    assert key_a != key_b
    assert chat_ui.DECISION_CACHE.get(key_b) is None


def test_missing_user_id_is_stateless(monkeypatch):
    chat_ui.DECISION_CACHE.clear()

    def fake_route(payload):
        # Ensure no previous_decision is passed when user is unresolved
        assert payload.get("previous_decision") is None
        return DummyResp(snapshot={"from": payload.get("tag")})

    monkeypatch.setattr(chat_ui, "route_request", fake_route)

    handler = types.SimpleNamespace(client_address=("5.6.7.8", 0))
    req = {"message": "hi", "tag": "noid"}
    key, _, _ = chat_ui._compute_identity(req, handler.client_address)
    assert key is None
    resp = chat_ui.route_request(req)
    assert resp.metadata.get("decision_snapshot") == {"from": "noid"}
    assert chat_ui.DECISION_CACHE == {}
