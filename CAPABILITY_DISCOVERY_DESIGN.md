# WESLR Capability Discovery Radar — Subsystem Design

## SECTION 1 — SUBSYSTEM PURPOSE

The Capability Discovery Radar is NOT a trend scanner.

A trend scanner asks: "What tools and techniques are popular?" — it tracks signals in the world.

The Capability Discovery Radar asks: "What can WESLR NOT do that it SHOULD be able to do?" — it tracks gaps.

It consumes signals from GitHub, Reddit, HN, and other sources not to identify trends, but to identify **capability gaps**. When it sees repeated mentions of a workflow or tool that implies a capability WESLR lacks, it generates a ranked suggestion for the operator to evaluate.

It's a gap detector disguised as a signal reader.

---

## SECTION 2 — DATA MODEL

```typescript
interface CapabilitySuggestion {
  id: string;                    // UUID v4
  title: string;                 // "Real-time collaboration editing"
  capability_type: 
    | "real_time_collab"
    | "ai_assisted_writing"
    | "visual_workflow_builder"
    | "cross_platform_sync"
    | "native_mobile"
    | "offline_first"
    | "markdown_extensions"
    | "data_integrations"
    | "automation_patterns"
    | "custom_theming"
    | "privacy_controls"
    | "backup_synchronization"
    | "api_access_level"
    | "audit_logging"
    | "team_management"
    | "custom_workflow_hooks"
    | "version_history"
    | "collaborative_annotations";
  
  summary: string;               // 1-2 sentences describing the capability
  why_it_matters: string;        // Impact on user workflow, productivity, or quality
  improvement_area: string;      // Which WESLR area it improves (e.g., "collaboration", "workflow")
  provenance: {
    sources: Array<{
      url: string;
      title: string;
      snippet: string;
      relevance_score: number;   // 0-1
      signal_type: "tool_mention" | "workflow_mention" | "capability_statement";
      timestamp: string;         // ISO 8601
    }>;
    detection_pattern: string;   // e.g., "tool X + workflow Y suggests capability Z"
  };
  
  confidence: number;            // 0-1 (how reliably does this signal a capability gap?)
  rank_score: number;            // 0-100, dynamically recomputed
  status: SuggestionStatus;
  denied_until?: string;         // ISO 8601 timestamp (if status=denied)
  
  created_at: string;            // ISO 8601
  last_seen_at: string;          // ISO 8601
  last_ranked_at?: string;       // ISO 8601
  
  // Search / filter fields
  tags: string[];
  mentions_count: number;        // How many signals detected this capability
  growth_trend: "declining" | "stable" | "growing" | "exploding";
  
  // Metadata for operator context
  first_seen_at?: string;        // First time this capability was detected
  source_diversity: number;      // Number of unique sources
  github_activity?: {
    stars: number;
    commits_last_30d: number;
    open_issues: number;
    last_commit: string;
  };
  science_relevance?: "low" | "medium" | "high";
  architectural_fit: "low" | "medium" | "high";  // How well it fits WESLR's architecture
}
```

---

## SECTION 3 — STATE MACHINE

```
┌─────────┐
│   NEW   │  ←─ Scanner creates suggestion from signal
└───┬─────┘
    │ Confidence threshold met
    ▼
┌─────────────┐
│ SUGGESTED   │  ←─ Ready for operator review
└───┬─────────┘
    │
    ├───[Operator Accept]───────►┌──────────┐
    │                            │ ACCEPTED │  ←─ Implementation queue
    │                            └──────────┘
    │
    ├───[Operator Deny]─────────┐
    │                           │ (record denied_until: now + 24h)
    ▼                           ▼
┌──────────┐                ┌─────────┐
│ DENIED   │◄─24h expiry───┤ SUGGESTED │
└──────────┘                └─────────┘
    │
    │ (new evidence arrives)
    ▼
┌───────────┐
│ SNOOZED   │  ←─ Operator manually suppresses (custom duration)
└─────┬─────┘
      │
      │ (duration expires OR new evidence)
      ▼
┌─────────┐
│SUGGESTED│
└─────────┘

┌─────────────┐
│   ARCHIVED  │  ←─ Irrelevant (no new signals in 30 days, low rank)
└─────────────┘

Transitions:

- NEW → SUGGESTED: Confidence ≥ 0.6
- SUGGESTED → ACCEPTED: Operator action "accept"
- SUGGESTED → DENIED: Operator action "deny" (sets denied_until = now + 24h)
- DENIED → SUGGESTED: denied_at + 24h elapsed AND new evidence
- SUGGESTED → SNOOZED: Operator action "snooze" (sets snoozed_until)
- SNOOZED → SUGGESTED: snoozed_until elapsed
- SUGGESTED → ARCHIVED: rank_score < 5 AND last_seen_at > 30d
- ARCHIVED → SUGGESTED: rank_score > 20 OR user searches archived
```

---

## SECTION 4 — DETECTION LOGIC

**Signal Sources:**

1. **GitHub** — Repositories, discussions, feature requests, issues
2. **Reddit** — Subreddits: r/selfhosted, r/privacy, r/tooling, r/programming
3. **HN** — Show HN, comments about workflow capabilities
4. **Product Hunt** — New tool launches with capability descriptions
5. **Twitter/X** — Tool developers announcing capabilities

**Detection Patterns:**

```typescript
interface Signal {
  type: "tool_mention" | "workflow_mention" | "capability_statement";
  text: string;
  url: string;
  timestamp: string;
  
  // Extracted capability hints
  capability_hint?: {
    name: string;
    description: string;
    evidence: string[];  // snippets from source
  };
  
  // Evidence that WESLR lacks this capability
  gap_evidence: {
    current_weslr_state: string;  // What WESLR can do now
    missing_capability: string;   // What is mentioned but missing
    impact: string;               // Why this matters
  };
}
```

**From Signal → Suggestion:**

1. Extract capability hint from signal text (NLP + pattern matching)
2. Compare against WESLR's known capabilities (database of features)
3. Generate gap_evidence: what's missing vs what's present
4. Compute confidence: 
   - Signal strength (upvotes, stars, comments)
   - Repeated mentions across sources
   - Source credibility
5. Build provenance object with all sources
6. Assign status = NEW, created_at = now, last_seen_at = now
7. Compute initial rank_score based on factors below

---

## SECTION 5 — RANKING

**Rank Score (0-100) Formula:**

```
rank_score = (
    mention_factor * 0.25 +
    growth_factor * 0.15 +
    source_diversity_factor * 0.15 +
    github_factor * 0.20 +
    science_factor * 0.10 +
    fit_factor * 0.15
)
```

**Components:**

| Factor | Formula / Logic | Weight |
|--------|-----------------|--------|
| **Mention Frequency** | log(mentions_count + 1) / log(1000) * 100 | 25% |
| **Growth Trend** | "declining"=20, "stable"=50, "growing"=80, "exploding"=100 | 15% |
| **Source Diversity** | min(unique_sources, 5) / 5 * 100 | 15% |
| **GitHub Activity** | stars/1000 + commits/50 + (issues > 0 ? 10 : 0) | 20% |
| **Science Relevance** | "high"=100, "medium"=60, "low"=20 | 10% |
| **Architectural Fit** | Operator score or ML classification | 15% |

**Dynamic Ranking:**

- Recompute rank_score every 24h
- Apply decay: rank_score = rank_score * 0.98^(days_since_seen)
- Boost signals with recent activity (last_seen_at < 7d)

---

## SECTION 6 — OPERATOR EXPERIENCE

**Operator UI Flow:**

```
┌─────────────────────────────────────────────┐
│  Capability Discovery Radar Dashboard      │
├─────────────────────────────────────────────┤
│  Search: [_________________]  Filter: All  │
├─────────────────────────────────────────────┤
│  ▼ New Capabilities (3)                    │
│    ┌─────────────────────────────────────┐ │
│    │ Real-time collaboration editing     │ │
│    │ Summary: ...                        │ │
│    │ Why it matters: ...                 │ │
│    │ Sources: GitHub, Reddit             │ │
│    │ Rank: 78  Confidence: 0.82          │ │
│    │ [Accept] [Deny] [Snooze] [Archive] │ │
│    └─────────────────────────────────────┘ │
│  ▼ Archived (12)                           │
└─────────────────────────────────────────────┘
```

**Actions:**

| Action | Behavior |
|--------|----------|
| **Accept** | Moves to ACCEPTED, creates task in WESLR backlog |
| **Deny** | Moves to DENIED, sets denied_until = now + 24h, suppresses display |
| **Snooze** | Moves to SNOOZED, sets snoozed_until = custom duration (1h, 4h, 1d, 3d, 7d) |
| **Archive** | Moves to ARCHIVED, will be auto-removed if rank_score stays low |
| **Search** | Filter by title, tags, capability_type, status, source |

**Search & Filter Syntax:**

```
# Search
"real-time collaboration"
capability_type:real_time_collab
source:github
status:suggested
rank:>70
confidence:>0.8

# Combined
"markdown extensions" source:reddit status:suggested rank:>50
```

---

## SECTION 7 — ARCHITECTURE FIT

```
┌─────────────────────────────────────────────────────────────────────┐
│                           WESLR Core                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │
│  │   Scanner    │→ │Concept Graph │→ │Request Intell│→ │Operator │ │
│  │ (signals)    │  │(cap graph)   │  │(tasks)       │  │  UI     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────┬───┘ │
│         │              │              │                    │        │
│         ▼              ▼              ▼                    ▼        │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Capability Discovery Radar                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────┐ │  │
│  │  │  Detector  │→ │  Normalizer│→ │  Ranker    │→ │Storage  │ │  │
│  │  │(signals→gap│  │(gap→sugg)  │  │(rank_score)│  │(DB)    │ │  │
│  │  │  evidence) │  │            │  │            │  │        │ │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └─────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│                    ┌─────────────────┐                              │
│                    │Operator Actions │                              │
│                    │(accept/deny/etc)│                              │
│                    └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

**Relationships:**

- **Scanner** → Provides raw signals (GitHub, Reddit, etc.)
- **Concept Graph** → WESLR's capability graph; used to detect gaps
- **Request Intelligence** → Operator workflow context; helps prioritize suggestions
- **Capability Discovery Radar** → Receives signals, generates suggestions, maintains state
- **Operator UI** → Displays suggestions, captures decisions

**Storage:**

- SQLite database (local-first, synced to Gateway if available)
- Tables: `capability_suggestions`, `suggestion_sources`, `operator_decisions`
- Search index:fts5 (SQLite full-text search)

---

## SECTION 8 — IMPLEMENTATION PLAN

**Phase 1 — Core Infrastructure (Week 1)**

- [ ] Create CapabilitySuggestion data model (TypeScript interface)
- [ ] Design SQLite schema with FTS5 support
- [ ] Implement basic CRUD operations
- [ ] Build simple CLI for suggestion management
- [ ] Implement state machine transitions (NEW→SUGGESTED, DENIED→SUGGESTED, etc.)

**Phase 2 — Detection Engine (Week 2)**

- [ ] Build GitHub scraper (issues, discussions, repos)
- [ ] Build Reddit scraper (subreddit queries)
- [ ] Implement signal parsing (extract capability hints)
- [ ] Implement gap detection (compare against WESLR capabilities)
- [ ] Compute confidence scores

**Phase 3 — Ranking Engine (Week 3)**

- [ ] Implement rank_score formula
- [ ] Add growth trend detection
- [ ] Build dynamic ranking scheduler (recompute every 24h)
- [ ] Implement decay logic

**Phase 4 — Operator Experience (Week 4)**

- [ ] Build simple web UI (Tauri + HTML/CSS)
- [ ] Implement search and filter
- [ ] Implement decision actions (accept/deny/snooze/archive)
- [ ] Store operator decisions in database

**Phase 5 — Integration (Week 5)**

- [ ] Connect to Scanner (receive signals)
- [ ] Connect to Concept Graph (gap detection)
- [ ] Connect to Request Intelligence (context-aware ranking)
- [ ] Add auto-archival (rank < 5 for 30 days)

**Phase 6 — Polish (Week 6)**

- [ ] Add mobile support (Tauri iOS/Android)
- [ ] Implement sync (Gateway → mobile)
- [ ] Add analytics (what capabilities are most requested)
- [ ] Build operator feedback loop (why was this denied?)

---

## SECTION 9 — STOP

- **Subsystems Design:** Capability Discovery Radar — gap detection, not trend scanning
- **Data Model:** CapabilitySuggestion (id, title, capability_type, summary, why_it_matters, improvement_area, provenance, confidence, rank_score, status, denied_until, created_at, last_seen_at, tags, mentions_count, growth_trend)
- **State Machine:** NEW → SUGGESTED (confidence ≥ 0.6) → ACCEPTED/DENIED/SNOOZED/ARCHIVED with 24h denial rule
- **Ranking Model:** 6-factor formula (mention frequency, growth, source diversity, GitHub activity, science relevance, architectural fit)
- **Architecture Fit:** Between Scanner/Concept Graph and Operator UI, as a central suggestion engine
- **Phased Plan:** 6 weeks — infrastructure, detection, ranking, UI, integration, polish
