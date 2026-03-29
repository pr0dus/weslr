"""Commands registry for Weslr.

Central registry for all command modules, enabling easy discovery and routing.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional

COMMANDS_DIR = Path(__file__).resolve().parent


def get_command_modules() -> List[str]:
    """Get list of available command modules."""
    modules = []
    for importer, modname, ispkg in pkgutil.iter_modules([str(COMMANDS_DIR)]):
        if not ispkg:  # Skip subdirectories
            modules.append(modname)
    return sorted(modules)


def load_command_module(module_name: str) -> Optional[Any]:
    """Load a command module by name."""
    try:
        return importlib.import_module(f"commands.{module_name}")
    except ImportError as e:
        print(f"Failed to import commands.{module_name}: {e}")
        return None


def get_command_handlers() -> Dict[str, Callable]:
    """Get all command handlers from registered modules."""
    handlers = {}
    modules = get_command_modules()

    for module_name in modules:
        module = load_command_module(module_name)
        if module:
            # Look for cmd_* functions in module
            for name in dir(module):
                if name.startswith("cmd_"):
                    handlers[name] = getattr(module, name)

    return handlers


def register_command(module_name: str, command_name: str):
    """Register a command from a module."""
    module = load_command_module(module_name)
    if module and hasattr(module, command_name):
        return getattr(module, command_name)
    return None


# Import all command modules to register them
def init():
    """Initialize all command modules."""
    for module_name in get_command_modules():
        load_command_module(module_name)


# Initialize on import
init()
