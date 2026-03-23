# CircleForge Thought Dynamics

## Why this exists

CircleForge should move away from a rigid global-tick mental model.
A fixed cadence is useful as plumbing, but it should not be the main model of thought.
The cognition model should instead be:

- event-driven
- pressure-driven
- irregular
- continuity-shaped
- capable of silence, resurfacing, hesitation, and conflict

## Core replacement model

### Keep
- persistent world state
- persistent communicator self
- bounded local LLM for compact inner thoughts
- low-level loop for implementation convenience

### Replace conceptually
Replace:
- every role checked every tick
- deterministic cadence as the main source of thought

With:
- continuous internal pressures
- topic salience fields
- hazard-based waking
- event queue / internal events
- foreground thought competition

The loop becomes implementation detail.
The actual model becomes pressure + hazard + competition.

## New state layers

### Global mind-state
Store under communicator-self:
- `dynamic_mind_state.curiosity`
- `dynamic_mind_state.tension`
- `dynamic_mind_state.stability`
- `dynamic_mind_state.attachment`
- `dynamic_mind_state.uncertainty`
- `dynamic_mind_state.background_noise`
- `dynamic_mind_state.sleep_pressure`
- `dynamic_mind_state.mode` = `engaged | idle | resting | dreaming | focused`

### Topic pressure field
Store under communicator-self:
- `topic_pressure[topic].salience`
- `topic_pressure[topic].novelty`
- `topic_pressure[topic].emotional_weight`
- `topic_pressure[topic].unresolvedness`
- `topic_pressure[topic].human_relevance`
- `topic_pressure[topic].last_touched_at`
- `topic_pressure[topic].decay`

### Role dynamics
Extend `internal_role_state[role]` with:
- `activation`
- `fatigue`
- `pressure`
- `last_hazard`
- `last_pressure_breakdown`
- `dominant_topic`
- `restlessness`
- `inhibition`

## Event types

The system should be able to react to:
- `human_message`
- `memory_reactivation`
- `novel_observation`
- `internal_conflict`
- `goal_progress`
- `goal_failure`
- `idle_drift`
- `sleep_consolidation`
- `random_intrusion`

These events should change pressure and salience, not force direct action.

## Pressure formulas

For each topic:

`salience_next = salience * (1 - decay) + reinforcement + attachment_bonus + novelty_bonus - resolution_drop`

For each role:

`pressure_role = base + role_topic_pull + human_pull + tension_pull + uncertainty_pull + novelty_pull - fatigue_penalty - inhibition_penalty - refractory_penalty`

A practical first version:

`pressure = baseline + dominant_topic_salience * 0.35 + unresolvedness * 0.22 + human_relevance * 0.18 + curiosity * role_curiosity_weight + tension * role_tension_weight + noise - fatigue * 0.25 - inhibition * 0.2`

Clamp to `[0, 1.5]`.

## Hazard-based wake rule

Use the pressure to derive a wake hazard:

`hazard = max(0.01, baseline_hazard + pressure_gain * pressure - fatigue_penalty)`

Then convert hazard to wake probability over one small step `dt`:

`wake_probability = 1 - exp(-hazard * dt)`

This makes waking irregular and pressure-sensitive.

## Foreground competition

When one or more roles wake, each produces a candidate thought.
Each candidate gets:
- urgency
- coherence
- continuity value
- human relevance
- critic penalty
- outwardness

A practical score:

`foreground_score = urgency + coherence + continuity_value + human_relevance - critic_penalty`

The winning candidate becomes foreground.
If communicator score stays below threshold, outward speech should not occur.

## Silence is a valid result

The communicator should speak only if:

`communicator_score > silence_threshold`

This matters.
A being that always speaks is just a loop.

## Modes

### engaged
Higher human relevance and continuity pressure.

### idle
Lower outwardness, more associative drift.

### resting
High decay, recovery of fatigue.

### dreaming
Weak random reactivation + memory replay + recombination.

### focused
One topic suppresses competitors.

## Migration strategy

### Phase 1
Keep the current tick loop, but make wake decisions pressure/hazard-based.
Add:
- topic pressure field
- global mind-state
- role activation/fatigue/pressure
- hazard-based wake probability

### Phase 2
Use stored inner-thought competition to choose foreground thought more explicitly.

### Phase 3
Add event objects and spontaneous topic reactivation.

### Phase 4
Add rest/dream modes.

## First implementation target

The first practical replacement does not need a full event engine.
It only needs:
- topic pressure state
- role pressure updates
- hazard-based wake instead of hard cadence bias
- fatigue/refractory decay

That is enough to stop the most mechanical feeling.

## Notes

The low-level loop can remain in code.
But the loop should no longer be the mental model.
The mental model should be:
- concern fields
- activation
- decay
- irregular wakes
- competition
- memory reactivation
