"""ARC official-public parse adapter shape using dummy/no-data fixtures only.

This lane intentionally rejects real official/public source bundles. It only
parses a local dummy/no-data fixture so the future surface can be exercised
without touching official ARC data.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION_V1 = "arc_official_public_data_adapter_v1"
DUMMY_SOURCE_KIND_V1 = "dummy_no_data_fixture_v1"
DUMMY_APPROVED_PHASE_V1 = "phase_2_public_parse_scorer_validation"
DUMMY_FIXTURE_RELATIVE_PATH_V1 = Path("weslr/tests/fixtures/arc_official_public_dummy_no_data_v1.json")
ALLOWED_PACKET_KEYS_V1 = (
    "task_id",
    "anonymized_task_id",
    "train_pairs",
    "test_inputs",
    "required_output_count",
    "format_metadata",
    "parse_status",
    "source_kind",
    "packet_metadata",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _dummy_fixture_path() -> Path:
    return _repo_root() / DUMMY_FIXTURE_RELATIVE_PATH_V1


def _safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_safe(item) for item in value]
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, set):
        return [_safe(item) for item in sorted(value, key=repr)]
    return str(value)


def _checksum_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture_checksum() -> str:
    return _checksum_bytes(_dummy_fixture_path().read_bytes())


def build_arc_official_public_dummy_approval_manifest_v1(*, source_version_or_snapshot: str = "dummy-no-data-v1") -> dict[str, Any]:
    fixture_path = _dummy_fixture_path()
    return {
        "owner_approved": True,
        "approval_reference": "dummy-public-parse-scorer-0001",
        "approved_phase": DUMMY_APPROVED_PHASE_V1,
        "source_kind": DUMMY_SOURCE_KIND_V1,
        "source_location": str(DUMMY_FIXTURE_RELATIVE_PATH_V1),
        "source_version_or_snapshot": source_version_or_snapshot,
        "checksum": _fixture_checksum(),
        "read_only_required": True,
        "offline_required": True,
        "no_hidden_private_data": True,
        "no_network_fetch": True,
        "no_mutation_in_place": True,
        "dummy_no_data": True,
        "approved_scope": {
            "scope": "dummy-no-data-public-parse-scorer-shape",
            "fixture_only": True,
            "source_location": str(fixture_path),
        },
        "claim_policy": {
            "official_score_claimable": False,
            "official_percentage_claimable": "none/0",
            "synthetic_official_score_mixing": False,
            "competition_submission_authority": False,
        },
    }


def validate_arc_official_public_dummy_approval_manifest_v1(manifest: Any) -> dict[str, Any]:
    data = manifest if isinstance(manifest, Mapping) else {}
    if not data:
        raise ValueError("Invalid approval manifest")
    issues: list[str] = []
    if data.get("owner_approved") is not True:
        issues.append("owner_not_approved")
    if str(data.get("approval_reference", "")).strip() == "":
        issues.append("missing_approval_reference")
    if str(data.get("approved_phase", "")).strip() != DUMMY_APPROVED_PHASE_V1:
        issues.append("unsupported_approved_phase")
    if str(data.get("source_kind", "")).strip() != DUMMY_SOURCE_KIND_V1:
        issues.append("unsupported_source_kind")
    if str(data.get("source_location", "")).strip() != str(DUMMY_FIXTURE_RELATIVE_PATH_V1):
        issues.append("source_location_must_point_to_dummy_fixture")
    if str(data.get("source_version_or_snapshot", "")).strip() == "":
        issues.append("missing_source_version_or_snapshot")
    checksum = str(data.get("checksum", "")).strip()
    if checksum == "":
        issues.append("missing_checksum")
    elif checksum != _fixture_checksum():
        issues.append("checksum_mismatch")
    if data.get("read_only_required") is not True:
        issues.append("missing_read_only_requirement")
    if data.get("offline_required") is not True:
        issues.append("missing_offline_requirement")
    if data.get("no_hidden_private_data") is not True:
        issues.append("missing_no_hidden_private_data")
    if data.get("no_network_fetch") is not True:
        issues.append("missing_no_network_fetch")
    if data.get("no_mutation_in_place") is not True:
        issues.append("missing_no_mutation_in_place")
    approved_scope = data.get("approved_scope") if isinstance(data.get("approved_scope"), Mapping) else {}
    if not approved_scope:
        issues.append("missing_approved_scope")
    claim_policy = data.get("claim_policy") if isinstance(data.get("claim_policy"), Mapping) else {}
    if not claim_policy:
        issues.append("missing_claim_policy")
    if claim_policy.get("official_score_claimable") is not False:
        issues.append("official_score_claimable_must_be_false")
    if str(claim_policy.get("official_percentage_claimable", "")).strip().lower() not in {"none/0", "none", "0", "not claimable"}:
        issues.append("official_percentage_claimable_must_remain_none_zero")
    if claim_policy.get("synthetic_official_score_mixing") is not False:
        issues.append("synthetic_official_score_mixing_must_be_false")
    if claim_policy.get("competition_submission_authority") is not False:
        issues.append("competition_submission_authority_must_be_false")
    if data.get("official_data_class") == "public_official_arc":
        issues.append("synthetic_as_official_claim")
    if data.get("dummy_no_data") is not True:
        issues.append("missing_dummy_no_data_marker")
    if issues:
        raise ValueError(f"Invalid approval manifest: {sorted(set(issues))}")
    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "owner_approved": True,
        "approval_reference": str(data.get("approval_reference")),
        "approved_phase": DUMMY_APPROVED_PHASE_V1,
        "source_kind": DUMMY_SOURCE_KIND_V1,
        "source_location": str(DUMMY_FIXTURE_RELATIVE_PATH_V1),
        "source_version_or_snapshot": str(data.get("source_version_or_snapshot")),
        "checksum": checksum,
        "approved_scope": deepcopy(approved_scope),
        "claim_policy": deepcopy(claim_policy),
        "official_percentage_claimable_value": 0,
        "dummy_no_data": True,
    }


def reject_official_public_source_path_v1(source_path: Any) -> dict[str, Any]:
    path = Path(str(source_path)) if source_path is not None else None
    if path is None:
        raise PermissionError("Official/public source path cannot be opened in this lane")
    allowed = _dummy_fixture_path().resolve()
    if path.resolve() != allowed:
        raise PermissionError("Official/public source path cannot be opened in this lane")
    return {"valid": True, "source_path": str(path)}


def open_dummy_fixture_source_path_v1(source_path: Any) -> str:
    reject_official_public_source_path_v1(source_path)
    return _dummy_fixture_path().read_text(encoding="utf-8")


def _validate_dummy_fixture_structure(data: Mapping[str, Any]) -> None:
    if data.get("dummy_no_data") is not True:
        raise ValueError("Dummy fixture marker missing")
    if data.get("source_kind") != DUMMY_SOURCE_KIND_V1:
        raise ValueError("Dummy fixture source kind mismatch")
    tasks = data.get("tasks") if isinstance(data.get("tasks"), list) else []
    if not tasks:
        raise ValueError("Dummy fixture has no tasks")


def _task_to_solver_packet(task: Mapping[str, Any], *, task_index: int) -> dict[str, Any]:
    train_pairs = []
    for pair_index, pair in enumerate(task.get("train_pairs", []) if isinstance(task.get("train_pairs"), list) else []):
        train_pairs.append(
            {
                "pair_id": f"p{pair_index}",
                "input_grid": deepcopy(pair.get("input_grid", [])),
                "output_grid": deepcopy(pair.get("output_grid", [])),
            }
        )
    test_inputs = []
    for test_index, test in enumerate(task.get("test_inputs", []) if isinstance(task.get("test_inputs"), list) else []):
        test_inputs.append(
            {
                "test_input_index": test_index,
                "input_grid": deepcopy(test.get("input_grid", [])),
            }
        )
    return {
        "task_id": f"anon_dummy_{task_index:03d}",
        "anonymized_task_id": f"anon_dummy_{task_index:03d}",
        "train_pairs": train_pairs,
        "test_inputs": test_inputs,
        "required_output_count": 2,
        "format_metadata": {
            "format_id": "arc_grid_v1",
            "json_safe": True,
            "offline_only": True,
        },
        "parse_status": "parsed",
        "source_kind": DUMMY_SOURCE_KIND_V1,
        "packet_metadata": {
            "task_index": task_index,
            "dummy_no_data": True,
            "solver_visible": True,
        },
    }


def _task_to_reference_record(task: Mapping[str, Any], *, task_index: int) -> dict[str, Any]:
    reference_outputs = task.get("reference_outputs", []) if isinstance(task.get("reference_outputs"), list) else []
    output_grid = reference_outputs[0].get("output_grid", []) if reference_outputs else []
    return {
        "task_id": f"anon_dummy_{task_index:03d}",
        "reference_output": deepcopy(output_grid),
        "reference_shape": {
            "height": len(output_grid) if isinstance(output_grid, list) else 0,
            "width": len(output_grid[0]) if isinstance(output_grid, list) and output_grid else 0,
        },
        "packet_metadata": {
            "task_index": task_index,
            "dummy_no_data": True,
            "scorer_visible": True,
        },
    }


def load_arc_official_public_dummy_no_data_bundle_v1(*, manifest: Any | None = None) -> dict[str, Any]:
    approval_manifest = build_arc_official_public_dummy_approval_manifest_v1() if manifest is None else manifest
    validated_manifest = validate_arc_official_public_dummy_approval_manifest_v1(approval_manifest)
    fixture_data = json.loads(open_dummy_fixture_source_path_v1(_dummy_fixture_path()))
    _validate_dummy_fixture_structure(fixture_data)
    tasks = fixture_data.get("tasks", []) if isinstance(fixture_data.get("tasks"), list) else []
    solver_visible_tasks = []
    reference_tasks = []
    for task_index, task in enumerate(tasks):
        solver_visible_tasks.append(_task_to_solver_packet(task, task_index=task_index))
        reference_tasks.append(_task_to_reference_record(task, task_index=task_index))
    bundle = {
        "schema_version": SCHEMA_VERSION_V1,
        "synthetic_only": True,
        "official_data_touched": False,
        "public_data_touched": False,
        "network_touched": False,
        "dummy_no_data": True,
        "approval_manifest": validated_manifest,
        "source_descriptor": {
            "source_kind": DUMMY_SOURCE_KIND_V1,
            "source_location": str(DUMMY_FIXTURE_RELATIVE_PATH_V1),
            "source_version_or_snapshot": validated_manifest["source_version_or_snapshot"],
            "checksum": validated_manifest["checksum"],
        },
        "task_count": len(solver_visible_tasks),
        "anonymized_task_ids": [task["anonymized_task_id"] for task in solver_visible_tasks],
        "solver_visible_tasks": solver_visible_tasks,
        "scorer_reference_tasks": reference_tasks,
        "source_checksum": validated_manifest["checksum"],
    }
    return bundle


def validate_solver_visible_packet_v1(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        raise ValueError("Solver-visible packet must be a mapping")
    allowed = set(ALLOWED_PACKET_KEYS_V1)
    present = set(packet.keys())
    if not {"task_id", "anonymized_task_id", "train_pairs", "test_inputs", "required_output_count", "format_metadata", "parse_status", "source_kind", "packet_metadata"}.issubset(present):
        raise ValueError("Solver-visible packet missing required fields")
    forbidden = present - allowed
    if forbidden:
        raise ValueError(f"Solver-visible packet has forbidden fields: {sorted(forbidden)}")
    if packet.get("required_output_count") != 2:
        raise ValueError("Solver-visible packet must require exactly two outputs")
    text = json.dumps(_safe(packet), ensure_ascii=False).lower()
    for token in ("expected_output", "reference_output", "latent_rule", "answer_descriptor", "toy_task_type", "family_id", "variant", "source_task_id"):
        if token in text:
            raise ValueError(f"Forbidden token leaked to solver-visible packet: {token}")
    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "anonymized_task_id": str(packet.get("anonymized_task_id")),
        "required_output_count": int(packet.get("required_output_count", 0)),
        "train_pair_count": len(packet.get("train_pairs", [])) if isinstance(packet.get("train_pairs"), list) else 0,
        "test_input_count": len(packet.get("test_inputs", [])) if isinstance(packet.get("test_inputs"), list) else 0,
    }


__all__ = [
    "ALLOWED_PACKET_KEYS_V1",
    "DUMMY_APPROVED_PHASE_V1",
    "DUMMY_FIXTURE_RELATIVE_PATH_V1",
    "DUMMY_SOURCE_KIND_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_official_public_dummy_approval_manifest_v1",
    "load_arc_official_public_dummy_no_data_bundle_v1",
    "open_dummy_fixture_source_path_v1",
    "reject_official_public_source_path_v1",
    "validate_arc_official_public_dummy_approval_manifest_v1",
    "validate_solver_visible_packet_v1",
]
