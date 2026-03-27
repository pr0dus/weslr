"""Entity extraction module for Weslr.

Implements hybrid unsupervised + supervised entity detection with traceable
reasoning and human-in-the-loop curation interface.
"""

from __future__ import annotations

import re
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from collections import Counter

import entity_graph as eg


# Base directory for entity extraction storage
BASE_DIR = Path(__file__).resolve().parent
EXTRACTION_HISTORY_PATH = BASE_DIR / "extraction_history.json"
ENTITY_EXTRACTOR_CONFIG_PATH = BASE_DIR / "entity_extractor_config.json"


@dataclass
class ExtractionResult:
    """Result of entity extraction from a source."""
    entity: eg.Entity
    source_id: str
    confidence: float
    extracted_at: int
    reasoning: Dict[str, Any]  # Traceable reasoning for the extraction
    pattern_type: str  # Pattern used: regex, dependency, heuristic, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity.to_dict(),
            "source_id": self.source_id,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at,
            "reasoning": self.reasoning,
            "pattern_type": self.pattern_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExtractionResult:
        entity_data = data.get("entity", {})
        if isinstance(entity_data, dict):
            entity = eg.Entity.from_dict(entity_data)
        else:
            entity = entity_data
        return cls(
            entity=entity,
            source_id=data.get("source_id", ""),
            confidence=data.get("confidence", 0.5),
            extracted_at=data.get("extracted_at", int(time.time())),
            reasoning=data.get("reasoning", {}),
            pattern_type=data.get("pattern_type", "unknown")
        )


@dataclass
class Pattern:
    """Named entity pattern with regex and metadata."""
    name: str
    regex: str
    entity_type: str
    confidence: float = 0.7
    description: str = ""

    def compile(self):
        return re.compile(self.regex, re.IGNORECASE)


# Predefined patterns for supervised extraction
DEFAULT_PATTERNS = [
    # People names (capitalized words, common title prefixes)
    Pattern(
        name="person_name",
        regex=r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b",
        entity_type="person",
        confidence=0.6,
        description="Potential person names (capitalized multi-word tokens)"
    ),
    # Email addresses
    Pattern(
        name="email",
        regex=r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
        entity_type="contact",
        confidence=0.95,
        description="Email addresses"
    ),
    # URLs
    Pattern(
        name="url",
        regex=r"\b(https?://[^\s]+)\b",
        entity_type="website",
        confidence=0.95,
        description="URLs"
    ),
    # Project IDs (common format)
    Pattern(
        name="project_id",
        regex=r"\b(project-[a-z0-9-]+)\b",
        entity_type="organization",
        confidence=0.9,
        description="Project identifiers"
    ),
    # Date expressions
    Pattern(
        name="date",
        regex=r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b",
        entity_type="event",
        confidence=0.8,
        description="Date expressions"
    ),
    # Time expressions
    Pattern(
        name="time",
        regex=r"\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?|(\d{1,2}(?:st|nd|rd|th)?)\s*(?:AM|PM|am|pm)?)\b",
        entity_type="event",
        confidence=0.75,
        description="Time expressions"
    ),
]


class EntityExtractor:
    """Hybrid unsupervised + supervised entity extraction engine."""

    def __init__(
        self,
        patterns: List[Pattern] = None,
        min_confidence: float = 0.5,
        max_entities_per_text: int = 20
    ):
        self.patterns = patterns or DEFAULT_PATTERNS
        self.compiled_patterns = {p.name: p.compile() for p in self.patterns}
        self.min_confidence = min_confidence
        self.max_entities_per_text = max_entities_per_text
        self.extraction_history: List[ExtractionResult] = []
        self.entity_clusters: Dict[str, List[str]] = {}  # cluster_id -> entity_ids

    def extract_from_text(
        self,
        text: str,
        source_id: str,
        graph: eg.EntityGraph = None
    ) -> List[ExtractionResult]:
        """Extract entities from text using hybrid approach."""
        results = []

        # Supervised extraction via regex patterns
        for pattern in self.patterns:
            for match in pattern.compile().finditer(text):
                entity_name = match.group(1) if match.groups() else match.group(0)

                # Skip if too short or looks like a variable (all lowercase with underscores)
                if len(entity_name) < 2:
                    continue
                if re.match(r"^[a-z_]+$", entity_name):
                    continue

                # Check for ghost entity
                existing = graph.get_entity_by_name(entity_name) if graph else None
                if existing and not existing.is_ghost:
                    # Update existing entity
                    existing.add_evidence(
                        source=source_id,
                        content=text[:200],
                        confidence_boost=0.05
                    )
                    continue

                entity = graph.add_entity(
                    name=entity_name,
                    entity_type=pattern.entity_type,
                    confidence=pattern.confidence,
                    is_ghost=True
                ) if graph else None

                result = ExtractionResult(
                    entity=entity,
                    source_id=source_id,
                    confidence=pattern.confidence,
                    extracted_at=int(time.time()),
                    reasoning={
                        "pattern": pattern.name,
                        "match": match.group(0),
                        "position": [match.start(), match.end()],
                        "text_snippet": text[max(0, match.start()-30):match.end()+30]
                    },
                    pattern_type="regex"
                )
                results.append(result)

        # Unsupervised extraction via clustering (n-gram analysis)
        unsupervised = self._extract_unsupervised(text, graph, source_id)
        results.extend(unsupervised)

        return results[:self.max_entities_per_text]

    def _extract_unsupervised(
        self,
        text: str,
        graph: eg.EntityGraph = None,
        source_id: str = ""
    ) -> List[ExtractionResult]:
        """Extract entities via unsupervised n-gram clustering."""
        results = []

        # Tokenize and find candidate n-grams
        words = re.findall(r"\b[A-Z][a-z]+\b", text)  # CamelCase or TitleCase tokens
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1) if len(words) > 1]

        # Cluster candidates by frequency
        all_candidates = words + bigrams
        freq = Counter(all_candidates)

        # High-frequency candidates are likely entities
        for candidate, count in freq.items():
            if count >= 2 and len(candidate) > 3:  # Minimum threshold
                # Calculate confidence based on frequency and length
                confidence = min(0.9, 0.5 + (count * 0.1))

                existing = graph.get_entity_by_name(candidate) if graph else None
                if existing and not existing.is_ghost:
                    existing.add_evidence(
                        source=source_id,
                        content=text[:200],
                        confidence_boost=0.02 * count
                    )
                    continue

                entity = graph.add_entity(
                    name=candidate,
                    entity_type="concept",
                    confidence=confidence,
                    is_ghost=True
                ) if graph else None

                result = ExtractionResult(
                    entity=entity,
                    source_id=source_id,
                    confidence=confidence,
                    extracted_at=int(time.time()),
                    reasoning={
                        "method": "unsupervised",
                        "frequency": count,
                        "type": "ngram" if " " in candidate else "unigram"
                    },
                    pattern_type="clustering"
                )
                results.append(result)

        return results

    def cluster_entities(
        self,
        entities: List[eg.Entity],
        threshold: float = 0.7
    ) -> Dict[str, List[eg.Entity]]:
        """Cluster similar entities using fuzzy matching."""
        clusters = {}

        for entity in entities:
            found_cluster = False
            for cluster_id, members in clusters.items():
                # Calculate similarity with cluster representative
                rep = members[0]
                similarity = self._entity_similarity(entity, rep)

                if similarity >= threshold:
                    members.append(entity)
                    found_cluster = True
                    break

            if not found_cluster:
                cluster_id = f"cluster_{len(clusters)}"
                clusters[cluster_id] = [entity]

        return clusters

    def _entity_similarity(self, e1: eg.Entity, e2: eg.Entity) -> float:
        """Calculate similarity between two entities."""
        # Name overlap
        name_overlap = len(set(e1.name.lower().split()) & set(e2.name.lower().split()))
        name_total = len(set(e1.name.lower().split()) | set(e2.name.lower().split()))
        name_score = name_overlap / name_total if name_total > 0 else 0

        # Type match
        type_score = 1.0 if e1.type == e2.type else 0.0

        # Alias overlap
        aliases1 = set(a.lower() for a in e1.aliases)
        aliases2 = set(a.lower() for a in e2.aliases)
        alias_overlap = len(aliases1 & aliases2) / len(aliases1 | aliases2) if (aliases1 | aliases2) else 0

        # Weighted combination
        return 0.5 * name_score + 0.3 * type_score + 0.2 * alias_overlap

    def add_extraction(self, result: ExtractionResult):
        """Record an extraction for history."""
        self.extraction_history.append(result)

    def get_extraction_history(self) -> List[ExtractionResult]:
        """Get all extraction history."""
        return self.extraction_history

    def save_history(self, path: Path = EXTRACTION_HISTORY_PATH):
        """Save extraction history to JSON."""
        with open(path, "w") as f:
            json.dump([r.to_dict() for r in self.extraction_history], f, indent=2)

    @classmethod
    def load_history(cls, path: Path = EXTRACTION_HISTORY_PATH) -> List[ExtractionResult]:
        """Load extraction history from JSON."""
        if not path.exists():
            return []
        with open(path, "r") as f:
            data = json.load(f)
            return [ExtractionResult.from_dict(d) for d in data]


# CLI interface for curation
def cli_entity_curate(
    graph: eg.EntityGraph,
    entity_id: str,
    action: str
) -> bool:
    """Entity curation CLI: merge, split, confirm, ghost.

    Actions:
    - merge <id1> <id2> -> Merge two entities
    - split <id> -> Split entity into separate entities
    - confirm <id> -> Promote ghost to authoritative
    - ghost <id> -> Demote authoritative to ghost
    - delete <id> -> Delete entity
    """
    if action == "confirm":
        entity = graph.promote_entity(entity_id)
        if entity:
            print(f"✓ Promoted entity '{entity.name}' to authoritative")
            return True

    elif action == "ghost":
        entity = graph.get_entity(entity_id)
        if entity and not entity.is_ghost:
            entity.is_ghost = True
            entity.metadata["demoted_at"] = int(time.time())
            graph.save()
            print(f"✓ Demoted entity '{entity.name}' to ghost")
            return True

    elif action == "delete":
        if graph.delete_entity(entity_id):
            print(f"✓ Deleted entity {entity_id}")
            return True

    elif action == "merge":
        # This would need two entity IDs - handled separately
        print("Merge requires two entity IDs: entity-curate merge <id1> <id2>")
        return False

    print(f"✗ Action '{action}' on entity {entity_id} failed")
    return False


def cli_entity_merge(graph: eg.EntityGraph, id1: str, id2: str) -> bool:
    """Merge two entities into one."""
    e1 = graph.get_entity(id1)
    e2 = graph.get_entity(id2)

    if not e1 or not e2:
        print("✗ One or both entities not found")
        return False

    if e1.is_ghost and not e2.is_ghost:
        # Keep e2, merge e1 into it
        target, source = e2, e1
    else:
        target, source = e1, e2

    # Merge aliases
    target.aliases.extend(s for s in source.aliases if s not in target.aliases)

    # Merge evidence
    target.evidence.extend(source.evidence)
    target.confidence = min(1.0, target.confidence + source.confidence * 0.5)

    # Merge relationships
    for rel_id in source.relationships:
        if rel_id not in target.relationships:
            target.relationships.append(rel_id)

    # Delete source
    graph.delete_entity(source.id)

    # Update target
    graph.update_entity(target.id, aliases=target.aliases, confidence=target.confidence)

    print(f"✓ Merged '{source.name}' into '{target.name}'")
    return True


def load_extractor_config(path: Path = ENTITY_EXTRACTOR_CONFIG_PATH) -> Dict[str, Any]:
    """Load entity extractor configuration."""
    if not path.exists():
        return {
            "min_confidence": 0.5,
            "max_entities_per_text": 20,
            "patterns": [p.__dict__ for p in DEFAULT_PATTERNS],
            "cluster_threshold": 0.7
        }
    with open(path, "r") as f:
        return json.load(f)


def save_extractor_config(config: Dict[str, Any], path: Path = ENTITY_EXTRACTOR_CONFIG_PATH):
    """Save entity extractor configuration."""
    with open(path, "w") as f:
        json.dump(config, f, indent=2)


def main():
    """CLI entry point for entity curation."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python entity_extractor.py <command> [args]")
        print("Commands:")
        print("  list [--limit N]")
        print("  details <entity_id>")
        print("  merge <id1> <id2>")
        print("  promote <entity_id>")
        print("  ghost <entity_id>")
        print("  delete <entity_id>")
        return

    command = sys.argv[1]
    graph = eg.get_entity_graph()

    if command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        entities = graph.get_all_entities()[:limit]
        for e in entities:
            ghost_marker = " (GHOST)" if e.is_ghost else ""
            print(f"{e.id}: {e.name} ({e.type}) - {e.confidence:.2f}{ghost_marker}")

    elif command == "details":
        if len(sys.argv) < 3:
            print("Usage: entity-curate details <entity_id>")
            return
        entity = graph.get_entity(sys.argv[2])
        if entity:
            print(json.dumps(entity.to_dict(), indent=2))
        else:
            print(f"Entity {sys.argv[2]} not found")

    elif command == "merge":
        if len(sys.argv) < 4:
            print("Usage: entity-curate merge <id1> <id2>")
            return
        cli_entity_merge(graph, sys.argv[2], sys.argv[3])

    elif command in ("promote", "ghost", "delete"):
        if len(sys.argv) < 3:
            print(f"Usage: entity-curate {command} <entity_id>")
            return
        cli_entity_curate(graph, sys.argv[2], command)

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
