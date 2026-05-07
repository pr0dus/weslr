"""
weslr/auto_refinement_config.py

Controlled global auto-apply configuration.
Stored at ~/.weslr/auto_refinement_config.json (project-local: .weslr_state/)

All fields:
- global_auto_apply_enabled: bool — master kill-switch for auto-apply
- enabled_zones: list[str] — which zones may auto-apply (default: ["green"])
- max_auto_applications_per_day: int — rate limit
- require_audit_log: bool — must have writable audit file
- require_rollback_snapshot: bool — must create snapshot before apply
- require_simulation_pass: bool — simulation must pass
- require_regression_pass: bool — regression must pass
- created_at / updated_at
"""

from dataclasses import dataclass, asdict
from typing import Optional
import json
import os

DEFAULT_STORE_DIR = os.path.expanduser("~/.weslr")
PROJECT_STORE_DIR = ".weslr_state"

DEFAULT_CONFIG = {
    "global_auto_apply_enabled": False,
    "enabled_zones": ["green"],
    "max_auto_applications_per_day": 1,
    "require_audit_log": True,
    "require_rollback_snapshot": True,
    "require_simulation_pass": True,
    "require_regression_pass": True,
    "created_at": None,
    "updated_at": None,
}


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _store_path(explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit
    if os.path.exists(PROJECT_STORE_DIR):
        return os.path.join(PROJECT_STORE_DIR, "auto_refinement_config.json")
    os.makedirs(DEFAULT_STORE_DIR, exist_ok=True)
    return os.path.join(DEFAULT_STORE_DIR, "auto_refinement_config.json")


@dataclass
class AutoRefinementConfig:
    global_auto_apply_enabled: bool = False
    enabled_zones: list[str] = None
    max_auto_applications_per_day: int = 1
    require_audit_log: bool = True
    require_rollback_snapshot: bool = True
    require_simulation_pass: bool = True
    require_regression_pass: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if self.enabled_zones is None:
            self.enabled_zones = ["green"]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "AutoRefinementConfig":
        return cls(**d)

    def save(self, path: Optional[str] = None) -> None:
        p = _store_path(path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        self.updated_at = _now_iso()
        if self.created_at is None:
            self.created_at = self.updated_at
        with open(p, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "AutoRefinementConfig":
        p = _store_path(path)
        if not os.path.exists(p):
            cfg = cls()
            cfg.created_at = _now_iso()
            cfg.updated_at = _now_iso()
            return cfg
        with open(p) as f:
            return cls.from_dict(json.load(f))

    def is_auto_enabled_for(self, zone: str) -> bool:
        return (
            self.global_auto_apply_enabled
            and zone in self.enabled_zones
        )

    def can_auto_apply(
        self,
        zone: str,
        simulation_pass: bool,
        regression_pass: bool,
        audit_log_present: bool,
        rollback_possible: bool,
        daily_count: int,
    ) -> tuple[bool, list[str]]:
        """Returns (allowed, reasons_blocked)."""
        reasons = []
        if not self.global_auto_apply_enabled:
            reasons.append("global_auto_apply_enabled is False")
        if zone not in self.enabled_zones:
            reasons.append(f"zone={zone} not in enabled_zones={self.enabled_zones}")
        if self.require_simulation_pass and not simulation_pass:
            reasons.append("require_simulation_pass but simulation_pass=False")
        if self.require_regression_pass and not regression_pass:
            reasons.append("require_regression_pass but regression_pass=False")
        if self.require_audit_log and not audit_log_present:
            reasons.append("require_audit_log but audit log not present")
        if self.require_rollback_snapshot and not rollback_possible:
            reasons.append("require_rollback_snapshot but rollback not possible")
        if daily_count >= self.max_auto_applications_per_day:
            reasons.append(f"daily count {daily_count} >= max {self.max_auto_applications_per_day}")
        return (len(reasons) == 0, reasons)


def load_config(path: Optional[str] = None) -> AutoRefinementConfig:
    return AutoRefinementConfig.load(path)


def save_config(cfg: AutoRefinementConfig, path: Optional[str] = None) -> None:
    cfg.save(path)