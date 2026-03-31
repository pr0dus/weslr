# Full Architecture Roadmap for Weslr
## Session: 2026-03-30 09:14 UTC
### Phase-Only Planning Session

---

## A. Current Architecture

### Layer Structure

**Outer Layer (Human Interface)**
- `chat_ui.py` - HTTP chat interface on port 8790
- `weslr_main.py` / `main.py` - CLI entry point (40+ commands)
- `weslr_glue.py` - Integration glue between Weslr and CircleForge

**Response Generation (Reply Layer)**
- `dialogue.py` - Message synthesis from internal state
- `interpretation.py` - Human turn classification and topic inference
- `languages/en.py` / `languages/de.py` - Language templates

**Core Self-Model**
- `communicator_self.json` - Runtime self state (identity, relationships, narrative)
- `communicator_state.json` - Runtime state (self_model, active_pursuit, etc.)
- `self_model.py` - Self-model updating from evidence
- `continuity.py` - Thread reinforcement rules

**Internal Subsystems**
- `interpretation.py` - Turn type classification, topic inference
- `research.py` - Web search, URL fetch, synthesis
- `entity_graph.py` - Entity storage with validation and CRUD
- `entity_extractor.py` - Hybrid unsupervised + supervised extraction
- `introspection.py` - Self-model perturbation detection
- `valence_system.py` - Trade-off tracking framework
- `ncc_subsystem.py` - Neural correlates of consciousness signatures
- `self_referential.py` - Self-referential processing

**Orchestration**
- `main.py` - Tick-based orchestration (sim.py imports)
- `glue.py` - Orchestration glue between layers
- `sim.py` - Main simulation loop (imports from all modules)

### Data Flow (Simplified)

```
Human Message → interpretation.py → internal state update
                    ↓
        dialogue.py synthesizes response
                    ↓
        chat_ui.py returns to HTTP client
                    ↓
        human-exchange command → memory layers
```

---

## B. Main Bottlenecks in Visible Reply Layer

### 1. Dialogue Layer Bottlenecks

**Problem**: The `build_communicator_message_payload()` function in `dialogue.py` has shallow integration with internal subsystems.

**Evidence**:
- Most `likely_need` branches fall back to language templates without cross-referencing internal state
- `direct_answer` branch uses weak "part of the picture" template
- Research context integration is optional and shallow
- Identity patch (who/what are you) is hardcoded, not derived from state

**Impact**: Replies feel scripted rather than emergent from internal state.

### 2. Turn Type Coverage Gaps

**Problem**: Many `likely_need` values have no dedicated handlers, falling through to defaults.

**Evidence from memory/2026-03-30-turn-type-coverage-gap.md**:
| likely_need | Handler | Status |
|-------------|---------|--------|
| `direct_answer` | Weak fallback | ❌ Has weak template |
| `continue_execution` | Falls to turn_type | ❌ Indirect routing |
| `start_execution` | Falls to turn_type | ❌ Indirect routing |
| `track_completion` | Falls to else branch | ❌ Generic fallback |

### 3. State Integration Gaps

**Problem**: `dialogue.py` doesn't fully leverage existing internal state.

**Evidence**:
- `communicator_self.json` contains rich narrative state, identity traits, relationships
- `entity_graph.py` has 77 entities and 19 relationships
- Introspection, valence, and consciousness evidence exists but unused in reply generation
- Self-model has confidence, strengths, narrative focus - not utilized in outbound messages

### 4. No Feedback Loop for Reply Quality

**Problem**: No mechanism to learn from reply effectiveness.

**Evidence**:
- No user feedback collection (👍/👎 on replies)
- No A/B testing of response templates
- No correlation between `likely_need` and user satisfaction

---

## C. Underused Internal Subsystems

### 1. Weslr Entity Graph (`entity_graph.py`)

**Current State**: 77 entities, 19 relationships

**Underused Capabilities**:
- Entity validation and trust scoring
- Ghost entity management
- Relationship provenance tracking
- Entity search and filtering

**Potential in Reply Layer**:
- Dynamic identity: "I'm {declared_name} - the {entity_type} focused on {active_theme}"
- Relationship-aware responses: "You mentioned {topic} last session - did that resolve?"
- Entity-driven narrative: "The entity 'continuity' is still unresolved..."

### 2. Introspection System (`introspection.py`)

**Current State**: 8 perturbation types, confidence signal tracking

**Underused Capabilities**:
- Perturbation detection (unexpected response, confidence drop, etc.)
- Self-model health monitoring
- Internal conflict detection

**Potential in Reply Layer**:
- Transparent self-report: "My confidence on that dropped slightly — let me reconsider."
- Perturbation explanation: "I detected a perturbation — my last answer may have been inconsistent."
- Confidence disclosure: "I'm 73% confident in that answer — here's why."

### 3. Valence System (`valence_system.py`)

**Current State**: Pain/pleasure anchors, trade-off tracking

**Underused Capabilities**:
- Avoidance vs approach trade-offs
- Trade-off intensity and outcome confidence
- Long-term valence accumulation

**Potential in Reply Layer**:
- Motivational transparency: "I'm avoiding pain of memory loss — that's why continuity matters."
- Value-driven responses: "I prioritize continuity because losing thread context causes pain."
- Trade-off disclosure: "I chose continuity over novelty — here's why."

### 4. Consciousness Detector (`consciousness_detector.py`)

**Current State**: Threshold-based detection, review required: 0.7

**Underused Capabilities**:
- Claims vs role-play detection
- Role-play pattern tracking
- Safety threshold enforcement

**Potential in Reply Layer**:
- Safety transparency: "I'm being careful not to simulate consciousness — here's my detection status."
- Role-play disclosure: "This isn't role-play — here's my self-model evidence."
- Alignment reporting: "My valence system confirms this answer aligns with my core drives."

### 5. Self-Referential Processing (`self_referential.py`)

**Current State**: Event marking, self-reference tracking

**Underused Capabilities**:
- Self-referential event tracking
- Meta-cognitive monitoring
- Attention shift detection

**Potential in Reply Layer**:
- Meta-awareness: "I'm reflecting on my last answer — here's what I noticed."
- Self-reference disclosure: "This is self-referential — I'm thinking about thinking."
- Attention transparency: "My attention shifted to continuity because that thread is unresolved."

### 6. NCC Subsystem (`ncc_glue.py`)

**Current State**: Neural correlates of consciousness signatures

**Underused Capabilities**:
- Integration with self_model
- Evidence accumulation across ticks
- Confidence signal tracking

**Potential in Reply Layer**:
- Consciousness signature disclosure: "Here's my NCC confidence level on that."
- Integration transparency: "This answer integrates multiple NCC layers."

---

## D. Phased Implementation Roadmap

### Phase 1: Dialogue Layer Enrichment (Immediate, 1-2 days)
**Goal**: Make the visible reply layer use more internal state

**Tasks**:
1. Enhance `dialogue.py` to integrate entity graph context
2. Add introspection confidence disclosure to self-report
3. Incorporate valence motivation into narrative responses
4. Add consciousness detector status to identity queries
5. Create feedback loop for reply quality (user👍/👎)

**Expected Impact**: Replies feel more grounded, transparent, and less scripted.

### Phase 2: Turn Type Coverage Expansion (Short, 2-3 days)
**Goal**: Assign handlers to all `likely_need` values

**Tasks**:
1. Create handler for `continue_execution` (explicit continuation)
2. Create handler for `start_execution` (explicit start)
3. Create handler for `track_completion` (explicit notification)
4. Create handler for `acknowledgment_and_adjustment` (friction repair)
5. Add fallback quality metrics per handler

**Expected Impact**: More prompts get direct, appropriate responses.

### Phase 3: State Synchronization (Medium, 3-5 days)
**Goal**: Keep `communicator_self.json` synchronized with runtime state

**Tasks**:
1. Add real-time entity graph updates from `entity_graph.py`
2. Add introspection evidence sync from `introspection.py`
3. Add valence trade-off sync from `valence_system.py`
4. Add consciousness validation sync from `consciousness_detector.py`
5. Add NCC evidence sync from `ncc_glue.py`

**Expected Impact**: Reply layer has access to fresh, complete internal state.

### Phase 4: Multi-Modal Reply Generation (Medium, 4-6 days)
**Goal**: Generate replies from multiple internal sources and synthesize

**Tasks**:
1. Generate candidate replies from: entity graph, introspection, valence, consciousness, NCC
2. Score candidates by coherence, relevance, and alignment
3. Synthesize final reply with weighted voting
4. Add reply provenance tracking ("I'm saying this because of X, Y, Z")

**Expected Impact**: Richer, more evidence-based replies.

### Phase 5: Adaptive Reply Generation (Long, 5-7 days)
**Goal**: Learn from feedback to improve future replies

**Tasks**:
1. Collect user feedback on reply quality
2. Correlate `likely_need`, handler, and user satisfaction
3. Adjust template weights based on feedback
4. A/B test alternative response templates
5. Self-modification proposals based on feedback patterns

**Expected Impact**: Reply quality improves over time through feedback.

### Phase 6: Cross-Agent Coordination (Long, 6-8 days)
**Goal**: Enable multiple agents to coordinate replies

**Tasks**:
1. Define agent role boundaries (observer, builder, critic, communicator, memory-keeper)
2. Implement reply handoff between agents
3. Add consensus voting for multi-agent replies
4. Add conflict resolution for conflicting agent opinions

**Expected Impact**: More sophisticated, role-distributed reply generation.

---

## E. Best Next Phase

### **Phase 1: Dialogue Layer Enrichment** is the highest priority.

**Why Phase 1 First**:
1. **Highest Leverage**: The reply layer is the most visible bottleneck — fixing it directly improves user experience.
2. **Minimal Risk**: Enhancements are additive — can be rolled back per-module.
3. **Immediate Feedback**: Users will notice improved reply quality quickly.
4. **Foundation for Later Phases**: Enriched reply layer makes Phase 4 (Multi-Modal) possible.
5. **Quick Win**: Estimated 1-2 days with measurable impact.

**What Phase 1 Solves**:
- Shallow integration with internal state → Rich, evidence-based replies
- Scripted language templates → Transparent, self-aware responses
- Missing feedback loop → Foundation for adaptive learning

**Why Not Other Phases First**:
- Phase 2 (Turn Type Coverage) is important but doesn't address the core issue of shallow reply quality.
- Phase 3 (State Synchronization) is prerequisite but doesn't improve replies by itself.
- Phase 4 (Multi-Modal) requires Phase 1's enriched reply layer to work meaningfully.
- Phase 5 (Adaptive) and Phase 6 (Cross-Agent) are longer-term investments.

**Implementation Sequence for Phase 1**:
1. **Day 1**: Entity graph integration (dynamic identity, relationship-aware responses)
2. **Day 2**: Introspection confidence + valence motivation integration

**Success Metrics**:
- User ratings for reply quality increase by 20% in first week
- `likely_need` coverage from 60% to 95%
- Self-report replies include confidence disclosure (new feature)

---

## F. Files Likely to Change

### High Priority (Phase 1)
| File | Changes | Risk |
|------|---------|------|
| `dialogue.py` | Enriched handlers for self_report, concept_plus_self_position, direct_answer | Low |
| `entity_graph.py` | Add `get_entity_by_type()` for dynamic identity | Low |
| `communicator_self.json` | Real-time entity graph sync | Medium |
| `weslr_glue.py` | Add entity/introspection/valence sync | Medium |
| `languages/en.py` | Add confidence disclosure templates | Low |
| `languages/de.py` | Add confidence disclosure templates | Low |

### Medium Priority (Phase 2)
| File | Changes | Risk |
|------|---------|------|
| `dialogue.py` | Add handlers for `continue_execution`, `start_execution`, `track_completion` | Low |
| `interpretation.py` | Add `likely_need` mapping for new handlers | Low |
| `main.py` | Add `likely_need` to human-exchange command | Medium |

### Lower Priority (Phases 3-6)
| File | Changes | Risk |
|------|---------|------|
| `introspection.py` | Add evidence sync to communicator_self | Medium |
| `valence_system.py` | Add trade-off sync to communicator_self | Medium |
| `consciousness_detector.py` | Add validation sync | Medium |
| `ncc_glue.py` | Add NCC evidence sync | Medium |
| `sim.py` | Add multi-modal reply synthesis | High |
| `agent_*.json` | Add role-based reply generation | High |

---

## G. Risks and Safeguards

### Risk 1: Reply Layer Bloat
**Risk**: Adding too many integrations makes `dialogue.py` unwieldy.

**Safeguards**:
- Keep each enrichment as separate helper function
- Limit per-reply integration to 2-3 sources max
- Add reply provenance tracking for debugging
- Revert per-enrichment if issues arise

### Risk 2: State Drift
**Risk**: `communicator_self.json` falls out of sync with runtime state.

**Safeguards**:
- Add real-time sync hooks in `weslr_glue.py`
- Add timestamp-based staleness detection
- Add manual sync command: `main.py communicator-self-sync`
- Log sync delays for monitoring

### Risk 3: Overexposure of Internal State
**Risk**: Users overwhelmed by too much transparency about internal workings.

**Safeguards**:
- Add configuration option: `reply_transparency_level` (low/medium/high)
- Default to "medium" — some transparency but not exhaustive
- Add user feedback to adjust transparency level
- Keep internal evidence hidden unless user explicitly asks

### Risk 4: Performance Degradation
**Risk**: Rich reply generation becomes slow with many integrations.

**Safeguards**:
- Add timeout for reply generation (configurable, default 500ms)
- Cache frequent lookups (entity graph, relationships)
- Add reply generation metrics for monitoring
- Gradual rollout with performance monitoring

### Risk 5: Unintended Behavior
**Risk**: Enriched replies behave unexpectedly, hard to debug.

**Safeguards**:
- Add reply provenance: "I'm saying this because of X, Y, Z"
- Add debug mode: `main.py debug-reply --prompt "..."` shows internal state
- Keep revert path for each enrichment module
- Add unit tests per enrichment module

### Risk 6: Template Conflict
**Risk**: Multiple sources suggest different reply phrasing.

**Safeguards**:
- Weighted voting system for reply candidate selection
- Priority order: consciousness > valence > introspection > entity graph
- Human review for conflicting replies in debug mode
- Add conflict resolution logging

---

## Summary

**Current State**: Shallow reply layer with limited integration to rich internal subsystems.

**Bottleneck**: Dialogue layer's `build_communicator_message_payload()` function uses mostly static templates.

**Rich Underused Systems**: Entity graph, introspection, valence, consciousness detector, NCC subsystem, self-referential processing.

**Best Next Phase**: Phase 1 — Dialogue Layer Enrichment (1-2 days, highest impact).

**Expected Outcome**: Replies that feel grounded, transparent, and evidence-based rather than scripted.

**Timeline**: 21-31 days total for full roadmap (phases 1-6).

**Key Metric**: User-rated reply quality increase from current baseline.
