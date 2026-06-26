# WESLR ARC Controlled Improvement Evidence V1

## Status
Diagnostic evidence only. This records a controlled internal diagnostic → intervention → measurement loop for synthetic ARC solver work.

## What this layer records

- lane name
- baseline metrics
- intervention type
- after metrics
- delta metrics
- plain file / commit references
- evidence scope
- boundary flags
- non-claim flags
- validation status
- next-lane recommendation

## Recorded improvement chains

### Known-family improvement chain
- before primitive expansion: `14 / 6 / 28 / 0`
- after primitive expansion: `14 / 30 / 4 / 0`
- after partial-to-exact repair: `41 / 3 / 4 / 0`

### Held-out compositional improvement chain
- before depth-2 search: `1 / 2 / 11 / 0`
- after depth-2 search: `9 / 3 / 2 / 0`

## Boundary facts

This evidence layer is bounded to internal synthetic measurements and preserves the following controls:

- synthetic-only scope
- no external competition data contact
- no benchmark-example copying
- no answer-key exposure
- no provider/model dependency
- no ChatResponder/respond_chat dependency
- no website/runtime wiring
- no `.weslr` writes
- no public score claim
- no readiness claim beyond measured synthetic improvement

## Gap reading

The controlled loop shows:

- executor coverage improved first
- partial results were then converted to exact results
- held-out composition improved under bounded depth-2 search
- some held-out cases remain structurally unsupported under the current depth-2 primitive set
- the remaining gap still favors depth-2 repair before any deeper search change

## Next lane

Recommended next lane: `IMPLEMENT_ARC_DEPTH2_REMAINING_FAILURE_REPAIR_V1`

Fallback lane: `DESIGN_ARC_DEPTH3_SEARCH_BOUNDARY_V1`

## Non-goals

- no implementation in this doc layer
- no solver behavior change
- no external data ingestion
- no hidden authority claim
- no general-intelligence claim
