# CONTINUITY_MEMORY_CONSOLIDATION_v1

## Purpose
WESLR needs more than immediate chat carryover and previous_decision deltas. A structured continuity memory layer must retain meaningful patterns over time (habits, preferences, long-running threads) without turning into a visible chatbot transcript. The goal is to improve relevance, stability, and self-assessment while keeping continuity hidden by default.

## Memory Layers
- **Interaction Memory (ephemeral, session-level):** Recent turns/messages; used for immediate coherence. Time horizon: minutes/hours. Store: last few user intents, clarifications. Do not store: sensitive long-term preferences, status deltas, governance signals.
- **Working Continuity Memory (short/medium term):** Active threads and short-lived contexts (ongoing tasks, current session themes). Time horizon: hours/days. Store: active goals, current blockers, short-term plans, recent evidence context. Do not store: raw transcripts beyond necessary context; unrelated personal trivia.
- **Consolidated Continuity Memory (longer-lived, user-scoped):** Promoted, structured facts about the user’s patterns, stable preferences, recurring blockers, important decisions/outcomes, cross-topic relationships. Time horizon: weeks/months. Store: stable preferences (work cadence, communication style), recurring bottlenecks, habits (e.g., workout-lunch timing), long-running unresolved threads, repeated cross-topic links (email ↔ planning). Do not store: fleeting chatter, low-confidence guesses, transient errors.
- **Long-Term Doctrine / System Knowledge:** Global/system-level rules, governance, role/permission contracts, workflow contracts. Time horizon: persistent. Store: policies, contracts, safety/governance, architectural doctrine. Do not store: user-specific data.

## Promotion Rules
Promote from interaction/working to consolidated when:
- A preference is repeated/consistent (e.g., light lunch before workout; prefers afternoon focus block).
- A recurring pattern emerges (repeated bottlenecks, recurring tasks, long-running threads that span days).
- Important decisions/outcomes are reached (approvals/denials, resolved blockers, key choices).
- Cross-topic relationships repeat (planning interacts with email timing; workouts after lunch; coding blocked by missing context).
- Communication preferences become stable (brevity, tone, detail level).

## Non-Promotion / Forgetting Rules
Keep or drop as temporary when:
- One-off trivial chat details with no reuse value.
- Fleeting phrasing or small talk.
- Low-confidence/speculative guesses not yet validated.
- Transient artifacts (temporary URLs, draft snippets) unless promoted as part of an important decision/outcome.

## Partitioning
- Partition all continuity layers by (workspace_id, user_id); allow explicit shared/workspace scope for shared facts; maintain global/system doctrine separately.
- Anti-leakage: never surface or reuse consolidated continuity across users/workspaces unless explicitly shared; logging/telemetry must tag with partition keys.

## Conversation Influence
- Default: continuity stays hidden; subject-following replies leverage relevant consolidated facts subtly (e.g., suggest timing a workout after a light lunch; propose an email slot in the admin block).
- No “since last time” unless explicitly requested (status/recap/debug modes).
- Memory narration only when asked or when necessary for clarity (“You mentioned preferring light lunches before workouts—want to schedule it that way?”).
- Chat mode uses interaction/working memory for immediate coherence; can pull promoted hints from consolidated memory without exposing internal structure.

## Self-Improvement Link
- Consolidated continuity provides structured signals for governed self-assessment: recurring bottlenecks, pattern of low-confidence answers, repeated user preferences not honored.
- Self-improvement proposals can target reducing friction (e.g., better scheduling hints, avoiding repeated context loss), guided by consolidated patterns and governed by existing self-assessment doctrine.

## Status
- Design documented here; no code changes in this doc.
