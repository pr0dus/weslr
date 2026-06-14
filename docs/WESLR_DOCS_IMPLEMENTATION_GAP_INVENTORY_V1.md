# WESLR Docs Implementation Gap Inventory V1

## 1. purpose
Read-only inventory of docs/artifacts that are implemented, missing, blocked, or pending review.

## 2. repo/branch/head
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `42d6579567fc1be1d90f5aa93e91e61b200a8fb5`

## 3. scan method
- tracked docs: `git ls-files docs`
- untracked docs: `find docs -maxdepth 1 -type f`
- helper modules: `git ls-files 'weslr/*.py'`
- tests: `git ls-files 'weslr/tests/*.py'`
- safe marker scan: filename + short text marker search only; no raw content retained

## 4. tracked docs count
1047

## 5. untracked docs count
59

## 6. helper module count
1436

## 7. test file count
534

## 8. classification table
| artifact/doc path | category | detected status markers | expected implementation file | expected test file | implementation status | review status | blocker | recommended next lane | confidence |
|---|---|---|---|---|---|---|---|---|---|
| docs/WESLR_ARTIFACT_FORWARD_WORK_PLAN_HELPERS_REVIEW_V1.md | review doc | - | weslr/artifact_forward_work_plan.py | weslr/tests/test_artifact_forward_work_plan_v1.py | implemented_source_and_tests_found | review missing | review missing | REVIEW_WESLR_ARTIFACT_FORWARD_WORK_PLAN_HELPERS_V1 | high |
| docs/WESLR_UNEXPLAINED_SIGNAL_ARTIFACT_PIPELINE_V1.md | design doc | blocked | weslr/unexplained_signal_artifact.py | weslr/tests/test_unexplained_signal_artifact_v1.py | implemented_source_and_tests_found | review_found | none | REVIEW_WESLR_UNEXPLAINED_SIGNAL_ARTIFACT_PIPELINE_V1 | high |
| docs/WESLR_UNEXPLAINED_SIGNAL_ARTIFACT_PIPELINE_REVIEW_V1.md | review doc | blocked, IMPLEMENT_ | weslr/unexplained_signal_artifact.py | weslr/tests/test_unexplained_signal_artifact_v1.py | review_found | review_found | none | REVIEW_WESLR_UNEXPLAINED_SIGNAL_ARTIFACT_PIPELINE_V1 | high |
| docs/WESLR_UNEXPLAINED_SIGNAL_ARTIFACT_HELPERS_REVIEW_V1.md | review doc | blocked, IMPLEMENT_, RUN_ | weslr/unexplained_signal_artifact.py | weslr/tests/test_unexplained_signal_artifact_v1.py | review_found | review_found | none | REVIEW_WESLR_UNEXPLAINED_SIGNAL_ARTIFACT_PIPELINE_V1 | high |
| docs/WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_PLAN_V1.md | implementation plan | blocked, REVIEW_, RUN_, REPAIR_ | - | - | blocked_result | review_found | local metadata locator unavailable | REPAIR_WESLR_LOCAL_METADATA_LOCATOR_AVAILABILITY_V1 | high |
| docs/WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_RESULT_V1.md | result doc | blocked, REVIEW_, RUN_ | - | - | blocked_result | review_found | local metadata locator unavailable | REVIEW_WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_RESULT_V1 | high |


## 9. design docs with implementation found
- `docs/WESLR_UNEXPLAINED_SIGNAL_ARTIFACT_PIPELINE_V1.md` → `weslr/unexplained_signal_artifact.py` + `weslr/tests/test_unexplained_signal_artifact_v1.py`
- `docs/WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_PLAN_V1.md` is linked to a blocked run result rather than a missing helper

## 10. design docs missing implementation
- `docs/WESLR_ARTIFACT_FORWARD_WORK_PLAN_HELPERS_REVIEW_V1.md` is missing as a review artifact, not an implementation doc

## 11. implementations missing review
- `weslr/artifact_forward_work_plan.py` + `weslr/tests/test_artifact_forward_work_plan_v1.py` appear implemented, but `docs/WESLR_ARTIFACT_FORWARD_WORK_PLAN_HELPERS_REVIEW_V1.md` is absent

## 12. blocked result docs
- `docs/WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_RESULT_V1.md` → blocked by local metadata locator unavailability

## 13. environment repair needs
- `REPAIR_WESLR_LOCAL_METADATA_LOCATOR_AVAILABILITY_V1`

## 14. untracked docs needing classification
- pre-existing untracked docs under `docs/` remain unclassified and untouched

## 15. current critical gaps
- blocked local metadata locator
- missing artifact-forward-work-plan helper review doc
- broader untracked docs classification backlog

## 16. recommended next lanes
- `REVIEW_WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_RESULT_V1`
- `REPAIR_WESLR_LOCAL_METADATA_LOCATOR_AVAILABILITY_V1`
- `REVIEW_WESLR_ARTIFACT_FORWARD_WORK_PLAN_HELPERS_V1`

## 17. final judgment
docs_implementation_gap_inventory_needs_repair
