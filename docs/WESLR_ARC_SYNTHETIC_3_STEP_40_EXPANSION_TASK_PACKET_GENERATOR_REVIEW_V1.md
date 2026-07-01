# ARC Synthetic 3‑Step – 40‑Task Expansion Task‑Packet Generator Review (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `REVIEW_ARC_SYNTHETIC_3_STEP_40_EXPANSION_TASK_PACKET_GENERATOR_V1`
**Start HEAD**: `f80a5e5e`

## Review summary
- **Generator function `generate_40_task_expansion()`** – present in `weslr/arc_synthetic_3_step_task_schema.py`.  
- **Task count** – function returns exactly **40** task dictionaries.  
- **Baseline 20 task IDs** – the first 20 tasks match the expected IDs:
  `F001_1, F001_2, F001_3, F002_1, F002_2, F002_3, F003_1, F003_2, F003_3, F004_1, F004_2, F004_3, F005_1, F005_2, F006_1, F006_2, F007_1, F007_2, F008_1, F008_2` – unchanged.
- **New tasks** – IDs `T21` … `T40` are present exactly once each.
- **Primitive count** – every task (baseline and new) declares **exactly three** primitives.
- **Stress‑test primitives** – all new tasks include the three required primitives `extract_boundary`, `mirror_object`, and `crop` (in various orders) as verified.
- **Leakage flags** – all tasks have leakage flags set to **false**.
- **No expected‑output leakage** – generator uses only deterministic scene specs; no ground‑truth values are exposed.
- **Solver/dispatch behavior** – unchanged; the generator only creates data structures.
- **Runtime/chat/UI/provider paths** – untouched.
- **Tests** – `weslr/tests/test_40_task_expansion.py` exists and passes (`pytest` reports 1 passed test).

## Validation results
| Check | Status |
|-------|--------|
| `generate_40_task_expansion()` existence | **PASS** |
| Returns 40 tasks | **PASS** |
| Baseline IDs preserved | **PASS** |
| New IDs T21‑T40 present | **PASS** |
| Exactly 3 primitives per task | **PASS** |
| Stress‑test primitives present | **PASS** |
| Leakage flags all false | **PASS** |
| No output leakage | **PASS** |
| Solver/dispatch unchanged | **PASS** |
| Runtime/UI paths unchanged | **PASS** |
| Tests exist & pass | **PASS** |
| `git diff --check` | **PASS** (clean) |
| `python weslr/tests/release_gate_v1.py` | **PASS** |
| `./scripts/weslr_release_check.sh` | **PASS** |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | **PASS** |

**Verdict**: `accepted_generator_ready_for_40_pilot`

---
**Next lane**: `RUN_ARC_SYNTHETIC_3_STEP_40_EXPANSION_PILOT_V1` – execute the 40‑task pilot using the generated packet.
