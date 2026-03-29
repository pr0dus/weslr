"""Weslr Time System - Persistent clock with timezone support.

Features:
- Independent clock for Weslr's internal time tracking
- Timezone-aware (default: Europe/Berlin)
- Synced with system time on startup
- Persists across resets (only ticks reset on full reset)
- Configurable timezone and DST settings
"""

from __future__ import annotations

import time
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

# Base directory
BASE_DIR = Path(__file__).resolve().parent
WESLR_TIME_PATH = BASE_DIR / "weslr_time_state.json"
WESLR_TIME_CONFIG_PATH = BASE_DIR / "weslr_time_config.json"


# ============================================================================
# TIMEZONE CONFIGURATION
# ============================================================================

TIMEZONES = {
    "Europe/Berlin": {
        "name": "Central European Time",
        "code": "CET",
        "offset_hours": 1,  # CET is UTC+1
        "offset_hours_dst": 2,  # CEST is UTC+2
        "dst_start": "last_sunday_march",  # Last Sunday in March
        "dst_end": "last_sunday_october",   # Last Sunday in October
    },
    "Europe/Paris": {
        "name": "Central European Time",
        "code": "CET",
        "offset_hours": 1,
        "offset_hours_dst": 2,
        "dst_start": "last_sunday_march",
        "dst_end": "last_sunday_october",
    },
    "Europe/London": {
        "name": "Western European Time",
        "code": "GMT",
        "offset_hours": 0,
        "offset_hours_dst": 1,
        "dst_start": "last_sunday_march",
        "dst_end": "last_sunday_october",
    },
    "US/Eastern": {
        "name": "Eastern Time",
        "code": "EST",
        "offset_hours": -5,
        "offset_hours_dst": -4,
        "dst_start": "second_sunday_march",
        "dst_end": "first_sunday_november",
    },
    "UTC": {
        "name": "Coordinated Universal Time",
        "code": "UTC",
        "offset_hours": 0,
        "offset_hours_dst": 0,
        "dst_start": None,
        "dst_end": None,
    },
}


def get_current_dst_offset() -> int:
    """Get current DST offset for Europe/Berlin."""
    now = datetime.now(timezone.utc)
    
    # Check if DST is in effect (CET vs CEST)
    # DST in EU: last Sunday in March to last Sunday in October
    year = now.year
    
    # Find last Sunday in March
    last_march_day = datetime(year, 3, 31, tzinfo=timezone.utc)
    while last_march_day.weekday() != 6:  # 6 = Sunday
        last_march_day -= timedelta(days=1)
    
    # Find last Sunday in October
    last_october_day = datetime(year, 10, 31, tzinfo=timezone.utc)
    while last_october_day.weekday() != 6:
        last_october_day -= timedelta(days=1)
    
    # Check if current date is in DST period
    if last_march_day <= now < last_october_day:
        return 2  # CEST (UTC+2)
    else:
        return 1  # CET (UTC+1)


def get_timezone_offset(tz_name: str = "Europe/Berlin") -> int:
    """Get timezone offset in hours (including DST if applicable)."""
    if tz_name not in TIMEZONES:
        return 0
    
    tz_config = TIMEZONES[tz_name]
    
    if tz_name.startswith("Europe/") or tz_name.startswith("UTC"):
        # Use DST-aware calculation
        return tz_config["offset_hours_dst"] if get_current_dst_offset() > 1 else tz_config["offset_hours"]
    
    return tz_config["offset_hours"]


def get_local_datetime(tz_name: str = "Europe/Berlin") -> datetime:
    """Get current datetime in specified timezone."""
    utc_now = datetime.now(timezone.utc)
    offset_hours = get_timezone_offset(tz_name)
    return utc_now + timedelta(hours=offset_hours)


def format_time(dt: datetime, tz_name: str = "Europe/Berlin") -> str:
    """Format datetime for display."""
    tz_config = TIMEZONES.get(tz_name, {})
    code = tz_config.get("code", "UTC")
    return dt.strftime(f"%Y-%m-%d %H:%M:%S {code}")


# ============================================================================
# WESLR TIME STATE
# ============================================================================

def get_default_weslr_time_config() -> Dict[str, Any]:
    """Get default Weslr time configuration."""
    return {
        "timezone": "Europe/Berlin",
        "auto_sync": True,
        "start_time": int(time.time()),
        "time_initialized": True,
        "config_version": "1.0",
    }


def load_weslr_time_config() -> Dict[str, Any]:
    """Load Weslr time configuration."""
    if WESLR_TIME_CONFIG_PATH.exists():
        try:
            with open(WESLR_TIME_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Merge with defaults
                default = get_default_weslr_time_config()
                default.update(config)
                return default
        except Exception:
            pass
    
    config = get_default_weslr_time_config()
    save_weslr_time_config(config)
    return config


def save_weslr_time_config(config: Dict[str, Any]) -> None:
    """Save Weslr time configuration."""
    with open(WESLR_TIME_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def load_weslr_time_state() -> Dict[str, Any]:
    """Load Weslr time state from disk."""
    if WESLR_TIME_PATH.exists():
        try:
            with open(WESLR_TIME_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    
    config = load_weslr_time_config()
    state = {
        "start_time": config.get("start_time", int(time.time())),
        "last_sync": int(time.time()),
        "timezone": config.get("timezone", "Europe/Berlin"),
        "ticks_elapsed": 0,
        "current_datetime": format_time(get_local_datetime(config.get("timezone", "Europe/Berlin")), config.get("timezone", "Europe/Berlin")),
        "config": config,
    }
    return state


def save_weslr_time_state(state: Dict[str, Any]) -> None:
    """Save Weslr time state to disk."""
    state["last_sync"] = int(time.time())
    with open(WESLR_TIME_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ============================================================================
# WESLR TIME CLASS
# ============================================================================

class WeslrTime:
    """Weslr's persistent time management system."""
    
    def __init__(self):
        self.config = load_weslr_time_config()
        self.state = load_weslr_time_state()
        self._current_time = self.state.get("start_time", int(time.time()))
        
        # Ensure timezone is set
        if "timezone" not in self.state:
            self.state["timezone"] = self.config.get("timezone", "Europe/Berlin")
    
    def get_current_time(self) -> int:
        """Get current Unix timestamp."""
        if self.config.get("auto_sync", True):
            return int(time.time())
        return self._current_time
    
    def get_current_datetime(self) -> datetime:
        """Get current datetime object."""
        return get_local_datetime(self.state.get("timezone", "Europe/Berlin"))
    
    def format_time(self, dt: Optional[datetime] = None) -> str:
        """Format datetime for display."""
        if dt is None:
            dt = self.get_current_datetime()
        return format_time(dt, self.state.get("timezone", "Europe/Berlin"))
    
    def get_timezone(self) -> str:
        """Get current timezone."""
        return self.state.get("timezone", "Europe/Berlin")
    
    def get_year(self) -> int:
        """Get current year in Weslr's time."""
        return self.get_current_datetime().year
    
    def get_tick_count(self) -> int:
        """Get elapsed ticks since start."""
        return self.state.get("ticks_elapsed", 0)
    
    def increment_tick(self) -> int:
        """Increment tick count and return new value."""
        self.state["ticks_elapsed"] = self.state.get("ticks_elapsed", 0) + 1
        self.save()
        return self.state["ticks_elapsed"]
    
    def save(self) -> None:
        """Save state to disk."""
        save_weslr_time_state(self.state)
    
    def reset_ticks_only(self) -> None:
        """Reset tick count but keep clock running."""
        self.state["ticks_elapsed"] = 0
        self.save()
    
    def reset_full(self) -> None:
        """Full reset (called on /reset)."""
        self.state = {
            "start_time": self.config.get("start_time", int(time.time())),
            "last_sync": int(time.time()),
            "timezone": self.config.get("timezone", "Europe/Berlin"),
            "ticks_elapsed": 0,
            "current_datetime": format_time(get_local_datetime(self.config.get("timezone", "Europe/Berlin")), self.config.get("timezone", "Europe/Berlin")),
            "config": self.config,
        }
        self.save()


# Global instance
_weslr_time: Optional[WeslrTime] = None


def get_weslr_time() -> WeslrTime:
    """Get or create the global WeslrTime instance."""
    global _weslr_time
    if _weslr_time is None:
        _weslr_time = WeslrTime()
    return _weslr_time


def reset_weslr_time_ticks() -> None:
    """Reset only tick count, keep clock running."""
    get_weslr_time().reset_ticks_only()


# ============================================================================
# CLI COMMANDS
# ============================================================================

def cmd_weslr_time(args) -> None:
    """Display current Weslr time and state."""
    wt = get_weslr_time()
    
    dt = wt.get_current_datetime()
    current_time = wt.format_time(dt)
    year = wt.get_year()
    timezone_name = wt.get_timezone()
    tick_count = wt.get_tick_count()
    
    print(f"Weslr Time System Status:")
    print(f"  Current Time: {current_time}")
    print(f"  Year: {year}")
    print(f"  Timezone: {timezone_name}")
    print(f"  Ticks Elapsed: {tick_count}")
    print()
    
    # DST info
    offset = get_timezone_offset(timezone_name)
    dst = "Yes (CEST)" if offset > 1 else "No (CET)"
    print(f"  DST Active: {dst} (UTC+{offset})")


def cmd_weslr_time_set_timezone(args) -> None:
    """Set Weslr's timezone."""
    new_tz = args.timezone
    if new_tz not in TIMEZONES:
        print(f"Unknown timezone: {new_tz}")
        print(f"Available: {', '.join(TIMEZONES.keys())}")
        return
    
    wt = get_weslr_time()
    wt.state["timezone"] = new_tz
    wt.save()
    
    dt = wt.get_current_datetime()
    print(f"Timezone set to {new_tz} ({TIMEZONES[new_tz]['name']})")
    print(f"Current time: {wt.format_time(dt)}")


def register_commands(subparsers) -> None:
    """Register Weslr time commands."""
    parser = subparsers.add_parser("time", help="Weslr time system")
    parser.add_argument("--timezone", "-tz", help="Set timezone")
    parser.add_argument("--list", "-l", action="store_true", help="List available timezones")
    parser.set_defaults(func=handle_weslr_time)


def handle_weslr_time(args) -> None:
    """Handle weslr time command."""
    if args.list:
        print("Available timezones:")
        for tz in TIMEZONES:
            print(f"  - {tz}")
        return
    
    if args.timezone:
        cmd_weslr_time_set_timezone(args)
        return
    
    cmd_weslr_time(args)


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Weslr Time System")
    parser.add_argument("--timezone", "-tz", help="Set timezone")
    parser.add_argument("--list", "-l", action="store_true", help="List timezones")
    args = parser.parse_args()
    
    if args.list:
        print("Available timezones:")
        for tz in TIMEZONES:
            print(f"  - {tz}")
    elif args.timezone:
        cmd_weslr_time_set_timezone(args)
    else:
        cmd_weslr_time(args)
