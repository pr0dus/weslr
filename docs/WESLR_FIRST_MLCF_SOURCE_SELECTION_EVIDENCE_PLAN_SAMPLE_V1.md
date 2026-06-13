# WESLR First MLCF Source Selection Evidence Plan Sample V1

## 1. Sample purpose
Run one metadata-only source-selection sample to decide where evidence should come from before any source access or ingestion.

## 2. Exact science direction input
```text
Science direction: Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.

Domain focus:

- RF / WiFi sensing
- indoor propagation and multipath
- material and surface scattering
- floor-plan constrained spatial inference
- sparse motion-sensitive signal maps

Owner intent:
WESLR should identify official and public evidence classes that would be needed before any stronger candidate method, probe, or experiment is trusted. GitHub may be useful for implementation references, but not enough as authoritative scientific evidence by itself.
```

## 3. Helper used
- build_mlcf_source_selection_evidence_plan_v1
- validate_mlcf_source_selection_evidence_plan_v1
- summarize_mlcf_source_selection_evidence_plan_v1
- to_mlcf_source_selection_evidence_plan_json_safe_v1

## 4. Plan id
- first_rf_material_floorplan_source_selection_plan

## 5. Validation posture
- valid
- valid: True
- blocked: False
- blocked labels: []

## 6. Recommended source classes
- official_standard
- official_government_or_agency_data
- official_vendor_documentation
- public_research_paper
- public_dataset
- github_repository
- public_lab_or_university_artifact
- public_benchmark_or_test_suite

## 7. Source priority order
- official_standard
- official_government_or_agency_data
- official_vendor_documentation
- public_research_paper
- public_dataset
- github_repository
- public_lab_or_university_artifact
- public_benchmark_or_test_suite

## 8. Source authority map
```json
{
  "github_repository": {
    "authority_level": "implementation_evidence",
    "evidence_roles": [
      "implementation_reference",
      "candidate_signal"
    ]
  },
  "official_government_or_agency_data": {
    "authority_level": "official_primary",
    "evidence_roles": [
      "measurement_data",
      "domain_context"
    ]
  },
  "official_standard": {
    "authority_level": "official_primary",
    "evidence_roles": [
      "definition_or_standard",
      "constraint_source"
    ]
  },
  "official_vendor_documentation": {
    "authority_level": "official_primary",
    "evidence_roles": [
      "implementation_reference",
      "constraint_source"
    ]
  },
  "public_benchmark_or_test_suite": {
    "authority_level": "public_secondary",
    "evidence_roles": [
      "counterexample_source",
      "replication_target"
    ]
  },
  "public_dataset": {
    "authority_level": "public_primary",
    "evidence_roles": [
      "measurement_data",
      "replication_target"
    ]
  },
  "public_lab_or_university_artifact": {
    "authority_level": "public_secondary",
    "evidence_roles": [
      "measurement_data",
      "replication_target"
    ]
  },
  "public_research_paper": {
    "authority_level": "public_primary",
    "evidence_roles": [
      "prior_art",
      "replication_target"
    ]
  }
}
```

## 9. Evidence role map
```json
{
  "github_repository": [
    "implementation_reference",
    "candidate_signal"
  ],
  "official_government_or_agency_data": [
    "measurement_data",
    "domain_context"
  ],
  "official_standard": [
    "definition_or_standard",
    "constraint_source"
  ],
  "official_vendor_documentation": [
    "implementation_reference",
    "constraint_source"
  ],
  "public_benchmark_or_test_suite": [
    "counterexample_source",
    "replication_target"
  ],
  "public_dataset": [
    "measurement_data",
    "replication_target"
  ],
  "public_lab_or_university_artifact": [
    "measurement_data",
    "replication_target"
  ],
  "public_research_paper": [
    "prior_art",
    "replication_target"
  ]
}
```

## 10. Quality checks
- Check provenance and source class
- Check access scope and licensing
- Check date, version, and freshness
- Check whether the source is authoritative for the claim
- Check for counterexamples and replication targets

## 11. Freshness checks
- Prefer current standards or current releases when defining interfaces
- Check publication date and version history
- Prefer the newest authoritative artifact when a version matters

## 12. License/access checks
- Confirm license or access rights before ingestion
- Prefer public, permissioned, or clearly documented access
- Confirm that the access mode matches the source class

## 13. Privacy checks
- Avoid personal data and unnecessary retention
- Avoid raw-content retention in the plan
- Keep the output metadata-only

## 14. Blocked source classes
- (none)

## 15. Why GitHub is useful
GitHub is useful as implementation evidence and a candidate-signal source, but it is not authoritative on its own.

## 16. Why GitHub is insufficient alone
GitHub can show implementation history and candidate signals, but it does not by itself establish authoritative scientific evidence.

## 17. Why official sources are needed
Official sources are needed to anchor definitions, measurements, and authoritative constraints.

## 18. Missing evidence
- No measurement dataset yet
- No official standard or protocol yet
- No replication target yet

## 19. Disconfirming evidence to seek
- A measurement that shows the bridge does not survive topology constraints
- A counterexample that makes the surface-scattering assumption unnecessary

## 20. Operator review need
Operator review is required before any source access or ingestion decision.

## 21. Next safe step
- prepare_authorized_ingestion_boundary

## 22. Authority status summary
- source ingestion authorized: False
- GitHub call authorized: False
- web call authorized: False
- public claim authorized: False
- final-answer authority: False
- runtime authorized: False

## 23. Safe metadata summary
- safe: True
- metadata_only: True
- json_safe: True
- no_source_ingestion: True
- no_raw_content_retention: True
- no_web_calls: True
- no_github_calls: True
- no_final_answer_authority: True

## 24. Whether the output is interesting
Yes.
- WESLR produced a useful source-selection plan.
- It separated official/primary sources from GitHub/community/implementation evidence.
- It identified what GitHub can and cannot provide.
- It identified official/public evidence classes needed for RF/material/floor-plan work.
- It avoided source access and ingestion.
- It avoided discovery/proof/public-science claims.
- It recommended a useful next safe step.

## 25. Whether the plan is ready for an authorized-ingestion-boundary preparation lane
Yes.

## 26. What it suggests as the next safe lane
prepare_authorized_ingestion_boundary

## 27. Helper gap found
No helper gap was revealed by this sample.

## Final judgment
first_mlcf_source_selection_evidence_plan_sample_valid_interesting_ready_for_authorized_ingestion_boundary_preparation
