"""Tests for the ARC-AGI-2 public-data approval manifest template."""

from __future__ import annotations

import builtins
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

from weslr.arc_agi2_public_data_approval_manifest import (
    build_arc_agi2_public_data_approval_manifest_template_v1,
    validate_arc_agi2_public_data_approval_manifest_v1,
    validate_arc_agi2_public_data_source_instance_metadata_v1,
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
        }
    )
    return manifest


def _make_instance_manifest(source_path: Path, checksum: str, *, approved_phase: str = "public_metadata_check_only") -> dict[str, object]:
    manifest = build_arc_agi2_public_data_approval_manifest_template_v1()
    manifest.update(
        {
            "approval_id": "approval-2026-07-04-instance",
            "approved_by_owner": True,
            "approval_timestamp": "2026-07-04T16:35:00+02:00",
            "source_type": "public ARC-AGI-2 Kaggle competition source bundle",
            "source_location_local_path": str(source_path),
            "source_origin": "Kaggle ARC Prize 2026 ARC-AGI-2 competition Data tab",
            "source_download_method": "manual owner download from Kaggle Data tab",
            "source_version_or_snapshot": "arc-prize-2026-arc-agi-2.zip",
            "checksum_value": checksum,
            "approved_phase": approved_phase,
            "allowed_operations": [
                "path_existence_check",
                "checksum_check",
                "git_tracking_exclusion_check",
                "read_only_check",
                "manifest_validation",
            ],
            "forbidden_operations": [
                "unzip",
                "parse",
                "score",
                "solver_run",
                "submission",
                "public_claim",
                "data_commit",
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
        assert template_manifest["allowed_operations"] == [
            "path_existence_check",
            "checksum_check",
            "git_tracking_exclusion_check",
            "read_only_check",
            "manifest_validation",
        ]

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
        owner_approved_manifest["approved_phase"] = "public_parse_only"
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

    def test_source_instance_metadata_check_passes_for_dummy_read_only_source(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        staging_root = tmp_path / "staging"
        repo_root.mkdir()
        staging_root.mkdir()
        source_path = tmp_path / "source" / "bundle.zip"
        source_path.parent.mkdir()
        source_path.write_bytes(b"dummy bundle payload")
        source_path.chmod(0o444)
        checksum = __import__("hashlib").sha256(source_path.read_bytes()).hexdigest()
        manifest = _make_instance_manifest(source_path, checksum)
        result = validate_arc_agi2_public_data_source_instance_metadata_v1(
            manifest,
            repo_root=repo_root,
            staging_root=staging_root,
        )
        assert result["valid"] is True
        assert result["source_outside_repo"] is True
        assert result["source_outside_staging"] is True
        assert result["source_git_tracked"] is False
        assert result["source_read_only"] is True
        assert result["checksum_match"] is True

    def test_source_inside_repo_fails(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        source_path = repo_root / "bundle.zip"
        source_path.write_bytes(b"dummy bundle payload")
        source_path.chmod(0o444)
        checksum = __import__("hashlib").sha256(source_path.read_bytes()).hexdigest()
        manifest = _make_instance_manifest(source_path, checksum)
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_source_instance_metadata_v1(manifest, repo_root=repo_root)

    def test_source_git_tracked_fails(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
        source_path = repo_root / "bundle.zip"
        source_path.write_bytes(b"dummy bundle payload")
        source_path.chmod(0o444)
        subprocess.run(["git", "add", "bundle.zip"], cwd=repo_root, check=True)
        checksum = __import__("hashlib").sha256(source_path.read_bytes()).hexdigest()
        manifest = _make_instance_manifest(source_path, checksum)
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_source_instance_metadata_v1(manifest, repo_root=repo_root)

    def test_checksum_mismatch_fails(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        source_path = tmp_path / "source" / "bundle.zip"
        source_path.parent.mkdir()
        source_path.write_bytes(b"dummy bundle payload")
        source_path.chmod(0o444)
        manifest = _make_instance_manifest(source_path, "0" * 64)
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_source_instance_metadata_v1(manifest, repo_root=repo_root)

    def test_read_only_required_fails_for_writable_source(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        source_path = tmp_path / "source" / "bundle.zip"
        source_path.parent.mkdir()
        source_path.write_bytes(b"dummy bundle payload")
        source_path.chmod(0o644)
        checksum = __import__("hashlib").sha256(source_path.read_bytes()).hexdigest()
        manifest = _make_instance_manifest(source_path, checksum)
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_source_instance_metadata_v1(manifest, repo_root=repo_root)

    def test_metadata_check_phase_must_not_progress_beyond_public_metadata_check_only(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        source_path = tmp_path / "source" / "bundle.zip"
        source_path.parent.mkdir()
        source_path.write_bytes(b"dummy bundle payload")
        source_path.chmod(0o444)
        checksum = __import__("hashlib").sha256(source_path.read_bytes()).hexdigest()
        manifest = _make_instance_manifest(source_path, checksum, approved_phase="public_parse_only")
        with pytest.raises(ValueError):
            validate_arc_agi2_public_data_source_instance_metadata_v1(manifest, repo_root=repo_root)
