# WESLR Entity-Scoped Memory Namespaces — Model & Implementation

**Canonical as of:** commit `TBD` (2026-05-07)

---

## SECTION 1 — FILES CREATED/MODIFIED

| File | Status | Purpose |
|---|---|---|
| `weslr/entity_memory.py` | New (~570 lines) | Entity-scoped memory namespaces: `MemoryRecord`, `EntityRelationship`, entity types, access levels, relationship types, role types, namespace paths, memory CRUD, relationship CRUD, access control, scope resolution, bounded summaries, `format_memory_response()` |
| `weslr/user_profile.py` | Modified | Added `MembershipClaim` dataclass, `memberships` field on `UserProfile`, membership helpers (`add_membership`, `list_memberships`, `summarize_memberships`, `get_verified_memberships`), save/load roundtrip for memberships |
| `weslr/meaning_state_context.py` | Modified | Added entity memory fields to `MeaningStateContext` dataclass; replaced memory/continuity section with entity-scoped resolution: resolves scopes from `channel_verified` + verified memberships + primary projects, loads scoped memories, falls back to legacy continuity anchors then global memory files |
| `weslr/test_entity_memory.py` | New (~520 lines) | 24 tests: ID stability, path construction, memory roundtrip, summarize, access control (unknown/profile_only/channel_verified/public), project/person separation, role evidence requirements, CEO access, multi-membership, namespace listing, scope resolution, profile membership roundtrip, no-LLM check, bounded response format, regressions |
| `weslr/commands/entity_memory_commands.py` | New (~310 lines) | CLI: `add`, `list`, `namespaces`, `summarize`, `relate`, `relationships`, `scopes` with `--base-path` override |

---

## SECTION 2 — ENTITY MEMORY MODEL

### Entity Types

- `person` — individual user/person identity
- `family` — family/household unit
- `household` — co-located household
- `company` — commercial entity
- `institution` — institutional/organizational entity
- `team` — team/workgroup
- `department` — department within company/institution
- `project` — project-scoped memory space
- `system` — WESLR system-level memory
- `unknown` — fallback for unidentified entities

### Access Levels

| Level | Description |
|---|---|
| `private` | Only the owning person (requires `channel_verified`) |
| `shared` | Group/institutional members (requires verified relationship) |
| `representative` | Verified representative with specific scope |
| `public` | Anyone, no identity required |
| `operator_only` | Operator only (requires `channel_verified`) |
| `role_restricted` | Role-dependent access, requires verified role |

### Namespace Paths

```
~/.weslr/memory/entities/<entity_type>/<entity_id>/memory.jsonl
~/.weslr/memory/entities/_relationships/relationships.jsonl
```

**Examples:**
```
memory/entities/person/user_abc123/memory.jsonl
memory/entities/family/fam_smith/memory.jsonl
memory/entities/household/household_home/memory.jsonl
memory/entities/company/acme_gmbh/memory.jsonl
memory/entities/institution/university_x/memory.jsonl
memory/entities/team/engineering_team/memory.jsonl
memory/entities/department/research_department/memory.jsonl
memory/entities/project/weslr/memory.jsonl
```

### Memory Record Schema

Each record in `memory.jsonl` (one JSON object per line):

```json
{
  "memory_id": "adb386a276914768",
  "timestamp": "2026-05-07T13:31:00.000000+00:00",
  "entity_type": "project",
  "entity_id": "project-weslr",
  "scope": "default",
  "access_level": "private",
  "source": "operator",
  "summary": "Worked on entity-scoped memory namespaces",
  "details": null,
  "tags": ["setup", "binding"],
  "confidence": 0.8,
  "verified": true,
  "created_by": "operator",
  "related_person_ids": [],
  "related_group_ids": [],
  "related_entity_ids": [],
  "project_ids": [],
  "provenance": "explicit",
  "retention_policy": "default",
  "memory_version": 1
}
```

---

## SECTION 3 — RELATIONSHIP / ROLE MODEL

### Relationship Types

- `member_of`
- `works_for`
- `owns`
- `leads`
- `represents`
- `manages`
- `belongs_to_household`
- `part_of_family`
- `contributes_to_project`
- `owns_project`
- `department_of`
- `team_of`
- `affiliated_with`
- `verified_representative_of`
- `unknown`

### Role Types

- `owner`
- `ceo`
- `operator`
- `admin`
- `member`
- `employee`
- `representative`
- `contractor`
- `advisor`
- `viewer`
- `guardian`
- `parent`
- `child`
- `spouse`
- `sibling`
- `household_member`
- `project_owner`
- `project_contributor`
- `unknown`

### Evidence Fields (per Relationship)

```json
{
  "relationship_id": "9e1617da1acd4720",
  "person_id": "alice",
  "entity_type": "company",
  "entity_id": "acme_gmbh",
  "entity_display_name": "ACME GmbH",
  "role": "ceo",
  "relationship_type": "leads",
  "strength": "strong",
  "verified": true,
  "confidence": 0.85,
  "source": "explicit_operator",
  "created_at": "2026-05-07T13:31:00.000000+00:00",
  "updated_at": "2026-05-07T13:31:00.000000+00:00",
  "evidence": [],
  "limitations": []
}
```

### Many-to-Many Support

A person can belong to multiple entities simultaneously:
- A person can be part of a family
- A person can work at a company
- A person can own or be CEO of a company
- A person can represent an institution
- A person can belong to a team or department
- A person can work on multiple projects

Each membership is stored as a separate `EntityRelationship` record. Scopes are resolved independently; there is no automatic scope merging.

---

## SECTION 4 — ACCESS CONTROL

### Access Matrix

| Identity Status | PRIVATE | SHARED | OPERATOR_ONLY | PUBLIC |
|---|---|---|---|---|
| `unknown` | ❌ | ❌ | ❌ | ✅ |
| `profile_only` / `onboarded_unverified` | ❌ | ❌ requires verified role | ❌ | ✅ |
| `channel_verified` | ✅ own person memory | ❌ requires verified relationship | N/A | ✅ |

### Group/Institution Safeguards

- Company/family memory requires verified relationship (`verified=True`) to access `SHARED` level
- CEO/owner role must be explicit and evidence-scored
- Unverified membership claims never grant memory access automatically
- A person can be in many groups but each group memory requires its own verified relationship
- No silent auto-binding of identity or memory access

### Role Evidence Requirements

| Role | Can Access SHARED Memory? | Requirement |
|---|---|---|
| Verified CEO/owner | ✅ | `verified=True`, `confidence >= 0.85` |
| Verified representative | ✅ | `verified=True`, evidence of authority |
| Verified member/employee | ⚠️ | Only with explicit access grant |
| Unverified membership claim | ❌ | Cannot access group memory |
| Text self-claim | ❌ | Never sufficient for access |

---

## SECTION 5 — MEANING STATE INTEGRATION

### Scope Resolution (`resolve_memory_scopes`)

```
channel_verified  → personal scope + project scopes + verified entity scopes
onboarded_unverified → project scopes + verified entity scopes (no personal)
unknown  → only PUBLIC scopes
```

### Memory Loading Order

1. **Entity-scoped memories** — loaded from all resolved scopes (person, project, company, family, etc.)
2. **Continuity anchors fallback** — `l2_session.continuity.continuity_anchors`
3. **Global memory file fallback** — structured summary from latest `memory/YYYY-MM-DD.md` file

### New MeaningStateContext Fields

```python
memory_scope_used: Optional[str]       # e.g. "personal", "project_weslr"
entity_memory_available: Optional[str]  # e.g. "personal memory for alice"
entity_relationships_used: list[str]   # e.g. ["company/acme_gmbh (ceo)"]
memory_access_limitations: list[str]    # any access restrictions applied
```

---

## SECTION 6 — RESPONSE BEHAVIOR

### Bounded Memory Response Format

`format_memory_response()` produces user-facing memory summaries:

```
From Alice's personal memory: I recall: setup, binding, testing [3 memory records, 2 verified]
```

```
I have no stored memories for project weslr yet.
```

**No raw file dumps.** Bounded summaries only with:
- Record count
- Verified count
- Tag/topics list (max 5 tags)
- Confidence band indicators

### CLI Scope Display

```
=== Memory scopes for identity_status=channel_verified, user_id=alice ===
  personal: person/person-alice [private]
  project_weslr: project/project-weslr [operator_only]
  company_acme_gmbh: company/acme_gmbh [shared]

=== Memory scopes for identity_status=onboarded_unverified ===
  (personal scope not available)
  project_weslr: project/project-weslr [operator_only]
  company_acme_gmbh: company/acme_gmbh [shared]
```

---

## SECTION 7 — CLI COMMANDS

```
python3 -m weslr.commands.entity_memory_commands add \
  --entity-type project --entity-id weslr \
  --summary "Worked on entity-scoped memory namespaces" \
  --tags setup,binding --confidence 0.8 --verified \
  --base-path /tmp/...

python3 -m weslr.commands.entity_memory_commands list \
  --entity-type project --entity-id weslr --base-path /tmp/...

python3 -m weslr.commands.entity_memory_commands namespaces \
  --base-path /tmp/...

python3 -m weslr.commands.entity_memory_commands relate \
  --person-id alice --entity-type company --entity-id acme_gmbh \
  --role ceo --relationship-type leads --verified --confidence 0.85 \
  --base-path /tmp/...

python3 -m weslr.commands.entity_memory_commands relationships \
  --person-id alice --base-path /tmp/...

python3 -m weslr.commands.entity_memory_commands scopes \
  --identity-status channel_verified --user-id alice \
  --primary-projects weslr --base-path /tmp/...
```

---

## SECTION 8 — TEST RESULTS

```
=== ENTITY MEMORY NAMESPACE TESTS ===
  PASS  entity_id generation stable
  PASS  memory path construction
  PASS  append/load memory roundtrip
  PASS  summarize produces structured summary
  PASS  unknown cannot access private person memory
  PASS  profile-only cannot access private person memory
  PASS  channel_verified user can access own person memory
  PASS  public access level always allowed
  PASS  project memory separate from person memory
  PASS  unverified membership/role does not grant shared memory
  PASS  verified CEO role can access company memory
  PASS  person can have multiple memberships without scope collision
  PASS  memory namespaces list correctly
  PASS  resolve_memory_scopes includes personal + project + company for channel_verified
  PASS  profile_only has no personal scope, has project + verified family
  PASS  profile memberships survive save/load roundtrip
  PASS  entity_memory.py has no LLM imports
  PASS  format_memory_response is bounded, no raw dump
  PASS  user profile tests pass (14/14)
  PASS  channel identity tests pass (16/16)
  PASS  meaning vector tests pass (5/5)
  PASS  weight refinement tests pass (6/6)
  PASS  local bridge tests pass (6/6)
  PASS  voice pipeline tests pass (13/13)

Entity memory tests: 24 passed, 0 failed
```

---

## SECTION 9 — LIMITATIONS

- **Relationship depth learning** — future work (learned from conversation, not just explicit claims)
- **Role verification for groups/institutions** — still requires explicit operator command
- **Migration from old global memories** — future work (existing `memory/` files remain as-is; new entity-scoped memory is additive)
- **STT/voiceprint identity** — future work
- **Federated identity** — cross-device/group shared memory is future work
- **Per-user memory learned from interaction** — future work

---

## SECTION 10 — DOCTRINE

**WESLR memory is not only per-user.**

WESLR memory is entity-scoped: person, family, household, company, institution, team, department, project.

- A verified person may access their own memory.
- A person may belong to families, companies, institutions, teams, departments, and projects.
- A representative may access group memory only with verified role evidence.
- A CEO/owner role must be explicit and evidence-scored.
- Shared memory must never leak across entities silently.
