"""Cross-reference existing memory structures with Weslr entity graph.

Maps public_memory.json, messages.json, and relationships.json into
the entity graph with traceable provenance.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import entity_graph as eg


BASE_DIR = Path(__file__).resolve().parent
PUBLIC_MEMORY_PATH = BASE_DIR / "public_memory.json"
MESSAGES_PATH = BASE_DIR / "messages.json"
RELATIONSHIPS_PATH = BASE_DIR / "relationships.json"


def load_json(path: Path) -> List[Dict[str, Any]]:
    """Load JSON file, return empty list if not exists."""
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


class MemoryCrossRef:
    """Cross-references existing memory with entity graph."""

    def __init__(self, graph: eg.EntityGraph = None):
        self.graph = graph or eg.get_entity_graph()
        self.extraction_log: List[Dict[str, Any]] = []

    def cross_reference_public_memory(self, source: str = "public_memory.json"):
        """Map public_memory.json items to entity graph."""
        memory_items = load_json(PUBLIC_MEMORY_PATH)

        for item in memory_items:
            if not isinstance(item, dict):
                continue

            item_id = item.get("id", "unknown")
            item_kind = item.get("kind", "concept")
            item_title = item.get("title", item_id)
            item_content = item.get("content", "")
            item_stability = item.get("stability", 0.5)

            # Create entity for each memory item
            entity = self.graph.add_entity(
                name=item_title,
                entity_type=item_kind,
                aliases=[item_id],
                confidence=item_stability,
                is_ghost=False,  # Public memory is authoritative
                metadata={
                    "source": source,
                    "original_id": item_id,
                    "created_at": item.get("created_at", int(time.time())),
                    "updated_at": item.get("updated_at", int(time.time()))
                }
            )

            # Add evidence with provenance
            entity.add_evidence(
                source=source,
                content=item_content[:200] if item_content else item_id,
                confidence_boost=0.1 * item_stability
            )

            self.extraction_log.append({
                "type": "memory_item",
                "entity_id": entity.id,
                "original_id": item_id,
                "source": source,
                "timestamp": int(time.time())
            })

        self.graph.save()
        return len(self.extraction_log)

    def cross_reference_messages(self, source: str = "messages.json"):
        """Map messages.json to entity graph with relationships."""
        messages = load_json(MESSAGES_PATH)

        # Track agents mentioned in messages
        agents = set()
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            from_agent = msg.get("from_agent", "")
            to_agent = msg.get("to_agent", "")
            if from_agent:
                agents.add(from_agent)
            if to_agent:
                agents.add(to_agent)

        # Create entities for agents
        agent_entities = {}
        for agent_name in agents:
            entity = self.graph.add_entity(
                name=agent_name,
                entity_type="person",
                confidence=0.9,
                is_ghost=False,
                metadata={"source": source, "created_at": int(time.time())}
            )
            agent_entities[agent_name] = entity

            # Add evidence from message history
            agent_messages = [m for m in messages if m.get("from_agent") == agent_name]
            if agent_messages:
                entity.add_evidence(
                    source=source,
                    content=f"Active participant in {len(agent_messages)} messages",
                    confidence_boost=0.1
                )

        # Create relationships between agents based on messaging
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            from_agent = msg.get("from_agent", "")
            to_agent = msg.get("to_agent", "")
            kind = msg.get("kind", "communication")

            if from_agent in agent_entities and to_agent in agent_entities:
                rel = self.graph.add_relationship(
                    source_id=agent_entities[from_agent].id,
                    target_id=agent_entities[to_agent].id,
                    rel_type=kind,
                    strength=0.8,
                    provenance={
                        "source": source,
                        "message_id": msg.get("id", "unknown"),
                        "created_at": msg.get("created_at", int(time.time())),
                        "traceable": True
                    }
                )

        self.graph.save()
        return len(agent_entities), len(messages)

    def cross_reference_relationships(self, source: str = "relationships.json"):
        """Map relationships.json to entity graph as edges."""
        rels = load_json(RELATIONSHIPS_PATH)

        # Track agents in relationships
        agents = set()
        for rel in rels:
            if not isinstance(rel, dict):
                continue
            agents.add(rel.get("source_agent", ""))
            agents.add(rel.get("target_agent", ""))

        # Create entities for agents if not already created
        agent_entities = {}
        for agent_name in agents:
            if agent_name and agent_name not in agent_entities:
                entity = self.graph.add_entity(
                    name=agent_name,
                    entity_type="person",
                    confidence=0.9,
                    is_ghost=False,
                    metadata={"source": source, "created_at": int(time.time())}
                )
                agent_entities[agent_name] = entity

        # Create relationships
        rel_count = 0
        for rel in rels:
            if not isinstance(rel, dict):
                continue

            source_agent = rel.get("source_agent", "")
            target_agent = rel.get("target_agent", "")
            trust = rel.get("trust", 0.5)
            usefulness = rel.get("usefulness", 0.5)

            if source_agent in agent_entities and target_agent in agent_entities:
                # Create relationship with combined trust/usefulness as strength
                strength = (trust + usefulness) / 2
                self.graph.add_relationship(
                    source_id=agent_entities[source_agent].id,
                    target_id=agent_entities[target_agent].id,
                    rel_type="collaboration",
                    strength=strength,
                    provenance={
                        "source": source,
                        "trust": trust,
                        "usefulness": usefulness,
                        "friction": rel.get("friction", 0.0),
                        "last_event": rel.get("last_event", "unknown"),
                        "updated_at": rel.get("updated_at", int(time.time())),
                        "traceable": True
                    }
                )
                rel_count += 1

        self.graph.save()
        return len(agent_entities), rel_count

    def cross_reference_all(self) -> Dict[str, int]:
        """Cross-reference all memory structures."""
        results = {}

        # Public memory
        count = self.cross_reference_public_memory()
        results["public_memory"] = count
        print(f"✓ Cross-referenced {count} items from public_memory.json")

        # Messages
        agents, msg_count = self.cross_reference_messages()
        results["messages"] = msg_count
        results["message_agents"] = agents
        print(f"✓ Cross-referenced {msg_count} messages ({agents} agents)")

        # Relationships
        agents, rel_count = self.cross_reference_relationships()
        results["relationships"] = rel_count
        results["rel_agents"] = agents
        print(f"✓ Cross-referenced {rel_count} relationships ({agents} agents)")

        # Log summary
        stats = self.graph.get_entity_stats()
        results["total_entities"] = stats["total_entities"]
        results["total_relationships"] = stats["total_relationships"]

        return results


def main():
    """CLI entry point."""
    import sys

    graph = eg.get_entity_graph()
    ref = MemoryCrossRef(graph)

    if len(sys.argv) < 2:
        print("Usage: python cross_reference.py <command>")
        print("Commands:")
        print("  all - Cross-reference all memory structures")
        print("  public - Cross-reference public_memory.json")
        print("  messages - Cross-reference messages.json")
        print("  relationships - Cross-reference relationships.json")
        print("  stats - Show current entity graph stats")
        return

    command = sys.argv[1]

    if command == "all":
        results = ref.cross_reference_all()
        print(f"\nResults: {results}")

    elif command == "public":
        count = ref.cross_reference_public_memory()
        print(f"Cross-referenced {count} items from public_memory.json")

    elif command == "messages":
        agents, msg_count = ref.cross_reference_messages()
        print(f"Cross-referenced {msg_count} messages ({agents} agents)")

    elif command == "relationships":
        agents, rel_count = ref.cross_reference_relationships()
        print(f"Cross-referenced {rel_count} relationships ({agents} agents)")

    elif command == "stats":
        stats = graph.get_entity_stats()
        print(f"Total entities: {stats['total_entities']}")
        print(f"Authoritative: {stats['authoritative_entities']}")
        print(f"Ghost: {stats['ghost_entities']}")
        print(f"Total relationships: {stats['total_relationships']}")
        print(f"Entities by type: {stats['entities_by_type']}")


if __name__ == "__main__":
    main()
