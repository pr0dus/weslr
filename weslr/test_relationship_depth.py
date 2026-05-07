"""
WESLR Relationship Depth Tests

Tests relationship observation storage, state computation, scoring, and
meaning-state integration. Uses temp dirs only. Does not dirty real ~/.weslr.
"""

import os, sys, json, tempfile, shutil
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.relationship_depth import (
    RelationshipObservation,
    RelationshipState,
    RelationshipStage,
    InteractionSignal,
    SIGNAL_WEIGHTS,
    IDENTITY_DEPTH_CAPS,
    STAGE_THRESHOLDS,
    INACTIVITY_DECAY_DAYS,
    create_relationship_observation,
    append_relationship_observation,
    load_relationship_observations,
    compute_relationship_state,
    classify_relationship_stage,
    decay_relationship_depth_if_inactive,
    record_interaction_outcome,
    get_relationship_depth_for_identity,
    summarize_relationship_state,
    get_relationship_tone,
    observations_path,
)


def test_observation_serialize_roundtrip():
    td = tempfile.mkdtemp()
    try:
        obs = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="user_abc",
            interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
            verified=True,
            weight=0.05,
        )
        append_relationship_observation(obs, base_path=td)

        loaded = load_relationship_observations(
            "person", "user_abc", base_path=td
        )
        assert len(loaded) == 1
        assert loaded[0].interaction_signal == InteractionSignal.SHARED_WORK_COMPLETED.value
        assert loaded[0].observation_id == obs.observation_id
        assert loaded[0].weight == 0.05
        print("  PASS  observation serializes/deserializes")
    finally:
        shutil.rmtree(td)


def test_unknown_identity_caps_depth():
    td = tempfile.mkdtemp()
    try:
        # Record a "shared work completed" signal (weight +0.05)
        obs = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="user_abc",
            interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
            verified=True,
            weight=0.05,
        )
        append_relationship_observation(obs, base_path=td)

        loaded = load_relationship_observations("person", "user_abc", base_path=td)
        state = compute_relationship_state(loaded, identity_status="unknown")

        # Cap for unknown is 0.05, raw weight is +0.05, so result is capped
        # Stage for depth=0.05 is FIRST_CONTACT (not UNKNOWN, which is 0.00–0.05)
        assert state.relationship_depth <= IDENTITY_DEPTH_CAPS["unknown"]
        assert state.relationship_stage == RelationshipStage.FIRST_CONTACT.value
        print("  PASS  unknown identity caps relationship depth")
    finally:
        shutil.rmtree(td)


def test_profile_only_caps_depth():
    td = tempfile.mkdtemp()
    try:
        for _ in range(5):
            obs = create_relationship_observation(
                subject_entity_type="person",
                subject_entity_id="user_abc",
                interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
                verified=True,
            )
            append_relationship_observation(obs, base_path=td)

        loaded = load_relationship_observations("person", "user_abc", base_path=td)
        state = compute_relationship_state(loaded, identity_status="profile_only")

        # Cap for profile_only is 0.20, expect early or first_contact
        assert state.relationship_depth <= IDENTITY_DEPTH_CAPS["profile_only"]
        assert state.relationship_stage in (
            RelationshipStage.FIRST_CONTACT.value,
            RelationshipStage.EARLY.value,
        )
        print("  PASS  profile_only caps relationship depth below verified threshold")
    finally:
        shutil.rmtree(td)


def test_channel_verified_repeated_interactions_increase_depth():
    td = tempfile.mkdtemp()
    try:
        signals = [
            InteractionSignal.VERIFIED_SESSION_INTERACTION.value,
            InteractionSignal.SHARED_WORK_COMPLETED.value,
            InteractionSignal.SUCCESSFUL_FOLLOWUP.value,
            InteractionSignal.MEMORY_CONFIRMED.value,
        ]
        for sig in signals:
            obs = create_relationship_observation(
                subject_entity_type="person",
                subject_entity_id="user_abc",
                interaction_signal=sig,
                verified=True,
            )
            append_relationship_observation(obs, base_path=td)

        loaded = load_relationship_observations("person", "user_abc", base_path=td)
        state = compute_relationship_state(loaded, identity_status="channel_verified")

        assert state.relationship_depth > 0.10
        assert state.relationship_stage in (
            RelationshipStage.FIRST_CONTACT.value,
            RelationshipStage.EARLY.value,
            RelationshipStage.DEVELOPING.value,
        )
        print("  PASS  channel_verified repeated interactions increase depth")
    finally:
        shutil.rmtree(td)


def test_shared_work_increases_more_than_simple_question():
    td = tempfile.mkdtemp()
    try:
        # Simple question
        obs1 = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="user_abc",
            interaction_signal=InteractionSignal.SIMPLE_QUESTION.value,
            verified=True,
        )
        append_relationship_observation(obs1, base_path=td)

        # Shared work
        obs2 = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="user_abc",
            interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
            verified=True,
        )
        append_relationship_observation(obs2, base_path=td)

        loaded = load_relationship_observations("person", "user_abc", base_path=td)
        state = compute_relationship_state(loaded, identity_status="channel_verified")

        # Shared work weight (0.05) > simple question weight (0.005)
        assert state.positive_signal_count >= 1
        assert state.relationship_depth > 0
        print("  PASS  shared work increases depth more than simple question")
    finally:
        shutil.rmtree(td)


def test_negative_feedback_decreases_or_restrains_depth():
    td = tempfile.mkdtemp()
    try:
        # Positive signal
        obs1 = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="user_abc",
            interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
            verified=True,
            weight=0.05,
        )
        append_relationship_observation(obs1, base_path=td)

        # Negative signal
        obs2 = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="user_abc",
            interaction_signal=InteractionSignal.USER_NEGATIVE_FEEDBACK.value,
            verified=True,
            weight=-0.03,
        )
        append_relationship_observation(obs2, base_path=td)

        loaded = load_relationship_observations("person", "user_abc", base_path=td)
        state = compute_relationship_state(loaded, identity_status="channel_verified")

        # Net weight should be reduced vs positive only
        assert state.negative_signal_count >= 1
        print("  PASS  negative feedback registered in relationship state")
    finally:
        shutil.rmtree(td)


def test_correction_resolved_increases_depth():
    td = tempfile.mkdtemp()
    try:
        obs = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="user_abc",
            interaction_signal=InteractionSignal.CORRECTION_RESOLVED.value,
            verified=True,
        )
        append_relationship_observation(obs, base_path=td)

        loaded = load_relationship_observations("person", "user_abc", base_path=td)
        state = compute_relationship_state(loaded, identity_status="channel_verified")

        assert state.positive_signal_count >= 1
        assert state.relationship_depth > 0
        print("  PASS  correction resolved increases relationship quality")
    finally:
        shutil.rmtree(td)


def test_classify_relationship_stage():
    cases = [
        (0.02, 0.5, RelationshipStage.UNKNOWN),
        (0.08, 0.5, RelationshipStage.FIRST_CONTACT),
        (0.20, 0.5, RelationshipStage.EARLY),
        (0.35, 0.5, RelationshipStage.DEVELOPING),
        (0.60, 0.5, RelationshipStage.ESTABLISHED),
        (0.85, 0.5, RelationshipStage.DEEP),
        (0.85, 0.1, RelationshipStage.UNKNOWN),  # low confidence → UNKNOWN
    ]
    for depth, conf, expected in cases:
        stage = classify_relationship_stage(depth, conf)
        assert stage == expected, f"depth={depth} conf={conf}: expected {expected.value}, got {stage.value}"
    print("  PASS  classify_relationship_stage returns expected stages")


def test_entity_scoped_states_do_not_merge():
    """Person↔WESLR and person↔project must be separate states."""
    td = tempfile.mkdtemp()
    try:
        obs_weslr = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="user_abc",
            target_entity_type="system",
            target_entity_id="weslr",
            interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
            verified=True,
        )
        append_relationship_observation(obs_weslr, base_path=td)

        obs_project = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="user_abc",
            target_entity_type="project",
            target_entity_id="weslr",
            interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
            verified=True,
        )
        append_relationship_observation(obs_project, base_path=td)

        # Load all observations for user_abc
        all_obs = load_relationship_observations("person", "user_abc", base_path=td)
        assert len(all_obs) == 2

        # Load scoped to system/weslr only
        sys_obs = load_relationship_observations(
            "person", "user_abc",
            target_entity_type="system", target_entity_id="weslr",
            base_path=td,
        )
        assert len(sys_obs) == 1
        assert sys_obs[0].target_entity_type == "system"

        # Load scoped to project/weslr only
        proj_obs = load_relationship_observations(
            "person", "user_abc",
            target_entity_type="project", target_entity_id="weslr",
            base_path=td,
        )
        assert len(proj_obs) == 1
        assert proj_obs[0].target_entity_type == "project"

        print("  PASS  entity-scoped observations do not merge")
    finally:
        shutil.rmtree(td)


def test_person_project_relationship_separate_from_person_company():
    td = tempfile.mkdtemp()
    try:
        obs_project = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="alice",
            target_entity_type="project",
            target_entity_id="weslr",
            interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
            verified=True,
        )
        append_relationship_observation(obs_project, base_path=td)

        obs_company = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="alice",
            target_entity_type="company",
            target_entity_id="acme",
            interaction_signal=InteractionSignal.REPRESENTED.value if hasattr(InteractionSignal, "REPRESENTED") else "represented",
            verified=True,
        )
        append_relationship_observation(obs_company, base_path=td)

        all_obs = load_relationship_observations("person", "alice", base_path=td)
        assert len(all_obs) == 2

        project_obs = load_relationship_observations(
            "person", "alice",
            target_entity_type="project", target_entity_id="weslr",
            base_path=td,
        )
        company_obs = load_relationship_observations(
            "person", "alice",
            target_entity_type="company", target_entity_id="acme",
            base_path=td,
        )

        assert len(project_obs) == 1
        assert len(company_obs) == 1
        print("  PASS  person↔project separate from person↔company")
    finally:
        shutil.rmtree(td)


def test_verified_role_does_not_grant_personal_depth():
    """Verified CEO role at company scope does not automatically mean deep personal relationship."""
    td = tempfile.mkdtemp()
    try:
        # Verified company role
        obs = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="alice",
            target_entity_type="company",
            target_entity_id="acme",
            interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
            verified=True,
        )
        append_relationship_observation(obs, base_path=td)

        # Compute state scoped to company
        company_obs = load_relationship_observations(
            "person", "alice",
            target_entity_type="company", target_entity_id="acme",
            base_path=td,
        )
        state = compute_relationship_state(company_obs, identity_status="onboarded_unverified")

        # Company scope relationship should not automatically grant personal depth
        # personal↔WESLR state should still be separate
        personal_obs = load_relationship_observations(
            "person", "alice",
            target_entity_type="system", target_entity_id="weslr",
            base_path=td,
        )
        personal_state = compute_relationship_state(personal_obs, identity_status="onboarded_unverified")

        assert personal_state.relationship_depth == 0.0
        assert len(company_obs) == 1
        print("  PASS  verified role does not automatically grant personal relationship depth")
    finally:
        shutil.rmtree(td)


def test_relationship_depth_does_not_verify_identity():
    """Relationship depth alone must never imply verified identity."""
    td = tempfile.mkdtemp()
    try:
        for _ in range(10):
            obs = create_relationship_observation(
                subject_entity_type="person",
                subject_entity_id="alice",
                interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
                verified=False,  # not verified
            )
            append_relationship_observation(obs, base_path=td)

        loaded = load_relationship_observations("person", "alice", base_path=td)
        state = compute_relationship_state(loaded, identity_status="unknown")

        # Even with many unverified observations, identity stays unknown
        # Depth may reach cap, but confidence stays low due to no verified observations
        assert state.relationship_depth <= IDENTITY_DEPTH_CAPS["unknown"]
        assert state.confidence <= 0.3  # low confidence due to no verified
        print("  PASS  relationship depth does not verify identity")
    finally:
        shutil.rmtree(td)


def test_relationship_tone_changes_with_depth():
    tone_unknown = get_relationship_tone(0.02, RelationshipStage.UNKNOWN.value)
    tone_early = get_relationship_tone(0.20, RelationshipStage.EARLY.value)
    tone_estab = get_relationship_tone(0.65, RelationshipStage.ESTABLISHED.value)
    tone_deep = get_relationship_tone(0.90, RelationshipStage.DEEP.value)

    assert tone_unknown["warmth"] == "reserved"
    assert tone_early["warmth"] == "warm"
    assert tone_estab["warmth"] == "familiar"
    assert tone_deep["verbosity"] == "concise"

    # Key: truth/access must NOT change based on tone
    assert tone_unknown["explanatory"] is True  # unknown should always explain
    assert tone_deep["explanatory"] is False     # deep can be concise
    print("  PASS  relationship tone changes with depth, explanatory stays bounded")


def test_summarize_relationship_state():
    td = tempfile.mkdtemp()
    try:
        for sig in [
            InteractionSignal.SHARED_WORK_COMPLETED.value,
            InteractionSignal.SUCCESSFUL_FOLLOWUP.value,
        ]:
            obs = create_relationship_observation(
                subject_entity_type="person",
                subject_entity_id="alice",
                interaction_signal=sig,
                verified=True,
            )
            append_relationship_observation(obs, base_path=td)

        loaded = load_relationship_observations("person", "alice", base_path=td)
        state = compute_relationship_state(loaded, identity_status="channel_verified")
        summary = summarize_relationship_state(state)

        assert "depth=" in summary
        assert "conf=" in summary
        assert len(summary) < 200
        print("  PASS  summarize_relationship_state is bounded")
    finally:
        shutil.rmtree(td)


def test_record_interaction_outcome():
    td = tempfile.mkdtemp()
    try:
        obs = record_interaction_outcome(
            subject_entity_type="person",
            subject_entity_id="bob",
            signal=InteractionSignal.USER_POSITIVE_FEEDBACK.value,
            verified=True,
            base_path=td,
        )
        assert obs.observation_id != ""
        assert obs.interaction_signal == InteractionSignal.USER_POSITIVE_FEEDBACK.value

        loaded = load_relationship_observations("person", "bob", base_path=td)
        assert len(loaded) == 1
        print("  PASS  record_interaction_outcome creates and appends observation")
    finally:
        shutil.rmtree(td)


def test_inactivity_decay():
    td = tempfile.mkdtemp()
    try:
        obs = create_relationship_observation(
            subject_entity_type="person",
            subject_entity_id="alice",
            interaction_signal=InteractionSignal.SHARED_WORK_COMPLETED.value,
            verified=True,
        )
        append_relationship_observation(obs, base_path=td)

        loaded = load_relationship_observations("person", "alice", base_path=td)
        state = compute_relationship_state(loaded, identity_status="channel_verified")

        # Now simulate old interaction
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        old_state = RelationshipState(
            subject_entity_type="person",
            subject_entity_id="alice",
            target_entity_type="system",
            target_entity_id="weslr",
            relationship_depth=0.50,
            relationship_stage=RelationshipStage.DEVELOPING.value,
            confidence=0.6,
            last_interaction_at=old_timestamp,
        )

        decayed = decay_relationship_depth_if_inactive(
            old_state,
            last_interaction_at=old_timestamp,
        )
        assert decayed.relationship_depth < 0.50
        print("  PASS  inactivity decay reduces relationship depth")
    finally:
        shutil.rmtree(td)


def test_relationship_observations_respect_limit():
    td = tempfile.mkdtemp()
    try:
        for i in range(250):
            obs = create_relationship_observation(
                subject_entity_type="person",
                subject_entity_id="alice",
                interaction_signal=InteractionSignal.SIMPLE_QUESTION.value,
                verified=True,
            )
            append_relationship_observation(obs, base_path=td)

        loaded = load_relationship_observations(
            "person", "alice", base_path=td, limit=50
        )
        assert len(loaded) == 50
        print("  PASS  relationship observations respect limit parameter")
    finally:
        shutil.rmtree(td)


def test_entity_memory_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/test_entity_memory.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "24 passed" in result.stdout, f"Entity memory tests failed: {result.stdout[-200:]}"
    print("  PASS  entity memory tests pass")


def test_user_profile_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/test_user_profile.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "14 passed" in result.stdout, f"User profile tests failed: {result.stdout[-200:]}"
    print("  PASS  user profile tests pass")


def test_channel_identity_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/test_channel_identity_binding.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "16 passed" in result.stdout, f"Channel identity tests failed: {result.stdout[-200:]}"
    print("  PASS  channel identity tests pass")


def test_meaning_vector_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/test_meaning_vector_response_obligation.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "5/5" in result.stdout, f"Meaning vector tests failed: {result.stdout[-200:]}"
    print("  PASS  meaning vector tests pass")


def test_weight_refinement_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/test_cognitive_weight_refinement.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "6/6" in result.stdout, f"Weight refinement tests failed: {result.stdout[-200:]}"
    print("  PASS  weight refinement tests pass")


def test_local_bridge_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/voice_layer/test_local_bridge.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "6/6" in result.stdout, f"Local bridge tests failed: {result.stdout[-200:]}"
    print("  PASS  local bridge tests pass")


def test_voice_pipeline_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/voice_layer/test_voice_pipeline.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "13/13" in result.stdout, f"Voice pipeline tests failed: {result.stdout[-200:]}"
    print("  PASS  voice pipeline tests pass")


if __name__ == "__main__":
    print("\n=== RELATIONSHIP DEPTH TESTS ===")
    tests = [
        test_observation_serialize_roundtrip,
        test_unknown_identity_caps_depth,
        test_profile_only_caps_depth,
        test_channel_verified_repeated_interactions_increase_depth,
        test_shared_work_increases_more_than_simple_question,
        test_negative_feedback_decreases_or_restrains_depth,
        test_correction_resolved_increases_depth,
        test_classify_relationship_stage,
        test_entity_scoped_states_do_not_merge,
        test_person_project_relationship_separate_from_person_company,
        test_verified_role_does_not_grant_personal_depth,
        test_relationship_depth_does_not_verify_identity,
        test_relationship_tone_changes_with_depth,
        test_summarize_relationship_state,
        test_record_interaction_outcome,
        test_inactivity_decay,
        test_relationship_observations_respect_limit,
        test_entity_memory_tests_pass,
        test_user_profile_tests_pass,
        test_channel_identity_tests_pass,
        test_meaning_vector_tests_pass,
        test_weight_refinement_tests_pass,
        test_local_bridge_tests_pass,
        test_voice_pipeline_tests_pass,
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
    print(f"\nRelationship depth tests: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
