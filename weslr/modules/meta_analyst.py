"""
weslr/modules/meta_analyst.py
=============================
Phase 9 — Meta-Analysis: pool evidence across hypotheses/studies.

Pure Python implementation — no scipy.stats required.
Uses _norm_cdf and _norm_ppf from experiment_simulation (imported) OR
standalone pure-Python implementations here.

Author: OCC (WESLR governed intelligence) — Phase 9
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

# ── Pure-Python normal CDF and inverse CDF ────────────────────────────────────

def _erfinv(y: float) -> float:
    """Bisection search for inverse error function."""
    if y < -1.0 or y > 1.0:
        raise ValueError(f"erfinv requires y in [-1, 1], got {y}")
    if y == 0.0:
        return 0.0
    if y == 1.0:
        return float("inf")
    if y == -1.0:
        return float("-inf")
    # Bracket [-5, 5] — erf(z) is monotonic
    lo, hi = -5.0, 5.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        fmid = math.erf(mid) - y
        if abs(fmid) < 1e-14:
            return mid
        if fmid * (math.erf(lo) - y) < 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0

def _norm_cdf(x: float) -> float:
    """Standard normal CDF via error function."""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def _norm_ppf(p: float) -> float:
    """Standard normal quantile function."""
    return math.sqrt(2.0) * _erfinv(2.0 * p - 1.0)


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Study:
    """A single study in the meta-analysis."""
    study_id: str
    effect_size: float
    standard_error: float
    sample_size: int
    weight_fixed: float = 0.0
    weight_random: float = 0.0


@dataclass
class MetaResult:
    """Output of a meta-analysis run."""
    pooled_effect: float
    se: float
    z: float
    p: float
    ci_lower: float
    ci_upper: float
    tau_sq: float = 0.0          # between-study variance (RE only)
    q_statistic: float = 0.0     # Cochran's Q
    i_squared: float = 0.0      # heterogeneity %
    pooled_type: str = "fixed"   # "fixed" or "random"
    studies: list[Study] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Aliases for tests that expect different field names
    _ALIASES = {
        "pooled_se": "se",
        "se_estimate": "se",
        "p_value": "p",
        "ci_low": "ci_lower",
        "ci_high": "ci_upper",
        "i2": "i_squared",
        "tau_squared": "tau_sq",
    }

    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access: result['pooled_effect'].

        Handles common field-name aliases used by tests.
        Integer keys are supported for iteration compatibility.
        """
        if isinstance(key, int):
            # Support iteration-style access (Python falls back to __getitem__(0), __getitem__(1)...)
            keys = list(self.keys())
            return keys[key]
        if key in self._ALIASES:
            return getattr(self, self._ALIASES[key])
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def keys(self):
        """Return field names for dict()-style access."""
        return ["pooled_effect", "se", "z", "p", "ci_lower", "ci_upper", "tau_sq", "q_statistic", "i_squared", "pooled_type"]

    def summary(self) -> str:
        sig = "***" if self.p < 0.001 else "**" if self.p < 0.01 else "*" if self.p < 0.05 else "n.s."
        return (
            f"Pooled effect: {self.pooled_effect:.4f} (95% CI {self.ci_lower:.4f}–{self.ci_upper:.4f}), "
            f"z={self.z:.3f}, p={self.p:.4f} {sig} | "
            f"Heterogeneity: I²={self.i_squared:.1f}%, τ²={self.tau_sq:.4f}"
        )


# ── Tenant-aware study store ───────────────────────────────────────────────────

_TENANT_STUDIES: dict[str, list[Study]] = {}
_current_tenant_getter: callable = lambda: "default"

def set_tenant_getter(fn: callable) -> None:
    global _current_tenant_getter
    _current_tenant_getter = fn


def _tenant_studies() -> list[Study]:
    return _TENANT_STUDIES.setdefault(_current_tenant_getter(), [])


# ── MetaAnalysis class ─────────────────────────────────────────────────────────

class MetaAnalysis:
    """
    Fixed-effect and random-effects (DerSimonian-Laird) meta-analysis.

    Methods:
      add_study(effect_size, standard_error, sample_size, study_id)
      list_studies() -> list[Study]
      clear_studies()
      fixed_effect_pooled() -> MetaResult
      random_effect_pooled() -> MetaResult
      heterogeneity() -> (Q, I2, tau_sq)
      from_hypotheses(hypothesis_ids, repo) -> int  [import from repo]
    """

    MAX_STUDIES = 100

    def __init__(self):
        pass

    # ── Study management ───────────────────────────────────────────────────

    def add_study(
        self,
        study_id: str,
        effect_size: float,
        standard_error: float,
        n: Optional[int] = None,
    ) -> Study:
        """Add a study to the current tenant's meta-analysis pool."""
        studies = _tenant_studies()
        if len(studies) >= self.MAX_STUDIES:
            raise RuntimeError(f"Max studies ({self.MAX_STUDIES}) reached")
        if study_id is None:
            study_id = f"study_{len(studies)+1}"
        if standard_error <= 0:
            raise ValueError(f"standard_error must be > 0, got {standard_error}")
        study = Study(
            study_id=study_id,
            effect_size=float(effect_size),
            standard_error=float(standard_error),
            sample_size=int(n) if n is not None else 0,
        )
        studies.append(study)
        return study

    def list_studies(self) -> list[Study]:
        """Return all studies for current tenant."""
        return list(_tenant_studies())

    def clear_studies(self) -> None:
        """Remove all studies for current tenant."""
        _tenant_studies().clear()

    def remove_study(self, study_id: str) -> bool:
        """Remove a specific study."""
        studies = _tenant_studies()
        for i, s in enumerate(studies):
            if s.study_id == study_id:
                studies.pop(i)
                return True
        return False

    def run_analysis(self, model: str = "fixed") -> MetaResult:
        """Run meta-analysis. model ∈ {"fixed", "random"}."""
        if model == "fixed":
            return self.fixed_effect_pooled()
        elif model == "random":
            return self.random_effect_pooled()
        else:
            raise ValueError(f"model must be 'fixed' or 'random', got {model!r}")

    # ── Fixed-effect pooling ───────────────────────────────────────────────

    def fixed_effect_pooled(self) -> MetaResult:
        """
        Inverse-variance weighted fixed-effect meta-analysis.

        weight_i = 1 / SE_i²
        pooled   = Σ(w_i × y_i) / Σ(w_i)
        SE       = 1 / sqrt(Σw_i)
        Z        = pooled / SE
        p        = 2 × (1 - Φ(|Z|))
        95% CI   = pooled ± 1.96 × SE
        """
        studies = _tenant_studies()
        if not studies:
            raise RuntimeError("No studies in pool — add studies first")
        if len(studies) == 1:
            y = studies[0].effect_size
            se = studies[0].standard_error
            z = y / se if se > 0 else 0.0
            p = 2 * (1 - _norm_cdf(abs(z)))
            ci_lo = y - 1.96 * se
            ci_hi = y + 1.96 * se
            return MetaResult(
                pooled_effect=y, se=se, z=z, p=p,
                ci_lower=ci_lo, ci_upper=ci_hi,
                q_statistic=0.0, i_squared=0.0, pooled_type="fixed",
                studies=list(studies),
            )

        # Compute fixed weights
        ws = []
        ys = []
        for s in studies:
            w = 1.0 / (s.standard_error ** 2)
            ws.append(w)
            ys.append(s.effect_size)
            s.weight_fixed = w

        sum_w = sum(ws)
        sum_wy = sum(w * y for w, y in zip(ws, ys))
        pooled = sum_wy / sum_w
        se = 1.0 / math.sqrt(sum_w)
        z = pooled / se if se > 0 else 0.0
        p = 2 * (1 - _norm_cdf(abs(z)))
        ci_lo = pooled - 1.96 * se
        ci_hi = pooled + 1.96 * se

        # Cochran's Q
        q = sum(w * (y - pooled) ** 2 for w, y in zip(ws, ys))
        k = len(studies)
        i_sq = max(0.0, (q - (k - 1)) / q * 100.0) if q > 0 else 0.0

        return MetaResult(
            pooled_effect=round(pooled, 6),
            se=round(se, 6),
            z=round(z, 4),
            p=round(p, 6),
            ci_lower=round(ci_lo, 6),
            ci_upper=round(ci_hi, 6),
            q_statistic=round(q, 4),
            i_squared=round(i_sq, 2),
            pooled_type="fixed",
            studies=list(studies),
        )

    # ── Random-effects (DerSimonian-Laird) ─────────────────────────────────

    def random_effect_pooled(self) -> MetaResult:
        """
        DerSimonian-Laird random-effects meta-analysis.

        tau² = max(0, (Q - (k-1)) / (Σw_i - Σw_i²/Σw_i))
        RE weights: w*_i = 1 / (SE_i² + tau²)
        """
        studies = _tenant_studies()
        if not studies:
            raise RuntimeError("No studies in pool")

        # First compute Q and fixed weights
        k = len(studies)
        ws = []
        ys = []
        for s in studies:
            w = 1.0 / (s.standard_error ** 2)
            ws.append(w)
            ys.append(s.effect_size)
            s.weight_fixed = w

        sum_w = sum(ws)
        sum_wy = sum(w * y for w, y in zip(ws, ys))
        pooled_fixed = sum_wy / sum_w

        q = sum(w * (y - pooled_fixed) ** 2 for w, y in zip(ws, ys))
        denom = sum_w - sum(w ** 2 for w in ws) / sum_w
        tau_sq = max(0.0, (q - (k - 1)) / denom) if denom > 0 else 0.0

        # RE weights
        re_ws = []
        for s, se in zip(studies, [si.standard_error for si in studies]):
            w_star = 1.0 / (se ** 2 + tau_sq)
            re_ws.append(w_star)
            s.weight_random = w_star

        sum_re_w = sum(re_ws)
        sum_re_wy = sum(w * y for w, y in zip(re_ws, ys))
        pooled = sum_re_wy / sum_re_w
        se = 1.0 / math.sqrt(sum_re_w) if sum_re_w > 0 else 0.0
        z = pooled / se if se > 0 else 0.0
        p = 2 * (1 - _norm_cdf(abs(z)))
        ci_lo = pooled - 1.96 * se
        ci_hi = pooled + 1.96 * se

        i_sq = max(0.0, (q - (k - 1)) / q * 100.0) if q > 0 else 0.0

        return MetaResult(
            pooled_effect=round(pooled, 6),
            se=round(se, 6),
            z=round(z, 4),
            p=round(p, 6),
            ci_lower=round(ci_lo, 6),
            ci_upper=round(ci_hi, 6),
            tau_sq=round(tau_sq, 6),
            q_statistic=round(q, 4),
            i_squared=round(i_sq, 2),
            pooled_type="random",
            studies=list(studies),
        )

    # ── Heterogeneity stats ────────────────────────────────────────────────

    def heterogeneity(self) -> tuple[float, float, float]:
        """Return (Q, I², tau²) from current studies."""
        studies = _tenant_studies()
        if len(studies) < 2:
            return 0.0, 0.0, 0.0

        ys = [s.effect_size for s in studies]
        ws = [1.0 / (s.standard_error ** 2) for s in studies]
        sum_w = sum(ws)
        sum_wy = sum(w * y for w, y in zip(ws, ys))
        pooled = sum_wy / sum_w

        q = sum(w * (y - pooled) ** 2 for w, y in zip(ws, ys))
        k = len(studies)
        i_sq = max(0.0, (q - (k - 1)) / q * 100.0) if q > 0 else 0.0

        denom = sum_w - sum(w ** 2 for w in ws) / sum_w
        tau_sq = max(0.0, (q - (k - 1)) / denom) if denom > 0 else 0.0

        return round(q, 4), round(i_sq, 2), round(tau_sq, 6)

    # ── Import from HypothesisRepository ────────────────────────────────────

    def from_hypotheses(self, hypothesis_ids: list[str], repo) -> int:
        """
        Import effect sizes from hypotheses in the repository.

        Each hypothesis must have metadata['effect_size'] and metadata['standard_error'].
        Returns number of studies imported.
        """
        count = 0
        for hid in hypothesis_ids:
            h = repo.get(hid)
            if h is None:
                continue
            effect_size = h.metadata.get("effect_size")
            standard_error = h.metadata.get("standard_error")
            n = h.metadata.get("sample_size") or h.metadata.get("n")
            if effect_size is not None and standard_error is not None:
                self.add_study(effect_size, standard_error, int(n) if n else 30, hid)
                count += 1
        return count

    def __repr__(self) -> str:
        return f"MetaAnalysis(studies={len(_tenant_studies())}, max={self.MAX_STUDIES})"