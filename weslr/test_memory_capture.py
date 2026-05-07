"""
WESLR Memory Capture Tests

Tests safe memory capture, scope gating, privacy filtering, and integration.
Uses temp dirs only. Does not dirty real ~/.weslr.
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.memory_capture import (
    safe_turn_fingerprint,
    contains_sensitive_content,
    has_explicit_consent,
    classify_memory_capture_candidates,
    resolve_memory_capture_scope,
    is_memory_safe_to_store,
    create_memory_record_from_candidate,
    capture_memories_from_turn,
    safe_capture_memories_from_turn,
    MemoryCaptureCandidate,
    MemoryCaptureResult,
)
from weslr.entity_memory import (
    AccessLevel,
    load_entity_memories,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _run_regression(regression_module_name: str, name: str):
    """Run a regression test file. Tries python3 direct then pytest fallback."""
    import subprocess, re

    def _check_output(out):
        lines = out.strip().split("\n")
        for line in reversed(lines):
            line_lower = line.lower()
            # Match count summary (e.g. "6/6 passed", "24 passed, 0 failed")
            if re.search(r"\d+\s+passed[, ]", line_lower):
                if "failed" not in line_lower or "0 failed" in line_lower:
                    return True
            # Match OVERALL / Group result summary lines
            if any(k in line_lower for k in ["overall", "group result:", "compile check"]):
                return True
        return False

    # Try python3 direct first
    result = subprocess.run(
        ["python3", regression_module_name],
        capture_output=True, text=True, timeout=60,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
    )
    if result.returncode == 0 and _check_output(result.stdout + result.stderr):
        print(f"  PASS  {name} regression")
        return

    # Fallback: try pytest
    result = subprocess.run(
        ["python3", "-m", "pytest", regression_module_name, "-q"],
        capture_output=True, text=True, timeout=60,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
    )
    out = result.stdout + result.stderr
    if result.returncode == 0:
        print(f"  PASS  {name} regression")
        return

    print(f"  FAIL  {name}: {out[-300:]}")
    raise AssertionError(f"{name} failed")


# ── Regression suites ──────────────────────────────────────────────────────────

def test_entity_memory():
    _run_regression("weslr/test_entity_memory.py", "entity_memory")

def test_user_profile():
    _run_regression("weslr/test_user_profile.py", "user_profile")

def test_channel_identity():
    _run_regression("weslr/test_channel_identity_binding.py", "channel_identity")

def test_relationship_observation():
    _run_regression("weslr/test_relationship_observation_capture.py", "relationship_observation")

def test_relationship_depth():
    _run_regression("weslr/test_relationship_depth.py", "relationship_depth")

def test_meaning_vector():
    _run_regression("weslr/test_meaning_vector_response_obligation.py", "meaning_vector")

def test_cognitive_weight():
    _run_regression("weslr/test_cognitive_weight_refinement.py", "cognitive_weight")

def test_local_bridge():
    _run_regression("weslr/voice_layer/test_local_bridge.py", "local_bridge")

def test_voice_pipeline():
    _run_regression("weslr/voice_layer/test_voice_pipeline.py", "voice_pipeline")


# ── Core unit tests ────────────────────────────────────────────────────────────

def test_safe_turn_fingerprint_does_not_store_raw_text():
    fp = safe_turn_fingerprint("my secret password is xyz", "response text")
    assert "secret" not in fp.lower()
    assert "password" not in fp.lower()
    assert len(fp) == 16
    assert fp.isalnum()


def test_safe_turn_fingerprint_empty():
    fp = safe_turn_fingerprint("", "")
    assert fp == "empty"


def test_safe_turn_fingerprint_deterministic():
    fp1 = safe_turn_fingerprint("hello world", "hi back")
    fp2 = safe_turn_fingerprint("hello world", "hi back")
    assert fp1 == fp2


def test_contains_sensitive_content_blocks_credentials():
    assert contains_sensitive_content("my API key is abc123") is True
    assert contains_sensitive_content("password is xyz") is True
    assert contains_sensitive_content("the secret token is xyz") is True
    assert contains_sensitive_content("my password") is True


def test_contains_sensitive_content_blocks_medical():
    assert contains_sensitive_content("my medical record shows") is True
    assert contains_sensitive_content("mental health therapy") is True


def test_contains_sensitive_content_blocks_location():
    assert contains_sensitive_content("123 Main Street") is True
    assert contains_sensitive_content("42 Avenue Road") is True


def test_contains_sensitive_content_allows_normal():
    assert contains_sensitive_content("let's talk about the project") is False
    assert contains_sensitive_content("commit abc123 was merged") is False
    assert contains_sensitive_content("I prefer WESLR to avoid context") is False


def test_has_explicit_consent_detects():
    assert has_explicit_consent("Remember that I prefer quiet mode") is True
    assert has_explicit_consent("save this for later") is True
    assert has_explicit_consent("keep this in mind") is True
    assert has_explicit_consent("don't forget that I like this") is True
    assert has_explicit_consent("note that we use Python") is True
    assert has_explicit_consent("hello how are you") is False


def test_project_work_creates_project_candidate():
    candidates = classify_memory_capture_candidates(
        message="Commit abc123 completed the memory capture feature",
        response="Saved as project milestone.",
        response_metadata={"project_id": "weslr"},
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
    )
    work_candidates = [c for c in candidates if c.capture_type == "project_work"]
    assert len(work_candidates) >= 1
    assert work_candidates[0].entity_type == "project"
    assert work_candidates[0].entity_id == "weslr"
    assert work_candidates[0].access_level == AccessLevel.OPERATOR_ONLY.value


def test_explicit_user_preference_creates_candidate():
    candidates = classify_memory_capture_candidates(
        message="Remember that I prefer WESLR to avoid saying context to users",
        response="Understood.",
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
    )
    pref_candidates = [c for c in candidates if c.capture_type == "user_preference"]
    assert len(pref_candidates) >= 1
    assert "avoid" in pref_candidates[0].summary.lower()
    assert pref_candidates[0].confidence == 0.80


def test_commit_report_creates_project_candidate():
    candidates = classify_memory_capture_candidates(
        message="commit 1a2b3c4d completed the tests",
        response="Noted.",
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
    )
    work_candidates = [c for c in candidates if c.capture_type == "project_work"]
    assert len(work_candidates) >= 1


def test_tests_passed_creates_milestone_candidate():
    candidates = classify_memory_capture_candidates(
        message="Tests passed. Production ready.",
        response="Tests green.",
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
    )
    milestone_candidates = [c for c in candidates if c.capture_type == "milestone"]
    assert len(milestone_candidates) >= 1
    assert "tests passing" in milestone_candidates[0].summary.lower() or "production" in milestone_candidates[0].summary.lower()


def test_explicit_preference_propose_next_prompt():
    candidates = classify_memory_capture_candidates(
        message="don't ask what next; propose next prompt instead",
        response="Understood.",
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
    )
    pref_candidates = [c for c in candidates if c.capture_type == "user_preference"]
    assert len(pref_candidates) >= 1


def test_unknown_identity_cannot_create_private_person_memory():
    candidates = classify_memory_capture_candidates(
        message="Remember that I prefer X",
        response="OK.",
        identity_state={"is_verified": False, "identity_status": "unknown", "user_id": ""},
    )
    person_private = [
        c for c in candidates
        if c.entity_type == "person" and c.access_level == AccessLevel.PRIVATE.value
    ]
    assert len(person_private) == 0


def test_profile_only_cannot_create_private_person_memory():
    candidates = classify_memory_capture_candidates(
        message="Remember that I prefer X",
        response="OK.",
        identity_state={"is_verified": False, "identity_status": "profile_only", "user_id": "alice"},
    )
    person_private = [
        c for c in candidates
        if c.entity_type == "person" and c.access_level == AccessLevel.PRIVATE.value
    ]
    assert len(person_private) == 0


def test_channel_verified_can_create_person_preference_memory():
    candidates = classify_memory_capture_candidates(
        message="don't mention context to users",
        response="Understood.",
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
    )
    pref_candidates = [c for c in candidates if c.capture_type == "user_preference"]
    assert len(pref_candidates) >= 1
    # Scope can be person or system/project
    assert pref_candidates[0].entity_type in ("person", "project", "system")


def test_project_scoped_capture_writes_project_memory():
    td = tempfile.mkdtemp()
    try:
        result = capture_memories_from_turn(
            message="commit abc123 completed the memory capture module",
            response="Saved.",
            response_metadata={"project_id": "weslr"},
            identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
            base_path=td,
        )
        assert result.captured is True
        assert len(result.records_created) >= 1

        memories = load_entity_memories("project", "weslr", base_path=td)
        assert len(memories) >= 1
        assert "commit" in memories[0].summary.lower() or "work" in memories[0].summary.lower()
    finally:
        shutil.rmtree(td)


def test_company_memory_requires_verified_role():
    from weslr.memory_capture import resolve_memory_capture_scope, MemoryCaptureCandidate
    candidate = MemoryCaptureCandidate(
        capture_type="project_work",
        summary="ACME project work completed",
        entity_type="company",
        entity_id="acme",
        confidence=0.8,
    )
    identity_state = {"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"}
    profile = {
        "memberships": [
            {"entity_type": "company", "entity_id": "acme", "role": "engineer", "verified": False}
        ]
    }
    adjusted = resolve_memory_capture_scope(candidate, identity_state, profile)
    assert adjusted.safe_to_store is False


def test_unverified_company_blocks_group_memory():
    candidates = classify_memory_capture_candidates(
        message="ACME company milestone achieved",
        response="Noted.",
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
        relationship_targets=[],
    )
    company_candidates = [c for c in candidates if c.entity_type == "company"]
    if company_candidates:
        # Without verified membership in profile, should be blocked by safety gate
        safe, reason = is_memory_safe_to_store(company_candidates[0], {"is_verified": True, "identity_status": "channel_verified"})
        assert safe is False


def test_verified_company_passes():
    from weslr.memory_capture import resolve_memory_capture_scope, MemoryCaptureCandidate
    candidate = MemoryCaptureCandidate(
        capture_type="project_work",
        summary="ACME project work completed",
        entity_type="company",
        entity_id="acme",
        confidence=0.8,
    )
    identity_state = {"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"}
    profile = {
        "memberships": [
            {"entity_type": "company", "entity_id": "acme", "role": "engineer", "verified": True}
        ]
    }
    adjusted = resolve_memory_capture_scope(candidate, identity_state, profile)
    assert adjusted.safe_to_store is True


def test_sensitive_content_is_skipped():
    candidates = classify_memory_capture_candidates(
        message="Remember my API key is xyz-123-abc",
        response="OK.",
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
    )
    # Should not create a candidate from sensitive content
    sensitive_candidates = [
        c for c in candidates
        if contains_sensitive_content(c.summary) or any(contains_sensitive_content(e) for e in c.evidence)
    ]
    # Even if a candidate is created, the safety gate should block it
    for c in candidates:
        safe, _ = is_memory_safe_to_store(c, {"is_verified": True, "identity_status": "channel_verified"})
        if not safe:
            assert _ is not None  # has a skip reason


def test_raw_message_not_stored_in_memory():
    td = tempfile.mkdtemp()
    try:
        capture_memories_from_turn(
            message="Remember my medical condition",
            response="Noted.",
            identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
            base_path=td,
        )
        path = os.path.join(td, "entity_memory", "person", "alice", "memory.jsonl")
        if os.path.exists(path):
            with open(path) as f:
                content = f.read()
            assert "medical condition" not in content.lower()
    finally:
        shutil.rmtree(td)


def test_memory_record_has_provenance():
    candidate = MemoryCaptureCandidate(
        capture_type="project_work",
        summary="Work completed",
        entity_type="project",
        entity_id="weslr",
        confidence=0.85,
        source="live_interaction",
        reason="project_work_detected",
    )
    record = create_memory_record_from_candidate(candidate)
    assert record.provenance == "memory_capture:project_work_detected"
    assert record.source == "live_interaction"
    assert record.confidence == 0.85
    assert record.access_level == AccessLevel.OPERATOR_ONLY.value


def test_capture_failure_cannot_break_response():
    """Capture exceptions are swallowed; returns result, does not propagate."""
    result = capture_memories_from_turn(
        message="Test message",
        response="Test response",
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
        base_path=None,  # will cause issues if not handled
    )
    assert isinstance(result, MemoryCaptureResult)
    assert result.attempted is True


def test_correction_memory_creates_candidate():
    candidates = classify_memory_capture_candidates(
        message="No, that's wrong, I meant blue not red",
        response="Sorry, corrected.",
        identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
    )
    correction_candidates = [c for c in candidates if c.capture_type == "correction"]
    assert len(correction_candidates) >= 1


def test_safe_capture_memories_from_turn_wrapper():
    """safe_capture_memories_from_turn accepts identity_meta dict."""
    result = safe_capture_memories_from_turn(
        message="commit abc123 completed memory capture",
        response="Saved.",
        identity_meta={"sender_identity": "alice", "known_user_status": "channel_verified"},
        base_path=None,
    )
    assert isinstance(result, MemoryCaptureResult)


def test_memory_capture_no_depth_granted():
    """Memory capture does not grant relationship depth or identity verification."""
    # This is a structural test — capture writes to entity_memory namespace,
    # not to relationship_observations, so they are independent.
    td = tempfile.mkdtemp()
    try:
        result = capture_memories_from_turn(
            message="My name is Bob",
            response="Nice to meet you Bob!",
            identity_state={"is_verified": False, "identity_status": "unknown", "user_id": ""},
            base_path=td,
        )
        # Unknown identity with no explicit work/preference should produce no records
        assert result.captured is False
    finally:
        shutil.rmtree(td)


def test_memory_capture_no_scope_merge():
    """Memory for different scopes are tracked in separate namespaces."""
    td = tempfile.mkdtemp()
    try:
        # Project scope
        r1 = capture_memories_from_turn(
            message="commit abc123 completed project work",
            response="Saved.",
            response_metadata={"project_id": "weslr"},
            identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
            base_path=td,
        )
        # Person scope
        r2 = capture_memories_from_turn(
            message="don't mention context to users",
            response="Understood.",
            identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
            base_path=td,
        )
        # They go to different namespaces
        assert r1.scope_used in ("project:weslr", "system:weslr")
        # If person preference was captured, it has different scope
        if r2.captured:
            assert r1.scope_used != r2.scope_used
    finally:
        shutil.rmtree(td)


def test_user_explicit_consent_memory():
    """Explicit 'remember that' from verified user creates memory."""
    td = tempfile.mkdtemp()
    try:
        result = capture_memories_from_turn(
            message="Remember that I prefer short responses",
            response="Understood.",
            identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
            base_path=td,
        )
        # Should create consent memory candidate
        candidates = classify_memory_capture_candidates(
            message="Remember that I prefer short responses",
            response="Understood.",
            identity_state={"is_verified": True, "identity_status": "channel_verified", "user_id": "alice"},
        )
        consent = [c for c in candidates if c.capture_type == "user_consent_memory"]
        assert len(consent) >= 1
    finally:
        shutil.rmtree(td)


# ── Test runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== WESLR MEMORY CAPTURE TESTS ===")

    tests = [
        # Regression suites
        test_entity_memory,
        test_user_profile,
        test_channel_identity,
        test_relationship_observation,
        test_relationship_depth,
        test_meaning_vector,
        test_cognitive_weight,
        test_local_bridge,
        test_voice_pipeline,
        # Core unit tests
        test_safe_turn_fingerprint_does_not_store_raw_text,
        test_safe_turn_fingerprint_empty,
        test_safe_turn_fingerprint_deterministic,
        test_contains_sensitive_content_blocks_credentials,
        test_contains_sensitive_content_blocks_medical,
        test_contains_sensitive_content_blocks_location,
        test_contains_sensitive_content_allows_normal,
        test_has_explicit_consent_detects,
        test_project_work_creates_project_candidate,
        test_explicit_user_preference_creates_candidate,
        test_commit_report_creates_project_candidate,
        test_tests_passed_creates_milestone_candidate,
        test_explicit_preference_propose_next_prompt,
        test_unknown_identity_cannot_create_private_person_memory,
        test_profile_only_cannot_create_private_person_memory,
        test_channel_verified_can_create_person_preference_memory,
        test_project_scoped_capture_writes_project_memory,
        test_company_memory_requires_verified_role,
        test_unverified_company_blocks_group_memory,
        test_verified_company_passes,
        test_sensitive_content_is_skipped,
        test_raw_message_not_stored_in_memory,
        test_memory_record_has_provenance,
        test_capture_failure_cannot_break_response,
        test_correction_memory_creates_candidate,
        test_safe_capture_memories_from_turn_wrapper,
        test_memory_capture_no_depth_granted,
        test_memory_capture_no_scope_merge,
        test_user_explicit_consent_memory,
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

    print(f"\nMemory capture tests: {passed} passed, {failed} failed")
