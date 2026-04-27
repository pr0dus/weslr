# ISS v1 Checkpoint — 2026-04-26

## Files Created

| File | Purpose |
|------|---------|
| `weslr/iss/probe_exec.py` | Run git/python/node commands, capture stdout/stderr/exit |
| `weslr/iss/evaluator.py` | Classify OK/DEGRADED/BROKEN from probe output |
| `weslr/iss/record.py` | Append evaluator result to JSONL log |
| `weslr/iss/report.py` | Deterministic human-readable text from evaluator JSON |

## Chain

```
probe_exec.py → evaluator.py → record.py → report.py
     (subprocess)    (classify)     (JSONL)      (text)
```

## Validation Status

- **probe_exec.py**: Returns structured JSON, overall_status OK confirmed
- **evaluator.py**: OK/BROKEN/DEGRADED paths all verified, recommended_next_step correct
- **record.py**: Appends to `memory/iss_records.jsonl`, 3 sample records written, 7 fields each
- **report.py**: All three states (OK/BROKEN/DEGRADED) produce correct deterministic text

## Known Limitation

`report.py` CLI accepts file path or JSON string argument only.
Pipe-to-stdin does not work due to argv-only parsing.
Use `--sample` or pass file path for CLI invocation.

## Next Recommended Step

ISS proposal layer — after checkpoint written.

Do not add new features before this checkpoint is confirmed.