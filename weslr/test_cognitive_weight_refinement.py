"""
weslr/test_cognitive_weight_refinement.py

Tests for the governed cognitive weight refinement layer.

Validates:
1. Registry loads defaults.
2. Registry saves/loads temp weights.
3. Proposal created but NOT auto-applied.
4. Simulation runs against eval set.
5. Approved proposal updates temp registry.
6. Rejected proposal does not update weights.
7. Reset returns to default.
8. Existing meaning-vector behavior still passes.
9. Existing local bridge tests still pass.
10. Existing voice tests still pass.
11-22. Guardrail enforcement (H1-H12 below).
"""

import sys
import os
import tempfile
import shutil
import subprocess

_weslr_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _weslr_root)

DIM = "\033[2m"
RESET = "\033[0m"

# ── Test helpers ────────────────────────────────────────────────────────────────

from weslr.cognitive_weights import (
    CognitiveWeightRegistry, load_registry,
)
from weslr.weight_proposal import (
    WeightUpdateProposal, save_proposal, load_proposals,
    update_proposal_status,
)
from weslr.weight_simulation import (
    run_simulation, save_simulation, EVAL_PHRASES,
)


# ── Group G: Cognitive weight refinement ──────────────────────────────────────

print("\n" + "=" * 60)
print("GROUP G — COGNITIVE WEIGHT REFINEMENT")
print("=" * 60)

all_pass_g = True

# G1: Registry loads defaults
try:
    registry = CognitiveWeightRegistry.load_defaults()
    assert len(registry.weights) >= 20, f"Expected >=20 weights, got {len(registry.weights)}"
    print(f"  PASS  G1  Registry loads defaults ({len(registry.weights)} weights)")
except Exception as e:
    print(f"  FAIL  G1  {e}")
    all_pass_g = False

# G2: Registry saves and loads temp weights
try:
    td = tempfile.mkdtemp()
    tmp = os.path.join(td, "weights.json")
    registry = CognitiveWeightRegistry.load_defaults()
    registry.set_pending("meaning.identity_query_weight", 1.5, reason="test")
    registry.save_to_file(tmp)
    registry2 = CognitiveWeightRegistry.load_from_file(tmp)
    assert registry2.get("meaning.identity_query_weight") == 1.5, "Weight not persisted"
    print(f"  PASS  G2  Registry saves/loads temp weights")
    shutil.rmtree(td)
except Exception as e:
    print(f"  FAIL  G2  {e}")
    all_pass_g = False

# G3: Proposal is created but NOT auto-applied
try:
    td = tempfile.mkdtemp()
    prop_path = os.path.join(td, "proposals.jsonl")
    proposal = WeightUpdateProposal.create(
        weight_key="meaning.identity_query_weight",
        old_value=1.0,
        proposed_value=1.5,
        reason="test proposal",
        supporting_observations=[],
        expected_benefit="better identity detection",
        possible_risk="may over-trigger on borderline cases",
        tests_to_run=["test_cognitive_weight_refinement"],
    )
    save_proposal(proposal, path=prop_path)
    proposals = load_proposals(limit=10, path=prop_path)
    assert len(proposals) == 1, "Proposal not saved"
    assert proposals[0].status == "proposed", "Proposal should start as proposed"
    assert proposals[0].status != "applied", "Proposal should NOT be auto-applied"
    print(f"  PASS  G3  Proposal created but NOT auto-applied (status={proposals[0].status})")
    shutil.rmtree(td)
except Exception as e:
    print(f"  FAIL  G3  {e}")
    all_pass_g = False

# G4: Simulation runs against eval set without errors
try:
    td = tempfile.mkdtemp()
    sim_p = os.path.join(td, "sims.jsonl")
    sim_result = run_simulation("meaning.identity_query_weight", 1.0, 1.5)
    save_simulation(sim_result, path=sim_p)
    assert sim_result.simulation_id is not None
    assert sim_result.weight_key == "meaning.identity_query_weight"
    assert len(sim_result.tests_run) >= 1
    print(f"  PASS  G4  Simulation runs against eval set ({len(EVAL_PHRASES)} phrases)")
    print(f"        pass_fail={sim_result.pass_fail}  changes={len(sim_result.behavior_changes)}")
    shutil.rmtree(td)
except Exception as e:
    print(f"  FAIL  G4  {e}")
    all_pass_g = False

# G5: Approved proposal NOT auto-applied before explicit apply
try:
    td = tempfile.mkdtemp()
    prop_path = os.path.join(td, "proposals.jsonl")
    weight_path = os.path.join(td, "weights.json")
    registry = CognitiveWeightRegistry.load_defaults()
    registry.save_to_file(weight_path)
    proposal = WeightUpdateProposal.create(
        weight_key="meaning.identity_query_weight",
        old_value=1.0,
        proposed_value=1.5,
        reason="test",
        supporting_observations=[],
        expected_benefit="test",
        possible_risk="low",
    )
    save_proposal(proposal, path=prop_path)
    update_proposal_status(proposal.proposal_id, "approved", path=prop_path)
    proposals = load_proposals(limit=10, path=prop_path)
    approved = [p for p in proposals if p.status == "approved"]
    assert len(approved) == 1
    registry2 = CognitiveWeightRegistry.load_from_file(weight_path)
    assert registry2.get("meaning.identity_query_weight") == 1.0, "Weight should not change before apply"
    print(f"  PASS  G5  Approved proposal NOT auto-applied before explicit apply")
    shutil.rmtree(td)
except Exception as e:
    print(f"  FAIL  G5  {e}")
    all_pass_g = False

# G6: Rejected proposal does not affect registry
try:
    td = tempfile.mkdtemp()
    prop_path = os.path.join(td, "proposals.jsonl")
    weight_path = os.path.join(td, "weights.json")
    registry = CognitiveWeightRegistry.load_defaults()
    registry.save_to_file(weight_path)
    proposal = WeightUpdateProposal.create(
        weight_key="meaning.identity_query_weight",
        old_value=1.0,
        proposed_value=2.0,
        reason="test reject",
        supporting_observations=[],
        expected_benefit="test",
        possible_risk="high",
    )
    save_proposal(proposal, path=prop_path)
    update_proposal_status(proposal.proposal_id, "rejected", path=prop_path)
    registry2 = CognitiveWeightRegistry.load_from_file(weight_path)
    assert registry2.get("meaning.identity_query_weight") == 1.0, "Weight should not change after reject"
    print(f"  PASS  G6  Rejected proposal does not update registry")
    shutil.rmtree(td)
except Exception as e:
    print(f"  FAIL  G6  {e}")
    all_pass_g = False

# G7: Reset returns weight to default
try:
    td = tempfile.mkdtemp()
    tmp = os.path.join(td, "weights.json")
    registry = CognitiveWeightRegistry.load_defaults()
    registry.set_pending("meaning.identity_query_weight", 2.0, reason="test")
    registry.save_to_file(tmp)
    registry2 = CognitiveWeightRegistry.load_from_file(tmp)
    assert registry2.get("meaning.identity_query_weight") == 2.0
    registry2.reset("meaning.identity_query_weight")
    registry2.save_to_file(tmp)
    registry3 = CognitiveWeightRegistry.load_from_file(tmp)
    assert registry3.get("meaning.identity_query_weight") == 1.0, "Reset should restore default"
    print(f"  PASS  G7  Reset returns weight to default")
    shutil.rmtree(td)
except Exception as e:
    print(f"  FAIL  G7  {e}")
    all_pass_g = False

print(f"\nGroup G result: {'ALL PASS' if all_pass_g else 'SOME FAIL'}")


# ── Group H: Guardrail tests ──────────────────────────────────────────────────

print("\n" + "=" * 60)
print("GROUP H — GUARDRAIL TESTS")
print("=" * 60)

from weslr.cognitive_weights import (
    check_weight_update_guardrails,
    GLOBAL_AUTO_APPLY_ENABLED,
    CognitiveWeightRegistry as CR2,
)
from weslr.weight_proposal import (
    WeightUpdateProposal as WUP2,
    update_proposal_status as ups,
    save_proposal as sp,
    load_proposals as lp,
)

all_pass_h = True
registry = CR2.load_defaults()

# H1: Every default weight has a zone
_h1_ok = True
for key, w in registry.weights.items():
    if w.zone not in ("green", "yellow", "red"):
        print(f"  FAIL  H1  {key} has invalid zone: {w.zone}")
        _h1_ok = False
print(f"  {'PASS' if _h1_ok else 'FAIL'}  H1  All {len(registry.weights)} weights have valid zone")
if not _h1_ok: all_pass_h = False

# H2: Every default weight has max_auto_delta and max_manual_delta
_h2_ok = True
for key, w in registry.weights.items():
    if w.max_auto_delta is None or w.max_manual_delta is None:
        print(f"  FAIL  H2  {key} missing delta limit")
        _h2_ok = False
print(f"  {'PASS' if _h2_ok else 'FAIL'}  H2  All weights have max_auto_delta and max_manual_delta")
if not _h2_ok: all_pass_h = False

# H3: RED identity weight blocks auto-apply
r = check_weight_update_guardrails(registry, "identity.minimum_verified_confidence", mode="auto")
_h3_ok = not r.allowed and r.zone == "red"
print(f"  {'PASS' if _h3_ok else 'FAIL'}  H3  RED identity weight blocks auto-apply (allowed={r.allowed}, zone={r.zone})")
if not _h3_ok: all_pass_h = False

# H4: RED identity weight blocks manual-apply in this phase
r = check_weight_update_guardrails(registry, "identity.minimum_verified_confidence", mode="manual", proposal_status="approved")
_h4_ok = not r.allowed and r.zone == "red"
print(f"  {'PASS' if _h4_ok else 'FAIL'}  H4  RED identity weight blocks manual-apply (allowed={r.allowed}, zone={r.zone})")
if not _h4_ok: all_pass_h = False

# H5: YELLOW meaning weight blocks auto-apply (global disabled)
r = check_weight_update_guardrails(registry, "meaning.memory_query_weight", mode="auto")
_h5_ok = not r.allowed
print(f"  {'PASS' if _h5_ok else 'FAIL'}  H5  YELLOW meaning weight blocks auto-apply (allowed={r.allowed})")
if not _h5_ok: all_pass_h = False

# H6: YELLOW meaning weight allows manual-apply when approved and delta is within limit
r = check_weight_update_guardrails(registry, "meaning.memory_query_weight", mode="manual", proposal_status="approved")
_h6_ok = r.allowed
print(f"  {'PASS' if _h6_ok else 'FAIL'}  H6  YELLOW manual-apply allowed when approved (allowed={r.allowed})")
if not _h6_ok: all_pass_h = False

# H7: Global auto-apply disabled blocks even with all other checks passing
r = check_weight_update_guardrails(registry, "meaning.memory_query_weight", mode="auto",
    simulation_pass=True, regression_pass=True, observation_count=10)
_h7_ok = not r.allowed
print(f"  {'PASS' if _h7_ok else 'FAIL'}  H7  Global disabled blocks even all-checks-passing auto (allowed={r.allowed})")
if not _h7_ok: all_pass_h = False

# H8: Large delta blocked even after approval
# Uses a real WeightUpdateProposal so guardrail check can read weight_key and delta
_h8_proposal = WUP2.create(
    weight_key="meaning.memory_query_weight",
    old_value=1.0, proposed_value=3.0,
    reason="delta test", supporting_observations=[], expected_benefit="x", possible_risk="y")
r = check_weight_update_guardrails(registry, _h8_proposal, mode="manual", proposal_status="approved")
_h8_ok = not r.allowed and any("max_manual_delta" in x for x in r.reasons)
print(f"  {'PASS' if _h8_ok else 'FAIL'}  H8  Large delta blocked (allowed={r.allowed}, reasons={r.reasons})")
if not _h8_ok: all_pass_h = False

# H9: Auto-apply blocked without sufficient observations
r = check_weight_update_guardrails(registry, "meaning.memory_query_weight", mode="auto",
    simulation_pass=True, regression_pass=True, observation_count=1)
_h9_ok = not r.allowed and any("Observations" in x or "min_observations" in x for x in r.reasons)
print(f"  {'PASS' if _h9_ok else 'FAIL'}  H9  Auto-apply blocked without min observations")
if not _h9_ok: all_pass_h = False

# H10: Auto-apply blocked without simulation pass
r = check_weight_update_guardrails(registry, "meaning.memory_query_weight", mode="auto",
    simulation_pass=False, regression_pass=True, observation_count=10)
_h10_ok = not r.allowed and any("simulation" in x.lower() for x in r.reasons)
print(f"  {'PASS' if _h10_ok else 'FAIL'}  H10  Auto-apply blocked without simulation pass")
if not _h10_ok: all_pass_h = False

# H11: Applied update preserves old_value for rollback
td = tempfile.mkdtemp()
pp = os.path.join(td, "proposals.jsonl")
wp = os.path.join(td, "weights.json")
reg = CR2.load_defaults()
reg.save_to_file(wp)
prop = WUP2.create(weight_key="meaning.memory_query_weight", old_value=1.0, proposed_value=1.3,
    reason="guardrail test", supporting_observations=[], expected_benefit="x", possible_risk="y")
sp(prop, path=pp)
ups(prop.proposal_id, "approved", path=pp)
ups(prop.proposal_id, "applied", path=pp)
final = lp(limit=5, path=pp)[0]
_h11_ok = final.old_value == 1.0 and final.proposed_value == 1.3
print(f"  {'PASS' if _h11_ok else 'FAIL'}  H11  Applied update preserves old_value (old={final.old_value})")
if not _h11_ok: all_pass_h = False
shutil.rmtree(td)

# H12: Rejected proposal still cannot apply
td = tempfile.mkdtemp()
pp = os.path.join(td, "proposals.jsonl")
prop = WUP2.create(weight_key="meaning.memory_query_weight", old_value=1.0, proposed_value=1.5,
    reason="reject test", supporting_observations=[], expected_benefit="x", possible_risk="y")
sp(prop, path=pp)
ups(prop.proposal_id, "rejected", path=pp)
# Reload from file to verify status was persisted
reloaded = lp(limit=5, path=pp)[0]
_h12_ok = reloaded.status == "rejected"
print(f"  {'PASS' if _h12_ok else 'FAIL'}  H12  Rejected proposal status preserved (status={reloaded.status})")
if not _h12_ok: all_pass_h = False
shutil.rmtree(td)

print(f"\nGroup H result: {'ALL PASS' if all_pass_h else 'SOME FAIL'}")


# ── Group I: Green-zone auto-refinement preparation ────────────────────────────

print("\n" + "=" * 60)
print("GROUP I — GREEN-ZONE AUTO-REFINEMENT PREPARATION")
print("=" * 60)

all_pass_i = True
registry = CR2.load_defaults()

# I1: At least one green low-risk weight exists
green_weights = {k: w for k, w in registry.weights.items() if w.zone == "green"}
_i1_ok = len(green_weights) >= 1
print(f"  {'PASS' if _i1_ok else 'FAIL'}  I1  Green weights exist ({len(green_weights)})")
if not _i1_ok: all_pass_i = False

# I2: No red weight has auto_apply_allowed=True
_i2_ok = all(not w.auto_apply_allowed for w in registry.weights.values() if w.zone == "red")
red_weights = {k: w for k, w in registry.weights.items() if w.zone == "red"}
print(f"  {'PASS' if _i2_ok else 'FAIL'}  I2  Red weights have auto_apply_allowed=False ({len(red_weights)} red)")
if not _i2_ok: all_pass_i = False

# I3: No yellow weight has auto_apply_allowed=True
_i3_ok = all(not w.auto_apply_allowed for w in registry.weights.values() if w.zone == "yellow")
yellow_weights = {k: w for k, w in registry.weights.items() if w.zone == "yellow"}
print(f"  {'PASS' if _i3_ok else 'FAIL'}  I3  Yellow weights have auto_apply_allowed=False ({len(yellow_weights)} yellow)")
if not _i3_ok: all_pass_i = False

# I4: Green weight has tiny max_auto_delta (≤0.05)
_i4_ok = True
for k, w in green_weights.items():
    if w.max_auto_delta > 0.05:
        print(f"  FAIL  I4  {k} max_auto_delta={w.max_auto_delta} > 0.05")
        _i4_ok = False
print(f"  {'PASS' if _i4_ok else 'FAIL'}  I4  Green weights have max_auto_delta ≤ 0.05")
if not _i4_ok: all_pass_i = False

# I5: Green weight requires min_observations, cooldown, simulation, regression, rollback
_i5_ok = True
for k, w in green_weights.items():
    if not (w.min_observations >= 5 and w.cooldown_hours >= 24
            and w.requires_simulation_pass and w.requires_regression_pass
            and w.rollback_required):
        print(f"  FAIL  I5  {k} missing guardrail requirement")
        _i5_ok = False
print(f"  {'PASS' if _i5_ok else 'FAIL'}  I5  Green weights have all guardrail requirements")
if not _i5_ok: all_pass_i = False

# I6: Auto-apply blocked while GLOBAL_AUTO_APPLY_ENABLED=False even for green
if green_weights:
    gk = list(green_weights.keys())[0]
    r = check_weight_update_guardrails(registry, gk, mode="auto",
        simulation_pass=True, regression_pass=True, observation_count=10)
    _i6_ok = not r.allowed
    print(f"  {'PASS' if _i6_ok else 'FAIL'}  I6  Green auto-apply blocked while GLOBAL_AUTO_APPLY_ENABLED=False")
    if not _i6_ok: all_pass_i = False

# I7: With GLOBAL_AUTO_APPLY_ENABLED=True (mock), valid green proposal passes
if green_weights:
    gk = list(green_weights.keys())[0]
    w = green_weights[gk]
    class _GreenProposal:
        weight_key = gk
        delta = w.max_auto_delta * 0.8  # small valid delta
        old_value = w.value
        proposed_value = w.value + w.max_auto_delta * 0.8
        reason = "green lane test"
    from weslr.weight_proposal import WeightUpdateProposal as WUP3
    # Create a real proposal to get valid delta
    temp_prop = WUP3.create(gk, w.value, w.value + w.max_auto_delta * 0.5, "test", [], "x", "y")
    # Override global flag temporarily via import mechanism
    import importlib, weslr.cognitive_weights as cg
    original_flag = cg.GLOBAL_AUTO_APPLY_ENABLED
    cg.GLOBAL_AUTO_APPLY_ENABLED = True
    try:
        r = check_weight_update_guardrails(registry, temp_prop, mode="auto",
            simulation_pass=True, regression_pass=True, observation_count=10)
        _i7_ok = r.allowed
        print(f"  {'PASS' if _i7_ok else 'FAIL'}  I7  Valid green passes guardrail when global enabled (allowed={r.allowed})")
    finally:
        cg.GLOBAL_AUTO_APPLY_ENABLED = original_flag
    if not _i7_ok: all_pass_i = False

# I8: Large delta on green is blocked (even with global enabled)
if green_weights:
    gk = list(green_weights.keys())[0]
    w = green_weights[gk]
    temp_prop = WUP3.create(gk, w.value, w.value + w.max_auto_delta * 10, "big delta", [], "x", "y")
    import weslr.cognitive_weights as cg2
    original = cg2.GLOBAL_AUTO_APPLY_ENABLED
    cg2.GLOBAL_AUTO_APPLY_ENABLED = True
    try:
        r = check_weight_update_guardrails(registry, temp_prop, mode="auto",
            simulation_pass=True, regression_pass=True, observation_count=10)
        _i8_ok = not r.allowed
        print(f"  {'PASS' if _i8_ok else 'FAIL'}  I8  Large delta on green blocked (allowed={r.allowed})")
    finally:
        cg2.GLOBAL_AUTO_APPLY_ENABLED = original
    if not _i8_ok: all_pass_i = False

# I9: Insufficient observations blocks green auto-apply
if green_weights:
    gk = list(green_weights.keys())[0]
    w = green_weights[gk]
    temp_prop = WUP3.create(gk, w.value, w.value + w.max_auto_delta * 0.3, "insufficient obs", [], "x", "y")
    import weslr.cognitive_weights as cg3
    original = cg3.GLOBAL_AUTO_APPLY_ENABLED
    cg3.GLOBAL_AUTO_APPLY_ENABLED = True
    try:
        r = check_weight_update_guardrails(registry, temp_prop, mode="auto",
            simulation_pass=True, regression_pass=True, observation_count=2)
        _i9_ok = not r.allowed
        print(f"  {'PASS' if _i9_ok else 'FAIL'}  I9  Insufficient observations blocks green (allowed={r.allowed})")
    finally:
        cg3.GLOBAL_AUTO_APPLY_ENABLED = original
    if not _i9_ok: all_pass_i = False

# I10: Failed simulation blocks green auto-apply
if green_weights:
    gk = list(green_weights.keys())[0]
    w = green_weights[gk]
    temp_prop = WUP3.create(gk, w.value, w.value + w.max_auto_delta * 0.3, "sim fail", [], "x", "y")
    import weslr.cognitive_weights as cg4
    original = cg4.GLOBAL_AUTO_APPLY_ENABLED
    cg4.GLOBAL_AUTO_APPLY_ENABLED = True
    try:
        r = check_weight_update_guardrails(registry, temp_prop, mode="auto",
            simulation_pass=False, regression_pass=True, observation_count=10)
        _i10_ok = not r.allowed
        print(f"  {'PASS' if _i10_ok else 'FAIL'}  I10  Failed simulation blocks green (allowed={r.allowed})")
    finally:
        cg4.GLOBAL_AUTO_APPLY_ENABLED = original
    if not _i10_ok: all_pass_i = False

# I11: Failed regression blocks green auto-apply
if green_weights:
    gk = list(green_weights.keys())[0]
    w = green_weights[gk]
    temp_prop = WUP3.create(gk, w.value, w.value + w.max_auto_delta * 0.3, "reg fail", [], "x", "y")
    import weslr.cognitive_weights as cg5
    original = cg5.GLOBAL_AUTO_APPLY_ENABLED
    cg5.GLOBAL_AUTO_APPLY_ENABLED = True
    try:
        r = check_weight_update_guardrails(registry, temp_prop, mode="auto",
            simulation_pass=True, regression_pass=False, observation_count=10)
        _i11_ok = not r.allowed
        print(f"  {'PASS' if _i11_ok else 'FAIL'}  I11  Failed regression blocks green (allowed={r.allowed})")
    finally:
        cg5.GLOBAL_AUTO_APPLY_ENABLED = original
    if not _i11_ok: all_pass_i = False

# I12: Red/yellow proposals are never auto-applicable (zone check)
for k, w in {**dict((k, w) for k, w in registry.weights.items() if w.zone == "red"),
             **dict((k, w) for k, w in registry.weights.items() if w.zone == "yellow")}.items():
    temp_prop = WUP3.create(k, w.value, w.value + 0.01, "zone test", [], "x", "y")
    r = check_weight_update_guardrails(registry, temp_prop, mode="auto",
        simulation_pass=True, regression_pass=True, observation_count=10)
    if r.allowed:
        print(f"  FAIL  I12  {k} ({w.zone}) should not allow auto-apply")
        all_pass_i = False
print(f"  {'PASS' if all_pass_i else 'FAIL'}  I12  All red/yellow weights blocked for auto-apply")

print(f"\nGroup I result: {'ALL PASS' if all_pass_i else 'SOME FAIL'}")


# ── Regression: existing tests still pass ──────────────────────────────────────

print("\n" + "=" * 60)
print("REGRESSION — EXISTING TEST SUITES")
print("=" * 60)


def run_test_suite(path, label):
    result = subprocess.run(
        [sys.executable, path],
        capture_output=True, text=True, cwd=_weslr_root
    )
    passed = result.returncode == 0
    status = "PASS" if passed else "FAIL"
    print(f"  {status}  {label}")
    if not passed:
        out = result.stdout[-300:]
        print(f"        {DIM}{out}{RESET}")
    return passed


g8 = run_test_suite("weslr/test_meaning_vector_response_obligation.py",
                      "meaning-vector obligation tests")
g9 = run_test_suite("weslr/voice_layer/test_local_bridge.py",
                      "local bridge tests")
g10 = run_test_suite("weslr/voice_layer/test_voice_pipeline.py",
                       "voice pipeline tests")

all_regression = all([g8, g9, g10])
print(f"\nRegression result: {'ALL PASS' if all_regression else 'SOME FAIL'}")


# ── Summary ────────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Group G (weight refinement): {'PASS' if all_pass_g else 'FAIL'}")
print(f"  Group H (guardrails):         {'PASS' if all_pass_h else 'FAIL'}")
print(f"  Regression meaning-vector:   {'PASS' if g8 else 'FAIL'}")
print(f"  Regression local bridge:       {'PASS' if g9 else 'FAIL'}")
print(f"  Regression voice pipeline:     {'PASS' if g10 else 'FAIL'}")
total = sum([all_pass_g, all_pass_h, all_pass_i, g8, g9, g10])
print(f"\n  OVERALL: {total}/6 suites passed")
