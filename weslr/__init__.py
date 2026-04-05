"""Weslr Platform Core (v1)

Portable agent platform, runtime-agnostic.

Core modules:
- adapters: Runtime adapters (OpenClaw, Claude, OpenAI)
- continuity: Continuity state management
- contracts: Contract layer for state management
- concept_graph: Concept graph layer (linked knowledge)
- evidence_policy: Evidence policy and requirements
- file_ingestion: Text file ingestion
- file_router: Unified file routing
- request_intelligence: Request intelligence layer
- state: WESLR state management
- structured_data: Structured data handling
- task_anchor: Task anchors for continuity
"""

__version__ = "1.0.0"

from . import adapters
from . import continuity
from . import contracts
from . import concept_graph
from . import evidence_policy
from . import file_ingestion
from . import file_router
from . import request_intelligence
from . import state
from . import structured_data
from . import task_anchor

__all__ = [
    "adapters",
    "continuity",
    "contracts",
    "concept_graph",
    "evidence_policy",
    "file_ingestion",
    "file_router",
    "request_intelligence",
    "state",
    "structured_data",
    "task_anchor",
]
