# CircleForge Release Ledger

This file is the human-readable rollback map for CircleForge.

Use it alongside git tags and backup archives so it is easy to answer:
- what changed in each version
- what the intended direction was
- what backup/tag to return to if a new step goes wrong

## Rollback policy

For every meaningful version step:
- update `config.py` version
- add a short entry here
- create a backup archive in the workspace root
- create/push a git tag when the state is verified

Recommended rollback order:
1. inspect `RELEASES.md`
2. choose a git tag
3. if needed, restore from the matching backup archive

## Releases

### v0.0.40
- category-aware publishing templates
- delivery-mode recommendations
- stronger buyer/problem/install framing in wrappers and handoffs
- commit: `ed47673`

### v0.0.41
- proof-weighted monetization via SQLite `artifact_proof`
- explain output connected to tracked evidence
- commit: `2639b04`

### v0.0.42
- external validation signals with `validate`
- artifact-level real usage / buyer-fit / acceptance / rejection / revision outcomes
- commit: `2f7aa3d`

### v0.0.43
- sellability model introduced
- opportunity model introduced
- entity-defined niche metadata on artifacts
- prompt steering removed in favor of opportunity memory + world pressure mechanics
- opportunity-theme pack grouping introduced
- rejection learning for opportunity themes introduced
- commits:
  - `d9a709e`
  - `4f8b111`
  - `b7136b4`
  - `3e9bb8a`
  - `d850d3b`

### v0.0.44
- opportunity theme clustering / merge support introduced
- version ledger added for rollback clarity
- intended direction: fewer isolated labels, more emerging niche families with explicit revert points
- commit: `9c544d3`
- backup: `CircleForge-backup-20260321-152102.tar.gz`
- tag: `v0.0.44`

### v0.0.45
- pack-level offer/test/outcome tracking introduced
- pack outcomes now feed back into clustered opportunity themes
- packs carry offer / accept / reject / revision counters
- `pack` CLI command added for recording pack-level outcomes
- commit: `9f81fdc`
- backup: `CircleForge-backup-20260321-152717.tar.gz`
- tag: `v0.0.45`

### v0.0.46
- theme lifecycle states introduced
- dormancy / decay / decline behavior added
- overloaded themes can split into emergent subthemes
- repeated signals can register emergent theme candidates
- intended direction: stabilize the opportunity ecology before building the operator dashboard
- commit: `f45876a`
- backup: `CircleForge-backup-20260321-154511.tar.gz`
- tag: `v0.0.46`

### v0.0.47
- operator dashboard renderer introduced
- local HTML/JSON visibility layer added for themes, packs, queues, logs, and release ledger
- intended direction: make CircleForge legible to human operators without requiring JSON spelunking
- commit: `c15abf1`
- backup: `CircleForge-backup-20260321-154938.tar.gz`
- tag: `v0.0.47`
