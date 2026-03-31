"""Weslr Self-Improvement Observation Layer.

Records repeated weaknesses in Weslr's own behavior.
Used by the self-improvement proposal engine.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


OBSERVATIONS_FILE = "self_improvement_observations.json"
BASE_DIR = Path(__file__).resolve().parent


def get_observations_path() -> Path:
    """Get path to observations storage file."""
    return BASE_DIR / OBSERVATIONS_FILE


def load_observations() -> list[dict]:
    """Load all observations from storage."""
    path = get_observations_path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_observations(observations: list[dict]) -> None:
    """Save observations to storage."""
    path = get_observations_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(observations, f, indent=2)


def record_observation(
    type: str,
    pattern: str,
    source_layer: str,
    count: int = 1,
) -> dict:
    """Record a new observation of repeated weakness.

    Args:
        type: One of allowed observation types
        pattern: Description of the repeated pattern
        source_layer: Which layer of the system (e.g., "dialogue", "interpretation")
        count: How many times this pattern was observed

    Returns:
        dict with observation details or error
    """
    allowed_types = [
        "repeated_fallback",
        "repeated_generic_response",
        "repeated_user_dissatisfaction",
        "repeated_route_failure",
        "repeated_concept_mismatch",
    ]

    if type not in allowed_types:
        return {
            "ok": False,
            "error": f"Invalid observation type. Must be one of: {allowed_types}",
        }

    now_ts = int(time.time())
    observation_id = f"obs-{now_ts}"

    observation = {
        "id": observation_id,
        "type": type,
        "pattern": pattern,
        "count": count,
        "last_seen": now_ts,
        "first_seen": now_ts,
        "source_layer": source_layer,
        "created_at": now_ts,
    }

    # Load existing, append, save
    observations = load_observations()
    observations.append(observation)
    save_observations(observations)

    return {
        "ok": True,
        "observation_id": observation_id,
        "type": type,
        "pattern": pattern,
        "source_layer": source_layer,
        "count": count,
        "recorded_at": now_ts,
    }


def list_observations(
    type: str | None = None,
    source_layer: str | None = None,
    limit: int = 50,
) -> dict:
    """List observations, optionally filtered.

    Args:
        type: Filter by observation type
        source_layer: Filter by source layer
        limit: Maximum results to return

    Returns:
        dict with observations list and metadata
    """
    observations = load_observations()

    # Apply filters
    if type:
        observations = [o for o in observations if o.get("type") == type]
    if source_layer:
        observations = [o for o in observations if o.get("source_layer") == source_layer]

    # Sort by most recent first
    observations = sorted(observations, key=lambda o: o.get("last_seen", 0), reverse=True)

    # Apply limit
    observations = observations[:limit]

    return {
        "ok": True,
        "total": len(observations),
        "limit": limit,
        "observations": observations,
    }


def get_repeated_fallbacks(limit: int = 10) -> list[dict]:
    """Convenience function to get repeated fallback observations."""
    result = list_observations(type="repeated_fallback", limit=limit)
    return result.get("observations", [])
