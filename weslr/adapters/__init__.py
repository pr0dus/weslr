"""Weslr Source Adapters (v1)

Adapters for external source signal ingestion (Reddit, GitHub).
Each adapter produces SourceSignal objects for the capability ingestion pipeline.

All adapters follow the same pattern:
1. Parse input (file, dict, API response)
2. Extract signal fields (title, url, body, tags, provenance)
3. Return SourceSignal object
4. Preserve source metadata for provenance tracking

Phase 3: Minimal real-source adapters - Reddit and GitHub only.
"""

from .reddit_adapter import RedditAdapter, RedditSignal
from .github_adapter import GitHubAdapter, GitHubSignal

__all__ = [
    "RedditAdapter",
    "RedditSignal",
    "GitHubAdapter",
    "GitHubSignal",
]
