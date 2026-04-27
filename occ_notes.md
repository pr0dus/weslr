# OCC Notes — Disposable Debug Scratchpad

Purpose:
This file is for OCC debugging observations only.

Rules:
- NOT Weslr memory
- NOT doctrine
- NOT source of truth
- Delete-safe: Weslr must function if this file is removed
- Every entry must separate VERIFIED, ASSUMPTION, and NEXT CHECK

---

## Entry Template

OCC | YYYY-MM-DD HH:MM
VERIFIED:
- ...

ASSUMPTION:
- ...

NEXT CHECK:
- ...

---

OCC | 2026-04-24
VERIFIED:
- Active repo path: `/data/data/com.termux/files/home/.openclaw/workspace`
- `Path(__file__).resolve().parent / "weslr"` resolves to active workspace `weslr/`
- Clean baseline verified:
  - `weslr/entity_cooccurrence.json` has empty `pairs`
  - `weslr/relationship_proposals.json` has empty `proposals` and `proposed_pairs`
  - `weslr/proposal_stability.json` has empty `stability`
- M-layer functions importable/callable after live recovery:
  - `_record_cooccurrence`
  - `get_cooccurrence`
  - `generate_relationship_proposals`
  - `has_relationship_proposal`
  - `compute_proposal_stability`
  - `get_proposal_stability`
  - `get_proposal_stability_info`
  - `get_entity_cooccurrence_summary`
  - `list_proposals_by_classification`

ASSUMPTION:
- None.

NEXT CHECK:
- Continue part-by-part debugging from clean baseline before adding new behavior.