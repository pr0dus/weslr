# COGNITIVE_ADEQUACY_VALIDATION_SCENARIOS_v1

**Scope:** Doctrine-first validation scenarios for the Cognitive Adequacy Detection layer. No implementation. Defines testable situations where inadequate internal reasoning/proposal quality must be detected.

## SECTION 1 — SCENARIO FAMILIES
- Repetitive shallow proposals (same task class, minimal deltas).
- Repeated rejects / ignores (operator rejects/ignores proposals for a task class).
- Repeated low-confidence streaks (low confidence across consecutive proposals in a loop/task class).
- Same-fix loops (same fix proposed multiple times without acceptance/improvement).
- No improvement after multiple cycles (confidence/usefulness fails to improve across cycles).
- Evidence-to-action failure (evidence cited but no actionable path produced).

## SECTION 2 — PASS / FAIL EXPECTATIONS
- Repetitive shallow proposals: adequacy score lowers; reason cites repetitive shallow proposals; evidence references lineage ids and iteration counts; emit cognitive-improvement proposal.
- Repeated rejects/ignores: adequacy score lowers; reason cites low usefulness (reject/ignore rate); evidence references lineage status/audit; emit cognitive-improvement proposal.
- Low-confidence streaks: adequacy score lowers; reason cites repeated low confidence; evidence references confidence traces; emit cognitive-improvement proposal.
- Same-fix loops: adequacy score lowers; reason cites unaccepted repeated fix; evidence references lineage proposals; emit cognitive-improvement proposal.
- No improvement after cycles: adequacy score lowers; reason cites stagnant confidence/usefulness; evidence references trends; emit cognitive-improvement proposal.
- Evidence-to-action failure: adequacy score lowers; reason cites failure to translate evidence to action; evidence references proposals and signals; emit cognitive-improvement proposal.

## SECTION 3 — FALSE POSITIVE GUARDS
- Intentionally repeated operator-requested patterns (explicitly requested repetition) should NOT trigger inadequacy.
- Early low-sample loops (insufficient cycles/data) should NOT trigger; require minimum sample.
- Temporary low confidence during exploration (early exploratory passes) should NOT trigger if improving or within allowed exploratory budget.

## SECTION 4 — NEXT STEP
- Convert these scenarios into a test harness design for the adequacy detection layer (doctrine-first) before implementation.
