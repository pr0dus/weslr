"""
weslr/commands/simulation_commands.py
=====================================
Phase 6.8 — Command handlers for experiment simulation.

Handles: /simulate model, /simulate predict, /simulate sweep,
         /simulate power, /experiment design

Author: OCC (WESLR governed intelligence) — Phase 6.8
"""

from __future__ import annotations

import re
import shlex
from typing import Optional

from weslr.modules.experiment_simulation import ExperimentSimulation


# ── Session state (in-process, per-session) ────────────────────────────────

_SIM: Optional[ExperimentSimulation] = None
_SIM_HISTORY: list[str] = []


def get_active_sim() -> ExperimentSimulation:
    """Return active simulation, creating a default one if needed."""
    global _SIM
    if _SIM is None:
        _SIM = ExperimentSimulation(model_type="emax", parameters={"E_max": 100, "ED50": 10})
    return _SIM


def set_active_sim(sim: ExperimentSimulation) -> None:
    global _SIM
    _SIM = sim


# ── Helpers ─────────────────────────────────────────────────────────────────

_STR_TO_BOOL = {"true": True, "false": False, "1": True, "0": False, "yes": True, "no": False}


def _parse_kv(kv: str) -> tuple[str, float]:
    """Parse 'key=value' into (key, float(value))."""
    if "=" not in kv:
        raise ValueError(f"Expected key=value, got '{kv}'")
    k, v = kv.strip().split("=", 1)
    k = k.strip()
    try:
        v = float(v)
    except ValueError:
        raise ValueError(f"Value for '{k}' must be numeric, got '{v}'")
    return k, v


def _parse_dose_list(doses_str: str) -> list[float]:
    """Parse comma/whitespace-separated dose list."""
    parts = re.split(r"[,\s]+", doses_str.strip())
    values = []
    for p in parts:
        if not p:
            continue
        try:
            values.append(float(p))
        except ValueError:
            raise ValueError(f"Invalid dose value '{p}' — must be numeric")
    if not values:
        raise ValueError("No dose values provided")
    return values


# ── Handlers ────────────────────────────────────────────────────────────────

_KNOWN_MODELS = {"linear", "emax", "exponential", "custom"}


def _handle_simulate_model(message: str, lowered: str) -> str:
    """Handle /simulate model [type] [key=value ...]"""
    global _SIM, _SIM_HISTORY

    # Strip prefix
    for prefix in ("/simulate model ", "simulate model ", "/sim model ", "sim model "):
        if lowered.startswith(prefix):
            body = lowered[len(prefix) :]
            break
    else:
        body = lowered

    body = body.strip()
    if not body:
        sim = get_active_sim()
        tmpl = sim.model_type
        return (
            f"Current model: {tmpl}\n"
            f"Formula: {sim._formula}\n"
            f"Parameters: {sim.parameters}\n"
            f"Noise SD: {sim.noise_sd}"
        )

    # First token is model type
    tokens = body.split()
    model_type = tokens[0].lower()
    if model_type not in _KNOWN_MODELS:
        return (
            f"Unknown model type '{model_type}'. "
            f"Available: {', '.join(_KNOWN_MODELS)}"
        )

    params: dict = {}
    noise_sd = 0.0
    seed = 42

    for tok in tokens[1:]:
        tok = tok.strip()
        if not tok:
            continue
        if tok.startswith("noise_sd=") or tok.startswith("noise="):
            _, val = tok.split("=", 1)
            try:
                noise_sd = float(val)
            except ValueError:
                return f"Invalid noise_sd value: {val}"
        elif tok.startswith("seed="):
            _, val = tok.split("=", 1)
            try:
                seed = int(val)
            except ValueError:
                return f"Invalid seed value: {val}"
        elif "=" in tok:
            k, v = _parse_kv(tok)
            params[k] = v
        else:
            return f"Unrecognized token '{tok}' — use key=value"

    # Set default params for known templates
    if model_type == "emax":
        params.setdefault("E_max", 100.0)
        params.setdefault("ED50", 10.0)
    elif model_type == "linear":
        params.setdefault("slope", 1.0)
        params.setdefault("intercept", 0.0)
    elif model_type == "exponential":
        params.setdefault("A", 100.0)
        params.setdefault("k", 0.1)

    _SIM = ExperimentSimulation(
        model_type=model_type,
        parameters=params,
        noise_sd=noise_sd,
        seed=seed,
    )
    _SIM_HISTORY.append(f"model={model_type}")

    template = _SIM._formula
    return (
        f"Model set: {model_type}\n"
        f"Formula: {template}\n"
        f"Parameters: {params}\n"
        f"Noise SD: {noise_sd}\n"
        f"Seed: {seed}"
    )


def _handle_simulate_predict(message: str, lowered: str) -> str:
    """Handle /simulate predict <x_values>"""
    global _SIM

    for prefix in (
        "/simulate predict ",
        "simulate predict ",
        "/sim predict ",
        "sim predict ",
    ):
        if lowered.startswith(prefix):
            body = lowered[len(prefix) :]
            break
    else:
        return "Usage: /simulate predict <doses> — e.g. /simulate predict 0,5,10,20,50"

    body = body.strip()
    if not body:
        return "Usage: /simulate predict <doses> — e.g. /simulate predict 0,5,10,20,50"

    try:
        x_values = _parse_dose_list(body)
    except ValueError as exc:
        return str(exc)

    sim = get_active_sim()
    result = sim.predict(x_values)

    # Store last x for sweep
    sim._last_x = list(x_values)

    return sim.format_predictions(result)


def _handle_simulate_sweep(message: str, lowered: str) -> str:
    """Handle /simulate sweep <param> from <a> to <b> [steps=N]"""
    global _SIM

    for prefix in (
        "/simulate sweep ",
        "simulate sweep ",
        "/sim sweep ",
        "sim sweep ",
    ):
        if lowered.startswith(prefix):
            body = lowered[len(prefix) :]
            break
    else:
        return (
            "Usage: /simulate sweep <param> from <start> to <end> [steps=N]\n"
            "Example: /simulate sweep ED50 from 5 to 20 steps=10"
        )

    # Parse: <param> from <a> to <b> [steps=N]
    body = body.strip()

    # Extract steps before regex (it's optional)
    steps_match = re.search(r"\bsteps=(\d+)\b", body, re.IGNORECASE)
    n_steps = int(steps_match.group(1)) if steps_match else 10
    if steps_match:
        body = re.sub(r"\bsteps=\d+\b", "", body, flags=re.IGNORECASE).strip()

    m = re.match(
        r"^\s*(\w+)\s+from\s+([\d.]+)\s+to\s+([\d.]+)\s*$",
        body,
        re.IGNORECASE,
    )
    if not m:
        return (
            "Usage: /simulate sweep <param> from <start> to <end> [steps=N]\n"
            "Example: /simulate sweep ED50 from 5 to 20 steps=10"
        )

    param_name = m.group(1)
    try:
        range_start = float(m.group(2))
        range_end = float(m.group(3))
    except ValueError:
        return f"Invalid range values: start={m.group(2)}, end={m.group(3)}"

    if range_start >= range_end:
        return f"range_start ({range_start}) must be < range_end ({range_end})"

    sim = get_active_sim()
    sim._last_x = getattr(sim, "_last_x", [0, 1, 2, 3, 4, 5])

    results = sim.sweep(
        parameter_name=param_name,
        range_start=range_start,
        range_end=range_end,
        n_steps=n_steps,
    )

    return sim.format_sweep(results)


def _handle_simulate_power(message: str, lowered: str) -> str:
    """Handle /simulate power <effect_size> [alpha=N] [power=M]"""
    global _SIM

    for prefix in (
        "/simulate power ",
        "simulate power ",
        "/sim power ",
        "sim power ",
    ):
        if lowered.startswith(prefix):
            body = lowered[len(prefix) :]
            break
    else:
        return "Usage: /simulate power <effect_size> [alpha=N] [power=M]"

    body = body.strip()
    if not body:
        return "Usage: /simulate power <effect_size> [alpha=N] [power=M]"

    tokens = body.split()
    try:
        effect_size = float(tokens[0])
    except ValueError:
        return f"Invalid effect_size '{tokens[0]}' — must be numeric"

    alpha = 0.05
    power_val = 0.8
    test_type = "t_independent"

    for tok in tokens[1:]:
        tok = tok.strip()
        if tok.startswith("alpha="):
            _, val = tok.split("=", 1)
            alpha = float(val)
        elif tok.startswith("power="):
            _, val = tok.split("=", 1)
            power_val = float(val)
        elif tok.startswith("test="):
            _, val = tok.split("=", 1)
            test_type = val

    try:
        sim = get_active_sim()
        result = sim.power_analysis(
            effect_size=effect_size,
            alpha=alpha,
            power=power_val,
            test_type=test_type,
        )
        return sim.format_power(result)
    except ImportError as exc:
        return f"Error: {exc}"
    except ValueError as exc:
        return f"Error: {exc}"


def _handle_experiment_design(message: str, lowered: str) -> str:
    """Handle /experiment design [args]"""
    global _SIM

    for prefix in (
        "/experiment design ",
        "experiment design ",
        "/experiment ",
        "experiment ",
    ):
        if lowered.startswith(prefix):
            body = lowered[len(prefix) :]
            break
    else:
        body = lowered

    # Parse optional arms / duration / endpoints
    arms = ["Placebo", "Drug"]
    duration_weeks = 12
    endpoints = ["Change in biomarker", "Safety profile"]

    parts = re.split(r"\s+", body.strip()) if body.strip() else []
    i = 0
    while i < len(parts):
        tok = parts[i]
        if tok in ("arms", "arm"):
            arms_str = parts[i + 1] if i + 1 < len(parts) else ""
            if "," in arms_str or "+" in arms_str:
                sep = "," if "," in arms_str else "+"
                arms = [a.strip() for a in arms_str.split(sep) if a.strip()]
            i += 2
        elif tok in ("duration", "weeks"):
            try:
                duration_weeks = int(parts[i + 1])
                i += 2
            except (IndexError, ValueError):
                return f"Invalid duration: {parts[i+1] if i+1 < len(parts) else 'missing'}"
        elif tok in ("endpoint", "endpoints", "ep"):
            ep_val = parts[i + 1] if i + 1 < len(parts) else ""
            if ep_val:
                endpoints = [e.strip() for e in re.split(r"[,+]", ep_val) if e.strip()]
            i += 2
        else:
            i += 1

    trial = ExperimentSimulation.mock_trial_design(
        arms=arms,
        duration_weeks=duration_weeks,
        endpoints=endpoints,
        sample_size=64,
        dropout_rate=0.1,
    )
    return ExperimentSimulation.format_trial_design(trial)


# ── Top-level dispatcher ────────────────────────────────────────────────────

def handle_simulation_command(message: str, lowered: str) -> str:
    """Route simulation commands.

    Handles:
      /simulate model|predict|sweep|power [...]
      /experiment design [...]
    """
    global _SIM

    if (
        lowered.startswith("/simulate model ")
        or lowered.startswith("simulate model ")
        or lowered.startswith("/sim model ")
        or lowered.startswith("sim model ")
        or lowered == "/simulate model"
        or lowered == "simulate model"
    ):
        return _handle_simulate_model(message, lowered)

    if (
        lowered.startswith("/simulate predict ")
        or lowered.startswith("simulate predict ")
        or lowered.startswith("/sim predict ")
        or lowered.startswith("sim predict ")
    ):
        return _handle_simulate_predict(message, lowered)

    if (
        lowered.startswith("/simulate sweep ")
        or lowered.startswith("simulate sweep ")
        or lowered.startswith("/sim sweep ")
        or lowered.startswith("sim sweep ")
    ):
        return _handle_simulate_sweep(message, lowered)

    if (
        lowered.startswith("/simulate power ")
        or lowered.startswith("simulate power ")
        or lowered.startswith("/sim power ")
        or lowered.startswith("sim power ")
    ):
        return _handle_simulate_power(message, lowered)

    if (
        lowered.startswith("/experiment")
        or lowered.startswith("experiment ")
    ):
        return _handle_experiment_design(message, lowered)

    # Unknown — show usage
    return (
        "Simulation commands:\n"
        "  /simulate model [linear|emax|exponential|custom] [key=value...]\n"
        "  /simulate predict <doses>          — predict outcomes\n"
        "  /simulate sweep <p> from <a> to <b> [steps=N]\n"
        "  /simulate power <d> [alpha=N] [power=M]\n"
        "  /experiment design [arms=...] [duration=N] [endpoint=...]\n\n"
        "[SIMULATION MODE – Not real data]"
    )
