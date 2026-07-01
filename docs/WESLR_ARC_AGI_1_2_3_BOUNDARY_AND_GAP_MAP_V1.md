# WESLR ARC‑AGI 1/2/3 Boundary and Gap Map – V1

**Lane**: `DESIGN_ARC_AGI_1_2_3_BOUNDARY_AND_GAP_MAP_V1`
**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Start HEAD**: `ad26b3df`

---

## 1. Local Source‑Grounding Status
| Item | Present in Repository? | Comments |
|------|------------------------|----------|
| ARC‑AGI‑1 definition material | **Yes** (references in multiple docs, e.g., `WESLR_ARC_PRIZE_2026_ARC_AGI_2_RULES_AND_CONTRACT_ALIGNMENT_V1.md` mentions the ARC‑AGI‑1 format and constraints). No full specification file is present, only mentions of its format and that we must not claim participation. |
| ARC‑AGI‑2 definition material | **Yes** (several documents: `WESLR_ARC_AGI2_DATASET_DESCRIPTION_CONTRACT_UPDATE_V1.md`, `WESLR_ARC_PRIZE_2026_ARC_AGI_2_RULES_AND_CONTRACT_ALIGNMENT_V1.md`). These contain contract‑style guidance but not the full benchmark test set. |
| ARC‑AGI‑3 definition material | **No** – there is no file or documentation referring to ARC‑AGI‑3 in the repository. |
| Private/hidden benchmark material | **No** – the repo contains only public‑facing contract documents; no hidden test data or private files were found. |
| Official benchmark rules locally available | **Partial** – we have contract‑style descriptions for ARC‑AGI‑1 and ARC‑AGI‑2 (e.g., rules about format, no participation claims). Full official rulebooks are not present. |

---

## 2. Boundary Distinction
- **WESLR synthetic ARC‑style tasks** (2‑step, 3‑step, future ladders) are **internal calibration exercises**. They are not intended as ARC‑AGI benchmark submissions.
- **Static‑local Known‑Science Replay packets** are **internal evidence** used only for metadata‑only replay; they are never submitted to a public benchmark.
- **No** score, leaderboard, or participation claim is ever permitted for any of the above.
- All such work remains **outside** the ARC‑AGI evaluation pipeline and conforms to the strict leakage boundaries defined in prior design documents.

---

## 3. Capability Relevance Matrix
| Capability | Current WESLR | After 3‑step Pilot (expected) | ARC‑AGI‑1 Relevance | ARC‑AGI‑2 Relevance | ARC‑AGI‑3 Relevance / Unknown | Source‑Grounding Confidence |
|------------|--------------|----------------------------|--------------------|--------------------|------------------------------|------------------------------|
| **single‑step rule induction** | ✔︎ (basic rule‑like transformations) | ✔︎ (still present) | Medium – required for simple ARC‑AGI‑1 tasks. | Low – ARC‑AGI‑2 expects deeper abstraction. | Unknown – likely needed at higher levels. | High – documented in several ARC‑AGI‑1/2 docs. |
| **2‑step composition** | ✔︎ (stable 2‑step 80) | ✔︎ (unchanged) | High – ARC‑AGI‑1 baseline includes 2‑step chains. | Medium – foundation for deeper composition. | Unknown – may be prerequisite. | High – well‑documented. |
| **3‑step state carry‑over** | ✘ (not yet pilotled) | ✔︎ (pilot design) | Medium – ARC‑AGI‑1 may test limited multi‑step state. | High – ARC‑AGI‑2 explicitly stresses multi‑step carry‑over. | Unknown – future benchmarks may extend further. | Medium – design exists, no execution yet. |
| **object identity preservation** | ✔︎ (2‑step tests) | ✔︎ (pilot adds 3‑step checks) | High – required for consistent reasoning. | High – essential for deeper planning. | Unknown – likely still required. | High – references in ladder design docs. |
| **role memory** | ✘ (no explicit role tracking) | ✘ (still pending) | Low – not a primary ARC‑AGI‑1 requirement. | Medium – ARC‑AGI‑2 may need role‑aware reasoning. | Unknown – could become relevant. | Low – no source material mentions this explicitly. |
| **abstraction** | ✘ (tasks are concrete) | ✘ (pilot is still concrete) | Medium – ARC‑AGI‑1 includes simple abstraction tasks. | High – ARC‑AGI‑2 expects abstract reasoning. | Unknown – future benchmarks may increase abstraction depth. | Low – only indirect references. |
| **dynamic parameter inference** | ✔︎ (primitive parameters vary) | ✔︎ (pilot varies rotation, colour, etc.) | Medium – ARC‑AGI‑1 allows parameter variation. | High – ARC‑AGI‑2 expects robust inference across steps. | Unknown – likely needed. | Medium – documented in ladder design. |
| **branch rejection** | ✘ (no branching in current tasks) | ✘ (pilot does not include branches) | Low – not a core ARC‑AGI‑1 feature. | Medium – ARC‑AGI‑2 may test branch pruning. | Unknown – could be added later. | Low – no source material. |
| **shuffle invariance** | ✔︎ (2‑step audit passed) | ✔︎ (3‑step design includes shuffle‑invariance check) | Medium – ARC‑AGI‑1 expects basic robustness. | High – ARC‑AGI‑2 stresses invariance across longer pipelines. | Unknown – likely still important. | High – explicitly mentioned in prior docs. |
| **anti‑overfit checks** | ✔︎ (static‑local, no external data) | ✔︎ (pilot continues strict boundaries) | Medium – ARC‑AGI‑1 forbids leakage. | High – ARC‑AGI‑2 emphasises overfit protection. | Unknown – future benchmarks will maintain this. | High – boundary rules are well‑documented. |
| **trace / audit quality** | ✔︎ (2‑step trace contract) | ✔︎ (3‑step trace contract defined) | High – ARC‑AGI‑1 requires full traceability. | High – ARC‑AGI‑2 expects detailed audit logs. | Unknown – will remain essential. | High – trace contracts are defined in ladder docs. |
| **final‑answer discipline** | ✘ (internal reports only) | ✘ (still internal) | High – ARC‑AGI‑1 prohibits premature final‑answer generation. | High – ARC‑AGI‑2 enforces strict separation. | Unknown – will continue to be required. | High – explicitly enforced in boundary docs. |
| **evidence‑boundary control** | ✔︎ (static‑local replay packets) | ✔︎ (pilot maintains) | High – ARC‑AGI‑1 bans hidden evidence. | High – ARC‑AGI‑2 bans any leakage. | Unknown – same requirement. | High – documented throughout. |

---

## 4. Gap Map
### ARC‑AGI‑1
| Aspect | WESLR Currently Has | Missing / Needed | Blocked (must not claim) |
|--------|-------------------|------------------|--------------------------|
| 2‑step composition | ✔︎ stable 2‑step ladder (77/3) | None for basic chain | **No claim of participation or score.** |
| 3‑step carry‑over | ✘ (pilot not yet executed) | Implement 3‑step pilot, trace contract | **No benchmark claim** |
| Object identity | ✔︎ basic preservation | None | — |
| Shuffle invariance | ✔︎ (audit passed) | None | — |
| Final‑answer discipline | ✔︎ (internal reports only) | None | — |
| Public‑claim discipline | ✔︎ (forbidden) | None | — |
| Role memory, abstraction, branching | ✘ | Add role‑memory tracking, abstraction tasks, branch handling for future levels. | — |

### ARC‑AGI‑2
| Aspect | WESLR Currently Has | Missing / Needed | Source‑Grounding Confidence |
|--------|-------------------|------------------|------------------------------|
| 3‑step state carry‑over | Pilot design exists, not yet run | Execute pilot, verify carry‑over, produce trace logs. | **Medium** – design present, no execution evidence. |
| Deeper abstraction | ✘ | Introduce abstract reasoning tasks (e.g., rule induction across steps). | **Low** – no local definition. |
| Role memory & branch rejection | ✘ | Implement role‑state tracking and branch pruning logic. | **Low** |
| Parameter inference across steps | ✔︎ (dynamic parameters in pilot) | Strengthen inference robustness. | **Medium** |
| Shuffle invariance (extended) | ✔︎ (planned for 3‑step) | Verify across longer pipelines. | **Medium** |
| Full audit / trace quality | ✔︎ (trace contract defined) | Generate actual audit logs from pilot runs. | **Medium** |
| No public‑claim / final‑answer separation | ✔︎ (enforced) | Maintain discipline. | **High** |

### ARC‑AGI‑3 (Future / Unknown)
| Aspect | Local Evidence | Notes |
|--------|----------------|-------|
| Definition material | **None** – no ARC‑AGI‑3 spec in repo. |
| Expected capabilities | Likely an extension of ARC‑AGI‑2 (longer ladders, higher abstraction, meta‑reasoning). |
| Readiness | **Insufficient** – cannot produce a concrete gap map without source material. |

---

## 5. Hard Forbidden Claims (must never appear)
- "WESLR solves ARC‑AGI"
- "WESLR is ARC‑AGI‑ready"
- "WESLR has an ARC‑AGI score"
- "WESLR participates in ARC‑AGI"
- Any leaderboard or benchmark result claim
- Any public claim based on hidden/private test data
- Any final‑answer generation or candidate‑output‑surface wiring claim
- Any statement implying that a static‑local replay constitutes a benchmark submission

These are explicitly prohibited by the leakage flags in all task schemas and by the overall governance policy.

---

## 6. Recommended Safe Next Steps
| Track | Next Lane | Rationale |
|------|-----------|----------|
| **Track A – WESLR_INTERNAL_CAPABILITY_LADDER** | `IMPLEMENT_ARC_SYNTHETIC_3_STEP_TASK_SCHEMA_AND_PACKET_GENERATOR_V1` | Implements the JSON schema and diagnostic‑only packet generator designed in the 3‑step pilot, keeping work fully static‑local. |
| **Track B – ARC_AGI_BOUNDARY_AND_READINESS** | `CREATE_LOCAL_ARC_AGI_PUBLIC_SOURCE_PACKET_SCHEMA_V1` | Since we have concrete ARC‑AGI‑1 and ARC‑AGI‑2 contract documents, we can formalise a *public source packet schema* that captures the publicly disclosed benchmark fields without exposing hidden data. This prepares us for future alignment once full specifications become available. |

If later we discover that the ARC‑AGI‑2 contract is insufficient for a full schema, the alternative lane `DEFER_ARC_AGI_BOUNDARY_UNTIL_SOURCE_PACKET_EXISTS_V1` can be taken.

---

**Conclusion** – This document provides a source‑grounded status check, a clear capability‑to‑benchmark relevance matrix, a concise gap map for ARC‑AGI‑1/2/3, strict forbidden claim definitions, and concrete next lanes for both internal capability growth and benchmark‑boundary preparation.
