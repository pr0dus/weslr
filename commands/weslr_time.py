"""Commands for Weslr Time System."""

from __future__ import annotations

import sys
from pathlib import Path

# Add workspace to path
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR))

from commands import register_command
from weslr_time import get_weslr_time, cmd_weslr_time, cmd_weslr_time_set_timezone, register_commands, TIMEZONES


def register_commands(subparsers):
    """Register Weslr time commands."""
    parser = subparsers.add_parser("weslr-time", help="Weslr time system status and configuration")
    parser.add_argument("--timezone", "-tz", help="Set timezone")
    parser.add_argument("--list", "-l", action="store_true", help="List available timezones")
    parser.add_argument("--reset-ticks", action="store_true", help="Reset only tick count (keep clock running)")
    parser.set_defaults(func=handle_weslr_time)


def handle_weslr_time(args):
    """Handle weslr time command."""
    if args.list:
        print("Available timezones:")
        for tz in TIMEZONES:
            print(f"  - {tz}")
        return
    
    if args.timezone:
        cmd_weslr_time_set_timezone(args)
        return
    
    if args.reset_ticks:
        get_weslr_time().reset_ticks_only()
        print("Ticks reset to 0. Clock continues running.")
        return
    
    cmd_weslr_time(args)


if __name__ == "__main__":
    import argparse
    args = argparse.Namespace(list=False, timezone=None, reset_ticks=False)
    handle_weslr_time(args)
