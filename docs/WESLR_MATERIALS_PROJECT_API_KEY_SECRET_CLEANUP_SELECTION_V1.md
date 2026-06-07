# WESLR Materials Project API Key Secret Cleanup Selection V1

Date: 2026-06-07  
Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`  
Branch: `master`  
HEAD: `1c8909d`

## Final judgment

`weslr_materials_project_api_key_secret_cleanup_selected_ready_for_implementation`

## Scope check

This selection pass looked for materials-project secret hygiene only:

- API keys
- tokens
- secrets
- bearer tokens
- hardcoded credentials
- `.env`
- `API_KEY`
- `SECRET`
- `TOKEN`
- `Authorization`
- `Bearer`
- materials-related credential strings

## Result

No committed real Materials Project secret literal was found in the scanned repo surfaces.

The cleanup target is therefore:

1. env-var-based secret wiring that should stay secret-backed
2. docs-only secret guidance that should be kept accurate
3. any future unsafe placeholder or literal if introduced later

The Materials Project API implementation itself must be preserved.

## Commands run

- `git status --short`
- `git status --short --untracked-files=all`
- `git status --short --untracked-files=no`
- `grep -Rni "API_KEY\|SECRET\|TOKEN\|Authorization\|Bearer\|materials\|material" weslr docs scripts 2>/dev/null || true`
- `git diff --check`
- `python3 weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`

## Findings

| Finding type | File path | Symbol/function/class | Redacted evidence only | Recommended action | Key rotation needed? | Tests affected | Release-gate affected? |
|---|---|---|---|---|---|---|---|
| `safe_placeholder_no_action` | `weslr/modules/exhaustive_novelty_checker.py` | `MATERIALS_PROJECT_API_KEY`, `check_materials_project()`, `check_materials_project_thermodynamics()` | `MATERIALS_PROJECT_API_KEY = os.environ.get(...)`; `headers = {..., "x-api-key": api_key}`; `error: "no API key (set MATERIALS_PROJECT_API_KEY env var)"` | Preserve the generic adapter boundary; keep secret in env only; do not inline values | No | `weslr/tests/weslr/test_exhaustive_novelty_checker.py` | Yes, if code changes are made later |
| `docs_only_secret_warning` | `weslr/README.md` | Materials Project env-var table and frontier command docs | `MATERIALS_PROJECT_API_KEY`; `API key for Materials Project`; `if API key set` | Keep as operator guidance; if edited, keep wording secret-safe and non-public | No | None directly | No |
| `docs_only_secret_warning` | `docs/API_KEY_GREEN_ZONE_V1.md` | Secret-handling policy doc | `MATERIALS_PROJECT_API_KEY`; `secrets.MATERIALS_PROJECT_API_KEY`; `Do not echo it` | Preserve policy doc; align with any future cleanup, but do not remove the workflow pattern | No | None directly | No |
| `docs_only_secret_warning` | `docs/WESLR_MATERIALS_RESEARCH_WORKFLOW_V1.md` | Materials research workflow contract | `MATERIALS_PROJECT_API_KEY`; `do not be deployed into public production by default` | Preserve as governance guidance; update only if the materials lane changes | No | None directly | No |
| `no_secret_found` | `weslr/commands/frontier_commands.py` | `handle_frontier_novelty_exhaustive()` | `Materials Project`; `Heuristic (no MP API key)` | No code removal; keep source-agnostic output and generic fallback wording | No | None directly | No |
| `no_secret_found` | `scripts/expand_material_graph.py` | script entrypoints | materials-only graph expansion content; no secret-bearing literals found | No action | No | None directly | No |

## Selection notes

- I did **not** find a real committed Materials Project API key to redact.
- I did **not** select the Materials Project implementation for deletion.
- The generic external-API extension boundary should be preserved.
- If implementation work proceeds, it should focus on keeping credentials env-backed and documenting safe configuration, not removing the materials API lane.

## Verification

- `git diff --check`: pass
- `python3 weslr/tests/release_gate_v1.py`: pass
- `bash scripts/weslr_release_check.sh`: pass

## Recommended next lane

`IMPLEMENT_WESLR_MATERIALS_PROJECT_API_KEY_SECRET_CLEANUP_V1`
