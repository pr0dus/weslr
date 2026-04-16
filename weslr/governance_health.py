"""governance_health.py — WESLR unified state read surface

One coherent read-only aggregator for WESLR's operational state.
Composes from all existing subsystems — no writes, no side effects.

Composition sources:
- get_self_summary()           → identity, health, continuity, institutional, strengths, weaknesses
- get_institutional_health_summary()  → 7-category governance health
- get_pending_reflections()    → active drift concerns
- get_reflection_status_summary() → signal counts by status
- trust posture                → bootstrap verification state

Rules:
- read-only only; no writes, no side effects
- graceful degradation: each source independently skipped on failure
- called by operator or WESLR for self-assessment
"""

from __future__ import annotations

import time as _time


def get_weslr_state_summary() -> dict:
    """Return one coherent read-only summary of WESLR's operational state.

    This is the canonical operator- and WESLR-facing state aggregator.
    All sources are read-only; calling this never modifies any state.

    Returns:
        dict with keys:
        - generated_at: Unix timestamp
        - identity: dict (name, version, description)
        - trust_posture: dict (bootstrap verified count, pending, root trust)
        - health_posture: dict (subsystem counts, risk counts, governance quality)
        - continuity_posture: dict (continuity state or degraded message)
        - institutional_posture: dict (institution/role/governor counts)
        - drift_posture: dict (active reflections, cooldown, total signals)
        - active_concerns: list (pending drift reflection concerns)
        - strengths: list (working reliably)
        - unresolved_weaknesses: list (known degraded areas)
    """
    now = _time.time()

    # Core identity
    identity = _get_identity()

    # Trust posture
    trust = _get_trust_posture()

    # Composed self-model
    try:
        self_summary = _get_self_summary_composed()
    except Exception:
        self_summary = {"status": "degraded", "error": "self_model unavailable"}

    # Institutional health
    try:
        health = _get_institutional_health_composed()
    except Exception:
        health = {"status": "degraded", "error": "institution module unavailable"}

    # Drift / reflection posture
    drift = _get_drift_posture()

    # Active concerns
    try:
        active_concerns = _get_active_concerns()
    except Exception:
        active_concerns = []

    # Strengths
    strengths = _get_strengths(self_summary, health, trust, drift)

    # Unresolved weaknesses
    weaknesses = _get_unresolved_weaknesses(self_summary, health, drift)

    return {
        "generated_at": now,
        "identity": identity,
        "trust_posture": trust,
        "health_posture": health,
        "continuity_posture": self_summary.get("continuity_posture", {"status": "degraded"}),
        "institutional_posture": self_summary.get("institutional_posture", {"status": "degraded"}),
        "drift_posture": drift,
        "active_concerns": active_concerns,
        "strengths": strengths,
        "unresolved_weaknesses": weaknesses,
    }


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

def _get_identity() -> dict:
    return {
        "name": "WESLR",
        "version": "v1",
        "description": "Entity intelligence platform with governed self-assessment and institutional continuity",
    }


# ---------------------------------------------------------------------------
# Trust posture
# ---------------------------------------------------------------------------

def _get_trust_posture() -> dict:
    try:
        from weslr.bootstrap import (
            is_user_bootstrap_verified,
            _BOOTSTRAP_RECORDS,
            _BOOTSTRAP_BY_TIMELINE,
        )
        return {
            "bootstrap_verified_timelines": len(_BOOTSTRAP_BY_TIMELINE),
            "pending_bootstraps": len([r for r in _BOOTSTRAP_RECORDS.values() if r.get("status") == "PENDING"]),
            "root_trust": "bootstrap_completed",
            "status": "operational" if _BOOTSTRAP_BY_TIMELINE else "initializing",
        }
    except Exception:
        return {"status": "unknown", "error": "bootstrap module unavailable"}


# ---------------------------------------------------------------------------
# Self-model composition
# ---------------------------------------------------------------------------

def _get_self_summary_composed() -> dict:
    """Delegate to get_self_summary() from institution module."""
    from weslr.institution import get_self_summary
    return get_self_summary()


# ---------------------------------------------------------------------------
# Institutional health composition
# ---------------------------------------------------------------------------

def _get_institutional_health_composed() -> dict:
    """Delegate to get_institutional_health_summary() from institution module."""
    from weslr.institution import get_institutional_health_summary
    health = get_institutional_health_summary()

    sub = health.get("subsystem_health", {})
    gov = health.get("governance_quality", {})
    obs = health.get("observability_freshness", {})

    return {
        "subsystem_count": sub.get("subsystem_count", 0),
        "critical_risks": sub.get("critical_risk_count", 0),
        "high_risks": sub.get("high_risk_count", 0),
        "governance_decisions_approved": gov.get("decisions_by_type", {}).get("approved", 0),
        "governance_decisions_rejected": gov.get("decisions_by_type", {}).get("rejected", 0),
        "pending_proposals": gov.get("pending_proposal_count", 0),
        "capsule_operational": bool(obs.get("capsule_status", {})),
        "routing_count": len(obs.get("routing_summary", {}).get("routings", {})),
        "bootstrap_readiness": health.get("bootstrap_readiness", {}),
        "audit_trace_health": health.get("audit_trace_health", {}),
    }


# ---------------------------------------------------------------------------
# Drift / reflection posture
# ---------------------------------------------------------------------------

def _get_drift_posture() -> dict:
    try:
        from weslr.institution import (
            get_reflection_status_summary,
            _DRIFT_SIGNALS,
            _DRIFT_WINDOW_SECS,
            _MAX_SIGNALS,
        )
        now = _time.time()
        window_start = now - _DRIFT_WINDOW_SECS

        # Count signals in rolling window
        active_signals = [s for s in _DRIFT_SIGNALS if (now - s.observed_at) < _DRIFT_WINDOW_SECS]
        by_type: dict[str, int] = {}
        for s in active_signals:
            by_type[s.signal_type] = by_type.get(s.signal_type, 0) + 1

        summary = get_reflection_status_summary()

        return {
            "total_signals_in_window": len(active_signals),
            "signals_by_type": by_type,
            "window_seconds": _DRIFT_WINDOW_SECS,
            "max_signals": _MAX_SIGNALS,
            "reflection_summary": summary,
        }
    except Exception:
        return {"status": "degraded", "error": "drift module unavailable"}


# ---------------------------------------------------------------------------
# Active concerns
# ---------------------------------------------------------------------------

def _get_active_concerns() -> list[dict]:
    try:
        from weslr.institution import get_pending_reflections
        pending = get_pending_reflections()
        return [
            {
                "concern": r.get("concern", ""),
                "confidence": r.get("confidence", ""),
                "description": r.get("description", ""),
            }
            for r in pending
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Strengths
# ---------------------------------------------------------------------------

def _get_strengths(self_summary: dict, health: dict, trust: dict, drift: dict) -> list[str]:
    strengths = []
    try:
        if not health.get("critical_risks") and not health.get("high_risks"):
            strengths.append("no critical or high-severity architectural risks")
        if health.get("capsule_operational"):
            strengths.append("capsule observability operational")
        if trust.get("bootstrap_verified_timelines", 0) > 0:
            strengths.append("bootstrap trust root established")
        inst = self_summary.get("institutional_posture", {})
        if inst.get("institution_count", 0) > 0:
            strengths.append("institutional governance active")
        if drift.get("total_signals_in_window", 0) > 0:
            strengths.append("reflective drift monitoring active")
    except Exception:
        pass
    if not strengths:
        strengths.append("core systems nominal")
    return strengths


# ---------------------------------------------------------------------------
# Unresolved weaknesses
# ---------------------------------------------------------------------------

def _get_unresolved_weaknesses(self_summary: dict, health: dict, drift: dict) -> list[str]:
    weaknesses = []
    try:
        if health.get("critical_risks", 0) > 0:
            weaknesses.append(f"{health['critical_risks']} critical risk(s) require attention")
        if health.get("high_risks", 0) > 0:
            weaknesses.append(f"{health['high_risks']} high-severity risk(s) require attention")
        inst = self_summary.get("institutional_posture", {})
        if inst.get("vacant_roles", 0) > 0:
            weaknesses.append(f"{inst['vacant_roles']} role(s) are currently vacant")
        trust = _get_trust_posture()
        if trust.get("pending_bootstraps", 0) > 0:
            weaknesses.append(f"{trust['pending_bootstraps']} bootstrap(s) pending completion")
        refl = drift.get("reflection_summary", {})
        if refl.get("cooldown", 0) > 0:
            weaknesses.append("one or more drift concerns are in cooldown — monitor for re-surfacing")
        if drift.get("signals_by_type", {}).get("governance_override", 0) >= 5:
            weaknesses.append("elevated governance override frequency — review drift loop signals")
    except Exception:
        pass
    return weaknesses
