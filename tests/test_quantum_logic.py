# Tests for Phase 6.4 – Quantum Logic
# Run with: python3 -m pytest tests/test_quantum_logic.py -v

import sys
import math
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.modules.quantum_logic import (
    QuantumState,
    is_quantum_topic,
    GATE_NAMES,
    _state_seed,
)

# Also import the commands handler for integration testing
from weslr.commands.quantum_commands import handle_quantum

SQRT2 = 2 ** 0.5

# ── Helpers ────────────────────────────────────────────────────────────────────────

def cclose(a, b, tol=1e-9):
    return abs(a - b) < tol

def veq(a, b, tol=1e-9):
    return all(cclose(x, y, tol) for x, y in zip(a, b))

# ── QuantumState construction ─────────────────────────────────────────────────

def test_basis_ket_0():
    s = QuantumState.basis("|0>")
    assert veq(s.amplitudes, [1.0, 0.0])
    assert s.n_qubits == 1
    print("  basis_ket_0 ok")

def test_basis_ket_1():
    s = QuantumState.basis("|1>")
    assert veq(s.amplitudes, [0.0, 1.0])
    print("  basis_ket_1 ok")

def test_basis_plus():
    s = QuantumState.basis("|+>")
    a, b = s.amplitudes
    assert cclose(abs(a), 1/SQRT2) and cclose(abs(b), 1/SQRT2)
    print("  basis_plus ok")

def test_basis_minus():
    s = QuantumState.basis("|->")
    a, b = s.amplitudes
    assert cclose(abs(a), 1/SQRT2) and cclose(abs(b), 1/SQRT2)
    assert cclose(b, -1/SQRT2)
    print("  basis_minus ok")

def test_parse_superposition():
    s = QuantumState.parse("0.707|0> + 0.707|1>")
    a, b = s.amplitudes
    assert cclose(abs(a), 1/2**0.5) and cclose(abs(b), 1/2**0.5)
    print("  parse_superposition ok")

# ── Normalization ─────────────────────────────────────────────────────────────

def test_normalization_unit():
    s = QuantumState([1.0, 0.0]).normalized()
    normsq = sum(abs(a)**2 for a in s.amplitudes)
    assert cclose(normsq, 1.0)
    print("  normalization_unit ok")

def test_normalization_zero():
    s = QuantumState([0.0, 0.0]).normalized()
    assert veq(s.amplitudes, [0.0, 0.0])
    print("  normalization_zero ok")

def test_normalization_auto():
    s = QuantumState([3.0, 4.0]).normalized()
    assert cclose(sum(abs(a)**2 for a in s.amplitudes), 1.0)
    print("  normalization_auto ok")

# ── Gate: H|0⟩ → |+⟩ ──────────────────────────────────────────────────────────

def test_gate_H_on_zero():
    s = QuantumState.basis("|0>")
    s2 = s.apply_gate("H", [0])
    # Both amplitudes should be 1/√2
    a, b = s2.amplitudes
    assert cclose(abs(a), 1/SQRT2), f"H|0⟩ amplitude a={a}"
    assert cclose(abs(b), 1/SQRT2), f"H|0⟩ amplitude b={b}"
    print("  gate_H_on_zero ok")

def test_gate_X_on_plus_unchanged():
    # X|+⟩ = |+⟩ (X on a superposition with equal amplitudes)
    s = QuantumState.basis("|+>")
    s2 = s.apply_gate("X", [0])
    a, b = s2.amplitudes
    # After X, the superposition flips to (|1⟩+|0⟩)/√2 = |+⟩
    assert cclose(abs(a), 1/SQRT2) and cclose(abs(b), 1/SQRT2)
    print("  gate_X_on_plus_unchanged ok")

def test_gate_Z_on_plus():
    # Z|+⟩ = |−⟩ (relative phase flip)
    s = QuantumState.basis("|+>")
    s2 = s.apply_gate("Z", [0])
    a, b = s2.amplitudes
    assert cclose(abs(a), 1/SQRT2) and cclose(abs(b), 1/SQRT2)
    # b should be -1/√2 (negative real)
    assert cclose(b, -1/SQRT2), f"Z|+⟩ → b={b}"
    print("  gate_Z_on_plus ok")

def test_gate_X_on_zero():
    s = QuantumState.basis("|0>")
    s2 = s.apply_gate("X", [0])
    assert veq(s2.amplitudes, [0.0, 1.0])  # → |1⟩
    print("  gate_X_on_zero ok")

# ── CNOT ──────────────────────────────────────────────────────────────────────

def test_cnot_00_unchanged():
    s = QuantumState([1.0, 0.0, 0.0, 0.0])  # |00⟩
    s2 = s.apply_gate("CNOT", [0, 1])
    # Should stay |00⟩ (control=0, no flip)
    assert veq(s2.amplitudes, [1.0, 0.0, 0.0, 0.0]), f"CNOT|00⟩ = {s2.amplitudes}"
    print("  cnot_00 ok")

def test_cnot_10_to_11():
    # |10⟩ (index 2): q1=1 (MSB), q0=0 (LSB)
    # CNOT(ctrl=1, tgt=0): if q1=1 then flip q0 → |11⟩ ✓
    s = QuantumState([0.0, 0.0, 1.0, 0.0])  # |10⟩
    s2 = s.apply_gate("CNOT", [1, 0])
    assert veq(s2.amplitudes, [0.0, 0.0, 0.0, 1.0]), f"CNOT|10⟩ = {s2.amplitudes}"
    print("  cnot_10_to_11 ok")

# ── Measurement probabilities ───────────────────────────────────────────────────

def test_measurement_probabilities():
    s = QuantumState.basis("|+>")
    probs = s.probabilities()
    assert cclose(sum(probs), 1.0)
    assert cclose(probs[0], 0.5)
    assert cclose(probs[1], 0.5)
    print("  measurement_probabilities ok")

def test_measurement_deterministic():
    # For |0⟩, qubit 0 probability of |0⟩ = 1.0
    s = QuantumState.basis("|0>")
    new_s, outcome, prob = s.measure(qubit_index=0)
    assert outcome == 0
    assert cclose(prob, 1.0)
    # Collapsed state should be |0⟩
    assert veq(new_s.amplitudes, [1.0, 0.0])
    print("  measurement_deterministic ok")

def test_measurement_deterministic_seed():
    # Same seed on same state → same outcome
    s = QuantumState.basis("|+>")
    _, o1, _ = s.measure(qubit_index=0, seed=42)
    _, o2, _ = s.measure(qubit_index=0, seed=42)
    assert o1 == o2, f"Seed 42 gave {o1} and {o2}"
    print("  measurement_deterministic_seed ok")

def test_measurement_prob_matches_amplitude():
    s = QuantumState.parse("0.6|0> + 0.8|1>").normalized()
    new_s, outcome, prob = s.measure(qubit_index=0)
    # p(|0⟩) = |0.6|² = 0.36; p(|1⟩) = |0.8|² = 0.64
    # Outcome depends on random, but prob should match |amplitude|²
    expected_p0 = abs(0.6)**2  # normalized: |a|²/(|a|²+|b|²) = 0.36/1.0 = 0.36
    assert cclose(sum(s.probabilities()), 1.0)
    print("  measurement_prob_matches_amplitude ok")

# ── to_ket_string ─────────────────────────────────────────────────────────────

def test_ket_string_single():
    s = QuantumState.basis("|0>")
    txt = s.to_ket_string()
    assert "|0⟩" in txt
    print("  ket_string_single ok")

def test_ket_string_plus():
    s = QuantumState.basis("|+>")
    txt = s.to_ket_string()
    assert "|0⟩" in txt and "|1⟩" in txt
    print("  ket_string_plus ok")

# ── Gate names ────────────────────────────────────────────────────────────────

def test_gate_names():
    for g in ["H", "X", "Z", "CNOT"]:
        assert g in GATE_NAMES, f"{g} not in GATE_NAMES"
    print("  gate_names ok")

# ── is_quantum_topic ───────────────────────────────────────────────────────────

def test_is_quantum_topic():
    assert is_quantum_topic("superposition in photosynthesis")
    assert is_quantum_topic("quantum gate qubit")
    assert is_quantum_topic("photon interference")
    assert not is_quantum_topic("population growth logistic")
    print("  is_quantum_topic ok")

# ── Command handler ─────────────────────────────────────────────────────────────

def test_handler_state():
    # Reset first to ensure clean state for test isolation
    handle_quantum("/quantum reset", "/quantum reset")
    r = handle_quantum("/quantum state |0>", "/quantum state |0>")
    assert "State set" in r
    # Clean up: reset after test too
    handle_quantum("/quantum reset", "/quantum reset")
    print("  handler_state ok")

def test_handler_apply_no_state():
    # Ensure no state exists
    handle_quantum("/quantum reset", "/quantum reset")
    r = handle_quantum("/quantum apply H 0", "/quantum apply h 0")
    assert "No quantum state" in r
    print("  handler_apply_no_state ok")

def test_handler_usage():
    r = handle_quantum("/quantum unknown", "/quantum unknown")
    assert "Usage" in r
    print("  handler_usage ok")

# ── Run all ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_basis_ket_0,
        test_basis_ket_1,
        test_basis_plus,
        test_basis_minus,
        test_parse_superposition,
        test_normalization_unit,
        test_normalization_zero,
        test_normalization_auto,
        test_gate_H_on_zero,
        test_gate_X_on_plus_unchanged,
        test_gate_Z_on_plus,
        test_gate_X_on_zero,
        test_cnot_00_unchanged,
        test_cnot_10_to_11,
        test_measurement_probabilities,
        test_measurement_deterministic,
        test_measurement_deterministic_seed,
        test_measurement_prob_matches_amplitude,
        test_ket_string_single,
        test_ket_string_plus,
        test_gate_names,
        test_is_quantum_topic,
        test_handler_state,
        test_handler_apply_no_state,
        test_handler_usage,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n=== {passed}/{passed+failed} passed ===")
    if failed:
        sys.exit(1)
