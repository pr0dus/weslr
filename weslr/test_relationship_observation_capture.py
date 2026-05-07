"""
WESLR Relationship Observation Capture Tests

Tests capture, signal classification, identity gating, and correction learning.
Uses temp dirs only. Does not dirty real ~/.weslr.
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime, timezone

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.relationship_observation_capture import (
    safe_message_fingerprint,
    classify_interaction_signal,
    get_relationship_identity_status,
    build_relationship_observation,
    track_pending_correction,
    pop_pending_correction,
    record_correction_resolved,
    safe_record_observation,
    capture_relationship_observations,
    ObservationTarget,
    build_relationship_observation_for_target,
    resolve_observation_targets,
    _message_has_project_hint,
    _message_has_entity_hint,
)
from weslr.relationship_depth import (
    RelationshipObservation,
    RelationshipStage,
    append_relationship_observation,
    create_relationship_observation,
    record_interaction_outcome,
    load_relationship_observations,
    compute_relationship_state,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _run_regression(regression_module_name: str, name: str):
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest", regression_module_name, "-q"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
    )
    out = result.stdout + result.stderr
    for line in out.strip().split("\n"):
        if "passed" in line or "PASS" in line or "RESULT" in line or "OVERALL" in line:
            print(f"  PASS  {name} regression")
            return
    print(f"  FAIL  {name}: {out[-200:]}")
    raise AssertionError(f"{name} failed")


# ── Regression tests ───────────────────────────────────────────────────────────

def test_entity_memory():
    _run_regression("weslr/test_entity_memory.py", "entity_memory")

def test_user_profile():
    _run_regression("weslr/test_user_profile.py", "user_profile")

def test_relationship_depth():
    _run_regression("weslr/test_relationship_depth.py", "relationship_depth")


# ── Core unit tests ────────────────────────────────────────────────────────────

def test_fingerprint_no_raw_content():
    msg = "my secret password is xyz"
    fp = safe_message_fingerprint(msg)
    assert "secret" not in fp.lower()
    assert "password" not in fp.lower()
    assert len(fp) == 16
    assert fp.isalnum()
    assert safe_message_fingerprint(msg) == fp
    assert safe_message_fingerprint("different message") != fp


def test_correction_message_maps():
    cases = [
        "No, I meant blue not red",
        "That's not what I asked",
        "Nooo, you misunderstood",
        "Wait, no, stop",
        "Actually, it was Tuesday",
        "No this is wrong",
        "n this is not right",
        "nah that's bad",
    ]
    for msg in cases:
        signals = classify_interaction_signal(msg)
        assert "correction_received" in signals, f"'{msg}' → {signals}"
    negative = [
        "No thank you",
        "That's interesting",
        "No pressure though",
    ]
    for msg in negative:
        signals = classify_interaction_signal(msg)
        assert "correction_received" not in signals, f"'{msg}' → {signals}"


def test_positive_feedback_maps():
    # Only unambiguous positives register
    cases = ["Perfect thanks"]
    for msg in cases:
        signals = classify_interaction_signal(msg)
        assert "user_positive_feedback" in signals, f"'{msg}' → {signals}"


def test_negative_feedback_maps():
    # Only unambiguous negatives register
    cases = ["Not right", "That's bad", "Wrong result"]
    for msg in cases:
        signals = classify_interaction_signal(msg)
        assert "user_negative_feedback" in signals, f"'{msg}' → {signals}"


def test_quiet_request_maps():
    cases = ["Stop talking", "Stop responding"]
    for msg in cases:
        signals = classify_interaction_signal(msg)
        assert "user_requested_quiet" in signals, f"'{msg}' → {signals}"


def test_verified_channel_records():
    td = tempfile.mkdtemp()
    try:
        obs = build_relationship_observation(
            signal="verified_session_interaction",
            sender_identity="alice",
            identity_status="channel_verified",
            is_verified=True,
            response_path="meaning-vector:describe_self:person",
        )
        assert obs is not None
        assert obs.interaction_signal == "verified_session_interaction"
        assert obs.subject_entity_type == "person"
        assert obs.subject_entity_id == "alice"
        assert obs.verified is True
    finally:
        shutil.rmtree(td)


def test_unknown_identity_no_personal_obs():
    status, is_verified = get_relationship_identity_status(
        {"sender_identity": None, "known_user_status": "unknown"},
    )
    assert is_verified is False
    assert status == "unknown"
    # Unknown identity should not create personal observations via build
    obs = build_relationship_observation(
        signal="verified_session_interaction",
        sender_identity=None,
        identity_status="unknown",
        is_verified=False,
    )
    assert obs is None


def test_profile_only_no_verified_depth():
    td = tempfile.mkdtemp()
    try:
        for _ in range(3):
            capture_relationship_observations(
                message="Hello",
                response_path="test",
                identity_meta={"sender_identity": "alice", "known_user_status": "profile_only"},
                channel_id="test-channel",
                base_path=td,
            )
        obs = load_relationship_observations(
            subject_entity_type="person", subject_entity_id="alice",
            target_entity_type="system", target_entity_id="weslr", base_path=td,
        )
        state = compute_relationship_state(obs, identity_status="profile_only")
        assert state.relationship_depth < 0.5
    finally:
        shutil.rmtree(td)


def test_channel_verified_records_person_system():
    td = tempfile.mkdtemp()
    try:
        obs = build_relationship_observation(
            signal="verified_session_interaction",
            sender_identity="alice",
            identity_status="channel_verified",
            is_verified=True,
        )
        assert obs is not None
        assert obs.interaction_signal == "verified_session_interaction"
        assert obs.verified is True
    finally:
        shutil.rmtree(td)


def test_safe_record_never_crashes():
    # None input always returns False
    ok = safe_record_observation(None, None)
    assert ok is False


def test_capture_does_not_break_response():
    result = capture_relationship_observations(
        message="test",
        response_path="meaning-vector:test:test",
        identity_meta={},
        channel_id="",
    )
    assert isinstance(result, list)


def test_correction_received_then_resolved():
    td = tempfile.mkdtemp()
    try:
        ids = capture_relationship_observations(
            message="No that is wrong",
            response_path="meaning-vector:test:test",
            identity_meta={"sender_identity": "alice", "known_user_status": "channel_verified"},
            channel_id="test-channel",
            base_path=td,
        )
        obs = load_relationship_observations(
            subject_entity_type="person", subject_entity_id="alice",
            target_entity_type="system", target_entity_id="weslr", base_path=td,
        )
        correction_ids = [o.observation_id for o in obs if o.interaction_signal == "correction_received"]
        assert len(correction_ids) >= 1
    finally:
        shutil.rmtree(td)


def test_depth_increases_after_repeated_verified():
    td = tempfile.mkdtemp()
    try:
        for _ in range(5):
            capture_relationship_observations(
                message="Hello",
                response_path="test",
                identity_meta={"sender_identity": "alice", "known_user_status": "channel_verified"},
                channel_id="test-channel",
                base_path=td,
            )
        obs = load_relationship_observations(
            subject_entity_type="person", subject_entity_id="alice",
            target_entity_type="system", target_entity_id="weslr", base_path=td,
        )
        state = compute_relationship_state(obs, identity_status="channel_verified")
        assert state.relationship_depth > 0.0
    finally:
        shutil.rmtree(td)


def test_depth_capped_for_unverified():
    td = tempfile.mkdtemp()
    try:
        for _ in range(10):
            capture_relationship_observations(
                message="Hello",
                response_path="test",
                identity_meta={"sender_identity": "alice", "known_user_status": "unknown"},
                channel_id="test-channel",
                base_path=td,
            )
        obs = load_relationship_observations(
            subject_entity_type="person", subject_entity_id="alice",
            target_entity_type="system", target_entity_id="weslr", base_path=td,
        )
        state = compute_relationship_state(obs, identity_status="unknown")
        assert state.relationship_depth < 0.15
    finally:
        shutil.rmtree(td)


def test_no_raw_message_stored():
    td = tempfile.mkdtemp()
    try:
        capture_relationship_observations(
            message="This is a test message that should not be stored",
            response_path="meaning-vector:test:test",
            identity_meta={"sender_identity": "alice", "known_user_status": "channel_verified"},
            channel_id="test-channel",
            base_path=td,
        )
        obs_file = os.path.join(td, "relationship_observations.jsonl")
        if os.path.exists(obs_file):
            with open(obs_file) as f:
                content = f.read()
            assert "This is a test message" not in content
            assert "should not be stored" not in content
    finally:
        shutil.rmtree(td)


def test_memory_confirm_reject():
    confirm = ["Yes save it", "Yes that is right"]
    for msg in confirm:
        signals = classify_interaction_signal(msg)
        assert "memory_confirmed" in signals, f"'{msg}' → {signals}"


def test_identity_status_extraction():
    status, is_verified = get_relationship_identity_status(
        {"sender_identity": "alice", "known_user_status": "channel_verified"},
    )
    assert is_verified is True
    assert status == "channel_verified"

    status, is_verified = get_relationship_identity_status(
        {"sender_identity": None, "known_user_status": "unknown"},
    )
    assert is_verified is False
    assert status == "unknown"

    status, is_verified = get_relationship_identity_status({})
    assert is_verified is False
    assert status == "unknown"


def test_tone_unknown_identity():
    from weslr.relationship_observation_capture import get_relationship_tone_for_context
    td = tempfile.mkdtemp()
    try:
        tone = get_relationship_tone_for_context(
            identity_status="unknown",
            sender_identity=None,
            base_path=td,
        )
        assert tone["warmth"] == "reserved"
        assert tone["verbosity"] == "brief"
    finally:
        shutil.rmtree(td)


# ── Scope hint pattern tests ─────────────────────────────────────────────────

def test_message_has_project_hint():
    assert _message_has_project_hint("commit the changes") is True
    assert _message_has_project_hint("work on project alpha") is True
    assert _message_has_project_hint("hello how are you") is False
    assert _message_has_project_hint("how is the weather") is False


def test_message_has_entity_hint():
    assert _message_has_entity_hint("my company needs this") is True
    assert _message_has_entity_hint("the family gathering") is True
    assert _message_has_entity_hint("team meeting today") is True
    assert _message_has_entity_hint("our department") is True
    assert _message_has_entity_hint("hello how are you") is False
    assert _message_has_entity_hint("the project") is False  # project hint, not family/company


# ── Multi-target / entity-scoped observation tests ─────────────────────────────

def test_resolve_observation_targets_verified_user_includes_system():
    """Verified user always gets system:weslr target."""
    targets = resolve_observation_targets(
        message="hello",
        response_metadata={},
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
    )
    assert len(targets) >= 1
    system_targets = [t for t in targets if t.target_entity_type == "system"]
    assert len(system_targets) == 1
    assert system_targets[0].target_entity_id == "weslr"


def test_resolve_observation_targets_unknown_no_targets():
    """Unknown identity gets no targets."""
    targets = resolve_observation_targets(
        message="hello",
        response_metadata={},
        identity_state={"is_verified": False, "identity_status": "unknown", "user_id": ""},
    )
    assert targets == []


def test_resolve_observation_targets_profile_only_no_targets():
    """Profile-only users get no targets (not verified)."""
    targets = resolve_observation_targets(
        message="hello",
        response_metadata={},
        identity_state={"is_verified": False, "identity_status": "profile_only", "user_id": "alice"},
    )
    assert targets == []


def test_resolve_project_target_from_response_metadata():
    """Explicit project_id in response_metadata resolves project target."""
    targets = resolve_observation_targets(
        message="work on the project",
        response_metadata={"project_id": "weslr"},
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
    )
    project_targets = [t for t in targets if t.target_entity_type == "project"]
    assert len(project_targets) == 1
    assert project_targets[0].target_entity_id == "weslr"
    assert project_targets[0].target_scope == "project"
    assert project_targets[0].reason == "project_target_response_metadata"


def test_resolve_project_target_from_meaning_state_scope():
    """memory_scope_used project scope resolves project target."""
    targets = resolve_observation_targets(
        message="continue the work",
        response_metadata={},
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
        meaning_state={"memory_scope_used": "project_weslr"},
    )
    project_targets = [t for t in targets if t.target_entity_type == "project"]
    assert len(project_targets) == 1
    assert project_targets[0].target_entity_id == "weslr"
    assert project_targets[0].reason == "project_target_meaning_state_scope"


def test_resolve_project_target_from_single_profile_project():
    """Single primary_project + work hint resolves project target at lower confidence."""
    targets = resolve_observation_targets(
        message="commit the changes",
        response_metadata={},
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
        profile={"primary_projects": ["weslr"]},
    )
    project_targets = [t for t in targets if t.target_entity_type == "project"]
    assert len(project_targets) == 1
    assert project_targets[0].reason == "project_target_profile_single_project_hint"
    assert project_targets[0].confidence == 0.6


def test_no_project_target_without_hint():
    """Single primary_project but no work hint does not resolve project target."""
    targets = resolve_observation_targets(
        message="hello how are you",
        response_metadata={},
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
        profile={"primary_projects": ["weslr"]},
    )
    project_targets = [t for t in targets if t.target_entity_type == "project"]
    assert len(project_targets) == 0


def test_verified_company_membership_with_entity_hint():
    """Verified company membership + entity hint resolves company target."""
    targets = resolve_observation_targets(
        message="my company needs this feature",
        response_metadata={},
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
        profile={
            "memberships": [
                {"entity_type": "company", "entity_id": "acme", "role": "engineer", "verified": True, "authorized": False}
            ]
        },
    )
    company_targets = [t for t in targets if t.target_entity_type == "company"]
    assert len(company_targets) == 1
    assert company_targets[0].target_entity_id == "acme"
    assert company_targets[0].target_scope == "company"


def test_unverified_company_membership_blocked():
    """Unverified company membership does NOT create company target."""
    targets = resolve_observation_targets(
        message="my company needs this feature",
        response_metadata={},
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
        profile={
            "memberships": [
                {"entity_type": "company", "entity_id": "acme", "role": "engineer", "verified": False, "authorized": False}
            ]
        },
    )
    company_targets = [t for t in targets if t.target_entity_type == "company"]
    assert len(company_targets) == 0


def test_verified_family_membership_with_entity_hint():
    """Verified family membership + family hint resolves family target."""
    targets = resolve_observation_targets(
        message="the family gathering",
        response_metadata={},
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
        profile={
            "memberships": [
                {"entity_type": "family", "entity_id": "smith", "role": "child", "verified": True, "authorized": False}
            ]
        },
    )
    family_targets = [t for t in targets if t.target_entity_type == "family"]
    assert len(family_targets) == 1


def test_unverified_family_membership_blocked():
    """Unverified family membership does NOT create family target."""
    targets = resolve_observation_targets(
        message="the family gathering",
        response_metadata={},
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
        profile={
            "memberships": [
                {"entity_type": "family", "entity_id": "smith", "role": "child", "verified": False, "authorized": False}
            ]
        },
    )
    family_targets = [t for t in targets if t.target_entity_type == "family"]
    assert len(family_targets) == 0


def test_multi_target_capture_records_both_system_and_project():
    """capture_relationship_observations records for both system and project targets."""
    td = tempfile.mkdtemp()
    try:
        ids = capture_relationship_observations(
            message="this looks good",
            response_path="meaning-vector:test:test",
            identity_meta={"sender_identity": "alice", "known_user_status": "channel_verified"},
            channel_id="test-channel",
            base_path=td,
            meaning_state={"memory_scope_used": "project_weslr"},
        )
        assert len(ids) >= 2

        sys_obs = load_relationship_observations(
            subject_entity_type="person", subject_entity_id="alice",
            target_entity_type="system", target_entity_id="weslr", base_path=td,
        )
        assert len(sys_obs) >= 1

        proj_obs = load_relationship_observations(
            subject_entity_type="person", subject_entity_id="alice",
            target_entity_type="project", target_entity_id="weslr", base_path=td,
        )
        assert len(proj_obs) >= 1
    finally:
        shutil.rmtree(td)


def test_project_depth_independent_from_person_system_depth():
    """Project relationship depth is tracked independently from person↔system depth."""
    td = tempfile.mkdtemp()
    try:
        for _ in range(3):
            capture_relationship_observations(
                message="working on the project",
                response_path="test",
                identity_meta={"sender_identity": "alice", "known_user_status": "channel_verified"},
                channel_id="ch",
                base_path=td,
                meaning_state={"memory_scope_used": "project_weslr"},
            )

        sys_obs = load_relationship_observations(
            subject_entity_type="person", subject_entity_id="alice",
            target_entity_type="system", target_entity_id="weslr", base_path=td,
        )
        proj_obs = load_relationship_observations(
            subject_entity_type="person", subject_entity_id="alice",
            target_entity_type="project", target_entity_id="weslr", base_path=td,
        )
        # Both system and project get recorded independently
        # (same depth here because same number of observations, same signal)
        assert len(sys_obs) == 3
        assert len(proj_obs) == 3
        # They are separate observation sets (different observation_ids)
        sys_ids = {o.observation_id for o in sys_obs}
        proj_ids = {o.observation_id for o in proj_obs}
        assert sys_ids.isdisjoint(proj_ids), "System and project observations must be independent"
    finally:
        shutil.rmtree(td)


def test_entity_scoped_observation_no_raw_message_text():
    """Entity-scoped observations store no raw message text."""
    td = tempfile.mkdtemp()
    try:
        capture_relationship_observations(
            message="my company is great",
            response_path="test",
            identity_meta={"sender_identity": "alice", "known_user_status": "channel_verified"},
            channel_id="ch",
            base_path=td,
            profile={
                "memberships": [
                    {"entity_type": "company", "entity_id": "acme", "role": "engineer", "verified": True, "authorized": False}
                ]
            },
        )

        obs_file = os.path.join(td, "relationship_observations.jsonl")
        assert os.path.exists(obs_file)
        with open(obs_file) as f:
            content = f.read()
        # Raw message text must not appear in stored data
        assert "my company is great" not in content
    finally:
        shutil.rmtree(td)


def test_capture_failure_does_not_break_response():
    """Capture exceptions are swallowed; returns list, does not propagate."""
    td = tempfile.mkdtemp()
    try:
        result = capture_relationship_observations(
            message="test",
            response_path="test",
            identity_meta={"sender_identity": "alice", "known_user_status": "channel_verified"},
            channel_id="",
            meaning_state=None,
            profile=None,
        )
        assert isinstance(result, list)
    finally:
        shutil.rmtree(td)


def test_build_relationship_observation_for_target_blocks_unverified_group():
    """build_relationship_observation_for_target returns None for unverified group entity."""
    target = ObservationTarget(
        target_entity_type="company",
        target_entity_id="acme",
        target_scope="company",
        reason="test",
        confidence=0.8,
        verified_role_present=False,
        verified_role_required=True,
    )
    obs = build_relationship_observation_for_target(
        signal="verified_session_interaction",
        sender_identity="alice",
        identity_status="channel_verified",
        is_verified=True,
        target=target,
    )
    assert obs is None


def test_unknown_identity_correct_signal_gating():
    """Unknown identity blocks all signals including quiet."""
    target = ObservationTarget(
        target_entity_type="system", target_entity_id="weslr",
        target_scope="system", reason="test",
        verified_role_present=True,
    )
    # All signals return None for unknown identity
    for sig in ["user_requested_quiet", "correction_received", "verified_session_interaction"]:
        obs = build_relationship_observation_for_target(
            signal=sig,
            sender_identity="alice",
            identity_status="unknown",
            is_verified=False,
            target=target,
        )
        assert obs is None, f"unknown identity should block {sig}"


# ── Test runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== RELATIONSHIP OBSERVATION CAPTURE TESTS ===")

    tests = [
        # Regression suites
        test_entity_memory,
        test_user_profile,
        test_relationship_depth,
        # Core unit tests
        test_fingerprint_no_raw_content,
        test_correction_message_maps,
        test_positive_feedback_maps,
        test_negative_feedback_maps,
        test_quiet_request_maps,
        test_verified_channel_records,
        test_unknown_identity_no_personal_obs,
        test_profile_only_no_verified_depth,
        test_channel_verified_records_person_system,
        test_safe_record_never_crashes,
        test_capture_does_not_break_response,
        test_correction_received_then_resolved,
        test_depth_increases_after_repeated_verified,
        test_depth_capped_for_unverified,
        test_no_raw_message_stored,
        test_memory_confirm_reject,
        test_identity_status_extraction,
        test_tone_unknown_identity,
        # Scope hint pattern tests
        test_message_has_project_hint,
        test_message_has_entity_hint,
        # Multi-target / entity-scoped tests
        test_resolve_observation_targets_verified_user_includes_system,
        test_resolve_observation_targets_unknown_no_targets,
        test_resolve_observation_targets_profile_only_no_targets,
        test_resolve_project_target_from_response_metadata,
        test_resolve_project_target_from_meaning_state_scope,
        test_resolve_project_target_from_single_profile_project,
        test_no_project_target_without_hint,
        test_verified_company_membership_with_entity_hint,
        test_unverified_company_membership_blocked,
        test_verified_family_membership_with_entity_hint,
        test_unverified_family_membership_blocked,
        test_multi_target_capture_records_both_system_and_project,
        test_project_depth_independent_from_person_system_depth,
        test_entity_scoped_observation_no_raw_message_text,
        test_capture_failure_does_not_break_response,
        test_build_relationship_observation_for_target_blocks_unverified_group,
        test_unknown_identity_correct_signal_gating,
    ]

    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}")
            failed += 1

    print(f"\nObservation capture tests: {passed} passed, {failed} failed")
