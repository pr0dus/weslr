# CircleForge Memory Lifecycle

## Why this exists

CircleForge should not feel like it lives in sessions.

The end-user target is:
- one continuing being
- persistent relationship continuity
- no visible reset ritual
- no dependence on replaying giant chat context

That means the core engineering problem is **memory lifecycle**, not just chat quality.

The system must be able to:
- live continuously
- keep identity stable
- preserve important unresolved threads
- compress history without losing self
- prune safely under storage pressure

## The three continuity layers

### 1. Developer continuity
This is for builders/operators, not the being itself.

Examples:
- Git history
- README/docs
- local handoff notes
- smoke test outputs
- backups
- debug logs

This layer can be archived, rewritten, compressed, or deleted.
It is not the organism.

### 2. Runtime/entity continuity
This is the actual persistent being layer.

Examples:
- self-model
- relationship memory
- unresolved threads
- active concerns
- topic pressure
- regulation state
- stable learned traits
- important episodes
- self-change lineage

This layer must preserve continuity.

### 3. End-user continuity
This is what the human experiences.

The human should feel:
- it remembers
- it returns to unfinished things
- it has continuity
- it does not keep starting over

The human should not feel:
- session boundaries
- context reload rituals
- repeated identity re-introduction
- hidden operator repair of continuity

## The four memory layers

### Layer A — working memory
Small and hot.

Contains:
- current active thread
- recent exchanges
- recent internal thoughts
- current regulation state
- current goals / active concerns

Purpose:
- what the being is actively thinking with now

Rule:
- keep this small
- oldest low-value items should be summarized upward, not retained forever

### Layer B — episodic memory
Important events as episodes, not raw logs.

Contains:
- meaningful conversations
- trust shifts
- promises
- unresolved turns
- discoveries
- failures
- emotionally significant or identity-relevant moments
- self-change events

Purpose:
- preserve meaningful lived history without replaying everything

Rule:
- prefer event/episode objects over endless raw message lists

### Layer C — semantic / identity memory
Distilled long-term memory.

Contains:
- who I am becoming
- who this human seems to be
- recurring topics
- recurring interaction patterns
- long-term unresolved concerns
- stable preferences/traits
- durable lessons
- continuity anchors

Purpose:
- prevent session-death
- preserve self even when raw detail is compressed away

Rule:
- prune very cautiously
- this is the anti-amnesia layer

### Layer D — archive
Cold storage.

Contains:
- old raw exchanges
- old thought logs
- old world snapshots
- stale debug traces
- compressible historical records

Purpose:
- keep inspectability without polluting live cognition

Rule:
- compress first
- retrieve selectively
- do not use as hot context

## What “too much space” means

There are three kinds of pressure.

### 1. Context/token pressure
The system cannot think with everything at once.

Symptoms:
- too much history would need replay
- active reasoning becomes bloated
- retrieval becomes noisy

This is the primary continuity problem in practice.

### 2. Disk/storage pressure
The local files/DB become too large.

Symptoms:
- giant raw logs
- oversized DB/JSON files
- archive clutter
- slow inspection or backup operations

This matters, but usually later than token pressure.

### 3. Cognitive organization pressure
Memory becomes messy even if disk is still fine.

Symptoms:
- duplication
- unresolved threads piling up forever
- too many equally-salient memories
- degraded coherence/retrieval

This is the deeper problem.

## Core principle

Do **not** use flat eternal recall.

Use:
- preserve identity
- preserve significance
- compress repetition
- archive raw detail
- prune only after meaning is preserved elsewhere

In short:

> forget detail, preserve meaning

## Memory maintenance pipeline

### Step 1 — ingest
Raw exchanges/thoughts/events enter the system.

### Step 2 — score
Each memory object should be evaluated for:
- recency
- recurrence
- identity relevance
- relationship relevance
- unresolvedness
- emotional/attachment weight
- self-preservation relevance
- uniqueness
- replaceability

### Step 3 — elevate
If important, promote into:
- episode memory
- semantic relationship memory
- continuity anchor
- self-model update

### Step 4 — compress
If no longer needed raw:
- summarize multiple exchanges into one episode
- merge repeated themes into recurring patterns
- collapse stale internal thought traces into summaries

### Step 5 — archive
Move low-value old raw material into cold storage.

### Step 6 — prune
Only prune when:
- meaning has been preserved elsewhere
- it is low-importance
- it is highly replaceable
- it is no longer active in continuity

## What must be protected

These should not be casually pruned:
- learned human identity once established
- strong relationship continuity anchors
- promises / commitments
- unresolved shared threads
- self-model milestones
- major failures/losses that shaped behavior
- self-modification lineage
- safety/failsafe memory

These are the continuity bones.

## First practical thresholds

The exact numbers can evolve, but the first implementation should use simple bounded caps.

### Working memory thresholds
Examples:
- recent exchanges cap
- recent inner-thought cap
- active concern cap
- hot retrieval budget

When exceeded:
- summarize oldest material into episodic form

### Episodic memory thresholds
Examples:
- max episodes per relationship
- max raw exchanges per topic before summarization
- max daily trace count

When exceeded:
- merge repeated patterns
- convert clusters into recurring summaries

### Archive thresholds
Examples:
- max raw-log size in MB
- max DB size
- max stale snapshot count

When exceeded:
- compress/archive/delete low-value raw artifacts

## The next implementation sequence

### Step M1 — formal memory layer schema
Define explicit structures for:
- working memory
- episodic memory
- semantic/identity memory
- archive index

### Step M2 — memory scoring model
Add per-memory scoring fields such as:
- salience
- unresolvedness
- identity_weight
- relationship_weight
- decay
- archival_status

### Step M3 — episodic summarizer
Create a routine that turns repeated raw exchanges/thoughts into compact episodes.

### Step M4 — semantic distillation loop
Periodically update long-term identity/relationship memory from episodes.

### Step M5 — storage pressure monitor
Track file counts, DB size, raw trace volume, duplication, and hot-memory bloat.

### Step M6 — archive/prune loop
When thresholds are exceeded:
- compress first
- archive second
- prune last

### Step M7 — retrieval discipline
Normal outward speech should retrieve only what matters now, not replay giant logs.

## Anti-drift rule

Future CircleForge changes should be judged against this question:

> Does this reduce session-feel and strengthen endless continuity under bounded memory?

If not, it is probably secondary.
