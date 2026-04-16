"""Drift Emitter Wiring v1 — fail-open signal sources for the Reflective Drift Loop.

This module is the ONLY place drift signal emission calls live.
All three sources are wired here with mandatory fail-open wrapping.

Rule: emitter failure must never affect runtime flow.
"""

from __future__ import annotations

import traceback
import time as _time

# ---------------------------------------------------------------------------
# Internal drift loop API — imported lazily to avoid circular imports
# ---------------------------------------------------------------------------

def _record_drift(signal_type: str, value: float, context: dict | None = None, severity: str = "medium") -> None:
    """Record a drift signal with fail-open safety.

    This is the single internal gateway for all drift signal emission.
    Fail-open: any exception is swallowed and a trace is printed to stderr.
    """
    try:
        from weslr.institution import record_drift_signal
        record_drift_signal(signal_type, value, context, severity)
    except Exception:
        # Fail-open: never let emitter crash the runtime path
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Signal source 1 — Chat latency
# ---------------------------------------------------------------------------

def emit_latency_signal(duration_seconds: float, ok: bool) -> None:
    """Emit a latency drift signal from real chat path timing data.

    Called from the chat UI handler after each chat round-trip.
    Fails open silently.
    """
    _record_drift(
        signal_type="latency",
        value=duration_seconds,
        context={"ok": ok},
        severity="high" if duration_seconds > 10.0 else ("medium" if duration_seconds > 5.0 else "low"),
    )


# ---------------------------------------------------------------------------
# Signal source 2 — Bootstrap state transitions
# ---------------------------------------------------------------------------

def emit_bootstrap_signal(from_status: str, to_status: str, timeline_id: str) -> None:
    """Emit a bootstrap state-transition drift signal.

    Called when bootstrap moves through a meaningful state change:
    pending → completed, completed → expired, completed → revoked, etc.
    Fails open silently.
    """
    _record_drift(
        signal_type="lifecycle_stale",
        value=1.0,
        context={
            "bootstrap_transition": f"{from_status}→{to_status}",
            "timeline_id": timeline_id,
            "transition_at": _time.time(),
        },
        severity="high" if to_status in ("expired", "revoked") else "medium",
    )


# ---------------------------------------------------------------------------
# Signal source 3 — Governance override events
# ---------------------------------------------------------------------------

def emit_override_signal(override_type: str, proposal_id: str | None = None, human: str = "operator") -> None:
    """Emit a governance-override drift signal.

    Called when the operator overrides, rejects, or counteracts a WESLR
    recommendation. This is the "operator knows better" signal.
    Fails open silently.
    """
    _record_drift(
        signal_type="governance_override",
        value=1.0,
        context={
            "override_type": override_type,
            "proposal_id": proposal_id,
            "human": human,
            "at": _time.time(),
        },
        severity="medium",
    )
