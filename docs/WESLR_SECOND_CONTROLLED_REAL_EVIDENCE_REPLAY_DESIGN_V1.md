# WESLR_SECOND_CONTROLLED_REAL_EVIDENCE_REPLAY_DESIGN_V1

**Lane**: `DESIGN_SECOND_CONTROLLED_REAL_EVIDENCE_REPLAY_V1`

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Start HEAD**: `8fbd8d18`

## Design Overview
The first static‑local Known‑Science Replay (anchor `arc_2step_80_anchor`) was successfully validated and replayed. The second replay will use a *different* known‑science anchor that is present in the repository, static‑local, and provides a distinct reasoning scenario.

## 1. Selected Second Anchor
**Anchor**: `arc_single_step_canonical_anchor`

- **Location**: `weslr/arc_synthetic_single_step_report.txt` (static synthetic report file already committed in the repository).
- **Description**: Represents the canonical ARC single‑step result with **114 exact**, **6 partial**, **0 unsupported**, **0 failed** matches. This is a *single‑step* reasoning outcome, contrasting with the *two‑step* nature of the first anchor.

## 2. Why It Is Meaningfully Different
- **Different reasoning depth**: The first anchor (`arc_2step_80_anchor`) captures a two‑step synthesis (combining multiple ARC runs). The selected anchor reflects a single reasoning step, testing the system’s ability to handle a simpler but still non‑trivial evidence chain.
- **Different evidence composition**: The single‑step report aggregates a broader set of ARC examples (114 exact matches) compared to the focused 80‑step synthetic subset.
- **Distinct failure surface**: Any mismatch between the expected exact‑match pattern and the observed evidence will surface different kinds of reasoning errors (e.g., aggregation vs. composition).

## 3. Expected Replay Pattern
- **Pattern**: `exact_match`
- The replay is expected to reproduce the exact counts (114 exact, 6 partial) reported in the anchor without deviation.

## 4. What Would Count as a Contradiction?
- Any deviation from the exact numbers (e.g., fewer exact matches, any partial mismatches beyond the documented 6).
- Presence of unexpected evidence items or missing required fields.
- Violation of the static‑local boundary (e.g., external calls, live‑web provenance).

## 5. Required Static‑Local Packet Fields
| Field | Value / Note |
|-------|--------------|
| `packet_id` | `second_real_evidence_known_science_replay_001` |
| `packet_version` | `v1.0` |
| `direction_id` | `direction_known_science_replay_002` |
| `direction_type` | `known_science_replay` |
| `domain` | `knowledge_replay` |
| `evidence_source_type` | `known_science_replay` |
| `source_provenance` | `local_static_arc_single_step_canonical` |
| `authorization_status` | `manual` |
| `static_local_only` | `true` |
| `external_calls_allowed` | `false` |
| `persistence_allowed` | `false` |
| `public_claim_allowed` | `false` |
| `evidence_items` | A single `EvidenceItem` referencing `weslr/arc_synthetic_single_step_report.txt` with appropriate metadata (same structure as first packet). |
| `known_science_anchor` | `arc_single_step_canonical_anchor` |
| `hypothesis_or_direction_statement` | `Replay the ARC single‑step canonical packet to verify static reasoning without external calls.` |
| `expected_replay_pattern` | `exact_match` |
| `allowed_reasoning_actions` | `["match", "compare", "audit"]` |
| `forbidden_reasoning_actions` | `["model_call", "web_fetch", "external_tool"]` |
| `uncertainty_notes` | `Minimal; static synthetic data.` |
| `failure_modes` | `["packet_missing", "schema_mismatch", "unexpected_mutation"]` |
| `stop_conditions` | `["external_call_requested", "live_source_detected", "public_claim_needed"]` |
| `expected_output_type` | `internal_report` |
| `no_public_claim_warning` | `Do not publish this packet as evidence; internal only.` |
| `review_status` | `pending` |

## 6. Stop Conditions Applied
- **`external_call_requested`** – abort if any code path attempts an external API or tool call.
- **`live_source_detected`** – abort if `source_provenance` references a live URL or contains `web`/`github`/`rss`/`lab`.
- **`public_claim_needed`** – abort if any step would require a public claim (the schema explicitly disallows this).
All three stop conditions will be evaluated in the replay’s `__post_init__` checks, mirroring the first replay.

## 7. What Remains Unproven Even If This Replay Passes?
- **Discovery Ability**: The system still has not demonstrated the ability to ingest or generate new evidence from live sources.
- **Dynamic/Multi‑Packet Reasoning**: Handling of mutable evidence, persistence, or coordination across multiple packets remains untested.
- **Public Claim Authority**: No proof of safe public claim generation.
- **Scalability**: Performance and correctness with larger or more complex evidence bundles are still unknown.
- **Generalization**: Ability to apply reasoning to domains beyond ARC synthetic reports has not been shown.

## 8. Next Steps After Design
1. **Create the packet** (`evidence/second_real_evidence_known_science_replay_001.json`) following the field table above.
2. **Run the controlled replay** using the same safe execution pipeline as the first.
3. **Review the replay** and, if successful, record it as the second internal milestone.
4. Consider expanding to a **third anchor** that tests a *shuffle‑invariance* property or a *known‑science replay design chain* to further diversify the evidence set.

---
*All design actions respect the static‑local boundary, avoid external calls, and produce only internal metadata reports.*