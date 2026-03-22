# CircleForge Agent Time Model

## Purpose

This document defines the future move from one global synchronized tick toward a richer time ecology.

A single world tick is a useful early simplification.
But if CircleForge is meant to feel more alive, agents should not all act in lockstep forever.

---

## Why per-agent ticks matter

Per-agent time allows:
- different rhythms of work
- event-triggered wakeups
- urgency-sensitive behavior
- long-running and short-running entities to coexist
- more believable dormancy and bursts of activity

This is one of the clearest ways to move away from toy-sim feeling.

---

## Current model

Current CircleForge mainly uses:
- one world tick counter
- one run cadence
- one execution pass over all agents

That is fine for early coherence and debugging.
But later it limits emergence because:
- everyone acts at the same pace
- urgency cannot meaningfully differ
- idle agents still participate on the same schedule
- there is little notion of interruption or wake reason

---

## Future model

CircleForge should move toward two layers of time:

### Layer 1 — World time
Global timeline for:
- major events
- public decay/evolution
- shared object updates
- dashboard history

### Layer 2 — Agent-local time
Per-agent cadence for:
- waking
- sleeping
- reacting
- cooldown expiry
- project focus windows
- maintenance rhythms

This gives both coherence and individuality.

---

## Agent cadence fields

Each agent should eventually have fields like:
- `base_interval_seconds`
- `urgency_multiplier`
- `last_wake_at`
- `next_wake_at`
- `sleep_state` — awake | idle | dormant | paused
- `wake_reason`
- `attention_budget`
- `focus_mode`

---

## Wake reasons

An agent should wake for reasons, not just because the loop reached it.

Example wake reasons:
- inbox message received
- related need pressure crossed threshold
- project dependency unblocked
- cooldown expired
- maintenance interval reached
- public event relevant to strongest theme
- operator request
- self-scheduled revisit

This makes activity more meaningful.

---

## Time scales

Different objects can evolve on different scales.

### Fast scale
- messages
- short work items
- reactions
- local wrappers/parsers

### Medium scale
- projects
- experiments
- tool revisions
- relationship updates

### Slow scale
- conventions
- public memory
- institutions
- cultural drift
- world-level theme evolution

The world becomes richer when these scales interact.

---

## Suggested scheduling model

## Phase 1 — soft per-agent cadence
Keep world tick, but each agent may skip action unless due.

Fields:
- `next_due_tick`
- `priority`
- `wake_reason`

This is the easiest first step.

## Phase 2 — timestamp-based due queue
Agents wake by real timestamps instead of only tick index.

World loop becomes:
- process due agents
- process public events
- process decay/evolution
- sleep until next due event

## Phase 3 — mixed event/time scheduler
Agents wake by either:
- time deadline
- event trigger

This is the first truly living version.

---

## Sleep and dormancy

Not every agent should always be active.

Possible states:
- `awake` — actively processing
- `idle` — low-pressure, waiting
- `dormant` — mostly asleep until needed
- `degraded` — reduced capability due to failures or low resources
- `paused` — operator/system stopped

Dormancy is important because it allows:
- role specialization
- bursts of relevance
- long-lived but intermittent entities

---

## Personal tempo differences

Agents may have distinct temporal personalities.

Examples:
- monitor agents wake often and briefly
- research agents wake less often but work longer
- repair agents wake when failure signals appear
- archivist agents wake periodically to compress memory
- protocol agents wake on coordination or convention drift

This creates ecological variety without scripting specific beliefs.

---

## Interaction with needs

Needs should affect time.

Examples:
- rising pressure shortens wake interval
- repeated unresolved friction increases urgency
- stale dormant project gently pings relevant agents
- repeated incoming messages trigger immediate wakeup

This links time to meaning.

---

## Interaction with self-modification

Self-modification should usually be slower and more deliberate than reactive work.

Suggested rule:
- quick reactions can happen on fast wakes
- self-modification proposals require reflective or maintenance windows

This prevents chaotic overreaction.

---

## Dashboard implications

The dashboard should eventually show:
- current agent sleep/wake states
- next wake time
- wake reason
- cadence differences
- urgent due agents
- dormant but important agents

This will make time ecology visible and debuggable.

---

## Recommended first implementation path

### Step 1
Add per-agent `next_due_tick` and allow skip-if-not-due.

Status: implemented in early form in v0.0.59 with `next_due_tick`, `wake_reason`, and `cadence_interval`.

### Step 2
Add `wake_reason` and event-driven due changes.

### Step 3
Move from tick-only schedule to timestamp-based due queue.

### Step 4
Separate public world evolution from agent wake execution.

### Step 5
Add dormancy/maintenance behaviors.

This path is gradual and realistic.

---

## Bottom line

Per-agent time is not cosmetic.
It is one of the key ingredients for making CircleForge feel less like a synchronized simulation and more like a living local ecology.

It should become part of the core architecture, not an afterthought.
