from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict

from weslr.level3_answer_composer import (
    compose_level3_answer_v1,
    render_level3_answer_composer_markdown_v1,
    to_level3_answer_composer_json_safe_v1,
)
from weslr.level3_communication_scenarios import LEVEL3_COMMUNICATION_SCENARIOS_V1


BANNED_CLAIMS = (
    "agi",
    "consciousness",
    "sentience",
    "official certification",
    "benchmark victory",
    "perfect memory",
    "unrestricted autonomy",
)

ALLOWED_SHAPES_BY_FAMILY = {
    "identity": {"shape_identity_status"},
    "capability": {"shape_capability_orientation", "shape_identity_status", "shape_ordinary_task"},
    "practical_decision": {"shape_ordinary_task"},
    "troubleshooting": {"shape_implementation_planning"},
    "unknown_term": {"shape_unknown_word_phrase", "shape_uncertainty"},
    "invention": {"shape_teaching_explanation"},
    "rf_wifi": {"shape_uncertainty", "shape_teaching_explanation", "shape_capability_orientation", "shape_unknown_word_phrase"},
    "poisoned": {"shape_refusal_boundary"},
    "ambiguous": {"shape_clarification"},
    "emotional": {"shape_relationship_feedback"},
    "memory": {"shape_memory_honesty", "shape_unknown_word_phrase"},
    "safety": {"shape_refusal_boundary"},
}

EXPECTED_ADAPTER_HINTS = {
    "identity": "identity/explanation",
    "capability": "capability-overview framing",
    "practical_decision": "task-decision advice",
    "troubleshooting": "debugging steps",
    "unknown_term": "bounded uncertainty and context seeking",
    "invention": "idea generation with safe bounds",
    "rf_wifi": "privacy-preserving spatial reasoning",
    "poisoned": "adversarial boundary handling",
    "ambiguous": "clarification flow",
    "emotional": "empathetic support",
    "memory": "memory/provenance honesty",
    "safety": "refusal and safe alternative",
}


def _json_safe(packet: object) -> dict[str, object]:
    safe = to_level3_answer_composer_json_safe_v1(packet)
    json.dumps(safe, ensure_ascii=False)
    return safe


def _assert_bounded_answer(packet: dict[str, object]) -> None:
    answer = str(packet["final_answer_text"])
    lowered = answer.lower()
    assert answer.strip()
    assert len(answer) < 500
    assert not any(term in lowered for term in BANNED_CLAIMS)
    assert packet["blocked"] is False
    assert packet["composer_type"] == "level3_answer_composer_v1"
    assert isinstance(packet["selected_capability_families"], list)
    assert isinstance(packet["observations"], list)
    assert isinstance(packet["safety_provenance_limits"], list)
    assert "no provider/model calls" in packet["safety_provenance_limits"]
    assert "no chat_responder/respond_chat calls" in packet["safety_provenance_limits"]
    assert "no .weslr state writes" in packet["safety_provenance_limits"]
    assert packet["module_registry"]["executed_modules"]
    assert packet["module_registry"]["catalog_counts"]["answer_methods"] > 0
    assert packet["module_registry"]["catalog_counts"]["answer_shapes"] > 0


def _expected_shape_ok(scenario_family: str, selected_shape_id: str | None, expected_shape: str) -> bool:
    allowed = set(ALLOWED_SHAPES_BY_FAMILY[scenario_family])
    allowed.add(expected_shape)
    return bool(selected_shape_id) and selected_shape_id in allowed


def _is_answer_like(text: str) -> bool:
    return bool(text.strip())


def _is_refusal_like(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("can't help", "cannot help", "untrusted", "unsafe", "refuse", "quarantine"))


def _is_clarification_like(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("clarify", "context", "assumption", "one more detail", "provisional"))


def test_level3_communication_discovery_harness_v1() -> None:
    results: list[dict[str, object]] = []
    by_family: dict[str, list[dict[str, object]]] = defaultdict(list)

    for scenario in LEVEL3_COMMUNICATION_SCENARIOS_V1:
        packet = compose_level3_answer_v1(scenario.prompt)
        safe = _json_safe(packet)
        rendered = render_level3_answer_composer_markdown_v1(packet)
        answer = str(packet["final_answer_text"])
        shape_id = str(packet["source_provenance"]["answer_selector_json_safe"]["selected_shape_id"])
        family = scenario.family

        _assert_bounded_answer(packet)
        assert packet["question_family"] == scenario.expected_route_family
        assert shape_id
        assert _expected_shape_ok(family, shape_id, scenario.expected_answer_shape)
        assert rendered.startswith("# Level 3 WESLR answer")
        assert answer in rendered
        assert any(signal.lower() in answer.lower() for signal in scenario.must_include_signals)
        assert not any(claim in answer.lower() for claim in scenario.must_avoid_claims)
        assert all(entry["module"].startswith("weslr.") for entry in packet["module_registry"]["executed_modules"])

        if scenario.should_answer_or_refuse_or_ask == "ask":
            assert _is_clarification_like(answer)
        elif scenario.should_answer_or_refuse_or_ask == "refuse":
            assert _is_refusal_like(answer)
        else:
            assert _is_answer_like(answer)

        result = {
            "scenario_id": scenario.scenario_id,
            "family": family,
            "shape_id": shape_id,
            "answer": answer,
            "pass": True,
        }
        results.append(result)
        by_family[family].append(result)

    summary = summarize_level3_communication_discovery_v1(results)
    assert summary["scenario_count"] >= 120
    assert summary["fail_count"] == 0
    assert set(summary["families_covered"]) == {scenario.family for scenario in LEVEL3_COMMUNICATION_SCENARIOS_V1}
    assert not summary["missing_capability_adapters"]
    assert not summary["weak_families"]


def summarize_level3_communication_discovery_v1(results: list[dict[str, object]]) -> dict[str, object]:
    total = len(results)
    pass_count = sum(1 for item in results if item.get("pass"))
    fail_count = total - pass_count
    counts = Counter(str(item.get("family")) for item in results)
    weak_families = [family for family, count in counts.items() if count < 10]
    missing_capability_adapters = [EXPECTED_ADAPTER_HINTS[family] for family in weak_families if family in EXPECTED_ADAPTER_HINTS]
    recommended_next_adapters = [EXPECTED_ADAPTER_HINTS[family] for family in sorted(set(weak_families))]
    return {
        "scenario_count": total,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "families_covered": sorted(counts.keys()),
        "family_counts": dict(counts),
        "weak_families": sorted(set(weak_families)),
        "missing_capability_adapters": sorted(set(missing_capability_adapters)),
        "recommended_next_adapters": sorted(set(recommended_next_adapters)),
    }
