from unittest.mock import patch

from weslr.ingress_adapter import normalize_request, route_request
from weslr.chat_responder import Response


def test_normalize_request_maps_fields():
    raw = {
        "message": "status",
        "persona": "engineer",
        "domain": "technical",
        "previous_decision": {"what_matters_now": []},
        "mode": {"style": "concise"},
    }
    normalized = normalize_request(raw)
    assert normalized["message"] == "status"
    assert normalized["persona"] == "engineer"
    assert normalized["domain"] == "technical"
    assert normalized["previous_decision"] == {"what_matters_now": []}
    assert normalized["explanation_overrides"] == {"style": "concise"}


def test_route_request_calls_handle_request_once_and_forwards_previous():
    raw = {
        "message": "status",
        "persona": "engineer",
        "domain": "technical",
        "previous_decision": {"what_matters_now": []},
    }
    fake_resp = Response(content="ok")
    with patch("weslr.ingress_adapter.handle_request", return_value=fake_resp) as mock_handle:
        resp = route_request(raw)
    assert resp is fake_resp
    assert mock_handle.call_count == 1
    args, kwargs = mock_handle.call_args
    # normalized request passed first
    assert isinstance(args[0], dict)
    assert kwargs["persona"] == "engineer"
    assert kwargs["domain"] == "technical"
    assert kwargs["previous_decision"] == {"what_matters_now": []}


def test_route_request_defaults_persona_domain():
    raw = {"message": "status"}
    with patch("weslr.ingress_adapter.handle_request", return_value=Response(content="ok")) as mock_handle:
        route_request(raw)
    args, kwargs = mock_handle.call_args
    assert kwargs["persona"] == "general user"
    assert kwargs["domain"] == "general"
