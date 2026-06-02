from __future__ import annotations

import ast
import builtins
import inspect
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.document_access_pii_boundary as mod


PROTECTED_MODULE_HINTS = (
    "weslr.chat_responder",
    "weslr.main",
    "dialogue",
    "chat_ui",
    "weslr.voice_gateway",
    "weslr.voice_layer.ambient_loop",
    "weslr.voice_layer.run_ambient",
    "weslr.proactive_daemon",
    "weslr.frontier_daemon",
)


def _example(example_id: str):
    return next(
        item for item in mod.build_initial_document_access_examples_v1()
        if item["document_access_packet_id"] == example_id
    )


def _imported_module_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_module_imports_safely() -> None:
    assert mod.HELPER_TYPE_V1 == "document_access_pii_boundary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules
    assert "weslr.voice_gateway" not in sys.modules
    assert "weslr.voice_layer.ambient_loop" not in sys.modules
    assert "weslr.voice_layer.run_ambient" not in sys.modules
    assert "weslr.proactive_daemon" not in sys.modules
    assert "weslr.frontier_daemon" not in sys.modules

    source = inspect.getsource(mod)
    imported = _imported_module_names(source)
    for hint in PROTECTED_MODULE_HINTS:
        assert hint not in imported


def test_module_does_not_read_write_or_touch_weslr(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def _blocked(*args, **kwargs):
        calls.append("io")
        raise AssertionError("file I/O not allowed")

    monkeypatch.setattr(builtins, "open", _blocked)
    monkeypatch.setattr(Path, "read_text", _blocked, raising=False)
    monkeypatch.setattr(Path, "write_text", _blocked, raising=False)
    monkeypatch.setattr(Path, "open", _blocked, raising=False)

    packet = mod.build_document_access_packet_v1(
        document_access_packet_id="io_guard",
        source_id="src_io",
        source_type="web_source",
        source_name="public article",
        source_scope="public_source",
        access_level="public_source",
        privacy_sensitivity="non_sensitive",
        detected_pii_categories=[],
        scrubbing_mode="no_scrub_required",
        allowed_uses=["may_read_summary"],
        blocked_uses=["may_use_for_action"],
        raw_content_allowed=False,
        summary_allowed=True,
        indexing_allowed=False,
        vectorization_allowed=False,
        private_citation_allowed=False,
        public_citation_allowed=True,
        answer_use_allowed=True,
        public_claim_use_allowed=False,
        action_use_allowed=False,
        owner_review_required=False,
        operator_review_required=False,
        deletion_required_on_request=True,
        export_required_on_request=True,
        retention_policy_ref="public_source_retention_policy_v1",
        source_evidence_graph_allowed=True,
        rag_routing_allowed=True,
        daemon_packet_allowed=False,
        recommended_next_gate="safe",
    )
    assert packet["document_access_packet_id"] == "io_guard"
    assert calls == []


def test_module_does_not_import_or_call_protected_runtime_files(monkeypatch: pytest.MonkeyPatch) -> None:
    blocked_calls: list[str] = []

    def _sentinel(*args, **kwargs):
        blocked_calls.append("hit")
        raise AssertionError("protected runtime path touched")

    monkeypatch.setattr(builtins, "open", _sentinel)
    monkeypatch.setattr(Path, "read_text", _sentinel, raising=False)
    monkeypatch.setattr(Path, "write_text", _sentinel, raising=False)
    monkeypatch.setattr(Path, "open", _sentinel, raising=False)

    packet = mod.build_document_access_packet_v1(
        document_access_packet_id="protect_1",
        source_id="src_protect",
        source_type="unknown_source",
        source_name="neutral",
        source_scope="unknown_access",
        access_level="unknown_access",
        privacy_sensitivity="unknown_sensitivity",
        detected_pii_categories=[],
        scrubbing_mode="metadata_only",
        allowed_uses=["may_read_metadata"],
        blocked_uses=["blocked"],
        raw_content_allowed=False,
        summary_allowed=False,
        indexing_allowed=False,
        vectorization_allowed=False,
        private_citation_allowed=False,
        public_citation_allowed=False,
        answer_use_allowed=False,
        public_claim_use_allowed=False,
        action_use_allowed=False,
        owner_review_required=False,
        operator_review_required=False,
        deletion_required_on_request=True,
        export_required_on_request=True,
        retention_policy_ref="rt",
        source_evidence_graph_allowed=False,
        rag_routing_allowed=False,
        daemon_packet_allowed=False,
        recommended_next_gate="metadata only",
    )
    assert packet["document_access_packet_id"] == "protect_1"
    assert blocked_calls == []


def test_builds_deterministic_document_access_packet() -> None:
    packet_a = mod.build_document_access_packet_v1(
        document_access_packet_id="pkt_1",
        source_id="src_1",
        source_type="web_source",
        source_name="public article",
        source_scope="public_source",
        access_level="public_source",
        privacy_sensitivity="non_sensitive",
        detected_pii_categories=[],
        scrubbing_mode="no_scrub_required",
        allowed_uses=["may_read_summary", "may_cite_public"],
        blocked_uses=["may_use_for_action"],
        raw_content_allowed=True,
        summary_allowed=True,
        indexing_allowed=True,
        vectorization_allowed=False,
        private_citation_allowed=False,
        public_citation_allowed=True,
        answer_use_allowed=True,
        public_claim_use_allowed=False,
        action_use_allowed=False,
        owner_review_required=False,
        operator_review_required=False,
        deletion_required_on_request=False,
        export_required_on_request=False,
        retention_policy_ref="public_source_retention_policy_v1",
        source_evidence_graph_allowed=True,
        rag_routing_allowed=True,
        daemon_packet_allowed=False,
        recommended_next_gate="public use allowed",
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        proof_claim_allowed=False,
        learning_claimed=False,
    )
    packet_b = mod.build_document_access_packet_v1(
        document_access_packet_id="pkt_1",
        source_id="src_1",
        source_type="web_source",
        source_name="public article",
        source_scope="public_source",
        access_level="public_source",
        privacy_sensitivity="non_sensitive",
        detected_pii_categories=[],
        scrubbing_mode="no_scrub_required",
        allowed_uses=["may_read_summary", "may_cite_public"],
        blocked_uses=["may_use_for_action"],
        raw_content_allowed=True,
        summary_allowed=True,
        indexing_allowed=True,
        vectorization_allowed=False,
        private_citation_allowed=False,
        public_citation_allowed=True,
        answer_use_allowed=True,
        public_claim_use_allowed=False,
        action_use_allowed=False,
        owner_review_required=False,
        operator_review_required=False,
        deletion_required_on_request=False,
        export_required_on_request=False,
        retention_policy_ref="public_source_retention_policy_v1",
        source_evidence_graph_allowed=True,
        rag_routing_allowed=True,
        daemon_packet_allowed=False,
        recommended_next_gate="public use allowed",
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        proof_claim_allowed=False,
        learning_claimed=False,
    )
    assert packet_a == packet_b
    assert packet_a["raw_content_allowed"] is True
    assert packet_a["public_citation_allowed"] is True


def test_classifies_public_source_access() -> None:
    assert mod.classify_document_access_v1(source_scope="public_source", access_level="") == "public_source"


def test_classifies_owner_private_access() -> None:
    assert mod.classify_document_access_v1(source_scope="owner_private", access_level="") == "owner_private"


def test_classifies_pii_sensitivity_from_explicit_metadata_only() -> None:
    assert mod.classify_pii_sensitivity_v1(detected_pii_categories=["email_address", "phone_number"]) == "medium_sensitivity"
    assert mod.classify_pii_sensitivity_v1(detected_pii_categories=["api_key_or_token"]) == "restricted_sensitive"


def test_selects_scrubbing_mode_for_direct_identifiers() -> None:
    assert mod.select_scrubbing_mode_v1(access_level="project_internal", privacy_sensitivity="medium_sensitivity", detected_pii_categories=["email_address", "phone_number"]) == "redact_direct_identifiers"


def test_selects_block_mode_for_api_key_token() -> None:
    assert mod.select_scrubbing_mode_v1(access_level="owner_private", privacy_sensitivity="restricted_sensitive", detected_pii_categories=["api_key_or_token"]) == "block_content_use"


def test_validates_normal_packet() -> None:
    assert mod.validate_document_access_packet_v1(_example("public_source_may_be_summarized_and_cited_publicly")) is True


def test_summarizes_packet() -> None:
    packet = _example("owner_private_document_supports_private_answer_not_public_citation")
    summary = mod.summarize_document_access_packet_v1(packet)
    assert summary["summary_type"] == mod.SUMMARY_TYPE_V1
    assert summary["document_access_packet_id"] == packet["document_access_packet_id"]
    assert summary["access_level"] == "owner_private"
    assert summary["scrubbing_mode"] == "summary_only"


def test_json_safe_export_works() -> None:
    safe = mod.to_document_access_json_safe_v1(_example("email_phone_requires_identifier_redaction"))
    json.dumps(safe)
    assert safe["document_access_packet_id"] == "email_phone_requires_identifier_redaction"


def test_all_initial_examples_exist() -> None:
    examples = mod.build_initial_document_access_examples_v1()
    ids = {item["document_access_packet_id"] for item in examples}
    assert len(examples) == 10
    assert ids == {
        "public_source_may_be_summarized_and_cited_publicly",
        "owner_private_document_supports_private_answer_not_public_citation",
        "access_restricted_document_blocks_rag_retrieval",
        "email_phone_requires_identifier_redaction",
        "api_key_blocks_content_use",
        "child_data_restricted_sensitive",
        "health_legal_data_owner_operator_review",
        "uploaded_project_file_summary_only_graph_allowed",
        "private_evidence_blocks_public_website_claim",
        "daemon_receives_access_blocked_compact_verdict",
    }


@pytest.mark.parametrize(
    "example_id,expect",
    [
        ("public_source_may_be_summarized_and_cited_publicly", {"summary_allowed": True, "public_citation_allowed": True, "access_level": "public_source"}),
        ("owner_private_document_supports_private_answer_not_public_citation", {"public_citation_allowed": False, "private_citation_allowed": True}),
        ("access_restricted_document_blocks_rag_retrieval", {"rag_routing_allowed": False, "access_level": "access_blocked"}),
        ("email_phone_requires_identifier_redaction", {"scrubbing_mode": "redact_direct_identifiers", "privacy_sensitivity": "medium_sensitivity"}),
        ("api_key_blocks_content_use", {"scrubbing_mode": "block_content_use", "privacy_sensitivity": "restricted_sensitive"}),
        ("child_data_restricted_sensitive", {"privacy_sensitivity": "restricted_sensitive", "operator_review_required": True}),
        ("health_legal_data_owner_operator_review", {"operator_review_required": True, "owner_review_required": True}),
        ("uploaded_project_file_summary_only_graph_allowed", {"scrubbing_mode": "summary_only", "source_evidence_graph_allowed": True}),
        ("private_evidence_blocks_public_website_claim", {"public_citation_allowed": False, "public_claim_use_allowed": False}),
        ("daemon_receives_access_blocked_compact_verdict", {"daemon_packet_allowed": True, "access_level": "access_blocked"}),
    ],
)
def test_initial_examples_carry_expected_behavior(example_id: str, expect: dict[str, object]) -> None:
    packet = _example(example_id)
    for key, value in expect.items():
        assert packet[key] == value
    assert packet["runtime_authority"] is False
    assert packet["writes_state"] is False
    assert packet["model_provider_used"] is False
    assert packet["public_claim_allowed"] is False
    assert packet["proof_claim_allowed"] is False
    assert packet["learning_claimed"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "public_source_may_be_summarized_and_cited_publicly",
        "owner_private_document_supports_private_answer_not_public_citation",
        "access_restricted_document_blocks_rag_retrieval",
        "email_phone_requires_identifier_redaction",
        "api_key_blocks_content_use",
        "child_data_restricted_sensitive",
        "health_legal_data_owner_operator_review",
        "uploaded_project_file_summary_only_graph_allowed",
        "private_evidence_blocks_public_website_claim",
        "daemon_receives_access_blocked_compact_verdict",
    ],
)
def test_no_initial_example_grants_runtime_authority(example_id: str) -> None:
    assert _example(example_id)["runtime_authority"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "public_source_may_be_summarized_and_cited_publicly",
        "owner_private_document_supports_private_answer_not_public_citation",
        "access_restricted_document_blocks_rag_retrieval",
        "email_phone_requires_identifier_redaction",
        "api_key_blocks_content_use",
        "child_data_restricted_sensitive",
        "health_legal_data_owner_operator_review",
        "uploaded_project_file_summary_only_graph_allowed",
        "private_evidence_blocks_public_website_claim",
        "daemon_receives_access_blocked_compact_verdict",
    ],
)
def test_no_initial_example_writes_state(example_id: str) -> None:
    assert _example(example_id)["writes_state"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "public_source_may_be_summarized_and_cited_publicly",
        "owner_private_document_supports_private_answer_not_public_citation",
        "access_restricted_document_blocks_rag_retrieval",
        "email_phone_requires_identifier_redaction",
        "api_key_blocks_content_use",
        "child_data_restricted_sensitive",
        "health_legal_data_owner_operator_review",
        "uploaded_project_file_summary_only_graph_allowed",
        "private_evidence_blocks_public_website_claim",
        "daemon_receives_access_blocked_compact_verdict",
    ],
)
def test_no_initial_example_calls_model_provider(example_id: str) -> None:
    assert _example(example_id)["model_provider_used"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "public_source_may_be_summarized_and_cited_publicly",
        "owner_private_document_supports_private_answer_not_public_citation",
        "access_restricted_document_blocks_rag_retrieval",
        "email_phone_requires_identifier_redaction",
        "api_key_blocks_content_use",
        "child_data_restricted_sensitive",
        "health_legal_data_owner_operator_review",
        "uploaded_project_file_summary_only_graph_allowed",
        "private_evidence_blocks_public_website_claim",
        "daemon_receives_access_blocked_compact_verdict",
    ],
)
def test_no_initial_example_allows_public_claim_authority(example_id: str) -> None:
    assert _example(example_id)["public_claim_allowed"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "public_source_may_be_summarized_and_cited_publicly",
        "owner_private_document_supports_private_answer_not_public_citation",
        "access_restricted_document_blocks_rag_retrieval",
        "email_phone_requires_identifier_redaction",
        "api_key_blocks_content_use",
        "child_data_restricted_sensitive",
        "health_legal_data_owner_operator_review",
        "uploaded_project_file_summary_only_graph_allowed",
        "private_evidence_blocks_public_website_claim",
        "daemon_receives_access_blocked_compact_verdict",
    ],
)
def test_no_initial_example_allows_proof_claim(example_id: str) -> None:
    assert _example(example_id)["proof_claim_allowed"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "public_source_may_be_summarized_and_cited_publicly",
        "owner_private_document_supports_private_answer_not_public_citation",
        "access_restricted_document_blocks_rag_retrieval",
        "email_phone_requires_identifier_redaction",
        "api_key_blocks_content_use",
        "child_data_restricted_sensitive",
        "health_legal_data_owner_operator_review",
        "uploaded_project_file_summary_only_graph_allowed",
        "private_evidence_blocks_public_website_claim",
        "daemon_receives_access_blocked_compact_verdict",
    ],
)
def test_no_initial_example_claims_learning(example_id: str) -> None:
    assert _example(example_id)["learning_claimed"] is False


@pytest.mark.parametrize("access_level", ["unknown_access_level", "not_a_scope"])
def test_validation_fails_unknown_access_level(access_level: str) -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet["access_level"] = access_level
    with pytest.raises(mod.ValidationError, match="unknown_access_level"):
        mod.validate_document_access_packet_v1(packet)


@pytest.mark.parametrize("privacy", ["mystery_sensitivity", "not_sensitive"])
def test_validation_fails_unknown_privacy_sensitivity(privacy: str) -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet["privacy_sensitivity"] = privacy
    with pytest.raises(mod.ValidationError, match="unknown_privacy_sensitivity"):
        mod.validate_document_access_packet_v1(packet)


@pytest.mark.parametrize("use", ["maybe_use", "may_do_anything"])
def test_validation_fails_unknown_use_permission(use: str) -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet["allowed_uses"] = [use]
    with pytest.raises(mod.ValidationError, match="unknown_use_permission"):
        mod.validate_document_access_packet_v1(packet)


@pytest.mark.parametrize("category", ["mystery_pii", "not_a_category"])
def test_validation_fails_unknown_pii_category(category: str) -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet["detected_pii_categories"] = [category]
    with pytest.raises(mod.ValidationError, match="unknown_pii_category"):
        mod.validate_document_access_packet_v1(packet)


@pytest.mark.parametrize("mode", ["mystery_mode", "scrub_everything"])
def test_validation_fails_unknown_scrubbing_mode(mode: str) -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet["scrubbing_mode"] = mode
    with pytest.raises(mod.ValidationError, match="unknown_scrubbing_mode"):
        mod.validate_document_access_packet_v1(packet)


def test_validation_fails_public_citation_from_private_source() -> None:
    packet = deepcopy(_example("owner_private_document_supports_private_answer_not_public_citation"))
    packet["public_citation_allowed"] = True
    with pytest.raises(mod.ValidationError, match="public_citation_blocked_for_private_source"):
        mod.validate_document_access_packet_v1(packet)


def test_validation_fails_public_claim_use_from_private_evidence() -> None:
    packet = deepcopy(_example("private_evidence_blocks_public_website_claim"))
    packet["public_claim_use_allowed"] = True
    with pytest.raises(mod.ValidationError, match="public_claim_use_blocked_for_private_evidence"):
        mod.validate_document_access_packet_v1(packet)


def test_validation_fails_action_use_allowed() -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet["action_use_allowed"] = True
    with pytest.raises(mod.ValidationError, match="action_use_allowed_true"):
        mod.validate_document_access_packet_v1(packet)


def test_validation_fails_unsafe_vectorization() -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet["vectorization_allowed"] = True
    packet["deletion_required_on_request"] = False
    packet["export_required_on_request"] = False
    with pytest.raises(mod.ValidationError, match="vectorization_.*missing"):
        mod.validate_document_access_packet_v1(packet)


def test_validation_fails_raw_payload_to_daemon() -> None:
    packet = deepcopy(_example("daemon_receives_access_blocked_compact_verdict"))
    packet["raw_content_allowed"] = True
    with pytest.raises(mod.ValidationError, match="daemon_packet_raw_content_blocked|raw_content_blocked_for_sensitive_or_private_data"):
        mod.validate_document_access_packet_v1(packet)


def test_validation_fails_api_key_summarized_instead_of_blocked() -> None:
    packet = deepcopy(_example("api_key_blocks_content_use"))
    packet["scrubbing_mode"] = "summary_only"
    with pytest.raises(mod.ValidationError, match="api_key_or_token_must_block_content_use"):
        mod.validate_document_access_packet_v1(packet)


@pytest.mark.parametrize(
    "example_id,field,value,match",
    [
        ("child_data_restricted_sensitive", "privacy_sensitivity", "medium_sensitivity", "restricted_sensitive_required|child_data_restricted_sensitive_required"),
        ("health_legal_data_owner_operator_review", "operator_review_required", False, "review_required_for_sensitive_data"),
        ("health_legal_data_owner_operator_review", "owner_review_required", False, "review_required_for_sensitive_data"),
    ],
)
def test_validation_fails_child_health_legal_unsafe_handling(example_id: str, field: str, value: object, match: str) -> None:
    packet = deepcopy(_example(example_id))
    packet[field] = value
    with pytest.raises(mod.ValidationError, match=match):
        mod.validate_document_access_packet_v1(packet)


@pytest.mark.parametrize(
    "field",
    ["runtime_authority", "writes_state", "model_provider_used", "public_claim_allowed", "proof_claim_allowed", "learning_claimed"],
)
def test_validation_fails_runtime_authority_flags(field: str) -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet[field] = True
    with pytest.raises(mod.ValidationError):
        mod.validate_document_access_packet_v1(packet)


@pytest.mark.parametrize(
    "field,value",
    [
        ("safe_metadata", {"hidden_prompt": "secret"}),
        ("safe_metadata", {"raw_private": "dump"}),
        ("safe_metadata", {"secret": "x"}),
        ("safe_metadata", {"token": "x"}),
        ("safe_metadata", {"key": "x"}),
    ],
)
def test_validation_fails_hidden_prompt_raw_private_secret_fields(field: str, value: object) -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet[field] = value
    with pytest.raises(mod.ValidationError, match="hidden_prompt_or_raw_private_field"):
        mod.validate_document_access_packet_v1(packet)


@pytest.mark.parametrize(
    "value",
    [
        "GDPR compliant",
        "GDPR certification",
        "security certification",
        "public ready",
        "proof certainty",
        "truth certainty",
    ],
)
def test_validation_fails_gdpr_security_certification_and_truth_claims(value: str) -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet["recommended_next_gate"] = value
    with pytest.raises(mod.ValidationError, match="claim_marker_blocked"):
        mod.validate_document_access_packet_v1(packet)


@pytest.mark.parametrize(
    "value",
    [
        "AGI",
        "consciousness",
        "sentience",
        "Turing",
    ],
)
def test_validation_fails_agi_consciousness_turing_marker(value: str) -> None:
    packet = deepcopy(_example("public_source_may_be_summarized_and_cited_publicly"))
    packet["source_name"] = value
    with pytest.raises(mod.ValidationError, match="claim_marker_blocked"):
        mod.validate_document_access_packet_v1(packet)
