"""
Phase 6.5 – Causality Commands for WESLR

/propose cause <A> <B> [dataset_id]
/refine cause confounder <X> for <A> <B>
/causal graph
/causal intervene <A>=<value>

All causal state is per-session (webchat_fixed key for single-user).
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional

from weslr.modules.causality import (
    causal_confidence,
    confounder_check,
    correlation_test,
    get_dataset,
    is_causal_topic,
    list_datasets,
    suggest_intervention,
    time_order_heuristic,
    CAUSAL_KEYWORDS,
    register_dataset,
)

# ── Session key ────────────────────────────────────────────────────────────────

def _session_key(message: str) -> str:
    """Per-user session key for causal state storage."""
    return "webchat_causality_default"


# ── Per-session causal state ────────────────────────────────────────────────

class _CausalSession:
    """Holds causal graph + user-added knowledge for one session."""

    def __init__(self) -> None:
        # {(cause, effect): confidence_score}
        self.graph: dict[tuple[str, str], float] = {}
        # List of user-added confounders [(A, B, [confounders])]
        self.user_confounders: dict[tuple[str, str], list[str]] = {}
        # Last analysis result for reference
        self.last_analysis: Optional[dict] = None


_USER_SESSIONS: dict[str, _CausalSession] = {}


def _get_session(message: str) -> _CausalSession:
    key = _session_key(message)
    if key not in _USER_SESSIONS:
        _USER_SESSIONS[key] = _CausalSession()
    return _USER_SESSIONS[key]


# ── Commands ──────────────────────────────────────────────────────────────────

CAUSAL_COMMANDS = (
    "/propose cause",
    "/refine cause",
    "/causal graph",
    "/causal intervene",
)


def handle_causal_propose(message: str, lowered: str) -> str:
    """Route to sub-handler: /propose cause OR /causal ... commands."""
    if lowered.startswith("/propose cause") or lowered.startswith("/refine cause"):
        return _handle_propose_cause(message, lowered)
    elif lowered.startswith("/causal"):
        return _handle_causal_sub(message, lowered)
    return _usage_propose()


def _handle_propose_cause(message: str, lowered: str) -> str:
    """Route /propose cause and /refine cause subcommands."""
    if lowered.startswith("/propose cause"):
        body = lowered[len("/propose cause "):].strip()
        return _propose_cause(body, message)
    elif lowered.startswith("/refine cause"):
        body = lowered[len("/refine cause "):].strip()
        return _refine_cause(body, message)
    return _usage_propose()


def _propose_cause(body: str, message: str) -> str:
    """Parse: <A> <B> [dataset_id] [--confounders <C1,C2...>]"""
    # Parse "A B dataset_id" with optional --confounders flag
    # Format: "A B dataset_id" or "A B dataset_id --confounders C1,C2"
    parts = body.split(" --confounders ")
    main_part = parts[0].strip().split()
    confounders_part = parts[1].strip() if len(parts) > 1 else ""

    if len(main_part) < 2:
        return _usage_propose()

    A, B = main_part[0], main_part[1]
    dataset_id = main_part[2] if len(main_part) > 2 else "clinical_dose_response"

    confounder_list = (
        [c.strip() for c in confounders_part.split(",")]
        if confounders_part
        else []
    )

    try:
        data = get_dataset(dataset_id)
    except KeyError:
        available = ", ".join(list_datasets()) or "(none)"
        return f"Dataset {dataset_id!r} not found. Available: {available}"

    # Step 1: correlation test
    if A not in data or B not in data:
        return f"Variables {A!r} or {B!r} not in dataset {dataset_id!r}"

    x = data[A]
    y = data[B]
    corr_result = correlation_test(x, y, test_type="pearson", seed=42)

    # Step 2: temporal heuristic (mock timeline from variable names)
    # Use simple heuristic: earlier alphabetically variable → precedes
    timeline = _build_mock_timeline(A, B, dataset_id)
    temporal_score = time_order_heuristic(timeline, A, B)

    # Step 3: confounder check
    all_vars = list(data.keys())
    potential_confounders = [v for v in all_vars if v != A and v != B]
    conf_result = confounder_check(A, B, potential_confounders, data, seed=42)

    # Step 4: causal confidence
    conf = causal_confidence(corr_result, temporal_score, conf_result)

    # Step 5: intervention suggestion
    session = _get_session(message)
    graph = session.graph.copy()
    # Add current relationship to graph
    graph[(A, B)] = conf["score"]

    interv = suggest_intervention(A, B, graph, data, seed=42)

    # Store for later reference
    session.last_analysis = {
        "A": A, "B": B, "dataset": dataset_id,
        "correlation": corr_result,
        "confounder": conf_result,
        "confidence": conf,
        "intervention": interv,
    }

    # Build response
    sig_marker = "✅" if corr_result["significant"] else "❌"
    conf_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf["level"], "⚪")

    lines = [
        f"## Causal Analysis: {A} → {B}",
        f"",
        f"**Dataset:** {dataset_id} (n={corr_result['n']})",
        f"",
        f"### Correlation",
        f"{sig_marker} Pearson r = {corr_result['statistic']:.3f}  "
        f"(p = {corr_result['p_value']:.4f}), "
        f"effect size = {corr_result['effect_size']:.3f}",
        f"",
        f"### Temporal Precedence",
        f"{'A precedes B ✓' if temporal_score == 1 else 'B precedes A' if temporal_score == -1 else 'No consistent order'}",
        f"",
        f"### Confounding",
        f"Raw correlation: {conf_result['raw_correlation']:.3f}",
    ]

    if conf_result["confounders_found"]:
        lines.append(f"⚠️ Flagged confounders: {', '.join(conf_result['confounders_found'])}")
    else:
        lines.append("✅ No significant confounders detected")

    for c, adj in conf_result["adjustments"].items():
        lines.append(f"  {c}: adjusted r = {adj:.3f}")

    lines.extend([
        f"",
        f"### Causal Confidence {conf_emoji}",
        f"Score: **{conf['score']:.2f}** ({conf['level']})",
        f"  Correlation component:  {conf['breakdown']['correlation']:.2f}",
        f"  Temporal precedence:    {conf['breakdown']['temporal']:.2f}",
        f"  No confounding:        {conf['breakdown']['no_confounding']:.2f}",
        f"  Literature:            {conf['breakdown']['literature']:.2f}",
        f"",
        f"### Intervention Simulation",
        f"{interv['interpretation']}",
        f"  Original mean {B}: {interv['original_mean_B']}",
        f"  After do({A}={interv['intervention_value']}): {interv['intervened_mean_B']}",
        f"  ({'+' if interv['change_pct'] > 0 else ''}{interv['change_pct']:.1f}%)",
        f"",
        f"*Causal assumptions apply. Review before downstream use.*",
    ])

    return "\n".join(lines)


def _refine_cause(body: str, message: str) -> str:
    """Parse: confounder <X> for <A> <B> [--dataset <id>]"""
    if not body.startswith("confounder "):
        return _usage_refine()

    body = body[len("confounder "):].strip()
    # Pattern: "<X> for <A> <B> [--dataset <id>]"
    m = re.match(r"(\S+)\s+for\s+(\S+)\s+(\S+)(?:\s+--dataset\s+(\S+))?", body)
    if not m:
        return _usage_refine()

    X, A, B = m.group(1), m.group(2), m.group(3)
    dataset_id = m.group(4) or getattr(_get_session(message), "last_dataset", "clinical_dose_response")

    session = _get_session(message)
    key = (A, B)
    if key not in session.user_confounders:
        session.user_confounders[key] = []
    if X not in session.user_confounders[key]:
        session.user_confounders[key].append(X)

    # Re-run with added confounder
    try:
        data = get_dataset(dataset_id)
    except KeyError:
        return f"Dataset {dataset_id!r} not found."

    x, y = data[A], data[B]
    corr_result = correlation_test(x, y, test_type="pearson", seed=42)
    timeline = _build_mock_timeline(A, B, dataset_id)
    temporal_score = time_order_heuristic(timeline, A, B)
    all_vars = list(data.keys())
    potential = [v for v in all_vars if v != A and v != B]
    conf_result = confounder_check(A, B, potential, data, seed=42)

    # Add user-specified confounder explicitly
    if X not in conf_result["confounders_found"] and X in data:
        z = data[X]
        ra = _residuals(x, z)
        rb = _residuals(y, z)
        adj_r = correlation_test(ra, rb, test_type="pearson", seed=42)
        conf_result["adjustments"][X] = adj_r["effect_size"]
        if conf_result["raw_correlation"] - adj_r["effect_size"] > 0.3:
            conf_result["confounders_found"].append(X)

    conf = causal_confidence(corr_result, temporal_score, conf_result)

    conf_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf["level"], "⚪")
    lines = [
        f"## Refined: {A} → {B} (confounder: {X})",
        f"New confidence: **{conf['score']:.2f}** ({conf['level']}) {conf_emoji}",
        f"Confounders now: {conf['confounders'] or 'none'}",
    ]
    return "\n".join(lines)


def _handle_causal_sub(message: str, lowered: str) -> str:
    """Route /causal graph and /causal intervene."""
    if lowered.startswith("/causal graph"):
        return _causal_graph(message)
    elif lowered.startswith("/causal intervene"):
        body = lowered[len("/causal intervene "):].strip()
        return _causal_intervene(body, message)
    return _usage_causal()


def _causal_graph(message: str) -> str:
    """Display current causal graph."""
    session = _get_session(message)
    if not session.graph:
        return "No causal graph built yet. Run /propose cause first."

    lines = ["## Causal Graph", ""]
    for (A, B), conf in session.graph.items():
        arrow = f"{A} → {B} (conf={conf:.2f})"
        lines.append(f"  {arrow}")
    return "\n".join(lines)


def _causal_intervene(body: str, message: str) -> str:
    """Parse: <A>=<value> [--dataset <id>] [--target <B>]"""
    # Parse "A=50" or "drug_dose=50 --dataset clinical_dose_response"
    m = re.match(r"(\S+)=(\S+)(?:\s+--dataset\s+(\S+))?", body)
    if not m:
        return _usage_causal()

    A, val_str = m.group(1), m.group(2)
    dataset_id = m.group(3) or "clinical_dose_response"
    try:
        value = float(val_str)
    except ValueError:
        return f"Invalid value {val_str!r}. Must be numeric."

    try:
        data = get_dataset(dataset_id)
    except KeyError:
        return f"Dataset {dataset_id!r} not found."

    # Find B as most correlated to A in the dataset
    best_B, best_r = None, 0.0
    for var in data:
        if var == A:
            continue
        r = correlation_test(data[A], data[var], seed=42)
        if r["effect_size"] > best_r:
            best_r = r["effect_size"]
            best_B = var

    if best_B is None:
        return f"No target variable found for {A!r}"

    session = _get_session(message)
    interv = suggest_intervention(A, best_B, session.graph, data, intervention_value=value, seed=42)

    lines = [
        f"## Intervention: do({A} = {value})",
        f"Target: {best_B}",
        f"",
        f"{interv['interpretation']}",
        f"  Original mean: {interv['original_mean_B']}",
        f"  Intervened mean: {interv['intervened_mean_B']}",
        f"  Change: {interv['change_pct']:+.1f}%",
        f"",
        f"_{interv['assumption']}_",
    ]
    return "\n".join(lines)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _residuals(y, x):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    ssxx = sum((xi - mx) ** 2 for xi in x)
    if ssxx == 0:
        return [yi - my for yi in y]
    beta = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / ssxx
    alpha = my - beta * mx
    return [yi - (beta * xi + alpha) for xi, yi in zip(x, y)]


def _build_mock_timeline(A: str, B: str, dataset_id: str) -> list[tuple[str, float]]:
    """Build a simple timeline where variables appear in dataset order."""
    order = {
        "clinical_dose_response": ["drug_dose", "response", "age"],
        "confounded_demo": ["C", "A", "B"],
        "temporal_demo": ["campaign_spend", "awareness", "sales"],
    }
    var_order = order.get(dataset_id, list(get_dataset(dataset_id).keys()))
    return [(v, float(i)) for i, v in enumerate(var_order)]


# ── Usages ───────────────────────────────────────────────────────────────────

def _usage_propose() -> str:
    return (
        "Usage:\n"
        "  /propose cause <A> <B> [dataset_id]\n"
        "  /propose cause drug_dose response clinical_dose_response\n"
        "  /propose cause A B --confounders age,gender\n"
        "\nAvailable datasets: " + ", ".join(list_datasets())
    )


def _usage_refine() -> str:
    return (
        "Usage:\n"
        "  /refine cause confounder <X> for <A> <B> [--dataset <id>]\n"
        "  /refine cause confounder age for drug_dose response\n"
    )


def _usage_causal() -> str:
    return (
        "Usage:\n"
        "  /causal graph          — Show current causal graph\n"
        "  /causal intervene A=<value> [--dataset <id>]\n"
        "  /causal intervene drug_dose=50 --dataset clinical_dose_response\n"
    )


def is_causal_command(message: str) -> bool:
    """Return True if message looks like a causal command."""
    m = message.lower().strip()
    return m.startswith("/propose cause") or m.startswith("/refine cause") or m.startswith("/causal")
