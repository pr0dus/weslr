# WESLR ARC Official-Data Contamination Boundary (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_OFFICIAL_DATA_CONTAMINATION_BOUNDARY_V1`
**Start HEAD**: `b48b52a55e113258f8d77a3b70660289a9786836`
**actual preflight HEAD**: `b48b52a55e113258f8d77a3b70660289a9786836`

## Purpose

Define the strict boundary that must exist before any official ARC-AGI adapter, scorer, or local/public run is implemented.

## 1) Allowed data classes

| Data class | Allowed use | Forbidden use | Storage rules | Logging rules | Claim rules |
|---|---|---|---|---|---|
| Synthetic WESLR-generated tasks | Development, regression, anti-cheat, boundary design | Treating as official ARC evidence | May be stored in repo/docs as synthetic-only | May be logged as synthetic-only | Never claim official ARC performance from synthetic results |
| Public official ARC training/evaluation data | Only after explicit owner approval and in official-data lanes | Hidden use, ad hoc inspection outside protocol, mixing with synthetic claims | Read-only bundle, provenance recorded, no mutation | Log IDs/status/timing only; no answers | May support local official claims only after local run |
| Hidden/private ARC data | None | All uses forbidden | Must not be loaded, copied, or retained | Must not be logged | No claims |
| User-provided examples | Allowed only if explicitly labeled non-official and non-evaluative | Using as stand-in for official ARC data | Store separately from official bundles | Log as user-provided only | No official claims |
| Generated hard-mode tasks | Development and anti-cheat calibration only | Mixing with official ARC score claims | Store as synthetic-only | Log as synthetic-only | No official claims |
| Reports/logs/derived metadata | Audit, provenance, readiness, and traceability | Revealing hidden answers or internal task language in official solver logs | Separate synthetic vs official folders/records | Logs must omit expected outputs and internal rules | Claims must match evidence class |

## 2) Contamination risks

- hidden/private data exposure
- public-data overfitting
- answer memorization
- leakage through logs/reports
- solver seeing expected outputs
- task metadata leaking rules
- synthetic/official score mixing
- model/tool/web calls during evaluation
- accidental training on evaluation answers
- public claim inflation

## 3) No-contamination protocol

1. Record dataset provenance, version, source, and checksum before any official-data use.
2. Keep official data in a read-only bundle; never rewrite or normalize in place.
3. Separate synthetic, official-public, and private data paths.
4. Do not load hidden/private ARC data.
5. Do not surface expected outputs, latent rules, or internal task language to solver-visible logs.
6. During solving, disallow internet, tool, model, and web calls.
7. If the solver is changed after an official evaluation result, label that iteration as post-run and non-comparable.
8. Keep dev/test/public/private reports separate.
9. Never mix synthetic ARC-style scores with official public scores.
10. Preserve raw official inputs, emitted candidates, scorer output, and runtime metadata as separate artifacts.

## 4) Official-run phases

- **Phase 0:** synthetic-only development and anti-cheat proof
- **Phase 1:** official-format adapter dry-run with toy fixtures only
- **Phase 2:** public official data parse/scorer validation
- **Phase 3:** local public run
- **Phase 4:** post-run audit and contamination review
- **Phase 5:** competition participation design only if all gates pass

## 5) Result-claim policy

- Synthetic scores are never official ARC-AGI performance.
- Local public score claims must include dataset/version/checksum/runtime.
- Private score cannot be inferred from a local public score.
- No leaderboard or competition claim without an actual official submission result.
- No “ARC-AGI solved” claim from synthetic or local public results alone.

## 6) Logging policy

Logs may include:
- task ID
- status
- timing
- whether solved
- score metadata

Logs must not include:
- hidden/private answers
- expected outputs in solver-visible logs
- leaked rule metadata
- internal task language in the official solver-visible bundle

## 7) Implementation gates

- Gate 1: contamination boundary report committed
- Gate 2: toy-fixture adapter lane designed
- Gate 3: scorer validates only toy fixtures first
- Gate 4: official data import requires explicit owner approval

## 8) Readiness summary

- Official ARC local-public percentage claimable: **none yet**
- Official percentage claimable: **0**
- Current evidence: **synthetic ARC-style only**
- Official-format readiness: **not ready**
- Missing: **official adapter, scorer, two-output emitter, runtime harness, provenance protocol, contamination boundary**

## 9) Recommended next lane

- **Implement contamination-boundary checker**

That is the safest step before any official-data adapter or scorer work.
