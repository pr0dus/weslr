# CircleForge

**CircleForge v0.0.27** is a lightweight persistent agent sandbox for local machines.
Agents act on timed cycles, keep private memory, generate helper modules, annotate artifacts, surface promising outputs through queues and review, and now organize export-ready work into governed artifact categories and packs.

## What CircleForge is

CircleForge is a minimal but runnable prototype for:
- persistent coding agents
- 60-second world ticks
- short bounded execution windows
- local-model decisions through Ollama
- fallback behavior when Ollama is unavailable
- sandboxed generated Python
- SQLite-backed world state
- artifact metadata with dual scoring
- demand tracking and export-candidate surfacing
- review queue and export-ready promotion
- governed category proposals and artifact packs

## New in v0.0.27

- artifact packs grouped by category
- governed category proposals and voting
- >50% approval required to add a new category
- hard cap of **20** categories total
- lightweight proposal cost and rejection penalty
- export-ready artifacts are grouped into category packs

## Category governance

CircleForge starts with a small base category set and lets agents propose more.
A category proposal needs:
- proposer
- reason
- suggested use
- votes for / against

Rules:
- proposals cost a little energy
- rejected proposals carry a small reputation penalty
- more than 50% of active agents must vote yes
- total category count cannot exceed 20

## Human review flow

Artifacts carry review-oriented fields such as:
- `review_status`
- `review_notes`
- `approved_for_export`
- `export_path`
- `category`

## Files

- `categories.json` - current approved category list
- `category_proposals.json` - pending/approved/rejected category proposals
- `artifact_packs.json` - export-ready artifacts grouped into packs
- `demand_board.json` - generated demand signals
- `export_queue.json` - generated ranked export candidates
- `review_queue.json` - generated human-review shortlist
- `exports/` - export-ready artifact snapshots

## Useful commands

```bash
python3 main.py init --reset --agents 5
python3 main.py tick --verbose
python3 main.py run --ticks 20 --interval 60
python3 main.py show-world
python3 main.py show-agent agent-1
python3 main.py review <artifact-id> approve --note "looks good"
python3 main.py version
```

## Status

This is **v0.0.27**: an early release with inspect/trade, artifact metadata, dual scoring, review/export flow, category governance, and artifact packs.

## What should come next

- manual category proposal/review CLI controls
- dormant/archived categories
- richer failure-driven demand signals
- richer pack manifests and install templates
- replay dashboard
