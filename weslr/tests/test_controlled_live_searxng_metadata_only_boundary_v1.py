from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

import weslr.controlled_live_searxng_metadata_only_boundary as boundary
from weslr.controlled_live_searxng_metadata_only_boundary import (
    ALLOWED_RESULT_FIELDS_V1,
    SCHEMA_VERSION_V1,
    build_controlled_live_searxng_boundary_config_v1,
    build_controlled_live_searxng_query_v1,
    run_controlled_live_searxng_metadata_only_boundary_v1,
    summarize_controlled_live_searxng_metadata_only_result_packet_v1,
    to_controlled_live_searxng_metadata_only_json_safe_v1,
    validate_controlled_live_searxng_boundary_config_v1,
    validate_controlled_live_searxng_metadata_only_result_packet_v1,
    validate_controlled_live_searxng_query_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}


class GetterSpy:
    def __init__(self, payload: dict, *, status: int = 200, content_type: str = "application/json"):
        self.calls = []
        self.payload = payload
        self.status = status
        self.content_type = content_type

    def __call__(self, url: str, timeout: int):
        self.calls.append((url, timeout))
        return {
            "status": self.status,
            "headers": {"Content-Type": self.content_type},
            "body": json.dumps(self.payload).encode("utf-8"),
            "url": url,
        }


def _result(**overrides):
    base = {
        "title": "WESLR RFC boundary paper",
        "url": "https://example.org/rfc-boundary",
        "engine": "duckduckgo",
        "engines": ["duckduckgo"],
        "score": 0.9,
        "publishedDate": "2024-01-01T00:00:00+00:00",
        "content": "safe metadata snippet",
        "ignored_field": "must_drop",
    }
    base.update(overrides)
    return base


def _enabled_config(**overrides):
    return build_controlled_live_searxng_boundary_config_v1(enabled=True, **overrides)


def test_required_public_apis_exist():
    names = [
        "build_controlled_live_searxng_boundary_config_v1",
        "validate_controlled_live_searxng_boundary_config_v1",
        "build_controlled_live_searxng_query_v1",
        "validate_controlled_live_searxng_query_v1",
        "run_controlled_live_searxng_metadata_only_boundary_v1",
        "validate_controlled_live_searxng_metadata_only_result_packet_v1",
        "summarize_controlled_live_searxng_metadata_only_result_packet_v1",
        "to_controlled_live_searxng_metadata_only_json_safe_v1",
    ]
    for name in names:
        assert hasattr(boundary, name)
        assert callable(getattr(boundary, name))


def test_disabled_by_default():
    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary")
    assert packet["ok"] is False
    assert packet["reason"] == "disabled"
    assert packet["results"] == []


def test_enabled_only_by_explicit_config_and_getter_required():
    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config())
    assert packet["reason"] == "http_getter_required"


@pytest.mark.parametrize(
    "url,valid",
    [
        ("http://127.0.0.1:8888", True),
        ("http://localhost:8888", True),
        ("http://192.168.1.3:8888", False),
        ("https://example.com", False),
        ("http://example.com:8888", False),
        (":bad", False),
    ],
)
def test_loopback_and_malformed_url_validation(url, valid):
    result = validate_controlled_live_searxng_boundary_config_v1({"base_url": url})
    assert result["valid"] is valid


def test_timeout_and_result_count_capped():
    config = build_controlled_live_searxng_boundary_config_v1(enabled=True, timeout_seconds=99, max_results=99)
    assert config["timeout_seconds"] == 5
    assert config["max_results"] == 5


def test_query_validation_rules():
    assert validate_controlled_live_searxng_query_v1({"query": "https://example.com"})["errors"] == ["url_as_query"]
    assert validate_controlled_live_searxng_query_v1({"query": "bad\x00query"})["errors"] == ["control_chars_in_query"]
    assert validate_controlled_live_searxng_query_v1({"query": "x" * 201})["errors"] == ["query_too_long"]


def test_get_request_shape_is_correct_and_no_real_http_needed():
    spy = GetterSpy({"results": [_result()]})
    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=spy)
    assert packet["ok"] is True
    assert len(spy.calls) == 1
    url, timeout = spy.calls[0]
    parsed = urlparse(url)
    assert parsed.scheme == "http"
    assert parsed.netloc == "127.0.0.1:8888"
    assert parsed.path == "/search"
    params = parse_qs(parsed.query)
    assert params["q"] == ["weslr boundary"]
    assert params["format"] == ["json"]
    assert params["language"] == ["en"]
    assert "%25" not in url
    assert timeout == 5


@pytest.mark.parametrize(
    "query",
    ["weslr boundary design v1", "C++ RF sensing?", "naïve boundary — test"],
)
def test_query_is_encoded_once(query):
    url = boundary.build_controlled_live_searxng_request_url_v1(
        boundary.build_controlled_live_searxng_query_v1(query),
        _enabled_config(),
    )
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    assert params["q"] == [query]
    assert "%25" not in url
    assert "q=" in url


def test_raw_response_body_not_retained_and_unknown_fields_dropped():
    spy = GetterSpy({"results": [_result(), _result(url="https://github.com/pr0dus/weslr")]})
    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=spy)
    serialized = json.dumps(packet)
    assert "ignored_field" not in serialized
    assert "raw_body" not in serialized
    for item in packet["results"]:
        assert tuple(item.keys()) == ALLOWED_RESULT_FIELDS_V1


def test_snippet_disabled_by_default():
    spy = GetterSpy({"results": [_result(content="<b>raw</b> snippet")]})
    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=spy)
    assert packet["snippets_retained"] is False
    assert packet["results"][0]["snippet"] is None


def test_snippet_length_capped_when_enabled():
    spy = GetterSpy({"results": [_result(content="<b>" + ("x" * 400) + "</b>")]})
    packet = run_controlled_live_searxng_metadata_only_boundary_v1(
        "weslr boundary",
        config=_enabled_config(snippet_policy="enabled"),
        http_getter=spy,
    )
    assert packet["snippets_retained"] is True
    assert len(packet["results"][0]["snippet"]) == 280


def test_url_domain_extraction_and_locator_id_deterministic():
    spy = GetterSpy({"results": [_result(url="https://github.com/pr0dus/weslr")]})
    packet1 = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=spy)
    packet2 = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=spy)
    assert packet1["results"][0]["domain"] == "github.com"
    assert packet1["results"][0]["locator_id"] == packet2["results"][0]["locator_id"]


def test_blocked_result_handling_and_private_hidden_patterns():
    spy = GetterSpy(
        {
            "results": [
                _result(url="https://example.org/ok"),
                _result(url="https://example.org/login"),
                _result(url="https://example.org/private?token=abc"),
                _result(url="https://facebook.com/user/x"),
            ]
        }
    )
    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=spy)
    assert packet["results_count_kept"] == 1
    assert packet["results_count_blocked"] == 3
    reasons = {item["block_reason"] for item in packet["blocked"]}
    assert {"login_or_account_url", "credential_in_url", "personal_data_platform"}.issubset(reasons)


def test_source_class_authority_and_evidence_role_derivation():
    spy = GetterSpy({
        "results": [
            _result(title="IETF RFC spec", url="https://ietf.org/rfc"),
            _result(title="Vendor API docs", url="https://docs.vendor.example/api"),
            _result(title="Repo", url="https://github.com/pr0dus/weslr"),
        ]
    })
    packet = run_controlled_live_searxng_metadata_only_boundary_v1(
        "weslr boundary",
        config=_enabled_config(query_family="rfc"),
        http_getter=spy,
    )
    assert packet["results"][0]["source_class_hint"] == "official_standard"
    assert packet["results"][0]["authority_guess"] == "official_primary"
    assert packet["results"][0]["evidence_role_guess"] == "prior_art"
    assert packet["results"][1]["source_class_hint"] == "official_vendor_documentation"
    assert packet["results"][2]["source_class_hint"] == "github_repository"


def test_freshness_access_and_privacy_guesses_bounded():
    spy = GetterSpy({"results": [_result(url="https://nature.com/paper", publishedDate="2020-01-01T00:00:00+00:00")]})
    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=spy)
    result = packet["results"][0]
    assert result["freshness_status_guess"] in {"fresh", "recent", "stale", "unknown"}
    assert result["access_license_status_guess"] in {"open_access", "registration_required", "paywalled", "unknown"}
    assert result["privacy_status_guess"] in {"public_non_personal", "mixed_personal_signals", "personal_data_present"}


def test_no_authority_flag_true_and_json_safe_conversion_and_summary():
    spy = GetterSpy({"results": [_result()]})
    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=spy)
    assert packet["boundary_version"] == SCHEMA_VERSION_V1
    assert not any(packet["authority_status"][key] for key in packet["authority_status"] if key != "all_authority_flags_false")
    safe = to_controlled_live_searxng_metadata_only_json_safe_v1(packet)
    json.dumps(safe)
    summary = summarize_controlled_live_searxng_metadata_only_result_packet_v1(packet)
    assert summary["validation_posture"] == "valid"
    assert len(summary["summary_text"]) <= 220


def test_malformed_json_and_http_fail_closed():
    def malformed(_url: str, _timeout: int):
        return {"status": 200, "headers": {"Content-Type": "application/json"}, "body": b"{"}

    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=malformed)
    assert packet["reason"] == "searxng_malformed_json"

    def timeout(_url: str, _timeout: int):
        raise TimeoutError("boom")

    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=timeout)
    assert packet["reason"] == "searxng_timeout"


def test_validation_rejects_extra_fields_and_accepts_good_packet():
    spy = GetterSpy({"results": [_result()]})
    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=spy)
    validation = validate_controlled_live_searxng_metadata_only_result_packet_v1(packet)
    assert validation["valid"] is True
    broken = json.loads(json.dumps(packet))
    broken["results"][0]["extra"] = True
    validation = validate_controlled_live_searxng_metadata_only_result_packet_v1(broken)
    assert validation["valid"] is False


def test_no_forbidden_imports_or_calls_in_module_source():
    source = (REPO_ROOT / "weslr" / "controlled_live_searxng_metadata_only_boundary.py").read_text()
    forbidden_markers = [
        "chat_responder",
        "dialogue",
        "chat_ui",
        "import main",
        ".weslr",
        "mlcf_searxng_source_locator_adapter_boundary",
        "openai",
        "anthropic",
        "gemini",
        "sqlite3",
        "requests_cache",
    ]
    for marker in forbidden_markers:
        assert marker not in source


def test_no_mlcf_routing_or_runtime_public_integration_confirmation():
    spy = GetterSpy({"results": [_result()]})
    packet = run_controlled_live_searxng_metadata_only_boundary_v1("weslr boundary", config=_enabled_config(), http_getter=spy)
    assert packet["safe_status"]["no_mlcf_routing"] is True
    assert packet["safe_status"]["no_runtime_integration"] is True
    assert packet["safe_status"]["no_public_integration"] is True


def test_no_write_to_disk_and_no_real_http_in_subprocess():
    command = [
        sys.executable,
        "-c",
        (
            "from weslr.controlled_live_searxng_metadata_only_boundary import "
            "run_controlled_live_searxng_metadata_only_boundary_v1;"
            "import json;"
            "print(json.dumps(run_controlled_live_searxng_metadata_only_boundary_v1('weslr boundary')))"
        ),
    ]
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    packet = json.loads(completed.stdout.strip())
    assert packet["reason"] == "disabled"


def test_protected_files_unchanged_in_worktree():
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", *sorted(PROTECTED_FILES)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""
