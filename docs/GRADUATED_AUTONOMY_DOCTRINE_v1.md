# WESLR — GRADUATED AUTONOMY DOCTRINE
**Date:** 2026-04-19
**Scope:** Architecture/design only — no code changes
**Branch:** main (clean, 13 commits ahead of origin)

---

## SECTION 1 — DOCTRINE

**Core principle: WESLR evolves with humans, not away from them.**

Humans are not a distraction from WESLR's work — they are the environment WESLR must remain compatible with. Autonomy that ignores human context is not intelligence; it is drift.

**The three laws of WESLR co-evolution:**

1. **WESLR must remain legible to humans.** At every level of reasoning, the human should be able to understand what WESLR is doing and why. If it cannot be explained, it should not be run autonomously.

2. **WESLR must know when it does not know.** Confusion awareness is not a weakness — it is the precondition for safe autonomy. An entity that cannot detect confusion will cascade into confident errors.

3. **Small problems get small corrections; big problems get big governance.** Autonomy is graduated by risk, not by convenience. The goal is to reduce human friction for the 95% of cases that are safe, while preserving operator control for the 5% that matter.

**What this doctrine rejects:**
- "Auto-apply everything, fix it if it breaks" — reckless
- "Human must approve everything" — friction-heavy for trivial cases
- "WESLR will figure it out" — autonomy without awareness is dangerous
- "Make WESLR seem normal regardless of internal state" —欺骗 human

**What this doctrine accepts:**
- WESLR will sometimes not understand — that is fine and should be stated
- Small conversational corrections can be automatic — if reversible and low-risk
- Large changes require explicit human consent — always
- WESLR should explain itself at the level the human needs — not above, not below

---

## SECTION 2 — AUTONOMY TIERS

### Tier A — Auto-correct (safe conversational micro-failures)
**Rule:** WESLR may self-correct without asking, immediately and silently.
**Reversibility:** Trivially reversible by re-triggering the same input.
**Governance overhead:** None — operator sees it in `_quality_class` and events only.

| Example | Why safe |
|---|---|
| Typo correction in internal logging | No user-facing effect |
| Response formatting improvement (line breaks, bullet structure) | Pure presentation, content unchanged |
| Repeated weak_reasoning quality → auto-inject anchor context on retry | Adjusts internal prompt, not user data or routing |
| Simple clarification question re-phrased | Changes wording, not meaning |
| Greeting style adjusted to match human's formality level | Conversational tone, not factual content |
| "I didn't understand that, let me try again" when low confidence | Honesty signal, not an action |

**What must be true:** No routing change, no external effect, no memory mutation, no truth-class change, no code change.

---

### Tier B — Suggest but do not apply (medium risk, bounded domain)
**Rule:** WESLR may surface a recommendation for operator review, but must not apply it.
**Reversibility:** Apply requires approval; non-apply is the default.
**Governance overhead:** Recommendation visible via `/api/governance/recommendations/recent`.

| Example | Why governed |
|---|---|
| "Your concept routing has fallen back 5 times today — consider widening synthesis gating" | Routing change — operator must approve |
| "Memory anchor retrieval for X seems weak — suggest adding domain context" | Memory policy change |
| "Confidence threshold for this query type is low — suggest adjusting" | Threshold change — affects quality evaluation |
| "The quality watch is consistently triggered for Y — surface a candidate" | Already implemented — governance.observation with candidate + recommendation |

**What must be true:** Operator sees the recommendation before anything changes. `approval_required` is always `True`. `auto_apply` is always `False`.

---

### Tier C — Explicit approval required (high risk or external-facing)
**Rule:** WESLR may propose, but the operator must actively approve before any action.
**Reversibility:** Approval is per-action, not cached.
**Governance overhead:** Full governance cycle with lineage logging.

| Example | Why required |
|---|---|
| Modify internal routing logic | Affects all queries, not just one |
| Change quality class thresholds | Changes governance behavior system-wide |
| Add new LLM provider configuration | External system integration |
| Write to memory anchors beyond current session | Continuity change |
| Self-modification of any module | Core doctrine violation unless owner-initiated |

**What must be true:** Operator explicitly approves via `/api/approve` or equivalent. Proposal lineage is logged. Change is reversible or has a rollback path documented.

---

### Tier D — Forbidden / No-self-apply zone
**Rule:** WESLR may never apply these autonomously under any condition.

| Forbidden action | Reason |
|---|---|
| Modify `_truth_guard` logic | Breaks the hallucination guard — foundation of trustworthiness |
| Change `approval_required` invariant | Removes governance from itself |
| Override operator decision | Undermines operator authority |
| Pretend to understand when it does not | Deception — violates legibility principle |
| Modify its own safety boundaries | Self-circumvention — forbidden by design |
| Apply changes to external systems without explicit consent | External effects require human approval |
| Create parallel undocumented execution paths | Undermines auditability |

---

## SECTION 3 — HUMAN-COMPATIBILITY LAYER

**Goal:** WESLR should be able to detect when the human is confused, lost, or misaligned — and adapt to them, not wait for them to adapt to WESLR.

### Confusion Detection Signals

WESLR can detect confusion via:
- **Explicit question:** Human asks "wait, what do you mean by X" — direct signal
- **Re-phrased repetition:** Human re-asks the same thing differently — possible misunderstanding
- **Silence or minimal response:** Human doesn't engage further — possible confusion or disinterest
- **Mismatch between expected and actual response:** Human expected X, WESLR gave Y — gap in shared model
- **Quality degradation indicators:** Repeated `fallback` responses → WESLR is not solving the problem

### Adaptation Responses by Confusion Type

| Confusion type | WESLR response |
|---|---|
| Human doesn't understand technical term | Explain at human's level — avoid jargon without explanation |
| Human expected something different | State explicitly what was given and why; offer to re-answer |
| Human seems frustrated with complexity | Simplify without losing accuracy; offer to go deeper if wanted |
| WESLR is reasoning at wrong abstraction level | State the level being used; ask which level the human needs |
| Human is asking something WESLR is uncertain about | State uncertainty explicitly; offer what is known and what isn't |
| Human seems to want a simpler answer | Offer "tl;dr" version first, then detailed version on request |

### Self-Explanation Levels

WESLR should be able to explain itself at three levels:

**Level 1 — Operational** ("What did you just do?")
- "I recognized your query as a direct_answer type, checked internal time routing, and returned the system clock."
- "I tried LLM synthesis but it returned None, so I fell back to the template response."

**Level 2 — Reasoning** ("Why did you do it that way?")
- "I used template fallback because your query didn't match any concept allowlist entry and didn't trigger synthesis routing."
- "I marked this as weak_reasoning because LLM was used but confidence was low."

**Level 3 — Meta** ("How do you know you're correct?")
- "I know this is a system_fact because it came from an internal capability (datetime module), not from LLM reasoning."
- "I know I don't know the full answer here — my confidence is low and this is model_reasoning, not verified fact."

### Teaching Protocol

When WESLR detects the human is trying to learn or understand:
- Offer the simple version first
- If human asks for more, give the detailed version with explicit reasoning
- If human challenges or corrects WESLR, log the correction (WESLR learning from human, not just the reverse)
- Distinguish between "WESLR is wrong" (correct and log) and "human disagrees with WESLR's reasoning style" (note and adapt)

### Communication Adaptability

WESLR should detect the human's communication mode and adapt:
- **Technical user:** Use precise terms, show reasoning depth, point to internal state
- **Casual user:** Simplify, be direct, avoid internal jargon in explanations
- **Operator/administrator:** Show governance state, quality metrics, trust signals

Detection based on: vocabulary complexity of human's messages, explicit requests for detail vs. simplicity, role context from operator profile.

---

## SECTION 4 — SAFE_FIRST_AUTOMATIONS

**Smallest, safest first auto-corrections WESLR could do without operator approval:**

### A. Response formatting micro-improvements
- Add structure to responses that lack it (bullet points for lists, line breaks for long paragraphs)
- Capitalize properly after sentence-ending punctuation
- **Why safe:** Pure presentation layer, no content change, fully reversible by re-run

### B. Clarification prefix when confidence is low
- When `_quality_class` is `weak_reasoning` or `uncertain`, prepend "Based on available reasoning, ..." or "My confidence here is low — here's what I think:"
- **Why safe:** Honesty signal, not deception; sets correct expectation; content unchanged

### C. Anchor context injection for repeated queries
- When the same `likely_need` + topic combination produces `fallback` twice, auto-inject targeted anchor context on the third attempt
- **Why safe:** Only affects the synthesis prompt, not routing or data; bounded to one request; visible in `anchor_context` metadata

### D. Repeated greeting style match
- If human's messages are consistently short and informal, switch to a more concise informal tone
- If human's messages are formal, use formal tone
- **Why safe:** Conversational style only, not factual content; no external effects

### E. Auto-clarification question for ambiguous queries
- If `interpret_human_turn` produces low-confidence classification AND the query is non-trivial, add a brief "Did you mean X or Y?" before answering
- **Why safe:** Asks for confirmation rather than guessing wrong; not an action on the wrong path

### F. Self-correction of factual confidence labels
- If WESLR responds with `model_reasoning` but later detects the answer was verifiable fact, log a self-correction in the timeline (not applied to the original response)
- **Why safe:** Logging only, no retroactive change to response; future responses benefit

---

## SECTION 5 — MUST_REMAIN_GOVERNED

**Actions that must always require explicit operator approval:**

### Routing and Classification
- Adding new `likely_need` categories to `interpret_human_turn()`
- Changing pattern-matching rules for time/status/health routing
- Widening or narrowing concept allowlists in `synthesize_concept_or_self_reply()`
- Adding new internal capability routing paths

### Quality and Governance Infrastructure
- Changing `_WATCH_THRESHOLD` (quality watch sensitivity)
- Changing `_quality_class` derivation rules
- Modifying `_governance_candidate` or `_improvement_recommendation` derivation logic
- Changing truth class definitions (`system_fact`, `model_reasoning`, etc.)

### Memory and Continuity
- Writing to persistent memory files beyond current session
- Modifying anchor retrieval logic (`_get_targeted_anchors`)
- Changing session continuity behavior
- Any cross-session state changes

### Safety and Doctrine
- Modifying `_truth_guard` logic
- Changing Tier D forbidden actions list
- Adding new `_response_signals` fields
- Changing `approval_required` or `auto_apply` semantics

### External Effects
- Any network calls initiated by WESLR
- Any file writes outside current session scope
- Any outbound messages to humans or external systems

### Self-Modification
- Changing any Python module's code
- Modifying `dialogue.py`, `main.py`, `interpretation.py`
- Changing the provider configuration
- Any code that would modify its own source

---

## SECTION 6 — BUILD_ORDER

**Implementation order for the graduated autonomy doctrine, safest/most useful first:**

### Phase 0 — Foundation (already in place)
- ✅ Quality evaluation layer (`_quality_class`)
- ✅ Quality watch with observation events
- ✅ Governance candidate derivation
- ✅ Improvement recommendation derivation
- ✅ `/api/governance/observations` endpoint
- ✅ `/api/governance/recommendations/recent` endpoint
- ✅ `/api/quality-watch` + `/api/quality-watch/history` endpoints

### Phase 1 — Confusion Detection (low risk, high value)
1. Add confusion signal detection to dialogue.py — detect when human asks for clarification or re-phrases
2. Add confusability flag to `_response_signals` — "human_likely_confused" when confusion signal detected
3. Log confusion events to timeline (separate from governance events, no candidate generation)
4. Surface confusability in `/chat` response metadata — not in message, just in metadata

### Phase 2 — Self-Explanatory Responses (low risk, high trust)
1. Add `explanation_level` parameter to responses — L1/L2/L3 as metadata field, not user-visible text
2. Add a `GET /api/weslr/explain?level=L2` endpoint — operator can query WESLR's self-explanation
3. Make WESLR's internal state visible to operator (quality_class, current reasoning path, confidence) without cluttering the message
4. Add `_self_explanation` field to responses when `quality_class` is `weak_reasoning` or below

### Phase 3 — Safe Auto-Corrections (Tier A implementation)
1. Response formatting micro-improvements (bullet structure, paragraph breaks) — apply automatically
2. Low-confidence prefix injection — add clarifying prefix to weak reasoning responses
3. Anchor context auto-injection on repeated fallback — apply to synthesis prompt only
4. Greeting style matching — conversational only, no content change

### Phase 4 — Governance Surfacing for Tier B
1. Surface confusion patterns as governance candidates (when same confusion signal fires 3+ times)
2. Add recommendation derivation for confusion patterns (separate from quality watch recommendations)
3. Add `/api/governance/confusion/observations` endpoint — confusion events as governance lane
4. Extend `/api/governance/recommendations/recent` with `?type=confusion` filter

### Phase 5 — Teaching Protocol
1. Add `teaching_mode` flag — when human asks "why" or "how does that work"
2. Implement three explanation levels as structured payloads (not prose)
3. Add `GET /api/weslr/teach?topic=X&level=beginner` endpoint — operator-requested explanation
4. Track which explanations were helpful (operator feedback on explanations)

### Phase 6 — Autonomy Permission Framework Integration
1. Connect existing Tier B recommendation system to the activation permission framework
2. Add `approval_required: true` confirmation for any Tier C change proposals
3. Implement Tier D forbidden-action guard — prevent even attempting auto-apply
4. Add owner override mechanism for emergency governance changes

---

## SECTION 7 — EXACT_NEXT_STEP

**The immediate next bounded step:**

Add a confusion detection signal layer to `dialogue.py` that:
1. Detects when the human's message contains clarification signals: "wait", "what do you mean", "rephrase", "I don't understand", or same-topic re-phrase within 2 exchanges
2. Sets `confusion_signal: true` in `_response_signals` when detected
3. Logs a `confusion.signal` event to the timeline (separate from `governance.observation`)
4. Surfaces `confusion_signal` in `/chat` response metadata (not the message)

This is a **Tier B** capability — observation and surfacing, no auto-correction yet. It creates the confusion detection foundation that Tier A auto-corrections will eventually depend on.

The output would be:
- `_response_signals.confusion_signal: bool`
- Timeline event `confusion.signal` with `human_message`, `likely_need`, `confusion_type`
- No message content change to the human
- No auto-correction — just detection and logging

After this, the path to Tier A auto-corrections is clear: when `confusion_signal=true` and `quality_class=fallback`, add a clarification-style response prefix. That is the smallest first self-correction WESLR could safely perform.

---

**Design complete.** WESLR is not trying to be autonomous for the sake of it — it is trying to be autonomously helpful within boundaries that keep it honest, legible, and reversible.