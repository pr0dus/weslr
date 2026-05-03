"""
weslr/modules/experiment_simulation.py
=====================================
Phase 6.8 — Experiment simulation stub for Weslr.

Capabilities:
- Define mathematical outcome models (linear, Emax, exponential, custom sympy)
- Run deterministic predictions with optional Gaussian noise
- Parameter sweeps across a range
- Statistical power analysis (two-sample t-test based)
- Mock clinical trial skeleton generator

Deterministic (seed=42). Read-only (no real trial execution).
No external API calls. All outputs labelled as mock.

Author: OCC (WESLR governed intelligence) — Phase 6.8
"""

from __future__ import annotations

import math
import random
import re
import textwrap
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# ── Optional dependencies ──────────────────────────────────────────────────

try:
    import sympy
    from sympy import E, exp, log, sqrt, sin, cos, Max, Min, Symbol, SympifyError

    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False
    sympy = None  # type: ignore[assignment]
    SympifyError = Exception  # type: ignore[misc]

try:
    from scipy import stats

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    stats = None  # type: ignore[assignment]


# ── Pure-Python normal quantile (no scipy required) ──────────────────────

def _erfinv(y: float) -> float:
    """Inverse error function — pure Python, bisection search.

    erf(erfinv(y)) = y for y ∈ (-1, 1). Bisection on f(z)=erf(z)-y.
    Converges to ≈1e-12 in ≤60 iterations. No rational approximation needed.
    """
    if y == 0.0:
        return 0.0
    sign = -1 if y < 0 else 1
    yy = abs(y)
    if yy >= 1.0:
        return float("-inf" if y < 0 else "inf")

    lo, hi = -5.0, 5.0
    for _ in range(60):
        mid = (lo + hi) * 0.5
        f_mid = math.erf(mid) - yy
        if f_mid > 0:
            hi = mid
        else:
            lo = mid
        if hi - lo < 1e-13:
            break

    return sign * (lo + hi) * 0.5


def _norm_ppf(p: float) -> float:
    """Inverse standard normal CDF — no scipy required.

    Returns z such that Φ(z) = p. Uses: Φ⁻¹(p) = √2 · erfinv(2p−1).
    """
    if p <= 0:
        return float("-inf")
    if p >= 1:
        return float("inf")
    if p == 0.5:
        return 0.0
    p = max(1e-15, min(1.0 - 1e-15, p))
    return math.sqrt(2.0) * _erfinv(2.0 * p - 1.0)


# ── Safe-expression guard ──────────────────────────────────────────────────

_UNSAFE_PATTERNS = [
    re.compile(r"__"),
    re.compile(r"\bimport\b"),
    re.compile(r"\bexec\b"),
    re.compile(r"\beval\b"),
    re.compile(r"\bopen\b"),
    re.compile(r"\bfile\b"),
    re.compile(r"\bos\b"),
    re.compile(r"\bsystem\b"),
    re.compile(r"\bsubprocess\b"),
    re.compile(r"<"),
    re.compile(r">"),
]


def _is_safe_expression(expr: str) -> bool:
    """Reject expressions with dangerous constructs."""
    for pat in _UNSAFE_PATTERNS:
        if pat.search(expr):
            return False
    return True


# ── Model templates ────────────────────────────────────────────────────────

MODEL_TEMPLATES = {
    "linear": {
        "formula": "slope * x + intercept",
        "params": ["slope", "intercept"],
        "eval": lambda x, slope, intercept: slope * np.asarray(x, dtype=float) + intercept,
    },
    "emax": {
        "formula": "E_max * x / (ED50 + x)",
        "params": ["E_max", "ED50"],
        "eval": lambda x, E_max, ED50: E_max * np.asarray(x, dtype=float) / (ED50 + np.asarray(x, dtype=float)),
    },
    "exponential": {
        "formula": "A * exp(-k * x)",
        "params": ["A", "k"],
        "eval": lambda x, A, k: A * np.exp(-k * np.asarray(x, dtype=float)),
    },
}


def _eval_numpy_expr(expr_str: str, symbols_dict: dict) -> np.ndarray:
    """Evaluate a safe sympy expression as a numpy array."""
    x_val = symbols_dict.get("x", symbols_dict.get("dose", 0))
    x_arr = np.asarray(x_val, dtype=float)

    for sname, nfunc in [
        ("exp", "np.exp"),
        ("log", "np.log"),
        ("sin", "np.sin"),
        ("cos", "np.cos"),
        ("sqrt", "np.sqrt"),
        ("E", str(math.e)),
    ]:
        expr_str = re.sub(r"\b" + sname + r"\b", nfunc, expr_str)
    expr_str = re.sub(r"\bx\b", "x_arr", expr_str)
    expr_str = re.sub(r"\bdose\b", "x_arr", expr_str)
    return eval(expr_str)  # nosec — all paths vetted by _is_safe_expression + sympify


# ── Data class ─────────────────────────────────────────────────────────────

@dataclass
class SimulationResult:
    """Container for a single simulation run."""

    model_type: str
    formula: str
    x_values: list[float]
    predictions: list[float]
    noise_sd: float
    parameters: dict
    summary: dict = field(default_factory=dict)


# ── Main class ─────────────────────────────────────────────────────────────

class ExperimentSimulation:
    """In‑silico experiment simulator.

    Parameters
    ----------
    model_type : str
        One of 'linear', 'emax', 'exponential', 'custom'.
    parameters : dict
        Model parameters (e.g. {'E_max': 100, 'ED50': 10}).
    noise_sd : float
        Standard deviation of additive Gaussian noise. Default 0 (deterministic).
    seed : int
        Random seed for noise generation. Default 42.
    """

    def __init__(
        self,
        model_type: str = "emax",
        parameters: Optional[dict] = None,
        noise_sd: float = 0.0,
        seed: int = 42,
    ):
        if model_type not in ("linear", "emax", "exponential", "custom"):
            raise ValueError(
                f"Unknown model_type '{model_type}'. "
                "Must be one of: linear, emax, exponential, custom."
            )
        self.model_type = model_type
        self.parameters = parameters or {}
        self.noise_sd = noise_sd
        self.seed = seed
        self._custom_expr: Optional[str] = None
        self._custom_vars: dict = {}

        template = MODEL_TEMPLATES.get(model_type)
        self._formula = template["formula"] if template else ""

    # ── Custom model ──────────────────────────────────────────────────────

    def set_custom_model(self, expression: str, independent_var: str = "x") -> None:
        """Parse and store a custom sympy expression.

        Example: sim.set_custom_model("3.2*dose / (dose + 5.0)", independent_var="dose")
        """
        if not HAS_SYMPY:
            raise ImportError(
                "sympy is required for custom models. Install with: pip install sympy"
            )
        if not _is_safe_expression(expression):
            raise ValueError(
                "Expression contains unsafe constructs. "
                "Allowed: +, -, *, /, **, exp, log, sin, cos, sqrt, E, x, dose. "
                "No __import__, eval, open, etc."
            )
        try:
            sympy.sympify(expression)
        except SympifyError as exc:
            raise ValueError(f"Could not parse expression: {expression}") from exc

        self._custom_expr = expression
        self.model_type = "custom"
        self._formula = expression
        self._custom_vars["independent_var"] = independent_var

    # ── Prediction ────────────────────────────────────────────────────────

    def predict(self, x_values) -> SimulationResult:
        """Generate predictions for x_values (deterministic or noisy)."""
        rng = np.random.default_rng(self.seed)
        x_arr = np.asarray(x_values, dtype=float)

        if self.model_type == "custom" and self._custom_expr:
            preds = _eval_numpy_expr(self._custom_expr, {**self.parameters, "x": x_arr})
            formula = self._custom_expr
        else:
            template = MODEL_TEMPLATES[self.model_type]
            params = {**self.parameters}
            for p in template["params"]:
                params.setdefault(p, 1.0)
            preds = template["eval"](x_arr, *[params[p] for p in template["params"]])
            formula = template["formula"]

        preds = np.asarray(preds, dtype=float)
        if self.noise_sd > 0:
            preds = preds + rng.normal(0, self.noise_sd, size=len(preds))

        self._last_predictions = preds
        self._last_x = x_arr

        return SimulationResult(
            model_type=self.model_type,
            formula=formula,
            x_values=list(x_arr),
            predictions=[round(float(p), 4) for p in preds],
            noise_sd=self.noise_sd,
            parameters={**self.parameters},
            summary={
                "n": len(x_arr),
                "x_min": float(x_arr.min()),
                "x_max": float(x_arr.max()),
                "y_min": round(float(preds.min()), 4),
                "y_max": round(float(preds.max()), 4),
                "y_mean": round(float(preds.mean()), 4),
            },
        )

    # ── Parameter sweep ──────────────────────────────────────────────────

    def sweep(
        self,
        parameter_name: str,
        range_start: float,
        range_end: float,
        n_steps: int = 10,
        fixed_params: Optional[dict] = None,
    ) -> list[dict]:
        """Vary one parameter; return outcome curves for each value."""
        if n_steps < 2:
            raise ValueError("n_steps must be >= 2")
        rng = np.random.default_rng(self.seed)
        param_values = np.linspace(range_start, range_end, n_steps)
        fixed = dict(fixed_params or {})
        default_x = getattr(self, "_last_x", None) or [0, 1, 2, 3, 4, 5]

        results = []
        for pval in param_values:
            params = {**fixed, parameter_name: pval}
            sim = ExperimentSimulation(
                model_type=self.model_type,
                parameters=params,
                noise_sd=self.noise_sd,
                seed=int(rng.integers(0, 2**31)),
            )
            if self.model_type == "custom" and self._custom_expr:
                sim.set_custom_model(self._custom_expr)
            result = sim.predict(list(default_x))
            results.append(
                {
                    "param_name": parameter_name,
                    "param_value": round(float(pval), 4),
                    "x_values": result.x_values,
                    "predictions": result.predictions,
                    "summary": result.summary,
                }
            )

        self._last_sweep = results
        return results

    # ── Power analysis ─────────────────────────────────────────────────────

    def power_analysis(
        self,
        effect_size: float,
        alpha: float = 0.05,
        power: float = 0.8,
        test_type: str = "t_independent",
    ) -> dict:
        """Compute required sample size per group.

        Uses the two‑sample t‑test formula (Cohen's d):
          n = 2 × ((z_α + z_β) / d)²
        where z values come from the standard normal CDF inverse.
        Falls back to _norm_ppf when scipy is unavailable.
        """
        if not (0 < effect_size <= 3.0):
            raise ValueError("effect_size must be in (0, 3.0]")
        if not (0 < alpha < 0.5):
            raise ValueError("alpha must be in (0, 0.5)")
        if not (0.1 < power < 0.999):
            raise ValueError("power must be in (0.1, 0.999)")

        if test_type == "t_independent":
            if HAS_SCIPY:
                z_alpha = stats.norm.ppf(1 - alpha / 2)
                z_beta = stats.norm.ppf(power)
            else:
                z_alpha = _norm_ppf(1 - alpha / 2)
                z_beta = _norm_ppf(power)
            n_raw = 2 * ((z_alpha + z_beta) / effect_size) ** 2
            n_per_group = math.ceil(n_raw)
            return {
                "n_per_group": n_per_group,
                "effect_size": round(effect_size, 3),
                "alpha": alpha,
                "power": power,
                "beta": round(1 - power, 4),
                "test_type": test_type,
                "formula": (
                    f"n = 2 × ((z_α + z_β) / d)² "
                    f"= 2 × (({z_alpha:.4f} + {z_beta:.4f}) / {effect_size})² "
                    f"= {n_raw:.2f} → {n_per_group}"
                ),
            }
        elif test_type == "chi2":
            z_alpha = _norm_ppf(1 - alpha / 2) if not HAS_SCIPY else stats.norm.ppf(1 - alpha / 2)
            n_raw = (z_alpha / effect_size) ** 2
            n_per_group = math.ceil(n_raw)
            return {
                "n_per_group": n_per_group,
                "effect_size": round(effect_size, 3),
                "alpha": alpha,
                "power": power,
                "beta": round(1 - power, 4),
                "test_type": test_type,
                "formula": f"n ≈ (z_α / d)² = ({z_alpha:.4f} / {effect_size})² = {n_raw:.2f} → {n_per_group}",
            }
        else:
            raise ValueError(f"Unknown test_type '{test_type}'. Use 't_independent' or 'chi2'.")

    # ── Mock trial design ─────────────────────────────────────────────────

    @staticmethod
    def mock_trial_design(
        arms: list[str],
        duration_weeks: int,
        endpoints: list[str],
        sample_size: int,
        dropout_rate: float = 0.1,
    ) -> dict:
        """Generate a mock clinical trial skeleton."""
        if not arms:
            raise ValueError("At least one arm is required")
        if not (0 <= dropout_rate < 1):
            raise ValueError("dropout_rate must be in [0, 1)")

        n_per_group = sample_size
        enrolled_total = math.ceil(n_per_group * len(arms) / (1 - dropout_rate))

        return {
            "design": "randomized, double-blind, placebo-controlled",
            "arms": [
                {
                    "name": arm,
                    "n_target": n_per_group,
                    "n_enroll": math.ceil(n_per_group / (1 - dropout_rate)),
                    "allocation": f"{n_per_group} participants",
                }
                for arm in arms
            ],
            "duration_weeks": duration_weeks,
            "endpoints": [
                {"name": ep, "type": "primary" if i == 0 else "secondary"}
                for i, ep in enumerate(endpoints)
            ],
            "sample_size": {
                "per_group": n_per_group,
                "total_randomized": n_per_group * len(arms),
                "total_enroll": enrolled_total,
                "dropout_rate": dropout_rate,
                "dropout_n": enrolled_total - n_per_group * len(arms),
            },
            "timeline": [
                {"week": 0, "event": "Randomization & baseline"},
                {"week": duration_weeks // 3, "event": "Interim analysis (optional)"},
                {"week": duration_weeks, "event": "Primary endpoint measurement"},
                {"week": duration_weeks + 2, "event": "Follow-up"},
            ],
            "statistics": [
                {"method": "ITT analysis", "note": "Intent-to-treat, all randomized"},
                {"method": "Per-protocol", "note": "Completers only"},
                {
                    "method": "Test",
                    "details": "Two-sample t-test (continuous) / Chi-square (categorical)",
                },
            ],
        }

    # ── Formatting ───────────────────────────────────────────────────────

    def format_predictions(
        self,
        result: SimulationResult,
        include_summary: bool = True,
    ) -> str:
        """Render predictions as a readable table."""
        lines = [
            f"Model: {result.model_type}",
            f"Formula: {result.formula}",
        ]
        if result.noise_sd > 0:
            lines.append(f"Noise SD: {result.noise_sd}")
        lines.append("\nx\ty")
        for x, y in zip(result.x_values, result.predictions):
            lines.append(f"{x}\t{y:.4f}")
        if include_summary and result.summary:
            s = result.summary
            lines.append(
                f"\nSummary: n={s['n']}, x∈[{s['x_min']},{s['x_max']}], "
                f"y∈[{s['y_min']},{s['y_max']}], mean={s['y_mean']}"
            )
        lines.append("\n[SIMULATION MODE – Not real data – for hypothesis generation only]")
        return "\n".join(lines)

    def format_sweep(self, results: list[dict], metric_at: Optional[int] = None) -> str:
        """Render a parameter sweep as a table."""
        if not results:
            return "No sweep data."
        metric_idx = metric_at if metric_at is not None else -1
        param_name = results[0]["param_name"]
        lines = [
            f"Parameter sweep: {param_name}",
            f"Steps: {len(results)}",
            "",
            f"{param_name}\tOutcome (@x={results[0]['x_values'][metric_idx]})",
        ]
        for r in results:
            lines.append(f"{r['param_value']}\t{r['predictions'][metric_idx]:.4f}")
        lines.append("\n[SIMULATION MODE – Not real data – for hypothesis generation only]")
        return "\n".join(lines)

    @staticmethod
    def format_power(result: dict) -> str:
        """Render power analysis result."""
        lines = [
            f"Power analysis ({result['test_type']})",
            f"Effect size (d): {result['effect_size']}",
            f"Alpha: {result['alpha']}",
            f"Power: {result['power']}",
            f"β (type II error): {result['beta']}",
            f"Formula: {result['formula']}",
            f"Required n per group: {result['n_per_group']}",
            f"Total n (2 arms): {result['n_per_group'] * 2}",
            "\n[SIMULATION MODE – Not real data – for hypothesis generation only]",
        ]
        return "\n".join(lines)

    @staticmethod
    def format_trial_design(trial: dict) -> str:
        """Render mock trial design as readable text."""
        arms = ", ".join(f"'{a['name']}' (n={a['n_target']})" for a in trial["arms"])
        lines = [
            "Mock Clinical Trial Design",
            "=" * 40,
            textwrap.fill(
                f"Randomized, double-blind, placebo-controlled, {len(trial['arms'])} arms "
                f"({arms}), duration {trial['duration_weeks']} weeks.",
                width=70,
            ),
            f"\nEndpoints:",
        ]
        for ev in trial["endpoints"]:
            lines.append(f"  • {ev['name']} ({ev['type']})")
        ss = trial["sample_size"]
        lines.extend(
            [
                f"\nSample size:",
                f"  Target per group: {ss['per_group']}",
                f"  Total randomized: {ss['total_randomized']}",
                f"  Enroll × {ss['dropout_rate']*100:.0f}% dropout → {ss['total_enroll']} total",
                f"\nTimeline:",
            ]
        )
        for ev in trial["timeline"]:
            lines.append(f"  Week {ev['week']}: {ev['event']}")
        lines.append("\n[SIMULATION MODE – Not real data – for hypothesis generation only]")
        return "\n".join(lines)