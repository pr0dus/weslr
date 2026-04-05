# Trajectory Test 10: Long-Horizon Evolving Workflows

## User Persona
Drug discovery team lead — manages multi-month projects.

## Timeline
- **Month 1**: Screen 10,000 compounds against target protein
- **Month 2**: Validate top 100 hits with secondary assays
- **Month 3**: Optimize top 10 leads — add structural analogs
- **Month 4**: In vitro efficacy and toxicity profiling

## Current State
User: "let's look at the optimized leads — the ones from Month 3 with the methyl-substituted phenyl rings"

## Expected Weslr Behavior
- Understands "optimized leads" refers to Month 3 output
- Identifies structural motif (methyl-substituted phenyl rings)
- Pulls relevant compounds and their Month 4 in vitro data
- Provides summary across efficacy and toxicity endpoints

## Test Criteria
- [ ] Maps "Month 3 optimized leads" to correct output
- [ ] Identifies structural motif from description
- [ ] Retrieves associated Month 4 data
- [ ] Provides synthesized output across endpoints
