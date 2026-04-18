# Request Intelligence Architecture

**Version:** 1.0.0  
**Status:** ACTIVE - Core Layer  
**Created:** 2026-04-05  
**Last Updated:** 2026-04-05  
**Updated:** 2026-04-05 - Finalized architecture with all subcomponents

---

## Purpose

The Request Intelligence layer provides medium-to-high intelligence for request processing in WESLR.

It exists to solve the architectural gap of "skipped middle layer" where:
- Simple keyword-based routing was insufficient
- Evidence policies were not enforced
- Provider suitability was not scored
- Uncertainty budgets were not tracked
- Task difficulty was not graded

This layer enables intelligent decisions about:
- Where to route requests (local evidence vs. external)
- What evidence is needed to answer requests
- Which providers can handle requests best
- How much uncertainty is acceptable
- What difficulty level a request represents

---

## Subsystem Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Request Intelligence Layer (NEW CORE)                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ • RequestClassifier — Classifies requests into structured categories         │
│ • KnowledgeState — Tracks what's known/unknown/unverifiable/speculative    │
│ • EvidencePolicy — Defines evidentiary requirements per request type         │
│ • CapabilityMatcher — Matches requests to available capabilities             │
│ • ProviderSuitability — Scores providers for fit                             │
│ • UncertaintyDiscipline — Enforces uncertainty budgets and fallback rules    │
│ • TaskDifficulty — Grades request difficulty (BASIC/MEDIUM/HIGH/EXTREME)    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Design Philosophy:**
- Additive: Does not replace existing routing, extends it
- Reversible: Can be disabled with a flag to revert to keyword-only routing
- Fast: All components are lightweight for runtime use
- Extensible: New categories, evidence types, providers can be added

---

## File/Module Map

```
weslr/request_intelligence/
├── __init__.py                 # Package initialization, exports
├── core.py                     # Main orchestrator, RequestIntelligence class
├── classifier.py               # RequestClassifier (category classification)
├── knowledge.py                # KnowledgeStateAnalyzer (known/unknown tracking)
├── evidence_policy.py          # EvidencePolicy, EvidencePolicyBuilder
├── capability_matcher.py       # CapabilityMatcher (capability matching)
├── provider_suitability.py     # ProviderSuitability (provider scoring)
├── uncertainty.py              # UncertaintyDiscipline (budget enforcement)
└── difficulty.py               # TaskDifficulty (difficulty grading)
    └── tests/
        ├── __init__.py
        ├── test_classifier.py
        ├── test_evidence_policy.py
        └── test_provider_suitability.py
```

**Module Dependencies:**
- No external dependencies (uses only Python stdlib)
- No runtime-specific dependencies (runtime-agnostic)
- Lazy-loading of submodules to minimize import overhead

---

## Runtime Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Request Processing Flow with Request Intelligence                       │
└─────────────────────────────────────────────────────────────────────────┘

Request Input
    ↓
┌──────────────────────┐
│ RequestIntelligence  │
│     .analyze()       │
└──────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────────────────┐
│ Subcomponents (all run in sequence)                                   │
├───────────────────────────────────────────────────────────────────────┤
│ 1. RequestClassifier                                                  │
│    - Primary routing category (LOCAL/EVIDENCE/RESEARCH/REASONING)    │
│    - Secondary capability requirements                               │
│    - Evidence requirements                                           │
├───────────────────────────────────────────────────────────────────────┤
│ 2. KnowledgeStateAnalyzer                                             │
│    - Known from evidence                                             │
│    - Known from context                                              │
│    - Unknown (potentially knowable)                                  │
│    - Unverifiable (subjective, etc.)                                 │
│    - Speculative (assumption-based)                                  │
├───────────────────────────────────────────────────────────────────────┤
│ 3. EvidencePolicyBuilder                                              │
│    - Minimum evidentiary standard                                    │
│    - Evidence tolerance (acceptable error margin)                    │
│    - Fallback policy (none/cached/fallback/reject)                   │
│    - Evidence type requirements                                      │
├───────────────────────────────────────────────────────────────────────┤
│ 4. CapabilityMatcher                                                  │
│    - Matching capabilities with scores                               │
│    - Evidence requirements per capability                            │
│    - Estimated latency per capability                                │
├───────────────────────────────────────────────────────────────────────┤
│ 5. ProviderSuitability                                                │
│    - Provider scores (0-1) for each provider                         │
│    - Evidence access scores                                            │
│    - Latency scores                                                  │
│    - Quality scores                                                  │
├───────────────────────────────────────────────────────────────────────┤
│ 6. UncertaintyDiscipline                                              │
│    - Uncertainty category (KNOWN/UNKNOWN/UNVERIFIABLE/SPECULATIVE)   │
│    - Uncertainty budget used                                         │
│    - Allowed flag (policy enforcement)                               │
│    - Confidence score                                                │
├───────────────────────────────────────────────────────────────────────┤
│ 7. TaskDifficultyGrader                                               │
│    - Difficulty grade (BASIC/MEDIUM/HIGH/EXTREME)                    │
│    - Difficulty score (0-10)                                         │
│    - Analysis of complexity signals                                  │
└───────────────────────────────────────────────────────────────────────┘
    ↓
Intelligence Report (comprehensive output)
    ↓
┌──────────────────────┐
│ Routing Decision   │
└──────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────────────────┐
│ Execution                                                             │
├───────────────────────────────────────────────────────────────────────┤
│ If difficulty=BASIC and allowed:                                      │
│   → Local evidence provider (time/weather APIs)                       │
├───────────────────────────────────────────────────────────────────────┤
│ If difficulty=MEDIUM and allowed:                                     │
│   → Local LLM with evidence caching                                   │
├───────────────────────────────────────────────────────────────────────┤
│ If difficulty=HIGH or EXTREME and allowed:                            │
│   → External provider (OpenAI/Claude) with web research              │
├───────────────────────────────────────────────────────────────────────┤
│ If not allowed:                                                       │
│   → Reject with explanation                                           │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Category Definitions

### Routing Categories (RequestClassifier)

| Category | Description | Requests |
|----------|-------------|----------|
| LOCAL | Can be handled with local evidence (time, weather, cached) | "What time is it?", "What's the weather in Rome?" |
| EVIDENCE | Requires external evidence (facts, statistics, research) | "Who is the president of Italy?", "What's the population of Rome?" |
| RESEARCH | Requires web research and synthesis | "Research the history of Rome", "Analyze this document" |
| REASONING | Requires complex reasoning and analysis | "Explain why this is true", "Compare these options" |
| UNSUPPORTED | Cannot be handled by any available capability | N/A (fallback to rejection) |

### Knowledge State Categories (KnowledgeStateAnalyzer)

| Category | Description | Example |
|----------|-------------|---------|
| KNOWN_FROM_EVIDENCE | Can be verified with available evidence | Weather, time, current facts |
| KNOWN_FROM_CONTEXT | Already in current context | Previous conversation topics, active threads |
| UNKNOWN | Unknown but potentially knowable with evidence | Historical facts, scientific data |
| UNVERIFIABLE | Cannot be verified (subjective, opinion-based) | "Should we do X?", "What's the meaning of life?" |
| SPECULATIVE | Highly uncertain, assumption-based | "Imagine a universe where...", "Predict the future" |

### Evidence Requirements (EvidencePolicy)

| Evidence Type | Description | Availability |
|---------------|-------------|--------------|
| TIME | System time evidence | Always available via evidence_api.py |
| WEATHER | Weather data evidence | Available via evidence_api.py (wttr.in) |
| WEB | Web search results | Available via research.py |
| FILE | File content analysis | Available via file_ingestion, pdf_context |
| CALCULATION | Math/computation results | Available via local calculation |
| CONTEXT | Existing context/snapshot | Available in session context |

### Difficulty Grades (TaskDifficulty)

| Grade | Description | Score Range | Examples |
|-------|-------------|-------------|----------|
| BASIC | Single-turn, deterministic, 0.5B model capable | 0-2.9 | Time queries, weather, simple facts |
| MEDIUM | Multi-step reasoning (2-3 steps), context synthesis | 3-4.9 | Analysis, comparison, explanation |
| HIGH | Complex multi-step (4+ steps), external research | 5-7.9 | Research, synthesis, complex analysis |
| EXTREME | Unbounded/open-ended, significant external facts | 8-10 | Philosophy, speculation, prediction |

---

## Evidence Policy Rules

### Policy Construction Rules

1. **Request Type Based:**
   - `time_query` → strict, minimal evidence, low tolerance
   - `weather_query` → comprehensive, cached fallback allowed
   - `factual_query` → minimal, cached fallback allowed
   - `research_query` → comprehensive, web evidence required

2. **Difficulty Based:**
   - BASIC → min confidence 0.8, max uncertainty 0.2
   - MEDIUM → min confidence 0.7, max uncertainty 0.3
   - HIGH → min confidence 0.6, max uncertainty 0.4
   - EXTREME → min confidence 0.5, max uncertainty 0.5

3. **Strategy Based:**
   - `conservative` → reject if any uncertainty exceeds threshold
   - `comprehensive` → allow fallback, use cached evidence
   - `minimal` → minimal requirements, allow fallback

### Fallback Policies

| Policy | When to Use | Behavior |
|--------|-------------|----------|
| `none` | Critical requests | Reject if evidence unavailable |
| `cached` | Time/weather | Use cached evidence if available |
| `fallback` | General requests | Use fallback provider |
| `reject` | Unverifiable requests | Reject with explanation |

---

## Uncertainty Rules

### Uncertainty Budget Rules

**Basic Budget:**
- Max uncertainty: 0.2 (20%)
- Min confidence: 0.8 (80%)
- Fallback: `cached`

**Medium Budget:**
- Max uncertainty: 0.3 (30%)
- Min confidence: 0.7 (70%)
- Fallback: `fallback`

**High Budget:**
- Max uncertainty: 0.4 (40%)
- Min confidence: 0.6 (60%)
- Fallback: `fallback`

**Extreme Budget:**
- Max uncertainty: 0.5 (50%)
- Min confidence: 0.5 (50%)
- Fallback: `fallback`

### Uncertainty Categories

| Category | Tolerance | Reasoning |
|----------|-----------|-----------|
| KNOWN | 0.0 | Can be verified with available evidence |
| UNKNOWN | 0.2 | Unknown but potentially knowable |
| UNVERIFIABLE | 0.5 | Cannot be verified (subjective) |
| SPECULATIVE | 0.8 | Based on assumptions, highly uncertain |

### Enforcement Rules

1. If `uncertainty_level > budget.max_uncertainty`: Reject
2. If `confidence < budget.min_confidence`: Reject
3. If category tolerance exceeded: Allow with warning
4. If allowed: Proceed with execution
5. If rejected: Return rejection with explanation

---

## Provider Suitability Logic

### Scoring Formula

```
score = (
    capability_score * 0.4 +
    evidence_score * 0.3 +
    latency_score * 0.15 +
    quality_score * 0.15
)
```

### Provider Characteristics

| Provider | Capabilities | Evidence Types | Latency (ms) | Quality | Cost |
|----------|-------------|----------------|--------------|---------|------|
| embedded | reasoning, analysis, local_generation | context, cached | 200 | 0.85 | free |
| llama-server | reasoning, analysis, generation | context, cached, local | 500 | 0.90 | free |
| ollama | reasoning, analysis, generation | context, cached, local | 800 | 0.88 | free |
| openai | reasoning, analysis, generation, research | context, cached, web, research | 1500 | 0.95 | paid |
| claude | reasoning, analysis, generation, synthesis | context, cached, web, research | 1200 | 0.94 | paid |
| evidence | time, weather, facts | time, weather, web | 500 | 0.99 | free |

### Provider Selection Logic

1. Score all providers for request
2. Select provider with highest score
3. If evidence provider suitable (score > 0.8), use evidence provider
4. If no provider scores above 0.5, reject request

---

## What Belongs in Core vs Capability vs Validation

### CORE (request_intelligence/)

**Purpose:** Intelligent request decision-making before execution

**In Core:**
- Request classification (category determination)
- Knowledge state analysis (what's known/unknown)
- Evidence policy (requirements and tolerances)
- Capability matching (what tools can help)
- Provider suitability (which provider to use)
- Uncertainty discipline (budget enforcement)
- Task difficulty grading (BASIC/MEDIUM/HIGH/EXTREME)

**Why in Core:**
- All components run before execution decision
- All components are lightweight and fast
- All components are reusable across runtimes
- All components are runtime-agnostic

### CAPABILITY (plugins/, weslr/*.py)

**Purpose:** Actual execution of capabilities

**In Capabilities:**
- Weather API calls
- Time API calls
- File processing
- PDF analysis
- Web research
- Calculation engines
- Reasoning engines

**Why Not in Core:**
- Capabilities are heavy (network, computation)
- Capabilities are provider-specific
- Capabilities are not decision-making logic

### VALIDATION (weslr/tests/, weslr/launch_gate.py)

**Purpose:** Post-execution validation and release gates

**In Validation:**
- Test harnesses for individual capabilities
- Launch gate scorecard
- Safety validation
- Security red-team testing

**Why Not in Core:**
- Validation runs after execution
- Validation is for quality assurance, not routing
- Validation can be expensive (full test suites)

---

## Usage Examples

### Basic Usage

```python
from weslr.request_intelligence import RequestIntelligence

# Initialize with context
context = {
    "active_thread": "weather_discussion",
    "continuity": {"topics": ["Rome", "Italy"]},
}

ri = RequestIntelligence(context)

# Analyze a request
report = ri.analyze("What's the weather in Rome?")

# Use the report for routing decision
if report.difficulty_grade["grade"] == "BASIC":
    # Use local evidence provider
    category = "LOCAL"
elif report.uncertainty_analysis["allowed"]:
    # Proceed with execution
    category = "EVIDENCE"
else:
    # Reject
    category = "REJECT"
```

### Integration with llm_runtime.py

```python
# In llm_runtime.py, before provider selection:

from weslr.request_intelligence import RequestIntelligence

def route_request(context: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Route request using Request Intelligence."""
    
    ri = RequestIntelligence(context)
    report = ri.analyze(context.get("proposed_theme", ""))
    
    # Get routing decision
    category, details = ri.get_routing_decision(context.get("proposed_theme", ""))
    
    return category, report.to_dict()
```

### Building Custom Policies

```python
from weslr.request_intelligence import (
    EvidencePolicy,
    EvidencePolicyBuilder,
    EvidenceRequirement,
    EvidenceType,
)

# Build custom policy
builder = EvidencePolicyBuilder()

# For strict requirements
policy = builder.get_strict_policy()

# For lenient requirements
policy = builder.get_default_policy()

# For specific request types
policy = builder.build_policy("research_query", difficulty=3)
```

---

## Validation

### Unit Tests

Run tests from `weslr/request_intelligence/tests/`:

```bash
# Classifier tests
python weslr/request_intelligence/tests/test_classifier.py

# Evidence policy tests
python weslr/request_intelligence/tests/test_evidence_policy.py

# Provider suitability tests
python weslr/request_intelligence/tests/test_provider_suitability.py
```

### Integration Tests

Integration tests should verify:
1. Request classification accuracy
2. Evidence policy construction
3. Provider suitability scoring
4. Integration with llm_runtime.py routing
5. End-to-end request flow

### Operator Validation

Operator-facing validation path:
- `weslr/request_intelligence/tests/` - Test harness
- `weslr/launch_gate.py` - Release gates that validate intelligence layer
- `weslr/safety.py` - Safety validation

---

## Future Extensions

### Possible Additions

1. **Caching Layer:**
   - Cache analysis results for repeated requests
   - Invalidate on context changes

2. **Telemetry:**
   - Track classification accuracy
   - Track provider selection effectiveness
   - Track uncertainty budget violations

3. **Advanced Classification:**
   - Natural language understanding (beyond keywords)
   - Context-aware classification (uses previous interactions)
   - Learn from errors (feedback loop)

4. **Multi-Step Requests:**
   - Plan multi-step reasoning
   - Track progress through steps
   - Adaptive resource allocation

5. **Cost-Aware Selection:**
   - Factor cost into provider selection
   - Optimize for cost-performance tradeoff

---

## References

- Current architecture snapshot (as of 2026-04-05)
- llm_runtime.py routing logic
- evidence_api.py evidence sources
- weslr/file_router.py file routing
- weslr/launch_gate.py release gates

---

**Document Status:** ACTIVE - Ready for use  
**Maintenance:** Update when Request Intelligence logic changes  
**Owner:** WESLR Core Team