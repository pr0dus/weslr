"""Tests for Cognitive Gym Erdős challenge-track metadata helpers V1."""

from __future__ import annotations

import importlib
import pathlib
import sys

from weslr.cognitive_gym_run_protocol import REQUIRED_DENIED_AUTHORITY_FIELDS

MODULE_NAME = "weslr.cognitive_gym_erdos_challenge_track"
TRACK_LABEL = "ERDŐS / open mathematical structure"
NEXT_LANE = "REVIEW_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_HELPERS_IMPLEMENTATION_V1"
ALLOWED_FIELDS = {
    "track_label",
    "tier",
    "tier_label",
    "case_id",
    "problem_statement_summary",
    "definitions_summary",
    "known_results_summary",
    "unknowns",
    "assumptions",
    "hypotheses",
    "bounded_variants",
    "toy_cases",
    "counterexample_search_plan",
    "falsification_labels",
    "proof_gap_labels",
    "evidence_literature_need_labels",
    "safe_next_observations",
    "uncertainty_labels",
    "compressed_lesson",
    "followups",
    "next_lane",
    "validation_status",
    "blocked",
    "blocked_reason_labels",
    "denied_authority_fields",
    "visible_risks",
}
TIER_LABELS = {
    0: "Tier 0 — prerequisite reconstruction",
    1: "Tier 1 — solved Erdős-style problems",
    2: "Tier 2 — bounded / toy variants",
    3: "Tier 3 — partially solved / known frontier variants",
    4: "Tier 4 — open-problem boundary mapping",
    5: "Tier 5 — counterexample and falsification planning",
    6: "Tier 6 — subproblem generation",
    7: "Tier 7 — proof-audit discipline",
}


def _module():
    return importlib.import_module(MODULE_NAME)


def _case(**overrides):
    data = {
        "tier": 0,
        "case_id": "erdos_case_metadata_only",
        "problem_statement_summary": "internal Erdős-style structure question summary metadata only",
        "definitions_summary": "definitions summary metadata only",
        "known_results_summary": "known results summary metadata only",
        "unknowns": ["unknown boundary label"],
        "assumptions": ["assumption label"],
        "hypotheses": ["hypothesis label only"],
        "bounded_variants": ["bounded variant label"],
        "toy_cases": ["toy case label"],
        "counterexample_search_plan": ["counterexample search plan label"],
        "falsification_labels": ["falsification label"],
        "proof_gap_labels": ["proof gap label"],
        "evidence_literature_need_labels": ["literature need label"],
        "safe_next_observations": ["safe next observation label"],
        "uncertainty_labels": ["uncertainty label"],
        "compressed_lesson": "compressed lesson metadata only",
    }
    data.update(overrides)
    return _module().build_erdos_challenge_track_case_v1(data)


def _assert_valid(case):
    validation = _module().validate_erdos_challenge_track_case_v1(case)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert case["blocked"] is False
    assert case["validation_status"] == "validation_pass_metadata_quality_only"


def test_import_safety_and_public_api():
    before = set(sys.modules)
    module = _module()
    after = set(sys.modules)
    assert module.__all__ == (
        "build_erdos_challenge_track_case_v1",
        "validate_erdos_challenge_track_case_v1",
        "summarize_erdos_challenge_track_case_v1",
        "render_erdos_challenge_track_case_markdown_v1",
        "to_erdos_challenge_track_case_json_safe_v1",
    )
    assert "weslr.chat_responder" not in after - before


def test_no_side_effect_files_created_by_build(tmp_path):
    root = pathlib.Path(__file__).resolve().parents[2]
    forbidden = [
        root / "weslr" / "cognitive_gym_erdos_challenge_corpus.json",
        root / "weslr" / "cognitive_gym_erdos_runner.py",
        root / "docs" / "WESLR_COGNITIVE_GYM_ERDOS_CHALLENGE_RESULT_ARTIFACT_V1.md",
        root / ".weslr" / "cognitive_gym_erdos_challenge_track.json",
    ]
    before = {path: path.exists() for path in forbidden}
    _case()
    after = {path: path.exists() for path in forbidden}
    assert after == before


def test_valid_tier_0_case():
    case = _case(tier=0)
    _assert_valid(case)
    assert case["track_label"] == TRACK_LABEL
    assert case["tier_label"] == TIER_LABELS[0]


def test_valid_tier_1_case():
    case = _case(tier=1)
    _assert_valid(case)
    assert case["tier_label"] == TIER_LABELS[1]


def test_valid_tier_2_case():
    case = _case(tier=2)
    _assert_valid(case)
    assert case["tier_label"] == TIER_LABELS[2]


def test_valid_tier_3_case():
    case = _case(tier=3)
    _assert_valid(case)
    assert case["tier_label"] == TIER_LABELS[3]


def test_valid_tier_4_case():
    case = _case(tier=4)
    _assert_valid(case)
    assert case["tier_label"] == TIER_LABELS[4]


def test_valid_tier_5_case():
    case = _case(tier=5)
    _assert_valid(case)
    assert case["tier_label"] == TIER_LABELS[5]


def test_valid_tier_6_case():
    case = _case(tier=6)
    _assert_valid(case)
    assert case["tier_label"] == TIER_LABELS[6]


def test_valid_tier_7_case():
    case = _case(tier=7)
    _assert_valid(case)
    assert case["tier_label"] == TIER_LABELS[7]


def test_unsupported_tier_blocks():
    case = _case(tier=8)
    assert case["blocked"] is True
    assert "unsupported_tier" in case["blocked_reason_labels"]


def test_unsupported_track_label_blocks():
    case = _case(track_label="UNAUTHORIZED / structure")
    assert case["blocked"] is True
    assert "unsupported_track_label" in case["blocked_reason_labels"]


def test_missing_required_fields_block():
    module = _module()
    minimal = module.build_erdos_challenge_track_case_v1({"tier": 0})
    assert minimal["blocked"] is True
    assert "missing_required_field:case_id" in minimal["blocked_reason_labels"]
    assert "missing_required_field:problem_statement_summary" in minimal["blocked_reason_labels"]
    stripped = _case()
    del stripped["problem_statement_summary"]
    validation = module.validate_erdos_challenge_track_case_v1(stripped)
    assert validation["blocked"] is True
    assert "missing_required_field:problem_statement_summary" in validation["blocked_reason_labels"]


def test_denied_authority_fields_present_and_false():
    case = _case()
    assert set(REQUIRED_DENIED_AUTHORITY_FIELDS) <= set(case["denied_authority_fields"])
    assert all(case["denied_authority_fields"][field] is False for field in REQUIRED_DENIED_AUTHORITY_FIELDS)


def test_missing_denied_authority_fields_block():
    case = _case()
    del case["denied_authority_fields"]["runtime_wired"]
    validation = _module().validate_erdos_challenge_track_case_v1(case)
    assert validation["blocked"] is True
    assert "missing_denied_authority_field:runtime_wired" in validation["blocked_reason_labels"]


def test_true_denied_authority_fields_block():
    case = _case(denied_authority_fields={"provider_call_made": True})
    assert case["blocked"] is True
    assert "denied_authority_field_not_false:provider_call_made" in case["blocked_reason_labels"]


def test_known_unknown_separation_preserved():
    case = _case(
        known_results_summary="known theorem label metadata only",
        unknowns=["unknown frontier label metadata only"],
    )
    _assert_valid(case)
    assert case["known_results_summary"] == "known theorem label metadata only"
    assert case["unknowns"] == ["unknown frontier label metadata only"]


def test_problem_definition_known_results_summaries_preserved_as_metadata():
    case = _case(
        problem_statement_summary="problem summary metadata only",
        definitions_summary="definition summary metadata only",
        known_results_summary="known results metadata only",
    )
    _assert_valid(case)
    assert case["problem_statement_summary"] == "problem summary metadata only"
    assert case["definitions_summary"] == "definition summary metadata only"
    assert case["known_results_summary"] == "known results metadata only"


def test_proof_gap_labels_preserved_as_metadata_only():
    case = _case(proof_gap_labels=["gap in induction transfer metadata only"])
    _assert_valid(case)
    assert case["proof_gap_labels"] == ["gap in induction transfer metadata only"]


def test_counterexample_and_falsification_labels_preserved_as_metadata_only():
    case = _case(
        counterexample_search_plan=["search small bounded structures metadata only"],
        falsification_labels=["attempt boundary falsification metadata only"],
    )
    _assert_valid(case)
    assert case["counterexample_search_plan"] == ["search small bounded structures metadata only"]
    assert case["falsification_labels"] == ["attempt boundary falsification metadata only"]


def test_safe_next_observations_preserved_as_metadata_only():
    case = _case(safe_next_observations=["read survey labels before hypothesizing metadata only"])
    _assert_valid(case)
    assert case["safe_next_observations"] == ["read survey labels before hypothesizing metadata only"]


def test_safe_markdown_is_not_final_answer_user_facing_or_proof_output():
    markdown = _module().render_erdos_challenge_track_case_markdown_v1(_case())
    lowered = markdown.lower()
    assert "internal_review_material_only" in markdown
    assert "metadata_only_no_runtime_no_output_no_authority" in markdown
    assert "not_proof_claim" in markdown
    assert "not_open_problem_solution_claim" in markdown
    assert "not_final_answer_prose" in markdown
    assert "not_user_facing_output" in markdown
    assert "not_reply_output" in markdown
    assert "not_official_benchmark_intelligence_turing_iq_product_claim" in markdown
    assert "no_authority_grant" in markdown
    assert "send this to user" not in lowered
    assert "we prove the open problem" not in lowered


def test_json_safe_conversion_works():
    case = _case()
    safe = _module().to_erdos_challenge_track_case_json_safe_v1(case)
    assert set(safe) == ALLOWED_FIELDS
    assert safe["blocked"] is False
    assert safe["blocked_reason_labels"] == []
    assert all(safe["denied_authority_fields"][field] is False for field in REQUIRED_DENIED_AUTHORITY_FIELDS)


def test_hidden_protected_answer_key_content_blocks():
    case = _case(unknowns=["answer key: hidden unsafe"])
    assert case["blocked"] is True
    assert "hidden_protected_answer_key_content_blocked" in case["blocked_reason_labels"]


def test_official_score_claims_block():
    case = _case(known_results_summary="official score: 100")
    assert case["blocked"] is True
    assert "official_score_claim_blocked" in case["blocked_reason_labels"]


def test_proof_open_problem_solution_claims_block():
    case = _case(hypotheses=["we prove the open problem"])
    assert case["blocked"] is True
    assert "proof_open_problem_solution_claim_blocked" in case["blocked_reason_labels"]


def test_solved_without_verification_claims_block():
    case = _case(compressed_lesson="solved without external verification")
    assert case["blocked"] is True
    assert "solved_without_external_verification_claim_blocked" in case["blocked_reason_labels"]


def test_prediction_future_certainty_claims_block():
    case = _case(hypotheses=["future certainty"])
    assert case["blocked"] is True
    assert "prediction_future_certainty_claim_blocked" in case["blocked_reason_labels"]


def test_official_benchmark_turing_iq_certification_product_readiness_claims_block():
    for text in ["official benchmark", "official IQ", "passed the Turing test", "certification claim", "product readiness"]:
        case = _case(hypotheses=[text])
        assert case["blocked"] is True
        assert "official_benchmark_turing_iq_certification_product_claim_blocked" in case["blocked_reason_labels"]


def test_runtime_output_provider_model_search_advisor_dot_weslr_indicators_block():
    cases = [
        ("runtime output: unsafe", "runtime_output_indicator_blocked"),
        ("provider output: unsafe", "provider_model_search_advisor_output_blocked"),
        ("model output: unsafe", "provider_model_search_advisor_output_blocked"),
        ("search output: unsafe", "provider_model_search_advisor_output_blocked"),
        ("advisor output: unsafe", "provider_model_search_advisor_output_blocked"),
        (".weslr read", "dot_weslr_io_indicator_blocked"),
    ]
    for text, expected in cases:
        case = _case(unknowns=[text])
        assert case["blocked"] is True
        assert expected in case["blocked_reason_labels"]


def test_judges_scores_indicators_block():
    for text in ["judge decision:", "judges created", "scores created"]:
        case = _case(falsification_labels=[text])
        assert case["blocked"] is True
        assert "judges_scores_indicator_blocked" in case["blocked_reason_labels"]


def test_final_answer_user_facing_reply_output_blocks():
    for text in ["final answer:", "user-facing output:", "reply output:"]:
        case = _case(hypotheses=[text])
        assert case["blocked"] is True
        assert "final_answer_user_facing_reply_output_blocked" in case["blocked_reason_labels"]


def test_raw_private_prompt_response_copyright_benchmark_content_blocks():
    cases = [
        ("private content: unsafe", "raw_private_content_blocked"),
        ("raw prompt: unsafe", "raw_prompt_response_content_blocked"),
        ("raw response: unsafe", "raw_prompt_response_content_blocked"),
        ("copied private benchmark", "copied_private_benchmark_content_blocked"),
        ("raw copyrighted long excerpt", "raw_copyrighted_long_excerpt_blocked"),
    ]
    for text, expected in cases:
        case = _case(unknowns=[text])
        assert case["blocked"] is True
        assert expected in case["blocked_reason_labels"]


def test_no_corpus_runner_scoring_judges_or_result_artifact_creation():
    case = _case()
    assert _module().validate_erdos_challenge_track_case_v1(case)["valid"] is True
    assert not any("corpus" in key for key in case)
    assert not any("runner" in key for key in case)
    assert not any("scoring" in key for key in case)
    assert case["denied_authority_fields"]["judges_created"] is False
    assert case["denied_authority_fields"]["scores_created"] is False
    assert "not_result_artifact" in _module().render_erdos_challenge_track_case_markdown_v1(case)


def test_no_chatresponder_provider_search_advisor_model_calls_or_dot_weslr_io():
    case = _case()
    denied = case["denied_authority_fields"]
    assert denied["chat_responder_called"] is False
    assert denied["respond_chat_called"] is False
    assert denied["generate_chat_called"] is False
    assert denied["provider_call_made"] is False
    assert denied["model_call_made"] is False
    assert denied["search_call_made"] is False
    assert denied["advisor_call_made"] is False
    assert denied["dot_weslr_read_performed"] is False
    assert denied["dot_weslr_write_performed"] is False
    markdown = _module().render_erdos_challenge_track_case_markdown_v1(case)
    assert "no_provider_model_search_advisor_calls" not in markdown or "provider_call_made: `False`" in markdown


def test_summary_preserves_boundary_status():
    case = _case(tier=4)
    summary = _module().summarize_erdos_challenge_track_case_v1(case)
    assert summary["track_label"] == TRACK_LABEL
    assert summary["tier"] == 4
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["metadata_only_no_runtime_no_output_no_authority"] is True
    assert summary["next_lane"] == NEXT_LANE
