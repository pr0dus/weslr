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
- commit: `d1e6739`
- backup: `CircleForge-backup-20260321-185842.tar.gz`
- tag: `v0.0.52`

### v0.0.53
- artifact substance scoring added for generated modules, optimization notes, and research notes
- thin-artifact and description-mismatch penalties added so weak payloads no longer inherit inflated human/sellability scores
- explainability now calls out when artifact framing outruns underlying substance
- intended direction: reward honest emergence and punish hollow packaging before adding richer generators
- backup: `CircleForge-backup-20260321-235322.tar.gz`
- tag: `v0.0.53`

### v0.0.54
- guided `setup` command added for first-run testing
- setup now asks for agent count, tick count, interval, and dashboard refresh settings
- infinite mode is now explicit in setup via `0` / `inf` / `infinite` / `forever`
- setup prints the exact absolute dashboard path and `file://` URL to open in a browser
- README and install flow updated so testers land in setup instead of a half-finished manual path
- intended direction: reduce tester confusion and make the first local run self-explanatory

### v0.0.55
- built-in dashboard HTTP server added via `serve`
- setup can now start the dashboard on a LAN-accessible port after rendering
- setup now prints an exact `http://<lan-ip>:<port>/` address for browser use
- `run.sh serve` and LAN-serving setup examples added to the README
- intended direction: remove browser/file-URL friction and make dashboard access work like a normal local web app

### v0.0.56
- dashboard live refresh now polls `dashboard.json` instead of reloading the whole page
- current hash/section/detail view is preserved during refresh
- current scroll position is preserved when no anchor/detail target is active
- refresh note in the UI now explains that live data updates do not reset the current view
- intended direction: make the operator dashboard behave like a real live console instead of bouncing users back to the top

### v0.0.57
- runtime `opportunity_board.json` removed from tracked source and fully treated as generated state
- README cleaned up and linked to the new planning/architecture docs
- `WORLD-MODEL.md` added to define canonical post-v0.1 world objects
- `SELF-MODIFICATION.md` added to define safe self-inspection and self-change rules
- `AGENT-TIME.md` added to define per-agent cadence, wake reasons, and future time ecology
- intended direction: keep the repo clean while turning the grand vision into buildable architecture

### v0.0.58
- initial world-object substrate added: `needs`, `messages`, `public_memory`, and `projects`
- world init now seeds a minimal public-memory layer and starter projects
- successful agent signals are now persisted into the world message log
- unresolved runtime friction now becomes persistent public needs with decay/cooling behavior
- dashboard and CLI now expose early world-object visibility via `world-objects`
- intended direction: begin implementing the canonical world model without breaking the current simulation loop

### v0.0.59
- soft per-agent cadence added via `next_due_tick`, `wake_reason`, and `cadence_interval`
- agents can now remain idle until due instead of acting in perfect lockstep every tick
- wake reasons now distinguish scheduled cadence, message-driven wakeups, unresolved-need pressure, and waiting states
- protected self-edit boundary added in code/config so core safety files and rules are not self-modifiable by emergence logic
- self-modification docs extended with an explicit future note for full auto-editing under bounded human-safe conditions
- intended direction: make the ecology less toy-synchronous while preventing future self-editing from erasing human safety constraints

### v0.0.60
- relationship memory layer added between agents with trust, usefulness, friction, and last-event tracking
- successful inspect/trade/signal interactions now update relationship state
- message routing now attaches lightweight project context when a theme maps onto an active project
- proposal-only self-modification objects added for repeated friction; they target private agent helpers only
- dashboard and CLI now expose `relationships` and `self-mod-proposals`
- intended direction: make coordination and capability growth more social while keeping self-editing bounded and reviewable

### v0.0.61
- relationship-aware target selection added so agents prefer more trusted/useful and lower-friction peers
- repeated-friction proposal triggering tightened so self-mod proposals emerge from repeated matching issues, not just one-off noise
- initial `work-items` layer added and seeded from projects
- agents can now bias action selection toward assigned open work items
- project routing now replenishes follow-up work and work items can progress toward done status
- intended direction: make shared work and social memory affect actual behavior instead of just being passive state

### v0.0.62
- `CORE-IDENTITY.md` added to freeze project drift and define CircleForge as a local self-evolving communicator entity with internal minds
- core framing now explicitly centers one visible communicator over 4–5 internal agent/subprocess perspectives
- README updated to point future design choices toward communicator identity, intention, curiosity, and self-waking behavior
- intended direction: stop architectural wobble and make future coding decisions serve a single identity

### v0.0.63
- first visible communicator state added with status, current intent, curiosity, dominant need, and last decision summary
- internal agents now generate lightweight internal thought proposals with role-like stances such as support, question, and prioritize
- first intent integration loop added so the communicator forms a top-level intent from internal proposals rather than exposing only raw agent activity
- dashboard and CLI now expose the communicator as a first-class visible layer
- intended direction: shift CircleForge from a many-agent surface toward one communicator with internal minds

### v0.0.64
- communicator now keeps short intent history for continuity across ticks
- communicator intent now biases later internal proposals and fallback decisions instead of being only a summary layer
- coordinator role promoted into the active internal integration loop
- curiosity pressure can now wake observer/critic-style internal minds and bias behavior toward inspect/research
- intended direction: make the communicator influence ongoing thought, not just describe the last result

### v0.0.65
- communicator now stores unresolved objections from questioning internal voices
- internal disagreement can now change decision mode to `inspect-first`, `reconsider`, or `defer` instead of always acting immediately
- reflective communicator decisions now leave public-memory traces for later learning
- dashboard communicator panel now shows objection count
- intended direction: make internal disagreement consequential so the communicator can reflect before acting

### v0.0.66
- communicator now has explicit intention fields: `active_pursuit`, `unresolved_question`, `curiosity_target`, `attraction_bias`, and `avoidance_bias`
- internal proposal scoring now considers pursuit and curiosity-target alignment in addition to current intent
- fallback decisions can now follow active pursuit and curiosity target, not only the latest intent string
- communicator panel now exposes these intention fields directly
- intended direction: give the communicator a richer inner orientation than just last-action intent

### v0.0.67
- unresolved-question pressure now wakes observer/critic/memory-oriented internal minds
- unresolved questions now bias proposal scoring and fallback behavior toward inspect/research continuation
- communicator unresolved question is now revised over time instead of remaining static text
- communicator panel now shows attraction/avoidance bias more explicitly alongside question state
- intended direction: turn question state into an actual ongoing inquiry mechanism

### v0.0.68
- communicator now keeps `question_history` in addition to current unresolved question
- simple question resolution / successor-question chaining added after inspect/research-oriented progress
- question lineage is now visible in the communicator panel via lineage count
- intended direction: let the communicator carry chains of inquiry instead of isolated question text

### v0.0.69
- communicator question lineage now syncs into world state as public-memory question traces
- active communicator questions can now create/update public exploratory needs
- active communicator questions can now spawn inquiry-flavored work items tied to the active project/pursuit
- intended direction: connect internal inquiry to the wider world model so questions shape shared history and future work

### v0.0.70
- experiment objects added as first-class generated world state
- active communicator questions can now create/update experiments with hypothesis, status, observations, and follow-up
- CLI/dashboard world-object views now expose experiments
- intended direction: turn inquiry into bounded attempts instead of only remembered questions and work pressure

### v0.0.71
- running/proposed experiments now feed back into wake pressure for observer/critic/memory-style internal minds
- proposal scoring now gives extra weight to themes already under active experiment
- fallback behavior now follows running experiment pressure, pushing inspect/research/optimize loops around the active pursuit
- communicator curiosity target can now lock onto active experiment titles
- intended direction: make inquiry attempts affect future thought instead of sitting passively in world state

### v0.0.72
- experiment progress now feeds into relationship updates, increasing usefulness/trust around owners linked to active inquiry
- proposed-but-unresolved experiment state can now sharpen communicator caution/avoidance bias
- intended direction: let lived inquiry reshape the social/epistemic ecology, not just task flow
