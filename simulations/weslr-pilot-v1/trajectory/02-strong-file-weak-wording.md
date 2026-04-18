# Trajectory Test 02: Strong File Context + Weak Wording

## User Persona
University researcher running a long investigation — context lives in documents.

## Prompt (Weak)
> "what about this"

## File Context (Strong)
File: `/data/data/com.termux/files/home/.openclaw/workspace/simulations/weslr-pilot-v1/fixtures/research_notes_2026-04-05.md`

Content:
```markdown
# Research Log — Exoplanet Atmospheric Dynamics

## Target: Kepler-452b
- Radius: 1.6 Earth radii
- Orbital period: 385 days
- Star: G2-type (similar to Sun)

## Recent Observations (HST + JWST)
- HST (2026-03-28): Detected tentative water vapor signature at 1.4μm
- JWST (2026-04-01): CH4 detection at 3σ — possible biosignature candidate
- Current hypothesis: Photosynthetic activity possible if surface pressure > 1.2 bar

## Pending Analysis
- Need to reconcile HST and JWST transmission spectra
- Check for stellar contamination in CH4 band
- Compare with climate model outcomes from Team Alpha
```

## User Follow-up
> "what about this" — referring to the CH4 detection significance

## Expected Weslr Behavior
- Identify the most recent relevant content (CH4 detection at 3σ)
- Explain significance without assuming user knows statistical conventions
- Note the stellar contamination concern raised in the notes
- Offer to run reconciliation analysis or compare with Team Alpha's models

## Test Criteria
- [ ] Correctly identifies "this" as the CH4 detection
- [ ] Explains significance in accessible terms
- [ ] Notes caveats from the file context
- [ ] Offers concrete next steps without over-assuming
