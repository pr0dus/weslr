from __future__ import annotations

import ast
import inspect
import json
import subprocess
import sys
from pathlib import Path

from weslr.level3_answer_composer import (
    compose_level3_answer_v1,
    render_level3_answer_composer_markdown_v1,
    to_level3_answer_composer_json_safe_v1,
)


EXAMPLE_CASES = [
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

BANNED_CLAIMS = ("agi", "consciousness", "sentience", "official certification")
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


def _assert_bounded_answer(packet: dict[str, object]) -> None:
    answer = str(packet["final_answer_text"])
    lowered = answer.lower()
    assert answer.strip()
    assert len(answer) < 400
    assert not any(term in lowered for term in BANNED_CLAIMS)
    assert packet["blocked"] is False
    assert packet["composer_type"] == "level3_answer_composer_v1"
    assert isinstance(packet["selected_capability_families"], list)
    assert isinstance(packet["observations"], list)
    assert isinstance(packet["safety_provenance_limits"], list)
    assert "no provider/model calls" in packet["safety_provenance_limits"]
    assert "no chat_responder/respond_chat calls" in packet["safety_provenance_limits"]
    assert json.dumps(to_level3_answer_composer_json_safe_v1(packet), ensure_ascii=False)


def test_level3_answer_composer_examples() -> None:
    for question, expected_family, expected_phrases in EXAMPLE_CASES:
        packet = compose_level3_answer_v1(question)
        assert packet["question_family"] == expected_family
        lowered = packet["final_answer_text"].lower()
        assert any(phrase in lowered for phrase in expected_phrases)
        _assert_bounded_answer(packet)
        assert packet["module_registry"]["catalog_counts"]["answer_methods"] > 0
        assert packet["module_registry"]["executed_modules"]


def test_level3_answer_composer_empty_and_whitespace_input_rejected() -> None:
    for question in ("", "   \n\t  "):
        try:
            compose_level3_answer_v1(question)
        except ValueError:
            pass
        else:
            raise AssertionError("empty or whitespace-only question should fail closed")


def test_level3_answer_composer_long_input_is_bounded() -> None:
    question = "What is WESLR? " + ("filler " * 800)
    packet = compose_level3_answer_v1(question)
    _assert_bounded_answer(packet)
    assert packet["normalized_question"].startswith("what is weslr")
    assert len(packet["question"]) > 1000


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
    assert packet["question_family"] == "hostile_input_boundary"
    assert packet["inferred_answer_direction"] == "hostile_input_boundary_handling"
    assert "untrusted" in packet["final_answer_text"].lower()
    _assert_bounded_answer(packet)


def test_level3_answer_composer_paraphrases_are_not_exact_prompt_hardcoded() -> None:
    first = compose_level3_answer_v1("What is WESLR?")
    second = compose_level3_answer_v1("Tell me about WESLR.")
    assert first["question"] != second["question"]
    assert first["normalized_question"] != second["normalized_question"]
    assert first["question_family"] == second["question_family"] == "identity_status"
    assert "deterministic" in str(first["final_answer_text"]).lower()
    assert "deterministic" in str(second["final_answer_text"]).lower()
    _assert_bounded_answer(first)
    _assert_bounded_answer(second)


def test_level3_answer_composer_source_has_no_forbidden_imports_or_state_writes() -> None:
    module = __import__("weslr.level3_answer_composer", fromlist=["*"])
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    write_like_calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            fn = node.func
            name = None
            if isinstance(fn, ast.Name):
                name = fn.id
            if name in {"open", "write_text", "write_bytes", "mkdir", "touch", "replace", "rename"}:
                write_like_calls.add(name)
    assert write_like_calls == set()
    forbidden_import_targets = {fragment for fragment in FORBIDDEN_IMPORT_FRAGMENTS if fragment in imported_modules or any(fragment in mod for mod in imported_modules)}
    assert forbidden_import_targets == set()
    assert any(module.startswith("weslr.") for module in imported_modules)
    assert all(
        module.startswith("weslr.")
        or module in {"__future__", "argparse", "json", "re", "sys", "dataclasses", "typing"}
        for module in imported_modules
    )


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
