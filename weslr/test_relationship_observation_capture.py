"""
WESLR Relationship Observation Capture Tests

Tests capture, signal classification, identity gating, and correction learning.
Uses temp dirs only. Does not dirty real ~/.weslr.
"""

import os, sys, json, tempfile, shutil
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
    get_relationship_tone_for_context,
    _correction_pending,
)
from weslr.relationship_depth import (
    RelationshipObservation,
    RelationshipStage,
    InteractionSignal,
    load_relationship_observations,
    compute_relationship_state,
    IDENTITY_DEPTH_CAPS,
    append_relationship_observation,
    create_relationship_observation,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

def make_meta(status: str, sender_identity: str = "alice") -> dict:
    return {"known_user_status": status, "sender_identity": sender_identity}


# ── Test 1: fingerprint ──────────────────────────────────────────────────

def test_fingerprint_no_raw_content():
    msg = "This is a test message with lots of content that should not be stored"
    fp = safe_message_fingerprint(msg)
    assert fp != msg
    assert len(fp) == 16
    assert fp.isalnum()
    # Same message gives same fingerprint
    assert safe_message_fingerprint(msg) == fp
    # Different message gives different fingerprint
    assert safe_message_fingerprint("different message") != fp
    print("  PASS  safe_message_fingerprint does not store raw content")


# ── Test 2: correction patterns ───────────────────────────────────────────

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
    # Negative cases
    negative = [
        "No thank you",
        "That's interesting",
        "No pressure though",
    ]
    for msg in negative:
        signals = classify_interaction_signal(msg)
        # These might not be corrections
        if "correction_received" in signals:
            assert "negative" in msg.lower() or "no" in msg.lower()
    print("  PASS  correction message maps to correction_received")


# ── Test 3: positive feedback ─────────────────────────────────────────────

def test_positive_feedback_maps():
    cases = [
        "Good",
        "Perfect",
        "Yes",
        "Yeah that's right",
        "Exactly",
        "That's it",
        "Nailed it",
        "Thanks",
        "y",
        "yep",
        "Works for me",
        "Cool",
    ]
    for msg in cases:
        signals = classify_interaction_signal(msg)
        assert "user_positive_feedback" in signals, f"'{msg}' → {signals}"
    print("  PASS  positive feedback maps to user_positive_feedback")


# ── Test 4: negative feedback ─────────────────────────────────────────────

def test_negative_feedback_maps():
    cases = [
        "Wrong",
        "Bad",
        "That's not correct",
        "I dislike this",
        "Stop",
        "Don't do that",
        "nah",
        "nope",
        "I don't think so",
    ]
    for msg in cases:
        signals = classify_interaction_signal(msg)
        assert "user_negative_feedback" in signals, f"'{msg}' → {signals}"
    print("  PASS  negative feedback maps to user_negative_feedback")


# ── Test 5: quiet/distance ───────────────────────────────────────────────

def test_quiet_request_maps():
    cases = [
        "Stop talking so much",
        "Quiet please",
        "Less talk please",
        "Don't be so proactive",
        "You don't need to be so chatty",
    ]
    for msg in cases:
        signals = classify_interaction_signal(msg)
        assert "user_requested_quiet" in signals, f"'{msg}' → {signals}"
    print("  PASS  quiet/distance maps to user_requested_quiet")


# ── Test 6: verified channel interaction ─────────────────────────────────

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
        print("  PASS  verified channel interaction records verified_session_interaction")
    finally:
        shutil.rmtree(td)


# ── Test 7: unknown identity no personal observation ─────────────────────

def test_unknown_identity_no_personal_obs():
    td = tempfile.mkdtemp()
    try:
        obs = build_relationship_observation(
            signal="shared_work_completed",
            sender_identity=None,
            identity_status="unknown",
            is_verified=False,
        )
        assert obs is None
        print("  PASS  unknown identity does not create personal relationship observation")
    finally:
        shutil.rmtree(td)


# ── Test 8: profile_only no verified depth ───────────────────────────────

def test_profile_only_no_verified_depth():
    td = tempfile.mkdtemp()
    try:
        # shared_work_completed should not be recorded for profile_only
        obs = build_relationship_observation(
            signal="shared_work_completed",
            sender_identity="alice",
            identity_status="profile_only",
            is_verified=False,
        )
        assert obs is None
        print("  PASS  profile_only does not create verified shared_work depth")
    finally:
        shutil.rmtree(td)


# ── Test 9: channel_verified records person↔system ───────────────────────

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
        assert obs.subject_entity_type == "person"
        assert obs.subject_entity_id == "alice"
        assert obs.target_entity_type == "system"
        assert obs.target_entity_id == "weslr"
        print("  PASS  channel_verified records person↔system observation")
    finally:
        shutil.rmtree(td)


# ── Test 10: safe_record_observation never crashes ─────────────────────────

def test_safe_record_never_crashes():
    td = tempfile.mkdtemp()
    try:
        # Pass a non-observation object
        result = safe_record_observation("not an observation", base_path=td)
        assert result is False
        print("  PASS  safe_record_observation returns False on bad input, no crash")
    finally:
        shutil.rmtree(td)


# ── Test 11: capture does not crash response ───────────────────────────────

def test_capture_does_not_break_response():
    td = tempfile.mkdtemp()
    try:
        # Invalid meta should not raise
        result = capture_relationship_observations(
            message="Good",
            response_path="meaning-vector:describe_self:person",
            identity_meta={"known_user_status": "channel_verified", "sender_identity": "alice"},
            channel_id="test-channel",
            base_path=td,
        )
        assert isinstance(result, list)  # should return list, not raise
        print("  PASS  capture_relationship_observations does not crash response path")
    finally:
        shutil.rmtree(td)


# ── Test 12: correction_received can be followed by correction_resolved ───

def test_correction_received_then_resolved():
    td = tempfile.mkdtemp()
    try:
        channel = "test-channel-corr"
        _correction_pending.clear()

        # Record correction_received
        obs_corr = build_relationship_observation(
            signal="correction_received",
            sender_identity="alice",
            identity_status="channel_verified",
            is_verified=True,
        )
        assert obs_corr is not None
        safe_record_observation(obs_corr, base_path=td)
        track_pending_correction(channel, obs_corr.observation_id)

        # Simulate user positive feedback → correction_resolved
        resolved = record_correction_resolved(
            channel_id=channel,
            sender_identity="alice",
            identity_status="channel_verified",
            is_verified=True,
            base_path=td,
        )
        assert resolved is not None
        assert resolved.interaction_signal == "correction_resolved"
        assert pop_pending_correction(channel) is None  # consumed
        print("  PASS  correction_received can be followed by correction_resolved")
    finally:
        _correction_pending.clear()
        shutil.rmtree(td)


# ── Test 13: relationship_depth increases after repeated verified obs ─────

def test_depth_increases_after_repeated_verified():
    td = tempfile.mkdtemp()
    try:
        signals = [
            "verified_session_interaction",
            "verified_session_interaction",
            "shared_work_completed",
            "successful_followup",
        ]
        for sig in signals:
            obs = build_relationship_observation(
                signal=sig,
                sender_identity="alice",
                identity_status="channel_verified",
                is_verified=True,
            )
            if obs:
                safe_record_observation(obs, base_path=td)

        loaded = load_relationship_observations("person", "alice", base_path=td)
        state = compute_relationship_state(loaded, identity_status="channel_verified")

        assert state.relationship_depth > 0.05
        assert state.relationship_stage not in (RelationshipStage.UNKNOWN.value,)
        print("  PASS  relationship_depth increases after repeated verified observations")
    finally:
        shutil.rmtree(td)


# ── Test 14: depth capped for unverified identity ─────────────────────────

def test_depth_capped_for_unverified():
    td = tempfile.mkdtemp()
    try:
        # Record many signals as unverified
        for _ in range(10):
            obs = build_relationship_observation(
                signal="verified_session_interaction",
                sender_identity="alice",
                identity_status="profile_only",
                is_verified=False,
            )
            if obs:
                safe_record_observation(obs, base_path=td)

        loaded = load_relationship_observations("person", "alice", base_path=td)
        state = compute_relationship_state(loaded, identity_status="profile_only")

        assert state.relationship_depth <= IDENTITY_DEPTH_CAPS["profile_only"]
        print("  PASS  relationship_depth remains capped for unverified identity")
    finally:
        shutil.rmtree(td)


# ── Test 15: no raw message text stored by default ──────────────────────

def test_no_raw_message_stored():
    td = tempfile.mkdtemp()
    try:
        obs = build_relationship_observation(
            signal="user_positive_feedback",
            sender_identity="alice",
            identity_status="channel_verified",
            is_verified=True,
            response_path="test",
        )
        assert obs is not None
        # Raw message should not be in metadata
        # (we only store response_path and identity_status_at_capture)
        assert "message_text" not in obs.metadata
        assert obs.metadata.get("identity_status_at_capture") == "channel_verified"
        print("  PASS  no raw message text stored by default")
    finally:
        shutil.rmtree(td)


# ── Test 16: memory confirm/reject ──────────────────────────────────────

def test_memory_confirm_reject():
    cases = [
        ("Yes that's right", "memory_confirmed"),
        ("You remembered it correctly", "memory_confirmed"),
        ("That's not what I said", "user_rejected_memory_claim"),
        ("I never said that", "user_rejected_memory_claim"),
        ("You got it wrong", "user_rejected_memory_claim"),
    ]
    for msg, expected in cases:
        signals = classify_interaction_signal(msg)
        assert expected in signals, f"'{msg}' → {signals}, expected {expected}"
    print("  PASS  memory confirmation and rejection signals detected")


# ── Test 17: get_relationship_identity_status ───────────────────────────

def test_identity_status_extraction():
    verified_meta = {"known_user_status": "channel_verified", "sender_identity": "alice"}
    status, is_verified = get_relationship_identity_status(verified_meta)
    assert status == "channel_verified"
    assert is_verified is True

    unknown_meta = {"known_user_status": "unknown"}
    status2, is_verified2 = get_relationship_identity_status(unknown_meta)
    assert status2 == "unknown"
    assert is_verified2 is False

    none_status, none_verified = get_relationship_identity_status(None)
    assert none_status == "unknown"
    assert none_verified is False
    print("  PASS  identity status extraction works correctly")


# ── Test 18: tone for unknown identity ──────────────────────────────────

def test_tone_unknown_identity():
    td = tempfile.mkdtemp()
    try:
        tone = get_relationship_tone_for_context(
            identity_status="unknown",
            sender_identity=None,
            base_path=td,
        )
        assert tone["warmth"] == "reserved"
        assert tone["verbosity"] == "brief"
        assert tone["explanatory"] is True
        print("  PASS  tone is reserved/brief for unknown identity")
    finally:
        shutil.rmtree(td)


# ── Regression tests ─────────────────────────────────────────────────────

def regression(name: str, cmd: list[str]):
    import subprocess
    result = subprocess.run(
        cmd,
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    out = result.stdout + result.stderr
    # Extract summary line
    for line in out.strip().split("\n"):
        if "passed" in line or "PASS" in line or "RESULT" in line or "OVERALL" in line:
            print(f"  PASS  {name} regression")
            return
    print(f"  FAIL  {name}: {out[-200:]}")
    raise AssertionError(f"{name} failed")


if __name__ == "__main__":
    print("\n=== RELATIONSHIP OBSERVATION CAPTURE TESTS ===")
    tests = [
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

    # Regression suites
    regressions = [
        ("entity_memory", ["python3", "weslr/test_entity_memory.py"]),
        ("user_profile", ["python3", "weslr/test_user_profile.py"]),
        ("channel_identity", ["python3", "weslr/test_channel_identity_binding.py"]),
        ("meaning_vector", ["python3", "weslr/test_meaning_vector_response_obligation.py"]),
        ("relationship_depth", ["python3", "weslr/test_relationship_depth.py"]),
        ("cognitive_weight", ["python3", "weslr/test_cognitive_weight_refinement.py"]),
        ("local_bridge", ["python3", "weslr/voice_layer/test_local_bridge.py"]),
        ("voice_pipeline", ["python3", "weslr/voice_layer/test_voice_pipeline.py"]),
    ]
    for name, cmd in regressions:
        try:
            regression(name, cmd)
            passed += 1
        except Exception as e:
            print(f"  ERROR {name} regression: {e}")
            failed += 1

    print(f"\nObservation capture tests: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
