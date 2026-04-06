#!/usr/bin/env python3
"""Run curated ingestion pass on the curated batch."""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from capability_ingestion import (
    CapabilityDiscoveryRadar, 
    CapabilitySuggestionStore, 
    SourceSignal,
    SourceKind,
    CapabilityIngestionPipeline,
    SignalStatus
)
from adapters.reddit_adapter import RedditAdapter
from adapters.github_adapter import GitHubAdapter
from adapters.reddit_adapter import RedditSignal
from adapters.github_adapter import GitHubSignal

def main():
    batch_path = Path(__file__).parent / "test_data" / "curated_batch.json"
    
    print("=" * 60)
    print("SECTION 2 — INGESTION RUN")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = CapabilityIngestionPipeline()
    store = pipeline.store
    
    # Load curated batch
    print(f"\nLoading curated batch from: {batch_path}")
    
    # Process Reddit signals
    reddit_adapter = RedditAdapter()
    reddit_signals_raw = reddit_adapter.from_file(batch_path)
    print(f"\nReddit signals loaded: {len(reddit_signals_raw)}")
    for s in reddit_signals_raw:
        print(f"  - {s.title}")
    
    # Process GitHub signals  
    github_adapter = GitHubAdapter()
    github_signals_raw = github_adapter.from_file(batch_path)
    print(f"\nGitHub signals loaded: {len(github_signals_raw)}")
    for s in github_signals_raw:
        print(f"  - {s.title}")
    
    # Merge all signals
    all_signals = reddit_signals_raw + github_signals_raw
    print(f"\nTotal signals: {len(all_signals)}")
    
    # Ingest each signal
    source_signals_created = 0
    suggestions_created = 0
    duplicates = 0
    
    for sig in all_signals:
        # Create SourceSignal directly (skip adapter conversion)
        signal = SourceSignal(
            id=sig.id,
            source_kind=sig.source_kind,
            title=sig.title,
            url=sig.url,
            body=sig.body,
            snippet=sig.snippet,
            tags=sig.tags,
            detected_capability=sig.detected_capability,
            source_timestamp=sig.source_timestamp,
            provenance=sig.provenance,
            confidence=sig.confidence,
        )
        source_signals_created += 1
        
        # Ingest through pipeline
        result = pipeline.ingest_signal(signal)
        
        if result["status"] == "ingested":
            suggestions_created += 1
            print(f"\n  Ingested: {signal.title}")
            print(f"    Suggestion ID: {result['suggestion_id']}")
            print(f"    Provenance: {signal.provenance}")
        elif result["status"] == "duplicate":
            duplicates += 1
            print(f"\n  DUPLICATE: {signal.title}")
            print(f"    Original: {result['duplicate_of']}")
        else:
            print(f"\n  REJECTED: {signal.title}")
            print(f"    Error: {result.get('error', 'unknown')}")
    
    # Report summary
    print("\n" + "=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)
    print(f"Source signals created: {source_signals_created}")
    print(f"Suggestions created: {suggestions_created}")
    print(f"Duplicates detected: {duplicates}")
    
    # Show top suggestions
    print("\nTop pending suggestions:")
    from capability_suggestion import SuggestionStatus
    top = store.list_all(status=SuggestionStatus.NEW, include_archived=False)
    for s in sorted(top, key=lambda x: x.priority, reverse=True)[:10]:
        print(f"  - {s.title} (priority: {s.priority}) - {s.provenance}")
        print(f"      {s.capability_type.value} | {s.description[:80]}...")
    
    # Show provenance summary
    print("\nProvenance summary:")
    provenance_counts = {}
    for s in top:
        key = str(s.provenance)
        provenance_counts[key] = provenance_counts.get(key, 0) + 1
    for key, count in sorted(provenance_counts.items()):
        print(f"  {key}: {count}")
    
    return store

if __name__ == "__main__":
    store = main()
