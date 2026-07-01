# DESIGN: First Real‑Evidence Packet Schema (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Start HEAD**: `399ed2eec2591b88ac5883f921c20d0cda699d70`
**Dispatch**: `CREATE_FIRST_REAL_EVIDENCE_PACKET_SCHEMA_V1`
**Selected Direction**: `Known‑Science Replay`

---

## Purpose
Define a strict, static‑only packet schema that governs the first controlled real‑evidence run for WESLR. The schema is expressed as immutable Python dataclasses with a lightweight validation helper and a focused pytest suite.

---

## Schema Overview
*File:* `weslr/real_evidence_packet_schema.py`

### Top‑Level Packet (`RealEvidencePacket`)
| Field | Type | Description | Boundary Enforcement |
|---|---|---|---|
| `packet_id` | `str` | Unique identifier for the packet. | — |
| `packet_version` | `str` | Schema version, e.g. `"v1.0"`. | — |
| `direction_id` | `str` | Identifier for the evidence direction. | — |
| `direction_type` | `Literal["known_science_replay", "owner_workflow", "synthetic_transfer"]` | Must be `"known_science_replay"` for this lane. | — |
| `domain` | `str` | Domain of the packet (e.g. `"knowledge_replay"`). | — |
| `evidence_source_type` | `Literal["known_science_replay", "owner_provided", "public_safe_copy"]` | Must be `"known_science_replay"`. | — |
| `source_provenance` | `str` | Provenance description (must be static/local). | Must **not** contain `web`, `github`, `rss`, `lab` substrings.
| `authorization_status` | `Literal["manual", "automated"]` | Must be `"manual"`. | — |
| `static_local_only` | `bool` | **True** – enforces static‑local requirement. | Must be `True`.
| `external_calls_allowed` | `bool` | **False** – no provider/model/tool calls. | Must be `False`.
| `persistence_allowed` | `bool` | **False** – `.weslr` persistence forbidden. | Must be `False`.
| `public_claim_allowed` | `bool` | **False** – no public claim generation. | Must be `False`.
| `evidence_items` | `List[EvidenceItem]` | Container for individual evidence entries. | Must contain at least one entry.
| `known_science_anchor` | `str` | Reference to the original ARC synthetic packet. | — |
| `hypothesis_or_direction_statement` | `str` | Describes the intended replay hypothesis. | — |
| `expected_replay_pattern` | `str` | Expected pattern (e.g., `"exact_match"`). | — |
| `allowed_reasoning_actions` | `List[str]` | Whitelisted reasoning actions (e.g., `"match"`). | — |
| `forbidden_reasoning_actions` | `List[str]` | Black‑list (must include `"model_call"`, `"web_fetch"`). | — |
| `uncertainty_notes` | `str` | Any remaining uncertainty. | — |
| `failure_modes` | `List[str]` | Enumerated failure conditions. | — |
| `stop_conditions` | `List[str]` | Conditions under which the run must abort. | — |
| `expected_output_type` | `Literal["internal_report", "metadata_summary"]` | Must be `"internal_report"`. | — |
| `no_public_claim_warning` | `str` | Warning text to be attached to reports. | — |
| `review_status` | `Literal["pending", "approved", "rejected"]` | Current review state. | — |

### Evidence Item (`EvidenceItem`)
| Field | Type | Description | Boundary Checks |
|---|---|---|---|
| `item_id` | `str` | Unique identifier for the item. | — |
| `item_type` | `Literal["text", "image", "audio", "binary", "structured"]` | Type of the item. | — |
| `content_summary` | `str` | Brief description of the content. | — |
| `source_reference` | `str` | Path or reference inside the repo. | Must **not** contain `web`, `github`, `rss`, `lab`.
| `provenance_status` | `Literal["author_provided", "public_copy", "synthetic_replay"]` | Provenance classification. | — |
| `allowed_use` | `Literal["internal", "review", "audit"]` | Permitted usage contexts. | — |
| `forbidden_use` | `Literal["public_claim", "benchmark", "persistence"]` | Disallowed usage contexts. | — |
| `injection_risk_notes` | `str` | Notes on any prompt‑injection risk. | — |
| `sensitive_data_status` | `Literal["none", "redacted", "confidential"]` | Sensitivity classification. | — |
| `uncertainty_notes` | `str` | Uncertainty specific to the item. | — |

---

## Boundary Encoding (explicitly enforced in `__post_init__`)
- **No live web / RSS / GitHub / lab‑notebook** – checks on `source_provenance` and each `EvidenceItem.source_reference`.
- **No provider/model calls** – `external_calls_allowed` forced to `False`.
- **No retrieval / tool execution** – same flag and absence of any `model_call` in `forbidden_reasoning_actions`.
- **No private/hidden data** – `sensitive_data_status` must be `"none"` unless explicitly redacted, and the validator asserts the field is present.
- **No `.weslr` writes** – `persistence_allowed` forced to `False`.
- **No database writes** – implicitly covered by persistence flag.
- **No runtime/chat wiring** – no fields for chat integration; schema is pure data.
- **No public / benchmark claims** – `public_claim_allowed` forced to `False` and `forbidden_use` includes `"public_claim"` and `"benchmark"`.
- **No final‑answer generation** – `expected_output_type` limited to internal report types.

---

## Validation Helper (`validate_packet`)
A thin wrapper that:
1. Converts each `evidence_items` dict into an immutable `EvidenceItem`.
2. Instantiates `RealEvidencePacket` – the dataclass `__post_init__` runs all boundary asserts.
3. Raises `RealEvidenceSchemaError` with a clear message on any violation.

---

## Tests (`weslr/tests/test_real_evidence_packet_schema.py`)
- **`test_valid_packet_passes_validation`** – builds a minimal conforming packet and asserts successful validation.
- **`test_invalid_packet_fails_on_web_provenance`** – injects a live‑web URL into `source_provenance` and expects a schema error.
- Additional pytest collection ensures the file is discovered by the release‑gate harness.

---

## Release‑Gate Allowance
Only files inside `weslr/` and the new test file are touched; they fall under the existing exact‑file release‑gate allowance. No other repo areas are modified.

---

## Validation Checklist
- **`py_compile`** – all new Python modules import cleanly.
- **Focused pytest** – passes (`pytest -q weslr/tests/test_real_evidence_packet_schema.py`).
- **`python weslr/tests/release_gate_v1.py`** – PASS (no new staged disallowed paths).
- **`git diff --check`** – PASS (no whitespace errors).
- **`./scripts/weslr_release_check.sh`** – PASS.
- **`./scripts/chat_weslr_de_health_check.sh --mode source-repo`** – PASS.

---

*Prepared by OCC – OpenClaw Coder.*
