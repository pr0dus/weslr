"""
weslr/test_meaning_vector_response_obligation.py

Tests meaning vector, response obligation, and meaning response formation.
"""

import sys
import os
# Add parent of weslr/ to path so 'from weslr.x import y' works
_weslr_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _weslr_root)

from weslr.linguistic_meaning import analyze_meaning
from weslr.response_obligation import determine_response_obligation
from weslr.meaning_state_context import gather_meaning_state
from weslr.meaning_response import form_meaning_response
from sim import load_tier

# ── Test fixtures ─────────────────────────────────────────────────────────────

VERIFIED_FIXTURE = {
    'sender_identity': 'Arthur',
    'known_user_status': 'verified',
    'sender_confidence': 0.95,
    'relationship_depth': 0.25,
    'known_user_evidence': [{'source': 'test_fixture', 'strength': 'high', 'note': 'verified identity'}],
    'onboarding_profile': {'role': 'operator', 'project': 'WESLR', 'preference': 'adaptive'}
}

NONE_FIXTURE = None  # No identity


def _make_state(obligation_type, with_identity=True):
    """Build a minimal MeaningStateContext for testing."""
    from weslr.meaning_state_context import MeaningStateContext
    if with_identity:
        return MeaningStateContext(
            sender_identity='Arthur',
            known_user_status='verified',
            sender_confidence=0.95,
            identity_evidence=[],
            onboarding_profile_summary='role=operator, project=WESLR',
            relationship_depth=0.25,
            memory_available=False,
            memory_summary=None,
            memory_sources_checked=[],
            self_model_summary='Weslr entity intelligence system',
            capability_summary='WESLR entity intelligence',
            continuity_summary=None,
            timeline_summary=None,
            sources_used=['test_fixture'],
            sources_failed=[],
            state_confidence=0.8,
        )
    else:
        return MeaningStateContext(
            sender_identity=None,
            known_user_status='unknown',
            sender_confidence=0.0,
            identity_evidence=[],
            onboarding_profile_summary=None,
            relationship_depth=0.0,
            memory_available=False,
            memory_summary=None,
            memory_sources_checked=[],
            self_model_summary=None,
            capability_summary=None,
            continuity_summary=None,
            timeline_summary=None,
            sources_used=[],
            sources_failed=[],
            state_confidence=0.1,
        )


def _make_obligation(obligation_type, confidence=0.75):
    """Build a minimal ResponseObligation for testing."""
    from weslr.response_obligation import ResponseObligation
    type_map = {
        'verify_identity': ('verify_identity', ['identity_state'], 'bounded'),
        'report_memory_state': ('report_memory_state', ['memory_state'], 'bounded'),
        'describe_self': ('describe_self', ['self_model'], 'bounded'),
        'orient_new_contact': ('orient_new_contact', ['identity_state', 'session_profile'], 'partial'),
    }
    ot, req, disc = type_map.get(obligation_type, ('fallback_uncertainty', [], 'deferred'))
    return ResponseObligation(
        obligation_type=ot,
        required_state=req,
        disclosure_level=disc,
        identity_verification_required=False,
        memory_evidence_required=False,
        should_answer_bounded=True,
        should_ask_clarifying=False,
        confidence=confidence,
        reason='test',
        evidence=[],
    )


def _run(text, fixture=None, l2=None, with_state=True):
    mv = analyze_meaning(text)
    ob = determine_response_obligation(mv, test_metadata=fixture, l2_session=l2)
    if with_state:
        state = gather_meaning_state(ob, test_metadata=fixture, l2_session=l2)
    else:
        state = _make_state(obligation_type=ob.obligation_type, with_identity=(fixture is not None))
    result = form_meaning_response(mv, ob, state)
    return {
        'text': text,
        'meaning_vector': mv,
        'obligation': ob,
        'state': state,
        'result': result,
    }


# ── Group A: Meaning vector classification ──────────────────────────────────────

print("=" * 60)
print("GROUP A — MEANING VECTOR CLASSIFICATION")
print("=" * 60)

identity_group = [
    "do you know me?",
    "have we met before?",
    "do you recognize me?",
    "you remember who I am, right?",
]
memory_group = [
    "what do you remember?",
    "what did we work on last time?",
    "do you still have context?",
    "can you recall our previous thread?",
]
first_contact_group = [
    "I am new here",
    "this is my first time",
    "I don't think we've met",
    "I'm just starting with you",
]
self_model_group = [
    "what are you?",
    "who are you?",
    "what kind of system are you?",
    "explain yourself",
]

def check_group(name, group, expected_dim):
    print(f"\n--- {name} ---")
    all_pass = True
    for text in group:
        mv = analyze_meaning(text)
        score = mv.speech_act_scores.get(expected_dim, 0.0)
        rel_score = mv.relational_scores.get(expected_dim.replace('_query', '_check').replace('_act', ''), 0.0)
        combined = max(score, rel_score)
        status = "PASS" if combined >= 0.3 else "FAIL"
        if combined < 0.3:
            all_pass = False
        print(f"  {status}  {text!r:45s}  {expected_dim}={combined:.2f}")
    return all_pass

g1 = check_group("Identity group", identity_group, "identity_query")
g2 = check_group("Memory group", memory_group, "memory_query")
g3 = check_group("First-contact group", first_contact_group, "first_contact")
g4 = check_group("Self-model group", self_model_group, "self_model_query")

print(f"\nGroup A result: {'ALL PASS' if all([g1,g2,g3,g4]) else 'SOME FAIL'}")


# ── Group B: Response obligation ───────────────────────────────────────────────

print("\n" + "=" * 60)
print("GROUP B — RESPONSE OBLIGATION DETERMINATION")
print("=" * 60)

obligation_cases = [
    ("do you know me?", "verify_identity"),
    ("have we met before?", "verify_identity"),
    ("what do you remember?", "report_memory_state"),
    ("do you still have context?", "report_memory_state"),
    ("I am new here", "orient_new_contact"),
    ("this is my first time", "orient_new_contact"),
    ("what are you?", "describe_self"),
    ("who are you?", "describe_self"),
]

all_pass_b = True
for text, expected in obligation_cases:
    mv = analyze_meaning(text)
    ob = determine_response_obligation(mv, test_metadata=VERIFIED_FIXTURE)
    status = "PASS" if ob.obligation_type == expected else "FAIL"
    if status == "FAIL":
        all_pass_b = False
    print(f"  {status}  {text!r:35s}  expected={expected:25s}  got={ob.obligation_type}")

print(f"\nGroup B result: {'ALL PASS' if all_pass_b else 'SOME FAIL'}")


# ── Group C: Response output (verified identity) ────────────────────────────────

print("\n" + "=" * 60)
print("GROUP C — RESPONSE OUTPUT (VERIFIED IDENTITY)")
print("=" * 60)

FORBIDDEN_PHRASES = [
    "I'm uncertain how to respond",
    "I'm designed to stay grounded in what I understand",
    "signal_uncertainty_strong",
]

def check_output(text, fixture, description):
    mv = analyze_meaning(text)
    ob = determine_response_obligation(mv, test_metadata=fixture)
    state = gather_meaning_state(ob, test_metadata=fixture, l2_session=None)
    result = form_meaning_response(mv, ob, state)
    content = result.content if result else "[no result]"
    
    has_forbidden = any(fp.lower() in content.lower() for fp in FORBIDDEN_PHRASES)
    status = "FAIL" if has_forbidden else "PASS"
    
    print(f"  {status}  {description}")
    print(f"        obligation={ob.obligation_type}")
    print(f"        candidate={result.selected_candidate_type if result else 'NONE'}")
    print(f"        llm_used={result.metadata.get('llm_used') if result else 'N/A'}")
    print(f"        content={content[:80]}")

check_output("do you know me?", VERIFIED_FIXTURE, "identity query (verified)")
check_output("what do you remember?", VERIFIED_FIXTURE, "memory query (verified)")
check_output("I am new here", VERIFIED_FIXTURE, "first contact (verified identity)")
check_output("what are you?", VERIFIED_FIXTURE, "self-model query (verified)")


# ── Group D: Response output (no identity) ─────────────────────────────────────

print("\n" + "=" * 60)
print("GROUP D — RESPONSE OUTPUT (NO IDENTITY)")
print("=" * 60)

check_output("do you know me?", NONE_FIXTURE, "identity query (no identity)")
check_output("have we met before?", NONE_FIXTURE, "relationship check (no identity)")
check_output("what do you remember?", NONE_FIXTURE, "memory query (no identity)")


# ── Compile check ──────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("COMPILE CHECK")
print("=" * 60)
try:
    import weslr.linguistic_meaning
    import weslr.response_obligation
    import weslr.meaning_state_context
    import weslr.meaning_response
    print("  PASS  all modules import correctly")
    compile_pass = True
except Exception as e:
    print(f"  FAIL  import error: {e}")
    compile_pass = False


# ── Group E: Response quality assertions ───────────────────────────────────

print("\n" + "=" * 60)
print("GROUP E — RESPONSE QUALITY ASSERTIONS")
print("=" * 60)

MEMORY_FORBIDDEN = ["Memory file:", "memory/", "Memory file:", "Memory:"]
SELF_MODEL_FORBIDDEN = ["IDENTITY.md", "# IDENTITY.md", "SOUL.md:", "# SOUL.md"]
NEW_CONTACT_FORBIDDEN = ["i'll note it", "i'll remember", "i'll record", "i'll save"]
OCC_AS_WESLR = ["i am occ", "occ is", "as occ", "occ —"]

quality_cases = [
    ("what do you remember?", NONE_FIXTURE, "MEMORY_STATE_REPORT", MEMORY_FORBIDDEN, "memory dump"),
    ("who are you?", NONE_FIXTURE, "SELF_MODEL_DESCRIPTION", SELF_MODEL_FORBIDDEN + OCC_AS_WESLR, "raw IDENTITY.md dump or OCC naming"),
    ("I am new here", NONE_FIXTURE, "NEW_CONTACT_ORIENTATION", NEW_CONTACT_FORBIDDEN, "unsupported write claim"),
    ("what kind of system are you?", NONE_FIXTURE, "SELF_MODEL_DESCRIPTION", SELF_MODEL_FORBIDDEN + OCC_AS_WESLR, "raw file or OCC naming"),
]

all_pass_e = True
for text, fixture, expected_candidate, forbidden_list, description in quality_cases:
    mv = analyze_meaning(text)
    ob = determine_response_obligation(mv, test_metadata=fixture)
    state = gather_meaning_state(ob, test_metadata=fixture, l2_session=None)
    result = form_meaning_response(mv, ob, state)
    content = result.content if result else ""

    # Candidate type check
    candidate_ok = result and result.selected_candidate_type == expected_candidate

    # Forbidden phrase check
    forbidden_found = any(fp.lower() in content.lower() for fp in forbidden_list)

    # LLM check
    llm_ok = result and result.metadata.get("llm_used") is False

    status = "PASS" if (candidate_ok and not forbidden_found and llm_ok) else "FAIL"
    if status == "FAIL":
        all_pass_e = False

    print(f"  {status}  {description}")
    if result:
        print(f"        candidate={result.selected_candidate_type}  (expected={expected_candidate})")
        print(f"        llm_used={result.metadata.get('llm_used')}")
        print(f"        content={content[:90]}...")
        if forbidden_found:
            for fp in forbidden_list:
                if fp.lower() in content.lower():
                    print(f"        WARNING: found forbidden phrase: {fp!r}")

print(f"\nGroup E result: {'ALL PASS' if all_pass_e else 'SOME FAIL'}")


# ── Summary ────────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Group A (meaning classification): {'PASS' if all([g1,g2,g3,g4]) else 'FAIL'}")
print(f"  Group B (obligation determination): {'PASS' if all_pass_b else 'FAIL'}")
print(f"  Group E (response quality):         {'PASS' if all_pass_e else 'FAIL'}")
print(f"  Compile check:                      {'PASS' if compile_pass else 'FAIL'}")
total = sum([all([g1,g2,g3,g4]), all_pass_b, all_pass_e, compile_pass])
print(f"\n  OVERALL: {total}/4 groups passed")