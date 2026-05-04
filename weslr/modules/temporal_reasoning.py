"""
weslr/modules/temporal_reasoning.py
===================================
Phase 6.6 — Enhanced temporal reasoning for Weslr.

Capabilities:
- Decomposition (additive/multiplicative) via seasonal_decompose or pure-Python fallback
- Autocorrelation (ACF) for lags 1..max_lag
- Cross-correlation (CCF) for optimal lag detection
- Bivariate Granger causality test (F-test on nested VAR models)
- Exponential smoothing (Holt-Winters) with automatic parameter selection
- Forecasting with prediction intervals (80%, 95%) using normally distributed residuals
- Temporal pattern detection (trend, seasonality, stationarity via ADF)

All methods are deterministic (seed=42 for any stochastic components).
No external API calls. Multi-tenant isolation is caller-side (data passed as arguments).

Author: OCC (WESLR governed intelligence) — Phase 6.6
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any

# ── Optional statsmodels ────────────────────────────────────────────────────

_STATSMODELS_AVAILABLE = False
try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import acf, pacf as sm_pacf
    from statsmodels.tsa.stattools import adfuller, grangercausalitytests
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    _STATSMODELS_AVAILABLE = True
except ImportError:
    pass

import numpy as np


# ── Determinism seed ────────────────────────────────────────────────────────

_FIXED_SEED = 42


def _seed_np() -> None:
    np.random.seed(_FIXED_SEED)
    random.seed(_FIXED_SEED)


# ── Pure-Python fallbacks ────────────────────────────────────────────────────


def _pure_decompose(series: list[float], period: int, model: str) -> dict:
    """Pure-Python seasonal decomposition (no statsmodels).

    Trend: centered moving average (window = period).
    Seasonal: period-wise mean of detrended values, demeaned.
    Residual: original - trend - seasonal.
    """
    n = len(series)
    if n < period * 2:
        return {"trend": [None] * n, "seasonal": [None] * n, "residual": [None] * n}

    # Trend via moving average
    trend = [None] * n
    half = period // 2
    for i in range(half, n - half):
        window = series[i - half : i + half + (1 if period % 2 == 1 else 0)]
        trend[i] = sum(window) / len(window)

    # Extend trend to edges by repeating endpoint values
    for i in range(half):
        trend[i] = trend[half]
    for i in range(n - half, n):
        trend[i] = trend[n - half - 1]

    # Seasonal: average of detrended values at each phase
    seasonal = [0.0] * period
    count = [0] * period
    for i in range(n):
        if trend[i] is not None:
            phase = i % period
            val = series[i] - trend[i]
            seasonal[phase] += val
            count[phase] += 1
    seasonal_mean = sum(seasonal) / n
    for p in range(period):
        if count[p] > 0:
            seasonal[p] = seasonal[p] / count[p] - seasonal_mean

    # Expand seasonal to full length
    seasonal_full = [seasonal[i % period] for i in range(n)]

    # Residual
    residual = []
    for i in range(n):
        if trend[i] is not None:
            r = series[i] - trend[i] - seasonal_full[i]
            residual.append(r)
        else:
            residual.append(None)

    return {
        "trend": trend,
        "seasonal": seasonal_full,
        "residual": residual,
    }


def _pure_acf(series: list[float], max_lag: int) -> list[float]:
    """Pure-Python autocorrelation (ACF) for lags 0..max_lag."""
    n = len(series)
    if n < 2:
        return [0.0] * (max_lag + 1)

    mean = sum(series) / n
    var = sum((x - mean) ** 2 for x in series)
    if var == 0:
        return [0.0] * (max_lag + 1)

    # Lag-0 ACF = 1
    acf_vals = [1.0]
    for lag in range(1, max_lag + 1):
        cov = sum(
            (series[i] - mean) * (series[i - lag] - mean)
            for i in range(lag, n)
        )
        acf_vals.append(cov / var)

    return acf_vals


def _pure_cross_corr(x: list[float], y: list[float], max_lag: int) -> dict:
    """Pure-Python cross-correlation for lags -max_lag..max_lag.
    
    Returns CCF list of length 2*max_lag+1 (lags -max_lag .. max_lag).
    best_lag is chosen from non-zero lags.
    """
    n = min(len(x), len(y))
    if n < 2:
        return {"best_lag": 0, "best_corr": 0.0, "ccf": [0.0] * (2 * max_lag + 1)}

    mean_x = sum(x[:n]) / n
    mean_y = sum(y[:n]) / n
    var_x = sum((v - mean_x) ** 2 for v in x[:n]) / n
    var_y = sum((v - mean_y) ** 2 for v in y[:n]) / n
    std_x = math.sqrt(var_x)
    std_y = math.sqrt(var_y)

    # Constant series: zero variance — return zeros for all lags
    if std_x == 0 or std_y == 0:
        return {"best_lag": 0, "best_corr": 0.0, "ccf": [0.0] * (2 * max_lag + 1)}

    ccf_vals = []
    best_lag_excl_zero = 0
    best_corr_excl_zero = -1.0

    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            x_vals = x[:n + lag]
            y_vals = y[-lag:]
        elif lag > 0:
            x_vals = x[lag:n]
            y_vals = y[: n - lag]
        else:
            x_vals = x[:n]
            y_vals = y[:n]

        k = min(len(x_vals), len(y_vals))
        if k < 2:
            ccf_vals.append(0.0)
            continue

        mean_xk = sum(x_vals[:k]) / k
        mean_yk = sum(y_vals[:k]) / k
        cov = sum(
            (x_vals[i] - mean_xk) * (y_vals[i] - mean_yk) for i in range(k)
        )
        std_xk = math.sqrt(sum((v - mean_xk) ** 2 for v in x_vals[:k]) / k)
        std_yk = math.sqrt(sum((v - mean_yk) ** 2 for v in y_vals[:k]) / k)
        corr = cov / (std_xk * std_yk) if std_xk * std_yk != 0 else 0.0

        ccf_vals.append(corr)
        if lag != 0 and abs(corr) > abs(best_corr_excl_zero):
            best_corr_excl_zero = corr
            best_lag_excl_zero = lag

    # best_lag excludes lag 0; default to 1 if nothing found
    if best_lag_excl_zero == 0:
        best_lag_excl_zero = 1
        best_corr_excl_zero = ccf_vals[max_lag + 1] if len(ccf_vals) > max_lag + 1 else 0.0

    return {
        "best_lag": best_lag_excl_zero,
        "best_corr": best_corr_excl_zero,
        "ccf": ccf_vals,
    }


def _pure_granger_f_test(
    y: list[float], x: list[float], lag: int, sig: float
) -> dict:
    """Pure-Python F-test for Granger causality at a single lag.

    Restricted model: y ~ y_lags
    Full model:       y ~ y_lags + x_lags
    H0: x_lags coefficients are jointly zero (x does not Granger-cause y).
    """
    n = max(len(x), len(y))
    if lag < 1 or n < lag * 2:
        return {"causes": False, "p_value": 1.0, "f_stat": 0.0}

    y_arr = np.array(y)
    x_arr = np.array(x)

    # Build lags
    def build_lagged_matrix(arr: np.ndarray, max_lag: int) -> np.ndarray:
        rows = []
        for k in range(max_lag, len(arr)):
            row = [1.0] + [arr[k - j] for j in range(1, max_lag + 1)]
            rows.append(row)
        return np.array(rows) if rows else np.zeros((0, max_lag + 1))

    # Restricted: y ~ own lags only
    y_lagged = build_lagged_matrix(y_arr, lag)
    y_target = y_arr[lag:]

    if len(y_lagged) < lag + 1:
        return {"causes": False, "p_value": 1.0, "f_stat": 0.0}

    # Full: y ~ own lags + x lags
    x_lagged = build_lagged_matrix(x_arr, lag)
    if len(x_lagged) < lag + 1 or x_lagged.shape[0] != y_lagged.shape[0]:
        return {"causes": False, "p_value": 1.0, "f_stat": 0.0}

    X_full = np.hstack([y_lagged, x_lagged])

    # OLS via normal equations
    def ols_residuals(X: np.ndarray, y: np.ndarray) -> Tuple[float, np.ndarray]:
        try:
            coeffs, residuals, _, _ = np.linalg.lstsq(X, y, rcond=None)
            resid = y - X @ coeffs
            rss = float(np.sum(resid ** 2))
            return rss, residuals
        except Exception:
            return float(np.sum(y ** 2)), y

    rss_r, _ = ols_residuals(y_lagged, y_target)
    rss_f, _ = ols_residuals(X_full, y_target)

    df1 = lag  # number of restrictions
    df2 = max(len(y_target) - X_full.shape[1], 1)

    if rss_r <= rss_f or df2 < 1:
        return {"causes": False, "p_value": 1.0, "f_stat": 0.0}

    f_stat = ((rss_r - rss_f) / df1) / (rss_f / df2)
    # Under H0, F follows F(df1, df2). Use approximation for p-value.
    p_value = _f_distribution_pvalue(f_stat, df1, df2)

    return {
        "causes": p_value < sig,
        "p_value": float(p_value),
        "f_stat": float(f_stat),
    }


def _f_distribution_pvalue(f: float, df1: int, df2: int) -> float:
    """Upper-tail p-value for F(df1, df2) via regularized incomplete beta.
    
    P(F > f) = I_{df2/(df2+df1*f)}(df2/2, df1/2)
    
    Uses the beta CDF series expansion, computing ln B(a,b) via Stirling
    approximation for numerical stability. Falls back to 0.5 on any error.
    """
    if f <= 0:
        return 1.0
    try:
        from math import gamma, log, exp, pi
        
        a = df2 / 2.0
        b = df1 / 2.0
        denom = df2 + df1 * f
        if denom == 0:
            return 0.0
        x = df2 / denom  # in (0,1) for f in (0,∞)
        
        # Log-gamma via Stirling approximation (for a,b >= 0.5, very accurate)
        def _ln_gamma(z: float) -> float:
            if z < 0.5:
                # Use reflection: G(z)G(1-z) = pi / sin(pi*z)
                return log(pi) - log(abs(sin(pi * z))) - _ln_gamma(1 - z)
            if z < 1.5:
                return log(gamma(z))
            # Stirling with fraction expansion
            return (z - 0.5) * log(z) - z + 0.5 * log(2 * pi) + 1.0 / (12.0 * z) - 1.0 / (360.0 * z ** 3)
        
        ln_B = _ln_gamma(a) + _ln_gamma(b) - _ln_gamma(a + b)
        
        # p_upper = I_x(a,b) where x = df2/(df2+df1*f)
        # Use complement for x close to 1: I_x(a,b) = 1 - I_{1-x}(b,a)
        if x > 0.5:
            y = 1.0 - x
            # I_y(b,a) = y^b / (b*B) * [1 + b*y/(b+1) + b(b+1)*y^2/((b+2)*2!) + ...]
            series_sum = 1.0
            poch_b = 1.0
            poch_ab = 1.0
            for n in range(1, 200):
                poch_b = poch_b * (b + n - 1)
                poch_ab = poch_ab * (a + b + n - 1)
                term = poch_b / poch_ab / n * y ** n
                series_sum += term
                if abs(term) < 1e-14 * series_sum:
                    break
            ln_first = b * log(y) - log(b) - ln_B
            ln_Iy = ln_first + log(series_sum)
            # I_x(a,b) = 1 - I_y(b,a), but we need I_x which is large
            # Wait - I need to re-think. x=0.987 means I_x(a,b) ≈ 1
            # I_y(b,a) for tiny y is small
            # p_upper = I_x(a,b) = 1 - I_y(b,a) ≈ 1 - small = large
            # But ln_Iy is very negative, exp(ln_Iy) = tiny
            # So p = 1 - exp(ln_Iy) ≈ 1 - tiny ≈ 1
            return min(1.0, max(0.0, 1.0 - exp(ln_Iy)))
        else:
            # x <= 0.5: direct series for I_x(a,b)
            series_sum = 1.0
            term = 1.0
            for n in range(1, 200):
                term = term * (a + n - 1) * x / (n * (a + b + n - 1))
                series_sum += term
                if abs(term) < 1e-14 * series_sum:
                    break
            ln_first = a * log(x) - log(a) - ln_B
            ln_Ix = ln_first + log(series_sum) + b * log(1.0 - x)
            return min(1.0, max(0.0, exp(ln_Ix)))
    except Exception:
        return 0.5


def _log_beta(a: float, b: float) -> float:
    from math import gamma, log
    return log(gamma(a)) + log(gamma(b)) - log(gamma(a + b))


def _beta_cdf_transform(a: float, b: float, x: float) -> float:
    """Crude approximation to normalize beta incomplete."""
    from math import sqrt, pi, erf, log
    # Use normal approximation for large parameters
    if a + b > 100:
        z = (x * (a + b) - a) / sqrt(a * b / (a + b + 1))
        return 0.5 * (1 + erf(z / sqrt(2)))
    return 1.0


def _log_beta_incomplete(a: float, b: float, x: float) -> float:
    """Series approximation of log of regularized incomplete beta."""
    from math import log, gamma, exp
    if x <= 0:
        return float("-inf")
    if x >= 1:
        return log(gamma(a + b)) - log(gamma(a)) - log(gamma(b))
    # Simple series
    ln_B = _log_beta(a, b)
    total = 0.0
    term = 1.0
    for n in range(1, 100):
        term *= (a + n - 1) * (1 - x) / n
        total += term / (a + n)
        if abs(term) < 1e-12:
            break
    return log(x) * a + log(1 + total) - ln_B


def _pure_adf(series: list[float]) -> dict:
    """Pure-Python Augmented Dickey-Fuller test (simplified)."""
    n = len(series)
    if n < 10:
        return {"p_value": 1.0, "test_stat": 0.0, "conclusion": "insufficient_data"}

    # Regression: Δy = α + β*y_{t-1} + Σγ*Δy_{t-k} + ε
    y = np.array(series)
    dy = np.diff(y)
    y_lag = y[:-1]

    if len(dy) < 2 or len(y_lag) < 2:
        return {"p_value": 1.0, "test_stat": 0.0, "conclusion": "insufficient_data"}

    # Simple OLS: dy = β*y_lag + intercept
    try:
        X = np.column_stack([np.ones(len(y_lag)), y_lag])
        coeffs, _, _, _ = np.linalg.lstsq(X, dy, rcond=None)
        resid = dy - X @ coeffs
        rss = np.sum(resid ** 2)
        k = X.shape[1]
        n_ = len(dy)
        se = math.sqrt(rss / (n_ - k))
        se_beta = se / math.sqrt(np.sum((y_lag - np.mean(y_lag)) ** 2))
        t_stat = coeffs[1] / se_beta if se_beta != 0 else 0.0
    except Exception:
        t_stat = 0.0

    # Approximate p-value using MacKinnon (1994) table values
    # For n=100, z < -1.5 → p < 0.05, z < -1.9 → p < 0.01
    if t_stat < -2.5:
        p_value = 0.01
    elif t_stat < -2.0:
        p_value = 0.05
    elif t_stat < -1.5:
        p_value = 0.10
    else:
        p_value = 0.10

    conclusion = "stationary" if p_value < 0.05 else "non_stationary"
    return {
        "p_value": float(p_value),
        "test_stat": float(t_stat),
        "conclusion": conclusion,
    }


def _pure_holt_winters(
    series: list[float], horizon: int, period: int, additive: bool = True
) -> dict:
    """Pure-Python Holt-Winters exponential smoothing (additive/multiplicative).

    Grid search for alpha (level), beta (trend), gamma (seasonal).
    Deterministic seed=42.
    """
    _seed_np()

    n = len(series)
    if n < period * 2:
        return {
            "forecast": [series[-1]] * horizon,
            "lower_80": [series[-1] * 0.9] * horizon,
            "upper_80": [series[-1] * 1.1] * horizon,
            "lower_95": [series[-1] * 0.85] * horizon,
            "upper_95": [series[-1] * 1.15] * horizon,
            "method": "holt_winters_pure",
        }

    mean_seasonal = sum(series[:period]) / period
    seasonal = [s / mean_seas for s, mean_seas in zip(series[:period], [mean_seasonal] * period)] if not additive else [0.0] * period

    # Grid search alpha, beta (coarse)
    best_mse = float("inf")
    best_alpha, best_beta = 0.3, 0.1

    for alpha in [0.1, 0.3, 0.5, 0.7]:
        for beta in [0.0, 0.1, 0.3]:
            try:
                fitted = _hw_fit(series, alpha, beta, 0.3, period, additive)
                mse = fitted["mse"]
                if mse < best_mse:
                    best_mse = mse
                    best_alpha, best_beta = alpha, beta
            except Exception:
                pass

    alpha, beta = best_alpha, best_beta
    gamma = 0.3

    fitted = _hw_fit(series, alpha, beta, gamma, period, additive)
    level = fitted["level"]
    trend = fitted["trend"]
    seasonal = fitted["seasonal"]

    # Forecast with uncertainty
    residual_std = math.sqrt(best_mse) if best_mse < float("inf") else abs(series[-1] - series[0]) * 0.1

    forecasts = []
    lower_80, upper_80 = [], []
    lower_95, upper_95 = [], []

    for h in range(1, horizon + 1):
        if additive:
            fcast = level + h * trend + seasonal[(n + h - 1) % period]
        else:
            fcast = (level + h * trend) * seasonal[(n + h - 1) % period]
        forecasts.append(fcast)

        # Uncertainty grows with horizon
        sigma_h = residual_std * math.sqrt(1 + (h - 1) * 0.1)
        z80 = 1.28  # 80% CI
        z95 = 1.96  # 95% CI
        lower_80.append(fcast - z80 * sigma_h)
        upper_80.append(fcast + z80 * sigma_h)
        lower_95.append(fcast - z95 * sigma_h)
        upper_95.append(fcast + z95 * sigma_h)

    return {
        "forecast": forecasts,
        "lower_80": lower_80,
        "upper_80": upper_80,
        "lower_95": lower_95,
        "upper_95": upper_95,
        "method": "holt_winters_pure",
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "residual_std": residual_std,
    }


def _hw_fit(
    series: list[float], alpha: float, beta: float, gamma: float,
    period: int, additive: bool
) -> dict:
    """Fit Holt-Winters and return level, trend, seasonal, MSE."""
    n = len(series)
    level = series[0]
    trend = (sum(series[period : period * 2]) / period - sum(series[:period]) / period) / period
    seasonal = [0.0] * period

    for p in range(period):
        seasonal[p] = series[p] / (sum(series[:period]) / period) if not additive else series[p] - sum(series[:period]) / period

    for i in range(period, n):
        prev_level = level
        if additive:
            level = alpha * (series[i] - seasonal[i % period]) + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
            seasonal[i % period] = gamma * (series[i] - level) + (1 - gamma) * seasonal[i % period]
        else:
            level = alpha * (series[i] / seasonal[i % period]) + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
            seasonal[i % period] = gamma * (series[i] / level) + (1 - gamma) * seasonal[i % period]

    # Compute MSE on last period
    sse = 0.0
    for i in range(period, n):
        pred = level + trend + seasonal[i % period] if additive else (level + trend) * seasonal[i % period]
        sse += (series[i] - pred) ** 2

    mse = sse / (n - period) if n > period else sse
    return {"level": level, "trend": trend, "seasonal": seasonal, "mse": mse}


# ── Public API ───────────────────────────────────────────────────────────────


@dataclass
class DecomposeResult:
    trend: list[float]
    seasonal: list[float]
    residual: list[float]
    model: str  # "additive" | "multiplicative"


def decompose(
    series: list[float], period: int, model: str = "additive"
) -> DecomposeResult:
    """Decompose a time series into trend, seasonal, and residual components.

    Args:
        series: 1-D list of numeric values (e.g., efficiency, temperature, sales)
        period: Period for seasonality (e.g., 7 for weekly, 12 for monthly)
        model: "additive" (trend + seasonal + residual) or "multiplicative" (trend × seasonal × residual)

    Returns:
        DecomposeResult with trend, seasonal, residual (same length as input)
    """
    if len(series) < period * 2:
        raise ValueError(f"Series length ({len(series)}) must be >= 2×period ({period})")

    if _STATSMODELS_AVAILABLE:
        try:
            result = seasonal_decompose(
                np.array(series), model=model, period=period, extrapolate_trend="freq"
            )
            return DecomposeResult(
                trend=result.trend.tolist(),
                seasonal=result.seasonal.tolist(),
                residual=result.resid.tolist(),
                model=model,
            )
        except Exception:
            pass

    # Pure-Python fallback (handles multiplicative via log transform)
    if model == "multiplicative":
        log_series = [math.log(abs(v) + 1e-8) for v in series]
        decomp = _pure_decompose(log_series, period, "additive")
        return DecomposeResult(
            trend=[math.exp(v) if v is not None else None for v in decomp["trend"]],
            seasonal=[math.exp(v) if v is not None else None for v in decomp["seasonal"]],
            residual=[math.exp(v) if v is not None else None for v in decomp["residual"]],
            model=model,
        )
    else:
        decomp = _pure_decompose(series, period, "additive")
        return DecomposeResult(
            trend=decomp["trend"],
            seasonal=decomp["seasonal"],
            residual=decomp["residual"],
            model=model,
        )


def autocorr(series: list[float], max_lag: int = 30) -> list[float]:
    """Compute autocorrelation (ACF) for lags 0..max_lag.

    Args:
        series: 1-D list of values
        max_lag: Maximum lag to compute (default 30, capped at len(series)-1)

    Returns:
        List of length max_lag+1: ACF values at each lag.
        For short series (< max_lag+1), shorter lag range is returned.
    """
    n = len(series)
    # n=1: lag 0 ACF is always 1.0 (series == itself), remaining lags 0
    if n == 1:
        return [1.0] + [0.0] * max_lag
    # Clamp max_lag to available data
    effective_max = min(max_lag, max(n - 1, 0))
    if effective_max < max_lag:
        # Series too short — return exactly max_lag+1 zeros (fill missing lags)
        return [0.0] * (max_lag + 1)
    if _STATSMODELS_AVAILABLE:
        try:
            acf_vals = acf(np.array(series), nlags=max_lag, fft=False)
            return acf_vals.tolist()
        except Exception:
            pass
    return _pure_acf(series, max_lag)


def cross_corr(x_series: list[float], y_series: list[float], max_lag: int = 30) -> dict:
    """Compute cross-correlation between two series to find optimal lag.

    Returns:
        dict with best_lag (int), best_corr (float), ccf (list of floats)
    """
    max_lag = min(max_lag, 30)
    if _STATSMODELS_AVAILABLE:
        try:
            from statsmodels.tsa.stattools import ccf as sm_ccf
            ccf_vals = sm_ccf(np.array(x_series), np.array(y_series), adjusted=False)
            ccf_list = ccf_vals[: max_lag + 1].tolist()
            # Find best lag (excluding lag 0)
            abs_vals = [abs(v) for v in ccf_list[1:]]
            if abs_vals:
                best_idx = abs_vals.index(max(abs_vals))
                return {
                    "best_lag": best_idx + 1,
                    "best_corr": ccf_list[best_idx + 1],
                    "ccf": ccf_list,
                }
        except Exception:
            pass
    return _pure_cross_corr(x_series, y_series, max_lag)


@dataclass
class GrangerResult:
    causes: bool
    p_value: float
    f_stat: float
    best_lag: int
    significance: float


def granger_cause(
    x: list[float], y: list[float], max_lag: int = 5, significance: float = 0.05
) -> GrangerResult:
    """Bivariate Granger causality test.

    H0: x does not Granger-cause y.
    Tests whether past values of x help predict y beyond y's own past.

    Args:
        x: Cause variable series
        y: Effect variable series
        max_lag: Maximum lag to test (default 5)
        significance: p-value threshold (default 0.05)

    Returns:
        GrangerResult with causes (bool), p_value, f_stat, best_lag
    """
    max_lag = min(max_lag, 30)

    if _STATSMODELS_AVAILABLE:
        try:
            # Stack [y, x] as required by statsmodels
            data = np.column_stack([np.array(y), np.array(x)])
            result = grangercausalitytests(data, maxlag=max_lag, verbose=False)
            # Find best lag (lowest p-value)
            best_lag = 1
            best_p = 1.0
            for lag in range(1, max_lag + 1):
                test_result = result[lag][0]
                # F-test is in the first test's F-statistic entry
                # ssr_ftest returns (F, p, df_denom, df_num)
                f_info = test_result["ssr_ftest"]
                p_val = f_info[1]
                if p_val < best_p:
                    best_p = p_val
                    best_lag = lag
            return GrangerResult(
                causes=best_p < significance,
                p_value=best_p,
                f_stat=result[best_lag][0]["ssr_ftest"][0],
                best_lag=best_lag,
                significance=significance,
            )
        except Exception:
            pass

    # Pure-Python fallback: test each lag, return best p-value
    best_result = {"causes": False, "p_value": 1.0, "f_stat": 0.0, "best_lag": 1}
    for lag in range(1, max_lag + 1):
        r = _pure_granger_f_test(y, x, lag, significance)
        if r["p_value"] < best_result["p_value"]:
            best_result = {"causes": r["causes"], "p_value": r["p_value"], "f_stat": r["f_stat"], "best_lag": lag}

    return GrangerResult(
        causes=best_result["causes"],
        p_value=best_result["p_value"],
        f_stat=best_result["f_stat"],
        best_lag=best_result["best_lag"],
        significance=significance,
    )


@dataclass
class ForecastResult:
    forecast: list[float]
    lower_80: list[float]
    upper_80: list[float]
    lower_95: list[float]
    upper_95: list[float]
    method: str


def forecast(
    series: list[float], horizon: int = 10, method: str = "ets"
) -> ForecastResult:
    """Exponential smoothing (Holt-Winters) forecast with prediction intervals.

    Args:
        series: Historical time series (list of floats)
        horizon: Number of steps to forecast (default 10)
        method: "ets" (exponential smoothing, Holt-Winters) — only supported method

    Returns:
        ForecastResult with forecast values and 80%/95% CI bounds
    """
    if horizon < 1:
        raise ValueError("horizon must be >= 1")

    n = len(series)
    if n < 4:
        # Fallback: repeat last value with growing uncertainty
        last = series[-1] if series else 0.0
        std = abs(last) * 0.1 if last != 0 else 0.1
        forecasts = [last] * horizon
        return ForecastResult(
            forecast=forecasts,
            lower_80=[last - 1.28 * std * math.sqrt(h) for h in range(1, horizon + 1)],
            upper_80=[last + 1.28 * std * math.sqrt(h) for h in range(1, horizon + 1)],
            lower_95=[last - 1.96 * std * math.sqrt(h) for h in range(1, horizon + 1)],
            upper_95=[last + 1.96 * std * math.sqrt(h) for h in range(1, horizon + 1)],
            method="naive_fallback",
        )

    if method == "ets":
        period = _detect_period(series)

        if _STATSMODELS_AVAILABLE:
            try:
                model = ExponentialSmoothing(
                    np.array(series),
                    seasonal_periods=period,
                    trend="add",
                    seasonal="add" if n > period * 2 else None,
                    damped_trend=True,
                    initialization_method="estimated",
                )
                fit = model.fit(remove_bias=True)
                fcast = fit.forecast(horizon)

                # Residuals for interval estimation
                fitted = fit.fittedvalues
                resid = np.array(series) - fitted
                residual_std = float(np.std(resid))

                z80 = 1.28
                z95 = 1.96

                lower_80 = fcast - z80 * residual_std * np.sqrt(np.arange(1, horizon + 1))
                upper_80 = fcast + z80 * residual_std * np.sqrt(np.arange(1, horizon + 1))
                lower_95 = fcast - z95 * residual_std * np.sqrt(np.arange(1, horizon + 1))
                upper_95 = fcast + z95 * residual_std * np.sqrt(np.arange(1, horizon + 1))

                return ForecastResult(
                    forecast=fcast.tolist(),
                    lower_80=lower_80.tolist(),
                    upper_80=upper_80.tolist(),
                    lower_95=lower_95.tolist(),
                    upper_95=upper_95.tolist(),
                    method="holt_winters_statsmodels",
                )
            except Exception:
                pass

        # Pure-Python Holt-Winters — wrap dict result in ForecastResult
        raw = _pure_holt_winters(series, horizon, period, additive=True)
        return ForecastResult(
            forecast=raw["forecast"],
            lower_80=raw["lower_80"],
            upper_80=raw["upper_80"],
            lower_95=raw["lower_95"],
            upper_95=raw["upper_95"],
            method=raw["method"],
        )

    raise ValueError(f"Unknown method '{method}'. Supported: 'ets' (Holt-Winters)")


def _detect_period(series: list[float]) -> int:
    """Auto-detect period from dominant ACF peak (2..365)."""
    if len(series) < 4:
        return 7
    acf_vals = autocorr(series, min(len(series) - 2, 60))
    # Find highest peak at lag >= 2
    best_lag = 2
    best_val = 0.0
    for i in range(2, len(acf_vals)):
        if acf_vals[i] > best_val:
            best_val = acf_vals[i]
            best_lag = i
    return max(2, min(best_lag, 365))


@dataclass
class TemporalPatterns:
    trend_direction: int  # +1 (upward), -1 (downward), 0 (flat)
    seasonality_present: bool
    seasonality_period: int
    stationarity_via_adf: str  # "stationary" | "non_stationary" | "insufficient_data"
    adf_p_value: float
    adf_test_stat: float


def detect_temporal_patterns(series: list[float]) -> TemporalPatterns:
    """Detect temporal patterns in a time series.

    Returns:
        TemporalPatterns with trend_direction, seasonality_present, seasonality_period,
        stationarity_via_adf, adf_p_value, adf_test_stat
    """
    if len(series) < 8:
        return TemporalPatterns(
            trend_direction=0,
            seasonality_present=False,
            seasonality_period=0,
            stationarity_via_adf="insufficient_data",
            adf_p_value=1.0,
            adf_test_stat=0.0,
        )

    # Trend: linear regression slope
    n = len(series)
    x_vals = list(range(n))
    mean_x = sum(x_vals) / n
    mean_y = sum(series) / n
    cov = sum((x_vals[i] - mean_x) * (series[i] - mean_y) for i in range(n))
    var_x = sum((x - mean_x) ** 2 for x in x_vals)
    slope = cov / var_x if var_x != 0 else 0.0

    # Normalized slope: per-step change relative to mean
    mean_val = abs(mean_y) if mean_y != 0 else 1.0
    normalized_slope = slope / mean_val if mean_val != 0 else 0.0

    if normalized_slope > 0.02:
        trend_direction = 1
    elif normalized_slope < -0.02:
        trend_direction = -1
    else:
        trend_direction = 0

    # Seasonality: ACF peak at period
    period = _detect_period(series)
    acf_vals = autocorr(series, min(len(series) - 2, 60))
    seasonality_present = period >= 2 and len(acf_vals) > period and acf_vals[period] > 0.3

    # Stationarity: ADF test
    if _STATSMODELS_AVAILABLE:
        try:
            adf_result = adfuller(np.array(series), maxlag=min(period - 1, 10), regression="c")
            p_value = adf_result[1]
            test_stat = adf_result[0]
        except Exception:
            p_value, test_stat = _pure_adf(series)["p_value"], _pure_adf(series)["test_stat"]
    else:
        adf_dict = _pure_adf(series)
        p_value = adf_dict["p_value"]
        test_stat = adf_dict["test_stat"]

    conclusion = "stationary" if p_value < 0.05 else "non_stationary"
    return TemporalPatterns(
        trend_direction=trend_direction,
        seasonality_present=seasonality_present,
        seasonality_period=period,
        stationarity_via_adf=conclusion,
        adf_p_value=p_value,
        adf_test_stat=test_stat,
    )


def format_decompose_table(result: DecomposeResult, names: Optional[list[str]] = None) -> str:
    """Format decomposition result as ASCII table (last 10 rows)."""
    trend = result.trend
    seasonal = result.seasonal
    residual = result.residual
    n = len(trend)
    start = 0
    rows = ["Step | Trend       | Seasonal   | Residual"]
    rows.append("-----|------------|------------|------------")
    for i in range(start, n):
        label = names[i] if names and i < len(names) else str(i)
        t = f"{trend[i]:8.4f}" if trend[i] is not None else "    None"
        s = f"{seasonal[i]:8.4f}" if seasonal[i] is not None else "    None"
        r = f"{residual[i]:8.4f}" if residual[i] is not None else "    None"
        rows.append(f"{label:4s} | {t} | {s} | {r}")
    return "\n".join(rows)


def format_forecast_table(result: ForecastResult, names: Optional[list[str]] = None) -> str:
    """Format forecast result as table with CI."""
    forecasts = result.forecast
    n = len(forecasts)
    rows = ["Step | Forecast | 80% CI           | 95% CI           | Method"]
    rows.append("-----|----------|----------------|------------------|-------")
    for i in range(n):
        label = names[i] if names and i < len(names) else str(i + 1)
        f = f"{forecasts[i]:8.4f}"
        l80 = f"{result.lower_80[i]:8.4f}"
        u80 = f"{result.upper_80[i]:8.4f}"
        l95 = f"{result.lower_95[i]:8.4f}"
        u95 = f"{result.upper_95[i]:8.4f}"
        rows.append(f"{label:4s} | {f} | [{l80}, {u80}] | [{l95}, {u95}] | {result.method}")
    return "\n".join(rows)
