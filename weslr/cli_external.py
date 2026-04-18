"""Weslr CLI - External and variation commands.

Commands moved here from main.py:
- Opportunity lifecycle management commands
- Variation generation commands
- Entity graph commands
- Relationship commands

This module holds commands that interface with external systems.
Note: Diagnostics, fallback, and fallback_trace commands remain in main.py.
"""

from __future__ import annotations

import json
from pathlib import Path

# Import Weslr modules
try:
    from weslr import self_architecture as sa
except ImportError:
    sa = None

# Import root-level modules for entity graph
try:
    import entity_graph
except ImportError:
    entity_graph = None


def emit(data):
    """Emit JSON to stdout."""
    print(json.dumps(data, indent=2))


def register_commands(subparsers):
    """Register external command parsers."""
    
    # === Opportunity Lifecycle Commands ===
    opportunity_parser = subparsers.add_parser("opportunity-list", help="list all opportunity themes with their lifecycle states")
    opportunity_parser.set_defaults(func=cmd_opportunity_list)

    opportunity_transition_parser = subparsers.add_parser("opportunity-transition", help="transition an opportunity to a new lifecycle state")
    opportunity_transition_parser.add_argument("--theme", required=True, help="theme name")
    opportunity_transition_parser.add_argument("--target", required=True, help="target state (hypothesis, validated, production, rejected, archived)")
    opportunity_transition_parser.set_defaults(func=cmd_opportunity_transition)

    opportunity_auto_transition_parser = subparsers.add_parser("opportunity-auto-transition", help="run auto-transition checks on all opportunities")
    opportunity_auto_transition_parser.set_defaults(func=cmd_opportunity_auto_transition)

    opportunity_reject_parser = subparsers.add_parser("opportunity-reject", help="record a rejection for an opportunity theme")
    opportunity_reject_parser.add_argument("--theme", required=True, help="theme name")
    opportunity_reject_parser.add_argument("--reason", required=True, help="rejection reason")
    opportunity_reject_parser.set_defaults(func=cmd_opportunity_reject)

    opportunity_cluster_parser = subparsers.add_parser("opportunity-cluster", help="show cross-agent opportunity clustering")
    opportunity_cluster_parser.set_defaults(func=cmd_opportunity_cluster)

    opportunity_revisit_parser = subparsers.add_parser("opportunity-revisit", help="inspect and trigger theme revisit tracking")
    opportunity_revisit_parser.set_defaults(func=cmd_opportunity_revisit)

    # === Variation Generation Commands ===
    variation_generate_parser = subparsers.add_parser("variation-generate", help="generate math-based variations for a rejected theme")
    variation_generate_parser.add_argument("--theme", required=True, help="theme name")
    variation_generate_parser.add_argument("--method", default="hybrid", help="method: markov, bandit, entropy, gradient, hybrid")
    variation_generate_parser.add_argument("--count", type=int, default=3, help="maximum variations to generate")
    variation_generate_parser.set_defaults(func=cmd_variation_generate)

    variation_list_parser = subparsers.add_parser("variation-list", help="list all themes with their generated variations and math scores")
    variation_list_parser.set_defaults(func=cmd_variation_list)

    variation_show_parser = subparsers.add_parser("variation-show", help="show detailed variation history for a theme")
    variation_show_parser.add_argument("--theme", required=True, help="theme name")
    variation_show_parser.set_defaults(func=cmd_variation_show)

    # === Entity Graph Commands ===
    entity_parser = subparsers.add_parser("entity-list", help="list entities in the entity graph")
    entity_parser.add_argument("--limit", "-l", type=int, default=None, help="limit results")
    entity_parser.set_defaults(func=cmd_entity_list)

    entity_details_parser = subparsers.add_parser("entity-details", help="show detailed information about an entity")
    entity_details_parser.add_argument("id", help="entity ID")
    entity_details_parser.set_defaults(func=cmd_entity_details)

    entity_add_parser = subparsers.add_parser("entity-add", help="add a new entity")
    entity_add_parser.add_argument("name", help="entity name")
    entity_add_parser.add_argument("--type", "-t", default="other", help="entity type (person, organization, concept, event, object, other)")
    entity_add_parser.add_argument("--aliases", "-a", default="", help="comma-separated aliases")
    entity_add_parser.add_argument("--confidence", "-c", type=float, default=0.5, help="initial confidence (0.0-1.0)")
    entity_add_parser.add_argument("--authoritative", action="store_true", help="add as authoritative (not ghost)")
    entity_add_parser.add_argument("--metadata", "-m", default="", help="JSON metadata")
    entity_add_parser.set_defaults(func=cmd_entity_add)

    entity_promote_parser = subparsers.add_parser("entity-promote", help="promote ghost entity to authoritative")
    entity_promote_parser.add_argument("id", help="entity ID")
    entity_promote_parser.set_defaults(func=cmd_entity_promote)

    entity_search_parser = subparsers.add_parser("entity-search", help="search entities by name or alias")
    entity_search_parser.add_argument("query", help="search query")
    entity_search_parser.set_defaults(func=cmd_entity_search)

    entity_stats_parser = subparsers.add_parser("entity-stats", help="show entity graph statistics")
    entity_stats_parser.set_defaults(func=cmd_entity_stats)

    # === Relationship Commands ===
    relationship_parser = subparsers.add_parser("relationship-list", help="list relationships in the entity graph")
    relationship_parser.add_argument("--limit", "-l", type=int, default=None, help="limit results")
    relationship_parser.set_defaults(func=cmd_relationship_list)

    relationship_add_parser = subparsers.add_parser("relationship-add", help="add a relationship between entities")
    relationship_add_parser.add_argument("source", help="source entity name")
    relationship_add_parser.add_argument("target", help="target entity name")
    relationship_add_parser.add_argument("--type", "-t", default="related_to", help="relationship type")
    relationship_add_parser.add_argument("--strength", "-s", type=float, default=0.5, help="relationship strength")
    relationship_add_parser.add_argument("--provenance", "-p", default="", help="JSON provenance")
    relationship_add_parser.set_defaults(func=cmd_relationship_add)


# ============================================================================
# Opportunity Lifecycle Commands
# ============================================================================

def cmd_opportunity_list(args):
    """List all opportunity themes with their lifecycle states."""
    if sa is None:
        emit({"error": "opportunity management not available in current configuration"})
        return
    result = sa.get_all_opportunities()
    emit(result)


def cmd_opportunity_transition(args):
    """Transition an opportunity to a new lifecycle state."""
    if sa is None:
        emit({"error": "opportunity management not available in current configuration"})
        return
    theme = args.theme
    target = args.target
    result = sa.transition_opportunity(theme, target)
    emit(result)


def cmd_opportunity_auto_transition(args):
    """Run auto-transition checks on all opportunities."""
    if sa is None:
        emit({"error": "opportunity management not available in current configuration"})
        return
    result = sa.auto_transition_opportunities()
    emit(result)


def cmd_opportunity_reject(args):
    """Record a rejection for an opportunity theme."""
    if sa is None:
        emit({"error": "opportunity management not available in current configuration"})
        return
    theme = args.theme
    reason = args.reason
    result = sa.reject_opportunity(theme, reason)
    emit(result)


def cmd_opportunity_cluster(args):
    """Show cross-agent opportunity clustering."""
    if sa is None:
        emit({"error": "opportunity management not available in current configuration"})
        return
    result = sa.get_opportunity_clustering()
    emit(result)


def cmd_opportunity_revisit(args):
    """Inspect and trigger theme revisit tracking."""
    if sa is None:
        emit({"error": "opportunity management not available in current configuration"})
        return
    result = sa.inspect_opportunity_revisit()
    emit(result)


# ============================================================================
# Variation Generation Commands
# ============================================================================

def cmd_variation_generate(args):
    """Generate math-based variations for a rejected theme."""
    theme = args.theme
    method = args.method
    count = args.count

    try:
        from variation_generator import generate_variations
        result = generate_variations(theme, method=method, count=count)
    except Exception:
        result = {"error": "variation generation not available in current configuration"}
    emit(result)


def cmd_variation_list(args):
    """List all themes with their generated variations and math scores."""
    try:
        from variation_generator import list_all_variations
        result = list_all_variations()
    except Exception:
        result = {"error": "variation listing not available in current configuration"}
    emit(result)


def cmd_variation_show(args):
    """Show detailed variation history for a theme."""
    theme = args.theme

    try:
        from variation_generator import get_variation_history
        result = get_variation_history(theme)
    except Exception:
        result = {"error": "variation history not available in current configuration"}
    emit(result)


# ============================================================================
# Entity Graph Commands
# ============================================================================

def cmd_entity_list(args):
    """List entities in the entity graph."""
    if entity_graph is None:
        emit({"error": "entity_graph module not available"})
        return
    try:
        entities = entity_graph.get_all_entities(limit=args.limit)
        emit({"entities": entities, "count": len(entities)})
    except Exception as e:
        emit({"error": str(e)})


def cmd_entity_details(args):
    """Show detailed information about an entity."""
    if entity_graph is None:
        emit({"error": "entity_graph module not available"})
        return
    try:
        entity = entity_graph.get_entity_by_id(args.id)
        if entity:
            emit(entity)
        else:
            emit({"error": f"Entity not found: {args.id}"})
    except Exception as e:
        emit({"error": str(e)})


def cmd_entity_add(args):
    """Add a new entity."""
    if entity_graph is None:
        emit({"error": "entity_graph module not available"})
        return
    try:
        metadata = {}
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                emit({"error": "Invalid JSON in --metadata"})
                return
        aliases = args.aliases.split(",") if args.aliases else []
        entity = entity_graph.add_entity(
            name=args.name,
            entity_type=args.type,
            aliases=aliases,
            confidence=args.confidence,
            authoritative=args.authoritative,
            metadata=metadata,
        )
        emit(entity)
    except Exception as e:
        emit({"error": str(e)})


def cmd_entity_promote(args):
    """Promote ghost entity to authoritative."""
    if entity_graph is None:
        emit({"error": "entity_graph module not available"})
        return
    try:
        result = entity_graph.promote_entity(args.id)
        emit(result)
    except Exception as e:
        emit({"error": str(e)})


def cmd_entity_search(args):
    """Search entities by name or alias."""
    if entity_graph is None:
        emit({"error": "entity_graph module not available"})
        return
    try:
        entities = entity_graph.search_entities(args.query)
        emit({"entities": entities, "count": len(entities)})
    except Exception as e:
        emit({"error": str(e)})


def cmd_entity_stats(args):
    """Show entity graph statistics."""
    if entity_graph is None:
        emit({"error": "entity_graph module not available"})
        return
    try:
        stats = entity_graph.get_graph_stats()
        emit(stats)
    except Exception as e:
        emit({"error": str(e)})


# ============================================================================
# Relationship Commands
# ============================================================================

def cmd_relationship_list(args):
    """List relationships in the entity graph."""
    if entity_graph is None:
        emit({"error": "entity_graph module not available"})
        return
    try:
        relationships = entity_graph.get_all_relationships(limit=args.limit)
        emit({"relationships": relationships, "count": len(relationships)})
    except Exception as e:
        emit({"error": str(e)})


def cmd_relationship_add(args):
    """Add a relationship between entities."""
    if entity_graph is None:
        emit({"error": "entity_graph module not available"})
        return
    try:
        provenance = {}
        if args.provenance:
            try:
                provenance = json.loads(args.provenance)
            except json.JSONDecodeError:
                emit({"error": "Invalid JSON in --provenance"})
                return
        result = entity_graph.add_relationship(
            source=args.source,
            target=args.target,
            relationship_type=args.type,
            strength=args.strength,
            provenance=provenance,
        )
        emit(result)
    except Exception as e:
        emit({"error": str(e)})
