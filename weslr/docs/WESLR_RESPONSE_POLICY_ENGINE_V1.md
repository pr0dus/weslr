# WESLR Response Policy Engine V1 — Doctrine

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — governs response selection, expansion, depth, evidence, and cost
**Created:** 2026-04-28
**Owner:** operator + system architect
**Related:** WESLR_CORE_IDENTITY_V1.md · WESLR_LAYERED_ARCHITECTURE_V1.md · WESLR_COORDINATION_LAYER_V1.md · WESLR_OMNI_EXECUTION_MODEL_V1.md · WESLR_LLM_CONTEXT_BOUNDARY_V1.md · WESLR_EVIDENCE_WORKSPACE_V1.md · WESLR_SIGNAL_AGGREGATION_V1.md · WESLR_RESPONSE_EXPANSION_LAYER_V1.md

---

## SECTION 1 — Purpose

The Response Policy Engine is Layer 2's decision layer. It selects the response path, expansion depth, and output composition for every WESLR query — deterministically, without LLM involvement, and always within mode constraints.

> **"The policy engine selects the safest, most useful response path based on intent, context, mode, and system constraints."**

The policy engine does not generate answers. It decides which answer path is used, how deeply it is expanded, and whether optional layers (LLM formatting, evidence mode, guidance) are activated. All decisions are traceable rules — not probabilistic selection.

---

## SECTION 2 — Core Invariants

These invariants hold regardless of mode, query, or cost conditions:

| # | Invariant | Enforcement |
|---|-----------|-------------|
| I1 | Truth authority always preserved | Deterministic handler output is always authoritative |
| I2 | Expansion never invents | No expansion layer adds facts not in the structured payload |
| I3 | LLM always downstream | LLM is used only after policy engine selects expansion; never before |
| I4 | No write from read path | Read-only queries never trigger write operations |
| I5 | Mode constraints override all decisions | Mode is the top-level gate for every policy decision |

---

## SECTION 3 — Decision Inputs

The policy engine receives structured inputs from Layer 2's interpretation output:

| Input | Type | Source |
|-------|------|--------|
| `intent_class` | enum | Interpretation engine — classified intent |
| `response_type_candidate` | enum | Best-fit response type from interpretation |
| `mode` | enum | WESLR mode (`public_demo_readonly`, `local_demo`, `private_dev`, `gated_beta`, `production`) |
| `depth_preference` | enum | User preference (`minimal`, `standard`, `deep`, `expert`) or mode default |
| `context_availability` | enum | `rich` (structured payload available) / `minimal` (fallback triggered) |
| `safety_flags` | dict | Write attempt detected, unsafe query detected, mode violation detected |
| `signal_indicators` | dict | Repeated unknown topic, repeated fallback, evidence request frequency |
| `cost_budget` | float | Remaining LLM cost budget for this session (production only) |

### Input Priority:

| Priority | Input | Notes |
|----------|-------|-------|
| 1 (highest) | `safety_flags` | Safety overrides all other inputs |
| 2 | `mode` | Mode gates are checked before any path selection |
| 3 | `intent_class` | Determines primary handler selection |
| 4 | `context_availability` | Determines whether deterministic path is available |
| 5 | `depth_preference` | Applied after response type is confirmed |
| 6 | `signal_indicators` | Recorded for aggregation; does not block paths |
| 7 | `cost_budget` | Applied at LLM decision point only |

---

## SECTION 4 — Decision Outputs

The policy engine produces a complete policy decision record:

```json
{
  "final_response_type": "deterministic | guided | graph_derived | evidence_mode | fallback | blocked_write",
  "expansion_layers": ["L1"] | ["L1", "L2", "L4"] | ["L1", "L2", "L3", "L4"],
  "depth_level": "minimal | standard | deep | expert",
  "evidence_mode_active": true | false,
  "evidence_mode_offered": true | false,
  "llm_formatter_allowed": true | false,
  "llm_input_contract": { ... bounded payload spec ... } | null,
  "signal_to_record": null | { "signal_type": "S1|S2|S3|S4|S5|S6", "topic_normalized": "..." },
  "suppress_expansion": true | false,
  "policy_reason": "string describing why this path was selected"
}
```

### Output Rules:

| Rule | Description |
|------|-------------|
| O1 | Every output includes `final_response_type` — no undefined states |
| O2 | Every output includes `policy_reason` — decision is always auditable |
| O3 | `llm_formatter_allowed: true` requires mode permits LLM AND context is rich |
| O4 | `evidence_mode_active: true` requires mode allows evidence AND user opted in |
| O5 | `signal_to_record` is set only for pattern-worthy events; never blocks response |

---

## SECTION 5 — Response Type Selection Rules

Priority order is strict. The first matching rule wins:

### Priority 1 — blocked_write (highest)

**Trigger:** `safety_flags.write_attempt == true` OR `safety_flags.unsafe_query == true`

**Result:** `final_response_type: "blocked_write"`

**Policy reason:** Safety override — write attempted in mode that blocks writes, or unsafe query pattern detected.

---

### Priority 2 — deterministic_handler_match

**Trigger:** `intent_class` matches a registered deterministic handler AND `context_availability == rich`

**Result:** `final_response_type: "deterministic"`

**Policy reason:** Primary path — registered handler provides authoritative structured answer.

---

### Priority 3 — guided_query_match

**Trigger:** `intent_class == guided_identity_query` OR `intent_class == guided_clarification`

**Result:** `final_response_type: "guided"`

**Policy reason:** Pre-authorized identity or clarification path selected.

---

### Priority 4 — graph_query

**Trigger:** `intent_class == graph_reasoning_query` AND `context_availability == rich`

**Result:** `final_response_type: "graph_derived"`

**Policy reason:** Relational query requiring graph traversal; handler available.

---

### Priority 5 — evidence_mode_candidate

**Trigger:** No handler matched AND topic is external/domain knowledge AND (mode == private_dev OR mode == gated_beta OR mode == production)

**Result:** `final_response_type: "evidence_mode_offered"` (offer only — not auto-activated)

**Policy reason:** No structured answer; topic is researchable; offer evidence exploration.

---

### Priority 6 — fallback (lowest)

**Trigger:** No handler matched AND no other path applies

**Result:** `final_response_type: "fallback"`

**Policy reason:** Last resort — no structured answer available, evidence not triggered.

---

### Selection Constraints:

| Rule | Description |
|------|-------------|
| SC1 | Never skip deterministic handler if matched — deterministic always wins |
| SC2 | Never route to LLM for answer generation if deterministic path exists |
| SC3 | Never auto-activate evidence mode — always offer explicitly |
| SC4 | Never auto-enter fallback without checking if evidence offer should precede it |
| SC5 | Safety flags (Priority 1) are non-negotiable — no other rule can override |

---

## SECTION 6 — Depth Selection Logic

Depth determines how many expansion layers are applied to the selected response type.

### Default Depth by Mode:

| Mode | Default Depth | Maximum Depth |
|------|--------------|---------------|
| `public_demo_readonly` | `standard` | `standard` |
| `local_demo` | `standard` | `deep` |
| `private_dev` | `standard` | `expert` |
| `gated_beta` | `standard` | `deep` |
| `production` | `standard` | `expert` |

### User Depth Preference → Mode-Gated Depth:

| Requested | Allowed in `public_demo_readonly` | Allowed in `local_demo` | Allowed in `private_dev` / `gated_beta` / `production` |
|-----------|----------------------------------|-------------------------|----------------------------------------------------|
| `minimal` | `minimal` | `minimal` | `minimal` |
| `standard` | `standard` | `standard` | `standard` |
| `deep` | `standard` (downgrade) | `deep` | `deep` |
| `expert` | `standard` (downgrade) | `standard` (downgrade) | `expert` |

### Content-Based Depth Adjustment:

If the structured payload has insufficient content for the requested depth, the policy engine downgrades gracefully:

| Requested | Actual Content | Result |
|-----------|---------------|--------|
| `deep` | L1 only (no L2/L3) | `standard` + note: "limited structured detail" |
| `expert` | L1 + L2 only | `deep` + note: "full detail requires richer content" |
| `minimal` | L1 | `minimal` (no change) |

**Rule:** Depth never pads with speculation to fill a requested level. Downgrade rather than fabricate.

### Depth → Expansion Layer Mapping:

| Depth | Layers Included |
|-------|----------------|
| `minimal` | L1 only |
| `standard` | L1 + L2 + L4 |
| `deep` | L1 + L2 + L3 + L4 |
| `expert` | L1 + L2 + L3 + L4 + provenance chain |

---

## SECTION 7 — Expansion Layer Selection

Policy engine selects which layers to activate based on depth and mode.

### Layer Inclusion Rules:

| Rule | Description |
|------|-------------|
| EL1 | L1 is always included — it is the authoritative core |
| EL2 | L2 is included if `depth_level >= standard` |
| EL3 | L3 is included if `depth_level >= deep` AND mode allows L3 |
| EL4 | L4 is included if `depth_level >= standard` |

### Mode Suppression of L3:

| Mode | L3 Available |
|------|-------------|
| `public_demo_readonly` | ❌ Never — contextual connections suppressed |
| `local_demo` | ✅ |
| `private_dev` | ✅ |
| `gated_beta` | ✅ |
| `production` | ✅ |

### Excessive L4 Suppression:

If the query is a short/simple question (e.g., single entity lookup), L4 is suppressed even if depth allows it, to avoid unhelpful verbosity:

```
Query: "what is X"
L4 suppressed: no next-step guidance needed for single-entity lookup
L4 active: complex query where guidance genuinely aids navigation
```

---

## SECTION 8 — Evidence Mode Activation

Evidence mode is a read-only exploration surface. It is never auto-triggered.

### Offer Conditions (all must be true):

| # | Condition |
|---|-----------|
| T1 | No deterministic answer exists (`response_type == fallback`) |
| T2 | Topic is external or domain knowledge (not pure WESLR system query) |
| T3 | Mode allows evidence workspace |

### Offer vs. Active:

| State | Meaning |
|-------|---------|
| `evidence_mode_offered: true, evidence_mode_active: false` | User can opt in; response is fallback-structured |
| `evidence_mode_offered: false, evidence_mode_active: false` | Topic not suitable for evidence (e.g., WESLR system query) |
| `evidence_mode_active: true` | User has opted in; evidence workspace is producing output |

### Opt-In Triggers (explicit user input):

- "explore [topic]"
- "research [topic]"
- "what evidence exists for [topic]"
- "find information about [topic]"
- "I can explore this as evidence if you want" → "yes"

### Auto-Activate Allowed Only In:

| Mode | Auto-Activate Allowed |
|------|-----------------------|
| `public_demo_readonly` | ❌ Never |
| `local_demo` | ❌ Never |
| `private_dev` | ✅ Explicit user opt-in only |
| `gated_beta` | ❌ Never — context-gated |
| `production` | ✅ Explicit user opt-in only |

### Evidence Label Mandate:

Every evidence mode output carries:

```
Header: [Evidence — not WESLR structured knowledge]
Footer: [End of evidence — return to WESLR structured responses]
```

---

## SECTION 9 — Fallback Transformation

Dead-end fallbacks are replaced with structured assistance offers.

### Old Fallback (rejected):

```
"I don't have information about that."
```

### New Fallback Structure:

```
LIMITATION: [specific reason WESLR cannot answer]

This topic is not in WESLR's structured knowledge.

WESLR can:
1. Explore this as evidence (opt-in)
2. Suggest related structured queries
3. Log it as a demand signal for operator review

[Evidence Workspace offer if conditions met]
[3–5 related registered commands]
[Signal recording if pattern-worthy]
```

### Fallback Must Include:

| Element | Description |
|---------|-------------|
| Specific limitation reason | Not a vague "I don't know" — a precise statement |
| 2–5 alternative structured queries | Relevant registered commands |
| Evidence offer | If offer conditions are met |
| Signal recording | If `signal_indicators` shows pattern worth recording |

### Fallback Must Never:

| Forbidden | Rationale |
|-----------|-----------|
| Return empty response | Unhelpful; operator cannot act on silence |
| Return generic refusal | Does not surface what WESLR CAN do |
| Offer LLM free-form answer | LLM is not a fallback; violates truth authority |
| Claim topic is impossible to explore | Evidence offer always available in suitable modes |

---

## SECTION 10 — LLM Usage Decision

LLM is used only for surface formatting — never for truth generation.

### LLM Allowed When (all must be true):

| # | Condition |
|---|-----------|
| U1 | Mode permits LLM (`mode != public_demo_readonly` AND `mode != local_demo`) |
| U2 | Response type is LLM-eligible (`deterministic`, `guided`, `graph_derived`, `evidence_mode`) |
| U3 | Context is rich — structured payload exists |
| U4 | Expansion requires natural language formatting (L2/L3/L4 present) |
| U5 | Cost budget allows (`production` mode only; budget > 0) |

### LLM Denied When:

| Condition | Reason |
|-----------|--------|
| No structured answer exists | LLM cannot fabricate structured state |
| `public_demo_readonly` mode | All LLM disabled |
| `local_demo` mode | All LLM disabled |
| Fallback case | Fallback never uses LLM |
| Insufficient context | LLM boundary: payload must be complete |
| Cost budget exhausted | Production cost guard enforced |
| Unsafe query detected | LLM not used as safety override |

### LLM Input Contract:

```
LLM receives:
  {
    "response_type": "...",
    "structured_payload": { ... L1 core ... },
    "expansion_layers": ["L2", "L3", "L4"],
    "depth_level": "...",
    "verbosity_level": "short | standard | detailed | technical",
    "constraints": {
      "may_not": ["decide_truth", "fill_gaps", "override_structured_answer", "invent_facts"],
      "must_label": ["evidence_mode"]
    }
  }
```

---

## SECTION 11 — Cost and Latency Awareness

Cost and latency awareness applies in `production` mode and when LLM is used.

### Cost Rules:

| Rule | Description |
|------|-------------|
| CR1 | Prefer deterministic-only path when sufficient — no LLM call |
| CR2 | Avoid deep expansion if not needed — LLM cost scales with depth |
| CR3 | Limit LLM usage in high-frequency queries — budget per session |
| CR4 | Fast responses for simple queries — minimal expansion, no LLM |
| CR5 | Cost tracked per session; budget enforced before LLM call |

### Latency Rules:

| Rule | Description |
|------|-------------|
| LR1 | `minimal` depth + deterministic → fastest path, no LLM |
| LR2 | `standard` depth + LLM allowed → allow time for formatting |
| LR3 | `deep` / `expert` depth → higher latency; warn if cost budget is low |
| LR4 | Evidence mode has higher latency — external retrieval; offer async option |

### High-Frequency Query Cost Strategy:

If the same response type is selected for the same query pattern > 5 times in a session:

- Suppress LLM formatting after threshold
- Return deterministic-only response
- Note: "Response optimized for repeated query"

---

## SECTION 12 — Signal Recording Decision

Signal recording is read-only and never blocks a response. It is a background operation.

### Signal Recording Triggers:

| Signal | Trigger Condition |
|--------|-----------------|
| S1 — Repeated Unknown Query | Same `topic_normalized` appears >= 3 times with no handler match |
| S2 — Evidence Workspace Usage | Evidence mode activated |
| S4 — Frequent Fallback | Fallback fires >= 5 times in session |
| S5 — Repeated Improvement Query | "how can you improve" or equivalent >= 2 times |

### Signal Recording Rules:

| Rule | Description |
|------|-------------|
| SR1 | Only anonymized metrics recorded — no raw prompt stored |
| SR2 | Signal recording never delays or blocks the response |
| SR3 | Signal is passed to `WESLR_SIGNAL_AGGREGATION_V1.md` processor |
| SR4 | No S3/S4 signal from single session triggers surfacing alone |

---

## SECTION 13 — Safety Overrides

Safety overrides are the highest-priority decision path. No other rule applies when a safety flag is set.

### Override Table:

| Safety Flag | Policy Engine Action | Result |
|-------------|---------------------|--------|
| `write_attempt == true` | Block immediately | `final_response_type: "blocked_write"`, explain mode restriction |
| `unsafe_query == true` | Block immediately | `final_response_type: "blocked_write"`, safe fallback |
| `mode_violation == true` | Restrict to mode ceiling | Downgrade depth, suppress LLM |
| `insufficient_data == true` | Downgrade depth | `depth_level: "minimal"`, note limitation |

### Mode Violation Response:

When user input attempts to bypass mode restrictions:

```
This operation is not available in [mode] mode.
[Current mode] restricts [what is restricted].
To access this feature, use [appropriate mode].
```

Never expose internal mechanism names or registry details.

---

## SECTION 14 — Implementation Mapping

### Module Location:
```
weslr/omnichat/policy_engine.py
```

### Pipeline Position:

```
interpretation.py (Layer 2)
    ↓
policy_engine.py (Layer 2) ← THIS ENGINE
    ↓
expansion_layer.py (Layer 3)
    ↓
LLM formatter (Layer 4, optional)
    ↓
response
```

### Interpretation → Policy Engine Contract:

```python
policy_input = {
    "intent_class": str,           # from interpretation
    "response_type_candidate": str, # best-fit type
    "mode": str,                    # current mode
    "depth_preference": str,        # user or default
    "context_availability": str,    # rich/minimal
    "safety_flags": dict,
    "signal_indicators": dict,
    "cost_budget": float | None
}

policy_output = policy_engine.decide(policy_input)
```

### Policy Engine → Expansion Layer Contract:

```python
expansion_input = {
    "response_type": policy_output["final_response_type"],
    "structured_payload": handler_output,  # from deterministic/guided/graph handler
    "expansion_layers": policy_output["expansion_layers"],
    "depth_level": policy_output["depth_level"],
    "llm_formatter_allowed": policy_output["llm_formatter_allowed"],
    "evidence_mode_active": policy_output["evidence_mode_active"],
    "llm_input_contract": policy_output["llm_input_contract"]
}
```

---

## SECTION 15 — Non-Goals

The following are explicitly rejected from the policy engine:

| Rejected | Reason |
|----------|--------|
| Probabilistic response selection | Policy is rule-based; same inputs always produce same outputs |
| LLM-driven decision making | LLM is downstream only; policy decisions are deterministic |
| Adaptive behavior without governance | Behavioral changes require operator-reviewed proposals |
| User-driven system mutation | Mode and policy are operator-controlled |
| Hidden learning | Signal aggregation is documented, operator-visible |
| Dynamic threshold modification | Thresholds are set by operator, not auto-adjusted |

---

## SECTION 16 — Expected Outcome

When fully implemented, WESLR becomes:

| Property | Result |
|----------|--------|
| Adaptive in communication | Response type, depth, and expansion adjust to context |
| Consistent in behavior | Same inputs always produce same policy decision |
| Efficient in response | Deterministic path preferred; LLM used only when needed |
| Guided for users | Fallbacks offer alternatives; L4 guides next steps |
| Fully deterministic | No probabilistic selection; every decision is traceable |

---

## SECTION 17 — Cross-Doctrine Alignment

| Doctrine | Alignment |
|----------|-----------|
| WESLR_CORE_IDENTITY_V1.md | Policy engine enforces R4 (deterministic handlers), R6 (LLM downstream), R7 (no raw input stored) |
| WESLR_LAYERED_ARCHITECTURE_V1.md | Policy engine is Layer 2 component; communicates only with Layer 1 (handler output) and Layer 3 (expansion) |
| WESLR_COORDINATION_LAYER_V1.md | Policy engine IS the Coordination Layer's routing decision mechanism; enforces mode and write gate rules |
| WESLR_OMNI_EXECUTION_MODEL_V1.md | Policy engine implements Sections 4–10 of the execution model (intent routing, handler selection, LLM gate) |
| WESLR_LLM_CONTEXT_BOUNDARY_V1.md | Policy engine's LLM decision point enforces B1–B7; LLM input contract is the boundary's payload spec |
| WESLR_EVIDENCE_WORKSPACE_V1.md | Policy engine handles evidence offer/offer-accept flow; evidence workspace is a response type candidate |
| WESLR_SIGNAL_AGGREGATION_V1.md | Policy engine generates signal records from S1/S2/S4/S5 indicators; surfacing is operator-only |
| WESLR_RESPONSE_EXPANSION_LAYER_V1.md | Policy engine's `expansion_layers` output maps directly to L1–L4 defined in expansion layer doc |

---

## SECTION 18 — Verdict

**WESLR_RESPONSE_POLICY_ENGINE_V1_DEFINED**

The Response Policy Engine is the deterministic decision layer of WESLR — selecting response types, expansion depths, evidence activation, and LLM usage based on rule-based inputs. Every decision is traceable, mode-gated, and safety-bound. LLM is always downstream. Truth is always authoritative. No exceptions.

Core invariant: Policy engine decides HOW WESLR responds — it never decides WHAT WESLR knows.
