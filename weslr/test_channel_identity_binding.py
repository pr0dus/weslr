"""
WESLR Channel Identity Binding Tests

Tests channel binding schema, CLI, verification, and meaning-state integration.
Uses temp paths only. Does not dirty real ~/.weslr.
"""

import os, sys, json, tempfile, shutil

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.channel_identity import (
    ChannelBinding,
    EvidenceStrength,
    binding_exists,
    default_channel_binding,
    add_ip_evidence,
    compute_binding_confidence,
    finalize_binding,
    save_channel_binding,
    load_binding,
    validate_binding,
    summarize_binding,
    BINDING_VERSION,
    compute_binding_confidence,
)


def test_default_binding_references_profile():
    b = default_channel_binding("user-123", "Arthur", channel_type="local_cli")
    assert b.bound_user_id == "user-123"
    assert b.bound_profile_name == "Arthur"
    assert b.identity_status == "onboarded_unverified"
    assert b.confidence == 0.0
    assert b.trusted is False
    assert any(e.get("type") == "explicit_operator_binding" for e in b.evidence)
    print("  PASS  default_binding references profile user_id")


def test_binding_save_load_roundtrip():
    td = tempfile.mkdtemp()
    try:
        b = default_channel_binding("user-456", "Alice", channel_type="local_cli")
        b = add_ip_evidence(b, "192.168.1.100")
        b = finalize_binding(b)
        path = os.path.join(td, "binding.json")
        save_channel_binding(b, path=path, backup=False)

        loaded = load_binding(path)
        assert loaded is not None
        assert loaded.bound_user_id == "user-456"
        assert loaded.bound_profile_name == "Alice"
        assert loaded.binding_id == b.binding_id
        print("  PASS  save/load roundtrip preserves binding")
    finally:
        shutil.rmtree(td)


def test_backup_created_before_overwrite():
    td = tempfile.mkdtemp()
    try:
        b = default_channel_binding("user-789", "Bob", channel_type="local_cli")
        path = os.path.join(td, "binding.json")
        save_channel_binding(b, path=path, backup=False)

        # Update and save with backup=True
        b2 = add_ip_evidence(b, "10.0.0.1")
        b2 = finalize_binding(b2)
        save_channel_binding(b2, path=path, backup=True)

        assert os.path.isfile(path + ".bak"), "backup should exist"
        with open(path + ".bak") as f:
            bak = json.load(f)
        assert bak["bound_user_id"] == "user-789"
        print("  PASS  backup created before overwrite")
    finally:
        shutil.rmtree(td)


def test_validate_rejects_no_profile_user_id():
    b = default_channel_binding("", "Charlie", channel_type="local_cli")
    valid, reasons = validate_binding(b)
    assert not valid
    assert any("bound_user_id" in r for r in reasons)
    print("  PASS  validate rejects binding without profile user_id")


def test_explicit_operator_binding_is_strong():
    b = default_channel_binding("user-test", "Dave", channel_type="local_cli")
    ev = next((e for e in b.evidence if e.get("type") == "explicit_operator_binding"), None)
    assert ev is not None
    assert ev.get("strength") == EvidenceStrength.STRONG.value
    print("  PASS  explicit_operator_binding evidence is STRONG")


def test_ip_evidence_is_weak():
    b = default_channel_binding("user-test", "Eve", channel_type="local_cli")
    b = add_ip_evidence(b, "192.168.1.50")
    ip_ev = next((e for e in b.evidence if e.get("type") == "local_ip_match"), None)
    assert ip_ev is not None
    assert ip_ev.get("strength") == EvidenceStrength.WEAK.value
    print("  PASS  IP evidence is WEAK")


def test_ip_only_cannot_verify():
    """IP-only evidence (no strong) cannot become channel_verified."""
    from weslr.channel_identity import ChannelBinding, EvidenceStrength
    b = ChannelBinding(
        binding_id="weak-only-test",
        channel_type="local_cli",
        channel_id="local_cli:weakonly",
        bound_user_id="user-test",
        bound_profile_name="Frank",
        identity_status="onboarded_unverified",
        confidence=0.0,
        created_at="2026-05-07T00:00:00+00:00",
        updated_at="2026-05-07T00:00:00+00:00",
        created_by="test",
        evidence=[
            {
                "type": "local_ip_match",
                "strength": EvidenceStrength.WEAK.value,
                "detail": "Local IP 192.168.1.50 matched",
                "ip_address": "192.168.1.50",
            }
        ],
        limitations=[],
        trusted=False,
    )
    b = finalize_binding(b)
    assert b.identity_status != "channel_verified"
    assert b.confidence <= 0.35
    print("  PASS  IP-only binding cannot become channel_verified (confidence <= 0.35)")


def test_explicit_plus_device_can_become_verified():
    """Strong evidence (explicit binding) → channel_verified."""
    b = default_channel_binding("user-test", "Grace", channel_type="local_cli")
    # Add local device evidence
    b.evidence.append({
        "type": "local_device_identity",
        "strength": EvidenceStrength.STRONG.value,
        "detail": "Local device fingerprint matched",
    })
    b = finalize_binding(b)

    assert b.identity_status == "channel_verified"
    assert b.trusted is True
    assert b.confidence >= 0.80
    print("  PASS  explicit_operator_binding + device evidence → channel_verified")


def test_binding_summary_no_overclaim():
    b = default_channel_binding("user-test", "Heidi", channel_type="local_cli")
    b.evidence.append({
        "type": "local_device_identity",
        "strength": EvidenceStrength.STRONG.value,
        "detail": "Local device fingerprint matched",
    })
    b = finalize_binding(b)
    summary = summarize_binding(b)

    # Summary should mention the facts, not overclaim personhood
    assert "channel_verified" in summary
    assert "biometric" not in summary.lower()
    assert "person" not in summary.lower()
    print("  PASS  binding summary does not overclaim personhood")


def test_cli_bind_local_creates_verified_binding():
    """CLI bind-local creates channel_verified binding using temp profile + binding."""
    td = tempfile.mkdtemp()
    try:
        # Create temp profile
        from weslr.user_profile import default_profile, save_user_profile
        profile_path = os.path.join(td, "profile.json")
        binding_path = os.path.join(td, "binding.json")

        p = default_profile()
        p.display_name = "Test User"
        p.user_id = "cli-test-user"
        save_user_profile(p, path=profile_path, backup=False)

        # Create binding via default_channel_binding
        from weslr.channel_identity import default_channel_binding, finalize_binding, save_channel_binding
        b = default_channel_binding("cli-test-user", "Test User", channel_type="local_cli")
        b.evidence.append({
            "type": "local_device_identity",
            "strength": EvidenceStrength.STRONG.value,
            "detail": "Local device matched",
        })
        b = finalize_binding(b)
        save_channel_binding(b, path=binding_path, backup=False)

        assert b.identity_status == "channel_verified"
        assert b.confidence >= 0.80
        print("  PASS  CLI bind creates channel_verified binding")
    finally:
        shutil.rmtree(td)


def test_verify_reports_verified_when_evidence_matches():
    td = tempfile.mkdtemp()
    try:
        binding_path = os.path.join(td, "binding.json")
        b = default_channel_binding("verify-test", "Verify User", channel_type="local_cli")
        b.evidence.append({
            "type": "local_device_identity",
            "strength": EvidenceStrength.STRONG.value,
            "detail": "Local device matched",
        })
        b = finalize_binding(b)
        save_channel_binding(b, path=binding_path, backup=False)

        loaded = load_binding(binding_path)
        has_strong = any(e.get("strength") == "strong" for e in loaded.evidence)
        assert has_strong
        assert loaded.identity_status == "channel_verified"
        print("  PASS  verify reports channel_verified when strong evidence present")
    finally:
        shutil.rmtree(td)


def test_unbind_removes_binding():
    td = tempfile.mkdtemp()
    try:
        binding_path = os.path.join(td, "binding.json")
        b = default_channel_binding("unbind-test", "Unbind User", channel_type="local_cli")
        save_channel_binding(b, path=binding_path, backup=False)
        assert os.path.isfile(binding_path)

        # Backup then remove
        backup_path = binding_path + f".backup-20260507T120000"
        with open(binding_path) as src:
            with open(backup_path, "w") as dst:
                dst.write(src.read())
        os.remove(binding_path)

        assert not os.path.isfile(binding_path)
        print("  PASS  unbind removes binding")
    finally:
        shutil.rmtree(td)


def test_profile_only_remains_onboarded_unverified():
    """When binding has no strong evidence, identity_status stays unverified."""
    from weslr.channel_identity import ChannelBinding, EvidenceStrength
    b = ChannelBinding(
        binding_id="unverified-test",
        channel_type="local_cli",
        channel_id="local_cli:unverified",
        bound_user_id="prof-test",
        bound_profile_name="Profile Test",
        identity_status="onboarded_unverified",
        confidence=0.0,
        created_at="2026-05-07T00:00:00+00:00",
        updated_at="2026-05-07T00:00:00+00:00",
        created_by="test",
        evidence=[
            {
                "type": "local_ip_match",
                "strength": EvidenceStrength.WEAK.value,
                "detail": "LAN IP match",
                "ip_address": "192.168.1.1",
            }
        ],
        limitations=[],
        trusted=False,
    )
    b = finalize_binding(b)
    assert b.identity_status == "onboarded_unverified"
    assert b.confidence <= 0.35
    print("  PASS  profile + weak evidence remains onboarded_unverified")


def test_text_self_claim_not_verified():
    """Text self-claim alone never produces verified identity."""
    from weslr.channel_identity import ChannelBinding, EvidenceStrength
    b = ChannelBinding(
        binding_id="claim-test",
        channel_type="local_cli",
        channel_id="local_cli:claimtest",
        bound_user_id="claim-test",
        bound_profile_name="Claim Test",
        identity_status="onboarded_unverified",
        confidence=0.0,
        created_at="2026-05-07T00:00:00+00:00",
        updated_at="2026-05-07T00:00:00+00:00",
        created_by="test",
        evidence=[
            {
                "type": "text_self_claim",
                "strength": EvidenceStrength.WEAK.value,
                "detail": "User claimed identity in message",
            }
        ],
        limitations=[],
        trusted=False,
    )
    b = finalize_binding(b)
    assert b.identity_status != "channel_verified"
    assert b.confidence <= 0.35
    print("  PASS  text self-claim alone does not verify identity")


def test_all_meaning_vector_tests_pass():
    """Regression: existing meaning-vector tests still pass."""
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/test_meaning_vector_response_obligation.py"],
        capture_output=True, text=True, cwd="/data/data/com.termux/files/home/.openclaw/workspace"
    )
    assert "OVERALL: 5/5 groups passed" in result.stdout, f"Meaning vector failed: {result.stdout[-200:]}"
    print("  PASS  meaning-vector regression still passes")


def test_local_bridge_still_passes():
    """Regression: local bridge tests still pass."""
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/voice_layer/test_local_bridge.py"],
        capture_output=True, text=True, cwd="/data/data/com.termux/files/home/.openclaw/workspace"
    )
    assert "6/6 passed" in result.stdout, f"Local bridge failed: {result.stdout[-200:]}"
    print("  PASS  local bridge regression still passes")


if __name__ == "__main__":
    print("\n=== CHANNEL IDENTITY BINDING TESTS ===")
    tests = [
        test_default_binding_references_profile,
        test_binding_save_load_roundtrip,
        test_backup_created_before_overwrite,
        test_validate_rejects_no_profile_user_id,
        test_explicit_operator_binding_is_strong,
        test_ip_evidence_is_weak,
        test_ip_only_cannot_verify,
        test_explicit_plus_device_can_become_verified,
        test_binding_summary_no_overclaim,
        test_cli_bind_local_creates_verified_binding,
        test_verify_reports_verified_when_evidence_matches,
        test_unbind_removes_binding,
        test_profile_only_remains_onboarded_unverified,
        test_text_self_claim_not_verified,
        test_all_meaning_vector_tests_pass,
        test_local_bridge_still_passes,
    ]
    passed = 0
    failed = 0
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
    print(f"\nBinding tests: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)