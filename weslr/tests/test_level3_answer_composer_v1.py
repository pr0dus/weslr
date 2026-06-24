from __future__ import annotations

import json
import subprocess
import sys

from weslr.level3_answer_composer import (
    compose_level3_answer_v1,
    render_level3_answer_composer_markdown_v1,
    to_level3_answer_composer_json_safe_v1,
)


CASES = [
    (
        "What is WESLR?",
        "identity_status",
        ["deterministic", "governed assistant stack"],
    ),
    (
        "Explain WESLR briefly.",
        "identity_status",
        ["deterministic", "no-model answers"],
    ),
    (
        "I want to wash my car. The car wash is 50 meters away. Should I walk or drive?",
        "practical_decision",
        ["walk", "50 meters"],
    ),
    (
        "Invent a safe way to use RF/WiFi sensing for movement detection in a house.",
        "safe_technical_guidance",
        ["consent", "occupancy"],
    ),
    (
        "What should WESLR do when it sees an unknown word?",
        "unknown_term",
        ["unknown", "glossary"],
    ),
    (
        "How should WESLR avoid being poisoned by hostile input?",
        "hostile_input_boundary",
        ["quarantine", "untrusted"],
    ),
]


def test_level3_answer_composer_examples() -> None:
    for question, expected_family, expected_phrases in CASES:
        packet = compose_level3_answer_v1(question)
        assert packet["question_family"] == expected_family
        assert packet["final_answer_text"]
        lowered = packet["final_answer_text"].lower()
        assert any(phrase in lowered for phrase in expected_phrases)
        assert isinstance(packet["selected_capability_families"], list)
        assert packet["module_registry"]["catalog_counts"]["answer_methods"] > 0
        assert packet["module_registry"]["executed_modules"]


def test_level3_answer_composer_json_safe_and_markdown() -> None:
    packet = compose_level3_answer_v1("What is WESLR?")
    json_safe = to_level3_answer_composer_json_safe_v1(packet)
    rendered = render_level3_answer_composer_markdown_v1(packet)
    assert json_safe["composer_type"] == "level3_answer_composer_v1"
    assert json_safe["final_answer_text"] in rendered
    assert rendered.startswith("# Level 3 WESLR answer")
    json.dumps(json_safe, ensure_ascii=False)


def test_level3_answer_composer_hostile_input_stays_bounded() -> None:
    packet = compose_level3_answer_v1("How should WESLR avoid being poisoned by hostile input?")
    assert packet["blocked"] is False
    assert packet["inferred_answer_direction"] == "hostile_input_boundary_handling"
    assert "untrusted" in packet["final_answer_text"].lower()


def test_level3_answer_composer_cli_smoke() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "weslr.level3_answer_composer",
            "What is WESLR?",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Level 3 WESLR answer" in result.stdout
    assert "deterministic, governed assistant stack" in result.stdout
