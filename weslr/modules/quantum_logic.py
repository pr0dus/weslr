# weslr.modules.quantum_logic – Phase 6.4 quantum state, gates, measurement
"""
Quantum logic awareness for Weslr.

Provides:
  - QuantumState: normalized state vector (1–3 qubits)
  - apply_gate(): matrix multiplication with gate definitions
  - measure(): probabilistic collapse via seeded PRNG
  - to_ket_string(): human-readable Dirac notation
  - QUANTUM_KEYWORDS: detection set for explore integration

All operations are local, read-only, no external calls.
Measurement uses Python's random.Random with a hash-based seed so that
the same state always produces the same outcome for the same qubit index.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Optional

# ── Gate definitions ────────────────────────────────────────────────────────────

# Use numpy if available, otherwise pure-Python lists
try:
    import numpy as np
    _NUMPY = True
except Exception:
    _NUMPY = False
    np = None  # type: ignore


# 1-qubit gates (2×2 complex matrices, acting on computational basis |0⟩, |1⟩)
_H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2) if _NUMPY else None
_X = np.array([[0, 1], [1, 0]], dtype=complex) if _NUMPY else None
_Z = np.array([[1, 0], [0, -1]], dtype=complex) if _NUMPY else None

# 2-qubit gates (4×4 for CNOT, qubit 0=control, qubit 1=target in |00⟩,|01⟩,|10⟩,|11⟩ ordering)
_CNOT = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
], dtype=complex) if _NUMPY else None

GATES_1: dict[str, "np.ndarray | list"] = {
    "H": _H,
    "X": _X,
    "Z": _Z,
}

GATES_2: dict[str, "np.ndarray | list"] = {
    "CNOT": _CNOT,
}

# Ordered list of all gates
GATE_NAMES = sorted(set(GATES_1) | set(GATES_2))


# ── QuantumState ───────────────────────────────────────────────────────────────

@dataclass
class QuantumState:
    """Normalized N-qubit quantum state vector.

    Representation:
      - 1 qubit:  [α, β]  (|0⟩ = [1,0], |1⟩ = [0,1])
      - 2 qubits: [α00, α01, α10, α11]  (tensor product |q1⟩⊗|q0⟩ order)
      - 3 qubits: [α000 … α111]  (8 amplitudes)

    The qubit order matches the computational basis ordering:
    qubit 0 = rightmost in Dirac notation |q1 q0⟩.
    """

    amplitudes: list[complex]
    n_qubits: int = field(init=False)

    def __post_init__(self):
        n = len(self.amplitudes)
        if n == 0 or (n & (n - 1)) != 0:
            raise ValueError(f"Amplitude list length must be a power of 2, got {n}")
        self.n_qubits = int(n).bit_length() - 1

    @staticmethod
    def basis(state_str: str) -> "QuantumState":
        """Parse a basis-state Dirac string.

        Single-qubit: '|0>', '|1>', '|+>', '|->', '|+i>', '|-i>'
        Multi-qubit:   '|00>', '|01>', '|10>', '|11>', '|000>', etc.
        """
        import re
        s = state_str.strip()

        # Handle single-qubit basis states
        if s == "|0>":
            return QuantumState([1, 0])
        if s == "|1>":
            return QuantumState([0, 1])
        if s in ("|+>", "|+⟩"):
            a = 1 / (2 ** 0.5)
            return QuantumState([a, a])
        if s in ("|->", "|−⟩"):
            a = 1 / (2 ** 0.5)
            return QuantumState([a, -a])
        if s in ("|+i>", "|+i⟩"):
            a = 1 / (2 ** 0.5)
            return QuantumState([a, 1j * a])
        if s in ("|-i>", "|-i⟩"):
            a = 1 / (2 ** 0.5)
            return QuantumState([a, -1j * a])

        # Multi-qubit binary states: |00>, |0101>, etc.
        bin_match = re.match(r"^\|([01]+)\s*>$", s)
        if bin_match:
            bits = bin_match.group(1)
            n = len(bits)
            if n > 3:
                raise ValueError(f"Maximum 3 qubits supported, got {n}")
            idx = int(bits, 2)
            dim = 2 ** n
            amps = [0.0] * dim
            amps[idx] = 1.0
            return QuantumState(amps)

        raise ValueError(f"Unknown basis state: {state_str}")

    @staticmethod
    def parse(text: str) -> "QuantumState":
        """Parse a Dirac expression: 'a|0> + b|1>' with numeric a,b."""
        import re
        text = text.strip()
        # Simple pattern: optional (coeff) followed by |0> or |1>
        # Captures: whole term before |bit>, and the bit (0 or 1)
        # Handles: "0.5|0>", "+ 0.5|1>", "|0>", "|1>", etc.
        terms = re.findall(
            r"([+-]?\s*[\d.]+)\s*\|\s*([01])\s*>",
            text,
        )
        if not terms:
            raise ValueError(f"Cannot parse quantum state: {text!r}")

        coeffs: dict[int, complex] = {0: 0, 1: 0}
        for raw, bit_str in terms:
            bit = int(bit_str)
            # Remove all whitespace so "+ 0.707" → "+0.707"
            raw = "".join(raw.split())
            try:
                val = float(raw) if raw not in ("+", "-", "") else (1 if raw in ("+", "") else -1)
                coeffs[bit] += complex(val, 0)
            except ValueError:
                coeffs[bit] += complex(1, 0)

        return QuantumState([coeffs[0], coeffs[1]]).normalized()

    def normalized(self) -> "QuantumState":
        """Return a new QuantumState with L2 norm = 1."""
        import math
        if _NUMPY:
            norm = float(np.linalg.norm(self.amplitudes))
        else:
            norm = math.sqrt(sum(abs(a) ** 2 for a in self.amplitudes))
        if norm == 0:
            return QuantumState([0.0] * len(self.amplitudes))
        return QuantumState([a / norm for a in self.amplitudes])

    def probabilities(self) -> list[float]:
        """Return P(|x⟩) = |amplitude|² for each basis state."""
        return [abs(a) ** 2 for a in self.amplitudes]

    def probability_of(self, index: int) -> float:
        """Return probability of basis state at `index`."""
        return abs(self.amplitudes[index]) ** 2

    # ── Gate application ──────────────────────────────────────────────────────

    def apply_gate(self, gate_name: str, qubit_indices: list[int]) -> "QuantumState":
        """Apply `gate_name` to the specified qubit(s).

        For single-qubit gates (H, X, Z): pass [qubit_index].
        For CNOT: pass [control_index, target_index].

        Uses tensor-product formalism to build the full-matrix and applies
        it to the state vector.
        """
        if gate_name not in GATE_NAMES:
            raise ValueError(f"Unknown gate: {gate_name}")

        if gate_name in GATES_1:
            if len(qubit_indices) != 1:
                raise ValueError(f"Gate {gate_name} needs 1 qubit index, got {len(qubit_indices)}")
            [qi] = qubit_indices
            gate_mat = GATES_1[gate_name]
            full_mat = _tensor_product(self.n_qubits, qi, gate_mat)

        elif gate_name in GATES_2:
            if len(qubit_indices) != 2:
                raise ValueError(f"Gate {gate_name} needs 2 qubit indices, got {len(qubit_indices)}")
            [ctrl, tgt] = qubit_indices
            gate_mat = GATES_2[gate_name]
            full_mat = _tensor_product_2qubit(self.n_qubits, ctrl, tgt, gate_mat)

        # Matrix multiply: new_state = mat @ state
        if _NUMPY:
            state_vec = np.array(self.amplitudes, dtype=complex)
            new_vec = full_mat @ state_vec
            return QuantumState(new_vec.tolist()).normalized()
        else:
            new_amps = _mat_vec_mul(full_mat, self.amplitudes)
            return QuantumState(new_amps).normalized()

    # ── Measurement ─────────────────────────────────────────────────────────

    def measure(self, qubit_index: int = 0, seed: Optional[int] = None) -> tuple["QuantumState", int, float]:
        """Measure qubit `qubit_index`, collapse, and return (new_state, outcome, probability).

        Uses random.Random seeded deterministically from state-vector hash + qubit_index
        when seed is None, so the same state always gives the same outcome.
        """
        probs = self.probabilities()
        # Probability that qubit=0: sum of probabilities for basis states where qubit_index bit = 0
        p0 = 0.0
        for idx, amp in enumerate(self.amplitudes):
            # In computational basis, qubit 0 is the LSB (rightmost) in |q_{n-1} … q_1 q_0⟩
            bit = (idx >> qubit_index) & 1
            if bit == 0:
                p0 += abs(amp) ** 2

        # Deterministic seed: hash of state bytes + qubit_index
        if seed is None:
            seed = _state_seed(self.amplitudes, qubit_index)

        rng = random.Random(seed)
        outcome = 0 if rng.random() < p0 else 1
        prob = p0 if outcome == 0 else 1.0 - p0

        # Collapse: keep only basis states matching the outcome, renormalize
        new_amps = [0.0] * len(self.amplitudes)
        for idx, amp in enumerate(self.amplitudes):
            bit = (idx >> qubit_index) & 1
            if bit == outcome:
                new_amps[idx] = amp

        return QuantumState(new_amps).normalized(), outcome, prob

    # ── Display ───────────────────────────────────────────────────────────────

    def to_ket_string(self, max_len: int = 120) -> str:
        """Return human-readable Dirac string, e.g. '0.707|0⟩ + 0.707|1⟩'."""
        import math

        def fmt(c: complex) -> str:
            if abs(c) < 1e-12:
                return None
            re, im = c.real, c.imag
            if im == 0:
                return f"{re:.3g}"
            if re == 0:
                return f"{im:.3g}j"
            sign = "+" if im >= 0 else "-"
            return f"{re:.3g}{sign}{abs(im):.3g}j"

        parts = []
        for idx, amp in enumerate(self.amplitudes):
            label = "".join(
                str((idx >> qi) & 1) for qi in range(self.n_qubits - 1, -1, -1)
            )
            coeff = fmt(amp)
            if coeff is None:
                continue
            parts.append(f"{coeff}|{label}⟩")

        if not parts:
            return "0"

        text = " + ".join(parts).replace("+ -", "- ")
        if len(text) > max_len:
            text = text[: max_len - 3] + "..."
        return text

    def __repr__(self) -> str:
        return f"QuantumState({self.amplitudes}, n_qubits={self.n_qubits})"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _state_seed(amplitudes: list[complex], qubit_index: int) -> int:
    """Deterministic seed from state vector and qubit index."""
    h = hashlib.sha256()
    for a in amplitudes:
        h.update(str(a).encode())
    h.update(str(qubit_index).encode())
    return int(h.hexdigest(), 16) % (2 ** 30)


def _identity(n: int) -> "list[list[complex]]":
    """Return n×n identity as pure-Python list."""
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def _kron(a: "list[list[complex]]", b: "list[list[complex]]") -> "list[list[complex]]":
    """Kronecker/tensor product of two pure-Python matrices."""
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    result = [
        [0.0] * (cols_a * cols_b) for _ in range(rows_a * rows_b)
    ]
    for i_a in range(rows_a):
        for j_a in range(cols_a):
            for i_b in range(rows_b):
                for j_b in range(cols_b):
                    result[i_a * rows_b + i_b][j_a * cols_b + j_b] = a[i_a][j_a] * b[i_b][j_b]
    return result


def _tensor_product(n_qubits: int, target_qubit: int, gate: "np.ndarray | list") -> "np.ndarray | list":
    """Build full N-qubit gate by tensor-product with identities."""
    dim = 2 ** n_qubits
    if _NUMPY:
        result = np.eye(dim, dtype=complex)
        # Apply gate to target qubit (LSB = qubit 0)
        for i in range(dim):
            # Extract bits for target qubit
            t_bit = (i >> target_qubit) & 1
            # Extract bits for all other qubits (preserved)
            upper_mask = dim - 1 ^ (1 << target_qubit)
            preserved_bits = i & upper_mask
            for j in range(2):
                new_bit = j
                # Construct index for |...t_bit...⟩
                idx_with_t = preserved_bits | (new_bit << target_qubit)
                result[i][idx_with_t] = gate[t_bit][j]
        return result
    else:
        # Pure-python: Kronecker product of I⊗...⊗gate⊗...⊗I
        result = [[0.0] * dim for _ in range(dim)]
        id_mat = _identity(2)
        # Build list of factors (I or gate) in qubit order: qubit 0 is rightmost
        factors = [id_mat] * n_qubits
        factors[target_qubit] = gate
        # Kronecker product in reverse (rightmost first)
        full = factors[n_qubits - 1]
        for f in reversed(factors[: n_qubits - 1]):
            full = _kron(f, full)
        return full


def _tensor_product_2qubit(n_qubits: int, ctrl: int, tgt: int, gate: "np.ndarray | list") -> "np.ndarray | list":
    """Build full N-qubit CNOT gate.

    Standard convention: qubit 0 = most significant (leftmost), qubit 1 = least significant (rightmost).
    CNOT(ctrl=0, tgt=1) means: if qubit 0 is |1⟩ then flip qubit 1.
    This means: if LSB(bit position 0) is 1, flip bit at position 1.
    """
    dim = 2 ** n_qubits
    if _NUMPY:
        result = np.eye(dim, dtype=complex)
        for i in range(dim):
            c_bit = (i >> ctrl) & 1
            t_bit = (i >> tgt) & 1
            if c_bit == 1:
                mask = 1 << tgt
                new_i = i ^ mask
                result[i][i] = 0
                result[i][new_i] = 1
            else:
                result[i][i] = 1
        return result
    else:
        result = [[0.0] * dim for _ in range(dim)]
        for i in range(dim):
            c_bit = (i >> ctrl) & 1
            if c_bit == 1:
                mask = 1 << tgt
                new_i = i ^ mask
                result[i][new_i] = 1
            else:
                result[i][i] = 1
        return result


def _mat_vec_mul(mat: "list[list[complex]]", vec: list[complex]) -> list[complex]:
    """Multiply matrix (list of lists) by vector (list)."""
    result = [0.0] * len(mat)
    for i, row in enumerate(mat):
        s = 0.0 + 0.0j
        for j, val in enumerate(row):
            s += val * vec[j]
        result[i] = s
    return result


# ── Discovery integration ──────────────────────────────────────────────────────

QUANTUM_KEYWORDS: set[str] = {
    "superposition", "interference", "quantum gate", "qubit", "quantum circuit",
    "entanglement", "wavefunction", "photon", "electron orbital", "molecular orbital",
    "spin state", "quantum coherence", "decoherence", "quantum dot",
    "photoexcitation", "photoemission", "excited state", "tunnelling",
    "double slit", "uncertainty principle", "pauli", "hadamard",
}

QUANTUM_DOMAINS: set[str] = {
    "photochemistry", "quantum biology", "materials science",
    "quantum computing", "molecular electronics",
}


def is_quantum_topic(text: str) -> bool:
    """Return True if `text` contains any quantum keyword."""
    t = text.lower()
    return any(kw in t for kw in QUANTUM_KEYWORDS)
