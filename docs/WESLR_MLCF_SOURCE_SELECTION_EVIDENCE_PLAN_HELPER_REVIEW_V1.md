# WESLR MLCF Source Selection and Evidence Acquisition Plan Helper V1 — Review

## Implementation summary
The helper is a deterministic, metadata-only source-plan builder. It selects source classes, authority levels, evidence roles, and safe next steps before any source access, browsing, or ingestion.

It gives WESLR a governed way to decide where to look first without fetching anything.

## API summary
Reviewed public APIs:
- `allowed_mlcf_source_classes_v1()`
- `allowed_mlcf_source_authority_levels_v1()`
- `allowed_mlcf_evidence_roles_v1()`
- `allowed_mlcf_source_selection_next_steps_v1()`
- `build_mlcf_source_selection_evidence_plan_v1(...)`
- `validate_mlcf_source_selection_evidence_plan_v1(...)`
- `summarize_mlcf_source_selection_evidence_plan_v1(...)`
- `to_mlcf_source_selection_evidence_plan_json_safe_v1(...)`
- `build_initial_mlcf_source_selection_evidence_plan_examples_v1()`

## Canonical example assessment
Reviewed examples:
1. `rf_material_floorplan_source_plan`
   - valid
   - recommends authoritative public sources plus GitHub as implementation evidence
   - next safe step: `prepare_authorized_ingestion_boundary`
2. `github_only_source_plan_blocked_as_insufficient`
   - valid
   - GitHub is useful, but not enough on its own
   - next safe step: `needs_repair`
3. `private_hidden_source_plan_blocked`
   - valid
   - blocked-source posture is preserved
   - next safe step: `blocked_by_safety`

## RF/material/floor-plan source-plan assessment
The RF/material/floor-plan plan correctly recommends:
- official standards
- government/agency data
- research papers
- datasets
- GitHub repositories
- public lab or university artifacts
- official vendor documentation

It also assigns expected evidence roles such as standards, measurement data, implementation references, prior art, counterexample sources, and replication targets.

## GitHub-only insufficiency assessment
The GitHub-heavy example is handled safely.
GitHub is explicitly treated as implementation evidence, not authoritative science evidence by itself.
The plan routes to `needs_repair` and identifies missing official standards, papers, datasets, and replication targets.

## Private / hidden / protected source blocking assessment
The blocked example correctly refuses closed-access planning.
It keeps the next safe step at `blocked_by_safety` and preserves a metadata-only posture.

## Source-class authority assessment
The helper cleanly separates:
- official / primary sources
- public / secondary sources
- implementation evidence
- community signal
- owner context
- internal context
- blocked sources

## Evidence-role assessment
The helper assigns evidence roles appropriately, including:
- definition_or_standard
- measurement_data
- implementation_reference
- prior_art
- candidate_signal
- counterexample_source
- replication_target
- constraint_source
- domain_context
- safety_boundary_context
- not_authoritative_context

## Authority / safety assessment
Reviewed fail-closed coverage includes:
- invalid source class / authority level / evidence role / next safe step
- empty science direction
- empty recommended source classes
- official claim without official source class
- GitHub-only official-evidence claim
- source ingestion authorization
- provider / tool / web / GitHub authority
- `.weslr` implication
- memory / project mutation
- behavior-pack promotion authority
- public claim / proof / discovery / AGI / benchmark authority
- cross-user leakage
- hidden / private / protected markers
- non-JSON-safe output handling

Assessment: metadata-only and bounded.

## Validation results
Passed:
- `python3 -m py_compile weslr/mlcf_source_selection_evidence_plan.py weslr/tests/test_mlcf_source_selection_evidence_plan_v1.py`
- `python3 -m pytest weslr/tests/test_mlcf_source_selection_evidence_plan_v1.py` (`49 passed`)
- `git diff --check`
- `python3 weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`

## Protected-file status
Unchanged:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`

## Ready for first controlled source-plan sample?
Yes.

## Recommended next lane
`RUN_WESLR_FIRST_MLCF_SOURCE_SELECTION_EVIDENCE_PLAN_SAMPLE_V1`

## Review conclusion
The helper is valid, bounded, metadata-only, and ready for the first controlled source-plan sample run.
