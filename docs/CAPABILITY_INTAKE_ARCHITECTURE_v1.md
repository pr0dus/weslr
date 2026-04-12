# CAPABILITY_INTAKE_ARCHITECTURE_v1

Purpose: Provide a governed, extensible intake layer so WESLR can safely receive, classify, and route diverse inputs/capabilities, while returning normalized outputs (evidence, confidence, provenance, uncertainty, decision-relevant findings) into the same core.

## 1) Purpose
- Support many input types (text, voice, docs, datasets, telemetry, images) without fragmenting core behavior.
- Ensure all capability handling routes through governed decision/explanation/continuity layers.
- Make extensibility explicit: new capability families can be proposed, classified, and integrated under governance.

## 2) Input Classes (examples, not exhaustive)
- Text/chat (messages, prompts)
- Voice/transcript (speech → text)
- Document/PDF (unstructured/semistructured text)
- Table/spreadsheet (CSV/TSV/XLSX)
- Chart/image/figure (raster or vector visuals)
- Dataset/scientific file (JSON, Parquet, NetCDF, FITS, etc.)
- Telemetry/log stream (operational signals, metrics, traces)
- Unknown structured artifact (any unfamiliar format)

## 3) Capability Classification
For each intake:
- Determine if core can handle directly (text/status queries, small evidence snippets).
- If not, route to an existing capability/tool (e.g., doc/text extraction, tabular ingestion, image→text, log/telemetry parser) when present.
- If extraction is needed first, run the extractor then feed normalized text/structured evidence into core.
- If unknown/unsupported, classify and propose: flag the type, suggest a bounded capability addition, await approval.

## 4) Same-Core Return Rule
All capability paths must return normalized outputs into the same WESLR core:
- Evidence payloads (text/snippets/structured summaries)
- Confidence/uncertainty signals
- Provenance (source, transformation steps)
- Decision-relevant findings (what matters, blockers, approvals, next actions) unchanged in contract
- No alternate truth per capability; governance/approvals unchanged.

## 5) Self-Assessment Link
- When repeated unsupported/unknown inputs appear, WESLR should signal a new capability family need, propose a minimal addition, explain value/risk, and await approval (see SELF_ASSESSMENT_DOCTRINE_v1).
- If an existing capability produces poor coverage/quality, surface an inadequacy signal with a proposal.

## 6) Anti-Fragmentation
- No per-capability divergence of operator truth or governance.
- Channel-agnostic: intake method (chat/voice/API/bridge) must still route through the same intake classification and core outputs.
- Extraction steps are preprocessing only; they do not change governance or decision semantics.

## 7) Success Criteria
- New inputs/capabilities can be added by classification + extraction + normalized return into core.
- Operators receive consistent, governed outputs regardless of input type.
- Unsupported inputs result in clear proposals, not silent failures or bypasses.
