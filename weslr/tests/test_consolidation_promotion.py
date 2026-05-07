"""
WESLR Consolidation Promotion — Tests (V2)

Covers: consolidation_config.py, consolidation_promotion.py
Uses temp dirs only; never writes to real .weslr paths.
"""

import json
import os
import pathlib
import tempfile

import pytest

from weslr.consolidation_config import ConsolidationConfig, load_config, save_config
from weslr.consolidation_promotion import (
    classify_zone,
    decide_promotion,
    auto_promote,
    get_auto_status,
    enable_auto,
    disable_auto,
    PromotionDecision,
    PromotionResult,
    _AUDIT_PATH,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_cluster(
    cluster_id="c1",
    destination="continuity_summary",
    tags=None,
    provenance=None,
    risk_level="low",
):
    return {
        "cluster_id": cluster_id,
        "proposed_destination": destination,
        "tags": tags or [],
        "provenance": provenance or [],
        "risk_level": risk_level,
        "summary": "test summary",
        "confidence": 0.7,
    }


def cfg_path(tmp):
    return str(pathlib.Path(tmp) / "consolidation_config.json")


def weslr_root(tmp):
    return str(tmp)


# ---------------------------------------------------------------------------
# consolidation_config.py tests
# ---------------------------------------------------------------------------

class TestConsolidationConfigDefaults:
    def test_default_all_off(self):
        cfg = ConsolidationConfig()
        assert cfg.consolidation_auto_enabled is False
        assert cfg.green_zone_auto_promotion_enabled is False

    def test_default_enabled_zones_contains_green(self):
        cfg = ConsolidationConfig()
        assert "green" in cfg.enabled_zones

    def test_default_require_provenance_true(self):
        cfg = ConsolidationConfig()
        assert cfg.require_provenance is True

    def test_default_require_audit_log_true(self):
        cfg = ConsolidationConfig()
        assert cfg.require_audit_log is True

    def test_default_allowed_green_destinations(self):
        cfg = ConsolidationConfig()
        assert "continuity_summary" in cfg.allowed_green_destinations
        assert "attention_memory" in cfg.allowed_green_destinations
        assert "entity_memory" not in cfg.allowed_green_destinations


class TestConsolidationConfigToFromDict:
    def test_roundtrip(self):
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
            enabled_zones=["green"],
            require_provenance=False,
            require_audit_log=False,
            allowed_green_destinations=["continuity_summary"],
        )
        d = cfg.to_dict()
        cfg2 = ConsolidationConfig.from_dict(d)
        assert cfg2.consolidation_auto_enabled is True
        assert cfg2.green_zone_auto_promotion_enabled is True
        assert cfg2.require_provenance is False
        assert cfg2.require_audit_log is False
        assert cfg2.allowed_green_destinations == ["continuity_summary"]


class TestConsolidationConfigIsAutoEnabled:
    def test_disabled_when_master_off(self):
        cfg = ConsolidationConfig(consolidation_auto_enabled=False, green_zone_auto_promotion_enabled=True)
        assert cfg.is_auto_enabled_for("green") is False

    def test_disabled_when_green_flag_off(self):
        cfg = ConsolidationConfig(consolidation_auto_enabled=True, green_zone_auto_promotion_enabled=False)
        assert cfg.is_auto_enabled_for("green") is False

    def test_enabled_when_both_on(self):
        cfg = ConsolidationConfig(consolidation_auto_enabled=True, green_zone_auto_promotion_enabled=True)
        assert cfg.is_auto_enabled_for("green") is True

    def test_disabled_for_yellow_zone(self):
        cfg = ConsolidationConfig(consolidation_auto_enabled=True, green_zone_auto_promotion_enabled=True)
        assert cfg.is_auto_enabled_for("yellow") is False


class TestConsolidationConfigCanAutoApply:
    def test_passes_green_destination_with_provenance(self):
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        allowed, reasons = cfg.can_auto_apply("green", "continuity_summary", ["src1"])
        assert allowed is True
        assert reasons == []

    def test_fails_missing_provenance(self):
        cfg = ConsolidationConfig(require_provenance=True)
        allowed, reasons = cfg.can_auto_apply("green", "continuity_summary", None)
        assert allowed is False
        assert any("provenance" in r for r in reasons)

    def test_fails_destination_not_in_allowed_list(self):
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        allowed, reasons = cfg.can_auto_apply("green", "entity_memory", ["src1"])
        assert allowed is False
        assert any("destination" in r for r in reasons)

    def test_fails_zone_not_enabled(self):
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
            enabled_zones=["green"],
        )
        allowed, reasons = cfg.can_auto_apply("yellow", "continuity_summary", ["src1"])
        assert allowed is False


class TestConsolidationConfigLoadSave:
    def test_save_and_load(self, tmp_path):
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        p = tmp_path / "consolidation_config.json"
        save_config(cfg, str(p))
        cfg2 = load_config(str(p))
        assert cfg2.consolidation_auto_enabled is True
        assert cfg2.green_zone_auto_promotion_enabled is True

    def test_load_missing_returns_defaults(self, tmp_path):
        cfg = load_config(str(tmp_path / "nonexistent.json"))
        assert cfg.consolidation_auto_enabled is False
        assert cfg.green_zone_auto_promotion_enabled is False

    def test_enable_sets_both_flags(self):
        cfg = ConsolidationConfig()
        cfg.enable()
        assert cfg.consolidation_auto_enabled is True
        assert cfg.green_zone_auto_promotion_enabled is True

    def test_disable_clears_both_flags(self):
        cfg = ConsolidationConfig(consolidation_auto_enabled=True, green_zone_auto_promotion_enabled=True)
        cfg.disable()
        assert cfg.consolidation_auto_enabled is False
        assert cfg.green_zone_auto_promotion_enabled is False


# ---------------------------------------------------------------------------
# consolidation_promotion.py — classify_zone tests
# ---------------------------------------------------------------------------

class TestClassifyZone:
    def test_green_default(self):
        assert classify_zone("continuity_summary", [], "c1") == "green"
        assert classify_zone("attention_memory", [], "c1") == "green"
        assert classify_zone("procedural_note", [], "c1") == "green"

    def test_red_forbidden_destination_doctrine(self):
        assert classify_zone("doctrine", [], "c1") == "red"
        assert classify_zone("doctrine_candidates", [], "c1") == "red"

    def test_red_forbidden_destination_entity_memory(self):
        assert classify_zone("entity_memory", [], "c1") == "red"

    def test_red_forbidden_destination_mission_store(self):
        assert classify_zone("mission_store", [], "c1") == "red"

    def test_red_forbidden_destination_code(self):
        assert classify_zone("code", [], "c1") == "red"

    def test_red_red_flag_tag(self):
        assert classify_zone("general", ["doctrine"], "c1") == "red"

    def test_red_identity_tag(self):
        assert classify_zone("general", ["identity"], "c1") == "red"

    def test_red_governance_tag(self):
        assert classify_zone("general", ["governance"], "c1") == "red"

    def test_red_research_truth_tag(self):
        assert classify_zone("general", ["research_truth"], "c1") == "red"

    def test_red_high_risk_tag(self):
        assert classify_zone("general", ["risk_level:high"], "c1") == "red"

    def test_yellow_weight_proposal_tag(self):
        assert classify_zone("general", ["weight_proposal"], "c1") == "yellow"

    def test_yellow_cognitive_anchor_tag(self):
        assert classify_zone("general", ["cognitive_anchor"], "c1") == "yellow"

    def test_yellow_belief_tag(self):
        assert classify_zone("general", ["belief"], "c1") == "yellow"

    def test_yellow_preference_tag(self):
        assert classify_zone("general", ["preference"], "c1") == "yellow"

    def test_yellow_bias_tag(self):
        assert classify_zone("general", ["bias"], "c1") == "yellow"

    def test_yellow_strategy_tag(self):
        assert classify_zone("general", ["strategy"], "c1") == "yellow"

    def test_yellow_mission_context_tag(self):
        assert classify_zone("general", ["mission_context"], "c1") == "yellow"

    def test_yellow_relationship_tag(self):
        assert classify_zone("general", ["relationship"], "c1") == "yellow"

    def test_yellow_role_assumption_tag(self):
        assert classify_zone("general", ["role_assumption"], "c1") == "yellow"

    def test_green_non_risky_destination_with_tags(self):
        assert classify_zone("continuity_summary", ["observation"], "c1") == "green"
        assert classify_zone("attention_memory", ["task"], "c1") == "green"


# ---------------------------------------------------------------------------
# consolidation_promotion.py — decide_promotion tests
# ---------------------------------------------------------------------------

class TestDecidePromotion:
    def test_v1_mode_no_auto_promote(self):
        """When both flags off (V1 mode), auto_promote=False."""
        cfg = ConsolidationConfig()
        cluster = make_cluster(destination="continuity_summary")
        decision = decide_promotion(cluster, cfg)
        assert decision.auto_promote is False

    def test_green_with_provenance_auto_promotes(self):
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        cluster = make_cluster(destination="continuity_summary", provenance=["src1"])
        decision = decide_promotion(cluster, cfg)
        assert decision.zone == "green"
        assert decision.auto_promote is True

    def test_yellow_never_auto_promotes(self):
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        cluster = make_cluster(destination="general", tags=["weight_proposal"], provenance=["src1"])
        decision = decide_promotion(cluster, cfg)
        assert decision.zone == "yellow"
        assert decision.auto_promote is False

    def test_red_never_auto_promotes(self):
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        cluster = make_cluster(destination="doctrine", provenance=["src1"])
        decision = decide_promotion(cluster, cfg)
        assert decision.zone == "red"
        assert decision.auto_promote is False

    def test_missing_provenance_blocked(self):
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
            require_provenance=True,
        )
        cluster = make_cluster(destination="continuity_summary", provenance=[])
        decision = decide_promotion(cluster, cfg)
        assert decision.auto_promote is False
        assert any("provenance" in r for r in decision.blocked_reasons)

    def test_auto_eligible_only_when_green_and_config_allows(self):
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        green_cluster = make_cluster(destination="continuity_summary", provenance=["src1"])
        yellow_cluster = make_cluster(destination="general", tags=["weight_proposal"], provenance=["src1"])

        green_decision = decide_promotion(green_cluster, cfg)
        yellow_decision = decide_promotion(yellow_cluster, cfg)

        assert green_decision.auto_eligible is True
        assert yellow_decision.auto_eligible is False  # yellow not in enabled_zones


# ---------------------------------------------------------------------------
# consolidation_promotion.py — auto_promote tests
# ---------------------------------------------------------------------------

class TestAutoPromote:
    def test_v1_disabled_returns_V1_disabled(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        cfg = ConsolidationConfig()  # both flags off
        cluster = make_cluster()
        result = auto_promote(cluster, cfg)
        assert result.promoted is False
        assert result.decision == "V1_disabled"
        assert result.record_written is False

    def test_green_auto_promoted_writes_record(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        cluster = make_cluster(destination="continuity_summary", provenance=["src1"], cluster_id="c-green")
        result = auto_promote(cluster, cfg)
        assert result.promoted is True
        assert result.decision == "auto_promoted"
        assert result.zone == "green"
        assert result.record_written is True

        # Verify destination file was written
        dest_file = pathlib.Path(tmp_path) / "continuity_summaries.jsonl"
        assert dest_file.exists()
        entries = [json.loads(l) for l in dest_file.read_text().strip().split("\n") if l.strip()]
        assert len(entries) == 1
        assert entries[0]["cluster_id"] == "c-green"

    def test_yellow_not_auto_promoted(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        cluster = make_cluster(destination="general", tags=["weight_proposal"], provenance=["src1"])
        result = auto_promote(cluster, cfg)
        assert result.promoted is False
        assert result.decision == "review_required"
        assert result.record_written is False

    def test_red_not_auto_promoted(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        cluster = make_cluster(destination="doctrine", provenance=["src1"])
        result = auto_promote(cluster, cfg)
        assert result.promoted is False
        assert result.decision == "approval_required"
        assert result.record_written is False

    def test_entity_memory_not_auto_promoted_even_if_green_zone(self, tmp_path, monkeypatch):
        """entity_memory is in FORBIDDEN_DESTINATIONS, always red."""
        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
        )
        cluster = make_cluster(destination="entity_memory", provenance=["src1"])
        result = auto_promote(cluster, cfg)
        assert result.zone == "red"
        assert result.promoted is False

    def test_blocked_missing_provenance_no_write(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        cfg = ConsolidationConfig(
            consolidation_auto_enabled=True,
            green_zone_auto_promotion_enabled=True,
            require_provenance=True,
        )
        cluster = make_cluster(destination="continuity_summary", provenance=[])
        result = auto_promote(cluster, cfg)
        assert result.promoted is False
        assert result.decision == "blocked"
        assert result.record_written is False


# ---------------------------------------------------------------------------
# consolidation_promotion.py — get_auto_status / enable_auto / disable_auto
# ---------------------------------------------------------------------------

class TestAutoStatusHelpers:
    def test_get_auto_status_default(self):
        cfg = ConsolidationConfig()
        status = get_auto_status(cfg)
        assert status["consolidation_auto_enabled"] is False
        assert status["green_zone_auto_promotion_enabled"] is False

    def test_enable_auto_saves_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        cfg = ConsolidationConfig()
        p = str(pathlib.Path(tmp_path) / "consolidation_config.json")
        cfg2 = enable_auto(cfg, p)
        assert cfg2.consolidation_auto_enabled is True
        assert cfg2.green_zone_auto_promotion_enabled is True

        # Reload and verify persisted
        cfg3 = load_config(p)
        assert cfg3.consolidation_auto_enabled is True

    def test_disable_auto_saves_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        p = str(pathlib.Path(tmp_path) / "consolidation_config.json")
        cfg = ConsolidationConfig(consolidation_auto_enabled=True, green_zone_auto_promotion_enabled=True)
        save_config(cfg, p)
        cfg2 = disable_auto(None, p)
        assert cfg2.consolidation_auto_enabled is False
        assert cfg2.green_zone_auto_promotion_enabled is False


# ---------------------------------------------------------------------------
# _write_destination_record tests
# ---------------------------------------------------------------------------

class TestWriteDestinationRecord:
    def test_writes_to_correct_file(self, tmp_path, monkeypatch):
        from weslr.consolidation_promotion import _write_destination_record

        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        cluster = make_cluster(cluster_id="c-write-test", destination="attention_memory", provenance=["src1"])
        success = _write_destination_record("attention_memory", cluster)
        assert success is True

        dest_file = pathlib.Path(tmp_path) / "attention_memory.jsonl"
        assert dest_file.exists()
        entry = json.loads(dest_file.read_text().strip())
        assert entry["cluster_id"] == "c-write-test"
        assert entry["destination"] == "attention_memory"

    def test_unknown_destination_returns_false(self, tmp_path, monkeypatch):
        from weslr.consolidation_promotion import _write_destination_record

        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        success = _write_destination_record("unknown_destination", make_cluster())
        assert success is False

    def test_creates_parent_directories(self, tmp_path, monkeypatch):
        from weslr.consolidation_promotion import _write_destination_record

        monkeypatch.setenv("WESLR_ROOT", str(tmp_path))
        cluster = make_cluster(cluster_id="c-nested", destination="procedural_note")
        success = _write_destination_record("procedural_note", cluster)
        assert success is True


# ---------------------------------------------------------------------------
# PromotionResult.to_dict tests
# ---------------------------------------------------------------------------

class TestPromotionResultToDict:
    def test_roundtrip(self):
        result = PromotionResult(
            cluster_id="c-test",
            promoted=True,
            zone="green",
            decision="auto_promoted",
            destination="continuity_summary",
            blocked_reasons=[],
            record_written=True,
        )
        d = result.to_dict()
        assert d["cluster_id"] == "c-test"
        assert d["promoted"] is True
        assert d["decision"] == "auto_promoted"


# ---------------------------------------------------------------------------
# PromotionDecision.to_dict tests
# ---------------------------------------------------------------------------

class TestPromotionDecisionToDict:
    def test_roundtrip(self):
        decision = PromotionDecision(
            cluster_id="c-dec",
            zone="yellow",
            auto_eligible=False,
            auto_promote=False,
            blocked_reasons=["zone not enabled"],
            destination="general",
            provenance=["src1"],
        )
        d = decision.to_dict()
        assert d["cluster_id"] == "c-dec"
        assert d["zone"] == "yellow"
        assert "zone not enabled" in d["blocked_reasons"]