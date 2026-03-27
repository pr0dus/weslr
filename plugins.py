# plugins.py - Plugin system for CircleForge
"""
Plugin system to load external addon modules dynamically.
This allows CircleForge to extend its capabilities without
modifying core code.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from config import BASE_DIR


# ============================================================================
# PLUGIN SYSTEM CONFIGURATION
# ============================================================================

PLUGINS_DIR = BASE_DIR / "plugins"
PLUGINS_CONFIG_PATH = BASE_DIR / "plugins_config.json"
PLUGINS_STATE_PATH = BASE_DIR / "plugins_state.json"


def get_plugins_dir() -> Path:
    """Get the plugins directory, creating it if needed."""
    if not PLUGINS_DIR.exists():
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    return PLUGINS_DIR


def load_plugins_config() -> Dict[str, Any]:
    """Load plugins configuration."""
    if PLUGINS_CONFIG_PATH.exists():
        try:
            with open(PLUGINS_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "plugins": {},
        "enabled": [],
        "disabled": [],
    }


def save_plugins_config(config: Dict[str, Any]) -> None:
    """Save plugins configuration."""
    with open(PLUGINS_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def load_plugins_state() -> Dict[str, Any]:
    """Load plugin state."""
    if PLUGINS_STATE_PATH.exists():
        try:
            with open(PLUGINS_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "loaded_at": 0,
        "plugins": {},
    }


def save_plugins_state(state: Dict[str, Any]) -> None:
    """Save plugin state."""
    with open(PLUGINS_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ============================================================================
# PLUGIN DISCOVERY
# ============================================================================

def discover_plugins() -> List[Dict[str, Any]]:
    """Find all plugin files in the plugins directory."""
    plugins = []
    
    plugins_dir = get_plugins_dir()
    if not plugins_dir.exists():
        return plugins
    
    for file_path in plugins_dir.glob("*.py"):
        if file_path.name == "__init__.py":
            continue
        
        plugins.append({
            "name": file_path.stem,
            "file": str(file_path),
            "status": "discovered",
            "discovered_at": int(time.time()),
        })
    
    return plugins


def discover_packages() -> List[Dict[str, Any]]:
    """Find all plugin packages (directories with __init__.py)."""
    packages = []
    
    plugins_dir = get_plugins_dir()
    if not plugins_dir.exists():
        return packages
    
    for item in plugins_dir.iterdir():
        if item.is_dir():
            init_file = item / "__init__.py"
            if init_file.exists():
                packages.append({
                    "name": item.name,
                    "path": str(item),
                    "status": "package",
                    "discovered_at": int(time.time()),
                })
    
    return packages


# ============================================================================
# PLUGIN LOADING
# ============================================================================

def load_plugin(name: str, file_path: str = None) -> Optional[Dict[str, Any]]:
    """Load a plugin from file."""
    if file_path is None:
        file_path = str(get_plugins_dir() / f"{name}.py")
    
    plugin_path = Path(file_path)
    if not plugin_path.exists():
        return {"error": f"Plugin file not found: {file_path}"}
    
    try:
        # Create module spec
        spec = importlib.util.spec_from_file_location(name, file_path)
        if spec is None or spec.loader is None:
            return {"error": f"Could not create module spec for {name}"}
        
        # Load module
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        
        # Get plugin metadata
        plugin_info = getattr(module, "PLUGIN_INFO", {})
        plugin_info["name"] = name
        plugin_info["file"] = file_path
        plugin_info["loaded_at"] = int(time.time())
        plugin_info["status"] = "loaded"
        
        # Get functions
        functions = []
        for attr in dir(module):
            if attr.startswith("_"):
                continue
            obj = getattr(module, attr)
            if callable(obj) and not isinstance(obj, type):
                functions.append(attr)
        
        plugin_info["functions"] = functions
        plugin_info["status"] = "loaded"
        
        return {"ok": True, "plugin": plugin_info}
    
    except Exception as e:
        return {"error": str(e), "status": "error"}


def load_plugins_from_config() -> Dict[str, Any]:
    """Load all plugins from configuration."""
    config = load_plugins_config()
    enabled = config.get("enabled", [])
    
    results = {
        "loaded": [],
        "failed": [],
        "skipped": [],
    }
    
    for plugin_name in enabled:
        file_path = str(get_plugins_dir() / f"{plugin_name}.py")
        result = load_plugin(plugin_name, file_path)
        
        if result.get("ok"):
            results["loaded"].append(result["plugin"])
        else:
            results["failed"].append({
                "plugin": plugin_name,
                "error": result.get("error", "unknown"),
            })
    
    return results


def enable_plugin(name: str) -> Dict[str, Any]:
    """Enable a plugin in configuration."""
    config = load_plugins_config()
    
    if name not in config.get("plugins", {}):
        config.setdefault("plugins", {})[name] = {
            "enabled": True,
            "enabled_at": int(time.time()),
        }
    else:
        config["plugins"][name]["enabled"] = True
        config["plugins"][name]["enabled_at"] = int(time.time())
    
    # Remove from disabled if present
    disabled = config.get("disabled", [])
    if name in disabled:
        disabled.remove(name)
    
    # Add to enabled if not present
    enabled = config.get("enabled", [])
    if name not in enabled:
        enabled.append(name)
    
    config["enabled"] = enabled
    save_plugins_config(config)
    
    return {"ok": True, "plugin": name, "status": "enabled"}


def disable_plugin(name: str) -> Dict[str, Any]:
    """Disable a plugin in configuration."""
    config = load_plugins_config()
    
    if name in config.get("plugins", {}):
        config["plugins"][name]["enabled"] = False
    
    # Remove from enabled
    enabled = config.get("enabled", [])
    if name in enabled:
        enabled.remove(name)
    
    # Add to disabled if not present
    disabled = config.get("disabled", [])
    if name not in disabled:
        disabled.append(name)
    
    config["enabled"] = enabled
    config["disabled"] = disabled
    save_plugins_config(config)
    
    return {"ok": True, "plugin": name, "status": "disabled"}


# ============================================================================
# PLUGIN UTILITIES
# ============================================================================

def reload_plugin(name: str) -> Dict[str, Any]:
    """Reload a plugin."""
    # Unload module
    if name in sys.modules:
        del sys.modules[name]
    
    # Reload
    return load_plugin(name)


def unload_plugin(name: str) -> Dict[str, Any]:
    """Unload a plugin."""
    if name in sys.modules:
        del sys.modules[name]
        return {"ok": True, "plugin": name, "status": "unloaded"}
    return {"ok": False, "error": "plugin not loaded"}


def list_plugins() -> Dict[str, Any]:
    """List all plugins and their status."""
    config = load_plugins_config()
    enabled = config.get("enabled", [])
    disabled = config.get("disabled", [])
    
    discovered = discover_plugins()
    packages = discover_packages()
    
    return {
        "discovered": discovered,
        "packages": packages,
        "enabled": enabled,
        "disabled": disabled,
        "total": len(discovered) + len(packages),
    }


def get_plugin_function(plugin_name: str, function_name: str) -> Optional[Callable]:
    """Get a plugin function by name."""
    if plugin_name not in sys.modules:
        return None
    
    module = sys.modules[plugin_name]
    return getattr(module, function_name, None)


# ============================================================================
# PLUGIN INTEGRATION
# ============================================================================

def integrate_plugins_into_core() -> Dict[str, Any]:
    """
    Integrate loaded plugins into CircleForge's core functionality.
    This connects plugins to the main system.
    """
    config = load_plugins_config()
    enabled = config.get("enabled", [])
    
    integration = {
        "plugins": {},
        "integration_status": "in_progress",
        "timestamp": int(time.time()),
    }
    
    for plugin_name in enabled:
        # Check if plugin is loaded
        if plugin_name in sys.modules:
            module = sys.modules[plugin_name]
            
            # Look for integration hooks
            integration_func = getattr(module, "integrate_with_circleforge", None)
            if integration_func:
                result = integration_func()
                integration["plugins"][plugin_name] = {
                    "integrated": result is not None,
                    "result": result,
                }
            else:
                integration["plugins"][plugin_name] = {
                    "integrated": True,
                    "reason": "no integration hook needed",
                }
        else:
            integration["plugins"][plugin_name] = {
                "integrated": False,
                "error": "plugin not loaded",
            }
    
    integration["integration_status"] = "complete"
    return integration


# ============================================================================
# PLUGIN TEMPLATE
# ============================================================================

PLUGIN_TEMPLATE = """
# {plugin_name}.py - Plugin for CircleForge
# Template for new plugins

# Required metadata
PLUGIN_INFO = {{
    "name": "{plugin_name}",
    "version": "0.1.0",
    "description": "{plugin_description}",
    "author": "Human",
    "enabled": True,
}}

# Plugin functions go here
def initialize():
    print(f"{plugin_name} plugin initialized")

def process_input(input_data):
    return input_data

def get_capabilities():
    return ["basic_processing"]

# Optional integration hook
def integrate_with_circleforge():
    return {{"capabilities": get_capabilities()}}

# Run on module load
if __name__ == "__main__":
    initialize()
"""

# ============================================================================
# PLUGIN CREATION
# ============================================================================

def create_plugin(name: str, description: str = "") -> Dict[str, Any]:
    """Create a new plugin template."""
    get_plugins_dir()  # Ensure directory exists
    
    plugin_content = PLUGIN_TEMPLATE.format(
        plugin_name=name,
        plugin_description=description,
    )
    
    plugin_path = get_plugins_dir() / f"{name}.py"
    plugin_path.write_text(plugin_content)
    
    return {
        "ok": True,
        "plugin": name,
        "path": str(plugin_path),
        "status": "created",
    }
