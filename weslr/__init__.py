"""Weslr Platform Core (v1)

Portable agent platform, runtime-agnostic.
"""

__version__ = "1.0.0"

from . import continuity
from . import contracts
from . import state
from . import task_anchor

__all__ = ["continuity", "contracts", "state", "task_anchor"]
