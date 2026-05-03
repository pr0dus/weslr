"""Command handler for /quantum — quantum state, gates, and measurement."""

from __future__ import annotations

import re
from typing import Optional

from weslr.modules.quantum_logic import (
    QuantumState,
    GATE_NAMES,
    is_quantum_topic,
)

# Per-user quantum state (keyed by user_id or session_id).
# In a multi-tenant system this would be per-user session storage.
_USER_STATES: dict[str, QuantumState] = {}


def handle_quantum(message: str, lowered: str) -> str:
    """Route to sub-handler based on first token after /quantum."""
    body = lowered.strip()
    tokens = body.split()
    subcmd = tokens[1] if len(tokens) > 1 else "state"

    if subcmd in ("state", "reset"):
        return _handle_state(message, body, subcmd)
    elif subcmd == "apply":
        return _handle_apply(message, body)
    elif subcmd == "measure":
        return _handle_measure(message, body)
    else:
        return _usage()


def _usage() -> str:
    gates = ", ".join(GATE_NAMES)
    return (
        "Usage:\n"
        "  /quantum state |0>            — Set initial state (|0>, |1>, |+>, |->)\n"
        "  /quantum state a|0> + b|1>     — Set superposition (complex a,b)\n"
        "  /quantum apply H 0             — Apply Hadamard to qubit 0\n"
        "  /quantum apply CNOT 0,1        — Apply CNOT: ctrl 0, target 1\n"
        "  /quantum measure [qubit=0]     — Measure qubit (collapses state)\n"
        "  /quantum reset                — Clear current quantum state\n"
        f"\nAvailable gates: {gates}"
    )


# ── State ────────────────────────────────────────────────────────────────────

def _handle_state(message: str, body: str, subcmd: str) -> str:
    if subcmd == "reset":
        key = _session_key(message)
        _USER_STATES.pop(key, None)
        return "Quantum state cleared."

    # Parse state expression: "/quantum state |0>" → "|0>"
    # body is the text after "/" (already lowercased by dispatcher)
    # e.g. body = "quantum state |0>" or "/quantum state |0>"
    raw = body.split(" ", 2)[-1].strip() if " " in body else ""

    if not raw:
        return _usage()

    try:
        raw_ket = raw.strip()
        if raw_ket.startswith(("|", "+", "-")):
            state = QuantumState.basis(raw_ket)
        else:
            state = QuantumState.parse(raw)
    except Exception as e:
        return f"Cannot parse state {raw!r}: {e}"

    state = state.normalized()
    key = _session_key(message)
    _USER_STATES[key] = state

    probs = state.probabilities()
    lines = [
        f"State set: {state.to_ket_string()}",
        f"Qubits: {state.n_qubits}",
        f"Dimensions: {2**state.n_qubits}",
        f"Probabilities: {', '.join(f'{p:.3f}' for p in probs)}",
    ]
    return "\n".join(lines)


# ── Apply ─────────────────────────────────────────────────────────────────────

def _handle_apply(message: str, body: str) -> str:
    key = _session_key(message)
    if key not in _USER_STATES:
        return "No quantum state set. Use '/quantum state |0>' first."

    # Extract gate name and qubit indices
    # Pattern: /quantum apply H 0  or  /quantum apply CNOT 0,1
    m = re.search(r"apply\s+([A-Za-z]+)\s+([\d,]+)", body)
    if not m:
        return f"Cannot parse /quantum apply: {body!r}\nUsage: /quantum apply <gate> <qubit>[,<qubit>]"

    gate_name = m.group(1).upper()
    indices_str = m.group(2)
    try:
        qubit_indices = [int(x) for x in indices_str.split(",")]
    except ValueError:
        return f"Invalid qubit index: {indices_str!r}"

    if gate_name not in GATE_NAMES:
        return f"Unknown gate {gate_name!r}. Available: {', '.join(GATE_NAMES)}"

    try:
        state = _USER_STATES[key].apply_gate(gate_name, qubit_indices)
    except Exception as e:
        return f"Gate application failed: {e}"

    _USER_STATES[key] = state

    return (
        f"After {gate_name} on qubit(s) {qubit_indices}:\n"
        f"  State: {state.to_ket_string()}\n"
        f"  Probs: {', '.join(f'{p:.3f}' for p in state.probabilities())}"
    )


# ── Measure ──────────────────────────────────────────────────────────────────

def _handle_measure(message: str, body: str) -> str:
    key = _session_key(message)
    if key not in _USER_STATES:
        return "No quantum state set. Use '/quantum state |0>' first."

    # Parse optional qubit index
    qubit = 0
    m = re.search(r"measure\s+(\d+)", body, re.IGNORECASE)
    if m:
        qubit = int(m.group(1))

    try:
        new_state, outcome, prob = _USER_STATES[key].measure(qubit_index=qubit)
    except Exception as e:
        return f"Measurement failed: {e}"

    _USER_STATES[key] = new_state

    basis = "".join(str((i >> qubit) & 1) for i in range(len(new_state.amplitudes)))
    lines = [
        f"Measurement on qubit {qubit}:",
        f"  Outcome: |{outcome}⟩",
        f"  Probability: {prob:.3f}",
        f"  Collapsed state: {new_state.to_ket_string()}",
        f"  Remaining probs: {', '.join(f'{p:.3f}' for p in new_state.probabilities())}",
    ]
    return "\n".join(lines)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _session_key(message: str) -> str:
    """Derive a stable per-user key from the message.

    For single-user webchat, use a fixed key so all quantum commands
    share the same session state. In multi-tenant contexts, derive
    from user/session ID instead.
    """
    # Fixed key for single-user webchat context
    return "webchat_quantum_default"
