from __future__ import annotations

import ast
import inspect
import json
from typing import Any

from weslr.arc_style_typed_primitive_signatures import (
    EXPECTED_PRIMITIVE_NAMES_V1,
    build_arc_style_typed_primitive_signature_catalog_v1,
    filter_arc_style_typed_primitive_signatures_by_color_effect_v1,
    filter_arc_style_typed_primitive_signatures_by_composability_tag_v1,
    filter_arc_style_typed_primitive_signatures_by_object_effect_v1,
    filter_arc_style_typed_primitive_signatures_by_shape_effect_v1,
    get_arc_style_typed_primitive_signature_v1,
    list_arc_style_typed_primitive_signatures_v1,
    summarize_arc_style_typed_primitive_signatures_v1,
    to_arc_style_typed_primitive_signatures_json_safe_v1,
    validate_arc_style_typed_primitive_signature_catalog_v1,
    validate_arc_style_typed_primitive_signature_v1,
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
    "requests",
    "pathlib",
    "subprocess",
)


def _json_safe(value: Any) -> Any:
    safe = to_arc_style_typed_primitive_signatures_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


def _contains_callable(value: Any) -> bool:
    if callable(value):
        return True
    if isinstance(value, dict):
        return any(_contains_callable(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_callable(item) for item in value)
    return False


def test_expected_primitives_have_signatures_and_validate() -> None:
    catalog = build_arc_style_typed_primitive_signature_catalog_v1()
    assert set(catalog.keys()) == set(EXPECTED_PRIMITIVE_NAMES_V1)
    catalog_validation = validate_arc_style_typed_primitive_signature_catalog_v1(catalog)
    assert catalog_validation["valid"] is True
    assert catalog_validation["primitive_names"] == sorted(EXPECTED_PRIMITIVE_NAMES_V1)
    for name in EXPECTED_PRIMITIVE_NAMES_V1:
        validation = validate_arc_style_typed_primitive_signature_v1(catalog[name])
        assert validation["valid"] is True
        assert validation["blocked_reason_labels"] == []
        assert get_arc_style_typed_primitive_signature_v1(name, catalog) == catalog[name]


def test_validation_rejects_missing_fields_unknown_names_and_unsafe_flags() -> None:
    catalog = build_arc_style_typed_primitive_signature_catalog_v1()
    base = catalog["move_single_object"]

    missing_fields = dict(base)
    del missing_fields["parameter_schema"]
    validation = validate_arc_style_typed_primitive_signature_v1(missing_fields)
    assert validation["valid"] is False
    assert "missing_required_fields" in validation["blocked_reason_labels"]

    unknown_name = dict(base)
    unknown_name["name"] = "not_real"
    validation = validate_arc_style_typed_primitive_signature_v1(unknown_name)
    assert validation["valid"] is False
    assert "unknown_primitive_name" in validation["blocked_reason_labels"]

    unsafe_flags = dict(base)
    unsafe_flags["leakage_flags"] = dict(base["leakage_flags"], uses_public_arc_kaggle_data=True)
    validation = validate_arc_style_typed_primitive_signature_v1(unsafe_flags)
    assert validation["valid"] is False
    assert any(label.startswith("unsafe_leakage_flag:") for label in validation["blocked_reason_labels"])

    unsafe_authority = dict(base)
    unsafe_authority["authority_flags"] = dict(base["authority_flags"], execution_authority=True)
    validation = validate_arc_style_typed_primitive_signature_v1(unsafe_authority)
    assert validation["valid"] is False
    assert "unsafe_authority_flag:execution_authority" in validation["blocked_reason_labels"]


def test_lookup_and_filter_helpers_are_deterministic() -> None:
    catalog = build_arc_style_typed_primitive_signature_catalog_v1()
    assert list_arc_style_typed_primitive_signatures_v1(catalog) == list_arc_style_typed_primitive_signatures_v1(catalog)
    assert filter_arc_style_typed_primitive_signatures_by_composability_tag_v1("rotate", catalog) == filter_arc_style_typed_primitive_signatures_by_composability_tag_v1("rotate", catalog)
    assert filter_arc_style_typed_primitive_signatures_by_shape_effect_v1("preserve_shape", catalog) == filter_arc_style_typed_primitive_signatures_by_shape_effect_v1("preserve_shape", catalog)
    assert filter_arc_style_typed_primitive_signatures_by_color_effect_v1("paint_pattern", catalog) == filter_arc_style_typed_primitive_signatures_by_color_effect_v1("paint_pattern", catalog)
    assert filter_arc_style_typed_primitive_signatures_by_object_effect_v1("move_object", catalog) == filter_arc_style_typed_primitive_signatures_by_object_effect_v1("move_object", catalog)
    assert get_arc_style_typed_primitive_signature_v1("missing", catalog) is None
    assert [signature["name"] for signature in filter_arc_style_typed_primitive_signatures_by_composability_tag_v1("rotate", catalog)] == ["rotate_object_90"]


def test_json_safe_export_contains_no_callable_objects() -> None:
    catalog = build_arc_style_typed_primitive_signature_catalog_v1()
    safe = _json_safe(catalog)
    assert _contains_callable(safe) is False
    assert safe["copy_grid"]["name"] == "copy_grid"
    assert safe["copy_grid"]["scope_flags"]["metadata_only_helper"] is True


def test_summary_contains_metadata_only_information() -> None:
    catalog = build_arc_style_typed_primitive_signature_catalog_v1()
    summary = summarize_arc_style_typed_primitive_signatures_v1(catalog)
    assert summary["signature_count"] == 16
    assert summary["metadata_only_helper"] is True
    assert summary["design_guarded"] is True
    assert summary["public_data_ready"] is False
    assert summary["kaggle_ready"] is False
    assert summary["execution_authority"] is False
    assert summary["program_search_authority"] is False
    assert summary["official_score_authority"] is False
    assert summary["primitive_names"] == sorted(EXPECTED_PRIMITIVE_NAMES_V1)


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.arc_style_typed_primitive_signatures", fromlist=["*"])
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
    assert "respond_chat(" not in source
    assert "chat_responder." not in source
    assert "openai" not in source.lower()
    assert "anthropic" not in source.lower()
    assert "write(" not in source.lower()
    assert "open(" not in source.lower()
