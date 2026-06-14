# WESLR Local Metadata Locator Availability Repair V1

## 1. Purpose
Diagnose why the local metadata locator was unavailable during the third controlled true run.

## 2. Repo / branch / start HEAD
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `b2a268c7da09d1cc2a9170169250ab8870987275`

## 3. Blocked third-run context
The third controlled true run on `energy_systems` was blocked before metadata querying because the local metadata locator was unavailable.

## 4. Diagnostic commands run
- `grep -RIn "SearXNG|searxng|metadata locator|metadata_locator|127.0.0.1:8888|localhost:8888|:8888" docs weslr scripts 2>/dev/null | head -200`
- `curl -sS -o /tmp/weslr_searxng_127.json -w "%{http_code} %{time_total}
" "http://127.0.0.1:8888/search?format=json&q=test"`
- `curl -sS -o /tmp/weslr_searxng_localhost.json -w "%{http_code} %{time_total}
" "http://localhost:8888/search?format=json&q=test"`
- `command -v docker`
- `command -v podman`
- `command -v ss`
- `command -v netstat`
- `ss -ltnp | grep -E ':8888|:8080|:8880|searx'`
- `netstat -ltnp | grep -E ':8888|:8080|:8880|searx'`
- `docker ps --format 'table {{.ID}}	{{.Image}}	{{.Status}}	{{.Ports}}	{{.Names}}'`
- `podman ps --format 'table {{.ID}}	{{.Image}}	{{.Status}}	{{.Ports}}	{{.Names}}'`
- `env | grep -Ei 'SEARX|METADATA|LOCATOR|WESLR'`
- `find . -maxdepth 3 -type f \( -name ".env" -o -name ".example" -o -name "config" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" \) -print | sort | head -100`

## 5. Endpoint status results
- `127.0.0.1:8888`: unreachable from this Termux environment
- `localhost:8888`: unreachable from this Termux environment
- HTTP status: connection failed, no JSON payload inspected

## 6. Process/container diagnostics
- `docker`: not available on this host path
- `podman`: not available on this host path
- `ss`: available; no listener shown for `:8888`, `:8080`, `:8880`, or `searx`
- `netstat`: available; no listener shown for those ports
- no running container/service evidence was found from this Termux environment

## 7. Repo reference findings
Repo text references exist for SearXNG and metadata-locator boundaries, including MLCF SearXNG locator adapter docs and live-sample docs. No repo evidence here showed a Termux-local locator endpoint binding.

## 8. Environment/config findings without secrets
- Environment scan showed no visible `SEARX`, `METADATA`, `LOCATOR`, or `WESLR` locator-setting values in the shell output
- No obvious config file path surfaced in the limited file scan that proved a reachable local locator URL for this host
- The observed `127.0.0.1:8888` assumption appears host-local to a different environment, not this Termux namespace

## 9. Likely root cause
`network_namespace_mismatch`

## 10. Safe repair options
- confirm whether SearXNG is running on a separate Nova/Ubuntu host rather than Termux
- identify the correct host-local bridge or endpoint configuration for this environment
- add a small metadata-locator availability helper or config resolver in a future repo-only lane
- ask owner approval before starting/restarting any service

## 11. Recommended repair path
`CONFIGURE_WESLR_LOCAL_SEARXNG_ENDPOINT_FOR_TERMUX_V1` or `IMPLEMENT_WESLR_LOCAL_METADATA_LOCATOR_AVAILABILITY_HELPER_V1`, depending on whether the fix is endpoint mapping or helper abstraction

## 12. What not to do
- do not rerun the third true run yet
- do not start or restart services here without owner approval
- do not expose services publicly
- do not fetch or ingest source content
- do not change runtime/chat/UI/voice files

## 13. Owner approval requirements
Any service start/restart or bridge exposure needs explicit owner approval.

## 14. Validation results
- `git diff --check`: pass
- `python3 weslr/tests/release_gate_v1.py`: pass
- `bash scripts/weslr_release_check.sh`: pass

## 15. Protected-file status
Unchanged: `weslr/chat_responder.py`, `weslr/main.py`, `main.py`, `dialogue.py`, `chat_ui.py`.

## 16. Recommended next lane
`CONFIGURE_WESLR_LOCAL_SEARXNG_ENDPOINT_FOR_TERMUX_V1`

## 17. Final judgment
diagnostic_only_no_service_change
