# WESLR API Key Green Zone V1

Date: 2026-05-08
Scope: external API keys used by WESLR workflows, starting with `MATERIALS_PROJECT_API_KEY`

## Purpose

This document defines when an API key may be used inside WESLR as a low-risk green-zone capability.
All examples below reference the secret name or env-var name only; never a real key value.

The immediate use case is the Materials Project API key for Scatti / CaSc2TiO6 research validation workflows.

## Green-zone definition

An API key is green-zone only when all of the following are true:

1. The key is stored as a GitHub Actions secret or equivalent protected runtime secret.
2. The key is never committed to the repository.
3. The key is never printed, logged, echoed, or included in generated artifacts.
4. The workflow using it is read-only.
5. The workflow does not mutate external services.
6. The workflow does not publish conclusions automatically.
7. The workflow output is labeled as screening / draft / validation support.
8. The workflow can run with a clear timeout and fail safely.
9. The workflow does not send private user data unless explicitly approved.
10. The workflow is scoped to a named task or manually triggered validation lane.

If any condition is false, the API key use is not green-zone and must be treated as yellow or red.

## Initial green-zone secret name

```text
MATERIALS_PROJECT_API_KEY
```

Allowed green-zone uses:

- read-only Materials Project formula lookup
- read-only Materials Project composition/system lookup
- read-only thermodynamic/stability metadata retrieval
- Scatti / CaSc2TiO6 novelty support checks
- manually triggered materials validation workflow
- cached or summarized screening report generation

Not allowed in green zone:

- printing the key
- committing the key
- uploading the key to artifacts
- using the key in a public frontend
- using the key from browser-side JavaScript
- automatic scientific publication
- automatic claims of discovery proof
- mutation of external accounts or services
- broad background scraping without task scope

## Recommended GitHub Actions pattern

Use the secret only inside the job environment:

```yaml
env:
  MATERIALS_PROJECT_API_KEY: ${{ secrets.MATERIALS_PROJECT_API_KEY }}
```

Do not echo it. Do not write it to files. Do not include it in logs.

Safe check pattern:

```bash
python - <<'PY'
import os
key = os.environ.get("MATERIALS_PROJECT_API_KEY")
if not key:
    raise SystemExit("MATERIALS_PROJECT_API_KEY is not configured")
print("Materials Project secret is configured")
PY
```

The output must confirm presence only, not reveal the key.

When documenting or testing this workflow, keep the literal value out of commits, logs, and artifacts.

## Materials / Scatti workflow stance

The Scatti workflow may use the key to support validation of CaSc2TiO6, but results must be framed correctly:

- database lookup result is evidence, not proof of novelty
- missing database entry is not proof that a compound has never existed
- screening stability or bandgap estimates are not final DFT validation
- generated reports must include limitations and confidence labels
- publication/export remains operator-reviewed

## Zone boundaries

### Green

Read-only, secret-backed, scoped, manually triggered or CI-scoped lookup that produces a draft validation artifact.

### Yellow

Any workflow that:

- combines API results with generated scientific claims
- writes persistent WESLR memory based on API output
- generates public-facing reports
- runs on a schedule
- processes customer/private data

Yellow-zone use requires explicit operator review before promotion or publication.

### Red

Any workflow that:

- exposes a key to browser/public code
- commits or logs a key
- mutates external accounts/services
- performs uncontrolled background querying
- publishes scientific claims automatically
- bypasses operator review

Red-zone use is blocked.

## CI rule

Default CI should not require external API keys.

A Materials/Scatti workflow should be a separate lane, preferably manual:

```yaml
on:
  workflow_dispatch:
```

This prevents ordinary PRs from failing because an external service is down, rate-limited, or missing credentials.

## Audit requirements

Any workflow using an API key must record:

- which secret name was used, not the secret value
- which endpoint family was queried
- query scope/formula/system
- timestamp
- success/failure
- whether output was draft/screening/operator-reviewed

## V1 conclusion

`MATERIALS_PROJECT_API_KEY` can be treated as green-zone only for read-only, scoped, secret-backed validation workflows.

It must not be used as a general runtime dependency, public frontend credential, or automatic publication authority.
