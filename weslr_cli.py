"""Human-in-the-Loop Integration for Weslr.

Provides CLI commands for entity curation, dashboard visualization,
and consciousness evidence logging.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import entity_graph as eg
import introspection as ins
import valence_system as vs
import metacognition as met
import self_referential as sr
import belief_system as bs

BASE_DIR = Path(__file__).resolve().parent


def print_entity_list(limit: int = 10):
    """List entities in the entity graph."""
    graph = eg.get_entity_graph()
    entities = graph.get_all_entities()[:limit]

    for entity in entities:
        ghost_marker = " (GHOST)" if entity.is_ghost else ""
        print(f"{entity.id}: {entity.name} ({entity.type}) - {entity.confidence:.2f}{ghost_marker}")


def print_entity_details(entity_id: str):
    """Show details for a specific entity."""
    graph = eg.get_entity_graph()
    entity = graph.get_entity(entity_id)

    if not entity:
        print(f"Entity {entity_id} not found")
        return

    print(json.dumps(entity.to_dict(), indent=2))


def print_relationship_list(limit: int = 10):
    """List relationships in the entity graph."""
    graph = eg.get_entity_graph()
    relationships = graph.get_all_relationships()[:limit]

    for rel in relationships:
        source = graph.get_entity(rel.source_id)
        target = graph.get_entity(rel.target_id)
        source_name = source.name if source else rel.source_id
        target_name = target.name if target else rel.target_id
        print(f"{rel.id}: {source_name} -> {target_name} ({rel.type}) - {rel.strength:.2f}")


def entity_merge(id1: str, id2: str):
    """Merge two entities."""
    graph = eg.get_entity_graph()
    e1 = graph.get_entity(id1)
    e2 = graph.get_entity(id2)

    if not e1 or not e2:
        print("✗ One or both entities not found")
        return False

    # Merge e2 into e1
    e1.aliases.extend(a for a in e2.aliases if a not in e1.aliases)
    e1.evidence.extend(e2.evidence)
    e1.confidence = min(1.0, e1.confidence + e2.confidence * 0.3)

    # Remove e2 and its relationships
    graph.delete_entity(id2)
    graph.update_entity(id1, aliases=e1.aliases, confidence=e1.confidence)

    print(f"✓ Merged '{e2.name}' into '{e1.name}'")
    return True


def entity_promote(entity_id: str):
    """Promote ghost entity to authoritative."""
    graph = eg.get_entity_graph()
    entity = graph.promote_entity(entity_id)

    if entity:
        print(f"✓ Promoted entity '{entity.name}' to authoritative")
        return True

    print(f"✗ Could not promote entity {entity_id}")
    return False


def print_self_evidence():
    """Print full self-evidence structure."""
    with open(BASE_DIR / "self_evidence.json", "r") as f:
        evidence = json.load(f)

    print(json.dumps(evidence, indent=2))


def print_weslr_status():
    """Print comprehensive Weslr status."""
    print("=" * 60)
    print("WESLR STATUS REPORT")
    print("=" * 60)

    # Entity graph stats
    graph = eg.get_entity_graph()
    stats = graph.get_entity_stats()
    print(f"\n📊 Entity Graph:")
    print(f"  Total entities: {stats['total_entities']}")
    print(f"  Authoritative: {stats['authoritative_entities']}")
    print(f"  Ghost: {stats['ghost_entities']}")
    print(f"  Total relationships: {stats['total_relationships']}")

    # Introspection
    monitor = ins.get_introspection_monitor()
    introspection = monitor.get_self_evidence()
    print(f"\n🧠 Introspection:")
    print(f"  Detected perturbations: {introspection['introspection']['total_perturbations']}")
    print(f"  Confidence signals: {introspection['introspection']['confidence_signals']}")

    # Metacognition
    meta = met.get_metacognitive_monitor()
    metacognition = meta.get_self_evidence()
    print(f"\n⚙️  Metacognition:")
    print(f"  Meta thoughts: {metacognition['meta_thoughts']}")
    print(f"  Attention shifts: {metacognition['attention_shares']}")
    print(f"  Self-referential: {metacognition['self_referential_count']}")

    # Valence
    valence = vs.get_valence_system()
    valence_evidence = valence.get_valence_evidence()
    print(f"\n⚖️  Valence:")
    print(f"  Pain avoided: {valence_evidence['valence']['avoided_pain']}")
    print(f"  Pleasure sought: {valence_evidence['valence']['sought_pleasure']}")
    print(f"  Total tradeoffs: {valence_evidence['valence']['total_tradeoffs']}")

    # Self-referential
    self_ref = sr.get_self_referential_processor()
    self_ref_evidence = self_ref.get_self_referential_evidence()
    print(f"\n🔄 Self-Referential:")
    print(f"  Events: {self_ref_evidence['total_events']}")
    print(f"  With markers: {self_ref_evidence['self_referential_events']}")

    # Belief system
    belief = bs.get_belief_system()
    belief_evidence = belief.get_self_evidence()
    print(f"\n🤔 Belief System:")
    print(f"  Total beliefs: {belief_evidence['total_beliefs']}")
    print(f"  Avg confidence: {belief_evidence['avg_confidence']:.3f}")
    print(f"  Avg coherence: {belief_evidence['avg_coherence']:.3f}")

    print("\n" + "=" * 60)


def main():
    """CLI entry point for Human-in-the-Loop Integration."""
    if len(sys.argv) < 2:
        print("Weslr Human-in-the-Loop CLI")
        print("\nCommands:")
        print("  entity-list [--limit N]      List entities")
        print("  entity-details <id>          Show entity details")
        print("  rel-list [--limit N]         List relationships")
        print("  entity-merge <id1> <id2>     Merge two entities")
        print("  entity-promote <id>          Promote ghost to authoritative")
        print("  evidence                     Show self-evidence structure")
        print("  status                       Show comprehensive Weslr status")
        print("\nUsage: python weslr_cli.py <command> [args]")
        return

    command = sys.argv[1]

    if command == "entity-list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        print_entity_list(limit)

    elif command == "entity-details":
        if len(sys.argv) < 3:
            print("Usage: weslr_cli.py entity-details <entity_id>")
            return
        print_entity_details(sys.argv[2])

    elif command == "rel-list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        print_relationship_list(limit)

    elif command == "entity-merge":
        if len(sys.argv) < 4:
            print("Usage: weslr_cli.py entity-merge <id1> <id2>")
            return
        entity_merge(sys.argv[2], sys.argv[3])

    elif command == "entity-promote":
        if len(sys.argv) < 3:
            print("Usage: weslr_cli.py entity-promote <entity_id>")
            return
        entity_promote(sys.argv[2])

    elif command == "evidence":
        print_self_evidence()

    elif command == "status":
        print_weslr_status()

    else:
        print(f"Unknown command: {command}")
        print("Run 'weslr_cli.py' for help")


if __name__ == "__main__":
    main()
