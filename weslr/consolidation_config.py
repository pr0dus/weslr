"""
WESLR Consolidation Config — V2

Loads and saves .weslr/consolidation_config.json.
Safe to import; no filesystem writes at module load time.
"""

from __future__ import annotations

import json
import os
import pathlib

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "consolidation_auto_enabled": False,       # master kill-switch
    "green_zone_auto_promotion_enabled": False, # green-zone auto-promote
    "enabled_zones": ["green"],               # which zones may auto-apply
    "require_provenance": True,                # reject candidates without provenance
    "require_audit_log": True,                # write audit event for every promotion
    "allowed_green_destinations": [
        "continuity_summary",
        "attention_memory",
        "digest_archive_marker",
        "procedural_note",
    ],
}

_CONFIG_PATH = pathlib.Path(os.environ.get(
    "WESLR_ROOT", pathlib.Path.home() / ".weslr"
)) / "consolidation_config.json"


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

class ConsolidationConfig:
    """Loaded configuration. All booleans explicitly typed for clarity."""

    __slots__ = (
        "consolidation_auto_enabled",
        "green_zone_auto_promotion_enabled",
        "enabled_zones",
        "require_provenance",
        "require_audit_log",
        "allowed_green_destinations",
    )

    def __init__(
        self,
        consolidation_auto_enabled: bool = False,
        green_zone_auto_promotion_enabled: bool = False,
        enabled_zones: list[str] | None = None,
        require_provenance: bool = True,
        require_audit_log: bool = True,
        allowed_green_destinations: list[str] | None = None,
    ):
        self.consolidation_auto_enabled = consolidation_auto_enabled
        self.green_zone_auto_promotion_enabled = green_zone_auto_promotion_enabled
        self.enabled_zones = enabled_zones if enabled_zones is not None else ["green"]
        self.require_provenance = require_provenance
        self.require_audit_log = require_audit_log
        self.allowed_green_destinations = (
            allowed_green_destinations
            if allowed_green_destinations is not None
            else _DEFAULTS["allowed_green_destinations"][:]
        )

    @classmethod
    def from_dict(cls, d: dict) -> "ConsolidationConfig":
        return cls(
            consolidation_auto_enabled=bool(d.get("consolidation_auto_enabled", False)),
            green_zone_auto_promotion_enabled=bool(d.get("green_zone_auto_promotion_enabled", False)),
            enabled_zones=list(d.get("enabled_zones", ["green"])),
            require_provenance=bool(d.get("require_provenance", True)),
            require_audit_log=bool(d.get("require_audit_log", True)),
            allowed_green_destinations=list(
                d.get("allowed_green_destinations", _DEFAULTS["allowed_green_destinations"])
            ),
        )

    def to_dict(self) -> dict:
        return {s: getattr(self, s) for s in self.__slots__}

    def is_auto_enabled_for(self, zone: str) -> bool:
        """Return True if auto-promotion is enabled for the given zone."""
        return (
            self.consolidation_auto_enabled
            and self.green_zone_auto_promotion_enabled
            and zone in self.enabled_zones
        )

    def can_auto_apply(
        self, zone: str, destination: str, provenance: list | None = None
    ) -> tuple[bool, list[str]]:
        """
        Return (allowed, blocked_reasons) for auto-promoting a candidate.

        Checks:
        1. Master switch
        2. Green zone toggle
        3. Zone in enabled_zones
        4. Destination in allowed_green_destinations
        5. Provenance present if require_provenance
        """
        reasons: list[str] = []

        if not self.consolidation_auto_enabled:
            reasons.append("consolidation_auto_enabled is False")
        if not self.green_zone_auto_promotion_enabled:
            reasons.append("green_zone_auto_promotion_enabled is False")
        if zone not in self.enabled_zones:
            reasons.append(f"zone={zone} not in enabled_zones={self.enabled_zones}")
        if destination not in self.allowed_green_destinations:
            reasons.append(
                f"destination={destination} not in allowed_green_destinations"
            )
        if self.require_provenance and (not provenance or len(provenance) == 0):
            reasons.append("provenance missing (require_provenance=True)")

        return (len(reasons) == 0, reasons)

    def enable(self) -> None:
        """Enable consolidation auto-promotion (sets both flags)."""
        self.consolidation_auto_enabled = True
        self.green_zone_auto_promotion_enabled = True

    def disable(self) -> None:
        """Disable consolidation auto-promotion (clears both flags)."""
        self.consolidation_auto_enabled = False
        self.green_zone_auto_promotion_enabled = False


# ---------------------------------------------------------------------------
# Load / Save
# ---------------------------------------------------------------------------

def load_config(path: str | None = None) -> ConsolidationConfig:
    """Load config from JSON file. Returns defaults if file missing."""
    p = pathlib.Path(path) if path else _CONFIG_PATH
    if not p.exists():
        return ConsolidationConfig()
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return ConsolidationConfig.from_dict(d)
    except (OSError, json.JSONDecodeError):
        return ConsolidationConfig()


def save_config(cfg: ConsolidationConfig, path: str | None = None) -> None:
    """Save config to JSON file. Creates parent directories."""
    p = pathlib.Path(path) if path else _CONFIG_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cfg.to_dict(), f, indent=2)
        f.write("\n")
