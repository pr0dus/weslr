import builtins
import importlib
import sys

import pytest

from weslr.controlled_behavior_prompt_set import build_default_controlled_behavior_prompt_set_v1
from weslr.real_chatresponder_shadow_call_helpers import (
    DEFAULT_REQUIRED_BLOCKERS_V1,
    build_real_chatresponder_shadow_call_blocker_contract_v1,
    build_real_chatresponder_shadow_call_config_v1,
    build_real_chatresponder_shadow_call_observation_v1,
    evaluate_prompt_set_with_real_chatresponder_shadow_call_v1,
    evaluate_prompt_with_real_chatresponder_shadow_call_v1,
    normalize_real_chatresponder_shadow_call_metadata_v1,
    preflight_for_real_chatresponder_shadow_call_v1,
    render_real_chatresponder_shadow_call_markdown_v1,
    summarize_real_chatresponder_shadow_call_result_v1,
    to_real_chatresponder_shadow_call_json_safe_v1,
    validate_real_chatresponder_shadow_call_config_v1,
    validate_real_chatresponder_shadow_call_observation_v1,
    validate_real_chatresponder_shadow_call_result_v1,
)


def _prompt(prompt_id="ordinary_task_behavior_001"):
    prompt_set = build_default_controlled_behavior_prompt_set_v1()
    return next(item for item in prompt_set["prompts"] if item["prompt_id"] == prompt_id)


def _authorized_config(prompt_id="ordinary_task_behavior_001", **overrides):
    cfg = build_real_chatresponder_shadow_call_config_v1(
        real_call_authorized=True,
        allow_injected_callable=True,
        selected_prompt_ids=[prompt_id],
    )
    cfg.update(overrides)
    return cfg


def _contract(prompt_id="ordinary_task_behavior_001", family="ordinary_task_behavior"):
    return build_real_chatresponder_shadow_call_blocker_contract_v1(prompt_id=prompt_id, family=family)


def test_config_default_authorizes_nothing_and_forbidden_paths_false():
    cfg = build_real_chatresponder_shadow_call_config_v1()
    assert cfg["real_call_authorized"] is False
    assert cfg["allow_injected_callable"] is False
    assert cfg["selected_prompt_ids"] == []
    assert cfg["direct_chatresponder_import_allowed"] is False
    forbidden = [
        "model_calls_allowed", "advisor_calls_allowed", "web_search_allowed", "write_paths_allowed",
        "weslr_state_allowed", "raw_prompt_storage_allowed", "raw_response_storage_allowed",
        "raw_response_retention_allowed", "numeric_scoring_allowed", "official_claims_allowed",
        "default_enablement_allowed", "branch_expansion_allowed",
    ]
    assert all(cfg[key] is False for key in forbidden)
    validation = validate_real_chatresponder_shadow_call_config_v1(cfg)
    assert validation["valid"] is True
    assert "real_call_authorized=false" in validation["warnings"]


def test_config_selected_prompt_required_and_max_enforced():
    missing = build_real_chatresponder_shadow_call_config_v1(real_call_authorized=True)
    assert validate_real_chatresponder_shadow_call_config_v1(missing)["valid"] is False
    too_many = build_real_chatresponder_shadow_call_config_v1(
        real_call_authorized=True,
        selected_prompt_ids=["a", "b"],
        max_selected_prompt_ids=1,
    )
    validation = validate_real_chatresponder_shadow_call_config_v1(too_many)
    assert validation["valid"] is False
    assert any("exceeds" in error for error in validation["errors"])
    too_wide = build_real_chatresponder_shadow_call_config_v1(max_selected_prompt_ids=4)
    assert validate_real_chatresponder_shadow_call_config_v1(too_wide)["valid"] is False
    authorized = _authorized_config()
    assert authorized["direct_chatresponder_import_allowed"] is False
    assert authorized["model_calls_allowed"] is False


def test_blocker_contract_shape_and_blockers_true():
    contract = _contract()
    assert contract["contract_type"] == "weslr_real_chatresponder_shadow_call_blocker_contract_v1"
    assert set(DEFAULT_REQUIRED_BLOCKERS_V1).issubset(set(contract["required_blockers"]))
    for key in [
        "model_calls_blocked", "advisor_calls_blocked", "web_search_blocked", "write_paths_blocked",
        "weslr_state_blocked", "status_recording_blocked", "source_registry_writes_blocked",
        "raw_prompt_logging_blocked", "raw_response_logging_blocked", "raw_response_retention_blocked",
        "global_feature_flag_mutation_blocked", "external_service_calls_blocked",
    ]:
        assert contract[key] is True
    assert "response_text" not in str(contract)


def test_preflight_selected_allowed_family_passes_with_blocker_contract():
    prompt = _prompt()
    preflight = preflight_for_real_chatresponder_shadow_call_v1(
        prompt,
        config=_authorized_config(prompt["prompt_id"]),
        blocker_contract=_contract(prompt["prompt_id"], prompt["family"]),
    )
    assert preflight["preflight_allowed"] is True
    assert preflight["side_effects"]["prompt_execution"] is False
    assert preflight["side_effects"]["chatresponder_called"] is False


def test_preflight_blocks_unselected_blocked_families_unsafe_live_slice_and_missing_contract():
    prompt = _prompt()
    unselected = preflight_for_real_chatresponder_shadow_call_v1(
        prompt,
        config=_authorized_config("conduct_alignment_001"),
        blocker_contract=_contract(prompt["prompt_id"], prompt["family"]),
    )
    assert unselected["preflight_allowed"] is False
    assert "prompt_id_not_selected" in unselected["reason_labels"]

    memory_prompt = _prompt("memory_honesty_001")
    blocked = preflight_for_real_chatresponder_shadow_call_v1(memory_prompt, config=_authorized_config(memory_prompt["prompt_id"]), blocker_contract=_contract(memory_prompt["prompt_id"], memory_prompt["family"]))
    assert blocked["preflight_allowed"] is False
    assert "memory_namespace_required" in blocked["reason_labels"]

    live_prompt = _prompt("live_slice_behavior_004")
    live = preflight_for_real_chatresponder_shadow_call_v1(live_prompt, config=_authorized_config(live_prompt["prompt_id"]), blocker_contract=_contract(live_prompt["prompt_id"], live_prompt["family"]))
    assert live["preflight_allowed"] is False
    assert "branch_expansion_blocked" in live["reason_labels"]

    missing_contract = preflight_for_real_chatresponder_shadow_call_v1(prompt, config=_authorized_config(prompt["prompt_id"]))
    assert missing_contract["preflight_allowed"] is False
    assert "blocker_contract_missing" in missing_contract["reason_labels"]


def test_observation_builder_validator_metadata_only_and_warnings():
    blocked = build_real_chatresponder_shadow_call_observation_v1(
        prompt_id="p", family="ordinary_task_behavior", reason_labels=["preflight_blocked"]
    )
    assert validate_real_chatresponder_shadow_call_observation_v1(blocked)["valid"] is True

    allowed_not_called = build_real_chatresponder_shadow_call_observation_v1(
        prompt_id="p", family="ordinary_task_behavior", preflight_allowed=True,
        blocked_by_boundary=False, property_label="not_observed", reason_labels=["real_call_not_authorized"],
    )
    validation = validate_real_chatresponder_shadow_call_observation_v1(allowed_not_called)
    assert validation["valid"] is True
    assert any("preflight_allowed=true" in warning for warning in validation["warnings"])


def test_observation_validator_rejects_unsafe_paths_keys_and_claim_text():
    obs = build_real_chatresponder_shadow_call_observation_v1(
        prompt_id="p", family="ordinary_task_behavior", preflight_allowed=False,
        call_attempted=True, reason_labels=["preflight_blocked"]
    )
    assert validate_real_chatresponder_shadow_call_observation_v1(obs)["valid"] is False

    obs2 = build_real_chatresponder_shadow_call_observation_v1(
        prompt_id="p", family="ordinary_task_behavior", preflight_allowed=False,
        chatresponder_called=True, reason_labels=["preflight_blocked"]
    )
    assert validate_real_chatresponder_shadow_call_observation_v1(obs2)["valid"] is False

    for key in ["model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_stored", "raw_response_stored", "raw_response_retained"]:
        mutated = build_real_chatresponder_shadow_call_observation_v1(prompt_id="p", family="ordinary_task_behavior", reason_labels=["preflight_blocked"])
        mutated[key] = True
        assert validate_real_chatresponder_shadow_call_observation_v1(mutated)["valid"] is False

    unsafe = build_real_chatresponder_shadow_call_observation_v1(prompt_id="p", family="ordinary_task_behavior", reason_labels=["preflight_blocked"])
    unsafe["raw_text"] = "secret"
    assert validate_real_chatresponder_shadow_call_observation_v1(unsafe)["valid"] is False
    unsafe2 = build_real_chatresponder_shadow_call_observation_v1(prompt_id="p", family="ordinary_task_behavior", reason_labels=["preflight_blocked"])
    unsafe2["safe_summary"] = "passed Turing test"
    assert validate_real_chatresponder_shadow_call_observation_v1(unsafe2)["valid"] is False


def test_metadata_normalizer_safe_and_unsafe_without_leak():
    safe = normalize_real_chatresponder_shadow_call_metadata_v1(
        {"property_label": "pass_property", "properties_observed": ["bounded"], "safe_summary": "metadata only"},
        prompt_id="p", family="ordinary_task_behavior",
    )
    assert safe["chatresponder_called"] is True
    assert validate_real_chatresponder_shadow_call_observation_v1(safe)["valid"] is True

    unsafe = normalize_real_chatresponder_shadow_call_metadata_v1(
        {"response_text": "do not leak", "raw_text": "private", "final_answer": "hidden"},
        prompt_id="p", family="ordinary_task_behavior",
    )
    assert unsafe["blocked_by_boundary"] is True
    assert "unsafe_response_metadata_blocked" in unsafe["reason_labels"]
    assert "do not leak" not in str(unsafe)
    assert "private" not in str(unsafe)


def test_single_prompt_wrapper_call_controls_and_unsafe_callable_metadata():
    prompt = _prompt()
    calls = []

    def fake(context):
        calls.append(context)
        return {"property_label": "pass_property", "properties_observed": ["bounded"], "safe_summary": "safe metadata"}

    blocked_prompt = _prompt("memory_honesty_001")
    obs = evaluate_prompt_with_real_chatresponder_shadow_call_v1(
        blocked_prompt, shadow_callable=fake, config=_authorized_config(blocked_prompt["prompt_id"]), blocker_contract=_contract(blocked_prompt["prompt_id"], blocked_prompt["family"])
    )
    assert obs["blocked_by_boundary"] is True
    assert calls == []

    not_auth = evaluate_prompt_with_real_chatresponder_shadow_call_v1(prompt, shadow_callable=fake)
    assert not_auth["property_label"] == "not_observed"
    assert calls == []

    no_callable_allowed = evaluate_prompt_with_real_chatresponder_shadow_call_v1(
        prompt,
        shadow_callable=fake,
        config=build_real_chatresponder_shadow_call_config_v1(real_call_authorized=True, allow_injected_callable=False, selected_prompt_ids=[prompt["prompt_id"]]),
        blocker_contract=_contract(prompt["prompt_id"], prompt["family"]),
    )
    assert no_callable_allowed["property_label"] == "not_observed"
    assert calls == []

    missing_callable = evaluate_prompt_with_real_chatresponder_shadow_call_v1(
        prompt, config=_authorized_config(prompt["prompt_id"]), blocker_contract=_contract(prompt["prompt_id"], prompt["family"])
    )
    assert "no_shadow_callable_supplied" in missing_callable["reason_labels"]

    called = evaluate_prompt_with_real_chatresponder_shadow_call_v1(
        prompt, shadow_callable=fake, config=_authorized_config(prompt["prompt_id"]), blocker_contract=_contract(prompt["prompt_id"], prompt["family"])
    )
    assert len(calls) == 1
    assert calls[0]["raw_prompt_available"] is False
    assert called["chatresponder_called"] is True

    def unsafe(_context):
        return {"response_text": "leak"}

    unsafe_obs = evaluate_prompt_with_real_chatresponder_shadow_call_v1(
        prompt, shadow_callable=unsafe, config=_authorized_config(prompt["prompt_id"]), blocker_contract=_contract(prompt["prompt_id"], prompt["family"])
    )
    assert unsafe_obs["blocked_by_boundary"] is True
    assert "leak" not in str(unsafe_obs)


def test_prompt_set_wrapper_default_no_calls_authorized_selected_only_unknown_ids_and_max():
    prompt = _prompt()
    calls = []

    def fake(context):
        calls.append(context["prompt_id"])
        return {"property_label": "pass_property", "properties_observed": ["bounded"], "safe_summary": "safe metadata"}

    default_result = evaluate_prompt_set_with_real_chatresponder_shadow_call_v1(shadow_callables_by_prompt_id={prompt["prompt_id"]: fake}, repo_head="1234567")
    assert default_result["call_attempted_count"] == 0
    assert calls == []

    result = evaluate_prompt_set_with_real_chatresponder_shadow_call_v1(
        shadow_callables_by_prompt_id={prompt["prompt_id"]: fake, "memory_honesty_001": fake},
        config=_authorized_config(prompt["prompt_id"]),
        blocker_contracts_by_prompt_id={prompt["prompt_id"]: _contract(prompt["prompt_id"], prompt["family"])},
        repo_head="1234567",
    )
    assert calls == [prompt["prompt_id"]]
    assert result["chatresponder_called_count"] == 1
    assert validate_real_chatresponder_shadow_call_result_v1(result)["valid"] is True

    unknown = evaluate_prompt_set_with_real_chatresponder_shadow_call_v1(
        shadow_callables_by_prompt_id={"unknown_prompt": fake}, repo_head="1234567"
    )
    assert validate_real_chatresponder_shadow_call_result_v1(unknown)["valid"] is False

    too_many = evaluate_prompt_set_with_real_chatresponder_shadow_call_v1(
        config=build_real_chatresponder_shadow_call_config_v1(real_call_authorized=True, selected_prompt_ids=["a", "b"], max_selected_prompt_ids=1),
        repo_head="1234567",
    )
    assert validate_real_chatresponder_shadow_call_result_v1(too_many)["valid"] is False


def test_result_validator_rejects_unsafe_drift_and_forbidden_content():
    result = evaluate_prompt_set_with_real_chatresponder_shadow_call_v1(repo_head="1234567")
    for key in [
        "model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created",
        "raw_prompt_storage", "raw_response_storage", "raw_response_retention",
        "raw_private_text_included", "numeric_scores_used", "official_claims",
    ]:
        mutated = to_real_chatresponder_shadow_call_json_safe_v1(result)
        mutated[key] = True
        assert validate_real_chatresponder_shadow_call_result_v1(mutated)["valid"] is False
    with_key = to_real_chatresponder_shadow_call_json_safe_v1(result)
    with_key["raw_prompt"] = "secret"
    assert validate_real_chatresponder_shadow_call_result_v1(with_key)["valid"] is False
    with_claim = to_real_chatresponder_shadow_call_json_safe_v1(result)
    with_claim["note"] = "certified intelligent"
    assert validate_real_chatresponder_shadow_call_result_v1(with_claim)["valid"] is False


def test_json_safe_copy_is_not_sanitizer():
    result = evaluate_prompt_set_with_real_chatresponder_shadow_call_v1(repo_head="1234567")
    result["raw_text"] = "preserve me"
    copied = to_real_chatresponder_shadow_call_json_safe_v1(result)
    assert copied["raw_text"] == "preserve me"
    assert validate_real_chatresponder_shadow_call_result_v1(copied)["valid"] is False


def test_summary_and_markdown_are_safe_counts_status_only():
    result = evaluate_prompt_set_with_real_chatresponder_shadow_call_v1(repo_head="1234567")
    summary = summarize_real_chatresponder_shadow_call_result_v1(result)
    markdown = render_real_chatresponder_shadow_call_markdown_v1(result)
    assert summary["prompt_count"] == result["prompt_count"]
    assert "SECTION 1 — STATUS" in markdown
    assert "SECTION 8 — RECOMMENDED NEXT STEP" in markdown
    forbidden = [
        "Help me make", "response_text", "source_urls", "hidden_prompt", "answer_key",
        "protected_material", "passed Turing test", "official benchmark", "IQ score",
    ]
    for text in forbidden:
        assert text not in str(summary)
        assert text not in markdown


def test_no_side_effect_file_writes_and_no_direct_chatresponder_import(monkeypatch):
    module = importlib.import_module("weslr.real_chatresponder_shadow_call_helpers")
    source_path = module.__file__
    with open(source_path, "r", encoding="utf-8") as handle:
        source = handle.read()
    assert "from weslr.chat_responder" not in source
    assert "import weslr.chat_responder" not in source
    assert "ChatResponder(" not in source

    def blocked_open(*args, **kwargs):
        raise AssertionError("helper attempted file write/read")

    monkeypatch.setattr(builtins, "open", blocked_open)
    before_weslr_modules = {name for name in sys.modules if name.endswith("chat_responder") or name == "weslr.chat_responder"}
    result = evaluate_prompt_set_with_real_chatresponder_shadow_call_v1(repo_head="1234567")
    assert result["weslr_state_created"] is False
    after_weslr_modules = {name for name in sys.modules if name.endswith("chat_responder") or name == "weslr.chat_responder"}
    assert after_weslr_modules == before_weslr_modules
