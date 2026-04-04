"""Weslr Platform Core (v1)

Portable agent platform, runtime-agnostic.
"""

__version__ = "1.0.0"

from . import adapters
from . import continuity
from . import contracts
from . import file_ingestion
from . import file_router
from . import state
from . import structured_data
from . import task_anchor

__all__ = [
    "adapters",
    "continuity",
    "contracts",
    "file_ingestion",
    "file_router",
    "state",
    "structured_data",
    "task_anchor",
]
