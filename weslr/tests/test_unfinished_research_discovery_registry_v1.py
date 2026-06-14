from __future__ import annotations

import ast
import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.unfinished_research_discovery_registry as registry
from weslr.unfinished_research_discovery_registry import (
    get_initial_domain_family_registry_v1,
    get_unfinished_research_registry_v1,
    summarize_domain_family_registry_v1,
    summarize_unfinished_research_registry_v1,
    to_domain_family_registry_json_safe_v1,
    to_unfinished_research_registry_json_safe_v1,
    validate_domain_family_registry_v1,
    validate_unfinished_research_registry_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _registry():
    return deepcopy(get_unfinished_research_registry_v1())


def _domain_registry():
    return deepcopy(get_initial_domain_family_registry_v1())


def test_modules_import_safely():
    assert registry is not None


def test_required_apis_exist():
    names = [
        "get_unfinished_research_registry_v1",
        "validate_unfinished_research_registry_v1",
        "summarize_unfinished_research_registry_v1",
        "to_unfinished_research_registry_json_safe_v1",
        "get_initial_domain_family_registry_v1",
        "validate_domain_family_registry_v1",
        "summarize_domain_family_registry_v1",
        "to_domain_family_registry_json_safe_v1",
    ]
    for name in names:
        assert hasattr(registry, name)
        assert callable(getattr(registry, name))


def test_initial_domain_family_registry_has_required_domains_and_fields():
    families = _domain_registry()
    ids = {item["domain_family_id"] for item in families}
    assert ids == {
        "rf_sensing",
        "energy_systems",
        "materials",
        "biology_medicine",
        "mathematics",
        "physics_quantum",
        "ai_cognition",
        "language_communication",
        "economics_labor",
        "standards_specification",
    }
    required = {
        "domain_family_id",
        "display_name",
        "description",
        "source_class_keywords",
        "signal_family_detection_cues",
        "query_templates",
        "likely_source_classes",
        "required_disconfirmation_classes",
        "blocked_claims",
        "operator_review_required",
    }
    for item in families:
        assert required.issubset(item)
        assert item["operator_review_required"] is True
        assert item["source_class_keywords"]
        assert item["signal_family_detection_cues"]
        assert item["query_templates"]
        assert item["likely_source_classes"]
        assert item["required_disconfirmation_classes"]
        assert item["blocked_claims"]


def test_valid_registry_validates_and_summarizes_metadata_only():
    packet = _registry()
    validation = validate_unfinished_research_registry_v1(packet)
    summary = summarize_unfinished_research_registry_v1(packet)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert summary["schema_version"] == "unfinished_research_discovery_registry_v1"
    assert summary["domain_family_count"] == 10
    assert summary["operator_review_required"] is True
    assert summary["summary_text"]
    assert "raw" not in json.dumps(summary).lower()
    assert "html" not in json.dumps(summary).lower()
    assert "snippet" not in json.dumps(summary).lower()


def test_denied_authority_flags_default_false_when_represented():
    packet = _registry()
    state = packet["denied_authority_flags_state"]
    assert all(value is False for value in state.values())
    validation = validate_unfinished_research_registry_v1(packet)
    assert validation["valid"] is True


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("schema_version", "wrong", "invalid_schema_version"),
        ("signal_types", ("wrong",), "invalid_signal_types"),
        ("routes", ("wrong",), "invalid_routes"),
        ("source_classes", ("wrong",), "invalid_source_classes"),
        ("evidence_roles", ("wrong",), "invalid_evidence_roles"),
        ("operator_confirmation_tokens", ("wrong",), "invalid_operator_confirmation_tokens"),
        ("expansion_recommendations", ("wrong",), "invalid_expansion_recommendations"),
        ("artifact_types", ("wrong",), "invalid_artifact_types"),
        ("required_disconfirmation_fields", ("wrong",), "invalid_required_disconfirmation_fields"),
        ("safe_discovery_meanings", ("wrong",), "invalid_safe_discovery_meanings"),
        ("forbidden_discovery_meanings", ("wrong",), "invalid_forbidden_discovery_meanings"),
        ("denied_authority_flags", ("wrong",), "invalid_denied_authority_flags"),
        ("forbidden_language_markers", ("wrong",), "invalid_forbidden_language_markers"),
    ],
)
def test_registry_invalid_values_fail_closed(field, value, expected_label):
    packet = _registry()
    packet[field] = value
    validation = validate_unfinished_research_registry_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_registry_missing_domain_family_fields_fail_closed():
    families = _domain_registry()
    families[0].pop("blocked_claims")
    validation = validate_domain_family_registry_v1(families)
    assert validation["blocked"] is True
    assert "missing_blocked_claims" in validation["blocked_labels"]


def test_domain_family_unknown_values_fail_closed():
    families = _domain_registry()
    families[0]["likely_source_classes"] = ("not_real",)
    validation = validate_domain_family_registry_v1(families)
    assert validation["blocked"] is True
    assert "unknown_source_class_value" in validation["blocked_labels"]


def test_json_safe_conversion_is_deterministic():
    packet = _registry()
    first = to_unfinished_research_registry_json_safe_v1(packet)
    second = to_unfinished_research_registry_json_safe_v1(packet)
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    domain_first = to_domain_family_registry_json_safe_v1(packet["domain_family_registry"])
    domain_second = to_domain_family_registry_json_safe_v1(packet["domain_family_registry"])
    assert domain_first == domain_second


def test_module_has_no_io_network_or_runtime_imports():
    source = inspect.getsource(registry)
    tree = ast.parse(source)
    forbidden = {"os", "sys", "subprocess", "socket", "urllib", "requests", "http", "pathlib", "openclaw"}
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports.isdisjoint(forbidden)
    assert "http://" not in source
    assert "https://" not in source
