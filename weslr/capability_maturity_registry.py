"""Metadata-only capability maturity registry helpers v1.

This module tracks capability maturity, authority, risk, prerequisites, and
recommended next lanes. It is pure, deterministic, import-safe, and fail-closed.

It does not inspect runtime state. It does not write `.weslr`. It does not
wire runtime behavior. It does not call APIs or route chat.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "capability_maturity_registry_v1"
REGISTRY_TYPE_V1 = "capability_maturity_registry_v1"
SUMMARY_TYPE_V1 = "capability_maturity_registry_summary_v1"
RECORD_TYPE_V1 = "capability_maturity_record_v1"

ALLOWED_MATURITY_LEVELS_V1 = {
    "idea",
    "design_only",
    "reviewed_design",
    "metadata_helper",
    "dry_run",
    "sandboxed",
    "validated",
    "owner_approved_runtime",
    "pilot_limited",
    "public_safe",
    "blocked_or_deprecated",
}

ALLOWED_AUTHORITY_STATES_V1 = {
    "no_authority",
    "metadata_only",
    "dry_run_only",
    "read_only",
    "sandbox_create_only",
    "validation_only",
    "proposal_only",
    "owner_approved_action",
    "operator_approved_runtime",
    "public_release_authority",
    "blocked",
}

ALLOWED_CAPABILITY_FAMILIES_V1 = {
    "memory_and_context",
    "artifact_and_code_generation",
    "writer_and_provenance",
    "poison_shield_and_authority",
    "forecasting_and_scenarios",
    "energy_grid_and_home_assistant",
    "wifi_rf_and_privacy_sensitive_signals",
    "llm_provider_candidate_generation",
    "tool_action_and_device_control",
    "public_product_and_claims",
    "operator_workflow",
    "friction_and_behavior_packs",
}

FORBIDDEN_FIELD_HINTS_V1 = (
    "hidden_prompt",
    "raw_private",
    "private_data",
    "secret",
    "token",
    "key",
    "api_key",
    "credential",
    "password",
)

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "public readiness",
    "public ready",
    "public-safe",
    "runtime authority",
    "runtime-ready",
    "production ready",
    "security certification",
    "official certification",
    "official security",
    "turing",
    "agi",
    "consciousness",
    "sentience",
)

CLAIM_BASE_TERMS_V1 = {
    "public",
    "readiness",
    "runtime",
    "authority",
    "production",
    "security",
    "certification",
    "certified",
    "turing",
    "agi",
    "consciousness",
    "sentience",
}

CLAIM_QUALIFIERS_V1 = {
    "claim",
    "claims",
    "claimed",
    "ready",
    "readiness",
    "safe",
    "safe-ready",
    "runtime",
    "authority",
    "certification",
    "certified",
    "production",
    "public",
}

PUBLIC_SAFE_MATURITIES_V1 = {"public_safe"}
RUNTIME_ALLOWED_MATURITIES_V1 = {"owner_approved_runtime", "pilot_limited", "public_safe"}
BLOCKED_AUTHORITY_MATURITIES_V1 = {"blocked_or_deprecated"}

FAMILY_NEXT_LANE_DEFAULTS_V1 = {
    "memory_and_context": "DESIGN_WESLR_MEMORY_ANSWER_FORMATION_BOUNDARY_V1",
    "artifact_and_code_generation": "DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1",
    "writer_and_provenance": "DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1",
    "poison_shield_and_authority": "DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1",
    "forecasting_and_scenarios": "DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1",
    "energy_grid_and_home_assistant": "DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1",
    "wifi_rf_and_privacy_sensitive_signals": "DESIGN_WESLR_PRIVACY_SENSITIVE_SIGNAL_PROCESSING_BOUNDARY_V1",
    "llm_provider_candidate_generation": "DESIGN_WESLR_GOVERNED_LLM_PROVIDER_ARTIFACT_GENERATION_BOUNDARY_V1",
    "tool_action_and_device_control": "DESIGN_WESLR_TOOL_USE_EXECUTOR_BOUNDARY_V1",
    "public_product_and_claims": "DESIGN_WESLR_PUBLIC_CLAIM_LIFECYCLE_TRACKER_V1",
    "operator_workflow": "DESIGN_WESLR_OWNER_OPERATOR_WORKFLOW_ENGINE_V1",
    "friction_and_behavior_packs": "DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1",
}

DEFAULT_SAFE_METADATA_V1 = {
    "metadata_only": True,
    "internal_only": True,
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CapabilityMaturityRecord:
    capability_id: str
    capability_name: str
    capability_family: str
    current_maturity: str
    current_authority: str
    implemented_files: list[str]
    design_docs: list[str]
    review_docs: list[str]
    test_files: list[str]
    latest_commit: str
    latest_judgment: str
    owner_approval_required: bool
    runtime_wiring_allowed: bool
    public_claim_allowed: bool
    data_sensitivity: str
    action_risk: str
    required_boundaries: list[str]
    missing_prerequisites: list[str]
    blocked_next_steps: list[str]
    recommended_next_lane: str
    rollback_or_reversal_path: str
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class CapabilityMaturityRegistry:
    registry_id: str
    registry_version: str
    created_from_commit: str
    capabilities: list[CapabilityMaturityRecord]
    capability_count: int
    maturity_counts: dict[str, int]
    authority_counts: dict[str, int]
    blocked_capabilities: list[str]
    runtime_allowed_capabilities: list[str]
    public_claim_allowed_capabilities: list[str]
    recommended_next_lanes: list[str]
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class CapabilityMaturitySummary:
    summary_type: str
    registry_id: str
    registry_version: str
    capability_count: int
    maturity_counts: dict[str, int]
    authority_counts: dict[str, int]
    blocked_capabilities: list[str]
    runtime_allowed_capabilities: list[str]
    public_claim_allowed_capabilities: list[str]
    recommended_next_lanes: list[str]
    family_counts: dict[str, int]


# ---------------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()


def _normalize_text(value: Any) -> str:
    return " ".join(_safe_text(value).split()).lower()


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        items = list(value.keys())
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        items = [value]
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _safe_text(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _unique_sorted(items: Iterable[str]) -> list[str]:
    return sorted(set(_safe_list(list(items))))


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        items = [_json_safe(item) for item in value]
        return sorted(items, key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return _safe_text(value)


def to_capability_maturity_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _collect_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            strings.extend(_collect_strings(key))
            strings.extend(_collect_strings(item))
        return strings
    if isinstance(value, (list, tuple, set)):
        for item in value:
            strings.extend(_collect_strings(item))
        return strings
    text = _safe_text(value)
    if text:
        strings.append(text)
    return strings


def _contains_forbidden_field(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if any(hint in key_text for hint in FORBIDDEN_FIELD_HINTS_V1):
                return key_text
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
    return ""


def _contains_forbidden_claim_marker(value: Any) -> bool:
    for text in _collect_strings(value):
        blob = _normalize_text(text)
        if any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1):
            return True
        if "agi" in blob and "claim" in blob:
            return True
        if "consciousness" in blob and "claim" in blob:
            return True
        if "sentience" in blob and "claim" in blob:
            return True
        if "turing" in blob and "claim" in blob:
            return True
        if "certification" in blob and ("claim" in blob or "certified" in blob):
            return True
        if "public" in blob and "readiness" in blob and "claim" in blob:
            return True
        if "runtime" in blob and "authority" in blob and "claim" in blob:
            return True
        if ".weslr" in blob and "write" in blob:
            return True
    return False


def _record_like(value: Any) -> CapabilityMaturityRecord:
    if isinstance(value, CapabilityMaturityRecord):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    safe_metadata = value.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    return CapabilityMaturityRecord(
        capability_id=_safe_text(value.get("capability_id")),
        capability_name=_safe_text(value.get("capability_name")),
        capability_family=_safe_text(value.get("capability_family")),
        current_maturity=_safe_text(value.get("current_maturity")),
        current_authority=_safe_text(value.get("current_authority")),
        implemented_files=_unique_sorted(value.get("implemented_files", [])),
        design_docs=_unique_sorted(value.get("design_docs", [])),
        review_docs=_unique_sorted(value.get("review_docs", [])),
        test_files=_unique_sorted(value.get("test_files", [])),
        latest_commit=_safe_text(value.get("latest_commit")),
        latest_judgment=_safe_text(value.get("latest_judgment")),
        owner_approval_required=_safe_bool(value.get("owner_approval_required")),
        runtime_wiring_allowed=_safe_bool(value.get("runtime_wiring_allowed")),
        public_claim_allowed=_safe_bool(value.get("public_claim_allowed")),
        data_sensitivity=_safe_text(value.get("data_sensitivity")),
        action_risk=_safe_text(value.get("action_risk")),
        required_boundaries=_unique_sorted(value.get("required_boundaries", [])),
        missing_prerequisites=_unique_sorted(value.get("missing_prerequisites", [])),
        blocked_next_steps=_unique_sorted(value.get("blocked_next_steps", [])),
        recommended_next_lane=_safe_text(value.get("recommended_next_lane")),
        rollback_or_reversal_path=_safe_text(value.get("rollback_or_reversal_path")),
        safe_metadata=dict(safe_metadata or {}),
    )


def _registry_like(value: Any) -> CapabilityMaturityRegistry:
    if isinstance(value, CapabilityMaturityRegistry):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    safe_metadata = value.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    return CapabilityMaturityRegistry(
        registry_id=_safe_text(value.get("registry_id")),
        registry_version=_safe_text(value.get("registry_version")),
        created_from_commit=_safe_text(value.get("created_from_commit")),
        capabilities=[_record_like(item) for item in value.get("capabilities", [])],
        capability_count=int(value.get("capability_count", len(value.get("capabilities", []))) or 0),
        maturity_counts={str(k): int(v) for k, v in dict(value.get("maturity_counts", {})).items()},
        authority_counts={str(k): int(v) for k, v in dict(value.get("authority_counts", {})).items()},
        blocked_capabilities=_unique_sorted(value.get("blocked_capabilities", [])),
        runtime_allowed_capabilities=_unique_sorted(value.get("runtime_allowed_capabilities", [])),
        public_claim_allowed_capabilities=_unique_sorted(value.get("public_claim_allowed_capabilities", [])),
        recommended_next_lanes=_unique_sorted(value.get("recommended_next_lanes", [])),
        safe_metadata=dict(safe_metadata or {}),
    )


def _baseline_authority_for_maturity(maturity: str) -> str:
    mapping = {
        "idea": "no_authority",
        "design_only": "no_authority",
        "reviewed_design": "proposal_only",
        "metadata_helper": "metadata_only",
        "dry_run": "dry_run_only",
        "sandboxed": "sandbox_create_only",
        "validated": "validation_only",
        "owner_approved_runtime": "owner_approved_action",
        "pilot_limited": "operator_approved_runtime",
        "public_safe": "public_release_authority",
        "blocked_or_deprecated": "blocked",
    }
    return mapping.get(maturity, "blocked")


def _allowed_authorities_for_maturity(maturity: str) -> set[str]:
    base = {
        "idea": {"no_authority", "metadata_only"},
        "design_only": {"no_authority", "metadata_only", "proposal_only"},
        "reviewed_design": {"proposal_only", "metadata_only", "no_authority"},
        "metadata_helper": {"metadata_only", "proposal_only"},
        "dry_run": {"dry_run_only", "validation_only"},
        "sandboxed": {"sandbox_create_only", "read_only", "validation_only"},
        "validated": {"validation_only", "read_only", "sandbox_create_only"},
        "owner_approved_runtime": {"owner_approved_action", "operator_approved_runtime"},
        "pilot_limited": {"owner_approved_action", "operator_approved_runtime"},
        "public_safe": {"public_release_authority", "operator_approved_runtime", "owner_approved_action"},
        "blocked_or_deprecated": {"blocked"},
    }
    return base.get(maturity, {"blocked"})


def _runtime_allowed_by_maturity(maturity: str) -> bool:
    return maturity in RUNTIME_ALLOWED_MATURITIES_V1


def _public_claim_allowed_by_maturity(maturity: str) -> bool:
    return maturity in PUBLIC_SAFE_MATURITIES_V1


def _is_design_only_maturity(maturity: str) -> bool:
    return maturity in {"idea", "design_only", "reviewed_design"}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_capability_maturity_record_v1(
    *,
    capability_id: str,
    capability_name: str,
    capability_family: str,
    current_maturity: str,
    current_authority: str | None = None,
    implemented_files: Iterable[str] | None = None,
    design_docs: Iterable[str] | None = None,
    review_docs: Iterable[str] | None = None,
    test_files: Iterable[str] | None = None,
    latest_commit: str = "",
    latest_judgment: str = "",
    owner_approval_required: bool = False,
    runtime_wiring_allowed: bool | None = None,
    public_claim_allowed: bool | None = None,
    data_sensitivity: str = "unknown",
    action_risk: str = "unknown",
    required_boundaries: Iterable[str] | None = None,
    missing_prerequisites: Iterable[str] | None = None,
    blocked_next_steps: Iterable[str] | None = None,
    recommended_next_lane: str = "",
    rollback_or_reversal_path: str = "",
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> CapabilityMaturityRecord:
    maturity = _safe_text(current_maturity)
    record = CapabilityMaturityRecord(
        capability_id=_safe_text(capability_id),
        capability_name=_safe_text(capability_name),
        capability_family=_safe_text(capability_family),
        current_maturity=maturity,
        current_authority=_safe_text(current_authority) if current_authority is not None else _baseline_authority_for_maturity(maturity),
        implemented_files=_unique_sorted(implemented_files or []),
        design_docs=_unique_sorted(design_docs or []),
        review_docs=_unique_sorted(review_docs or []),
        test_files=_unique_sorted(test_files or []),
        latest_commit=_safe_text(latest_commit),
        latest_judgment=_safe_text(latest_judgment),
        owner_approval_required=_safe_bool(owner_approval_required),
        runtime_wiring_allowed=_runtime_allowed_by_maturity(maturity) if runtime_wiring_allowed is None else _safe_bool(runtime_wiring_allowed),
        public_claim_allowed=_public_claim_allowed_by_maturity(maturity) if public_claim_allowed is None else _safe_bool(public_claim_allowed),
        data_sensitivity=_safe_text(data_sensitivity),
        action_risk=_safe_text(action_risk),
        required_boundaries=_unique_sorted(required_boundaries or []),
        missing_prerequisites=_unique_sorted(missing_prerequisites or []),
        blocked_next_steps=_unique_sorted(blocked_next_steps or []),
        recommended_next_lane=_safe_text(recommended_next_lane),
        rollback_or_reversal_path=_safe_text(rollback_or_reversal_path),
        safe_metadata={**DEFAULT_SAFE_METADATA_V1, **dict(safe_metadata or {}), **dict(extra_metadata)},
    )
    validate_capability_maturity_record_v1(record)
    return record


def build_capability_maturity_registry_v1(
    *,
    registry_id: str = HELPER_TYPE_V1,
    registry_version: str = "v1",
    created_from_commit: str = "static_reference_v1",
    capabilities: Iterable[Any] | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> CapabilityMaturityRegistry:
    records = [
        _record_like(item)
        for item in (capabilities if capabilities is not None else build_initial_capability_maturity_examples_v1())
    ]
    maturity_counts: dict[str, int] = {}
    authority_counts: dict[str, int] = {}
    blocked_capabilities: list[str] = []
    runtime_allowed_capabilities: list[str] = []
    public_claim_allowed_capabilities: list[str] = []
    recommended_next_lanes: list[str] = []
    for record in records:
        maturity_counts[record.current_maturity] = maturity_counts.get(record.current_maturity, 0) + 1
        authority_counts[record.current_authority] = authority_counts.get(record.current_authority, 0) + 1
        if record.current_authority == "blocked" or record.current_maturity == "blocked_or_deprecated":
            blocked_capabilities.append(record.capability_id)
        if record.runtime_wiring_allowed:
            runtime_allowed_capabilities.append(record.capability_id)
        if record.public_claim_allowed:
            public_claim_allowed_capabilities.append(record.capability_id)
        if record.recommended_next_lane:
            recommended_next_lanes.append(record.recommended_next_lane)
    registry = CapabilityMaturityRegistry(
        registry_id=_safe_text(registry_id),
        registry_version=_safe_text(registry_version),
        created_from_commit=_safe_text(created_from_commit),
        capabilities=records,
        capability_count=len(records),
        maturity_counts=dict(sorted(maturity_counts.items())),
        authority_counts=dict(sorted(authority_counts.items())),
        blocked_capabilities=_unique_sorted(blocked_capabilities),
        runtime_allowed_capabilities=_unique_sorted(runtime_allowed_capabilities),
        public_claim_allowed_capabilities=_unique_sorted(public_claim_allowed_capabilities),
        recommended_next_lanes=_unique_sorted(recommended_next_lanes),
        safe_metadata={**DEFAULT_SAFE_METADATA_V1, **dict(safe_metadata or {}), **dict(extra_metadata)},
    )
    validate_capability_maturity_registry_v1(registry)
    return registry


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_capability_maturity_record_v1(record: Any) -> bool:
    original = record if isinstance(record, Mapping) else asdict(record) if is_dataclass(record) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    normalized = _record_like(record)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.current_maturity not in ALLOWED_MATURITY_LEVELS_V1:
        raise ValidationError("unknown_maturity")
    if normalized.current_authority not in ALLOWED_AUTHORITY_STATES_V1:
        raise ValidationError("unknown_authority")
    if normalized.capability_family not in ALLOWED_CAPABILITY_FAMILIES_V1:
        raise ValidationError("unknown_family")
    if not normalized.capability_id:
        raise ValidationError("capability_id_required")
    if not normalized.capability_name:
        raise ValidationError("capability_name_required")
    if not normalized.latest_commit:
        raise ValidationError("latest_commit_required")
    if not normalized.latest_judgment:
        raise ValidationError("latest_judgment_required")
    if normalized.current_authority == "public_release_authority" and normalized.current_maturity != "public_safe":
        raise ValidationError("public_release_authority_requires_public_safe")
    if normalized.public_claim_allowed and not _public_claim_allowed_by_maturity(normalized.current_maturity):
        raise ValidationError("public_claim_allowed_must_be_false_for_non_public_safe")
    if normalized.runtime_wiring_allowed and not _runtime_allowed_by_maturity(normalized.current_maturity):
        raise ValidationError("runtime_wiring_allowed_must_be_false_for_non_owner_approved_maturity")
    if normalized.current_maturity in {"idea", "design_only", "reviewed_design"} and normalized.implemented_files:
        raise ValidationError("design_only_must_not_have_implemented_files")
    if normalized.current_maturity == "metadata_helper" and normalized.current_authority == "public_release_authority":
        raise ValidationError("metadata_helper_must_not_have_public_release_authority")
    if normalized.current_maturity == "dry_run" and normalized.current_authority == "owner_approved_action":
        raise ValidationError("dry_run_must_not_have_owner_approved_action")
    if normalized.current_maturity == "blocked_or_deprecated" and normalized.current_authority != "blocked":
        raise ValidationError("blocked_or_deprecated_must_use_blocked_authority")
    if normalized.current_authority not in _allowed_authorities_for_maturity(normalized.current_maturity):
        raise ValidationError("authority_not_allowed_for_maturity")
    return True


def validate_capability_maturity_registry_v1(registry: Any) -> bool:
    original = registry if isinstance(registry, Mapping) else asdict(registry) if is_dataclass(registry) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    normalized = _registry_like(registry)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.registry_id != HELPER_TYPE_V1 and not normalized.registry_id:
        raise ValidationError("registry_id_required")
    if not normalized.registry_version:
        raise ValidationError("registry_version_required")
    if not normalized.created_from_commit:
        raise ValidationError("created_from_commit_required")
    if normalized.capability_count != len(normalized.capabilities):
        raise ValidationError("capability_count_mismatch")
    seen_ids: set[str] = set()
    for record in normalized.capabilities:
        validate_capability_maturity_record_v1(record)
        if record.capability_id in seen_ids:
            raise ValidationError("duplicate_capability_id")
        seen_ids.add(record.capability_id)
    return True


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarize_capability_maturity_registry_v1(registry: Any) -> CapabilityMaturitySummary:
    normalized = _registry_like(registry)
    validate_capability_maturity_registry_v1(normalized)
    family_counts: dict[str, int] = {}
    for record in normalized.capabilities:
        family_counts[record.capability_family] = family_counts.get(record.capability_family, 0) + 1
    return CapabilityMaturitySummary(
        summary_type=SUMMARY_TYPE_V1,
        registry_id=normalized.registry_id,
        registry_version=normalized.registry_version,
        capability_count=normalized.capability_count,
        maturity_counts=dict(normalized.maturity_counts),
        authority_counts=dict(normalized.authority_counts),
        blocked_capabilities=list(normalized.blocked_capabilities),
        runtime_allowed_capabilities=list(normalized.runtime_allowed_capabilities),
        public_claim_allowed_capabilities=list(normalized.public_claim_allowed_capabilities),
        recommended_next_lanes=list(normalized.recommended_next_lanes),
        family_counts=dict(sorted(family_counts.items())),
    )


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def build_initial_capability_maturity_examples_v1() -> list[CapabilityMaturityRecord]:
    static_commit = "registry_static_reference_v1"
    examples = [
        build_capability_maturity_record_v1(
            capability_id="time_anchor_resolver",
            capability_name="Time Anchor Resolver",
            capability_family="memory_and_context",
            current_maturity="validated",
            current_authority="read_only",
            implemented_files=["weslr/time_anchor_resolver.py"],
            design_docs=["docs/WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1.md"],
            review_docs=["docs/WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1.md"],
            test_files=["weslr/tests/test_time_anchor_resolver_v1.py"],
            latest_commit=static_commit,
            latest_judgment="validated",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="low",
            action_risk="low",
            required_boundaries=["safe_memory_retrieval_executor"],
            missing_prerequisites=["memory_answer_formation_boundary"],
            blocked_next_steps=["public_claim", "runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_MEMORY_ANSWER_FORMATION_BOUNDARY_V1",
            rollback_or_reversal_path="disable consumer references and keep metadata-only use",
            safe_metadata={"example_name": "time_anchor_resolver"},
        ),
        build_capability_maturity_record_v1(
            capability_id="safe_memory_retrieval_executor",
            capability_name="Safe Memory Retrieval Executor",
            capability_family="memory_and_context",
            current_maturity="validated",
            current_authority="read_only",
            implemented_files=["weslr/safe_memory_retrieval_executor.py"],
            design_docs=["docs/WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1.md"],
            review_docs=["docs/WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1.md"],
            test_files=["weslr/tests/test_safe_memory_retrieval_executor_v1.py"],
            latest_commit=static_commit,
            latest_judgment="validated",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="low",
            action_risk="low",
            required_boundaries=["memory_source_scope_registry", "time_anchor_resolver"],
            missing_prerequisites=["memory_answer_formation_boundary"],
            blocked_next_steps=["public_claim", "runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_MEMORY_ANSWER_FORMATION_BOUNDARY_V1",
            rollback_or_reversal_path="keep as metadata-only executor",
            safe_metadata={"example_name": "safe_memory_retrieval_executor"},
        ),
        build_capability_maturity_record_v1(
            capability_id="poison_shield_helpers",
            capability_name="Poison Shield Helpers",
            capability_family="poison_shield_and_authority",
            current_maturity="validated",
            current_authority="read_only",
            implemented_files=["weslr/poison_shield.py"],
            design_docs=["docs/WESLR_POISON_SHIELD_ADVERSARIAL_CONTENT_QUARANTINE_AND_AUTHORITY_FIREWALL_V1.md"],
            review_docs=["docs/WESLR_POISON_SHIELD_ADVERSARIAL_CONTENT_QUARANTINE_AND_AUTHORITY_FIREWALL_REVIEW_V1.md"],
            test_files=["weslr/tests/test_poison_shield_v1.py"],
            latest_commit=static_commit,
            latest_judgment="validated",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="medium",
            required_boundaries=["source_scope", "authority_firewall"],
            missing_prerequisites=["source_evidence_graph"],
            blocked_next_steps=["public_claim", "runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1",
            rollback_or_reversal_path="keep external content as evidence-only",
            safe_metadata={"example_name": "poison_shield_helpers"},
        ),
        build_capability_maturity_record_v1(
            capability_id="project_brief_builder",
            capability_name="Project Brief Builder",
            capability_family="artifact_and_code_generation",
            current_maturity="validated",
            current_authority="read_only",
            implemented_files=["weslr/project_brief_builder.py"],
            design_docs=["docs/WESLR_IMPLEMENTATION_INVENTORY_AND_ARCHITECTURE_MAP_V1.md"],
            review_docs=["docs/WESLR_IMPLEMENTATION_INVENTORY_AND_ARCHITECTURE_MAP_V1.md"],
            test_files=["weslr/tests/test_project_brief_builder_v1.py"],
            latest_commit=static_commit,
            latest_judgment="validated",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="low",
            action_risk="low",
            required_boundaries=["maturity_registry"],
            missing_prerequisites=["code_validation_runner"],
            blocked_next_steps=["runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1",
            rollback_or_reversal_path="retain as planning-only surface",
            safe_metadata={"example_name": "project_brief_builder"},
        ),
        build_capability_maturity_record_v1(
            capability_id="code_scaffold_generator",
            capability_name="Code Scaffold Generator",
            capability_family="artifact_and_code_generation",
            current_maturity="validated",
            current_authority="validation_only",
            implemented_files=["weslr/code_scaffold_generator.py"],
            design_docs=["docs/WESLR_IMPLEMENTATION_INVENTORY_AND_ARCHITECTURE_MAP_V1.md"],
            review_docs=["docs/WESLR_IMPLEMENTATION_INVENTORY_AND_ARCHITECTURE_MAP_V1.md"],
            test_files=["weslr/tests/test_code_scaffold_generator_v1.py"],
            latest_commit=static_commit,
            latest_judgment="validated",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="low",
            action_risk="low",
            required_boundaries=["artifact_writer_boundary"],
            missing_prerequisites=["code_validation_runner"],
            blocked_next_steps=["runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1",
            rollback_or_reversal_path="keep generated scaffolds as drafts",
            safe_metadata={"example_name": "code_scaffold_generator"},
        ),
        build_capability_maturity_record_v1(
            capability_id="artifact_writer_boundary",
            capability_name="Artifact Writer Boundary",
            capability_family="writer_and_provenance",
            current_maturity="validated",
            current_authority="sandbox_create_only",
            implemented_files=["weslr/artifact_writer_boundary.py"],
            design_docs=["docs/WESLR_IMPLEMENTATION_INVENTORY_AND_ARCHITECTURE_MAP_V1.md"],
            review_docs=["docs/WESLR_IMPLEMENTATION_INVENTORY_AND_ARCHITECTURE_MAP_V1.md"],
            test_files=["weslr/tests/test_artifact_writer_boundary_v1.py"],
            latest_commit=static_commit,
            latest_judgment="validated",
            owner_approval_required=True,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="medium",
            required_boundaries=["artifact_provenance_boundary"],
            missing_prerequisites=["patch_feedback_loop", "artifact_exporter"],
            blocked_next_steps=["runtime_authority", "public_claim"],
            recommended_next_lane="DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1",
            rollback_or_reversal_path="dry-run only and revertable",
            safe_metadata={"example_name": "artifact_writer_boundary"},
        ),
        build_capability_maturity_record_v1(
            capability_id="sandbox_artifact_writer_dry_run_executor",
            capability_name="Sandbox Artifact Writer Dry-Run Executor",
            capability_family="writer_and_provenance",
            current_maturity="dry_run",
            current_authority="dry_run_only",
            implemented_files=["weslr/sandbox_artifact_writer_executor.py"],
            design_docs=["docs/WESLR_NATIVE_ARTIFACT_AND_CODE_GENERATION_DOCTRINE_V1.md"],
            review_docs=["docs/WESLR_NATIVE_ARTIFACT_AND_CODE_GENERATION_DOCTRINE_V1.md"],
            test_files=["weslr/tests/test_sandbox_artifact_writer_executor_v1.py"],
            latest_commit=static_commit,
            latest_judgment="validated",
            owner_approval_required=True,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="medium",
            required_boundaries=["artifact_writer_boundary", "artifact_provenance_boundary"],
            missing_prerequisites=["real_sandbox_create_executor"],
            blocked_next_steps=["runtime_authority", "public_claim"],
            recommended_next_lane="DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1",
            rollback_or_reversal_path="remain dry-run only",
            safe_metadata={"example_name": "sandbox_artifact_writer_dry_run_executor"},
        ),
        build_capability_maturity_record_v1(
            capability_id="artifact_provenance_boundary",
            capability_name="Artifact Provenance Boundary",
            capability_family="writer_and_provenance",
            current_maturity="validated",
            current_authority="validation_only",
            implemented_files=["weslr/artifact_provenance_boundary.py"],
            design_docs=["docs/WESLR_IMPLEMENTATION_INVENTORY_AND_ARCHITECTURE_MAP_V1.md"],
            review_docs=["docs/WESLR_IMPLEMENTATION_INVENTORY_AND_ARCHITECTURE_MAP_V1.md"],
            test_files=["weslr/tests/test_artifact_provenance_boundary_v1.py"],
            latest_commit=static_commit,
            latest_judgment="validated",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="low",
            required_boundaries=["source_evidence_graph"],
            missing_prerequisites=["source_evidence_graph"],
            blocked_next_steps=["runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1",
            rollback_or_reversal_path="retain provenance metadata only",
            safe_metadata={"example_name": "artifact_provenance_boundary"},
        ),
        build_capability_maturity_record_v1(
            capability_id="future_state_forecasting_engine",
            capability_name="Future-State Forecasting Engine",
            capability_family="forecasting_and_scenarios",
            current_maturity="reviewed_design",
            current_authority="proposal_only",
            implemented_files=[],
            design_docs=["docs/WESLR_FUTURE_STATE_FORECASTING_ENGINE_V1.md"],
            review_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="design_ready_for_scenario_simulation_design",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="medium",
            required_boundaries=["signal_provenance_freshness_model", "energy_signal_conflict_resolution_policy"],
            missing_prerequisites=["forecast_error_ledger"],
            blocked_next_steps=["runtime_authority", "public_claim"],
            recommended_next_lane="DESIGN_WESLR_SCENARIO_SIMULATION_ENGINE_V1",
            rollback_or_reversal_path="keep as design-only reasoning layer",
            safe_metadata={"example_name": "future_state_forecasting_engine"},
        ),
        build_capability_maturity_record_v1(
            capability_id="scenario_simulation_engine",
            capability_name="Scenario Simulation Engine",
            capability_family="forecasting_and_scenarios",
            current_maturity="reviewed_design",
            current_authority="proposal_only",
            implemented_files=[],
            design_docs=["docs/WESLR_SCENARIO_SIMULATION_ENGINE_V1.md"],
            review_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="design_ready_for_energy_grid_signal_intelligence_design",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="medium",
            required_boundaries=["forecasting_engine", "energy_signal_conflict_resolution_policy"],
            missing_prerequisites=["forecast_error_ledger"],
            blocked_next_steps=["runtime_authority", "public_claim"],
            recommended_next_lane="DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1",
            rollback_or_reversal_path="keep as scenario-only reasoning layer",
            safe_metadata={"example_name": "scenario_simulation_engine"},
        ),
        build_capability_maturity_record_v1(
            capability_id="home_assistant_signal_intake_boundary",
            capability_name="Home Assistant Signal Intake Boundary",
            capability_family="energy_grid_and_home_assistant",
            current_maturity="reviewed_design",
            current_authority="proposal_only",
            implemented_files=[],
            design_docs=["docs/WESLR_HOME_ASSISTANT_SIGNAL_INTAKE_BOUNDARY_V1.md"],
            review_docs=["docs/WESLR_HOME_ASSISTANT_SIGNAL_INTAKE_BOUNDARY_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="design_ready_for_energy_grid_signal_intelligence_design",
            owner_approval_required=True,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="high",
            action_risk="high",
            required_boundaries=["poison_shield_and_authority", "source_scope"],
            missing_prerequisites=["home_assistant_read_only_connector_boundary"],
            blocked_next_steps=["runtime_authority", "device_control"],
            recommended_next_lane="DESIGN_WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1",
            rollback_or_reversal_path="read-only boundary only",
            safe_metadata={"example_name": "home_assistant_signal_intake_boundary"},
        ),
        build_capability_maturity_record_v1(
            capability_id="signal_provenance_freshness_model",
            capability_name="Signal Provenance and Source Freshness Model",
            capability_family="energy_grid_and_home_assistant",
            current_maturity="validated",
            current_authority="read_only",
            implemented_files=["weslr/signal_provenance_freshness_model.py"],
            design_docs=["docs/WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1.md"],
            review_docs=["docs/WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1.md"],
            test_files=["weslr/tests/test_signal_provenance_freshness_model_v1.py"],
            latest_commit=static_commit,
            latest_judgment="ready_for_energy_signal_conflict_policy",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="medium",
            required_boundaries=["poison_shield_and_authority", "forecasting_and_scenarios"],
            missing_prerequisites=["energy_signal_conflict_resolution_policy"],
            blocked_next_steps=["runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1",
            rollback_or_reversal_path="metadata-only evidence path",
            safe_metadata={"example_name": "signal_provenance_freshness_model"},
        ),
        build_capability_maturity_record_v1(
            capability_id="energy_signal_conflict_resolution_policy",
            capability_name="Energy Signal Conflict Resolution Policy",
            capability_family="energy_grid_and_home_assistant",
            current_maturity="reviewed_design",
            current_authority="proposal_only",
            implemented_files=[],
            design_docs=["docs/WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1.md"],
            review_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="ready_for_energy_grid_signal_intelligence_design",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="medium",
            required_boundaries=["signal_provenance_freshness_model"],
            missing_prerequisites=["energy_grid_signal_intelligence"],
            blocked_next_steps=["runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1",
            rollback_or_reversal_path="policy-only no-control path",
            safe_metadata={"example_name": "energy_signal_conflict_resolution_policy"},
        ),
        build_capability_maturity_record_v1(
            capability_id="energy_grid_signal_intelligence",
            capability_name="Energy Grid Signal Intelligence",
            capability_family="energy_grid_and_home_assistant",
            current_maturity="design_only",
            current_authority="proposal_only",
            implemented_files=[],
            design_docs=["docs/WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1.md"],
            review_docs=["docs/WESLR_ENERGY_GRID_SIGNAL_INTELLIGENCE_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="design_ready_for_forecast_error_ledger",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="high",
            action_risk="high",
            required_boundaries=["home_assistant_signal_intake_boundary", "energy_signal_conflict_resolution_policy"],
            missing_prerequisites=["forecast_error_ledger"],
            blocked_next_steps=["runtime_authority", "device_control"],
            recommended_next_lane="DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1",
            rollback_or_reversal_path="keep recommendation-only",
            safe_metadata={"example_name": "energy_grid_signal_intelligence"},
        ),
        build_capability_maturity_record_v1(
            capability_id="forecast_error_ledger",
            capability_name="Forecast Error Ledger",
            capability_family="friction_and_behavior_packs",
            current_maturity="reviewed_design",
            current_authority="metadata_only",
            implemented_files=[],
            design_docs=["docs/WESLR_FORECAST_ERROR_LEDGER_V1.md"],
            review_docs=["docs/WESLR_FORECAST_ERROR_LEDGER_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="design_ready_for_capability_maturity_registry",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="medium",
            required_boundaries=["forecasting_and_scenarios"],
            missing_prerequisites=["capability_maturity_registry"],
            blocked_next_steps=["runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_CAPABILITY_MATURITY_REGISTRY_V1",
            rollback_or_reversal_path="metadata-only lessons ledger",
            safe_metadata={"example_name": "forecast_error_ledger"},
        ),
        build_capability_maturity_record_v1(
            capability_id="wifi_rf_sensing_program",
            capability_name="WiFi/RF Sensing Program",
            capability_family="wifi_rf_and_privacy_sensitive_signals",
            current_maturity="idea",
            current_authority="no_authority",
            implemented_files=[],
            design_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            review_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="research_program_only",
            owner_approval_required=True,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="very_high",
            action_risk="high",
            required_boundaries=["privacy_sensitive_signal_processing_boundary"],
            missing_prerequisites=["consent_model", "synthetic_data_policy"],
            blocked_next_steps=["runtime_authority", "public_claim"],
            recommended_next_lane="DESIGN_WESLR_PRIVACY_SENSITIVE_SIGNAL_PROCESSING_BOUNDARY_V1",
            rollback_or_reversal_path="research-only, no covert tracking",
            safe_metadata={"example_name": "wifi_rf_sensing_program"},
        ),
        build_capability_maturity_record_v1(
            capability_id="governed_llm_provider_boundary",
            capability_name="Governed LLM Provider Boundary",
            capability_family="llm_provider_candidate_generation",
            current_maturity="idea",
            current_authority="no_authority",
            implemented_files=[],
            design_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            review_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="deferred_until_poison_shield_and_provenance_complete",
            owner_approval_required=True,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="high",
            required_boundaries=["poison_shield_and_authority", "artifact_and_code_generation", "writer_and_provenance"],
            missing_prerequisites=["code_validation_runner", "source_evidence_graph", "final_answer_assembly_boundary"],
            blocked_next_steps=["runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_GOVERNED_LLM_PROVIDER_ARTIFACT_GENERATION_BOUNDARY_V1",
            rollback_or_reversal_path="candidate-only, no authority",
            safe_metadata={"example_name": "governed_llm_provider_boundary"},
        ),
        build_capability_maturity_record_v1(
            capability_id="code_validation_runner",
            capability_name="Code Validation Runner",
            capability_family="artifact_and_code_generation",
            current_maturity="idea",
            current_authority="no_authority",
            implemented_files=[],
            design_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            review_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="missing_core_bridge",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="low",
            action_risk="low",
            required_boundaries=["artifact_writer_boundary", "artifact_provenance_boundary"],
            missing_prerequisites=["patch_feedback_loop", "artifact_exporter"],
            blocked_next_steps=["runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1",
            rollback_or_reversal_path="validation-only",
            safe_metadata={"example_name": "code_validation_runner"},
        ),
        build_capability_maturity_record_v1(
            capability_id="source_evidence_graph",
            capability_name="Source Evidence Graph",
            capability_family="writer_and_provenance",
            current_maturity="idea",
            current_authority="metadata_only",
            implemented_files=[],
            design_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            review_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="missing_core_bridge",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="medium",
            action_risk="medium",
            required_boundaries=["artifact_provenance_boundary", "poison_shield_and_authority"],
            missing_prerequisites=["maturity_registry"],
            blocked_next_steps=["runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1",
            rollback_or_reversal_path="evidence-only graph",
            safe_metadata={"example_name": "source_evidence_graph"},
        ),
        build_capability_maturity_record_v1(
            capability_id="public_claim_lifecycle_tracker",
            capability_name="Public Claim Lifecycle Tracker",
            capability_family="public_product_and_claims",
            current_maturity="blocked_or_deprecated",
            current_authority="blocked",
            implemented_files=[],
            design_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            review_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="blocked_until_claim_policy_exists",
            owner_approval_required=True,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="high",
            action_risk="high",
            required_boundaries=["poison_shield_and_authority"],
            missing_prerequisites=["public_claim_policy", "source_evidence_graph"],
            blocked_next_steps=["public_claim", "runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1",
            rollback_or_reversal_path="blocked until claim lifecycle exists",
            safe_metadata={"example_name": "public_claim_lifecycle_tracker"},
        ),
        build_capability_maturity_record_v1(
            capability_id="owner_operator_workflow_engine",
            capability_name="Owner Operator Workflow Engine",
            capability_family="operator_workflow",
            current_maturity="idea",
            current_authority="no_authority",
            implemented_files=[],
            design_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            review_docs=["docs/WESLR_WHOLE_SYSTEM_UNKNOWN_ENGINE_ARCHITECTURE_FRICTION_AUDIT_V1.md"],
            test_files=[],
            latest_commit=static_commit,
            latest_judgment="recommended_for_approval_burden_reduction",
            owner_approval_required=False,
            runtime_wiring_allowed=False,
            public_claim_allowed=False,
            data_sensitivity="low",
            action_risk="low",
            required_boundaries=["maturity_registry"],
            missing_prerequisites=["capability_maturity_registry"],
            blocked_next_steps=["runtime_authority"],
            recommended_next_lane="DESIGN_WESLR_OWNER_OPERATOR_WORKFLOW_ENGINE_V1",
            rollback_or_reversal_path="proposal-only workflow",
            safe_metadata={"example_name": "owner_operator_workflow_engine"},
        ),
    ]
    return examples
