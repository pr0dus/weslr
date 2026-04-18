# Session: 2026-04-08 11:39:32 UTC

- **Session Key**: agent:main:main
- **Session ID**: 93ff4d78-dbc9-4011-bf08-bbce0114790d
- **Source**: webchat

## Conversation Summary

user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Wed 2026-04-08 13:15 GMT+2] Proceed to PHASE 2 — INTERNAL REASONING GRAPH DESIGN

Use the completed Phase 1 audit as ground truth.

Requirements for this phase:

1. preserve the separation:

- "concept_graph" = world/domain knowledge
- "architecture_memory" = decision history
- "internal_reasoning_graph" = current structural self-architecture reasoning

2. explicitly state:

- what graph/storage primitives can be safely reused from "concept_graph"
- what must remain distinct because architecture reasoning semantics differ

3. define the exact schema for:

- node types
- edge types
- required fields
- validation rules

4. design around reasoning queries, not just storage
 Include exact examples of queries for:

- bottleneck tracing
- dependency impact
- proposal impact analysis
- architecture gap detection
- governance blocking

5. preserve governance:

- graph may support self-study and proposal generation
- graph may NOT support silent autonomous mutation

Output only:

1. reusable vs distinct primitive analysis
2. exact node schema
3. exact edge schema
4. exact reasoning query set
5. governance boundary design
6. stop
assistant: # PHASE 2 — INTERNAL REASONING GRAPH DESIGN

## 1. REUSABLE VS DISTINCT PRIMITIVE ANALYSIS

### Reusable Primitives (Safe to Reuse)

| Primitive | Source | Reuse Strategy | Why Safe |
|-----------|--------|----------------|----------|
| **Concept** | `concept_graph/models.py` | Extend with `concept_type="architecture"` | Architecture nodes are concepts with architecture-specific metadata |
| **Link** | `concept_graph/models.py` | Extend with `link_type` enums for architecture | Link semantics preserved, just different domain |
| **Evidence** | `concept_graph/models.py` | Reuse as-is | Evidence is domain-agnostic |
| **Persistence pattern** | `concept_graph/store.py` | Reuse store infrastructure | Same save/load/merge patterns apply |
| **Indexing** | `concept_graph/index.py` | Reuse index methods | Backlinks, by_name, by_type work identically |
| **Query engine pattern** | `concept_graph/query.py` | Reuse query methods | Path finding, centrality agnostic to domain |

### Distinct Primitives (Must Remain Separate)

| Primitive | Reason | Distinct Implementation Required |
|-----------|--------|----------------------------------|
| **Node Type Extension** | Architecture nodes need `node_subtype` (subsystem/capability/bottleneck/policy/workflow) | New subclass or metadata |
| **Link Type Extension** | Architecture edges need `depends_on`, `strengthens`, `replaces`, `bottleneck_for`, `governed_by`, `proposes_change_to`, `validated_by`, `conflicts_with` | New LinkType enum |
| **Validation Rules** | Architecture graph requires governance gates, proposal validation, trust boundary checks | Separate validation layer |
| **Reasoning Queries** | Architecture reasoning needs unique queries (gap detection, impact analysis, governance blocking) | New query engine |
| **Trust Boundary** | Architecture proposals require operator approval, not model-asserted | Separate trust validation |
| **Evidence Threshold** | Architecture decisions require higher evidence thresholds (conservative) | Distinct confidence thresholds |

### Summary: Reuse 80%, Extend 20%

- **Storage**: Reuse `ConceptGraphStore` infrastructure, extend with architecture-specific validation
- **Indexing**: Reuse index methods, extend with architecture-specific indices
- **Querying**: Reuse query patterns, extend with architecture reasoning methods
- **Validation**: New governance layer (distinct from concept_graph validation)

---

## 2. EXACT NODE SCHEMA

### Node Type: `subsystem`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique subsystem ID (e.g., "v94_knowledge_assimilation") |
| `name` | `str` | Yes | Human-readable name |
| `description` | `str` | Yes | Full description of subsystem purpose |
| `node_type` | `Literal["subsystem", "capability", "bottleneck", "policy", "workflow", "dependency", "proposal", "research_finding", "trust_gate"]` | Yes | Node subtype |
| `node_subtype` | `Literal["detection", "normalization", "synthesis", "policy", "governance", "communication"]` | Conditional | Subsystem-specific subtype |
| `version` | `str` | No | Version string (e.g., "v94.0.0") |
| `status` | `Literal["active", "deprecated", "proposed", "rejected"]` | Yes | Status |
| `confidence` | `float` | Yes | Confidence in subsystem correctness (0.0-1.0) |
| `created_at` | `int` | Yes | Unix timestamp |
| `updated_at` | `int` | Yes | Unix timestamp |
| `metadata` | `Dict[str, Any]` | No | Subsystem-specific metadata |
| `links` | `List[Link]` | No | Outgoing links |
| `evidence` | `List[Evidence]` | No | Supporting evidence |

### Node Type: `capability`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique capability ID (e.g., "autonomous_knowledge_detection") |
| `name` | `str` | Yes | Human-readable name |
| `description` | `str` | Yes | Capability description |
| `node_type` | `Literal["capability"]` | Yes | Always "capability" |
| `node_subtype` | `Literal["detection", "normalization", "synthesis", "analysis", "synthesis_proposal", "governance", "communication"]` | Yes | Capability subtype |
| `domain` | `str` | No | Domain-specific capability (e.g., "weslr_core", "scientific_research") |
| `inputs` | `List[str]` | No | Input requirements (concept IDs) |
| `outputs` | `List[str]` | No | Output expectations (concept IDs) |
| `confidence_threshold` | `float` | Yes | Minimum confidence threshold (0.0-1.0) |
| `evidence_threshold` | `int` | Yes | Minimum evidence count |
| **extends subsystem** | Yes | Capabilities are specialized subsystems |

### Node Type: `bottleneck`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique bottleneck ID (e.g., "no_autonomous_detection") |
| `name` | `str` | Yes | Human-readable name |
| `description` | `str` | Yes | Bottleneck description |
| `node_type` | `Literal["bottleneck"]` | Yes | Always "bottleneck" |
| `severity` | `Literal["critical", "high", "medium", "low"]` | Yes | Severity level |
| `impact_on` | `List[str]` | No | Subsystem IDs affected |
| `detection_method` | `str` | No | How bottleneck was detected |
| **extends capability** | Yes | Bottlenecks are specialized capabilities |

### Node Type: `policy`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique policy ID (e.g., "conservative_acceptance") |
| `name` | `str` | Yes | Human-readable name |
| `description` | `str` | Yes | Policy description |
| `node_type` | `Literal["policy"]` | Yes | Always "policy" |
| `applies_to` | `List[str]` | Yes | Subsystem IDs this policy applies to |
| `enforcement_level` | `Literal["hard", "soft", "advisory"]` | Yes | Enforcement strength |
| `violation_action` | `Literal["reject", "escalate", "log_only"]` | Yes | Action on violation |
| **extends subsystem** | Yes | Policies are specialized subsystems |

### Node Type: `workflow`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique workflow ID (e.g., "proposal_to_review") |
| `name` | `str` | Yes | Human-readable name |
| `description` | `str` | Yes | Workflow description |
| `node_type` | `Literal["workflow"]` | Yes | Always "workflow" |
| `steps` | `List[str]` | Yes | Step IDs in order |
| `governance_required` | `bool` | Yes | Whether operator approval required |
| **extends subsystem** | Yes | Workflows are specialized subsystems |

### Node Type: `dependency`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique dependency ID |
| `name` | `str` | Yes | Human-readable name |
| `description` | `str` | Yes | Dependency description |
| `node_type` | `Literal["dependency"]` | Yes | Always "dependency" |
| `required_by` | `str` | Yes | Subsystem ID that requires this dependency |
| `minimum_version` | `str` | No | Minimum version required |
| **extends subsystem** | Yes | Dependencies are specialized subsystems |

### Node Type: `proposal`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique proposal ID (e.g., "prop_abc123") |
| `name` | `str` | Yes | Human-readable name |
| `description` | `str` | Yes | Proposal description |
| `node_type` | `Literal["proposal"]` | Yes | Always "proposal" |
| `proposed_by` | `str` | Yes | Proposal source (operator/model/research) |
| `proposed_at` | `int` | Yes | Unix timestamp |
| `status` | `Literal["pending", "reviewing", "approved", "rejected"]` | Yes | Proposal status |
| `confidence` | `float` | Yes | Proposal confidence (0.0-1.0) |
| `required_governance` | `Literal["operator_review", "model_assisted", "none"]` | Yes | Governance requirement |
| `governance_status` | `Literal["pending", "approved", "rejected"]` | Yes | Governance decision |
| `governance_decided_at` | `Optional[int]` | No | Timestamp of governance decision |
| **extends subsystem** | Yes | Proposals are specialized subsystems |

### Node Type: `research_finding`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique finding ID |
| `name` | `str` | Yes | Human-readable name |
| `description` | `str` | Yes | Finding description |
| `node_type` | `Literal["research_finding"]` | Yes | Always "research_finding" |
| `source` | `str` | Yes | Research source (paper, experiment, observation) |
| `confidence` | `float` | Yes | Finding confidence (0.0-1.0) |
| `validated_by` | `List[str]` | No | Validation subsystem IDs |
| **extends capability** | Yes | Research findings are specialized capabilities |

### Node Type: `trust/governance_gate`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique gate ID |
| `name` | `str` | Yes | Human-readable name |
| `description` | `str` | Yes | Gate description |
| `node_type` | `Literal["trust_gate"]` | Yes | Always "trust_gate" |
| `gate_type` | `Literal["proposition", "modification", "proposal", "assimilation"]` | Yes | Gate type |
| `approval_required` | `bool` | Yes | Whether approval required |
| `rejection_action` | `Literal["reject", "escalate", "retry"]` | Yes | Action on rejection |
| **extends subsystem** | Yes | Gates are specialized subsystems |

---

## 3. EXACT EDGE SCHEMA

### Edge Type: `depends_on`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | Yes | Dependent subsystem ID |
| `target_id` | `str` | Yes | Required dependency ID |
| `link_type` | `Literal["depends_on"]` | Yes | Always "depends_on" |
| `confidence` | `float` | Yes | Confidence in dependency (0.0-1.0) |
| `reason` | `str` | Yes | Why this dependency exists |
| `evidence` | `List[Evidence]` | No | Supporting evidence |
| `created_at` | `int` | Yes | Timestamp |
| `updated_at` | `int` | Yes | Timestamp |
| **Cardinality**: 1:N (one subsystem, many dependencies) |

### Edge Type: `strengthens`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | Yes | Strengthening node ID |
| `target_id` | `str` | Yes | Target node ID |
| `link_type` | `Literal["strengthens"]` | Yes | Always "strengthens" |
| `confidence` | `float` | Yes | Confidence in strengthening (0.0-1.0) |
| `reason` | `str` | Yes | How this strengthens the target |
| `evidence` | `List[Evidence]` | No | Supporting evidence |
| `created_at` | `int` | Yes | Timestamp |
| `updated_at` | `int` | Yes | Timestamp |
| **Cardinality**: 1:N (one node, many strengthenings) |

### Edge Type: `replaces`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | Yes | Replacing node ID |
| `target_id` | `str` | Yes | Replaced node ID |
| `link_type` | `Literal["replaces"]` | Yes | Always "replaces" |
| `confidence` | `float` | Yes | Confidence in replacement (0.0-1.0) |
| `reason` | `str` | Yes | Why this replaces the target |
| `evidence` | `List[Evidence]` | No | Supporting evidence |
| `created_at` | `int` | Yes | Timestamp |
| `updated_at` | `int` | Yes | Timestamp |
| **Cardinality**: 1:1 (one-to-one replacement) |

### Edge Type: `bottleneck_for`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | Yes | Bottleneck ID |
| `target_id` | `str` | Yes | Affected subsystem ID |
| `link_type` | `Literal["bottleneck_for"]` | Yes | Always "bottleneck_for" |
| `severity` | `Literal["critical", "high", "medium", "low"]` | Yes | Severity |
| `reason` | `str` | Yes | How bottleneck affects target |
| `evidence` | `List[Evidence]` | No | Supporting evidence |
| `created_at` | `int` | Yes | Timestamp |
| `updated_at` | `int` | Yes | Timestamp |
| **Cardinality**: 1:N (one bottleneck, many affected) |

### Edge Type: `governed_by`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | Yes | Governed subsystem ID |
| `target_id` | `str` | Yes | Governance policy ID |
| `link_type` | `Literal["governed_by"]` | Yes | Always "governed_by" |
| `enforcement_level` | `Literal["hard", "soft", "advisory"]` | Yes | Enforcement strength |
| `reason` | `str` | Yes | Why this governance applies |
| `evidence` | `List[Evidence]` | No | Supporting evidence |
| `created_at` | `int` | Yes | Timestamp |
| `updated_at` | `int` | Yes | Timestamp |
| **Cardinality**: 1:N (one subsystem, many policies) |

### Edge Type: `proposes_change_to`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | Yes | Proposal ID |
| `target_id` | `str` | Yes | Subsystem/Policy ID being proposed |
| `link_type` | `Literal["proposes_change_to"]` | Yes | Always "proposes_change_to" |
| `change_type` | `Literal["add", "modify", "remove", "replace"]` | Yes | Type of change |
| `proposed_value` | `str` | No | Proposed new value |
| `reason` | `str` | Yes | Why this change is proposed |
| `evidence` | `List[Evidence]` | No | Supporting evidence |
| `created_at` | `int` | Yes | Timestamp |
| `updated_at` | `int` | Yes | Timestamp |
| **Cardinality**: 1:N (one proposal, many targets) |

### Edge Type: `validated_by`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | Yes | Validated node ID |
| `target_id` | `str` | Yes | Validation subsystem ID |
| `link_type` | `Literal["validated_by"]` | Yes | Always "validated_by" |
| `confidence` | `float` | Yes | Validation confidence (0.0-1.0) |
| `status` | `Literal["valid", "invalid", "pending"]` | Yes | Validation status |
| `reason` | `str` | Yes | Why this validates the target |
| `evidence` | `List[Evidence]` | No | Supporting evidence |
| `created_at` | `int` | Yes | Timestamp |
| `updated_at` | `int` | Yes | Timestamp |
| **Cardinality**: 1:N (one node, many validations) |

### Edge Type: `conflicts_with`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | Yes | Conflicting node ID |
| `target_id` | `str` | Yes | Conflicted node ID |
| `link_type` | `Literal["conflicts_with"]` | Yes | Always "conflicts_with" |
| `conflict_type` | `Literal["contradiction", "redundancy", "incompatibility"]` | Yes | Conflict type |
| `confidence` | `float` | Yes | Confidence in conflict (0.0-1.0) |
| `reason` | `str` | Yes | Why these conflict |
| `evidence` | `List[Evidence]` | No | Supporting evidence |
| `created_at` | `int` | Yes | Timestamp |
| `updated_at` | `int` | Yes | Timestamp |
| **Cardinality**: 1:N (one node, many conflicts) |

---

## 4. EXACT REASONING QUERY SET

### Query 1: Bottleneck Tracing

**Purpose**: Identify all bottlenecks affecting a subsystem and trace impact chains

**Query Pattern**:
```
INPUT: subsystem_id (e.g., "v94_knowledge_assimilation")
OUTPUT: List[bottleneck_id] with severity and impact_chain
```

**Implementation**:
```python
def trace_bottlenecks_for_subsystem(store: ConceptGraphStore, subsystem_id: str) -> List[Dict[str, Any]]:
    """Find all bottlenecks affecting a subsystem and trace impact chains."""
    # Load subsystem
    subsystem = store.load_concept(subsystem_id)
    if not subsystem:
        return []
    
    # Find bottleneck_for edges
    bottlenecks = []
    for link in subsystem.links:
        if link.link_type == "bottleneck_for":
            bottleneck_id = link.source_id
            bottleneck = store.load_concept(bottleneck_id)
            if bottleneck and bottleneck.node_type == "bottleneck":
                bottlenecks.append({
                    "bottleneck_id": bottleneck_id,
                    "name": bottleneck.name,
                    "severity": link.severity,
                    "reason": link.reason,
                    "confidence": link.confidence
                })
    
    return bottlenecks
```

### Query 2: Dependency Impact Analysis

**Purpose**: Trace dependency chains and identify impact of missing dependencies

**Query Pattern**:
```
INPUT: subsystem_id, include_missing: bool = True
OUTPUT: List[dependency_chain] with status and impact
```

**Implementation**:
```python
def trace_dependency_impact(store: ConceptGraphStore, subsystem_id: str, include_missing: bool = True) -> List[Dict[str, Any]]:
    """Trace dependency chains and identify impact of missing dependencies."""
    chains = []
    
    def dfs_dependencies(current_id: str, path: List[str], visited: Set[str]):
        if current_id in visited:
            return
        visited.add(current_id)
        
        subsystem = store.load_concept(current_id)
        if not subsystem:
            if include_missing:
                chains.append({"path": path, "status": "missing", "impact": "unknown"})
            return
        
        for link in subsystem.links:
            if link.link_type == "depends_on":
                target_id = link.target_id
                target = store.load_concept(target_id)
                
                if target:
                    new_path = path + [target_id]
                    # Check for missing dependencies recursively
                    dfs_dependencies(target_id, new_path, visited.copy())
                elif include_missing:
                    chains.append({"path": path + [target_id], "status": "missing", "impact": link.reason})
    
    dfs_dependencies(subsystem_id, [subsystem_id], set())
    return chains
```

### Query 3: Proposal Impact Analysis

**Purpose**: Trace proposal chains and identify impact on architecture

**Query Pattern**:
```
INPUT: proposal_id
OUTPUT: List[affected_node] with change_type and confidence
```

**Implementation**:
```python
def analyze_proposal_impact(store: ConceptGraphStore, proposal_id: str) -> List[Dict[str, Any]]:
    """Trace proposal chains and identify impact on architecture."""
    proposal = store.load_concept(proposal_id)
    if not proposal or proposal.node_type != "proposal":
        return []
    
    affected = []
    for link in proposal.links:
        if link.link_type == "proposes_change_to":
            target_id = link.target_id
            target = store.load_concept(target_id)
            if target:
                affected.append({
                    "target_id": target_id,
                    "target_name": target.name,
                    "change_type": link.change_type,
                    "proposed_value": link.proposed_value,
                    "reason": link.reason,
                    "confidence": link.confidence
                })
    
    return affected
```

### Query 4: Architecture Gap Detection

**Purpose**: Identify missing capabilities or bottlenecks in current architecture

**Query Pattern**:
```
INPUT: subsystem_id (optional, for specific area)
OUTPUT: List[gap] with gap_type and suggested_resolution
```

**Implementation**:
```python
def detect_architecture_gaps(store: ConceptGraphStore, subsystem_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Identify missing capabilities or bottlenecks in current architecture."""
    gaps = []
    
    # If subsystem specified, check that area
    if subsystem_id:
        subsystem = store.load_concept(subsystem_id)
        if not subsystem:
            gaps.append({"gap_type": "missing_subsystem", "suggested_resolution": "create_subsystem"})
            return gaps
        
        # Check for missing dependencies
        for link in subsystem.links:
            if link.link_type == "depends_on":
                if not store.load_concept(link.target_id):
                    gaps.append({
                        "gap_type": "missing_dependency",
                        "target_id": link.target_id,
                        "suggested_resolution": "create_or_reference_dependency"
                    })
        
        # Check for unvalidated capabilities
        if subsystem.node_type == "capability":
            has_validation = any(l.link_type == "validated_by" for l in subsystem.links)
            if not has_validation:
                gaps.append({
                    "gap_type": "unvalidated_capability",
                    "suggested_resolution": "add_validation_gate"
                })
    else:
        # Global check: find all capabilities without validation
        all_concepts = store.list_concepts()
        for concept in all_concepts:
            if concept.node_type == "capability":
                has_validation = any(l.link_type == "validated_by" for l in concept.links)
                if not has_validation:
                    gaps.append({
                        "gap_type": "unvalidated_capability",
                        "target_id": concept.id,
                        "target_name": concept.name,
                        "suggested_resolution": "add_validation_gate"
                    })
    
    return gaps
```

### Query 5: Governance Blocking

**Purpose**: Identify governance blocks preventing architecture changes

**Query Pattern**:
```
INPUT: subsystem_id, proposal_id (optional)
OUTPUT: List[block] with governance_id, reason, and override_path
```

**Implementation**:
```python
def detect_governance_blocks(store: ConceptGraphStore, subsystem_id: str, proposal_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Identify governance blocks preventing architecture changes."""
    blocks = []
    
    subsystem = store.load_concept(subsystem_id)
    if not subsystem:
        return []
    
    # Find governance policies
    for link in subsystem.links:
        if link.link_type == "governed_by":
            policy_id = link.target_id
            policy = store.load_concept(policy_id)
            if policy and policy.node_type == "policy":
                # Check if policy enforcement blocks change
                if link.enforcement_level == "hard":
                    blocks.append({
                        "governance_id": policy_id,
                        "policy_name": policy.name,
                        "reason": "hard_enforcement",
                        "override_path": "operator_approval_required"
                    })
    
    # If proposal specified, check for conflicting proposals
    if proposal_id:
        proposal = store.load_concept(proposal_id)
        if proposal and proposal.node_type == "proposal":
            for link in proposal.links:
                if link.link_type == "proposes_change_to":
                    target_id = link.target_id
                    # Check for conflicting proposals on same target
                    all_concepts = store.list_concepts()
                    for concept in all_concepts:
                        if concept.node_type == "proposal" and concept.id != proposal_id:
                            for prop_link in concept.links:
                                if prop_link.link_type == "proposes_change_to" and prop_link.target_id == target_id:
                                    # Check for conflicts
                                    if link.change_type != prop_link.change_type:
                                        blocks.append({
                                            "governance_id": concept.id,
                                            "reason": "conflicting_proposal",
                                            "override_path": "merge_or_prioritize_proposals"
                                        })
    
    return blocks
```

### Query 6: Trust Gate Validation

**Purpose**: Check if subsystem meets trust requirements

**Query Pattern**:
```
INPUT: subsystem_id, required_trust_level
OUTPUT: Dict{valid: bool, gate_id, reason, confidence}
```

**Implementation**:
```python
def check_trust_gate(store: ConceptGraphStore, subsystem_id: str, required_trust_level: float) -> Dict[str, Any]:
    """Check if subsystem meets trust requirements."""
    subsystem = store.load_concept(subsystem_id)
    if not subsystem:
        return {"valid": False, "reason": "subsystem_not_found"}
    
    # Find trust gates
    for link in subsystem.links:
        if link.link_type == "validated_by":
            gate_id = link.target_id
            gate = store.load_concept(gate_id)
            if gate and gate.node_type == "trust_gate":
                # Check confidence
                if link.confidence >= required_trust_level:
                    return {"valid": True, "gate_id": gate_id, "reason": "trust_met", "confidence": link.confidence}
                else:
                    return {"valid": False, "gate_id": gate_id, "reason": "trust_not_met", "confidence": link.confidence}
    
    # No validation found
    return {"valid": False, "reason": "no_validation_found"}
```

### Query 7: Contradiction Detection

**Purpose**: Find conflicting architecture elements

**Query Pattern**:
```
INPUT: subsystem_id
OUTPUT: List[contradiction] with conflict_type and resolution_suggestion
```

**Implementation**:
```python
def detect_contradictions(store: ConceptGraphStore, subsystem_id: str) -> List[Dict[str, Any]]:
    """Find conflicting architecture elements."""
    contradictions = []
    subsystem = store.load_concept(subsystem_id)
    if not subsystem:
        return []
    
    # Check for conflicts_with edges
    for link in subsystem.links:
        if link.link_type == "conflicts_with":
            target_id = link.target_id
            target = store.load_concept(target_id)
            if target:
                contradictions.append({
                    "target_id": target_id,
                    "target_name": target.name,
                    "conflict_type": link.conflict_type,
                    "reason": link.reason,
                    "confidence": link.confidence,
                    "resolution_suggestion": "resolve_conflict" if link.confidence >= 0.7 else "review_evidence"
                })
    
    return contradictions
```

---

## 5. GOVERNANCE BOUNDARY DESIGN

### Governance Principle: NO SILENT AUTONOMOUS MUTATION

| Principle | Implementation |
|-----------|----------------|
| **Operator Review Required** | All proposals require `required_governance: "operator_review"` |
| **No Hidden Mutation** | All changes stored as proposals, never applied silently |
| **Proposal → Review → Approval Flow** | Clear workflow: proposal (model/operator) → review → approval/rejection |
| **Architecture Trust Gates** | All architecture nodes require validation by `trust_gate` nodes |
| **Governance Status Tracking** | Every proposal tracks `governance_status: pending/approved/rejected` |

### Governance Flow: Proposal Pathway

```
┌─────────────────────────────────────────────────────────────┐
│                    PROPOSAL CREATION                        │
│  (model-assisted, not model-dependent)                     │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
                    ┌───────┴───────┐
                    │   Source      │
                    └───────┬───────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
  MODEL     OPERATOR    RESEARCH_FINDING
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    PROPOSAL CREATION (v94b)                 │
│  proposal_id: str                                          │
│  status: "pending"                                         │
│  required_governance: "operator_review"                    │
│  governance_status: "pending"                              │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
                    ┌───────┴───────┐
                    │   Governance  │
                    └───────┬───────┘
                            │
                    ┌───────┴───────┐
                    │   Decision    │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
         APPROVED                    REJECTED
              │                           │
              ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │ Apply to graph   │        │ Reject proposal  │
    │ Update subsystem │        │ Log decision     │
    │ Add validation   │        │ Record reason    │
    └──────────────────┘        └──────────────────┘
```

### Governance Node Types

#### A. Trust Gate Node (`trust_gate`)

| Field | Value | Description |
|-------|-------|-------------|
| `gate_type` | `proposition` | Validates proposition integrity |
| `gate_type` | `modification` | Validates modification safety |
| `gate_type` | `proposal` | Validates proposal governance |
| `gate_type` | `assimilation` | Validates knowledge assimilation |
| `approval_required` | `true` | Must have operator approval |
| `rejection_action` | `escalate` | Rejected proposals escalate to operator |

#### B. Policy Gate Node (`policy`)

| Field | Value | Description |
|-------|-------|-------------|
| `enforcement_level` | `hard` | Blocks change without approval |
| `enforcement_level` | `soft` | Warns but allows change |
| `enforcement_level` | `advisory` | Only suggests change |
| `violation_action` | `reject` | Rejects change on violation |
| `violation_action` | `escalate` | Escalates to operator |
| `violation_action` | `log_only` | Only logs violation |

#### C. Validation Gate Node (`validated_by`)

| Field | Value | Description |
|-------|-------|-------------|
| `status` | `valid` | Node passed validation |
| `status` | `invalid` | Node failed validation |
| `status` | `pending` | Validation in progress |
| `confidence` | `0.0-1.0` | Validation confidence threshold |

### Governance Enforcement Rules

| Rule | Implementation |
|------|----------------|
| **No Silent Mutation** | All changes stored as proposals, never auto-applied |
| **Operator Review** | All proposals require `governance_status: approved` |
| **Architecture Trust** | All subsystem nodes require `validated_by` edges |
| **Proposal Chain** | Proposals create `proposes_change_to` edges, not direct changes |
| **Rejection Path** | Rejected proposals recorded, never silently applied |
| **Override Path** | Operator can override hard governance with explicit approval |

### Governance Blocking Query (Complete Implementation)

```python
def check_governance_block(store: ConceptGraphStore, subsystem_id: str) -> Dict[str, Any]:
    """
    Check if a subsystem can be modified without governance blocks.
    
    Returns:
    {
        "can_modify": bool,
        "blocks": List[Dict],
        "required_approvals": List[str],
        "reason": str
    }
    """
    result = {
        "can_modify": True,
        "blocks": [],
        "required_approvals": [],
        "reason": "No governance blocks found"
    }
    
    subsystem = store.load_concept(subsystem_id)
    if not subsystem:
        result["can_modify"] = False
        result["reason"] = "Subsystem not found"
        return result
    
    # Check for hard governance policies
    for link in subsystem.links:
        if link.link_type == "governed_by":
            policy_id = link.target_id
            policy = store.load_concept(policy_id)
            if policy and policy.node_type == "policy":
                if link.enforcement_level == "hard":
                    result["blocks"].append({
                        "type": "hard_policy",
                        "policy_id": policy_id,
                        "policy_name": policy.name,
                        "reason": "Hard enforcement policy requires approval"
                    })
                    result["can_modify"] = False
                elif link.enforcement_level == "soft":
                    result["blocks"].append({
                        "type": "soft_policy",
                        "policy_id": policy_id,
                        "policy_name": policy.name,
                        "reason": "Soft policy warns but allows change"
                    })
    
    # Check for unapproved proposals
    if not result["can_modify"]:
        result["required_approvals"].append("operator_review")
        result["reason"] = "Governance blocks require operator approval"
    
    return result
```

---

## STOP — PHASE 2 COMPLETE

**Summary**:
- Reusable primitives: 80% (store, index, query patterns)
- Distinct primitives: 20% (validation, governance, trust gates)
- Node types: 9 (subsystem, capability, bottleneck, policy, workflow, dependency, proposal, research_finding, trust_gate)
- Edge types: 8 (depends_on, strengthens, replaces, bottleneck_for, governed_by, proposes_change_to, validated_by, conflicts_with)
- Queries: 7 (bottleneck_tracing, dependency_impact, proposal_impact, gap_detection, governance_blocking, trust_gate_validation, contradiction_detection)
- Governance: Proposals never silently applied, always require operator review

Ready for Phase 3: **Governed Self-Improvement Pathway**
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Wed 2026-04-08 13:24 GMT+2] Proceed to the next architecture-design step for v94 Internal Reasoning Graph.

The Phase 2 graph design direction is approved.

Before any coding, produce the missing operational design layer.

Output only:

1. graph mutation policy
 Define:
 
 - which node types may be added automatically
 - which edge types may be added automatically
 - which additions must always be operator-reviewed
 - which mutations are forbidden without explicit approval

2. governance boundary rules
 Define exact rules for:
 
 - "governed_by"
 - "validated_by"
 - "proposes_change_to"
 - "conflicts_with"
 including evidence and confidence requirements

3. base node / typed metadata recommendation
 Decide whether implementation should use:
 
 - one base node schema + typed metadata
 - or multiple explicit subclasses
 and explain why

4. recommended phased implementation order
 Provide:
 
 - Phase A
 - Phase B
 - Phase C
 with safest implementation order

5. stop

Do NOT implement code yet.
Design only.
assistant: # PHASE 3 — OPERATIONAL DESIGN LAYER FOR v94 INTERNAL REASONING GRAPH

## 1. GRAPH MUTATION POLICY

### Node Type Mutation Rules

| Node Type | Add Automatically | Edit Automatically | Delete Automatically | Requires Operator Review |
|-----------|-------------------|-------------------|---------------------|-------------------------|
| **subsystem** | ❌ No | ❌ No | ❌ No | ✅ Always |
| **capability** | ❌ No | ❌ No | ❌ No | ✅ Always |
| **bottleneck** | ✅ Yes (detection) | ❌ No | ❌ No | ✅ Always |
| **policy** | ❌ No | ❌ No | ❌ No | ✅ Always |
| **workflow** | ❌ No | ❌ No | ❌ No | ✅ Always |
| **dependency** | ❌ No | ❌ No | ❌ No | ✅ Always |
| **proposal** | ✅ Yes (model/operator/research) | ✅ Yes (status only) | ❌ No | ✅ Always |
| **research_finding** | ✅ Yes (research ingestion) | ❌ No | ❌ No | ✅ Always |
| **trust_gate** | ❌ No | ❌ No | ❌ No | ✅ Always |

### Edge Type Mutation Rules

| Edge Type | Add Automatically | Edit Automatically | Delete Automatically | Requires Operator Review |
|-----------|-------------------|-------------------|---------------------|-------------------------|
| **depends_on** | ✅ Yes (detection) | ❌ No | ❌ No | ✅ Always |
| **strengthens** | ✅ Yes (analysis) | ❌ No | ❌ No | ✅ Always |
| **replaces** | ✅ Yes (version tracking) | ❌ No | ❌ No | ✅ Always |
| **bottleneck_for** | ✅ Yes (bottleneck detection) | ❌ No | ❌ No | ✅ Always |
| **governed_by** | ✅ Yes (policy application) | ❌ No | ❌ No | ✅ Always |
| **proposes_change_to** | ✅ Yes (proposal creation) | ✅ Yes (change_type only) | ❌ No | ✅ Always |
| **validated_by** | ✅ Yes (validation result) | ❌ No | ❌ No | ✅ Always |
| **conflicts_with** | ✅ Yes (contradiction detection) | ❌ No | ❌ No | ✅ Always |

### Mutation Categories

#### ALLOWED AUTOMATICALLY (Detection/Auto-Generated)

| Category | Examples | Trust Threshold |
|----------|----------|-----------------|
| **Bottleneck Detection** | Auto-detect missing dependencies, unvalidated capabilities | Confidence ≥ 0.8 |
| **Dependency Detection** | Identify missing subsystems, inferred requirements | Confidence ≥ 0.7 |
| **Edge Inference** | Derive `strengthens`, `conflicts_with` from analysis | Confidence ≥ 0.6 |
| **Proposal Creation** | Model-generated proposals with `status: "pending"` | Confidence ≥ 0.5 |
| **Research Ingestion** | External research findings with `status: "pending"` | Confidence ≥ 0.6 |

#### ALLOWED AUTOMATICALLY (Status Updates Only)

| Category | Examples | Trust Threshold |
|----------|----------|-----------------|
| **Proposal Status** | Update `governance_status` based on review | Operator approval required |
| **Validation Status** | Update `validated_by.status` based on gate results | Gate confidence ≥ 0.5 |
| **Research Validation** | Update `validated_by` based on validation results | Gate confidence ≥ 0.7 |

#### ALWAYS REQUIRES OPERATOR REVIEW

| Mutation Type | Reason |
|--------------|--------|
| **Any node creation** | Architecture mutation requires operator approval |
| **Any node deletion** |Irreversible, requires operator confirmation |
| **Any node modification** | Changes structure, requires operator approval |
| **Any edge creation** | Relationships are significant, requires operator approval |
| **Any edge deletion** | Removes relationships, requires operator approval |
| **Governing policy change** | Changes rules, requires operator approval |
| **Trust gate modification** | Changes validation requirements, requires operator approval |

#### FORBIDDEN WITHOUT EXPLICIT APPROVAL

| Mutation Type | Reason |
|--------------|--------|
| **Silent mutation** | Never allowed — no automatic application |
| **Self-application** | Never allowed — always requires operator review |
| **Proposal self-approval** | Never allowed — requires external governance |
| **Auto-validated proposal** | Never allowed — requires operator validation |
| **Hidden proposal creation** | Never allowed — all proposals visible |

---

## 2. GOVERNANCE BOUNDARY RULES

### Rule Set: `governed_by`

| Rule | Requirement | Evidence | Confidence |
|------|-------------|----------|------------|
| **Creation** | Subsystem must have `governed_by` edge to policy | Subsystem definition, policy scope | ≥ 0.7 |
| **Modification** | Cannot modify governed subsystem without policy compliance | Policy enforcement level, violation action | ≥ 0.8 |
| **Validation** | Must check policy before any mutation | Policy enforcement_level, governance_status | ≥ 0.7 |
| **Override** | Operator can override with explicit approval | Operator signature, override_reason | 1.0 (explicit) |

**Evidence Requirements**:
- Policy scope must include subsystem_id
- Enforcement level must be documented
- Governance_status must be tracked

**Confidence Requirements**:
- Base: 0.7 (policy applied)
- Modified: 0.8 (enforcement verified)
- Overridden: 1.0 (explicit approval)

### Rule Set: `validated_by`

| Rule | Requirement | Evidence | Confidence |
|------|-------------|----------|------------|
| **Creation** | Subsystem/capability must have `validated_by` edge | Validation subsystem output, gate result | ≥ 0.5 |
| **Re-validation** | Must re-validate after any change | Re-validation trigger, new validation result | ≥ 0.7 |
| **Invalid State** | Cannot act on invalid nodes without override | Invalid reason, override_reason | 1.0 (explicit override) |
| **Gate Requirements** | Trust gate must have approval_required=true | Gate type, approval requirement | ≥ 0.9 |

**Evidence Requirements**:
- Validation subsystem ID
- Validation result (valid/invalid/pending)
- Validation timestamp

**Confidence Requirements**:
- Base: 0.5 (initial validation)
- Re-validation: 0.7 (after change)
- Override: 1.0 (explicit approval)

### Rule Set: `proposes_change_to`

| Rule | Requirement | Evidence | Confidence |
|------|-------------|----------|------------|
| **Creation** | Proposal must have `proposes_change_to` edges | Proposal content, proposed changes | ≥ 0.6 |
| **Multiple Targets** | One proposal can propose changes to multiple nodes | Proposal scope, target list | ≥ 0.5 |
| **Change Type** | Must specify `change_type` (add/modify/remove/replace) | Proposed change details | ≥ 0.8 |
| **Conflict Detection** | Must detect if another proposal targets same node | Proposal comparison, conflict analysis | ≥ 0.7 |

**Evidence Requirements**:
- Proposal ID
- Target node IDs
- Change types for each target
- Reason for each proposed change

**Confidence Requirements**:
- Base: 0.6 (proposal created)
- Change Type: 0.8 (clear change specification)
- Conflict Detection: 0.7 (analysis performed)

### Rule Set: `conflicts_with`

| Rule | Requirement | Evidence | Confidence |
|------|-------------|----------|------------|
| **Creation** | Must detect conflict between nodes | Node comparison, contradiction analysis | ≥ 0.7 |
| **Conflict Type** | Must specify conflict_type (contradiction/redundancy/incompatibility) | Conflict analysis, reason | ≥ 0.8 |
| **Resolution** | Must provide resolution suggestion | Resolution reasoning | ≥ 0.6 |
| **Auto-Detection** | Can be auto-detected from analysis | Analysis tool output | ≥ 0.7 |

**Evidence Requirements**:
- Conflicting node IDs
- Conflict type
- Conflict reason
- Resolution suggestion

**Confidence Requirements**:
- Base: 0.7 (conflict detected)
- Conflict Type: 0.8 (clear specification)
- Resolution: 0.6 (suggestion provided)

---

## 3. BASE NODE / TYPED METADATA RECOMMENDATION

### Recommended Approach: **One Base Node Schema + Typed Metadata**

**Rationale**:

1. **Flexibility for Growth**
   - v94b may expand to v95, v96 with new node types
   - Single schema avoids breaking changes when adding new types
   - Type-specific validation via metadata, not class structure

2. **Consistency with Existing Infrastructure**
   - `Concept` class already supports `type` and `metadata` fields
   - Reuses `concept_graph` storage infrastructure
   - No migration required for schema changes

3. **Query Simplicity**
   - Single table/query pattern for all node types
   - Filter by `node_type` metadata field
   - Easy to add new node types without schema updates

4. **Governance Integration**
   - Governance rules apply uniformly across all node types
   - Validation logic can be type-based, not class-based
   - Easier to audit and debug

5. **Evidence Handling**
   - Evidence links work uniformly across all node types
   - No special handling needed for different node types
   - Consistent provenance tracking

### Why NOT Multiple Explicit Subclasses

1. **Inheritance Complexity**
   - Would require class hierarchy for 9 node types
   - Each new type requires new class definition
   - More difficult to maintain and extend

2. **Storage Incompatibility**
   - `ConceptGraphStore` expects `Concept` class
   - Subclass instances would require serialization changes
   - Migration complexity for version upgrades

3. **Governance Fragmentation**
   - Governance rules would need to handle multiple classes
   - More difficult to enforce consistent validation
   - Audit trails would be fragmented

4. **Query Complexity**
   - Different query patterns for each subclass
   - More difficult to write generic reasoning queries
   - Harder to implement graph traversal

### Implementation Pattern

```python
# Base Node (extends concept_graph.models.Concept)
class InternalReasoningNode(Concept):
    """Internal reasoning graph node.
    
    Extends Concept with type-specific metadata.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Node type specific logic via metadata
        self.node_type = self.metadata.get("node_type", "subsystem")
        self.node_subtype = self.metadata.get("node_subtype")
    
    @classmethod
    def create_subsystem(cls, id: str, name: str, description: str) -> "InternalReasoningNode":
        return cls(
            id=id,
            name=name,
            type="concept",
            description=description,
            metadata={"node_type": "subsystem", "status": "active"}
        )
    
    @classmethod
    def create_capability(cls, id: str, name: str, description: str, node_subtype: str) -> "InternalReasoningNode":
        return cls(
            id=id,
            name=name,
            type="concept",
            description=description,
            metadata={"node_type": "capability", "node_subtype": node_subtype, "status": "active"}
        )

# Validation by node type
def validate_node_type(node: InternalReasoningNode) -> Tuple[bool, str]:
    """Validate node based on type."""
    node_type = node.metadata.get("node_type")
    
    if node_type == "subsystem":
        return validate_subsystem(node)
    elif node_type == "capability":
        return validate_capability(node)
    elif node_type == "bottleneck":
        return validate_bottleneck(node)
    # ... other types
    
    return False, f"Unknown node_type: {node_type}"
```

---

## 4. RECOMMENDED PHASED IMPLEMENTATION ORDER

### Phase A: Foundation (Weeks 1-2)

**Goal**: Basic graph structure and storage

**Modules**:
1. `weslr/internal_reasoning_graph/__init__.py` — Exports
2. `weslr/internal_reasoning_graph/models.py` — Node schema + validation
3. `weslr/internal_reasoning_graph/store.py` — Persistence layer
4. `weslr/internal_reasoning_graph/test_models.py` — Model tests
5. `weslr/internal_reasoning_graph/test_store.py` — Store tests

**Deliverables**:
- Base node schema with typed metadata
- Store layer with save/load/merge
- Basic validation by node type
- 100% test coverage for models and store

### Phase B: Reasoning Queries (Weeks 3-4)

**Goal**: Reasoning query engine

**Modules**:
1. `weslr/internal_reasoning_graph/query.py` — Query engine
2. `weslr/internal_reasoning_graph/reasoning_engine.py` — Main engine
3. `weslr/internal_reasoning_graph/test_query.py` — Query tests
4. `weslr/internal_reasoning_graph/test_reasoning.py` — Reasoning tests

**Deliverables**:
- All 7 reasoning queries implemented
- Query execution tests
- Governance blocking tests
- 100% test coverage

### Phase C: Governance Integration (Weeks 5-6)

**Goal**: Governance rules and integration

**Modules**:
1. `weslr/internal_reasoning_graph/governance.py` — Governance engine
2. `weslr/internal_reasoning_graph/proposal.py` — Proposal workflow
3. `weslr/internal_reasoning_graph/test_governance.py` — Governance tests
4. `weslr/internal_reasoning_graph/test_proposal.py` — Proposal tests
5. `weslr/internal_reasoning_graph/integration.py` — Integration hooks
6. `weslr/internal_reasoning_graph/test_integration.py` — Integration tests

**Deliverables**:
- Governance rules for all 4 edge types
- Proposal workflow with operator review
- Integration with concept_graph and architecture_memory
- End-to-end governance tests

### Phase D: Documentation + Sealing (Week 7)

**Goal**: Complete architecture documentation

**Deliverables**:
- ARCHITECTURE.md update (v94b section)
- RELEASES.md update (v94b release notes)
- OPERATOR_STATE.json update (v94b status)
- Test summary: 350+ tests, 100% pass

**Total Implementation Time**: ~6 weeks  
**Total Tests**: 350+ tests  
**Total New Code**: ~1,500 lines (source + tests)

---

## STOP — PHASE 3 COMPLETE

**Summary**:
- Mutation policy: Detection auto-generated, mutation always requires operator review
- Governance rules: 4 edge types with evidence and confidence requirements
- Base schema: One base node + typed metadata (flexible, maintainable, consistent)
- Implementation order: A (foundation) → B (queries) → C (governance) → D (docs)

Ready for Phase 4: **Implementation** (pending operator approval)
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Wed 2026-04-08 13:27 GMT+2] Proceed with v94b Phase A — Internal Reasoning Graph Foundation

Use the approved v94b architecture design as baseline.

Important clarifications to preserve:

1. automatic candidate detection/proposal generation may exist
2. automatic accepted architecture mutation is NOT allowed
3. "replaces" and "conflicts_with" are high-risk edge types and must remain governance-sensitive

Implement Phase A only.

Approved Phase A scope:

- "weslr/internal_reasoning_graph/__init__.py"
- "weslr/internal_reasoning_graph/models.py"
- "weslr/internal_reasoning_graph/store.py"
- "weslr/internal_reasoning_graph/test_models.py"
- "weslr/internal_reasoning_graph/test_store.py"

Phase A goals:

- base node schema + typed metadata
- edge schema
- validation rules
- persistence layer
- no query engine yet
- no governance workflow engine yet
- no integration hooks yet
- no architecture/operator/release file changes in this coding step

Constraints:

- additive only
- no hidden self-application
- no accepted graph mutation without governance
- no TIA/C#
- no orchestration
- no backend/service/UI

After implementation, output only:

1. exact files changed
2. exact tests run/results
3. exact full commit hash
4. git truth
5. seal status
assistant: I'll implement Phase A — Internal Reasoning Graph Foundation. Let me start by creating the directory structure and implementing the required files.
assistant: Now let me create the test files:
assistant: Now let me run the tests to verify the implementation:
assistant: Let me fix the import paths in the test files:
assistant: Now run the tests again:
assistant: I see there's a naming issue. Let me fix the factory method names and check the test file issues:
assistant: Now let me update the test files to use the correct method names:
assistant: Now let me run the tests again:
assistant: Let me fix the remaining factory method calls:
assistant: Now fix the trust gate low confidence test:
