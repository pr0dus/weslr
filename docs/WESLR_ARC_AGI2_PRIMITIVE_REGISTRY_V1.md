# WESLR ARC-AGI2 Primitive Registry V1

## Repository
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Heads
- Start HEAD: `43c491189f7b367fef5d22893a5f23b29d4e4e17`
- Actual preflight HEAD: `43c491189f7b367fef5d22893a5f23b29d4e4e17`
- End HEAD: `eb8b8f37290508276cc0c8add11a11f3c74577a2`
- Commit status: code committed; report pending commit

## Files added/changed
- Added `weslr/arc_primitive_registry_v1.py`
- Added `weslr/tests/test_arc_primitive_registry_v1.py`

## Primitive registry summary
- Introduced a shared immutable primitive descriptor schema.
- Added a registry object that supports register, get, list, family filtering, export, and validation.
- Built a trace-safe built-in manifest for the current ARC capability vocabulary.

## Descriptor schema
Fields:
- `primitive_name`
- `family`
- `input_type`
- `output_type`
- `preconditions`
- `effect_summary`
- `train_inference_fn_name`
- `executor_fn_name`
- `inverse_or_comparable_relation`
- `rejection_reasons`
- `trace_safe_metadata`

Properties:
- immutable dataclass
- JSON-safe export
- function references stored as names only
- no raw grids or callable objects in the manifest

## Built-in primitive families
- object_bbox
- shape_geometry
- color_role
- resize_tile
- count_quantity

## Built-in primitive count
- 24 primitives

## Validation behavior
Validation fails on:
- empty primitive name
- duplicate primitive name
- empty family
- empty input/output type
- empty effect summary
- empty train inference function name
- empty executor function name
- empty rejection reasons
- unsafe trace metadata labels such as `raw_grid`, `expected_output`, `solution`, `answer_key`, `public_solution`

## Test summary
- descriptor creation ✅
- JSON-safe export ✅
- missing required fields rejection ✅
- unsafe trace metadata rejection ✅
- register / get / family listing ✅
- duplicate name rejection ✅
- built-in primitive set coverage ✅
- built-in registry validation ✅
- manifest label safety ✅

## Limitations
- Registry only.
- No primitive discovery logic yet.
- No family discovery logic yet.
- No universal runner yet.
- No public ARC data read.
- No Kaggle submission path involved.

## Validation
- `python -m py_compile weslr/arc_primitive_registry_v1.py` ✅
- `python -m pytest -q weslr/tests/test_arc_primitive_registry_v1.py` ✅
- `git diff --check` ✅
- `python weslr/tests/release_gate_v1.py` ✅
- `./scripts/weslr_release_check.sh` ✅
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo` ✅

## Health-check status
- Mandatory source-repo health check: PASS
- Exact status: PASS with 6 mandatory passes, 0 fails, 3 optional warnings

## Recommended next lane
- `TASK_FEATURE_SIGNATURE_EXTRACTOR_V1`

## Why this next
The registry is now the vocabulary layer. The next useful step is a task feature signature extractor that maps task packets into compact primitive-hint features for discovery and family ranking.

## Claim boundary
This lane only defines the registry vocabulary and validation contract.
It does not implement discovery, family search, or universal execution.
It does not use public ARC data or scored public feedback.

## Readiness verdict
`primitive_registry_v1_passed_ready_for_task_feature_signature_extractor_lane`
