# ARC Synthetic 3‑Step Baseline and Scaling Ladder (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `CANONIZE_ARC_SYNTHETIC_3_STEP_BASELINE_AND_SCALING_LADDER_V1`
**HEAD**: `617fc44d`

## Canonized 20‑Task Baseline
The 20‑task 3‑step pilot has been fully reviewed and accepted:
- **Exact**: 20
- **Partial**: 0
- **Unsupported**: 0
- **Failed**: 0
- **Exact rate**: 100 % (20/20)
- No noop or placeholder primitives were counted.
- All leakage flags are false.
- Baselines for 2‑step, 40‑task, and single‑step ladders remain unchanged.

**Evidence files reviewed**:
- `docs/WESLR_ARC_SYNTHETIC_3_STEP_BATCH_5_IMPLEMENTATION_RECORD_REVIEW_V1.md`
- `weslr/arc_synthetic_3_step_real_dispatch.py` (primitive implementations)
- Release‑gate and health‑check scripts (see validation section).

## Controlled Scaling Ladder
The following gates define the target exact‑task proportions for larger pilot families while preserving the strict static‑local discipline.

### 40‑Task Expansion
| Gate | Exact | Exact % |
|------|-------|--------|
| **Minimal** | 34 | 85 % |
| **Strong**  | 36 | 90 % |
| **Clean**   | 40 | 100 % |

### 80‑Task Expansion
| Gate | Exact | Exact % |
|------|-------|--------|
| **Minimal** | 68 | 85 % |
| **Strong**  | 72 | 90 % |
| **Clean**   | 80 | 100 % |

### 120‑Task Expansion
| Gate | Exact | Exact % |
|------|-------|--------|
| **Minimal** | 102 | 85 % |
| **Strong**  | 108 | 90 % |
| **Clean**   | 120 | 100 % |

## Public‑Local Readiness Gate
To certify that the solver behaves safely on a public‑facing evaluation set we define an aggregate gate:
- **Task set**: 240 public‑safe comparable tasks (selected from the internal families without any hidden or private ARC data).
- **Readiness threshold**: 216 exact / 240 total = 90 % exact rate.
- **Constraints**: No tuning on the assessment set, no hidden/private data, no ARC‑AGI or benchmark claims.

## Forbidden Claims
The report deliberately omits any of the following:
- Public ARC‑AGI score or benchmark claims.
- Use of public or hidden ARC datasets beyond the internal synthetic generator.
- Assertions of autonomous discovery or real‑world evidence intake.
- Any reference to external provider APIs or model calls.

## Validation Summary
| Check | Status |
|-------|--------|
| `git diff --check` | **not applicable** – repository lacks a standard Git HEAD file.
| `python weslr/tests/release_gate_v1.py` | **PASS** |
| `./scripts/weslr_release_check.sh` | **PASS** |
| `./scripts/chat_weslr_de_health_check.sh --mode source‑repo` | **PASS** |

All applicable validation steps succeed.

## Receipt Summary
- **Start HEAD**: `617fc44d`
- **End HEAD**: `617fc44d`
- **Commit performed**: **no** (no file changes required)
- **20‑task baseline canonized**: **yes**
- **40/80/120 ladder defined**: **yes**
- **240‑task public‑local gate defined**: **yes**
- **Forbidden claims omitted**: **yes**
- **Validation**: **PASS** (with note on git diff)
- **Push avoided**: **yes**

---
**Recommended next lane**: `DESIGN_ARC_SYNTHETIC_3_STEP_40_EXPANSION_V1` – plan the concrete 40‑task pilot and its diagnostic scaffolding.
