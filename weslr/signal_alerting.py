"""
WESLR Signal Alerting V1 — Non-invasive operator surface

Read-only signal alert classification.
NO writes. NO proposals. NO governance calls. NO LLM. NO auto-actions.

classify_signal_alert(signal, mode) -> SignalAlertResult
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SignalAlertResult:
    """Immutable alert classification result."""
    alert: bool
    severity: str          # "none" | "low" | "medium" | "high"
    reason: str
    signal_type: str
    topic: Optional[str]
    confidence: float


# ---------------------------------------------------------------------------
# Threshold constants (V1)
# ---------------------------------------------------------------------------
_S1_ALERT_FREQ = 10
_S1_ALERT_SESSIONS = 3
_S2_ALERT_USAGE = 5
_S2_ALERT_SESSIONS = 2
_S4_ALERT_TRIGGERS = 15
_S4_ALERT_SESSIONS = 3
_S5_ALERT_COUNT = 5
_S5_ALERT_SESSIONS = 2

# Severity multipliers
_HIGH_MULTIPLIER = 2.0
_MED_MULTIPLIER = 1.0


def classify_signal_alert(signal: dict, mode: str = "private_dev") -> SignalAlertResult:
    """
    Classify whether a signal warrants operator attention.

    Parameters
    ----------
    signal : dict
        Keys must include:
            signal_type (str): "S1_unknown_query" | "S2_evidence_usage"
                              | "S4_frequent_fallback" | "S5_improvement_query"
            frequency_count (int): for S1
            session_diversity (int): for S1
            usage_count (int): for S2
            unique_sessions (int): for S2
            trigger_count (int): for S4
            distinct_sessions (int): for S4
            count (int): for S5
            sessions (int): for S5
            topic (str, optional): topic identifier
    mode : str
        "public_demo_readonly" → alert always False
        anything else → evaluate normally

    Returns
    -------
    SignalAlertResult
        Immutable. No side effects.
    """
    # --- mode suppression ---
    if mode == "public_demo_readonly":
        return SignalAlertResult(
            alert=False,
            severity="none",
            reason="public_demo_readonly mode — alerts suppressed",
            signal_type=signal.get("signal_type", "unknown"),
            topic=signal.get("topic"),
            confidence=0.0
        )

    signal_type: str = signal.get("signal_type", "")
    topic: Optional[str] = signal.get("topic")

    # --- route by signal type ---
    if signal_type == "S1_unknown_query":
        return _classify_s1(signal, topic)
    elif signal_type == "S2_evidence_usage":
        return _classify_s2(signal, topic)
    elif signal_type == "S4_frequent_fallback":
        return _classify_s4(signal, topic)
    elif signal_type == "S5_improvement_query":
        return _classify_s5(signal, topic)
    else:
        return SignalAlertResult(
            alert=False,
            severity="none",
            reason=f"Unknown signal_type [{signal_type}] — no alert",
            signal_type=signal_type,
            topic=topic,
            confidence=0.0
        )


def _classify_s1(signal: dict, topic: Optional[str]) -> SignalAlertResult:
    freq = _int(signal.get("frequency_count", 0))
    sess_div = _int(signal.get("session_diversity", 0))

    threshold_met = freq >= _S1_ALERT_FREQ and sess_div >= _S1_ALERT_SESSIONS
    ratio = freq / _S1_ALERT_FREQ if _S1_ALERT_FREQ > 0 else 0.0

    alert, severity, confidence, reason = _eval(
        threshold_met, ratio, freq, _S1_ALERT_FREQ,
        f"S1 unknown query: freq={freq}(>={_S1_ALERT_FREQ}), "
        f"session_diversity={sess_div}(>={_S1_ALERT_SESSIONS})",
        topic
    )
    return SignalAlertResult(alert=alert, severity=severity, reason=reason,
                             signal_type="S1_unknown_query", topic=topic,
                             confidence=round(confidence, 4))


def _classify_s2(signal: dict, topic: Optional[str]) -> SignalAlertResult:
    usage = _int(signal.get("usage_count", 0))
    unique = _int(signal.get("unique_sessions", 0))

    threshold_met = usage >= _S2_ALERT_USAGE and unique >= _S2_ALERT_SESSIONS
    ratio = usage / _S2_ALERT_USAGE if _S2_ALERT_USAGE > 0 else 0.0

    alert, severity, confidence, reason = _eval(
        threshold_met, ratio, usage, _S2_ALERT_USAGE,
        f"S2 evidence usage: usage={usage}(>={_S2_ALERT_USAGE}), "
        f"unique_sessions={unique}(>={_S2_ALERT_SESSIONS})",
        topic
    )
    return SignalAlertResult(alert=alert, severity=severity, reason=reason,
                             signal_type="S2_evidence_usage", topic=topic,
                             confidence=round(confidence, 4))


def _classify_s4(signal: dict, topic: Optional[str]) -> SignalAlertResult:
    triggers = _int(signal.get("trigger_count", 0))
    distinct = _int(signal.get("distinct_sessions", 0))

    threshold_met = triggers >= _S4_ALERT_TRIGGERS and distinct >= _S4_ALERT_SESSIONS
    ratio = triggers / _S4_ALERT_TRIGGERS if _S4_ALERT_TRIGGERS > 0 else 0.0

    alert, severity, confidence, reason = _eval(
        threshold_met, ratio, triggers, _S4_ALERT_TRIGGERS,
        f"S4 frequent fallback: triggers={triggers}(>={_S4_ALERT_TRIGGERS}), "
        f"distinct_sessions={distinct}(>={_S4_ALERT_SESSIONS})",
        topic
    )
    return SignalAlertResult(alert=alert, severity=severity, reason=reason,
                             signal_type="S4_frequent_fallback", topic=topic,
                             confidence=round(confidence, 4))


def _classify_s5(signal: dict, topic: Optional[str]) -> SignalAlertResult:
    count = _int(signal.get("count", 0))
    sessions = _int(signal.get("sessions", 0))

    threshold_met = count >= _S5_ALERT_COUNT and sessions >= _S5_ALERT_SESSIONS
    ratio = count / _S5_ALERT_COUNT if _S5_ALERT_COUNT > 0 else 0.0

    alert, severity, confidence, reason = _eval(
        threshold_met, ratio, count, _S5_ALERT_COUNT,
        f"S5 improvement query: count={count}(>={_S5_ALERT_COUNT}), "
        f"sessions={sessions}(>={_S5_ALERT_SESSIONS})",
        topic
    )
    return SignalAlertResult(alert=alert, severity=severity, reason=reason,
                             signal_type="S5_improvement_query", topic=topic,
                             confidence=round(confidence, 4))


def _int(val) -> int:
    """Safe int coercion, None → 0."""
    if val is None:
        return 0
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _eval(
    threshold_met: bool,
    ratio: float,
    count: int,
    threshold: int,
    base_reason: str,
    topic: Optional[str]
):
    """
    Shared severity + confidence logic.

    Returns (alert, severity, confidence, reason).
    """
    if not threshold_met:
        return False, "none", 0.0, f"No alert: {base_reason}"
    if ratio >= _HIGH_MULTIPLIER:
        severity = "high"
        confidence = min(1.0, 0.5 + ratio * 0.25)
    elif ratio >= _MED_MULTIPLIER:
        severity = "medium"
        confidence = min(1.0, 0.3 + ratio * 0.25)
    else:
        severity = "low"
        confidence = min(1.0, 0.2 + ratio * 0.20)

    reason = f"ALERT [{severity.upper()}]: {base_reason}"
    if topic:
        reason += f" | topic={topic}"

    return True, severity, confidence, reason
