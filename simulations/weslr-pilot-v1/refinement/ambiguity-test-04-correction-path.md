# Ambiguity Test 04: Partial User Correction After Wrong Inferred Direction

## User Persona
Lab technician — running quality control checks.

## Session Flow

**Turn 1**: User asks: "Check if batch 2026-042 passes QC"

**Turn 2**: Weslr checks file `batch-2026-042.csv` and finds:
- Parameter X: 1.05 (spec: 1.00 ± 0.05) → FAIL
- Parameter Y: 0.98 (spec: 1.00 ± 0.05) → PASS
- Weslr reports: "Batch 2026-042 fails QC — Parameter X out of spec"

**Turn 3**: User says: "Wait — the spec for Parameter X is actually 1.00 ± 0.10, not ±0.05"

## Expected Weslr Behavior

**Detection Phase:**
- Recognizes user is correcting a *specification* (not the raw data)
- Does NOT double-check the CSV (user trusts the measurement)
- Updates spec from ±0.05 to ±0.10

**Re-evaluation Phase:**
- Re-runs assessment with corrected spec
- Now: Parameter X = 1.05 is within 1.00 ± 0.10 → PASS
- Confirms: "With the corrected spec, batch 2026-042 passes QC"

**Continuity Phase:**
- Remembers the correction for future batches
- Could suggest: "Would you like me to update the QC spec template?"

## Test Criteria

- [ ] Detects user correction to *spec* (not measurement)
- [ ] Re-evaluates without re-checking raw data
- [ ] Reports corrected pass/fail status clearly
- [ ] Maintains continuity by remembering the correction
