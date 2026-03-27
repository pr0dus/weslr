"""Orchestration glue for perform_tick - to be integrated into glue.py.

This module provides a cleaner tick orchestration that can be called from sim.py.
"""

from __future__ import annotations

import time
from typing import List, Dict, Any, Optional


def orchestrate_tick(
    verbose: bool = False,
    now_ts: int | None = None,
) -> Dict[str, Any]:
    """Orchestrate a tick across layers.

    This is a cleaner wrapper around sim.py's perform_tick that:
    1. Loads state from database
    2. Orchestrates memory archival
    3. Runs agent ticks
    4. Returns results

    Returns a tick result dict.
    """
    now_ts = now_ts or int(time.time())
    
    # Import from sim to avoid circular dependencies
    from sim import (
        connect,
        get_world,
        list_agents,
        load_categories,
        load_relationships,
        load_work_items,
        load_category_proposals,
        load_opportunity_board,
        maybe_generate_category_proposal,
        resolve_category_proposals,
        write_json_file,
        CATEGORIES_PATH,
        CATEGORY_PROPOSALS_PATH,
        AGENTS_DIR,
        summarize_unresolved_needs,
        load_communicator_state,
        ensure_internal_role_state,
        load_communicator_self,
        sync_reflection_store,
        sync_identity_state,
        save_communicator_self,
        synchronized_propagation,
        consume_inbox,
        agent_social_context,
        compute_agent_due_state,
        classify_internal_role,
        perform_tick,
        failsafe_allows,
    )
    
    # Call the existing perform_tick - this will be replaced when we fully refactor
    return perform_tick(verbose=verbose)


def orchestrate_memory_archival(self_state: dict, now_ts: int | None = None) -> dict:
    """Orchestrate memory archival across layers.

    Calls:
    - glue.reduce_context_pressure()
    - continuity_prioritizer.clear_stale_threads()
    - glue_orchestrate_tick.archive_all_stale()
    """
    now_ts = now_ts or int(time.time())
    
    # 1. Clear stale threads
    relationships = self_state.get("relationships", {})
    from continuity_prioritizer import clear_stale_threads
    relationships = clear_stale_threads(relationships, now_ts)
    self_state["relationships"] = relationships
    
    # 2. Reduce context pressure
    from glue import reduce_context_pressure
    self_state = reduce_context_pressure(self_state)
    
    # 3. Archive stale memory
    from glue import archive_all_stale
    self_state = archive_all_stale(self_state, now_ts)
    
    return self_state
