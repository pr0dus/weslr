#!/usr/bin/env python3
"""Weslr CLI - Entry point with subcommand routing.

Uses modular command architecture for maintainability.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

# Add workspace to path
WORKSPACE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE_DIR))



def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="weslr",
        description="Weslr - Entity intelligence system"
    )

    # Add global arguments
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # Create subparsers and register commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Load all command modules to register their subcommands
    commands_dir = WORKSPACE_DIR / "commands"
    for cmd_file in commands_dir.glob("*.py"):
        if cmd_file.name.startswith("_") or cmd_file.name == "__init__.py":
            continue  # Skip __init__.py and other private files

        module_name = cmd_file.stem
        try:
            module = importlib.import_module(f"commands.{module_name}")
            if hasattr(module, "register_commands"):
                module.register_commands(subparsers)
        except ImportError as e:
            print(f"Warning: Failed to load commands.{module_name}: {e}")

    # Handle commands
    args = parser.parse_args()

    if args.version:
        print("Weslr 0.1.0 (Alpha)")
        return

    if not args.command:
        # No command provided, show help
        parser.print_help()
        return

    # Execute command
    cmd_func = getattr(args, "func", None)
    if cmd_func:
        cmd_func(args)
    else:
        print(f"Command '{args.command}' not implemented")
        sys.exit(1)


if __name__ == "__main__":
    main()
