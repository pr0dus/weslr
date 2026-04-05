"""Evidence-gated APIs for external facts (time, weather)."""
from __future__ import annotations

import json
import socket
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def get_system_time() -> dict[str, Any]:
    """Return current system time/date as evidence."""
    now = datetime.now()
    return {
        "kind": "time_evidence",
        "timestamp": int(time.time()),
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": time.tzname[0],
        "source": "system",
    }


def get_weather(location: str | None = None) -> dict[str, Any]:
    """Return weather for location using wttr.in (no API key needed).
    
    If location is None, tries to infer from environment or returns error.
    """
    if not location:
        # Try to get location from environment
        location = "auto"
    
    try:
        # Use wttr.in for weather (no API key required)
        url = f"https://wttr.in/{location.replace(' ', '+')}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "Weslr/0.8"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        # Extract current weather
        current = data.get("current_condition", [{}])[0]
        location_info = data.get("nearest_area", [{}])[0] if data.get("nearest_area") else {}
        
        return {
            "kind": "weather_evidence",
            "location": location_info.get("areaName", [{}])[0].get("value", "unknown") if location_info else location,
            "temp_c": current.get("temp_C"),
            "temp_f": current.get("temp_F"),
            "weather_desc": current.get("weatherDesc", [{}])[0].get("value", "unknown"),
            "humidity": current.get("humidity"),
            "pressure": current.get("pressure"),
            "source": "wttr.in",
            "fetched_at": int(time.time()),
        }
    except socket.timeout:
        return {"kind": "error", "error": "timeout", "source": "weather_api"}
    except Exception as e:
        return {"kind": "error", "error": str(e)[:200], "source": "weather_api"}


def verify_evidence_provider(provider: str) -> bool:
    """Check if evidence provider is available."""
    if provider == "system_time":
        return True
    if provider == "weather":
        try:
            # Test connectivity to wttr.in
            socket.create_connection(("wttr.in", 443), timeout=3)
            return True
        except Exception:
            return False
    return False


def evidence_cache_path() -> Path:
    """Return path to evidence cache directory."""
    return Path.home() / ".weslr_evidence_cache"


def evidence_cache_file(evidence_type: str) -> Path:
    """Return path to cached evidence file."""
    return evidence_cache_path() / f"{evidence_type}.json"


def get_cached_evidence(evidence_type: str) -> dict[str, Any] | None:
    """Get cached evidence if available and not expired."""
    cache_file = evidence_cache_file(evidence_type)
    if not cache_file.exists():
        return None
    
    try:
        data = json.loads(cache_file.read_text())
        # Expire after 5 minutes
        if time.time() - data.get("cached_at", 0) > 300:
            return None
        return data
    except Exception:
        return None


def cache_evidence(evidence_type: str, evidence: dict[str, Any]) -> None:
    """Cache evidence for reuse."""
    cache_file = evidence_cache_file(evidence_type)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    evidence["cached_at"] = int(time.time())
    evidence["source"] = f"cached_{evidence.get('source', 'unknown')}"
    cache_file.write_text(json.dumps(evidence, ensure_ascii=False))
