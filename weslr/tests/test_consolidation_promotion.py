"""
WESLR Consolidation Promotion — Tests

Covers:
- default OFF
- ON permits green only
- yellow/red blocked
- missing provenance blocked
- audit written
- no entity/doctrine/code writes for disallowed candidates

All tests use temp directories. No real filesystem mutated.
"""

import json
import os
import pathlib
import tempfile
import pytest

# Import from package
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from weslr.consolidation_config import (
    ConsolidationConfig,
    load_config,
    save_config,
    _DEFAULTS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_temp_cfg():
    """Return (cfg, tmpdir). Config points to tmpdir."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    cfg = ConsolidationConfig()
    save_config(cfg, str(tmp / "consolidation_config.json"))
    return cfg, tmp


# ---------------------------------------------------------------------------
# ConsolidationConfig tests
# ---------------------------------------------------------------------------

class TestConsolidationConfigDefaults:
    def test_default_off(self):
        cfg = ConsolidationConfig()
        assert cfg.consolidation_auto_enabled is False
        assert cfg.green_zone_auto_promotion_enabled is False

    def test_default_zones(self):
        cfg = ConsolidationConfig()
        assert cfg.enabled_zones == ["green"]
        assert cfg.require_provenance is True
        assert cfg.require_audit_log is True

    def test_default_allowed_destinations(self):
        cfg = ConsolidationConfig()
        expected = [
            "continuity_summary",
            "attention_memory",
            "digest_archive_marker",
            "procedural_note",
        ]
        assert cfg.allowed_green_destinations == expected


class TestConsolidationConfigEnableDisable:
    def test_enable_sets_both_flags(self):
        cfg = ConsolidationConfig()
        cfg.enable()
        assert cfg.consolidation_auto_enabled is True
        assert cfg.green_zone_auto_promotion_enabled is True

    def test_disable_clears_both_flags(self):
        cfg = ConsolidationConfig()
        cfg.enable()
        cfg.disable()
        assert cfg.consolidation_auto_enabled is False
        assert cfg.green_zone_auto_promotion_enabled is False


class TestConsolidationConfigIsAutoEnabledFor:
    def test_disabled_returns_false(self):
        cfg = ConsolidationConfig()
        assert cfg.is_auto_enabled_for("green") is False

    def test_enabled_but_wrong_zone(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        assert cfg.is_auto_enabled_for("green") is True
        assert cfg.is_auto_enabled_for("yellow") is False
        assert cfg.is_auto_enabled_for("red") is False

    def test_both_on_green_zone(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        assert cfg.is_auto_enabled_for("green") is True


class TestConsolidationConfigCanAutoApply:
    def test_green_allows_when_enabled(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        cfg.allowed_green_destinations = ["continuity_summary"]
        allowed, reasons = cfg.can_auto_apply(
            "green", "continuity_summary", provenance=["source:session"]
        )
        assert allowed is True
        assert reasons == []

    def test_missing_provenance_blocked(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        cfg.allowed_green_destinations = ["continuity_summary"]
        cfg.require_provenance = True
        allowed, reasons = cfg.can_auto_apply(
            "green", "continuity_summary", provenance=None
        )
        assert allowed is False
        assert "provenance missing" in reasons[0]

    def test_empty_provenance_blocked(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        cfg.allowed_green_destinations = ["continuity_summary"]
        cfg.require_provenance = True
        allowed, reasons = cfg.can_auto_apply(
            "green", "continuity_summary", provenance=[]
        )
        assert allowed is False

    def test_wrong_destination_blocked(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        cfg.allowed_green_destinations = ["continuity_summary"]
        allowed, reasons = cfg.can_auto_apply(
            "green", "entity_memory", provenance=["source:session"]
        )
        assert allowed is False
        assert any("entity_memory" in r for r in reasons)

    def test_yellow_zone_blocked_even_when_green_enabled(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        allowed, reasons = cfg.can_auto_apply(
            "yellow", "continuity_summary", provenance=["source:session"]
        )
        assert allowed is False
        assert any("yellow" in r or "zone" in r for r in reasons)

    def test_red_zone_blocked(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        allowed, reasons = cfg.can_auto_apply(
            "red", "doctrine", provenance=["source:session"]
        )
        assert allowed is False


class TestConsolidationConfigPersistence:
    def test_save_load_roundtrip(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green", "yellow"]
        cfg.require_provenance = False
        cfg.allowed_green_destinations = ["continuity_summary"]

        tmp = pathlib.Path(tempfile.mkdtemp())
        save_config(cfg, str(tmp / "c.json"))

        loaded = load_config(str(tmp / "c.json"))
        assert loaded.consolidation_auto_enabled is True
        assert loaded.green_zone_auto_promotion_enabled is True
        assert loaded.enabled_zones == ["green", "yellow"]
        assert loaded.require_provenance is False
        assert loaded.allowed_green_destinations == ["continuity_summary"]

    def test_missing_file_returns_defaults(self):
        cfg = load_config("/nonexistent/path/config.json")
        assert cfg.consolidation_auto_enabled is False
        assert cfg.green_zone_auto_promotion_enabled is False
        assert cfg.enabled_zones == ["green"]

    def test_enable_save_load_cycle(self):
        cfg, tmp = make_temp_cfg()
        assert cfg.consolidation_auto_enabled is False
        cfg.enable()
        save_config(cfg, str(tmp / "consolidation_config.json"))
        loaded = load_config(str(tmp / "consolidation_config.json"))
        assert loaded.consolidation_auto_enabled is True
        assert loaded.green_zone_auto_promotion_enabled is True


# ---------------------------------------------------------------------------
# Zone classification tests
# ---------------------------------------------------------------------------

from weslr.consolidation_promotion import (
    classify_zone,
    decide_promotion,
    auto_promote,
    _AUDIT_PATH,
    PromotionResult,
)


class TestClassifyZone:
    def test_forbidden_destination_red(self):
        for dest in ["doctrine", "entity_memory", "mission_store", "code", "governance"]:
            assert classify_zone(dest, [], "c1") == "red", f"dest={dest}"

    def test_red_flag_tag_red(self):
        tags = ["risk_level:high"]
        assert classify_zone("continuity_summary", tags, "c1") == "red"

    def test_yellow_flag_tag_yellow(self):
        tags = ["weight_proposal"]
        assert classify_zone("continuity_summary", tags, "c1") == "yellow"

    def test_default_green(self):
        assert classify_zone("continuity_summary", [], "c1") == "green"

    def test_multiple_tags_highest_wins(self):
        # red overrides yellow
        assert classify_zone("continuity_summary", ["weight_proposal", "doctrine"], "c1") == "red"


class TestDecidePromotion:
    def test_v1_mode_both_flags_off(self):
        cfg = ConsolidationConfig()  # both flags False by default
        cluster = {
            "cluster_id": "c1",
            "proposed_destination": "continuity_summary",
            "provenance": ["source:session"],
            "tags": [],
        }
        decision = decide_promotion(cluster, cfg)
        # With both OFF, can_auto returns False → auto_promote=False
        assert decision.auto_promote is False
        assert decision.zone == "green"

    def test_green_enabled_auto_promote(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        cfg.allowed_green_destinations = ["continuity_summary"]
        cluster = {
            "cluster_id": "c1",
            "proposed_destination": "continuity_summary",
            "provenance": ["source:session"],
            "tags": [],
        }
        decision = decide_promotion(cluster, cfg)
        assert decision.auto_promote is True
        assert decision.zone == "green"

    def test_yellow_never_auto_promotes(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green", "yellow"]
        cluster = {
            "cluster_id": "c2",
            "proposed_destination": "continuity_summary",
            "provenance": ["source:session"],
            "tags": ["weight_proposal"],
        }
        decision = decide_promotion(cluster, cfg)
        assert decision.zone == "yellow"
        assert decision.auto_promote is False
        assert decision.blocked_reasons != []

    def test_red_never_auto_promotes(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green", "red"]
        cluster = {
            "cluster_id": "c3",
            "proposed_destination": "doctrine",
            "provenance": ["source:session"],
            "tags": [],
        }
        decision = decide_promotion(cluster, cfg)
        assert decision.zone == "red"
        assert decision.auto_promote is False

    def test_missing_provenance_blocked_when_required(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        cfg.allowed_green_destinations = ["continuity_summary"]
        cfg.require_provenance = True
        cluster = {
            "cluster_id": "c4",
            "proposed_destination": "continuity_summary",
            "provenance": [],
            "tags": [],
        }
        decision = decide_promotion(cluster, cfg)
        assert decision.auto_promote is False


# ---------------------------------------------------------------------------
# Audit log tests
# ---------------------------------------------------------------------------

from weslr.consolidation_promotion import _write_destination_record


class TestAuditLog:
    def test_audit_written_on_auto_promote(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        cfg.allowed_green_destinations = ["continuity_summary"]
        cfg.require_audit_log = True
        cfg.require_provenance = False

        tmp = pathlib.Path(tempfile.mkdtemp())
        audit_path = tmp / "consolidation_audit.jsonl"
        cluster = {
            "cluster_id": "c_audit_1",
            "proposed_destination": "continuity_summary",
            "provenance": [],
            "tags": [],
            "summary": "test summary",
        }

        # Patch audit path for test
        import weslr.consolidation_promotion as cp
        original_audit = cp._AUDIT_PATH
        cp._AUDIT_PATH = audit_path

        try:
            result = auto_promote(cluster, cfg)
            assert result.promoted is True
            assert audit_path.exists()
            with open(audit_path, encoding="utf-8") as f:
                entries = [json.loads(l) for l in f if l.strip()]
            assert len(entries) == 1
            assert entries[0]["decision"] == "auto_promoted"
            assert entries[0]["cluster_id"] == "c_audit_1"
        finally:
            cp._AUDIT_PATH = original_audit

    def test_audit_not_written_when_require_audit_false(self):
        cfg = ConsolidationConfig()
        cfg.consolidation_auto_enabled = True
        cfg.green_zone_auto_promotion_enabled = True
        cfg.enabled_zones = ["green"]
        cfg.allowed_green_destinations = ["continuity_summary"]
        cfg.require_audit_log = False

        tmp = pathlib.Path(tempfile.mkdtemp())
        audit_path = tmp / "consolidation_audit.jsonl"
        cluster = {
            "cluster_id": "c_no_audit",
            "proposed_destination": "continuity_summary",
            "provenance": [],
            "tags": [],
        }

        import weslr.consolidation_promotion as cp
        original_audit = cp._AUDIT_PATH
        cp._AUDIT_PATH = audit_path

        try:
            auto_promote(cluster, cfg)
            # Audit file may or may not exist depending on other code paths
            # but the audit_log() function returns early when require_audit_log is False
            # so no entry should be written
            if audit_path.exists():
                with open(audit_path, encoding="utf-8") as f:
                    entries = [json.loads(l) for l in f if l.strip()]
                # Only the V1_disabled entry from earlier test if any
                for e in entries:
                    assert e.get("cluster_id") != "c_no_audit"
        finally:
            cp._AUDIT_PATH = original_audit


# ---------------------------------------------------------------------------
# No forbidden writes tests
# ---------------------------------------------------------------------------

class TestNoForbiddenDestinationWrites:
    def test_entity_memory_not_written(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        cluster = {
            "cluster_id": "c_entity",
            "proposed_destination": "entity_memory",
            "provenance": ["source:session"],
            "tags": [],
            "summary": "entity test",
        }
        success = _write_destination_record("entity_memory", cluster)
        assert success is False  # not in destination_map

    def test_doctrine_not_written(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        cluster = {
            "cluster_id": "c_doctrine",
            "proposed_destination": "doctrine",
            "provenance": ["source:session"],
            "tags": [],
            "summary": "doctrine test",
        }
        success = _write_destination_record("doctrine", cluster)
        assert success is False

    def test_code_not_written(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        cluster = {
            "cluster_id": "c_code",
            "proposed_destination": "code",
            "provenance": ["source:session"],
            "tags": [],
            "summary": "code test",
        }
        success = _write_destination_record("code", cluster)
        assert success is False

    def test_allowed_destination_written(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        cluster = {
            "cluster_id": "c_allowed",
            "proposed_destination": "continuity_summary",
            "provenance": ["source:session"],
            "tags": [],
            "summary": "allowed test",
        }

        # Override WESLR_ROOT for this test
        original_root = os.environ.get("WESLR_ROOT")
        os.environ["WESLR_ROOT"] = str(tmp)

        try:
            success = _write_destination_record("continuity_summary", cluster)
            assert success is True
            dest_path = tmp / "continuity_summaries.jsonl"
            assert dest_path.exists()
            with open(dest_path, encoding="utf-8") as f:
                entries = [json.loads(l) for l in f if l.strip()]
            assert len(entries) == 1
            assert entries[0]["cluster_id"] == "c_allowed"
            assert entries[0]["destination"] == "continuity_summary"
        finally:
            if original_root is None:
                os.environ.pop("WESLR_ROOT", None)
            else:
                os.environ["WESLR_ROOT"] = original_root


# ---------------------------------------------------------------------------
# V1 invariant tests
# ---------------------------------------------------------------------------

class TestV1Invariant:
    def test_promotion_performed_false_when_disabled(self):
        cfg = ConsolidationConfig()  # default OFF
        cluster = {
            "cluster_id": "c_v1",
            "proposed_destination": "continuity_summary",
            "provenance": ["source:session"],
            "tags": [],
        }
        result = auto_promote(cluster, cfg)
        assert result.promoted is False
        assert result.decision == "V1_disabled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])