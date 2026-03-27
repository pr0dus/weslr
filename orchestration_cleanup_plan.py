"""Orchestration glue cleanup plan for sim.py.

This file documents the cleanup work needed to reduce sim.py complexity.
The goal is to move orchestration logic into dedicated glue modules,
leaving sim.py with core world management and state persistence.

Current issues:
1. sim.py has 182 functions total
2. Many functions are thin wrappers around glue module calls
3. Record_human_exchange has 500+ lines of mixed orchestration logic
4. Agent tick loop contains interleaved orchestration and action execution
5. Topic inference logic is embedded in record_human_exchange
6. Safety, interpretation, research, relationships all mixed together

Cleanup strategy:

## Phase 1: Extract pure orchestration functions to glue.py

These functions should be thin wrappers that just call the right module:

```python
# glue_orchestration.py (new)
def orchestrate_record_human_exchange(human_name, message, **kwargs):
    return glue.process_human_exchange(human_name, message, **kwargs)

def orchestrate_agent_tick(agent, world_state, relationships, **kwargs):
    return glue_orchestrate_agent(agent, world_state, relationships, **kwargs)

def orchestrate_memory_archival(self_state, now_ts):
    return continuity_prioritizer.clear_stale_threads(...)
           + semantic_memory.archive_stale(...)
           + glue.reduce_context_pressure(...)
```

## Phase 2: Simplify sim.py main functions

After Phase 1, sim.py should look more like:

```python
# sim.py (cleaned)
from glue import process_human_exchange, build_communicator_message, reduce_context_pressure
from glue_orchestration import orchestrate_record_human_exchange, orchestrate_agent_tick
from glue_persistence import load_world, save_world, load_relationships, save_relationships

def record_human_exchange(...):
    return orchestrate_record_human_exchange(...)

def perform_tick(...):
    world = load_world()
    relationships = load_relationships()
    
    # Agent loop
    for agent in world["agents"]:
        orchestrate_agent_tick(agent, world, relationships)
    
    # Memory archival
    glue_orchestrate_memory_archival(...)
    
    save_relationships(relationships)
    save_world(world)
```

## Phase 3: Move topic inference to glue

The fallback topic scoring logic in record_human_exchange should move to:

```python
# glue_topic_inference.py (new)
def infer_fallback_topics(relationships, self_state, message):
    # Extracted from sim.py record_human_exchange
    # Returns prioritized topic list
```

## Phase 4: Add orchestration tests

Add tests for each glue function to ensure orchestration is correct.

Estimated cleanup outcome:
- sim.py reduced from ~8000 lines to ~2000-3000 lines
- More testable, debuggable code
- Clearer separation of concerns
- Reusable orchestration functions
- Easier to maintain

Implementation order:
1. Extract topic inference logic → glue_topic_inference.py
2. Extract agent tick orchestration → glue_agent_orchestration.py
3. Extract memory archival orchestration → glue_memory_orchestration.py
4. Update sim.py to use glue modules
5. Add integration tests
6. Document new architecture
"""

from __future__ import annotations

# This file is documentation, not executable code
# It defines the cleanup plan for sim.py orchestration glue

ORCHESTRATION_CLEANUP_PLAN = {
    "status": "planned",
    "priority": "medium",
    "components": [
        "topic_inference_glue",
        "agent_tick_glue",
        "memory_archival_glue",
        "human_exchange_glue",
    ],
    "expected_outcomes": {
        "sim_py_lines_reduced": "50-60%",
        "testability_improved": True,
        "debuggability_improved": True,
        "reusability_improved": True,
    },
}
