"""Weslr Runtime Adapters (v1)

Runtime adapter interface definitions and base classes.
Adapters provide runtime-specific context to the Weslr platform.

No runtime-specific dependencies.
No user-facing behavior.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..contracts import RunResult


__all__ = [
    "AdapterPaths",
    "AdapterRuntime",
    "AdapterCommands",
    "AdapterConfig",
    "RunResult",
]


class AdapterPaths:
    """Base class for path resolution adapters.
    
    Runtime adapters must implement these methods to provide
    path resolution that works across different runtime environments.
    """
    
    def base_dir(self) -> str:
        """Return the Weslr workspace base directory."""
        raise NotImplementedError
    
    def state_dir(self) -> str:
        """Return the state storage directory."""
        raise NotImplementedError
    
    def continuity_dir(self) -> str:
        """Return the continuity snapshots directory."""
        raise NotImplementedError
    
    def agent_dir(self) -> str:
        """Return the agent data directory."""
        raise NotImplementedError
    
    def log_dir(self) -> str:
        """Return the log storage directory."""
        raise NotImplementedError


class AdapterRuntime:
    """Base class for runtime environment adapters.
    
    Provides runtime-specific information about the execution environment.
    """
    
    def version(self) -> str:
        """Return the runtime version string."""
        raise NotImplementedError
    
    def name(self) -> str:
        """Return the runtime name."""
        raise NotImplementedError
    
    def timezone(self) -> str:
        """Return the runtime timezone."""
        raise NotImplementedError
    
    def cpu_count(self) -> int:
        """Return the available CPU cores."""
        raise NotImplementedError
    
    def memory_bytes(self) -> int:
        """Return the available memory in bytes."""
        raise NotImplementedError


class AdapterCommands:
    """Base class for command execution adapters.
    
    Provides runtime-specific command execution capabilities.
    """
    
    def run_python(self, script: str, args: List[str]) -> RunResult:
        """Execute a Python script with given arguments."""
        raise NotImplementedError
    
    def run_command(self, cmd: str, args: List[str]) -> RunResult:
        """Execute a shell command."""
        raise NotImplementedError
    
    def spawn_process(self, cmd: str, args: List[str], callback=None) -> Any:
        """Spawn a background process."""
        raise NotImplementedError


class AdapterConfig:
    """Base class for configuration adapters.
    
    Provides runtime-specific configuration access.
    """
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        raise NotImplementedError
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value (session only)."""
        raise NotImplementedError
    
    def get_secret(self, key: str) -> str:
        """Get a sensitive configuration value (secret)."""
        raise NotImplementedError
