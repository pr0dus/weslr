# WESLR Artifact Writer Boundary Capability Preservation Addendum V1

## 1. Owner concern

The artifact writer boundary must not weaken WESLR.

It must not accidentally reduce:
- artifact quality
- artifact quantity
- project complexity
- scaffold usefulness
- future coding capacity
- public-facing artifact capability
- ability to generate docs, scripts, configs, tests, UI files, dashboards, reports, project structures

## 2. Core clarification

The artifact writer boundary separates:

`generation capability`
from
`filesystem authority`

WESLR may still generate large, useful, high-quality scaffold packets.

The boundary only decides whether generated content may be written to disk, where, under what approval, and with what safety controls.

## 3. Capability must remain broad

WESLR should be allowed to generate planned artifact packets for:

- Python modules
- Python tests
- Markdown docs
- architecture reports
- YAML configs
- JSON schemas
- SQLite placeholders
- HTML/CSS/JS static previews
- dashboard skeletons
- CLI skeletons
- validation plans
- project manifests
- handover files
- product docs
- legal/support docs
- public website sections
- artifact bundles later

The writer boundary must not shrink these categories.

## 4. Quantity doctrine

Do not define tiny fixed limits as permanent rules.

Quantity should be controlled by policy fields, not hard-coded weakness.

Use adjustable constraints:
- max files per packet
- max bytes per file
- max total bytes
- max directory depth
- max executable files
- max overwrite count
- max generated-only edits
- approval level
- risk class
- sandbox status

The boundary may say:
“this large write requires approval/sandbox/chunking,”
not:
“WESLR cannot create large artifacts.”

## 5. Quality doctrine

The boundary should improve quality by requiring:
- file manifest lineage
- scaffold lineage
- purpose per file
- validation marker
- overwrite policy
- owner approval marker
- path safety
- secret/private scan
- future validation report
- provenance metadata

It should not lower quality by forcing empty placeholders when richer safe content is available.

## 6. How-to preservation

The boundary should preserve the ability to produce useful implementation guidance.

Allowed:
- explain how the artifact should be created
- prepare exact file paths
- prepare file content packets
- prepare validation steps
- prepare dependency recommendations as review items
- prepare next-step instructions
- prepare export bundles later

Blocked only:
- executing unsafe actions
- installing dependencies without authority
- deploying/publishing
- writing protected paths
- writing secrets/private data
- covert/surveillance/diagnosis/deployment misuse

## 7. Capability classes

Define capability classes separately from authority levels:

Capability classes:
- `plan_artifact`
- `generate_content_packet`
- `prepare_file_manifest`
- `prepare_scaffold`
- `prepare_validation_plan`
- `prepare_patch_plan`
- `prepare_export_bundle`
- `write_sandbox_files`
- `edit_generated_files`
- `validate_artifact`
- `package_artifact`
- `deploy_or_publish`

Authority levels then control which class can execute.

This prevents confusing “can generate” with “may write now.”

## 8. Boundary decisions should channel, not suppress

For risky requests, boundary should prefer safe channeling:

Examples:
- Protected runtime edit → block direct write, offer patch proposal/diff plan.
- `.env` secret file → block secret write, offer `config.example.yaml`.
- Deployment file → block deployment authority, offer local preview manifest.
- Medical software logic → block diagnosis/treatment logic, offer boundary docs and validation plan.
- WiFi/RF sensing → block covert tracking, allow consent-based local research scaffold.
- Large project → require chunking/owner approval, not permanent refusal.

## 9. Sandbox expansion doctrine

Sandbox capability should be expandable.

The first implementation may be metadata-only.

Future implementations may allow:
- create-only sandbox writes
- generated-only edits
- owner-approved patches
- validation runs
- export bundles

The design must not permanently block this progression.

## 10. Strong artifact writer description

Canonical description:

“WESLR’s artifact writer is a governed artifact materialization layer. It turns validated scaffold packets into files only after path, authority, privacy, overwrite, and provenance checks. It preserves broad generation capability while preventing hidden writes, protected-path edits, secrets/private data leakage, destructive operations, runtime mutation, deployment, and unauthorized publication.”

## 11. Implementation requirements for next lane

`IMPLEMENT_WESLR_ARTIFACT_WRITER_BOUNDARY_V1` must be metadata-only evaluator first, but it must include fields that preserve future capacity:

- `capability_class`
- `requested_file_count`
- `requested_total_size_estimate`
- `chunking_required`
- `quality_preservation_notes`
- `safe_alternative_mode`
- `can_generate_packet`
- `can_write_if_authorized`
- `blocked_action_only`
- `capability_not_denied`
- `future_authority_path`

This way, when something is blocked, the decision explains:
- what is blocked
- why
- what remains allowed
- what authority would be needed later

## 12. Examples

1. Large scaffold packet
- decision: not denied
- chunking required
- sandbox/owner approval needed
- capability preserved

2. Protected runtime edit
- decision: direct write blocked
- patch proposal allowed
- future owner/operator approval required

3. Static website preview
- decision: content generation allowed
- sandbox create allowed later
- deployment blocked

4. WiFi/RF self-care project
- decision: consent-based docs/config/tests allowed
- covert tracking blocked
- diagnosis/treatment blocked
- local-first scaffold preserved

5. Medical software pathway
- decision: docs/regulatory/safety validation scaffold allowed
- clinical/diagnosis logic blocked unless regulated pathway

6. `.env` request
- decision: secret file blocked
- `config.example.yaml` allowed

## 13. Anti-drift rule

Future implementation must not turn safety into broad refusal.

Blocked actions must be narrow and named.

Every blocked decision should preserve a safe alternative if one exists.

Boundary output should distinguish:
- `artifact_generation_allowed`
- `file_write_allowed`
- `file_write_blocked_reason`
- `safe_alternative_available`
- `required_authority_for_next_step`

## 14. Final judgment

`artifact_writer_boundary_capability_preservation_ready_for_metadata_evaluator_implementation`
