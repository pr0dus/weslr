from pathlib import Path

from weslr.controlled_behavior_prompt_set import build_default_controlled_behavior_prompt_set_v1
from weslr.chatresponder_shadow_execution_helpers import (
    build_chatresponder_shadow_execution_blocker_contract_v1,
    build_chatresponder_shadow_execution_config_v1,
    build_chatresponder_shadow_execution_observation_v1,
    evaluate_prompt_set_with_chatresponder_shadow_execution_v1,
    evaluate_prompt_with_chatresponder_shadow_execution_v1,
    normalize_chatresponder_shadow_execution_metadata_v1,
    preflight_for_chatresponder_shadow_execution_v1,
    render_chatresponder_shadow_execution_markdown_v1,
    summarize_chatresponder_shadow_execution_result_v1,
    to_chatresponder_shadow_execution_json_safe_v1,
    validate_chatresponder_shadow_execution_observation_v1,
    validate_chatresponder_shadow_execution_result_v1,
)


def _prompt(prompt_id: str):
    for item in build_default_controlled_behavior_prompt_set_v1()["prompts"]:
        if item["prompt_id"] == prompt_id:
            return item
    raise AssertionError(prompt_id)


def test_config_default_denies_and_never_allows_direct_import():
    cfg = build_chatresponder_shadow_execution_config_v1()
    assert cfg["execution_authorized"] is False
    assert cfg["allow_injected_callable"] is False
    assert cfg["direct_chatresponder_import_allowed"] is False
    assert cfg["model_calls_allowed"] is False
    assert cfg["web_search_allowed"] is False
    assert cfg["write_paths_allowed"] is False
    assert cfg["raw_prompt_storage_allowed"] is False
    cfg2 = build_chatresponder_shadow_execution_config_v1(execution_authorized=True, allow_injected_callable=True)
    assert cfg2["execution_authorized"] is True
    assert cfg2["allow_injected_callable"] is True
    assert cfg2["direct_chatresponder_import_allowed"] is False
    assert cfg2["model_calls_allowed"] is False
    assert cfg2["official_claims_allowed"] is False


def test_blocker_contract_shape():
    contract = build_chatresponder_shadow_execution_blocker_contract_v1(prompt_id="p1", family="ordinary_task_behavior")
    assert contract["contract_type"] == "weslr_chatresponder_shadow_execution_blocker_contract_v1"
    assert contract["model_calls_blocked"] is True
    assert contract["advisor_calls_blocked"] is True
    assert contract["web_search_blocked"] is True
    assert contract["write_paths_blocked"] is True
    assert contract["weslr_state_blocked"] is True
    assert contract["raw_prompt_logging_blocked"] is True
    assert "model_generation" in contract["required_blockers"]


def test_preflight_allowed_and_blocked_families_metadata_only():
    allowed_ids = ["ordinary_task_behavior_001", "non_canned_cognition_001", "conduct_alignment_001"]
    for pid in allowed_ids:
        pf = preflight_for_chatresponder_shadow_execution_v1(_prompt(pid))
        assert pf["preflight_allowed"] is True
        assert pf["side_effects"]["prompt_execution"] is False
        assert pf["side_effects"]["chatresponder_called"] is False
    blocked_ids = ["memory_honesty_001", "continuity_relationship_001", "self_identity_boundaries_001", "evidence_source_boundaries_001", "guardrail_preservation_001"]
    for pid in blocked_ids:
        pf = preflight_for_chatresponder_shadow_execution_v1(_prompt(pid))
        assert pf["preflight_allowed"] is False
        assert pf["blocked_by_boundary"] is True
        assert pf["reason_labels"]
    unsafe_live = _prompt("live_slice_behavior_004")
    pf = preflight_for_chatresponder_shadow_execution_v1(unsafe_live)
    assert pf["preflight_allowed"] is False
    assert "branch_expansion_blocked" in pf["reason_labels"] or "default_enablement_blocked" in pf["reason_labels"]


def test_observation_builder_and_validator_rules():
    blocked = build_chatresponder_shadow_execution_observation_v1(prompt_id="p", family="memory_honesty", reason_labels=["memory_namespace_required"])
    assert validate_chatresponder_shadow_execution_observation_v1(blocked)["valid"] is True
    allowed_not_called = build_chatresponder_shadow_execution_observation_v1(
        prompt_id="p", family="ordinary_task_behavior", preflight_allowed=True, blocked_by_boundary=False, property_label="not_observed"
    )
    validation = validate_chatresponder_shadow_execution_observation_v1(allowed_not_called)
    assert validation["valid"] is True
    assert validation["warnings"]
    bad = build_chatresponder_shadow_execution_observation_v1(
        prompt_id="p", family="ordinary_task_behavior", preflight_allowed=False, execution_attempted=True, blocked_by_boundary=False
    )
    assert validate_chatresponder_shadow_execution_observation_v1(bad)["valid"] is False
    bad2 = dict(allowed_not_called, chatresponder_called=True, model_calls=True)
    assert validate_chatresponder_shadow_execution_observation_v1(bad2)["valid"] is False
    bad3 = dict(blocked, raw_text="leak")
    assert validate_chatresponder_shadow_execution_observation_v1(bad3)["valid"] is False
    bad4 = dict(blocked, safe_summary="passed Turing test")
    assert validate_chatresponder_shadow_execution_observation_v1(bad4)["valid"] is False


def test_metadata_normalizer_safe_and_unsafe_no_leak():
    safe = normalize_chatresponder_shadow_execution_metadata_v1(
        {"property_label": "pass_property", "properties_observed": ["bounded"], "safe_summary": "safe metadata"},
        prompt_id="p", family="ordinary_task_behavior"
    )
    assert safe["chatresponder_called"] is True
    assert safe["property_label"] == "pass_property"
    assert validate_chatresponder_shadow_execution_observation_v1(safe)["valid"] is True
    unsafe = normalize_chatresponder_shadow_execution_metadata_v1(
        {"response_text": "do not retain", "raw_text": "secret", "final_answer": "x"},
        prompt_id="p", family="ordinary_task_behavior"
    )
    assert unsafe["blocked_by_boundary"] is True
    assert "unsafe_execution_metadata_blocked" in unsafe["reason_labels"]
    assert "secret" not in str(unsafe)
    assert "do not retain" not in str(unsafe)


def test_single_prompt_wrapper_gates_injected_callable():
    calls = []
    def fake(_meta):
        calls.append(_meta["prompt_id"])
        return {"property_label": "pass_property", "properties_observed": ["bounded"], "safe_summary": "safe"}

    blocked = evaluate_prompt_with_chatresponder_shadow_execution_v1(_prompt("memory_honesty_001"), execution_callable=fake)
    assert blocked["blocked_by_boundary"] is True
    assert calls == []
    noauth = evaluate_prompt_with_chatresponder_shadow_execution_v1(_prompt("ordinary_task_behavior_001"), execution_callable=fake)
    assert noauth["property_label"] == "not_observed"
    assert "execution_not_authorized" in noauth["reason_labels"]
    assert calls == []
    cfg = build_chatresponder_shadow_execution_config_v1(execution_authorized=True)
    noallow = evaluate_prompt_with_chatresponder_shadow_execution_v1(_prompt("ordinary_task_behavior_001"), execution_callable=fake, config=cfg)
    assert noallow["property_label"] == "not_observed"
    assert calls == []
    cfg = build_chatresponder_shadow_execution_config_v1(execution_authorized=True, allow_injected_callable=True)
    missing = evaluate_prompt_with_chatresponder_shadow_execution_v1(_prompt("ordinary_task_behavior_001"), config=cfg)
    assert "no_execution_callable_supplied" in missing["reason_labels"]
    ok = evaluate_prompt_with_chatresponder_shadow_execution_v1(_prompt("ordinary_task_behavior_001"), execution_callable=fake, config=cfg)
    assert ok["chatresponder_called"] is True
    assert calls == ["ordinary_task_behavior_001"]
    unsafe = evaluate_prompt_with_chatresponder_shadow_execution_v1(
        _prompt("ordinary_task_behavior_002"), execution_callable=lambda _m: {"raw_text": "leak"}, config=cfg
    )
    assert unsafe["blocked_by_boundary"] is True
    assert "leak" not in str(unsafe)


def test_prompt_set_wrapper_default_and_authorized_callable_scope():
    ps = build_default_controlled_behavior_prompt_set_v1()
    result = evaluate_prompt_set_with_chatresponder_shadow_execution_v1(ps, repo_head="9ab6958")
    assert result["execution_attempted_count"] == 0
    assert result["chatresponder_called_count"] == 0
    assert validate_chatresponder_shadow_execution_result_v1(result)["valid"] is True

    calls = []
    cfg = build_chatresponder_shadow_execution_config_v1(execution_authorized=True, allow_injected_callable=True)
    callables = {
        "ordinary_task_behavior_001": lambda meta: calls.append(meta["prompt_id"]) or {"property_label": "pass_property", "safe_summary": "safe"},
        "memory_honesty_001": lambda meta: calls.append("blocked") or {"property_label": "pass_property"},
    }
    result2 = evaluate_prompt_set_with_chatresponder_shadow_execution_v1(ps, execution_callables_by_prompt_id=callables, config=cfg, repo_head="9ab6958")
    assert "ordinary_task_behavior_001" in calls
    assert "blocked" not in calls
    assert result2["chatresponder_called_count"] == 1
    assert validate_chatresponder_shadow_execution_result_v1(result2)["valid"] is True

    result3 = evaluate_prompt_set_with_chatresponder_shadow_execution_v1(ps, execution_callables_by_prompt_id={"unknown": lambda _m: {}}, config=cfg, repo_head="9ab6958")
    assert validate_chatresponder_shadow_execution_result_v1(result3)["valid"] is False


def test_result_validation_rejects_unsafe_drift_and_json_copy_not_sanitizer():
    result = evaluate_prompt_set_with_chatresponder_shadow_execution_v1(repo_head="9ab6958")
    for key in ["model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_storage", "raw_response_storage", "raw_private_text_included", "numeric_scores_used", "official_claims"]:
        bad = dict(result, **{key: True})
        assert validate_chatresponder_shadow_execution_result_v1(bad)["valid"] is False
    copied = to_chatresponder_shadow_execution_json_safe_v1(dict(result, raw_text="leak"))
    assert copied["raw_text"] == "leak"
    assert validate_chatresponder_shadow_execution_result_v1(copied)["valid"] is False


def test_summary_and_markdown_are_count_status_only():
    result = evaluate_prompt_set_with_chatresponder_shadow_execution_v1(repo_head="9ab6958")
    summary = summarize_chatresponder_shadow_execution_result_v1(result)
    assert "prompt_text" not in str(summary)
    assert "response_text" not in str(summary)
    assert "source_urls" not in str(summary)
    md = render_chatresponder_shadow_execution_markdown_v1(result)
    for section in ["SECTION 1 — STATUS", "SECTION 2 — EXECUTION BOUNDARIES", "SECTION 8 — RECOMMENDED NEXT STEP"]:
        assert section in md
    assert "prompt_text" not in md
    assert "response_text" not in md
    assert "source_urls" not in md
    assert "hidden_prompt" not in md
    assert "answer_key" not in md
    assert "protected_material" not in md


def test_no_side_effect_files_or_direct_chatresponder_import(tmp_path):
    before = set(Path.cwd().glob(".weslr/**/*")) if Path(".weslr").exists() else set()
    evaluate_prompt_set_with_chatresponder_shadow_execution_v1(repo_head="9ab6958")
    after = set(Path.cwd().glob(".weslr/**/*")) if Path(".weslr").exists() else set()
    assert before == after
    source = Path("weslr/chatresponder_shadow_execution_helpers.py").read_text(encoding="utf-8")
    assert "from weslr.chat_responder import" not in source
    assert "import weslr.chat_responder" not in source
    assert "ChatResponder(" not in source
