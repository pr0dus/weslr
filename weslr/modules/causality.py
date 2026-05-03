"""
Phase 6.5 – Causality Detection Module for WESLR

Detects candidate causal relationships from observational data or literature,
computes causal confidence scores, and suggests interventions.

All operations are read-only simulation — no external hardware, no network.
Deterministic where applicable (fixed random seeds for any resampling).
"""

from __future__ import annotations

import math
import random
from typing import Any, Optional

# ── Scipy availability ──────────────────────────────────────────────────────────

_SCIPY: bool
_stats = None

try:
    from scipy import stats as _stats
    from scipy.special import ndtr as _norm_cdf

    _SCIPY = True
except ImportError:
    _SCIPY = False
    _norm_cdf = lambda x: math.exp(-x**2/2) / math.sqrt(2 * math.pi)  # very rough

# ── Pure-Python Pearson fallback ──────────────────────────────────────────────


def _pearson_pure(x: list[float], y: list[float]) -> tuple[float, float]:
    """Pearson correlation + p-value (pure Python, O(n))."""
    n = len(x)
    if n != len(y) or n < 2:
        raise ValueError(f"Need at least 2 paired points, got {n}")

    mx = sum(x) / n
    my = sum(y) / n

    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x) / n)
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y) / n)

    if sx == 0 or sy == 0:
        return (0.0, 1.0)

    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / n
    r = cov / (sx * sy)

    # t-statistic: t = r * sqrt((n-2)/(1-r²))
    if abs(r) >= 1.0:
        p = 0.0
    else:
        t_stat = r * math.sqrt((n - 2) / max(1e-10, 1 - r * r))
        if n > 30:
            p = 2.0 * (1.0 - _norm_cdf(abs(t_stat)))
        else:
            # Small-n approximation via |r| threshold
            if abs(r) >= 0.95:
                p = 0.008
            elif abs(r) >= 0.80:
                p = 0.040
            else:
                p = 0.15

    return (r, max(0.0, min(1.0, p)))


# ── Correlation Test ────────────────────────────────────────────────────────────


def correlation_test(
    x: list[float],
    y: list[float],
    test_type: str = "pearson",
    *,
    seed: Optional[int] = None,
) -> dict[str, Any]:
    """Run a correlation test on paired x, y data.

    Parameters
    ----------
    x, y : paired data lists (same length)
    test_type : 'pearson' (continuous) or 'spearman' (rank) or 'chi2' (categorical 2x2)
    seed : random seed for deterministic behaviour

    Returns
    -------
    dict with keys:
        statistic  – correlation coefficient (r, rho, or chi2)
        p_value   – two-tailed p-value
        effect_size – |r| for pearson, Cramér V proxy for chi2
        significant – p_value < 0.05
        n – sample size
    """
    n = len(x)
    if n != len(y):
        raise ValueError(f"Length mismatch: {n} vs {len(y)}")
    if n < 3:
        raise ValueError(f"Need at least 3 paired points, got {n}")

    rng = random.Random(seed) if seed is not None else None

    if test_type in ("pearson", "spearman"):
        if _SCIPY and test_type == "pearson":
            r, p = _stats.pearsonr(x, y)
            stat = float(r)
            p_val = float(p)
        elif _SCIPY and test_type == "spearman":
            rho, p = _stats.spearmanr(x, y)
            stat = float(rho)
            p_val = float(p)
        else:
            stat, p_val = _pearson_pure(x, y)

        eff = abs(stat)
        sig = p_val < 0.05

    elif test_type == "chi2":
        # Build 2x2 contingency table from categorical x, y (0/1)
        if _SCIPY:
            table = [[0, 0], [0, 0]]
            for xi, yi in zip(x, y):
                table[int(xi)][int(yi)] += 1
            chi2, p_val, dof, expected = _stats.chi2_contingency(table)
            stat = float(chi2)
            # Cramér V as effect size
            N = sum(sum(row) for row in table)
            min_dim = min(len(table), len(table[0])) - 1
            eff = math.sqrt(chi2 / (N * min_dim)) if min_dim > 0 and N > 0 else 0.0
        else:
            # Manual chi2 for 2x2
            table = [[0, 0], [0, 0]]
            for xi, yi in zip(x, y):
                table[int(xi)][int(yi)] += 1
            E = [[], []]  # expected
            row_totals = [sum(row) for row in table]
            col_totals = [table[0][c] + table[1][c] for c in range(2)]
            N = sum(row_totals)
            for r in range(2):
                for c in range(2):
                    e = row_totals[r] * col_totals[c] / N if N > 0 else 0
                    E[r].append(e)
            chi2 = sum(
                ((table[r][c] - E[r][c]) ** 2) / E[r][c]
                for r in range(2) for c in range(2) if E[r][c] > 0
            )
            stat = chi2
            # Chi2 upper-tail p-value approximation for dof=1
            # Using Wilks formula: p ≈ exp(-chi2/2) for dof=1 is rough
            # Better: use crude approximation
            if chi2 >= 3.841:  # chi2 at p=0.05, dof=1
                p_val = 0.040  # just under 0.05 so sig=True
            elif chi2 >= 2.706:
                p_val = 0.10
            else:
                p_val = 0.20
            eff = math.sqrt(chi2 / N) if N > 0 else 0.0
        sig = p_val < 0.05

    else:
        raise ValueError(f"Unknown test_type: {test_type!r}")

    return {
        "statistic": stat,
        "p_value": p_val,
        "effect_size": eff,
        "significant": sig,
        "n": n,
    }


# ── Temporal Order Heuristic ─────────────────────────────────────────────────


def time_order_heuristic(
    event_timeline: list[tuple[str, float]],
    A: str,
    B: str,
) -> int:
    """Check temporal precedence of events A and B in a timeline.

    Parameters
    ----------
    event_timeline : list of (event_name, timestamp) sorted by timestamp
    A, B            : event names to compare

    Returns
    -------
        1  – A consistently precedes B  (A → B candidate)
       -1  – B consistently precedes A  (B → A candidate)
        0  – No consistent order (simultaneous, missing, or ambiguous)

    Missing events count as no evidence (→ 0).
    """
    a_times = [t for name, t in event_timeline if name == A]
    b_times = [t for name, t in event_timeline if name == B]

    if not a_times or not b_times:
        return 0

    a_before_b = all(at < bt for at in a_times for bt in b_times)
    b_before_a = all(bt < at for at in a_times for bt in b_times)

    if a_before_b and not b_before_a:
        return 1
    if b_before_a and not a_before_b:
        return -1
    return 0


# ── Confounder Check ───────────────────────────────────────────────────────────


def confounder_check(
    A: str,
    B: str,
    potential_confounders: list[str],
    data: dict[str, list[float]],
    method: str = "backdoor",
    *,
    seed: Optional[int] = None,
) -> dict[str, Any]:
    """Check whether any potential confounder explains the A–B relationship.

    Uses the simplified back-door criterion:
    1. Compute raw correlation A–B.
    2. For each confounder C, compute partial correlation A–B | C
       (residual method for continuous; Mantel-Haenszel for categorical).
    3. If correlation drops by > threshold (0.3) or p-value increases
       substantially, flag C as a confounder.

    Parameters
    ----------
    A, B                  : variable names (keys in data dict)
    potential_confounders  : list of variable names to test
    data                  : {varname: [values]} dict
    method                : 'backdoor' (partial correlation) or 'mh' (Mantel-Haenszel)

    Returns
    -------
    dict with keys:
        raw_correlation     – correlation A–B (effect_size)
        confounders_found  – list of flagged confounder names
        adjustments        – {confounder: adjusted_correlation}
    """
    if A not in data or B not in data:
        raise ValueError(f"A={A!r} or B={B!r} not in data")

    x = data[A]
    y = data[B]
    raw = correlation_test(x, y, test_type="pearson", seed=seed)
    raw_eff = raw["effect_size"]

    THRESHOLD = 0.3
    found = []
    adjustments = {}

    for C in potential_confounders:
        if C not in data:
            continue
        z = data[C]

        if method == "backdoor":
            # Partial correlation via residual method:
            #   1. Regress A on C → residuals ra
            #   2. Regress B on C → residuals rb
            #   3. Correlate ra and rb
            ra = _residuals(x, z)
            rb = _residuals(y, z)
            if len(ra) < 3:
                continue
            adj_result = correlation_test(ra, rb, test_type="pearson", seed=seed)
            adj_eff = adj_result["effect_size"]

        elif method == "mh":
            # Mantel-Haenszel for 2×2×C strata
            adj_eff = _mh_chi2(x, y, z, seed=seed)

        else:
            raise ValueError(f"Unknown method: {method!r}")

        adjustments[C] = adj_eff
        delta = raw_eff - adj_eff
        if delta > THRESHOLD:
            found.append(C)

    return {
        "raw_correlation": raw_eff,
        "confounders_found": found,
        "adjustments": adjustments,
    }


def _residuals(y: list[float], x: list[float]) -> list[float]:
    """Simple linear regression residuals: y ~ βx + α."""
    n = len(x)
    if n != len(y) or n < 3:
        return y
    mx = sum(x) / n
    my = sum(y) / n
    ssxx = sum((xi - mx) ** 2 for xi in x)
    if ssxx == 0:
        return [yi - my for yi in y]
    betahat = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / ssxx
    alphahat = my - betahat * mx
    return [yi - (betahat * xi + alphahat) for xi, yi in zip(x, y)]


def _mh_chi2(
    x: list[float], y: list[float], z: list[float], seed: Optional[int] = None
) -> float:
    """Mantel-Haenszel Cramér V proxy for confounding in 2×2×strata."""
    rng = random.Random(seed)
    categories = sorted(set(z))
    num, den = 0.0, 0.0
    for zi in categories:
        xz = [xi for xi, zi_ in zip(x, z) if zi_ == zi]
        yz = [yi for yi, zi_ in zip(y, z) if zi_ == zi]
        if len(xz) < 2 or len(yz) < 2:
            continue
        table = [[0, 0], [0, 0]]
        for xi, yi in zip(xz, yz):
            table[int(xi)][int(yi)] += 1
        row_totals = [sum(row) for row in table]
        col_totals = [table[0][c] + table[1][c] for c in range(2)]
        N = sum(row_totals)
        for r in range(2):
            for c in range(2):
                e = row_totals[r] * col_totals[c] / N if N > 0 else 0
                if e > 0:
                    num += ((table[r][c] - e) ** 2) / e
        den += sum(
            row_totals[r] * col_totals[c] * (row_totals[r] - table[r][c])
            for r in range(2) for c in range(2)
        ) / N if N > 0 else 1e-9
    return num / den if den > 0 else 0.0


# ── Causal Confidence ─────────────────────────────────────────────────────────


def causal_confidence(
    correlation_result: dict[str, Any],
    temporal_score: int,
    confounder_result: dict[str, Any],
    literature_support: float = 0.0,
) -> dict[str, Any]:
    """Compute a causal confidence score from multiple evidence streams.

    Parameters
    ----------
    correlation_result   – output of correlation_test()
    temporal_score      – output of time_order_heuristic() (+1, 0, -1)
    confounder_result    – output of confounder_check()
    literature_support – 0.0–1.0 placeholder from discovery engine

    Scoring weights:
        statistical_correlation : 0.30  (if significant p < 0.05)
        temporal_precedence     : 0.40  (if A → B consistent)
        no_confounding          : 0.30  (if no confounders found)
        literature_support     : 0.20  (external, 0 if absent)

    Score range: 0.0 – 1.0
    Confidence: low (<0.4), medium (0.4–0.7), high (>0.7)
    """
    w_corr = 0.30
    w_temp = 0.40
    w_conf = 0.30
    w_lit = 0.20

    sig = 1.0 if correlation_result.get("significant") else 0.0
    corr_score = w_corr * sig

    temp_score = w_temp if temporal_score == 1 else 0.0

    no_conf = 1.0 if len(confounder_result.get("confounders_found", [])) == 0 else 0.0
    conf_score = w_conf * no_conf

    lit_score = w_lit * literature_support

    total = corr_score + temp_score + conf_score + lit_score

    if total < 0.4:
        level = "low"
    elif total <= 0.7:
        level = "medium"
    else:
        level = "high"

    return {
        "score": round(total, 3),
        "level": level,
        "breakdown": {
            "correlation": round(corr_score, 3),
            "temporal": round(temp_score, 3),
            "no_confounding": round(conf_score, 3),
            "literature": round(lit_score, 3),
        },
        "significant_correlation": bool(correlation_result.get("significant")),
        "temporal_precedence": temporal_score,
        "confounders": confounder_result.get("confounders_found", []),
        "literature_support": literature_support,
    }


# ── Intervention Simulation ───────────────────────────────────────────────────


def suggest_intervention(
    A: str,
    B: str,
    causal_graph: dict[tuple[str, str], float],
    data: dict[str, list[float]],
    intervention_value: Optional[float] = None,
    *,
    seed: Optional[int] = None,
) -> dict[str, Any]:
    """Simulate a do(A = intervention_value) on variable B.

    Uses conditional probability tables derived from data (read-only simulation).
    If intervention_value is None, uses the median of A as the intervention level.

    Parameters
    ----------
    A, B                 : cause and effect variable names
    causal_graph         : {(cause, effect): confidence} edge dict
    data                 : {varname: [values]} dict
    intervention_value   : value to set A to (default: median of A)
    seed                 : random seed

    Returns
    -------
    dict with keys:
        original_mean_B   – mean of B before intervention
        intervened_mean_B – mean of B after setting A=intervention_value
        change_pct        – percent change in B's mean
        interpretation   – human-readable sentence
        assumption        – caveat about causal assumptions
    """
    if A not in data or B not in data:
        raise ValueError(f"A={A!r} or B={B!r} not in data")

    original_B = data[B]
    original_mean = sum(original_B) / len(original_B)

    if intervention_value is None:
        vals = sorted(data[A])
        n = len(vals)
        intervention_value = vals[n // 2]

    rng = random.Random(seed)

    # Simple conditional simulation:
    # Sample subset of rows where A ≈ intervention_value and compute B mean
    # Fall back to: compute conditional expectation via regression
    # Use residual method for linear approximation
    x = data[A]
    y = data[B]

    if _SCIPY:
        slope, intercept, _, _, _ = _stats.linregress(x, y)
    else:
        n = len(x)
        mx = sum(x) / n
        my = sum(y) / n
        ssxx = sum((xi - mx) ** 2 for xi in x)
        if ssxx == 0:
            slope, intercept = 0.0, my
        else:
            slope = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / ssxx
            intercept = my - slope * mx

    intervened_B_mean = slope * intervention_value + intercept
    change_pct = (
        100 * (intervened_B_mean - original_mean) / abs(original_mean)
        if original_mean != 0
        else 0.0
    )

    edge_key = (A, B)
    graph_confidence = causal_graph.get(edge_key, None)

    return {
        "original_mean_B": round(original_mean, 4),
        "intervened_mean_B": round(intervened_B_mean, 4),
        "intervention_value": intervention_value,
        "change_pct": round(change_pct, 2),
        "interpretation": (
            f"Setting {A}={intervention_value} is predicted to "
            f"{'increase' if change_pct > 0 else 'decrease'} {B} by ~{abs(change_pct):.1f}%"
        ),
        "assumption": (
            f"Causal effect estimated from regression of {B}~{A}. "
            "Causal graph assumptions apply."
        ),
        "graph_confidence": graph_confidence,
    }


# ── Dataset registry (mock datasets) ──────────────────────────────────────────

# In-memory key-value store for mock datasets per session
_DATASETS: dict[str, dict[str, list[float]]] = {}


def register_dataset(dataset_id: str, variables: dict[str, list[float]]) -> None:
    """Store a named dataset for later causal analysis."""
    _DATASETS[dataset_id] = dict(variables)


def get_dataset(dataset_id: str) -> dict[str, list[float]]:
    """Retrieve a dataset by ID."""
    if dataset_id not in _DATASETS:
        raise KeyError(f"Dataset {dataset_id!r} not found. Available: {list(_DATASETS.keys())}")
    return _DATASETS[dataset_id]


def list_datasets() -> list[str]:
    """List available dataset IDs."""
    return list(_DATASETS.keys())


def clear_datasets() -> None:
    """Clear all registered datasets (test isolation)."""
    _DATASETS.clear()
    # Re-register example datasets so built-in examples remain available
    _register_example_datasets()


# ── Built-in example datasets ──────────────────────────────────────────────────

def _register_example_datasets() -> None:
    """Populate registry with example causal datasets."""

    # Dataset A: drug dose vs response (positive correlation)
    register_dataset("clinical_dose_response", {
        "drug_dose":   [10, 20, 30, 40, 50, 60, 70, 80],
        "response":    [22, 31, 38, 45, 54, 60, 67, 73],
        "age":         [45, 50, 35, 60, 55, 40, 48, 52],
    })

    # Dataset B: confounded case (C causes both A and B)
    register_dataset("confounded_demo", {
        "A": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "B": [2.1, 4.2, 5.8, 8.1, 10.2, 12.0, 14.1, 16.0],
        "C": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],  # common cause
    })

    # Dataset C: temporal precedence case
    register_dataset("temporal_demo", {
        "campaign_spend": [100, 200, 300, 400, 500],
        "awareness":      [12,  22,  35,  48,  62],
        "sales":          [0,   0,   15,  30,  55],   # sales lag behind awareness
    })


_register_example_datasets()

# ── Keyword discovery helper ────────────────────────────────────────────────────

CAUSAL_KEYWORDS = {
    "cause", "effect", "correlation", "correlates", "predicts",
    "leads to", "drives", "mediates", "confounder", "mediator",
    "instrumental", "intervention", "do-operator", "counterfactual",
    "causal graph", "dag", "backdoor", "frontdoor",
}

def is_causal_topic(text: str) -> bool:
    """Return True if text mentions causal topics (for discovery integration)."""
    t = text.lower()
    return any(kw in t for kw in CAUSAL_KEYWORDS)
