# WESLR Official Benchmark Public Subset Readiness Map V1

**Status:** readiness doctrine for official-style evaluation plumbing  
**Date:** 2026-05-10  
**Scope:** provenance, schema, and reporting boundaries for future already-local public benchmark subsets  
**Implementation status:** metadata/schema only. No runtime download path. No official benchmark data included.

## 1. Purpose

WESLR-native sample suites are adapter checks. They exist to validate prompt formatting, label extraction, and bounded evaluation behavior.

Public-subset runs are different. They are internal evaluations over already-local public benchmark subsets that have been manually converted into WESLR's schema with provenance attached.

Official leaderboard scores are different again. They are governed by benchmark-specific rules, data handling, and submission procedures. They cannot be inferred from sample suites or internal public-subset runs.

## 2. Score classes

### Local sample score

A local sample score is produced from hand-written internal suites that exist only to test adapter infrastructure, prompt formatting, provenance plumbing, and bounded reasoning behavior.

It is **not** an external benchmark score.

### Internal public-subset score

An internal public-subset score is produced from a small already-local subset of public benchmark material that has been converted into WESLR's schema and annotated with strict provenance metadata.

It is useful for:
- failure analysis
- enrichment-gap discovery
- regression tracking
- route/format audits

It is **not** an official leaderboard score.

### Official leaderboard score

An official leaderboard score exists only when benchmark owners' rules, exact data conditions, and submission conditions are satisfied.

WESLR must not infer this score from:
- local sample suites
- internal public-subset runs
- converter outputs
- adapter behavior alone

## 3. Required boundaries

The following boundaries are mandatory:

- no official score claims
- no leaderboard language in internal eval outputs
- no benchmark answer memorization
- no hidden tuning to exact benchmark items
- no committed benchmark data unless the license explicitly allows it
- no internet/download path in runtime evaluation logic

These boundaries exist to preserve provenance, reduce contamination risk, and keep internal evaluation clearly separate from benchmark marketing or leaderboard signaling.

## 4. Public subset provenance

Each public-subset suite must include the following metadata:

- `dataset_name`
- `dataset_version`
- `dataset_source`
- `subset_name`
- `subset_size`
- `source_split`
- `license_note`
- `conversion_schema_version`
- `prompt_format_version`
- `adapter_version`
- `internal_eval: true`
- `sample_only: false`
- `official_score: false`

If these fields are absent, the suite is not ready to count as a public-subset internal evaluation.

## 5. Result metadata

Each run should output:

- `date_run`
- `repo_commit` if available
- `adapter_version`
- `suite_id`
- dataset metadata
- `official_score: false`
- `internal_eval: true` for public subsets
- `sample_only` flag
- selection method / failure mode

This metadata is required so later readers can distinguish:
- a local sample check
- an internal public-subset run
- an actual benchmark submission

## 6. Risk register

### Benchmark contamination

Heuristic improvements can drift into exact-item tuning if failure review is not separated from benchmark-item memorization.

### License terms

Public availability does not automatically permit redistribution inside the repository.

### Format mismatch

External benchmark formats may encode answers, splits, or metadata differently from WESLR's current schema.

### Tiny-subset overinterpretation

A small subset can exaggerate strength or weakness and should not be treated as broad benchmark readiness.

### Answer-choice leakage

Converters or prompt builders can accidentally reveal answer structure or ordering assumptions.

### Hardcoded heuristics

If WESLR grows exact benchmark-shaped phrase rules, internal evals stop measuring general capability and start measuring item leakage.

### Official score confusion

Internal public-subset results can be misread as official scores unless metadata and language are explicit.

## 7. Next allowed step

Only after this schema/provenance layer exists should WESLR:

- manually place an already-local converted public subset outside the repo or in an ignored/local path
- run an internal evaluation through the adapter
- record the result explicitly as non-official
- convert failures into enrichment gap records rather than benchmark-claim language

No benchmark download flow should be added to runtime. No official dataset should be bundled here by default.
