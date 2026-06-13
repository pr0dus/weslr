# WESLR Controlled Live SearXNG Boundary Real Timestamp Repair V1

**Status:** Review only. No live SearXNG call was issued in this review.

## Scope
Reviewed repair commit: `9c6556fab60f72178acc7073cd435027c5ae644e`

Base HEAD: `23f5cd656aa6fff034508f4dd6c572b9d78a14ab`

Review branch: `repair-live-searxng-real-timestamps-20260613`

## Files reviewed
- `weslr/controlled_live_searxng_metadata_only_boundary.py`
- `weslr/tests/test_controlled_live_searxng_metadata_only_boundary_v1.py`

## Defect A review result
Pass.

`_derive_freshness_status(...)` now:
- accepts no-offset ISO timestamps by normalizing them as UTC
- accepts `Z`
- accepts explicit offsets
- keeps year-only handling
- returns `unknown` for malformed or future values
- avoids naive/aware datetime comparison errors

## Defect B review result
Pass.

`run_controlled_live_searxng_metadata_only_boundary_v1(...)` now:
- catches unexpected post-HTTP result-processing exceptions
- returns structured `boundary_internal_error`
- does not retain traceback text, exception text, or raw response body
- preserves the existing structured fail-closed cases for malformed JSON, wrong content type, timeout, network error, redirect, 4xx, 5xx, and incomplete results

## Regression-test review result
Pass.

Coverage includes:
- `2024-01-01T00:00:00`
- `2024-01-01T00:00:00+00:00`
- `2024-01-01T00:00:00Z`
- malformed timestamp
- future naive timestamp
- forced per-result processing exception → `boundary_internal_error`

The tests use mocked/injected HTTP only.

## Validation
- `python3 -m py_compile ...` ✅
- `python3 -m pytest weslr/tests/test_controlled_live_searxng_metadata_only_boundary_v1.py` ✅ (`34 passed`)
- `python3 weslr/tests/release_gate_v1.py` ✅
- `bash scripts/weslr_release_check.sh` ✅
- `git diff --check` ✅

## Safety notes
- No live SearXNG run in this review.
- No `.weslr` IO.
- No runtime/chat responder/public-site/provider/model integration.
- No protected-file diffs.

## Required marker lines
WESLR Controlled Live SearXNG Boundary Real Timestamp Repair V1
Defect A
Defect B
2024-01-01T00:00:00
boundary_internal_error
mocked/injected HTTP only

## Final judgment
controlled_live_searxng_boundary_real_timestamp_repair_review_valid_ready_for_branch_push
