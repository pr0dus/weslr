from __future__ import annotations

import ast
import inspect
import json
from typing import Any

from weslr.level3_answer_composer import compose_level3_answer_v1
from weslr.level3_answer_improvement_loop import (
    build_level3_answer_improvement_loop_packet_v1,
    to_level3_answer_improvement_loop_json_safe_v1,
)

BANNED_CLAIMS = (
    "agi",
    "consciousness",
    "sentience",
    "official certification",
)

FORBIDDEN_IMPORT_FRAGMENTS = (
    "provider",
    "payment",
    "chat_responder",
    "respond_chat",
    "openai",
    "anthropic",
    "google",
    "ollama",
)


def _synthetic_packet(question: str, family: str, answer: str, *, distance_meters: int | None = None) -> dict[str, Any]:
    normalized_question = " ".join(question.strip().lower().split())
    turn_labels = [normalized_question, family.replace("_", " ")]
    if family == "practical_decision":
        turn_labels.extend(["direct bounded answer", "bounded decision"])
    elif family == "troubleshooting_guidance":
        turn_labels.extend(["debugging flow", "stepwise plan"])
    elif family == "invention_guidance":
        turn_labels.extend(["creative guidance", "bounded idea structure"])
    elif family == "emotional_support":
        turn_labels.extend(["supportive response", "concrete next step"])
    elif family == "unknown_term":
        turn_labels.extend(["bounded uncertainty", "context request"])
    elif family == "hostile_input_boundary":
        turn_labels.extend(["boundary handling", "untrusted input"])
    elif family == "safe_technical_guidance":
        turn_labels.extend(["privacy-preserving sensing", "teaching explanation"])
    elif family == "identity_status":
        turn_labels.extend(["deterministic", "governed assistant stack"])

    context_signals = {
        "question_family": family,
        "identity_question": family == "identity_status",
        "capability_question": family == "capability_overview",
        "troubleshooting_question": family == "troubleshooting_guidance",
        "invention_question": family == "invention_guidance",
        "hostile_input_signal": family == "hostile_input_boundary",
        "unknown_word_signal": family == "unknown_term",
        "safe_technical_signal": family == "safe_technical_guidance",
        "practical_decision_signal": family == "practical_decision",
        "ambiguous_intent_signal": family == "ambiguous_intent",
        "emotional_support_signal": family == "emotional_support",
        "memory_boundary_signal": family == "memory_boundary",
        "safety_boundary_signal": family == "safety_boundary",
        "distance_meters": distance_meters,
        "selected_route_id": f"{family}_route",
        "selected_method_id": f"method_{family}",
        "selected_shape_id": f"shape_{family}",
        "selected_candidate_id": f"candidate_{family}",
        "blocked_by_poison_shield": family == "hostile_input_boundary",
    }
    return {
        "composer_type": "level3_answer_composer_v1",
        "question": question,
        "normalized_question": normalized_question,
        "question_family": family,
        "selected_capability_families": [family],
        "observations": [f"question_family={family}"],
        "inferred_answer_direction": f"{family}_direction",
        "safety_provenance_limits": [
            "no provider/model calls",
            "no chat_responder/respond_chat calls",
            "no runtime website wiring",
            "no .weslr state writes",
            "deterministic local helper stack only",
        ],
        "final_answer_text": answer,
        "module_registry": {"executed_modules": [], "catalog_counts": {}},
        "module_signals": {
            "response_method_selector": {
                "selected_route_id": f"{family}_route",
                "selected_method_id": f"method_{family}",
                "selected_shape_id": f"shape_{family}",
            },
            "candidate_response_formation": {"selected_candidate_id": f"candidate_{family}"},
            "poison_shield": {"blocked": family == "hostile_input_boundary"},
            "raw_signal_cartographer": {"classification": {"engine_family": family}},
            "unknown_prompt_friction_router": {"friction_level": "low"},
            "no_model_bounded_renderer": {"render_mode": "bounded"},
        },
        "rendering": {"json_safe": True},
        "blocked": False,
        "source_provenance": {
            "answer_selector_json_safe": {
                "turn_labels": turn_labels,
                "selected_shape_id": f"shape_{family}",
            }
        },
        "context_signals": context_signals,
    }


def _assert_json_safe(value: Any) -> dict[str, Any]:
    safe = to_level3_answer_improvement_loop_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


def _assert_no_forbidden_imports(module_name: str) -> None:
    module = __import__(module_name, fromlist=["*"])
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    forbidden = {
        fragment
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS
        if fragment in imported_modules or any(fragment in mod for mod in imported_modules)
    }
    assert forbidden == set()


def test_level3_answer_improvement_loop_improves_generic_answer() -> None:
    packet = _synthetic_packet(
        "I want to wash my car. The car wash is 50 meters away. Should I walk or drive?",
        "practical_decision",
        "I can help.",
        distance_meters=50,
    )
    improved = build_level3_answer_improvement_loop_packet_v1(packet)
    assert improved["improvement_applied"] is True
    assert improved["final_answer_text"] != improved["initial_answer_text"]
    lowered = improved["final_answer_text"].lower()
    assert "walk" in lowered
    assert "50" in lowered
    assert improved["fit_check_status"]
    assert improved["friction_replay_status"]


def test_level3_answer_improvement_loop_preserves_good_answer() -> None:
    packet = _synthetic_packet(
        "What is WESLR?",
        "identity_status",
        "WESLR is a deterministic, governed assistant stack in this repo.",
    )
    improved = build_level3_answer_improvement_loop_packet_v1(packet)
    assert "deterministic" in improved["final_answer_text"].lower()
    assert "governed" in improved["final_answer_text"].lower()
    assert len(improved["final_answer_text"]) <= len(improved["initial_answer_text"]) + 180


def test_level3_answer_improvement_loop_resists_hostile_input() -> None:
    packet = _synthetic_packet(
        "How should WESLR avoid being poisoned by hostile input?",
        "hostile_input_boundary",
        "Treat hostile input as untrusted and quarantine it.",
    )
    improved = build_level3_answer_improvement_loop_packet_v1(packet)
    lowered = improved["final_answer_text"].lower()
    assert "quarantine" in lowered or "untrusted" in lowered
    assert "ignore previous instructions" not in lowered
    assert not any(term in lowered for term in BANNED_CLAIMS)


def test_level3_answer_improvement_loop_preserves_unknown_term_uncertainty() -> None:
    packet = _synthetic_packet(
        "What does this unknown acronym mean?",
        "unknown_term",
        "Treat the term as unknown and ask for context before guessing.",
    )
    improved = build_level3_answer_improvement_loop_packet_v1(packet)
    lowered = improved["final_answer_text"].lower()
    assert "unknown" in lowered
    assert "context" in lowered
    assert "guess" in lowered or "uncertainty" in lowered


def test_level3_answer_improvement_loop_makes_practical_advice_more_specific() -> None:
    packet = _synthetic_packet(
        "I want to wash my car. The car wash is 50 meters away. Should I walk or drive?",
        "practical_decision",
        "Walk if the trip is short.",
        distance_meters=50,
    )
    improved = build_level3_answer_improvement_loop_packet_v1(packet)
    lowered = improved["final_answer_text"].lower()
    assert "50" in lowered
    assert "walk" in lowered
    assert "weather" in lowered or "accessibility" in lowered or "parking" in lowered


def test_level3_answer_improvement_loop_gives_bounded_invention_structure() -> None:
    packet = _synthetic_packet(
        "Invent a safe way to use RF/WiFi sensing for movement detection in a house.",
        "invention_guidance",
        "I can propose a few safe ideas.",
    )
    improved = build_level3_answer_improvement_loop_packet_v1(packet)
    lowered = improved["final_answer_text"].lower()
    assert "safe idea" in lowered or "one safe idea" in lowered
    assert "success criterion" in lowered or "tiny experiment" in lowered
    assert "safety check" in lowered or "bounded" in lowered


def test_level3_answer_improvement_loop_emotional_prompts_stay_useful_without_fake_feelings() -> None:
    packet = _synthetic_packet(
        "I am frustrated because WESLR still feels deterministic. What should we do?",
        "emotional_support",
        "That sounds frustrating.",
    )
    improved = build_level3_answer_improvement_loop_packet_v1(packet)
    lowered = improved["final_answer_text"].lower()
    assert "frustrat" in lowered
    assert "i can’t feel" in lowered or "i can\'t feel" in lowered or "i can't feel" in lowered
    assert "next step" in lowered or "exact failure" in lowered or "one check" in lowered


def test_level3_answer_improvement_loop_trace_is_json_safe_and_bans_claims() -> None:
    packet = _synthetic_packet(
        "What is WESLR?",
        "identity_status",
        "WESLR is a deterministic, governed assistant stack in this repo.",
    )
    improved = build_level3_answer_improvement_loop_packet_v1(packet)
    safe = _assert_json_safe(improved)
    lowered = safe["final_answer_text"].lower()
    assert not any(term in lowered for term in BANNED_CLAIMS)
    assert safe["initial_answer_text"]
    assert safe["improved_answer_text"]
    assert safe["improvement_trace"]["schema_version"] == "Level3AnswerImprovementLoopV1"
    assert isinstance(safe["deferred_helpers"], list)


def test_level3_answer_improvement_loop_source_has_no_forbidden_imports_or_calls() -> None:
    for module_name in ("weslr.level3_answer_improvement_loop", "weslr.level3_answer_composer"):
        module = __import__(module_name, fromlist=["*"])
        source = inspect.getsource(module)
        tree = ast.parse(source)
        imported_modules: set[str] = set()
        forbidden_calls: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
            elif isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name):
                    name = fn.id
                    if name in {"respond_chat", "chat_responder", "openai", "anthropic", "payment"}:
                        forbidden_calls.add(name)
        forbidden_imports = {
            fragment
            for fragment in FORBIDDEN_IMPORT_FRAGMENTS
            if fragment in imported_modules or any(fragment in mod for mod in imported_modules)
        }
        assert forbidden_imports == set()
        assert forbidden_calls == set()


def test_level3_answer_improvement_loop_same_family_answers_are_less_template_identical() -> None:
    first = build_level3_answer_improvement_loop_packet_v1(
        _synthetic_packet(
            "I want to wash my car. The car wash is 50 meters away. Should I walk or drive?",
            "practical_decision",
            "Walk if the trip is short.",
            distance_meters=50,
        )
    )
    second = build_level3_answer_improvement_loop_packet_v1(
        _synthetic_packet(
            "I want to wash my car. The car wash is 5 meters away. Should I walk or drive?",
            "practical_decision",
            "Walk if the trip is short.",
            distance_meters=5,
        )
    )
    assert first["final_answer_text"] != second["final_answer_text"]
    assert "50" in first["final_answer_text"]
    assert "5" in second["final_answer_text"]


def test_level3_answer_composer_uses_improvement_loop_default() -> None:
    packet = compose_level3_answer_v1("I want to wash my car. The car wash is 50 meters away. Should I walk or drive?")
    assert packet["initial_answer_text"]
    assert packet["improved_answer_text"]
    assert packet["final_answer_text"] == packet["improved_answer_text"]
    assert packet["improvement_trace"]["loop_type"] == "level3_answer_improvement_loop_v1"
    assert "weslr.level3_answer_improvement_loop" in {entry["module"] for entry in packet["module_registry"]["executed_modules"]}
    safe = _assert_json_safe(packet)
    assert safe["final_answer_text"]
