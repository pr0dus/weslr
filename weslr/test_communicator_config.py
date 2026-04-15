#!/usr/bin/env python3
"""Tests for weslr/communicator_config.py — Phase C Communicator Wiring validation."""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from weslr.communicator_config import (
    load_operator_profile,
    save_operator_profile,
    update_operator_profile,
    derive_communicator_config,
    get_checkin_cadence,
    should_checkin_now,
    get_adaptation_level,
    can_self_modify,
    get_adaptation_limits,
    is_change_prohibited,
    get_escalation_config,
    should_escalate,
    format_escalation_message,
    get_allowed_capabilities,
    is_capability_allowed,
    get_forbidden_actions,
    is_action_forbidden,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def make_config(tmp_path):
    """Create a fake communicator_config module backed by tmp_path."""
    config = {
        "profile_path": tmp_path / "operator_profile.json",
        "communicator_self_path": tmp_path / "communicator_self.json",
    }
    return config


# ── Tests: Profile Loading / Saving ─────────────────────────────────────────

def test_load_operator_profile_empty():
    """Test: load_operator_profile returns empty dict when no profile exists."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        result = load_operator_profile()
        assert result == {}, f"Expected empty dict, got {result}"
    shutil.rmtree(tmp)


def test_load_operator_profile_existing():
    """Test: load_operator_profile loads existing profile."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        profile = {
            "name": "Alice",
            "role": "Engineering Lead",
            "checkin_style": "daily",
            "adaptation_level": "propose",
        }
        with open(tmp / "operator_profile.json", "w") as f:
            json.dump(profile, f)
        result = load_operator_profile()
        assert result["name"] == "Alice"
        assert result["checkin_style"] == "daily"
    shutil.rmtree(tmp)


def test_save_operator_profile():
    """Test: save_operator_profile writes to disk."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        profile = {"name": "Bob", "checkin_style": "hourly"}
        save_operator_profile(profile)
        loaded = json.loads((tmp / "operator_profile.json").read_text())
        assert loaded["name"] == "Bob"
        assert loaded["checkin_style"] == "hourly"
    shutil.rmtree(tmp)


def test_update_operator_profile_merges():
    """Test: update_operator_profile merges with existing history."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        initial = {"name": "Carol", "role": "DevOps", "checkin_style": "silent"}
        save_operator_profile(initial)
        update_operator_profile({
            "phase": "onboarding",
            "name": "Carol",
            "role": "DevOps",
            "checkin_style": "daily",
            "adaptation_level": "low-risk",
            "primary_outcome": "Speed up CI",
        })
        loaded = load_operator_profile()
        assert loaded["name"] == "Carol"
        assert loaded["checkin_style"] == "daily"
        assert loaded["adaptation_level"] == "low-risk"
        assert loaded["primary_outcome"] == "Speed up CI"
        assert len(loaded["_onboarding_history"]) == 1
    shutil.rmtree(tmp)


def test_update_operator_profile_keeps_last_3():
    """Test: update_operator_profile preserves last 3 onboarding submissions."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        for i in range(4):
            update_operator_profile({
                "phase": "onboarding",
                "name": f"Human{i}",
                "checkin_style": "daily",
                "run": i,
            })
        profile = load_operator_profile()
        history = profile["_onboarding_history"]
        assert len(history) == 3, f"Expected 3, got {len(history)}"
        assert history[-1]["answers"]["name"] == "Human3"
    shutil.rmtree(tmp)


# ── Tests: Config Derivation ──────────────────────────────────────────────────

def test_derive_communicator_config_defaults():
    """Test: derive_communicator_config returns stable defaults before onboarding."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        config = derive_communicator_config()
        assert config["checkin_style"] == "silent"
        assert config["standup_cadence"] == "none"
        assert config["adaptation_level"] == "propose"
        assert config["escalation_primary"] == ""
        assert config["escalation_channel"] == "none"
        assert config["_is_onboarded"] is False
    shutil.rmtree(tmp)


def test_derive_communicator_config_from_profile():
    """Test: derive_communicator_config reads from operator profile."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({
            "name": "Alice",
            "role": "CTO",
            "persona": "technical",
            "checkin_style": "verbose",
            "standup_cadence": "morning",
            "adaptation_level": "full",
            "escalation_primary": "@alice",
            "escalation_channel": "slack",
            "primary_outcome": "Ship faster",
            "time_horizon": "week",
            "urgency": "sprint",
        })
        config = derive_communicator_config()
        assert config["operator_name"] == "Alice"
        assert config["operator_role"] == "CTO"
        assert config["checkin_style"] == "verbose"
        assert config["standup_cadence"] == "morning"
        assert config["adaptation_level"] == "full"
        assert config["escalation_primary"] == "@alice"
        assert config["escalation_channel"] == "slack"
        assert config["primary_outcome"] == "Ship faster"
        assert config["time_horizon"] == "week"
        assert config["urgency"] == "sprint"
        assert config["_is_onboarded"] is True
    shutil.rmtree(tmp)


# ── Tests: Check-in Cadence ───────────────────────────────────────────────────

def test_get_checkin_cadence_default():
    """Test: get_checkin_cadence returns 'silent' before onboarding."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        assert get_checkin_cadence() == "silent"
    shutil.rmtree(tmp)


def test_get_checkin_cadence_verbose():
    """Test: get_checkin_cadence returns configured value."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"checkin_style": "hourly"})
        assert get_checkin_cadence() == "hourly"
        update_operator_profile({"checkin_style": "daily"})
        assert get_checkin_cadence() == "daily"
    shutil.rmtree(tmp)


def test_should_checkin_now_silent():
    """Test: should_checkin_now returns False when cadence is silent."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"checkin_style": "silent"})
        assert should_checkin_now(0, 1000000) is False
    shutil.rmtree(tmp)


def test_should_checkin_now_hourly():
    """Test: should_checkin_now returns True after 3600+ seconds."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"checkin_style": "hourly"})
        last = 1000000
        now = last + 3600
        assert should_checkin_now(last, now) is True
        assert should_checkin_now(last, now - 100) is False
    shutil.rmtree(tmp)


def test_should_checkin_now_daily():
    """Test: should_checkin_now respects daily cadence."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"checkin_style": "daily"})
        last = 1000000
        now = last + 86400
        assert should_checkin_now(last, now) is True
        assert should_checkin_now(last, now - 1) is False
    shutil.rmtree(tmp)


def test_should_checkin_now_verbose():
    """Test: should_checkin_now returns True after 1800s for verbose."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"checkin_style": "verbose"})
        last = 1000000
        now = last + 1800
        assert should_checkin_now(last, now) is True
        assert should_checkin_now(last, now - 1) is False
    shutil.rmtree(tmp)


# ── Tests: Adaptation / Capability Gates ─────────────────────────────────────

def test_get_adaptation_level_default():
    """Test: get_adaptation_level returns 'propose' before onboarding."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        assert get_adaptation_level() == "propose"
    shutil.rmtree(tmp)


def test_can_self_modify_propose():
    """Test: can_self_modify returns False when level is 'propose'."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"adaptation_level": "propose"})
        assert can_self_modify("prompt", "low") is False
        assert can_self_modify("config", "low") is False
        assert can_self_modify("code", "high") is False
    shutil.rmtree(tmp)


def test_can_self_modify_low_risk():
    """Test: can_self_modify allows low-risk changes at 'low-risk' level."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"adaptation_level": "low-risk"})
        assert can_self_modify("prompt", "low") is True
        assert can_self_modify("config", "low") is True
        assert can_self_modify("comment", "low") is True
        assert can_self_modify("formatting", "low") is True
        assert can_self_modify("code", "medium") is False
        assert can_self_modify("code", "high") is False
    shutil.rmtree(tmp)


def test_can_self_modify_full():
    """Test: can_self_modify allows low+medium impact at 'full' level."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"adaptation_level": "full"})
        assert can_self_modify("code", "low") is True
        assert can_self_modify("code", "medium") is True
        assert can_self_modify("code", "high") is False
    shutil.rmtree(tmp)


def test_can_self_modify_none():
    """Test: can_self_modify returns False when level is 'none'."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"adaptation_level": "none"})
        assert can_self_modify("prompt", "low") is False
    shutil.rmtree(tmp)


def test_get_adaptation_limits_empty():
    """Test: get_adaptation_limits returns empty list when not set."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        assert get_adaptation_limits() == []
    shutil.rmtree(tmp)


def test_get_adaptation_limits_parsed():
    """Test: get_adaptation_limits parses newline-separated limits."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({
            "adaptation_limits": "safety_gateway\noperator_override\nmemory_retention"
        })
        limits = get_adaptation_limits()
        assert len(limits) == 3
        assert "safety_gateway" in limits
        assert "operator_override" in limits
    shutil.rmtree(tmp)


def test_is_change_prohibited():
    """Test: is_change_prohibited checks against operator's limits."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({
            "adaptation_limits": "Never modify the safety gateway\nNever alter the operator override"
        })
        assert is_change_prohibited("safety_gateway") is True
        assert is_change_prohibited("operator_override") is True
        assert is_change_prohibited("prompt") is False
    shutil.rmtree(tmp)


# ── Tests: Escalation Routing ──────────────────────────────────────────────────

def test_get_escalation_config_defaults():
    """Test: get_escalation_config returns sensible defaults."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        esc = get_escalation_config()
        assert esc["primary_contact"] == ""
        assert esc["secondary_contact"] == ""
        assert esc["channel"] == "none"
        assert esc["is_configured"] is False
    shutil.rmtree(tmp)


def test_get_escalation_config_configured():
    """Test: get_escalation_config reflects operator profile."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({
            "escalation_primary": "@alice",
            "escalation_secondary": "@bob",
            "escalation_channel": "slack",
        })
        esc = get_escalation_config()
        assert esc["primary_contact"] == "@alice"
        assert esc["secondary_contact"] == "@bob"
        assert esc["channel"] == "slack"
        assert esc["is_configured"] is True
    shutil.rmtree(tmp)


def test_should_escalate_cost():
    """Test: should_escalate returns True for cost situations."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"escalation_primary": "@alice"})
        assert should_escalate("cost") is True
    shutil.rmtree(tmp)


def test_should_escalate_safety():
    """Test: should_escalate returns True for safety situations."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({"escalation_primary": "@alice"})
        assert should_escalate("safety") is True
    shutil.rmtree(tmp)


def test_should_escalate_unconfigured():
    """Test: should_escalate returns False when no contact is configured."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        assert should_escalate("cost") is False
        assert should_escalate("safety") is False
    shutil.rmtree(tmp)


def test_format_escalation_message():
    """Test: format_escalation_message produces readable output."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({
            "name": "Alice",
            "primary_outcome": "Ship faster",
            "urgency": "sprint",
            "escalation_primary": "@alice",
            "escalation_channel": "slack",
        })
        msg = format_escalation_message("cost", "Budget exceeded by 200%")
        assert "[Weslr Escalation" in msg
        assert "@alice" in msg
        assert "cost" in msg
        assert "Budget exceeded" in msg
        assert "Ship faster" in msg
    shutil.rmtree(tmp)


# ── Tests: Capability Gate Helpers ───────────────────────────────────────────

def test_get_allowed_capabilities_empty():
    """Test: get_allowed_capabilities returns empty list before onboarding."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        assert get_allowed_capabilities() == []
    shutil.rmtree(tmp)


def test_get_allowed_capabilities_from_profile():
    """Test: get_allowed_capabilities reads from operator profile."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({
            "allowed_capabilities": ["Read code, files, and docs", "Run tests and CI"]
        })
        caps = get_allowed_capabilities()
        assert len(caps) == 2
        assert "Read code, files, and docs" in caps
    shutil.rmtree(tmp)


def test_is_capability_allowed_no_profile():
    """Test: is_capability_allowed returns True before onboarding (no restrictions)."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        assert is_capability_allowed("write") is True
        assert is_capability_allowed("search") is True
    shutil.rmtree(tmp)


def test_is_capability_allowed_with_profile():
    """Test: is_capability_allowed respects operator's capability list."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({
            "allowed_capabilities": ["Read code, files, and docs", "Run tests and CI"]
        })
        assert is_capability_allowed("read") is True
        assert is_capability_allowed("test") is True
        assert is_capability_allowed("write") is False
    shutil.rmtree(tmp)


def test_get_forbidden_actions_empty():
    """Test: get_forbidden_actions returns empty list when not set."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        assert get_forbidden_actions() == []
    shutil.rmtree(tmp)


def test_get_forbidden_actions_parsed():
    """Test: get_forbidden_actions parses newline-separated forbidden actions."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({
            "forbidden_actions": "Never push directly to main\nNever delete resources\nNever modify production"
        })
        forbidden = get_forbidden_actions()
        assert len(forbidden) == 3
        assert "Never push directly to main" in forbidden
    shutil.rmtree(tmp)


def test_is_action_forbidden():
    """Test: is_action_forbidden checks against operator's forbidden list."""
    tmp = Path(tempfile.mkdtemp())
    with patch("weslr.communicator_config._base_dir", return_value=str(tmp)):
        save_operator_profile({
            "forbidden_actions": "Never push directly to main\nNever delete resources"
        })
        assert is_action_forbidden("push to main") is True
        assert is_action_forbidden("delete resources") is True
        assert is_action_forbidden("read code") is False
    shutil.rmtree(tmp)


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("load empty profile", test_load_operator_profile_empty),
        ("load existing profile", test_load_operator_profile_existing),
        ("save profile", test_save_operator_profile),
        ("update profile merges", test_update_operator_profile_merges),
        ("update profile keeps last 3", test_update_operator_profile_keeps_last_3),
        ("derive config defaults", test_derive_communicator_config_defaults),
        ("derive config from profile", test_derive_communicator_config_from_profile),
        ("get checkin cadence default", test_get_checkin_cadence_default),
        ("get checkin cadence verbose", test_get_checkin_cadence_verbose),
        ("should checkin silent", test_should_checkin_now_silent),
        ("should checkin hourly", test_should_checkin_now_hourly),
        ("should checkin daily", test_should_checkin_now_daily),
        ("should checkin verbose", test_should_checkin_now_verbose),
        ("get adaptation level default", test_get_adaptation_level_default),
        ("can self modify propose", test_can_self_modify_propose),
        ("can self modify low-risk", test_can_self_modify_low_risk),
        ("can self modify full", test_can_self_modify_full),
        ("can self modify none", test_can_self_modify_none),
        ("get adaptation limits empty", test_get_adaptation_limits_empty),
        ("get adaptation limits parsed", test_get_adaptation_limits_parsed),
        ("is change prohibited", test_is_change_prohibited),
        ("get escalation config defaults", test_get_escalation_config_defaults),
        ("get escalation config configured", test_get_escalation_config_configured),
        ("should escalate cost", test_should_escalate_cost),
        ("should escalate safety", test_should_escalate_safety),
        ("should escalate unconfigured", test_should_escalate_unconfigured),
        ("format escalation message", test_format_escalation_message),
        ("get allowed capabilities empty", test_get_allowed_capabilities_empty),
        ("get allowed capabilities from profile", test_get_allowed_capabilities_from_profile),
        ("is capability allowed no profile", test_is_capability_allowed_no_profile),
        ("is capability allowed with profile", test_is_capability_allowed_with_profile),
        ("get forbidden actions empty", test_get_forbidden_actions_empty),
        ("get forbidden actions parsed", test_get_forbidden_actions_parsed),
        ("is action forbidden", test_is_action_forbidden),
    ]

    print("=== Phase C Communicator Wiring — Validation ===")
    print()

    passed = []
    failed = []

    for name, fn in tests:
        try:
            fn()
            passed.append(name)
            print(f"  ✓ {name}")
        except AssertionError as e:
            failed.append((name, str(e)))
            print(f"  ✗ {name}: {e}")
        except Exception as e:
            failed.append((name, str(e)))
            print(f"  ✗ {name}: {e}")

    print()
    print(f"=== RESULTS: {len(passed)}/{len(tests)} passed ===")

    if failed:
        print()
        print("FAILURES:")
        for name, error in failed:
            print(f"  - {name}: {error}")
        sys.exit(1)
    else:
        print()
        print("All scenarios passed!")
        sys.exit(0)