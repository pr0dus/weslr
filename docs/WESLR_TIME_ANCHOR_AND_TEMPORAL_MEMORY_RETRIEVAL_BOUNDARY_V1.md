# WESLR Time Anchor and Temporal Memory Retrieval Boundary V1

## SECTION 1 — Executive doctrine

WESLR memory retrieval must be time-aware.

Temporal phrases are not just semantic content. They are retrieval constraints.

If the owner says “yesterday,” WESLR should first determine the exact local time window for yesterday before searching memory.

This improves:
- continuity
- trust
- recall precision
- session navigation
- project handover accuracy
- friction replay
- owner workflow

## SECTION 2 — Current gap

WESLR already has many planning and artifact helpers, but no explicit time-anchor layer yet.

Without time anchoring:
- “yesterday” may become vague semantic search
- “last session” may retrieve wrong context
- “before that commit” may be misunderstood
- “what did I say earlier” may lack source boundaries
- memory retrieval may mix unrelated days/sessions

## SECTION 3 — Time anchor layer position

Correct order:
1. parse user request
2. detect temporal references
3. resolve reference time
4. resolve local timezone/calendar day
5. build time-window packet
6. select source scope
7. retrieve candidate memories/logs/docs
8. rank temporal matches
9. answer with confidence / uncertainty

The time anchor layer must run before memory retrieval when temporal references are present.

## SECTION 4 — Temporal expression classes

Supported classes:
- absolute date: `2026-06-01`, `May 30`
- relative day: `yesterday`, `today`, `tomorrow`
- relative range: `last week`, `last month`, `past few days`
- day part: `this morning`, `last night`, `yesterday evening`
- session-relative: `last session`, `previous conversation`, `earlier in this chat`
- project-relative: `before the last commit`, `after the last lane`, `when we implemented X`
- event-relative: `after I sent the report`, `before OCC replied`
- vague temporal: `recently`, `a while ago`, `the other day`

## SECTION 5 — Time window packet

Future packet fields:
- `time_anchor_id`
- `original_phrase`
- `anchor_type`
- `reference_time`
- `timezone`
- `resolved_start`
- `resolved_end`
- `calendar_basis`
- `confidence`
- `needs_clarification`
- `source_scope_hint`
- `project_scope_hint`
- `session_scope_hint`
- `event_anchor`
- `commit_anchor`
- `safe_metadata`

Examples:
- yesterday → previous local calendar day 00:00:00 to 23:59:59
- this morning → current local day 05:00 to 12:00
- last week → previous local calendar week
- previous session → most recent session before current one
- after commit X → commit timestamp or lane report timestamp if available

## SECTION 6 — Timezone doctrine

Use local/user timezone where known.

For this owner, default likely Europe/Berlin unless runtime has stronger source.

Do not assume UTC for owner-facing phrases like “yesterday.”

Store timezone in the packet.

If timezone is unknown:
- use runtime/user timezone if available
- otherwise mark lower confidence
- ask clarification only if needed

## SECTION 7 — Source scope decision

After time anchor resolution, decide where to retrieve from:
- current conversation
- prior conversation summaries
- project memory
- WESLR docs/reports
- repo commit history metadata
- `.weslr` runtime memory later, if approved
- session logs later, if approved
- uploaded files, if explicitly in scope

This is source-scope planning only. No private data reading or dumping.

## SECTION 8 — Retrieval modes

Retrieval strategies:
1. temporal-first retrieval — time window first, then semantic filter
2. semantic-first retrieval — topic first, then time boost
3. hybrid retrieval — both time window and topic
4. event-anchor retrieval — commit/lane/report/event based

Rule:
- If the owner says “what did I say yesterday,” temporal-first dominates.
- If the owner says “what did I say yesterday about WiFi sensing,” use hybrid retrieval.

## SECTION 9 — Confidence and uncertainty

WESLR must answer honestly:
- high confidence: exact time window and matching records found
- medium confidence: window resolved but partial records
- low confidence: vague temporal phrase or incomplete records
- blocked: source not accessible or memory unavailable

If unavailable:
- do not fabricate
- say retrieval source is unavailable or incomplete

## SECTION 10 — Relationship to memory

Memory retrieval should not be one flat search.

Future order:
- time anchor
- namespace/source scope
- memory retrieval
- semantic ranking
- contradiction/friction check
- answer formation

This avoids pulling wrong memories from wrong dates/users/projects.

## SECTION 11 — Relationship to WESLR project workflow

Temporal anchoring matters for:
- OCC handovers
- lane history
- commit sequence
- “last report”
- “yesterday’s decision”
- “before this implementation”
- “what did we say about public claims?”
- “when did we decide to pause chat route?”

It should support project-relative anchors:
- before/after commit
- before/after lane
- before/after report
- before/after owner decision

## SECTION 12 — Safety and privacy boundaries

Forbidden:
- raw private log dumping
- hidden prompt exposure
- cross-user retrieval
- unauthorized `.weslr` reads
- private data persistence
- public ISS wording
- AGI/consciousness/sentience/Turing/certification claims
- runtime authority
- file writes
- model/provider/search calls

The layer may produce only metadata plans and safe summaries.

## SECTION 13 — Future helper design

Recommended future helper:
`weslr/time_anchor_resolver.py`

Public APIs later:
- `build_time_anchor_packet_v1(...)`
- `resolve_time_anchor_v1(...)`
- `validate_time_anchor_packet_v1(packet)`
- `summarize_time_anchor_packet_v1(packet)`
- `to_time_anchor_json_safe_v1(value)`
- `build_initial_time_anchor_examples_v1()`

Possible follow-up helper:
`weslr/temporal_memory_retrieval_plan.py`

Public APIs later:
- `build_temporal_memory_retrieval_plan_v1(...)`
- `validate_temporal_memory_retrieval_plan_v1(plan)`
- `summarize_temporal_memory_retrieval_plan_v1(plan)`

## SECTION 14 — Example cases

1. “What did I say yesterday?”
- anchor: yesterday
- mode: temporal-first
- source: owner conversation/session memory
- answer only if retrieval available

2. “What did we decide last week about WESLR public wording?”
- anchor: last week
- semantic topic: WESLR public wording
- mode: hybrid

3. “Before the file manifest builder, what came next?”
- project-relative anchor
- source: lane/commit history
- mode: event-anchor retrieval

4. “Earlier in this chat I said something about ISS.”
- session-relative anchor
- source: current conversation
- mode: temporal/session-first

5. “The other day I mentioned WiFi sensing.”
- vague temporal + semantic
- lower confidence or clarification may be needed

## SECTION 15 — Implementation sequence recommendation

Recommended sequence:
1. `IMPLEMENT_WESLR_TIME_ANCHOR_RESOLVER_V1`
2. `DESIGN_WESLR_TEMPORAL_MEMORY_RETRIEVAL_PLAN_V1`
3. `IMPLEMENT_WESLR_TEMPORAL_MEMORY_RETRIEVAL_PLAN_V1`
4. integrate with future memory retrieval/source-scope helpers
5. only later connect to live chat route after guarded review

Code scaffold generator can resume after this design or after resolver implementation, depending on owner priority.

## SECTION 16 — Boundaries

Confirmed:
- design only
- no runtime change
- no chat route
- no memory read
- no `.weslr` access
- no model/provider/search/advisor calls
- no file writes except this design doc
- protected files untouched

## SECTION 17 — Final judgment

`time_anchor_temporal_memory_boundary_design_ready_for_resolver_implementation`
