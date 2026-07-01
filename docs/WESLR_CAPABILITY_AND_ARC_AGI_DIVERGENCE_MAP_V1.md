# WESLR Capability & ARC‑AGI Divergence Map – V1

**Lane**: `DESIGN_WESLR_CAPABILITY_AND_ARC_AGI_DIVERGENCE_MAP_V1`
**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Start HEAD**: `34c07852`

---

## 1. Two‑Track Roadmap

| Track | Purpose | Next Lane | Allowed Work | Forbidden Work | Success Criteria | Risk |
|-------|---------|-----------|--------------|----------------|------------------|------|
| **WESLR_INTERNAL_CAPABILITY_LADDER** | Incrementally grow WESLR’s internal reasoning abilities without chasing external benchmarks. | `DESIGN_ARC_SYNTHETIC_3_STEP_PILOT_V1` (or later `DESIGN_ARC_SYNTHETIC_N_STEP_LADDER_V1`) | • 3‑step synthetic pilot (20 tasks).<br>• Blackboard state growth, parameter carry‑over, object identity preservation.<br>• Role memory, branch rejection, failure classification.<br>• Expansion to 4‑step, 5‑step, N‑step ladders.<br>• Static‑local evidence packets and controlled replay expansion. | • Any external API / model calls.<br>• Public or benchmark claims.<br>• `.weslr` persistence.<br>• Runtime/chat wiring.<br>• Live data ingestion. | All pilot tasks complete with **exact / partial** success metrics meeting the predefined thresholds (e.g., ≥ 95 % exact, ≤ 5 % partial, 0 unsupported/failed). | Over‑engineering before the pipeline is proven; risk of hidden external dependencies. |
| **ARC_AGI_BOUNDARY_AND_READINESS** | Map the capabilities required by the ARC‑AGI benchmark series (ARC‑AGI‑1, ARC‑AGI‑2, ARC‑AGI‑3) against current WESLR abilities, without submitting or claiming participation. | `DESIGN_ARC_AGI_1_2_3_BOUNDARY_AND_GAP_MAP_V1` | • Analyze publicly available ARC‑AGI descriptions (if present locally).<br>• Identify capability gaps, data‑boundary constraints, and forbidden actions.<br>• Produce a gap‑matrix and a high‑level readiness narrative. | • Ingesting ARC‑AGI private / hidden test data.<br>• Claiming leaderboard or benchmark scores.<br>• Using expected test outputs as hints.<br>• Final‑answer generation or candidate‑output‑surface wiring.<br>• Live retrieval or provider/model calls.<br>• `.weslr` writes. | A clear, sourced‑grounded map that shows which WESLR capabilities already align with each ARC‑AGI level and which remain missing, *without* making any participation claim. | Mis‑identifying requirements due to lack of official ARC‑AGI documentation; risk of accidental over‑claiming. |

---

## 2. Capability‑to‑Benchmark Gap Matrix

| Capability | Current WESLR | After 3‑step Pilot (Project) | ARC‑AGI‑1 Relevance | ARC‑AGI‑2 Relevance | ARC‑AGI‑3 (Future) |
|------------|----------------|-----------------------------|----------------------|----------------------|----------------------|
| **Object identity** | ✔︎ (preserved in 2‑step & static packets) | ✔︎ (tested across 3 steps) | High – required for multi‑step compositional reasoning. | Very High – needed for deeper planning and abstraction. | Unknown – likely still required. |
| **Multi‑step composition** | ✔︎ (2‑step) | ✔︎ (3‑step pilot) | High – benchmark expects chained transformations. | Very High – longer chains and planning horizons. | Future – N‑step composition may be needed. |
| **State carry‑over** | ✔︎ (static‑local packets) | ✔︎ (parameter propagation across 3 steps) | High – state must survive across steps. | Very High – state across many planning phases. | Expected – robust state management. |
| **Abstraction** | Minimal (synthetic tasks are concrete) | Emerging (pilot explores abstract parameter reuse) | Medium – ARC‑AGI‑1 includes simple rule induction. | High – deeper abstraction and concept formation required. | Very High – open‑ended reasoning. |
| **Rule induction** | None (tasks are predefined) | Partial (pilot may introduce rule‑like patterns) | Medium – benchmark may test simple rule extraction. | High – expects learning of reusable rules. | Future – advanced induction. |
| **Contradiction detection** | ✔︎ (stop‑condition checks) | ✔︎ (extended to 3‑step inconsistencies) | Medium – needed for error handling. | High – essential for planning under uncertainty. | Expected – advanced logical consistency. |
| **Anti‑overfit checks** | Basic (static‑local no‑overfit) | Added (shuffle‑invariance audit extended to 3 steps) | Medium – benchmark discourages memorisation. | High – stronger anti‑overfit controls required. | Future – may demand formal generalisation proofs. |
| **Shuffle invariance** | ✔︎ (2‑step audit passed) | ✔︎ (3‑step audit planned) | Medium – ensures robustness to permutation. | High – deeper invariance across longer sequences. | Expected – invariance across complex pipelines. |
| **Evidence boundary control** | ✔︎ (static‑local packets) | ✔︎ (expanded static‑local replay) | High – benchmark enforces strict data boundaries. | Very High – any leakage is disallowed. | Future – boundary enforcement remains critical. |
| **Final‑answer discipline** | Not applicable (internal reports only) | Not applicable (still internal) | High – benchmark expects a single final answer per task. | Very High – must separate candidate generation from final answer. | Expected – strict separation required. |
| **Public‑claim discipline** | Enforced (no public claim fields) | Enforced | High – benchmark forbids public claim of results before validation. | Very High – any claim must be vetted. | Expected – continues. |

*✔︎ indicates the capability is currently implemented or verified.*

---

## 3. Branch / Lane Strategy

| Option | Description | Pros | Cons |
|-------|-------------|------|------|
| **Continue 3‑step pilot first** | Finish the 20‑task pilot, collect traces, and assess internal metrics before any benchmark mapping. | • Guarantees a solid internal foundation.<br>• Provides concrete data for the gap matrix.<br>• No risk of premature benchmark exposure. | • Delays explicit ARC‑AGI boundary documentation. |
| **Create ARC‑AGI boundary report first** | Produce the divergence map now (this lane) and then continue the pilot. | • Early visibility of where effort is needed for future benchmarks.<br>• Aligns stakeholder expectations. | • May rely on speculative ARC‑AGI details if local definitions are missing. |
| **Run both in parallel** | Work on the pilot while drafting the divergence map as a separate documentation lane. | • Parallel progress, no idle time.<br>• Immediate feedback from pilot can refine the map. | • Requires coordination to avoid duplicated effort. |

**Recommendation** – Pursue **both in parallel**: the divergence map (this lane) is already being produced, and the 3‑step pilot design (Track A) proceeds concurrently. This satisfies the requirement for a roadmap while keeping the internal capability work on schedule.

---

## 4. Hard Boundary List (Forbidden Operations)

| Forbidden Action | Reason |
|------------------|--------|
| ARC‑AGI participation or leaderboard claims | Violates policy to avoid premature benchmark claims. |
| Public benchmark score claims | Would constitute an unauthorized public claim. |
| Use of hidden or private ARC‑AGI test data | Breaches data‑boundary rules and may expose non‑public material. |
| Expected test‑output usage as hints | Disallowed under **public‑claim discipline**. |
| Final‑answer generation or candidate‑output‑surface wiring | Breaks the **final‑answer discipline**; WESLR currently only produces internal reports. |
| Live retrieval / external provider or model calls | Violates static‑local evidence constraints. |
| `.weslr` persistence writes | Outside the allowed static‑local sandbox. |
| Any form of public export of internal traces without vetting | Could unintentionally leak proprietary methodology. |
| Direct incorporation of ARC‑AGI private specifications not present in the repo | Must not hallucinate or fabricate benchmark rules. |

---

## 5. Recommended Next Two Lanes

| Track | Recommended Next Lane | Justification |
|------|-----------------------|----------------|
| **Track A – WESLR_INTERNAL_CAPABILITY_LADDER** | `DESIGN_ARC_SYNTHETIC_3_STEP_PILOT_V1` – formalise the 20‑task pilot, define JSON schema for 3‑step tasks, and generate a diagnostic‑only packet set. | This advances the internal capability ladder while keeping all work within the static‑local boundary. |
| **Track B – ARC_AGI_BOUNDARY_AND_READINESS** | `DESIGN_ARC_AGI_1_2_3_BOUNDARY_AND_GAP_MAP_V1` – produce a more detailed, source‑grounded gap analysis for ARC‑AGI‑1 and ARC‑AGI‑2 (if local definitions exist) and outline unknown ARC‑AGI‑3 requirements. | Provides a documented roadmap for future benchmark readiness without any participation or claim. |

---

## 6. ARC‑AGI Source‑Grounding Status
- The repository **does not contain** any source‑grounded ARC‑AGI‑1, ARC‑AGI‑2, or ARC‑AGI‑3 definition files or private test data. Consequently, the gap matrix relies on publicly known benchmark characteristics and the **absence** of internal ARC‑AGI artefacts is explicitly noted.

---

**Conclusion** – The divergence map defines two clear, non‑overlapping tracks: an internal capability ladder that can proceed now, and a benchmark‑boundary track that will remain documentation‑only until concrete ARC‑AGI specifications are publicly available. Both tracks respect strict leakage boundaries and avoid any premature benchmark claims.
