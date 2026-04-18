# FRONT_DOOR_BRIDGE_CONTRACT_v1

Purpose: Define the minimal contract for a real front-door (chat/UI/API) bridge that routes human-facing ingress into WESLR’s core via weslr.ingress_adapter.route_request. No alternate logic; no governance or signal changes.

## 1) Bridge Purpose
- Provide one canonical human ingress (chat-first; voice can ride via STT/TT S) that normalizes raw UI/channel payloads and calls WESLR core through route_request.
- Preserve governed core: same request understanding, decision layer, governance, explanation, continuity.

## 2) Required Input Contract (from UI/channel)
- message/text (or transcript for voice)
- operator/channel identifier (user_id, channel_id)
- persona/domain if available (else defaults)
- summary mode or explanation overrides if available (optional)
- previous_decision if available (for deltas)
- optional channel metadata (surface-type, formatting hints)

## 3) WESLR Call Contract
- Call `weslr.ingress_adapter.route_request(raw_payload)`
- Normalized payload fields:
  - message
  - persona (default "general user")
  - domain (default "general")
  - previous_decision (optional, passed through)
  - explanation_overrides/mode (optional)
- route_request returns `Response(content, metadata, actions)` from WESLR core.

## 4) Output Contract (to UI/channel)
- Render Response.content to the user (respect channel formatting constraints).
- Optionally surface Response.actions if the channel supports actions.
- Safe metadata may be returned if channel can consume it (never alter truth/governance).

## 5) State Handoff Rule (minimal continuity)
- Bridge may cache/retrieve prior decision per operator/channel.
- When available, pass it as `previous_decision` in raw payload.
- If absent, call route_request without it. No deep persistence required initially.

## 6) Implementation Target Note
- To be implemented in the real ingress service (e.g., web backend/chat service/API gateway/OpenClaw-facing gateway). This repo does not contain that service; only the contract and core entrypoint exist here.

## 7) Success Criteria
- Any real front-door implementation calls route_request as the single path into WESLR.
- previous_decision flows when available to enable “Since last time” deltas.
- Operator sees the canonical contract-aligned output; governance unchanged.
