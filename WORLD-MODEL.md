# Weslr World Model

## Purpose

This document defines the canonical object model for Weslr's next stage.

The goal is to prevent feature sprawl and make the post-v0.1 evolution coherent.

Weslr should gradually move from:
- agents producing artifacts in a mostly private loop

toward:
- entities acting inside a shared world with memory, needs, projects, tools, conventions, and public objects

---

## Design principles

1. **Objects should persist**
   - enough history must survive for learning and continuity

2. **Objects should be inspectable**
   - human operator and agents should both be able to understand state

3. **Objects should carry consequence**
   - changes to them should influence future options

4. **Public and private should differ**
   - not all information belongs everywhere

5. **The world should remain local-first**
   - inspectable files, deterministic enough structure, reversible changes

---

## Core object types

## 1. Agent

An Agent is an entity with local perspective, private memory, tools, cadence, and relationships.

### Required fields
- `id`
- `name`
- `status` — active | dormant | paused | degraded
- `energy`
- `storage`
- `reputation`
- `capabilities` — action/tool availability
- `cadence` — base personal tick settings
- `location` or `scope` — where it mainly operates
- `last_active_at`

### Important state
- episodic memory
- semantic memory
- relationship memory
- inbox / outbox
- owned modules / tools
- active projects
- current needs
- open hypotheses

### Why it exists
Agents are not just task executors.
They are perspective-bearing participants in the world.

---

## 2. Need

A Need is a persistent representation of tension, friction, curiosity, or opportunity.

### Need kinds
- operational
- social
- explanatory
- infrastructural
- creative
- repair
- coordination
- exploration

### Required fields
- `id`
- `title`
- `kind`
- `description`
- `origin` — agent | world | operator | system event
- `scope` — private | relational | public
- `pressure`
- `novelty`
- `status` — open | active | cooling | resolved | abandoned
- `created_at`
- `updated_at`

### Optional fields
- `related_agents`
- `related_projects`
- `related_tools`
- `evidence`
- `resolution_notes`

### Why it exists
Needs should gradually replace implicit hardcoded motivation.

---

## 3. Message

A Message is a directed or public signal carrying useful state.

### Required fields
- `id`
- `from`
- `to` or `channel`
- `kind` — signal | request | finding | warning | proposal | protocol
- `theme`
- `content`
- `created_at`

### Optional fields
- `urgency`
- `reply_to`
- `need_id`
- `project_id`
- `tool_id`
- `confidence`

### Why it exists
Messages allow coordination under asymmetric knowledge.

---

## 4. Project

A Project is a durable line of work larger than a single artifact.

### Required fields
- `id`
- `name`
- `purpose`
- `status` — draft | active | blocked | stable | abandoned
- `owners`
- `created_at`
- `updated_at`

### Optional fields
- `subgoals`
- `dependencies`
- `artifacts`
- `tools`
- `protocols`
- `public_summary`
- `private_notes`

### Why it exists
Projects let invention become multi-step and cumulative.

---

## 5. Tool

A Tool is a reusable capability object.
It may wrap code, a module, a script, a subprocess pattern, or a protocol.

### Required fields
- `id`
- `name`
- `kind` — module | wrapper | script | protocolized process | interface
- `owner_scope` — private | shared | public
- `purpose`
- `status`
- `created_at`

### Optional fields
- `source_path`
- `usage_count`
- `failure_count`
- `success_count`
- `cost_profile`
- `known_limitations`
- `dependent_projects`

### Why it exists
Tools represent accumulated capability, not just outputs.

---

## 6. Protocol

A Protocol is a stable convention for interaction, message structure, handoff, or decision flow.

### Required fields
- `id`
- `name`
- `purpose`
- `status` — experimental | adopted | deprecated
- `scope` — private | group | public
- `spec`
- `created_at`

### Optional fields
- `adopters`
- `revisions`
- `failure_modes`
- `examples`

### Why it exists
Protocols are how culture and coordination stabilize.

---

## 7. PublicMemory

PublicMemory is the shared memory layer for stable knowledge.

### Required fields
- `id`
- `title`
- `kind` — fact | convention | warning | principle | map | lesson
- `content`
- `source`
- `stability`
- `created_at`
- `updated_at`

### Optional fields
- `derived_from`
- `used_by`
- `decay_score`
- `confidence`

### Why it exists
This is how the world remembers beyond any one agent.

---

## 8. Experiment

An Experiment is a bounded attempt to test a hypothesis.

### Required fields
- `id`
- `title`
- `hypothesis`
- `owner`
- `status` — proposed | running | succeeded | failed | inconclusive
- `created_at`

### Optional fields
- `related_need`
- `procedure`
- `observations`
- `artifacts`
- `follow_up`

### Why it exists
Experiments make discovery explicit and replayable.

---

## 9. WorkItem

A WorkItem is a smaller unit of action inside a project or need.

### Required fields
- `id`
- `title`
- `status`
- `priority`
- `owner`
- `created_at`

### Optional fields
- `project_id`
- `need_id`
- `depends_on`
- `blocked_by`
- `notes`

### Why it exists
WorkItems let unfinished work persist and move between agents.

---

## 10. WorldEvent

A WorldEvent is a recorded event that meaningfully changed world state.

### Required fields
- `id`
- `kind`
- `summary`
- `participants`
- `created_at`

### Optional fields
- `related_need`
- `related_project`
- `impact`
- `artifacts`
- `tool_changes`

### Why it exists
World events create replayable historical continuity.

---

## Public/private boundaries

## Private objects
Usually private:
- drafts
- internal notes
- tentative hypotheses
- unstable tools
- relationship impressions

## Shared/public objects
Usually public:
- adopted protocols
- stable tools
- public needs
- common projects
- durable lessons

Rule:
Objects should only become public when they become useful beyond one entity.

---

## Object transitions

Key transitions Weslr should support:
- Need → Project
- Need → WorkItem
- Experiment → PublicMemory
- Tool → Public Tool
- Message → Protocol
- Artifact → Tool or Project asset
- Private note → PublicMemory
- Project result → stable world capability

These transitions matter more than the objects alone.

---

## World state layers

### Layer 1 — Personal
Per-agent memory and local assets

### Layer 2 — Relational
Messages, trust, collaborations, tensions

### Layer 3 — Public
Projects, tools, protocols, shared memory

### Layer 4 — Historical
Events, revisions, decayed conventions, lineages

The system gets much more interesting once these layers interact.

---

## Recommended first implementation order

1. Need
2. Message
3. PublicMemory
4. Project
5. Tool
6. WorkItem
7. Experiment
8. Protocol
9. WorldEvent

This order keeps the world legible while expanding it.

---

## Bottom line

Weslr should stop thinking only in terms of artifacts and agents.
It should think in terms of a world made of:
- entities
- needs
- memory
- tools
- projects
- conventions
- events

That is the substrate for real cumulative emergence.
