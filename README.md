# CircleForge

**CircleForge v0.0.28** is a lightweight persistent agent sandbox for local machines.
Agents act on timed cycles, keep private memory, generate helper modules, annotate artifacts, surface promising outputs through queues and review, and now evolve a more realistic category system with uncategorized handling, imperfect voting, and dormant-category detection.

## New in v0.0.28

- `uncategorized` is now a valid temporary home for good weird artifacts
- category voting is less automatic and more selective
- underused categories can be marked dormant
- strong uncategorized artifacts can signal demand for new categories

## Why `uncategorized` matters

If an artifact does not fit any current category but still scores well, it should not be treated as bad.
Instead, CircleForge can:
- keep it in `uncategorized`
- still score and review it normally
- use repeated high-value uncategorized artifacts as evidence that a new category may be needed

## Category governance

Rules now include:
- more than 50% support to approve a category
- max 20 categories
- small proposal cost
- small rejection penalty
- dormant-category detection for underused categories

## What should come next

- lineage fields and parent/derived tracking
- manual category governance controls
- category retirement / revival logic
- richer failure-driven demand signals
- richer pack manifests and install templates
- replay dashboard
