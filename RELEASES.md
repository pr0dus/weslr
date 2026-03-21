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

### v0.0.48
- richer dashboard with agent opportunity-memory panels
- dashboard history snapshots added for lightweight trend tracking
- pack outcome visibility improved in the operator view
- intended direction: make the dashboard useful for monitoring, not just inspection
- commit: `8217af9`
- backup: `CircleForge-backup-20260321-155808.tar.gz`
- tag: `v0.0.48`

### v0.0.49
- dashboard drill-downs for top themes and top packs
- event feed for lifecycle changes and pack outcome changes
- safe-resume memory notes updated for future large-context sessions
- commit: `42d0967`
- backup: `CircleForge-backup-20260321-161724.tar.gz`
- tag: `v0.0.49`

### v0.0.50
- clickable dashboard navigation added with anchor links for world/themes/packs/artifacts/events
- artifact detail views added to the dashboard surface for top queued/packed artifacts
- persistent event log added outside transient dashboard history to keep operator-visible change memory
- runtime dashboard history / event log files excluded from commits for cleaner rollback hygiene
- commit: `04f1ad9`
- backup: `CircleForge-backup-20260321-164535.tar.gz`
- tag: `v0.0.50`

### v0.0.51
- dashboard auto-refresh/watch loop added for lightweight live monitoring
- clearer operator action commands surfaced directly in the dashboard
- theme trend snapshots now render short history sparklines for monitoring drift over time
- commit: `a389256`
- backup: `CircleForge-backup-20260321-164815.tar.gz`
- tag: `v0.0.51`

### v0.0.52
- explainability split added for artifacts and packs: internal strength, external proof, risks, and next actions
- pack offer brief generation added with weak-proof pack reporting
- runtime JSON handling hardened with blank-file tolerance and atomic writes
- intended direction: tighten operator-to-offer workflow and reduce brittleness before v0.1 synthesis
- commit: pending
- backup: pending
- tag: pending
