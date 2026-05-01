# WESLR_SOURCE_TRUST_RANKING_V1_LIVE_ON_STAGING

**Date:** 2026-05-01 21:50 CEST
**Verdict:** `WESLR_SOURCE_TRUST_RANKING_V1_LIVE_ON_STAGING`

---

## Section 1 — Verdict

**`WESLR_SOURCE_TRUST_RANKING_V1_LIVE_ON_STAGING`**

Source Trust Ranking V1 is live and ordering search results by source quality on staging.weslr.de.

---

## Section 2 — Implementation

| Item | Value |
|------|-------|
| Module | `weslr/source_trust_ranking.py` |
| Integrated into | `weslr/evidence_packet_builder.py` |
| Test | `test_source_trust_ranking_v1.py` — 29 passed |
| Packet builder test | `test_evidence_packet_builder_v1.py` — 21 passed |
| Pipeline test | `test_evidence_pipeline_v1.py` — 14 passed |
| Chat bridge test | `test_evidence_chat_bridge_v1.py` — 23 passed |
| Commit | `5e74710` |

---

## Section 3 — Live Source Ordering (OCW Confirmed)

### Turn 3 — "What is entropy?"

Sources ordered by trust score (highest first):

| # | Domain | Type | Trust |
|---|--------|------|-------|
| 1 | wikipedia.org | reference | high |
| 2 | quantamagazine.org | news_magazine | high |
| 3 | merriam-webster.com | reference | high |
| 4 | reddit.com | forum | low |
| 5 | youtube.com | video | low |

### Turn 4 — "Explain entropy very deeply."

| # | Domain | Type | Trust |
|---|--------|------|-------|
| 1 | wikipedia.org | reference | high |
| 2 | quantamagazine.org | news_magazine | high |
| 3 | britannica.com | reference | high |
| 4 | reddit.com | forum | low |
| 5 | youtube.com | video | low |

Reference/academic sources are now consistently placed above forums and video platforms.

---

## Section 4 — Meaning

Source trust ranking:

- **Ranks** stronger reference/science/academic sources above forums/videos
- **Preserves** all sources — none deleted
- **Does not verify** truth — only orders by quality
- **Does not write** memory or JSONL
- **Does not change** `truth_status` — remains `unverified`
- **Does not change** `authority` — remains `external_evidence_unverified`

---

## Section 5 — Authority Boundary

| Property | Value | Confirmed |
|----------|-------|-----------|
| Authority | `external_evidence_unverified` | ✅ |
| Truth status | `unverified` | ✅ |
| automatic_truth_write | `false` | ✅ |
| Ranking is quality ordering, not truth verification | yes | ✅ |
| Reddit/YouTube demoted, not deleted | yes | ✅ |
| No Ollama | confirmed | ✅ |

---

## Section 6 — Guard Result

OCW confirmed self/system question still blocked after ranking integration:

- **Query:** "What is WESLR?"
- **Path:** `system_definition_query`
- **No evidence search triggered** — self/system guard preserved

---

## Section 7 — Remaining Weaknesses

| Weakness | Status |
|----------|--------|
| Citation display still raw | 🔵 Not surfaced in reply text |
| No cross-turn source memory | 🔵 Each query is independent |
| No source cross-validation | 🔵 Relies on SearXNG order + trust rank |
| No rate limiting / trusted tester guard | 🔵 Not implemented |
| No disabled-search user message | 🔵 Falls back silently |

---

## Section 8 — Next Recommended Step

**`WESLR_CITATION_DISPLAY_POLISH_V1`**

Purpose: Show source URLs and titles cleanly in user-visible reply text, not only in `_evidence_metadata`.

Current state: Sources are present in `_evidence_metadata.source_urls` but not formatted for user display.

Desired state: Evidence-grounded answers include a clean inline citation section or footnote-style list.

---

## Commit History

| Commit | Description |
|--------|-------------|
| `5e74710` | WESLR: add source trust ranking for evidence results |
| `8b6a87a` | WESLR: checkpoint external evidence chat live on staging |
| `a50c1e7` | WESLR: wire evidence bridge into staging demo server |
| `3e17a36` | WESLR: allow evidence bridge on generic explanation fallback |
| `9595f6f` | WESLR: allow evidence bridge on confirmed-answer fallback |