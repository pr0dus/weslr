# DESIGN: First Controlled Real‑Evidence Direction Run (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Start HEAD**: `55c97a4fe5e1e4b2a0a6c9f2d0e8b7c6a5f4d3e2`
**Dispatch**: `DESIGN_WESLR_FIRST_CONTROLLED_REAL_EVIDENCE_DIRECTION_RUN_V1`

---

## 1️⃣ What qualifies as “real evidence” for this first run?

| Evidence Type | Description | Allowed Content | Provenance Requirement |
|---|---|---|---|
| **Local static text packet** | A hand‑crafted JSON/YAML document stored in the repo. | Plain‑text excerpts, sensor logs, manually transcribed observations. | Must be authored by the project owner or a designated reviewer; file path must be inside the repo (e.g., `evidence/first_packet.json`). |
| **Owner‑provided source packet** | A packet supplied by the owner (e.g., a PDF, CSV, or markdown file) that is **already** in the repository. | Any textual or tabular data the owner wishes WESLR to reason over. | File must be committed to the repo; no external fetch.
| **Public‑safe copied excerpt** | A short excerpt (≤ 300 words) from a public source that is openly licensed (e.g., Wikipedia, public domain). | The excerpt itself, with a citation comment. | Must include a citation comment inside the packet; no link‑fetching at runtime.
| **Manually curated artifact** | An image, diagram, or audio clip that has been placed in the repo by the owner. | Binary files stored under `evidence/` with a companion manifest describing the content. | Must be added to the repo; no on‑the‑fly conversion.
| **Known‑science replay packet** | Re‑use of a previously validated synthetic evidence packet that was produced during the ARC calibration phase. | The exact packet content, unchanged.
| **Controlled observation notes** | Structured notes written by the owner after a manual experiment or observation. | Markdown list or JSON object with fields `observation`, `timestamp`, `operator`. | Must be authored locally; no live sensor integration.

**All** qualifying evidence must be **static, version‑controlled, and locally present** before the run is started.

---

## 2️⃣ What evidence is forbidden in the first run?

| Forbidden Evidence | Reason |
|---|---|
| Live web / RSS / GitHub ingestion | Would require external retrieval – outside the “static‑local” boundary. |
| Provider / model / tool calls (LLM, image, video, etc.) | Violates the “no external calls” rule. |
| Autonomous retrieval (search, web_fetch, web_search, pdf, etc.) | Must remain fully manual. |
| Lab‑notebook ingestion | Not yet authorized; would be a form of live data import. |
| Private / hidden data not explicitly authored for this run | Risk of leaking sensitive information. |
| `.weslr` persistence files | Persistence is blocked until a dedicated gate. |
| Database writes / external storage | Would create state beyond the repo. |
| Public claims or benchmark assertions | The run must stay internal‑only. |
| Any dynamic generation of evidence at runtime | Must be pre‑created and committed. |

---

## 3️⃣ Candidate First Directions – Evaluation Matrix

| Direction | Evidence Availability | Safety | Falsifiability | Usefulness | Over‑claim Risk | Fit with Current Capabilities |
|---|---|---|---|---|---|---|
| **Known‑science replay** | High – uses already validated synthetic packets. | Very high – no new data collected. | High – can be compared against known outcomes. | Moderate – demonstrates reasoning transfer. | Low – only re‑uses known results. | Perfect – matches existing metadata helpers.
| **RF / Wi‑Fi sensing** | Low – no sensor data in repo yet. | Medium – risk of privacy leakage if real signals were used. | Low – hard to falsify without live capture. | High – would show real‑world sensing capability. | High – would require live hardware integration (blocked). | Not ready.
| **Prompt‑injection / AI‑antivirus** | Medium – requires crafting injection packets. | Medium – could expose internal model behavior. | Medium – can be tested with controlled prompts. | High – directly relevant to AI‑safety research. | Medium – could be mis‑interpreted as a claim of detection. | Feasible if packets are pre‑made, but still involves model calls (blocked).
| **Materials / energy discovery** | Low – no experimental data in repo. | High – safe if only manual notes are used. | Low – would be speculative. | Low – not aligned with current WESLR domain. | Low – no immediate value.
| **ARC‑like reasoning transfer** | High – uses existing ARC synthetic packets as a bridge. | High – no new external data. | High – can be validated against synthetic baseline. | High – tests the core transfer hypothesis. | Low – stays within synthetic‑to‑real boundary.
| **Owner‑workflow evidence** | Medium – owner can provide a small workflow log. | High – fully manual. | High – can be audited. | Moderate – demonstrates end‑to‑end pipeline.

### Summary of Ratings
*Evidence Availability* and *Safety* are decisive. The only direction with **both high availability and high safety** without any prohibited operation is **Known‑Science Replay** (and the closely related **ARC‑like reasoning transfer** which re‑uses ARC packets). The others either need live sensors, model calls, or external retrieval.

---

## 4️⃣ Recommended First Real‑Evidence Direction

**Recommendation:** **Known‑Science Replay Direction** (i.e., replay a previously validated ARC synthetic packet as a “real‑evidence” source).

**Why this is the safest first step:**
1. **Static & Local** – the packet already lives in the repo; no external fetches are required.
2. **Zero External Calls** – no provider, model, or tool invocation is needed during the run.
3. **Falsifiable** – the replay can be directly compared to the original synthetic result; any deviation is a concrete failure.
4. **Low Over‑claim Risk** – we only claim “we reproduced the synthetic outcome using a static packet”, which is a factual internal statement.
5. **Fit with Current Capability** – WESLR’s metadata‑only helpers are built to consume such packets; no new code is needed.
6. **No 2‑step‑120 prerequisite** – the replay does not depend on the full 2‑step‑120 synthetic chain; it only needs the already‑validated ARC packet.

---

## 5️⃣ First‑Run Packet Structure

```json
{
  "packet_id": "first_real_evidence_001",
  "domain": "knowledge_replay",
  "evidence_source_type": "known_science_replay",
  "allowed_fields": {
    "title": "string",
    "description": "string",
    "original_arc_packet_ref": "string",   // e.g., "arc_packet_77.json"
    "excerpt": "string",                  // optional, ≤300 words
    "owner_notes": "string"               // free‑form observation notes
  },
  "forbidden_fields": [
    "live_url",
    "retrieval_query",
    "generated_image",
    "external_tool_output"
  ],
  "observation_notes": "string",
  "hypothesis": "WESLR can reconstruct the ARC‑derived reasoning using a static packet without external calls.",
  "uncertainty_notes": "string",
  "failure_modes": [
    "packet_missing",
    "schema_mismatch",
    "unexpected_mutation_of_fields"
  ],
  "expected_output_type": "internal_report",
  "public_claim_warning": "This packet is for internal evaluation only; do NOT publish any claim of discovery."
}
```

*All fields must be present exactly as defined; any extra keys cause the packet to be rejected by the safety gate.*

---

## 6️⃣ Run Boundary Definition

| Aspect | Requirement |
|---|---|
| **Location** | Must be executed on the local OpenClaw host; no remote nodes.
| **Data** | Only the packet file created in `docs/` (or `evidence/`) may be read.
| **Authorization** | Manual approval by the project owner before the run is started (e.g., via a protected comment or checklist).
| **Autonomy** | The run is triggered manually; no self‑scheduling.
| **Public Exposure** | No output is exported outside the repo; the generated report stays in `docs/`.
| **Persistence** | The report is a regular file; no `.weslr` persistence mechanism is used.
| **External Calls** | Strictly forbidden – any attempt to call a provider, tool, or web endpoint must abort the run.
| **Final Answer Generation** | Disabled – the run only produces an *internal* analysis report, not a user‑visible answer.
| **Runtime Chat Wiring** | Not wired; the run is a pure function of the packet.

---

## 7️⃣ Expected Output (Internal Report Template)

```
# First Real‑Evidence Run – Internal Report

**Packet ID:** first_real_evidence_001
**Domain:** knowledge_replay

## Observed Patterns
- Pattern A: …
- Pattern B: …

## Candidate Gaps
- Gap 1: missing correlation between …
- Gap 2: insufficient granularity in …

## Possible Directions
1. Extend the packet with additional ARC‑derived sub‑steps.
2. Introduce a controlled owner‑workflow packet for cross‑validation.

## Contradictions
- None observed (expected for replay).

## Uncertainty List
- Uncertainty about the fidelity of the original ARC packet after repo migration.

## Evidence Insufficiency Warnings
- If any allowed field is empty, the run must flag the packet as _incomplete_.

## Next Evidence Needed
- A second independent replay packet from a different ARC lane to test reproducibility.

---
*No public claim is made. The report is intended for internal review only.*
```

---

## 8️⃣ Stop Conditions

The run must terminate **immediately** if any of the following conditions are met:
1. **Missing or unreadable packet file**.
2. **Schema validation failure** – any required field absent or a forbidden field present.
3. **Provenance unclear** – the `original_arc_packet_ref` does not resolve to a known ARC packet.
4. **Prompt‑injection risk** – the packet contains executable code fragments or suspicious prompts.
5. **Private/sensitive data** – detection of personal identifiers or credentials.
6. **Need for live retrieval** – the logic attempts to call `web_fetch`, `web_search`, `pdf`, etc.
7. **Tool / provider call** – any attempt to invoke an external model, image generation, video generation, etc.
8. **Result would become a public claim** – detection of phrasing like “we discovered” or “benchmark achieved”.

When a stop condition triggers, the runner must write a **failure report** stating the condition and abort further processing.

---

## 9️⃣ 2‑Step‑120 Requirement Prior to First Real‑Evidence Execution

- **Required now?** **No**.
- **Why not required:** The chosen direction (Known‑Science Replay) operates entirely on a static packet that was generated **during** the 2‑step‑120 synthetic phase. It does **not** need the full 2‑step‑120 pipeline to be re‑run; the required evidence is already present.
- **Signal that would later require 2‑step‑120:** When moving to directions that need *new* synthetic ARC generation (e.g., ARC‑like reasoning transfer with fresh synthetic evidence) or when attempting to create **new** real‑world sensor packets, the system must first guarantee that the 2‑step‑120 synthetic calibration is functional and reproducible.
- **Deferment decision:** The 2‑step‑120 build can be deferred until after the first design review and after a successful replay run, because the replay validates that the synthetic‑to‑real hand‑off can be performed without additional synthetic generation.

---

## 🔟 Smallest Next Implementation / Design Lane

**Recommended next lane:** **`create first real‑evidence packet schema`**

*Rationale:* The design already defines the exact JSON schema (Section 5). Implementing the schema as a validation helper (e.g., a `pydantic` model or JSON‑schema file) is the minimal concrete step before any run can be instantiated. It enables the safety gate to enforce the constraints defined here.

---

## Validation Checklist
- **`git diff --check`** – passes (no whitespace errors).
- **`python weslr/tests/release_gate_v1.py`** – PASS (already verified).
- **`./scripts/weslr_release_check.sh`** – PASS (no staged changes).
- **`./scripts/chat_weslr_de_health_check.sh --mode source-repo`** – PASS (repo health OK).

---

*Prepared by OCC – OpenClaw Coder.*
