"""Tests for the ARC-AGI-2 public-data approval manifest template."""

from __future__ import annotations

import builtins
import json
from pathlib import Path

import pytest

from weslr.arc_agi2_public_data_approval_manifest import (
    build_arc_agi2_public_data_approval_manifest_template_v1,
    validate_arc_agi2_public_data_approval_manifest_v1,
)


TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "config" / "arc_agi2_public_data_approval_manifest.template.json"


@pytest.fixture()
def template_manifest() -> dict[str, object]:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def owner_approved_manifest(template_manifest: dict[str, object]) -> dict[str, object]:
    manifest = dict(template_manifest)
    manifest.update(
        {
            "approval_id": "approval-2026-07-04-a",
            "approved_by_owner": True,
            "approval_timestamp": "2026-07-04T14:20:00+02:00",
            "source_type": "public_official_read_only_bundle",
            "source_location_local_path": "/synthetic/public/arc-agi2-read-only",
            "source_origin": "kaggle_announcement",
            "source_download_method": "manual_read_only_download",
            "source_version_or_snapshot": "arc-agi2-public-snapshot-2026-07-04",
            "checksum_value": "sha256:dummy-checksum-arc-agi2-0001",
            "allowed_operations": ["inspect_metadata_only", "manifest_validation", "checksum_verify"],
            "forbidden_operations": [
                "download_source",
                "open_official_task_json",
                "parse_official_task_json",
                "run_solver_on_official_data",
                "score_official_data",
                "submit_to_kaggle",
                "publish_score_claim",
                "use_network",
                "use_provider_api",
            ],
        }
    )
    return manifest


class TestArcAgi2PublicDataApprovalManifestTemplate:
    def test_template_has_safe_defaults_and_metadata_only_policies(self, template_manifest: dict[str, object]) -> None:
        assert template_manifest["approved_by_owner"] is False
        assert template_manifest["hidden_private_data_included"] is False
        assert template_manifest["read_only_required"] is True
        assert template_manifest["offline_required"] is True
        assert template_manifest["no_network_required"] is True
        assert template_manifest["official_score_claim_allowed"] is False
        assert template_manifest["kaggle_submission_allowed"] is False
        assert template_manifest["approved_phase"] == "public_parse_only"
        assert template_manifest["source_descriptor"]["metadata_only"] is True
        assert template_manifest["policy_notes"]["read_only_bundle_policy"].startswith("the approved source bundle")

    def test_missing_owner_approval_fails(self, template_manifest: dict[str, object]) -> None:
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_approval_manifest_v1(template_manifest)

    def test_missing_checksum_fails(self, owner_approved_manifest: dict[str, object]) -> None:
        owner_approved_manifest["checksum_value"] = ""
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_approval_manifest_v1(owner_approved_manifest)

    def test_hidden_private_included_fails(self, owner_approved_manifest: dict[str, object]) -> None:
        owner_approved_manifest["hidden_private_data_included"] = True
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_approval_manifest_v1(owner_approved_manifest)

    def test_network_required_source_fails(self, owner_approved_manifest: dict[str, object]) -> None:
        owner_approved_manifest["no_network_required"] = False
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_approval_manifest_v1(owner_approved_manifest)

    def test_official_score_claim_allowed_fails(self, owner_approved_manifest: dict[str, object]) -> None:
        owner_approved_manifest["official_score_claim_allowed"] = True
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_approval_manifest_v1(owner_approved_manifest)

    def test_kaggle_submission_allowed_fails(self, owner_approved_manifest: dict[str, object]) -> None:
        owner_approved_manifest["kaggle_submission_allowed"] = True
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_approval_manifest_v1(owner_approved_manifest)

    def test_public_parse_only_approval_passes_with_safe_fields(self, owner_approved_manifest: dict[str, object]) -> None:
        result = validate_arc_agi2_public_data_approval_manifest_v1(owner_approved_manifest)
        assert result["valid"] is True
        assert result["approved_by_owner"] is True
        assert result["approved_phase"] == "public_parse_only"
        assert result["read_only_required"] is True
        assert result["offline_required"] is True
        assert result["no_network_required"] is True
        assert result["official_score_claim_allowed"] is False
        assert result["kaggle_submission_allowed"] is False
        assert result["source_descriptor"]["metadata_only"] is True

    def test_manifest_validation_does_not_touch_real_arc_data(self, owner_approved_manifest: dict[str, object]) -> None:
        opened: list[str] = []

        def fake_open(*args, **kwargs):
            opened.append(str(args[0]) if args else "")
            raise AssertionError("manifest validation should not open files")

        original_open = builtins.open
        builtins.open = fake_open
        try:
            result = validate_arc_agi2_public_data_approval_manifest_v1(owner_approved_manifest)
        finally:
            builtins.open = original_open
        assert opened == []
        assert result["valid"] is True

    def test_builder_matches_template_shape(self) -> None:
        built = build_arc_agi2_public_data_approval_manifest_template_v1()
        assert built["competition_name"] == "ARC-AGI-2"
        assert built["approved_by_owner"] is False
        assert built["official_score_claim_allowed"] is False
        assert built["kaggle_submission_allowed"] is False
