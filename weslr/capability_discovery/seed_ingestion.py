"""Capability Discovery Radar - Seed Ingestion Pipeline.

Load and ingest from seed sources into the existing capability ingestion pipeline.
This provides a controlled way to bootstrap discovery from curated sources.

DO NOT add live crawling yet - this is sample/curated source entries first.
"""

from __future__ import annotations

import json
from typing import List, Dict, Any, Optional

# Relative import
try:
    from .seeds import SeedSource, SeedKind, get_enabled_seeds
    from .ingestion import CapabilityIngestionPipeline, SourceSignal, SourceKind
    from .store import CapabilityStore, get_store
except ImportError:
    from seeds import SeedSource, SeedKind, get_enabled_seeds
    from ingestion import CapabilityIngestionPipeline, SourceSignal, SourceKind
    from store import CapabilityStore, get_store


class SeedIngestionPipeline:
    """Ingests signals from seed sources."""

    def __init__(self, store: Optional[CapabilityStore] = None):
        self.store = store or get_store()
        self.ingestion_pipeline = CapabilityIngestionPipeline(self.store)

    def seed_to_signal(self, seed: SeedSource) -> SourceSignal:
        """Convert a seed source to a SourceSignal for ingestion."""
        return SourceSignal(
            id=f"seed-{seed.id}",
            source_kind=SourceKind.OTHER,  # Seeds use custom handling
            title=seed.name,
            url=seed.url,
            snippet=seed.description or "",
            body=seed.description or "",
            tags=seed.tags,
            detected_capability=seed.category,
            confidence=0.8 if seed.enabled else 0.3,  # Higher confidence for enabled
        )

    def ingest_seed(self, seed: SeedSource) -> Dict[str, Any]:
        """Ingest a single seed source."""
        signal = self.seed_to_signal(seed)
        result = self.ingestion_pipeline.ingest_signal(signal)
        return result

    def ingest_all_enabled(self) -> List[Dict[str, Any]]:
        """Ingest all enabled seeds."""
        results = []
        for seed in get_enabled_seeds():
            result = self.ingest_seed(seed)
            results.append(result)
        return results

    def ingest_by_kind(self, kind: SeedKind) -> List[Dict[str, Any]]:
        """Ingest seeds of a specific kind."""
        results = []
        for seed in get_enabled_seeds():
            if seed.kind == kind:
                result = self.ingest_seed(seed)
                results.append(result)
        return results

    def ingest_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Ingest seeds in a specific category."""
        results = []
        for seed in get_enabled_seeds():
            if seed.category == category:
                result = self.ingest_seed(seed)
                results.append(result)
        return results


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI interface for seed ingestion."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python capability_discovery/seed_ingestion.py <command> [args]")
        print("Commands:")
        print("  all              - Ingest all enabled seeds")
        print("  kind <kind>      - Ingest seeds by kind (reddit, github, science, pkm)")
        print("  category <cat>   - Ingest seeds by category")
        print("  list             - List enabled seeds")
        print("  summary          - Show ingestion summary")
        sys.exit(1)

    command = sys.argv[1]
    store = get_store()
    pipeline = SeedIngestionPipeline(store)

    if command == "all":
        results = pipeline.ingest_all_enabled()
        print(f"Ingested {len(results)} seeds")
        for r in results:
            print(f"  {r['signal_id']}: {r['status']}")

    elif command == "kind":
        if len(sys.argv) < 3:
            print("Usage: python capability_discovery/seed_ingestion.py kind <kind>")
            print("Kinds: reddit, github, science, pkm")
            sys.exit(1)
        kind = sys.argv[2]
        kind_map = {
            "reddit": SeedKind.REDDIT_COMMUNITY,
            "github": SeedKind.GITHUB_REPO,
            "science": SeedKind.SCIENCE_SOURCE,
            "pkm": SeedKind.PKM_ANCHOR,
        }
        results = pipeline.ingest_by_kind(kind_map.get(kind, SeedKind.OTHER))
        print(f"Ingested {len(results)} seeds of kind {kind}")

    elif command == "category":
        if len(sys.argv) < 3:
            print("Usage: python capability_discovery/seed_ingestion.py category <category>")
            sys.exit(1)
        category = sys.argv[2]
        results = pipeline.ingest_by_category(category)
        print(f"Ingested {len(results)} seeds in category {category}")

    elif command == "list":
        seeds = get_enabled_seeds()
        print(f"Enabled seeds ({len(seeds)}):")
        for s in seeds:
            print(f"  {s.id}: {s.name} [{s.kind.value}] - {s.category}")

    elif command == "summary":
        from .store import get_store
        store = get_store()
        suggestions = store.list_suggestions(limit=100)
        by_provenance: Dict[str, int] = {}
        for s in suggestions:
            for p in s.provenance:
                by_provenance[p.signal_type] = by_provenance.get(p.signal_type, 0) + 1
        summary = {
            "total_suggestions": len(suggestions),
            "by_provenance": by_provenance,
        }
        print(json.dumps(summary, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
