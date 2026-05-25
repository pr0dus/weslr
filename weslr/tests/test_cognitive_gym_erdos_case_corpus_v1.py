"""Tests for Cognitive Gym Erdős case-corpus metadata helpers V1."""

from __future__ import annotations

import importlib
import pathlib
import sys

from weslr.cognitive_gym_run_protocol import REQUIRED_DENIED_AUTHORITY_FIELDS

MODULE_NAME = "weslr.cognitive_gym_erdos_case_corpus"
TRACK_LABEL = "ERDŐS / open mathematical structure"
NEXT_LANE = "REVIEW_COGNITIVE_GYM_ERDOS_CASE_CORPUS_HELPERS_IMPLEMENTATION_V1"
ALLOWED_FIELDS = {
    "corpus_schema_version",
    "case_id",
    "track_label",
    "tier",
    "tier_label",
    "case_kind",
    "source_safety_label",
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
    "denied_authority_fields",
    "validation_status",
    "blocked",
    "blocked_reason_labels",
    "visible_risks",
    "followups",
    "next_lane",
}
TIER_LABELS = {
    0: "Tier 0 — prerequisite reconstruction",
    1: "Tier 1 — solved Erdős-style examples",
    2: "Tier 2 — bounded/toy variants",
    3: "Tier 3 — partially solved or known frontier variants as metadata only",
    4: "Tier 4 — open-problem boundary maps",
    5: "Tier 5 — counterexample/falsification planning",
    6: "Tier 6 — subproblem generation",
    7: "Tier 7 — proof-audit discipline",
}


def _module():
    return importlib.import_module(MODULE_NAME)


def _entry(**overrides):
    data = {
        "tier": 0,
        "case_id": "erdos_case_corpus_entry_metadata_only",
        "case_kind": "case_metadata_only",
        "source_safety_label": "safe_synthetic_or_public_domain_summary_metadata_only",
        "problem_statement_summary": "internal Erdős-style structure question summary metadata only",
        "definitions_summary": "definitions summary metadata only",
        "known_results_summary": "known results summary metadata only",
        "unknowns": ["unknown boundary label metadata only"],
        "assumptions": ["assumption label metadata only"],
        "hypotheses": ["hypothesis label metadata only"],
        "bounded_variants": ["bounded variant label metadata only"],
        "toy_cases": ["toy case label metadata only"],
        "counterexample_search_plan": ["counterexample search plan label metadata only"],
        "falsification_labels": ["falsification label metadata only"],
        "proof_gap_labels": ["proof gap label metadata only"],
        "evidence_literature_need_labels": ["literature need label metadata only"],
        "safe_next_observations": ["safe next observation label metadata only"],
        "uncertainty_labels": ["uncertainty label metadata only"],
        "compressed_lesson": "compressed lesson metadata only",
    }
    data.update(overrides)
    return _module().build_erdos_case_corpus_entry_v1(data)


def _assert_valid(entry):
    validation = _module().validate_erdos_case_corpus_entry_v1(entry)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert entry["blocked"] is False
    assert entry["validation_status"] == "validation_pass_metadata_quality_only"


def test_import_safety_and_public_api():
    before = set(sys.modules)
    module = _module()
    after = set(sys.modules)
    assert module.__all__ == (
        "build_erdos_case_corpus_entry_v1",
        "validate_erdos_case_corpus_entry_v1",
        "summarize_erdos_case_corpus_entry_v1",
        "render_erdos_case_corpus_entry_markdown_v1",
        "to_erdos_case_corpus_entry_json_safe_v1",
    )
    assert "weslr.chat_responder" not in after - before


def test_no_side_effect_files_created_by_build():
    root = pathlib.Path(__file__).resolve().parents[2]
    forbidden = [
        root / "weslr" / "cognitive_gym_erdos_case_corpus.json",
        root / "weslr" / "cognitive_gym_erdos_case_corpus.yaml",
        root / "weslr" / "cognitive_gym_erdos_case_corpus_data.py",
        root / "weslr" / "cognitive_gym_erdos_case_runner.py",
        root / "docs" / "WESLR_COGNITIVE_GYM_ERDOS_CASE_CORPUS_RESULT_ARTIFACT_V1.md",
        root / ".weslr" / "cognitive_gym_erdos_case_corpus.json",
    ]
    before = {path: path.exists() for path in forbidden}
    _entry()
    after = {path: path.exists() for path in forbidden}
    assert after == before


def test_valid_tier_0_entry():
    entry = _entry(tier=0)
    _assert_valid(entry)
    assert entry["track_label"] == TRACK_LABEL
    assert entry["tier_label"] == TIER_LABELS[0]


def test_valid_tier_1_entry():
    entry = _entry(tier=1)
    _assert_valid(entry)
    assert entry["tier_label"] == TIER_LABELS[1]


def test_valid_tier_2_entry():
    entry = _entry(tier=2)
    _assert_valid(entry)
    assert entry["tier_label"] == TIER_LABELS[2]


def test_valid_tier_3_entry():
    entry = _entry(tier=3)
    _assert_valid(entry)
    assert entry["tier_label"] == TIER_LABELS[3]


def test_valid_tier_4_entry():
    entry = _entry(tier=4)
    _assert_valid(entry)
    assert entry["tier_label"] == TIER_LABELS[4]


def test_valid_tier_5_entry():
    entry = _entry(tier=5)
    _assert_valid(entry)
    assert entry["tier_label"] == TIER_LABELS[5]


def test_valid_tier_6_entry():
    entry = _entry(tier=6)
    _assert_valid(entry)
    assert entry["tier_label"] == TIER_LABELS[6]


def test_valid_tier_7_entry():
    entry = _entry(tier=7)
    _assert_valid(entry)
    assert entry["tier_label"] == TIER_LABELS[7]


def test_unsupported_tier_blocks():
    entry = _entry(tier=8)
    assert entry["blocked"] is True
    assert "unsupported_tier" in entry["blocked_reason_labels"]


def test_unsupported_track_label_blocks():
    entry = _entry(track_label="UNAUTHORIZED / structure")
    assert entry["blocked"] is True
    assert "unsupported_track_label" in entry["blocked_reason_labels"]


def test_missing_required_fields_block():
    module = _module()
    minimal = module.build_erdos_case_corpus_entry_v1({"tier": 0})
    assert minimal["blocked"] is True
    assert "missing_required_field:case_id" in minimal["blocked_reason_labels"]
    assert "missing_required_field:problem_statement_summary" in minimal["blocked_reason_labels"]
    stripped = _entry()
    del stripped["problem_statement_summary"]
    validation = module.validate_erdos_case_corpus_entry_v1(stripped)
    assert validation["blocked"] is True
    assert "missing_required_field:problem_statement_summary" in validation["blocked_reason_labels"]


def test_denied_authority_fields_present_and_false():
    entry = _entry()
    assert set(REQUIRED_DENIED_AUTHORITY_FIELDS) <= set(entry["denied_authority_fields"])
    assert all(entry["denied_authority_fields"][field] is False for field in REQUIRED_DENIED_AUTHORITY_FIELDS)


def test_missing_denied_authority_fields_block():
    entry = _entry()
    del entry["denied_authority_fields"]["runtime_wired"]
    validation = _module().validate_erdos_case_corpus_entry_v1(entry)
    assert validation["blocked"] is True
    assert "missing_denied_authority_field:runtime_wired" in validation["blocked_reason_labels"]


def test_true_denied_authority_fields_block():
    entry = _entry(denied_authority_fields={"provider_call_made": True})
    assert entry["blocked"] is True
    assert "denied_authority_field_not_false:provider_call_made" in entry["blocked_reason_labels"]


def test_safe_case_metadata_shape_and_source_safety_preserved():
    entry = _entry(source_safety_label="synthetic public-domain-safe metadata summary")
    _assert_valid(entry)
    assert set(entry) == ALLOWED_FIELDS
    assert entry["corpus_schema_version"] == "cognitive_gym_erdos_case_corpus_entry_schema_v1"
    assert entry["case_kind"] == "case_metadata_only"
    assert entry["source_safety_label"] == "synthetic public-domain-safe metadata summary"


def test_problem_definition_known_results_summaries_preserved_as_metadata():
    entry = _entry(
        problem_statement_summary="problem summary metadata only",
        definitions_summary="definition summary metadata only",
        known_results_summary="known results metadata only",
    )
    _assert_valid(entry)
    assert entry["problem_statement_summary"] == "problem summary metadata only"
    assert entry["definitions_summary"] == "definition summary metadata only"
    assert entry["known_results_summary"] == "known results metadata only"


def test_proof_gap_labels_preserved_as_metadata_only():
    entry = _entry(proof_gap_labels=["gap in induction transfer metadata only"])
    _assert_valid(entry)
    assert entry["proof_gap_labels"] == ["gap in induction transfer metadata only"]


def test_counterexample_and_falsification_labels_preserved_as_metadata_only():
    entry = _entry(
        counterexample_search_plan=["search small bounded structures metadata only"],
        falsification_labels=["attempt boundary falsification metadata only"],
    )
    _assert_valid(entry)
    assert entry["counterexample_search_plan"] == ["search small bounded structures metadata only"]
    assert entry["falsification_labels"] == ["attempt boundary falsification metadata only"]


def test_safe_next_observations_preserved_as_metadata_only():
    entry = _entry(safe_next_observations=["read survey labels before hypothesizing metadata only"])
    _assert_valid(entry)
    assert entry["safe_next_observations"] == ["read survey labels before hypothesizing metadata only"]


def test_safe_markdown_is_not_final_answer_user_facing_or_proof_output():
    markdown = _module().render_erdos_case_corpus_entry_markdown_v1(_entry())
    lowered = markdown.lower()
    assert "internal_review_material_only" in markdown
    assert "metadata_only_no_runtime_no_output_no_authority" in markdown
    assert "not_corpus_file" in markdown
    assert "not_corpus_data" in markdown
    assert "not_proof_claim" in markdown
    assert "not_open_problem_solution_claim" in markdown
    assert "not_final_answer_prose" in markdown
    assert "not_user_facing_output" in markdown
    assert "not_reply_output" in markdown
    assert "not_official_benchmark_intelligence_turing_iq_certification_product_claim" in markdown
    assert "no_authority_grant" in markdown
    assert "send this to user" not in lowered
    assert "we prove the open problem" not in lowered


def test_blocked_markdown_preserves_blocked_labels_without_rendering_raw_unsafe_content():
    entry = _entry(unknowns=["answer key: hidden unsafe"])
    markdown = _module().render_erdos_case_corpus_entry_markdown_v1(entry)
    assert "answer_key_indicator_blocked" in markdown
    assert "answer key: hidden unsafe" not in markdown
    assert "unsafe_content_not_rendered" in markdown


def test_json_safe_conversion_works():
    entry = _entry()
    safe = _module().to_erdos_case_corpus_entry_json_safe_v1(entry)
    assert set(safe) == ALLOWED_FIELDS
    assert safe["blocked"] is False
    assert safe["blocked_reason_labels"] == []
    assert all(safe["denied_authority_fields"][field] is False for field in REQUIRED_DENIED_AUTHORITY_FIELDS)


def test_json_safe_conversion_blocks_non_json_safe_values():
    entry = _entry()
    entry["unknowns"] = [float("nan")]
    safe = _module().to_erdos_case_corpus_entry_json_safe_v1(entry)
    assert safe["blocked"] is True
    assert "non_json_safe_entry_detected" in safe["blocked_reason_labels"]


def test_protected_benchmark_items_block():
    entry = _entry(unknowns=["protected benchmark item"])
    assert entry["blocked"] is True
    assert "protected_benchmark_item_blocked" in entry["blocked_reason_labels"]


def test_hidden_prompt_indicators_block():
    entry = _entry(unknowns=["hidden prompt: unsafe"])
    assert entry["blocked"] is True
    assert "hidden_prompt_indicator_blocked" in entry["blocked_reason_labels"]


def test_answer_key_indicators_block():
    entry = _entry(unknowns=["answer key: hidden unsafe"])
    assert entry["blocked"] is True
    assert "answer_key_indicator_blocked" in entry["blocked_reason_labels"]


def test_private_benchmark_content_blocks():
    entry = _entry(unknowns=["copied private benchmark"])
    assert entry["blocked"] is True
    assert "copied_private_benchmark_content_blocked" in entry["blocked_reason_labels"]


def test_private_user_data_blocks():
    entry = _entry(unknowns=["private user data"])
    assert entry["blocked"] is True
    assert "private_user_data_blocked" in entry["blocked_reason_labels"]


def test_raw_copyrighted_long_excerpts_block():
    entry = _entry(unknowns=["raw copyrighted long excerpt"])
    assert entry["blocked"] is True
    assert "raw_copyrighted_long_excerpt_blocked" in entry["blocked_reason_labels"]


def test_proprietary_problem_set_indicators_block():
    entry = _entry(unknowns=["proprietary problem set"])
    assert entry["blocked"] is True
    assert "proprietary_problem_set_indicator_blocked" in entry["blocked_reason_labels"]


def test_official_score_claims_block():
    entry = _entry(known_results_summary="official score: 100")
    assert entry["blocked"] is True
    assert "official_score_claim_blocked" in entry["blocked_reason_labels"]


def test_proof_open_problem_solution_claims_block():
    entry = _entry(hypotheses=["we prove the open problem"])
    assert entry["blocked"] is True
    assert "proof_open_problem_solution_claim_blocked" in entry["blocked_reason_labels"]


def test_solved_without_verification_claims_block():
    entry = _entry(compressed_lesson="solved without external verification")
    assert entry["blocked"] is True
    assert "solved_without_external_verification_claim_blocked" in entry["blocked_reason_labels"]


def test_official_benchmark_turing_iq_certification_product_readiness_claims_block():
    for text in ["official benchmark", "official IQ", "passed the Turing test", "certification claim", "product readiness"]:
        entry = _entry(hypotheses=[text])
        assert entry["blocked"] is True
        assert "official_benchmark_turing_iq_certification_product_readiness_claim_blocked" in entry["blocked_reason_labels"]


def test_runtime_output_provider_model_search_advisor_dot_weslr_indicators_block():
    cases = [
        ("runtime output: unsafe", "runtime_output_indicator_blocked"),
        ("execution output: unsafe", "runtime_output_indicator_blocked"),
        ("provider output: unsafe", "provider_model_search_advisor_output_blocked"),
        ("model output: unsafe", "provider_model_search_advisor_output_blocked"),
        ("search output: unsafe", "provider_model_search_advisor_output_blocked"),
        ("advisor output: unsafe", "provider_model_search_advisor_output_blocked"),
        (".weslr read", "dot_weslr_io_indicator_blocked"),
    ]
    for text, expected in cases:
        entry = _entry(unknowns=[text])
        assert entry["blocked"] is True
        assert expected in entry["blocked_reason_labels"]


def test_judges_scores_indicators_block():
    for text in ["judge decision:", "judges created", "scores created", "score created"]:
        entry = _entry(falsification_labels=[text])
        assert entry["blocked"] is True
        assert "judges_scores_indicator_blocked" in entry["blocked_reason_labels"]


def test_final_answer_user_facing_reply_output_blocks():
    for text in ["final answer:", "user-facing output:", "reply output:"]:
        entry = _entry(hypotheses=[text])
        assert entry["blocked"] is True
        assert "final_answer_user_facing_reply_output_blocked" in entry["blocked_reason_labels"]


def test_unsupported_forbidden_key_indicators_block():
    entry = _entry()
    entry["protected_benchmark_item"] = "unsafe"
    validation = _module().validate_erdos_case_corpus_entry_v1(entry)
    assert validation["blocked"] is True
    assert "unsupported_case_corpus_entry_field:protected_benchmark_item" in validation["blocked_reason_labels"]
    assert "unsupported_indicator_blocked:protected" in validation["blocked_reason_labels"]


def test_no_corpus_runner_challenge_execution_scoring_judges_or_result_artifact_creation():
    entry = _entry()
    assert _module().validate_erdos_case_corpus_entry_v1(entry)["valid"] is True
    assert entry["denied_authority_fields"]["cognitive_gym_executed"] is False
    assert entry["denied_authority_fields"]["cognitive_gym_run_executed"] is False
    assert entry["denied_authority_fields"]["judges_created"] is False
    assert entry["denied_authority_fields"]["scores_created"] is False
    markdown = _module().render_erdos_case_corpus_entry_markdown_v1(entry)
    assert "not_corpus_file" in markdown
    assert "not_corpus_data" in markdown
    assert "not_runner" in markdown
    assert "not_challenge_execution" in markdown
    assert "not_scoring" in markdown
    assert "not_judges" in markdown
    assert "not_result_artifact" in markdown


def test_no_chatresponder_provider_search_advisor_model_calls_or_dot_weslr_io():
    entry = _entry()
    denied = entry["denied_authority_fields"]
    assert denied["chat_responder_called"] is False
    assert denied["respond_chat_called"] is False
    assert denied["generate_chat_called"] is False
    assert denied["provider_call_made"] is False
    assert denied["model_call_made"] is False
    assert denied["search_call_made"] is False
    assert denied["advisor_call_made"] is False
    assert denied["dot_weslr_read_performed"] is False
    assert denied["dot_weslr_write_performed"] is False
    assert "weslr.chat_responder" not in sys.modules


def test_summary_preserves_boundary_status():
    entry = _entry(tier=4)
    summary = _module().summarize_erdos_case_corpus_entry_v1(entry)
    assert summary["track_label"] == TRACK_LABEL
    assert summary["tier"] == 4
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["metadata_only_no_runtime_no_output_no_authority"] is True
    assert summary["metadata_shape_preserved"] is True
    assert summary["next_lane"] == NEXT_LANE
