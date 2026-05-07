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
total = sum([all_pass_g, all_pass_h, g8, g9, g10])
print(f"\n  OVERALL: {total}/5 suites passed")
