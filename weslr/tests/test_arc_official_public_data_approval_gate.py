"""Tests for the ARC official public-data approval manifest gate."""

from __future__ import annotations

import builtins

import pytest

from weslr.arc_official_public_data_approval_gate import (
    ALLOWED_APPROVED_PHASES_V1,
    validate_approval_manifest,
    validate_approval_manifest_claim,
)


@pytest.fixture()
def valid_manifest():
    return {
        "owner_approved": True,
        "approval_reference": "owner-approval-2026-07-02-a",
        "approved_phase": "phase_2_public_parse_scorer_validation",
        "source_type": "public_official_read_only_bundle",
        "source_location": "/synthetic/public/arc-read-only-bundle",
        "source_version_or_snapshot": "arc-2026.07-snapshot-01",
        "checksum": "sha256:dummy-checksum-001",
        "read_only_required": True,
        "approved_scope": {
            "scope": "public-official-read-only",
            "bundle_policy": "read-only",
        },
        "official_data_class": "public_official_arc",
        "claim_policy": {
            "official_score_claimable": False,
            "allow_official_score_before_local_run": False,
            "mix_synthetic_and_official_scores": False,
            "competition_submission_authority": False,
            "official_percentage_claimable": "none yet",
        },
        "offline_required": True,
        "no_hidden_private_data": True,
        "no_network_fetch": True,
        "no_mutation_in_place": True,
    }


class TestArcOfficialPublicDataApprovalGate:
    def test_valid_synthetic_dummy_approval_manifest_accepted_structurally(self, valid_manifest):
        opened = []

        def fake_open(*args, **kwargs):
            opened.append(args[0] if args else None)
            raise AssertionError("No file IO should occur in approval manifest validation")

        original_open = builtins.open
        builtins.open = fake_open
        try:
            result = validate_approval_manifest(valid_manifest)
        finally:
            builtins.open = original_open
        assert opened == []
        assert result["owner_approved"] is True
        assert result["approved_phase"] in ALLOWED_APPROVED_PHASES_V1
        assert result["official_data_class"] == "public_official_arc"
        assert result["official_percentage_claimable_text"] == "none yet"
        assert result["official_percentage_claimable_value"] == 0

    @pytest.mark.parametrize(
        "field, value",
        [
            ("owner_approved", False),
            ("approval_reference", ""),
            ("source_location", ""),
            ("source_version_or_snapshot", ""),
            ("checksum", ""),
        ],
    )
    def test_missing_required_fields_rejected(self, valid_manifest, field, value):
        bad = dict(valid_manifest)
        bad[field] = value
        with pytest.raises(ValueError):
            validate_approval_manifest(bad)

    def test_hidden_private_data_rejected(self, valid_manifest):
        bad = dict(valid_manifest)
        bad["official_data_class"] = "hidden_private_arc"
        with pytest.raises(ValueError):
            validate_approval_manifest(bad)

    def test_synthetic_as_official_rejected(self, valid_manifest):
        bad = dict(valid_manifest)
        bad["official_data_class"] = "synthetic_weslr"
        with pytest.raises(ValueError):
            validate_approval_manifest(bad)

    @pytest.mark.parametrize("source_type", ["network", "browser_fetched", "web_fetched", "remote"])
    def test_network_fetched_source_rejected(self, valid_manifest, source_type):
        bad = dict(valid_manifest)
        bad["source_type"] = source_type
        with pytest.raises(ValueError):
            validate_approval_manifest(bad)

    def test_mutable_source_rejected(self, valid_manifest):
        bad = dict(valid_manifest)
        bad["read_only_required"] = False
        bad["no_mutation_in_place"] = False
        with pytest.raises(ValueError):
            validate_approval_manifest(bad)

    @pytest.mark.parametrize("phase", ["phase_0_synthetic_only", "phase_1_toy_fixture_adapter", "phase_6_nonexistent"])
    def test_unsupported_phase_rejected(self, valid_manifest, phase):
        bad = dict(valid_manifest)
        bad["approved_phase"] = phase
        with pytest.raises(ValueError):
            validate_approval_manifest(bad)

    def test_premature_score_claim_rejected(self, valid_manifest):
        bad = dict(valid_manifest)
        bad["claim_policy"] = dict(valid_manifest["claim_policy"], official_score_claimable=True)
        with pytest.raises(ValueError):
            validate_approval_manifest(bad)

    def test_synthetic_official_score_mixing_rejected(self, valid_manifest):
        bad = dict(valid_manifest)
        bad["claim_policy"] = dict(valid_manifest["claim_policy"], mix_synthetic_and_official_scores=True)
        with pytest.raises(ValueError):
            validate_approval_manifest(bad)

    def test_competition_submission_authority_rejected(self, valid_manifest):
        bad = dict(valid_manifest)
        bad["claim_policy"] = dict(valid_manifest["claim_policy"], competition_submission_authority=True)
        with pytest.raises(ValueError):
            validate_approval_manifest(bad)

    def test_official_percentage_claimable_remains_none_zero_until_actual_approved_local_public_run_exists(self, valid_manifest):
        result = validate_approval_manifest(valid_manifest)
        assert result["official_percentage_claimable_text"] == "none yet"
        assert result["official_percentage_claimable_value"] == 0
        assert result["contamination_boundary"]["summary"]["official_percentage_claimable_value"] == 0

    def test_contamination_boundary_checker_is_respected(self, valid_manifest):
        result = validate_approval_manifest(valid_manifest)
        assert result["contamination_boundary"]["data_class"] == "public_official_arc"
        assert result["contamination_boundary"]["run_phase"] == "phase_2_public_parse_scorer_validation"
        assert result["contamination_boundary"]["summary"]["official_run_proof_present"] is False

    def test_validate_approval_manifest_claim_rejects_premature_official_claim(self):
        with pytest.raises(ValueError):
            validate_approval_manifest_claim(
                {
                    "claim_kind": "official_arc_performance",
                    "official_score_claimable": True,
                    "approved_phase": "phase_2_public_parse_scorer_validation",
                }
            )

    def test_validate_approval_manifest_claim_rejects_synthetic_official_mixing(self):
        with pytest.raises(ValueError):
            validate_approval_manifest_claim(
                {
                    "claim_kind": "synthetic_score",
                    "mix_synthetic_and_official_scores": True,
                }
            )

    def test_validate_approval_manifest_claim_rejects_competition_authority(self):
        with pytest.raises(ValueError):
            validate_approval_manifest_claim(
                {
                    "claim_kind": "approval_manifest",
                    "competition_submission_authority": True,
                }
            )
