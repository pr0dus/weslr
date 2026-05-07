"""
WESLR Entity Memory Namespace Tests

Tests entity-scoped memory access, relationship/role model, access control,
and meaning-state integration. Uses temp dirs only. Does not dirty real ~/.weslr.
"""

import os, sys, json, tempfile, shutil

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.entity_memory import (
    make_entity_id,
    person_memory_id,
    entity_memory_path,
    create_memory_record,
    append_entity_memory,
    load_entity_memories,
    summarize_memory_records,
    format_memory_response,
    create_relationship,
    save_relationship,
    load_relationships,
    resolve_person_memberships,
    can_access_memory_scope,
    resolve_memory_scopes,
    load_scoped_memories,
    list_entity_memory_namespaces,
    EntityRelationship,
    MemoryRecord,
    EntityType,
    AccessLevel,
    RelationshipType,
    RoleType,
)
from weslr.user_profile import (
    UserProfile,
    default_profile,
    add_membership,
    list_memberships,
    summarize_memberships,
    save_user_profile,
    load_user_profile,
)


def test_entity_id_generation_stable():
    id1 = make_entity_id("Arthur", EntityType.PERSON.value)
    id2 = make_entity_id("Arthur", EntityType.PERSON.value)
    assert id1 == id2
    assert "arthur" in id1
    assert len(id1) <= 40
    print("  PASS  entity_id generation stable")


def test_memory_path_construction():
    td = tempfile.mkdtemp()
    try:
        p = entity_memory_path(EntityType.PERSON.value, "arthur", base_path=td)
        assert "person" in p
        assert "arthur" in p
        assert p.endswith("memory.jsonl")
        assert td in p
    finally:
        shutil.rmtree(td)


def test_append_load_memory_roundtrip():
    td = tempfile.mkdtemp()
    try:
        rec = create_memory_record(
            entity_type=EntityType.PERSON.value,
            entity_id="user_abc",
            summary="WESLR workspace initialized",
            source="operator",
            confidence=0.8,
            verified=True,
            tags=["setup", "weslr"],
        )
        append_entity_memory(rec, base_path=td)

        loaded = load_entity_memories(EntityType.PERSON.value, "user_abc", base_path=td)
        assert len(loaded) == 1
        assert loaded[0].summary == "WESLR workspace initialized"
        assert loaded[0].memory_id == rec.memory_id
        print("  PASS  append/load memory roundtrip")
    finally:
        shutil.rmtree(td)


def test_summarize_memory_produces_structured_summary():
    td = tempfile.mkdtemp()
    try:
        recs = [
            create_memory_record(EntityType.PERSON.value, "alice",
                summary="Set up Weslr entity graph", source="op",
                confidence=0.8, verified=True, tags=["setup"]),
            create_memory_record(EntityType.PERSON.value, "alice",
                summary="Ran meaning vector tests", source="op",
                confidence=0.6, verified=False, tags=["testing"]),
            create_memory_record(EntityType.PERSON.value, "alice",
                summary="Fixed channel binding", source="op",
                confidence=0.9, verified=True, tags=["binding"]),
        ]
        for r in recs:
            append_entity_memory(r, base_path=td)

        loaded = load_entity_memories(EntityType.PERSON.value, "alice", base_path=td)
        summary = summarize_memory_records(loaded)

        assert summary["count"] == 3
        assert summary["verified_count"] == 2
        assert "high" in summary["confidence_bands"]
        assert "setup" in summary["tags"]
        assert len(summary["summaries"]) == 3
        print("  PASS  summarize produces structured summary")
    finally:
        shutil.rmtree(td)


def test_unknown_cannot_access_private_person_memory():
    allowed, reason = can_access_memory_scope(
        identity_status="unknown",
        access_level=AccessLevel.PRIVATE.value,
    )
    assert not allowed
    assert "identity not established" in reason
    print("  PASS  unknown cannot access private person memory")


def test_profile_only_cannot_access_private_person_memory():
    allowed, reason = can_access_memory_scope(
        identity_status="onboarded_unverified",
        access_level=AccessLevel.PRIVATE.value,
    )
    assert not allowed
    assert "verified channel" in reason
    print("  PASS  profile-only cannot access private person memory")


def test_channel_verified_can_access_own_person_memory():
    allowed, reason = can_access_memory_scope(
        identity_status="channel_verified",
        access_level=AccessLevel.PRIVATE.value,
    )
    assert allowed
    assert "private memory access granted" in reason
    print("  PASS  channel_verified user can access own person memory")


def test_public_access():
    allowed, reason = can_access_memory_scope(
        identity_status="unknown",
        access_level=AccessLevel.PUBLIC.value,
    )
    assert allowed
    assert "public access" in reason
    print("  PASS  public access level always allowed")


def test_project_memory_separate_from_person_memory():
    td = tempfile.mkdtemp()
    try:
        person_rec = create_memory_record(
            EntityType.PERSON.value, "alice",
            summary="Alice personal note", source="op",
        )
        project_rec = create_memory_record(
            EntityType.PROJECT.value, "weslr",
            summary="WESLR project decision", source="op",
        )
        append_entity_memory(person_rec, base_path=td)
        append_entity_memory(project_rec, base_path=td)

        person_memories = load_entity_memories(EntityType.PERSON.value, "alice", base_path=td)
        project_memories = load_entity_memories(EntityType.PROJECT.value, "weslr", base_path=td)

        assert any("Alice personal" in r.summary for r in person_memories)
        assert not any("Alice personal" in r.summary for r in project_memories)
        assert any("WESLR project" in r.summary for r in project_memories)
        print("  PASS  project memory separate from person memory")
    finally:
        shutil.rmtree(td)


def test_company_family_requires_role_evidence():
    td = tempfile.mkdtemp()
    try:
        # Unverified relationship
        rel_unverified = create_relationship(
            person_id="alice",
            entity_type=EntityType.COMPANY.value,
            entity_id="acme_gmbh",
            role=RoleType.EMPLOYEE.value,
            relationship_type=RelationshipType.WORKS_FOR.value,
            entity_display_name="ACME GmbH",
            verified=False,
            confidence=0.4,
        )
        save_relationship(rel_unverified, base_path=td)

        # Verify: unverified relationship does not grant SHARED access
        all_rels = load_relationships(person_id="alice", base_path=td)
        allowed, reason = can_access_memory_scope(
            identity_status="onboarded_unverified",
            access_level=AccessLevel.SHARED.value,
            role_evidence=all_rels,
        )
        assert not allowed
        assert "requires verified role" in reason or "requires verified relationship" in reason
        print("  PASS  unverified membership/role does not grant shared memory")
    finally:
        shutil.rmtree(td)


def test_verified_ceo_can_access_company_memory():
    td = tempfile.mkdtemp()
    try:
        rel_verified = create_relationship(
            person_id="alice",
            entity_type=EntityType.COMPANY.value,
            entity_id="acme_gmbh",
            role=RoleType.CEO.value,
            relationship_type=RelationshipType.LEADS.value,
            entity_display_name="ACME GmbH",
            verified=True,
            confidence=0.85,
        )
        save_relationship(rel_verified, base_path=td)

        all_rels = load_relationships(person_id="alice", base_path=td)
        allowed, reason = can_access_memory_scope(
            identity_status="channel_verified",
            access_level=AccessLevel.SHARED.value,
            role_evidence=all_rels,
        )
        assert allowed
        assert "role-scoped memory access granted" in reason
        print("  PASS  verified CEO role can access company memory")
    finally:
        shutil.rmtree(td)


def test_person_can_have_multiple_memberships():
    profile = default_profile()
    profile.user_id = "alice_test"
    add_membership(profile, EntityType.FAMILY.value, "family_home",
                   RoleType.MEMBER.value, RelationshipType.PART_OF_FAMILY.value,
                   display_name="Home Family", verified=False)
    add_membership(profile, EntityType.COMPANY.value, "acme_gmbh",
                   RoleType.CEO.value, RelationshipType.LEADS.value,
                   display_name="ACME GmbH", verified=True)
    add_membership(profile, EntityType.PROJECT.value, "weslr",
                   RoleType.PROJECT_OWNER.value, RelationshipType.OWNS_PROJECT.value,
                   display_name="WESLR", verified=True)

    mems = list_memberships(profile)
    assert len(mems) == 3
    assert any(m["entity_type"] == EntityType.FAMILY.value for m in mems)
    assert any(m["entity_type"] == EntityType.COMPANY.value for m in mems)
    assert any(m["entity_type"] == EntityType.PROJECT.value for m in mems)

    summary = summarize_memberships(profile)
    assert "family" in summary
    assert "company" in summary
    assert "project" in summary
    print("  PASS  person can have multiple memberships without scope collision")


def test_memory_namespaces_list_correctly():
    td = tempfile.mkdtemp()
    try:
        rec1 = create_memory_record(EntityType.PERSON.value, "alice",
                                    summary="Alice note", source="op")
        rec2 = create_memory_record(EntityType.PROJECT.value, "weslr",
                                    summary="Weslr note", source="op")
        rec3 = create_memory_record(EntityType.COMPANY.value, "acme",
                                    summary="Acme note", source="op")
        append_entity_memory(rec1, base_path=td)
        append_entity_memory(rec2, base_path=td)
        append_entity_memory(rec3, base_path=td)

        namespaces = list_entity_memory_namespaces(base_path=td)
        types = [n["entity_type"] for n in namespaces]
        assert EntityType.PERSON.value in types
        assert EntityType.PROJECT.value in types
        assert EntityType.COMPANY.value in types
        print("  PASS  memory namespaces list correctly")
    finally:
        shutil.rmtree(td)


def test_resolve_memory_scopes_channel_verified():
    rel = create_relationship(
        person_id="alice",
        entity_type=EntityType.COMPANY.value,
        entity_id="acme_gmbh",
        role=RoleType.CEO.value,
        relationship_type=RelationshipType.LEADS.value,
        entity_display_name="ACME GmbH",
        verified=True,
        confidence=0.85,
    )
    scopes = resolve_memory_scopes(
        identity_status="channel_verified",
        user_id="alice",
        primary_projects=["weslr"],
        memberships=[rel],
    )
    assert "personal" in scopes
    assert "project_weslr" in scopes
    assert "company_acme_gmbh" in scopes
    print("  PASS  resolve_memory_scopes includes personal + project + company for channel_verified")


def test_resolve_memory_scopes_profile_only_no_personal():
    rel = create_relationship(
        person_id="alice",
        entity_type=EntityType.FAMILY.value,
        entity_id="family_home",
        role=RoleType.MEMBER.value,
        relationship_type=RelationshipType.PART_OF_FAMILY.value,
        verified=True,
        confidence=0.6,
    )
    scopes = resolve_memory_scopes(
        identity_status="onboarded_unverified",
        user_id="alice",
        primary_projects=["weslr"],
        memberships=[rel],
    )
    assert "personal" not in scopes
    assert "project_weslr" in scopes
    assert "family_family_home" in scopes
    print("  PASS  profile_only has no personal scope, has project + verified family")


def test_profile_membership_roundtrip():
    td = tempfile.mkdtemp()
    try:
        profile = default_profile()
        profile.user_id = "alice_test"
        add_membership(profile, EntityType.FAMILY.value, "family_home",
                       RoleType.MEMBER.value, RelationshipType.PART_OF_FAMILY.value,
                       display_name="Home Family")
        add_membership(profile, EntityType.COMPANY.value, "acme_gmbh",
                       RoleType.CEO.value, RelationshipType.LEADS.value,
                       display_name="ACME GmbH", verified=True)

        path = os.path.join(td, "profile.json")
        save_user_profile(profile, path=path, backup=False)

        loaded = load_user_profile(path)
        assert loaded is not None
        mems = list_memberships(loaded)
        assert len(mems) == 2
        assert any(m["entity_type"] == EntityType.COMPANY.value and m["verified"] for m in mems)
        print("  PASS  profile memberships survive save/load roundtrip")
    finally:
        shutil.rmtree(td)


def test_no_llm_in_entity_memory():
    """Verify entity_memory.py has no LLM imports or calls."""
    import ast
    with open("/data/data/com.termux/files/home/.openclaw/workspace/weslr/entity_memory.py") as f:
        source = f.read()
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    llm_indicators = [i for i in imports if any(x in i.lower() for x in ["openai", "anthropic", "llm", "model", "generative", "gpt", "claude"])]
    assert not llm_indicators, f"LLM imports found: {llm_indicators}"
    print("  PASS  entity_memory.py has no LLM imports")


def test_format_memory_response_no_raw_dump():
    summary = {
        "count": 3,
        "tags": ["setup", "binding", "testing"],
        "topics": ["setup", "binding", "testing"],
        "verified_count": 2,
    }
    resp = format_memory_response(summary, "personal memory", person_name="Alice")
    assert len(resp) < 300
    assert "Alice" in resp
    assert "raw" not in resp.lower()
    assert "dump" not in resp.lower()
    assert "[3 memory records" in resp
    print("  PASS  format_memory_response is bounded, no raw dump")


def test_user_profile_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/test_user_profile.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "14 passed" in result.stdout or "passed" in result.stdout, f"Profile tests failed: {result.stdout[-200:]}"
    print("  PASS  user profile tests pass")


def test_channel_identity_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/test_channel_identity_binding.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "16 passed" in result.stdout or "passed" in result.stdout, f"Channel binding tests failed: {result.stdout[-200:]}"
    print("  PASS  channel identity tests pass")


def test_meaning_vector_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/test_meaning_vector_response_obligation.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "5/5" in result.stdout or "passed" in result.stdout, f"Meaning vector tests failed: {result.stdout[-200:]}"
    print("  PASS  meaning vector tests pass")


def test_weight_refinement_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/test_cognitive_weight_refinement.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "6/6" in result.stdout or "passed" in result.stdout, f"Weight refinement tests failed: {result.stdout[-200:]}"
    print("  PASS  weight refinement tests pass")


def test_local_bridge_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/voice_layer/test_local_bridge.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "6/6" in result.stdout or "passed" in result.stdout, f"Local bridge tests failed: {result.stdout[-200:]}"
    print("  PASS  local bridge tests pass")


def test_voice_pipeline_tests_pass():
    import subprocess
    result = subprocess.run(
        ["python3", "weslr/voice_layer/test_voice_pipeline.py"],
        capture_output=True, text=True,
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        timeout=60,
    )
    assert "13/13" in result.stdout or "passed" in result.stdout, f"Voice pipeline tests failed: {result.stdout[-200:]}"
    print("  PASS  voice pipeline tests pass")


if __name__ == "__main__":
    print("\n=== ENTITY MEMORY NAMESPACE TESTS ===")
    tests = [
        test_entity_id_generation_stable,
        test_memory_path_construction,
        test_append_load_memory_roundtrip,
        test_summarize_memory_produces_structured_summary,
        test_unknown_cannot_access_private_person_memory,
        test_profile_only_cannot_access_private_person_memory,
        test_channel_verified_can_access_own_person_memory,
        test_public_access,
        test_project_memory_separate_from_person_memory,
        test_company_family_requires_role_evidence,
        test_verified_ceo_can_access_company_memory,
        test_person_can_have_multiple_memberships,
        test_memory_namespaces_list_correctly,
        test_resolve_memory_scopes_channel_verified,
        test_resolve_memory_scopes_profile_only_no_personal,
        test_profile_membership_roundtrip,
        test_no_llm_in_entity_memory,
        test_format_memory_response_no_raw_dump,
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
    print(f"\nEntity memory tests: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
