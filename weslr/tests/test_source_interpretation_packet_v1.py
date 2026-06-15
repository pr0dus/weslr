from __future__ import annotations

import json
from copy import deepcopy

import weslr.source_interpretation_packet as sip
from weslr.source_interpretation_packet import (
    build_initial_source_interpretation_examples_v1,
    build_source_interpretation_packet_v1,
    render_source_interpretation_packet_markdown_v1,
    summarize_source_interpretation_packet_v1,
    to_source_interpretation_packet_json_safe_v1,
    validate_source_interpretation_packet_v1,
)


def test_public_apis_exist():
    for name in (
        "build_source_interpretation_packet_v1",
        "validate_source_interpretation_packet_v1",
        "summarize_source_interpretation_packet_v1",
        "render_source_interpretation_packet_markdown_v1",
        "to_source_interpretation_packet_json_safe_v1",
        "build_initial_source_interpretation_examples_v1",
    ):
        assert hasattr(sip, name)
        assert callable(getattr(sip, name))


def _base_packet() -> dict:
    return build_source_interpretation_packet_v1(
        interpretation_packet_id="base_interpretation_packet",
        ingestion_request_id="base_ingestion_request",
        authorization_packet_ref="authorization_packet_v1:base_ingestion_request",
        source_ref="https://example.org/base",
        source_class="public_research_paper",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        retention_mode="metadata_only_no_content_retention",
        source_metadata={
            "title": "Base source",
            "authors_or_organization": "Example Org",
            "publication_or_source_date": "2026-01-01",
            "source_host_or_domain": "example.org",
            "citation_or_provenance_ref": "Example Org 2026",
        },
        bounded_content_policy={
            "raw_content_allowed": False,
            "safe_paraphrase_allowed": True,
            "bounded_excerpt_allowed": False,
            "max_excerpt_chars": 0,
            "max_excerpt_count": 0,
            "citation_required": True,
            "source_location_ref_required": True,
            "raw_retention_allowed": False,
            "owner_authorization_required_for_raw_retention": False,
        },
        extracted_claims=[
            {
                "claim_id": "c1",
                "claim_text_or_safe_paraphrase": "Review-bound paraphrase only.",
                "claim_type": "result",
                "source_location_ref": "section 1",
                "evidence_role_candidate": "primary_evidence_candidate",
                "confidence_posture": "interpretation_medium",
                "required_review": "operator_review",
                "blocked_claims": ["no evidence promotion"],
                "disconfirmation_need": "A stronger counterexample.",
            }
        ],
        extracted_assumptions=[
            {
                "id": "a1",
                "statement": "The packet is review-bound.",
                "category": "boundary",
                "why_it_matters": "prevents overclaim",
                "what_would_break_it": "accepted-evidence lane",
                "review_required": "operator_review",
                "related_claim_ids": ["c1"],
            }
        ],
        method_limits=[
            {
                "id": "m1",
                "statement": "Metadata-only interpretation does not prove the claim.",
                "category": "retention",
                "why_it_matters": "truth boundary",
                "what_would_break_it": "new evidence lane",
                "review_required": "operator_review",
                "related_claim_ids": ["c1"],
            }
        ],
        evidence_role_candidates=[{"evidence_role_candidate": "primary_evidence_candidate"}],
        counterevidence_or_disconfirmation=[{"hint": "Need replication or contradiction."}],
        source_conflicts=[{"conflict_status": "no_known_conflict", "summary": "No known conflict."}],
        missing_evidence=[{"hint": "Need stronger corroboration."}],
        pattern_attribution_candidates=[
            {
                "source_pattern_id": "base_pattern",
                "target_domain_or_experiment": "analysis",
                "shared_structure": "bounded result",
                "key_differences": "No acceptance implied.",
                "possible_mechanism_overlap_posture": "possible overlap only",
                "disconfirmation_tests": ["replication failure"],
                "analogy_strength": "interpretation_medium",
                "blocked_claims": ["mechanistic overclaim"],
                "next_safe_step": "operator review",
            }
        ],
        artifact_route_candidates=[{"route": "artifact_forward_work_plan", "summary": "Later planning only."}],
        mlcf_normalization_hints=[{"hint": "source class", "value": "public_research_paper"}],
        oer_or_noop_hints=[{"hint": "route_to_operator_review"}],
        candidate_preparation_eligibility="candidate_preparation_premature",
        review_requirements={
            "owner_authorization_required": False,
            "owner_authorization_present": False,
            "operator_review_required": True,
            "expert_review_required": False,
            "required_review_labels": ["operator_review"],
        },
        blocked_claims=["no evidence promotion"],
        denied_authority_flags={flag: False for flag in sip._DENIED_AUTHORITY_FLAGS_V1},
        abort_conditions=["evidence promotion blocked"],
        blocked_labels=["review_bound"],
        safe_metadata_summary="base packet",
        next_safe_step="operator_review",
        final_judgment="interpretation_packet_pending_review",
    )


def test_valid_base_packet():
    packet = _base_packet()
    result = validate_source_interpretation_packet_v1(packet)
    assert result["valid"] is True
    assert result["blocked"] is False


def test_valid_public_research_paper_interpretation_example():
    examples = build_initial_source_interpretation_examples_v1()
    packet = examples[0]
    assert packet["interpretation_packet_id"] == "public_research_paper_interpretation_candidate"
    assert validate_source_interpretation_packet_v1(packet)["valid"] is True


def test_valid_official_standard_context_interpretation_example():
    packet = build_initial_source_interpretation_examples_v1()[1]
    assert validate_source_interpretation_packet_v1(packet)["valid"] is True
    assert packet["source_class"] == "official_standard"


def test_valid_github_implementation_reference_interpretation_example():
    packet = build_initial_source_interpretation_examples_v1()[2]
    assert validate_source_interpretation_packet_v1(packet)["valid"] is True
    assert packet["evidence_role_candidates"][0]["evidence_role_candidate"] == "implementation_reference"


def test_valid_false_assumption_disconfirmation_mapping_example():
    packet = build_initial_source_interpretation_examples_v1()[3]
    assert validate_source_interpretation_packet_v1(packet)["valid"] is True
    assert packet["candidate_preparation_eligibility"] == "candidate_preparation_possible_after_review"


def test_valid_pulsar_known_science_replay_reference_example():
    packet = build_initial_source_interpretation_examples_v1()[4]
    assert validate_source_interpretation_packet_v1(packet)["valid"] is True
    assert any(c["evidence_role_candidate"] == "known_science_replay_reference" for c in packet["evidence_role_candidates"])


def test_valid_owner_uploaded_pdf_no_raw_retention_example():
    packet = build_initial_source_interpretation_examples_v1()[5]
    assert validate_source_interpretation_packet_v1(packet)["valid"] is True
    assert packet["bounded_content_policy"]["raw_content_allowed"] is False


def test_valid_weak_source_not_evidence_example():
    packet = build_initial_source_interpretation_examples_v1()[8]
    assert validate_source_interpretation_packet_v1(packet)["valid"] is True
    roles = {item["evidence_role_candidate"] for item in packet["evidence_role_candidates"]}
    assert "weak_signal_only" in roles
    assert "not_evidence" in roles


def test_required_fields_validation():
    packet = _base_packet()
    del packet["final_judgment"]
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert any(label == "missing_field:final_judgment" for label in result["blocked_labels"])


def test_missing_authorization_reference_rejected():
    packet = _base_packet()
    packet["authorization_packet_ref"] = ""
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "missing_authorization_reference" in result["blocked_labels"]


def test_missing_source_ref_rejected():
    packet = _base_packet()
    packet["source_ref"] = ""
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "missing_source_ref" in result["blocked_labels"]


def test_missing_provenance_citation_minimum_rejected():
    packet = _base_packet()
    packet["source_metadata"] = {
        "title": "Base source",
        "authors_or_organization": "Example Org",
        "publication_or_source_date": "2026-01-01",
        "source_host_or_domain": "example.org",
    }
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "provenance_citation_minimum_missing" in result["blocked_labels"]


def test_invalid_and_blocked_source_classes_rejected():
    packet = _base_packet()
    packet["source_class"] = "not_a_real_class"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "invalid_source_class" in result["blocked_labels"]

    packet = _base_packet()
    packet["source_class"] = "blocked_source_class"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "blocked_source_class_rejected" in result["blocked_labels"]


def test_invalid_retention_mode_rejected():
    packet = _base_packet()
    packet["retention_mode"] = "invalid_retention"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "invalid_retention_mode" in result["blocked_labels"]


def test_blocked_retention_rejected():
    packet = _base_packet()
    packet["retention_mode"] = "blocked_retention"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "blocked_retention_not_allowed" in result["blocked_labels"]


def test_raw_content_without_authorization_rejected():
    packet = _base_packet()
    packet["source_metadata"]["raw_content"] = "raw content"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "raw_content_present" in result["blocked_labels"]


def test_bounded_excerpt_without_citation_or_source_location_rejected():
    packet = _base_packet()
    packet["retention_mode"] = "bounded_excerpt_with_citation"
    packet["bounded_content_policy"] = {
        "raw_content_allowed": False,
        "safe_paraphrase_allowed": True,
        "bounded_excerpt_allowed": True,
        "max_excerpt_chars": 0,
        "max_excerpt_count": 0,
        "citation_required": False,
        "source_location_ref_required": False,
        "raw_retention_allowed": False,
        "owner_authorization_required_for_raw_retention": False,
    }
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "bounded_excerpt_policy_incomplete" in result["blocked_labels"]


def test_metadata_only_mode_with_excerpts_rejected():
    packet = _base_packet()
    packet["bounded_content_policy"]["bounded_excerpt_allowed"] = True
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "metadata_only_excerpts_not_allowed" in result["blocked_labels"]


def test_hidden_prompts_and_secrets_rejected():
    packet = _base_packet()
    packet["safe_metadata_summary"] = "hidden prompt with secret token"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "sensitive_content_wording_present" in result["blocked_labels"]


def test_private_data_without_authorization_rejected():
    packet = _base_packet()
    packet["source_metadata"]["notes"] = "private memory"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "sensitive_content_wording_present" in result["blocked_labels"]


def test_accepted_evidence_candidate_and_final_answer_wording_rejected():
    packet = _base_packet()
    packet["extracted_claims"][0]["claim_text_or_safe_paraphrase"] = "accepted evidence and final answer"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "forbidden_claim_wording_present" in result["blocked_labels"] or "claim_marked_as_truth_or_acceptance" in result["blocked_labels"]


def test_proof_discovery_public_science_product_readiness_rejected():
    packet = _base_packet()
    packet["extracted_claims"][0]["claim_text_or_safe_paraphrase"] = "proof discovery public science product ready"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "forbidden_claim_wording_present" in result["blocked_labels"]


def test_same_mechanism_attribution_without_review_rejected():
    packet = _base_packet()
    packet["review_requirements"]["expert_review_required"] = False
    packet["pattern_attribution_candidates"][0]["possible_mechanism_overlap_posture"] = "same mechanism"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "same_mechanism_claim_blocked" in result["blocked_labels"]


def test_true_denied_authority_flag_rejected():
    packet = _base_packet()
    packet["denied_authority_flags"]["final_answer_authority"] = True
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert any(label == "denied_authority_true:final_answer_authority" for label in result["blocked_labels"])


def test_empty_blocked_claims_rejected():
    packet = _base_packet()
    packet["blocked_claims"] = []
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "blocked_claims_empty" in result["blocked_labels"]


def test_empty_abort_conditions_rejected():
    packet = _base_packet()
    packet["abort_conditions"] = []
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "abort_conditions_empty" in result["blocked_labels"]


def test_missing_review_requirements_rejected():
    packet = _base_packet()
    packet["review_requirements"] = {}
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "missing_review_requirements" in result["blocked_labels"]


def test_candidate_prep_route_without_review_or_evidence_normalization_rejected():
    packet = _base_packet()
    packet["candidate_preparation_eligibility"] = "candidate_preparation_possible_after_evidence_normalization"
    packet["review_requirements"]["operator_review_required"] = False
    packet["evidence_role_candidates"] = [{"evidence_role_candidate": "not_evidence"}]
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert any(label in result["blocked_labels"] for label in ("operator_review_required_for_candidate_prep", "candidate_prep_requires_candidate_role"))


def test_normalized_evidence_route_without_provenance_operator_review_or_candidate_role_rejected():
    packet = _base_packet()
    packet["artifact_route_candidates"] = [{"route": "normalized_evidence_packet"}]
    packet["review_requirements"]["operator_review_required"] = False
    packet["source_metadata"]["citation_or_provenance_ref"] = ""
    packet["evidence_role_candidates"] = [{"evidence_role_candidate": "not_evidence"}]
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert any(
        label in result["blocked_labels"]
        for label in (
            "normalized_evidence_requires_operator_review",
            "normalized_evidence_requires_provenance",
            "normalized_evidence_requires_candidate_role",
        )
    )


def test_expert_review_conflict_without_expert_review_rejected():
    packet = _base_packet()
    packet["source_conflicts"] = [{"conflict_status": "conflict_requiring_expert_review", "summary": "Needs expert review."}]
    packet["review_requirements"]["expert_review_required"] = False
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert any(label in result["blocked_labels"] for label in ("expert_review_required_for_conflict", "expert_review_required_for_conflict_escalation"))


def test_source_fetch_ingestion_authority_rejected():
    packet = _base_packet()
    packet["safe_metadata_summary"] = "source fetch authority"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "forbidden_claim_wording_present" in result["blocked_labels"]


def test_provider_model_runtime_authority_rejected():
    packet = _base_packet()
    packet["safe_metadata_summary"] = "provider call runtime enabled"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "forbidden_claim_wording_present" in result["blocked_labels"]


def test_ontology_auto_application_self_modification_rejected():
    packet = _base_packet()
    packet["safe_metadata_summary"] = "ontology applied automatically with self-modification"
    result = validate_source_interpretation_packet_v1(packet)
    assert result["blocked"] is True
    assert "forbidden_claim_wording_present" in result["blocked_labels"]


def test_markdown_renderer_safe_and_complete():
    md = render_source_interpretation_packet_markdown_v1(_base_packet())
    assert "Source interpretation packet" in md
    assert "Authorization posture" in md
    assert "Source metadata" in md
    assert "Bounded content policy" in md
    assert "Extracted claim candidates" in md
    assert "Assumptions" in md
    assert "Method limits" in md
    assert "Disconfirmation / counterevidence" in md
    assert "Conflicts" in md
    assert "Pattern attribution candidates" in md
    assert "Artifact route candidates" in md
    assert "Denied authority summary" in md


def test_markdown_renderer_excludes_raw_full_text_and_final_answer_implications():
    md = render_source_interpretation_packet_markdown_v1(_base_packet()).lower()
    assert "raw full text" not in md
    assert "final answer" not in md or "final judgment" in md
    assert "accepted evidence" not in md


def test_json_safe_copy_deterministic_and_non_mutating():
    packet = _base_packet()
    original = deepcopy(packet)
    first = to_source_interpretation_packet_json_safe_v1(packet)
    second = to_source_interpretation_packet_json_safe_v1(packet)
    assert first == second
    assert packet == original
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_summary_compact_and_safe():
    summary = summarize_source_interpretation_packet_v1(_base_packet())
    assert summary["interpretation_packet_id"] == "base_interpretation_packet"
    assert summary["ingestion_request_id"] == "base_ingestion_request"
    assert summary["authorization_packet_ref"] == "authorization_packet_v1:base_ingestion_request"
    assert summary["source_class"] == "public_research_paper"
    assert summary["retention_mode"] == "metadata_only_no_content_retention"
    assert summary["blocked"] is False


def test_examples_validate_except_intentionally_unsafe_examples():
    examples = build_initial_source_interpretation_examples_v1()
    for index in range(6):
        assert validate_source_interpretation_packet_v1(examples[index])["valid"] is True
    assert validate_source_interpretation_packet_v1(examples[6])["valid"] is False
    assert validate_source_interpretation_packet_v1(examples[7])["valid"] is False
    assert validate_source_interpretation_packet_v1(examples[8])["valid"] is True
