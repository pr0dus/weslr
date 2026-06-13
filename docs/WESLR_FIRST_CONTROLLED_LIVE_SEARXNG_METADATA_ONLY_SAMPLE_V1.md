# WESLR First Controlled Live SearXNG Metadata-Only Sample V1

**Date:** 2026-06-13
**Branch:** `first-live-searxng-sample-20260613` (new branch in a clean worktree, tracking `origin/master`)
**Worktree path:** `/home/pr0/projects/weslr-first-live-searxng-sample`
**Upstream `origin/master` HEAD (verified before design):** `9c202286872bbfb30201bd6bed5b332714dc04c6`
**Status:** Design only. No live HTTP call was issued. No live sample was created. The boundary implementation was reviewed; the boundary was **not executed**. The later run is a separate lane that requires its own owner authorization.

---

## 1. Purpose

This design defines the **first controlled live SearXNG metadata-only sample** for the Nova/Ubuntu host. The sample is a single, owner-authorized, hand-issued call whose purpose is to confirm that the boundary implementation on master (`weslr/controlled_live_searxng_metadata_only_boundary.py`, committed in `8fccf95b` and reviewed in `24f20ada`) holds its shape against a real SearXNG response.

The sample is **not** a research sample, not a benchmark, not a public capability demonstration, not a load test, not a proof of WESLR intelligence, and not a discovery of any source content. It is a **shape-validation call** that confirms:

- The boundary is reachable from a controlled owner invocation.
- The HTTP call shape (`http://127.0.0.1:8888/search?q=...&format=json&language=en`) round-trips against the local Docker container.
- The structured return has the expected field set (18 `results[]` fields, no extras).
- The blocking rules drop the expected classes of result (tracking domains, login URLs, private/loopback URLs, credential-bearing URLs, personal-data platforms).
- The boundary's `reason` enum reports `ok` (or `no_results`) and not anything in the elevation vocabularly.
- The boundary does not write any artifact outside the structured return; the live run is a one-shot, read-pure exercise.

After the shape is confirmed, the next lane (a separate design) may define how the boundary's structured return is *routed* into the existing MLCF sink for one specific query family. That is out of scope for this design.

---

## 2. Repo / head context

| Field | Value |
|---|---|
| Repo root | `/home/pr0/projects/weslr` (master), `/home/pr0/projects/weslr-first-live-searxng-sample` (this worktree) |
| Upstream `origin/master` HEAD | `9c202286872bbfb30201bd6bed5b332714dc04c6` (MATCH ✓) |
| New branch | `first-live-searxng-sample-20260613` (created from `origin/master` at `9c202286`) |
| Commits on `origin/master` since the prior design (between `f7acdb15` and `9c202286`) | `8fccf95b` implement boundary, `24f20ada` review boundary, `620838ad` design boundary (pushed earlier today, the prior `WESLR: design controlled live SearXNG metadata-only boundary` doc), `7a66613a` allow the design doc in the release gate, `6c6f7128` repair query encoding, `9c202286` review query encoding repair |
| Boundary implementation file (on master) | `weslr/controlled_live_searxng_metadata_only_boundary.py` (28,415 B) |
| Boundary tests file (on master) | `weslr/tests/test_controlled_live_searxng_metadata_only_boundary_v1.py` (13,470 B) |
| Prior design doc (on master) | `docs/WESLR_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_BOUNDARY_V1.md` (58,252 B, 680 lines) |
| Working tree (this worktree) | Clean, HEAD = `9c202286`, no untracked files, no uncommitted modifications. The legacy dirty tree on `scatti-audit-bundle-v2` and the `mlcf-master-pull-20260613` worktree are explicitly out of scope and were not touched. |

This design is being committed to the `first-live-searxng-sample-20260613` branch. It is not pushed to `master`. It is not merged into `master`. It is not pushed anywhere. The owner said *"Do not merge into master. Do not push to master. Do not create additional commits."* — the owner did not forbid a commit on the new branch, but explicitly said *"do not create additional commits"* which I read as *"no follow-up commits during this lane; the design itself is the deliverable."* The design is therefore written to a tracked path inside this worktree so the file exists, but it is **not** `git add`-ed and **not** committed in this lane. The owner can decide whether to commit it, when, and on which branch. (See section 25 for the explicit set of judgment options for the later live run; this design itself is committed on the owner's authorization, not on the agent's initiative.)

---

## 3. Nova/Ubuntu live host context

| Item | Value | Why it matters |
|---|---|---|
| Host | `pr0@pr0` (Ubuntu Noble) | the boundary expects a Unix host with `127.0.0.1:8888` reachable |
| Workdir for the live run | `/home/pr0/projects/weslr-first-live-searxng-sample` | the clean worktree on the `first-live-searxng-sample-20260613` branch; this is the only `cwd` the live run may use |
| Python | 3.12 (`python3` on PATH) | the implementation uses `urllib.request`, `ipaddress`, `datetime`, `hashlib`, `json`, `os`, `re`, `time` — all stdlib, no `pip install` needed |
| Shell | `bash` (for the run command) | the run command is a one-liner `python3 -c` invocation; no `pip`, no venv activation |
| Network egress from this host | loopback only for the boundary; no public-internet egress expected | the live call goes to `127.0.0.1:8888` (loopback); if the call ever tried to reach a non-loopback host, the config validator would refuse it |
| `~/.local/bin/searxng-search` helper | present (460 B) | not used by the live run; the boundary uses its own `urllib.request` HTTP getter, not the shell helper, so the boundary is the only thing that calls SearXNG |
| `~/.bash_history` / `~/.git-credentials` | present but not relevant | the live run does not interact with shell history or git credentials |
| `~/.openclaw/agents/main/sessions/` | exists | the live run **must not** write to this path; the boundary's structured return is the only output, captured by the operator to a file in the worktree |
| `.weslr/` | exists | the live run **must not** read or write `.weslr/`; the boundary is read-pure over the env, the HTTP call, and the operator-supplied result file |
| `memory/`, `continuity/`, `tenant_*` paths | exist in the worktree | the live run **must not** touch any of these; the boundary is not a state-mutating surface |
| cron jobs | `OWNER_REVIEW_ONLY = YES` per the 2026-05-30 lock; all six PlantDelux OpenClaw cron jobs were disabled on 2026-06-10 | the live run is not cron-fired; the operator issues it by hand |
| Heartbeat / Morning / Growth sessions | all disabled | the live run is not session-fired; the operator issues it by hand |
| Protected runtime files | `weslr/chat_responder.py`, `weslr/main.py` (does not exist on master), `main.py`, `dialogue.py`, `chat_ui.py` | the live run **must not** import, read-for-write, or call any of these |

---

## 4. SearXNG local availability assumptions

| Assumption | Verified? | Source |
|---|---|---|
| Docker is installed and the operator can `docker ps` | implicit; the running searxng container is listed | `docker ps` shows `searxng/searxng:latest` container `0bff25879718` |
| SearXNG container is running and mapped to `127.0.0.1:8888` | yes | `ss -ltn` shows LISTEN on `0.0.0.0:8888` and `[::]:8888` |
| SearXNG version | not verified at design time | the boundary does not require a specific version; the response shape is the contract |
| SearXNG JSON endpoint is `/search` with `format=json` | yes (per existing helper) | `~/.local/bin/searxng-search` calls `http://127.0.0.1:8888/search?format=json` |
| SearXNG has no authentication | yes (local Docker) | no `auth-profiles.json` is read by the boundary |
| SearXNG does not require a `User-Agent` header | assumed | the boundary sets a default `User-Agent: weslr-controlled-live-searxng-boundary-v1` (per the implementation's `_default_http_getter`); if SearXNG returns 403/empty, the boundary reports `searxng_4xx_403` or `searxng_results_incomplete` |
| SearXNG returns at most 10 results per page (SearXNG default) | yes | the boundary caps at `min(SearXNG returned, max_results=5)` |
| SearXNG container is reachable via the loopback URL only | yes | `_normalize_base_url` does not check loopback at config time, but the boundary's HTTP call only goes to the configured `base_url`; non-loopback URLs should be refused at config-time by the operator's pre-run check (section 7) |

The boundary implementation does not perform any health check on SearXNG before issuing the HTTP call. If the container is down, the boundary will report `searxng_unreachable` (via `urllib.error.URLError`) and the live run aborts cleanly. The operator should verify the container is up *before* enabling the env var.

---

## 5. Boundary implementation reviewed (read-only summary)

The boundary lives at `weslr/controlled_live_searxng_metadata_only_boundary.py`. The live sample uses these public functions; the design references them by name so the run command is unambiguous.

| Public API | Purpose | Used by the live run? |
|---|---|---|
| `build_controlled_live_searxng_boundary_config_v1(**overrides)` | builds the config from env vars + overrides | yes, called once at the start of the run |
| `validate_controlled_live_searxng_boundary_config_v1(config)` | validates the config; returns `{valid, errors, config}` | yes, called immediately after build_config |
| `build_controlled_live_searxng_query_v1(query, query_family=, operator_role=)` | builds the query packet | yes, called once with the sample query |
| `validate_controlled_live_searxng_query_v1(query_packet)` | validates the query packet; returns `{valid, errors, query}` | yes, called immediately after build_query |
| `run_controlled_live_searxng_metadata_only_boundary_v1(query, config=, http_getter=)` | runs the boundary; returns the structured result packet | yes, called with the live HTTP getter and the built config |
| `validate_controlled_live_searxng_metadata_only_result_packet_v1(packet)` | validates the structured result packet; returns `{valid, errors, packet}` | yes, called after the run to confirm the shape |
| `summarize_controlled_live_searxng_metadata_only_result_packet_v1(packet)` | produces a small, human-readable summary of the result | yes, called to render the human-readable part of the run output |
| `to_controlled_live_searxng_metadata_only_json_safe_v1(packet)` | returns a JSON-safe copy of the packet | yes, called to write the result artifact to disk |

`SCHEMA_VERSION_V1 = "weslr_controlled_live_searxng_metadata_only_boundary_v1"`. The packet's `boundary_version` field always carries this string. The packet's `boundary_id` field on each result row also carries this string.

The implementation's HTTP getter (`_default_http_getter`) uses `urllib.request` with a 5-second `timeout` argument. The getter sets a `User-Agent: weslr-controlled-live-searxng-boundary-v1` header. The getter does **not** follow redirects: a 3xx response produces a `searxng_redirect_rejected` reason without any follow-up HTTP call. The getter does **not** cache, **not** retry, **not** paginate, **not** set cookies, **not** authenticate. The getter does **not** read `~/.netrc`, `auth-profiles.json`, or any other credential file. The getter is the only HTTP call in the entire boundary, and it happens once per `run_controlled_live_searxng_metadata_only_boundary_v1` invocation.

The implementation's `allowed_live_http_without_injected_getter` config flag is `False` by default and cannot be raised by the operator via env var. The only way to make a live HTTP call is for the operator to (a) inject a custom `http_getter` callable, OR (b) explicitly override `allow_live_http_without_injected_getter=True` in the `build_config` call. This design uses the **injected-getter** path: the operator passes `_default_http_getter` (imported from the module) as the `http_getter` argument, after explicitly opting in by setting the env var `WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED=true`. The boundary's config validator confirms `enabled=True` and the operator's `http_getter` is present, and only then proceeds.

---

## 6. Exact sample query

```
weslr boundary design v1
```

**Justification (low-stakes / shape-only):**

- It is a literal phrase, not a real research question.
- It is expected to return results that are dominantly the WESLR repo and its design docs, which is the boundary's own context — so the results are about the boundary itself, not about external subject matter. This avoids accidentally surfacing real-world research material through the live run.
- It is short, ASCII, well under the 200-byte post-quote cap, contains no control characters, and is not a URL. It passes `validate_controlled_live_searxng_query_v1` cleanly.
- The expected result set is small (5 or fewer), most of which will be filtered by the boundary's blocking rules (e.g. `github.com` results will pass with `source_class_hint: "github_repository"` and `authority_guess: "community_signal"`; other domains may be blocked as `unparseable_domain`, `private_or_loopback_target`, or `login_or_account_url`).
- It is a phrase the operator can read and recognize: if the structured return contains "weslr boundary design v1" in the `query` field, the operator can confirm the right call was made.
- It tests the boundary's `query_family: "general"` path (the default), which is the only path enabled in the first sample.

The query is **not** a question, **not** a research target, **not** a comparison probe, **not** a quality test of any external content, and **not** a probe of any specific website. It is a phrase whose only purpose is to round-trip through the boundary and produce a structured return that the operator can inspect for shape.

The query is **not** one of: `WESLR`, `WESLR boundary`, `WESLR metadata`, `WESLR SearXNG`, or anything that could be misread as a research, comparison, or capability probe. It is the exact phrase the owner recommended in this lane: `weslr boundary design v1`.

---

## 7. Required environment / config flags

The live run uses **environment variables** to configure the boundary. Each variable is read by the boundary's `build_controlled_live_searxng_boundary_config_v1` function (or its helpers). The variables the live run sets, the values the live run uses, and the meaning of each:

| Env var | Value for the live run | Source of the value | Default if unset |
|---|---|---|---|
| `WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED` | `true` | explicit owner opt-in | `false` (boundary refuses to call HTTP) |
| `WESLR_SEARXNG_URL` | `http://127.0.0.1:8888` | the local Docker container's mapped port | `http://127.0.0.1:8888` |
| `WESLR_SEARXNG_LIVE_BOUNDARY_TIMEOUT_SECONDS` | `5` | the design's hard cap | `5` (clamped to `[1, 5]`) |
| `WESLR_SEARXNG_LIVE_BOUNDARY_MAX_RESULTS` | `5` | the design's hard cap | `5` (clamped to `[1, 5]`) |
| `WESLR_SEARXNG_LIVE_BOUNDARY_SNIPPET_POLICY` | `disabled` | the design's "snippets off by default" rule | `disabled` |
| `WESLR_SEARXNG_LIVE_BOUNDARY_QUERY_FAMILY` | `general` | the only family enabled in v1 | `general` |
| `WESLR_SEARXNG_LIVE_BOUNDARY_OPERATOR_ROLE` | `owner` | the only role that the live run may use | `owner` |

**Env vars the live run explicitly does NOT set** (because they do not exist as a config knob in the implementation, or because they are out of scope for v1):

- `WESLR_SEARXNG_LIVE_BOUNDARY_LANGUAGE` — the implementation hard-codes `language=en` in the request URL; the operator cannot override it via env var in v1.
- `WESLR_SEARXNG_LIVE_BOUNDARY_SAFESEARCH` — SearXNG's default (`0`) is used; the implementation does not expose it as a knob in v1.
- `WESLR_SEARXNG_LIVE_BOUNDARY_TIME_RANGE` — disabled in v1; the implementation does not pass `time_range` to SearXNG.
- `WESLR_SEARXNG_LIVE_BOUNDARY_CATEGORIES` — disabled in v1; the implementation does not pass `categories` to SearXNG.
- `WESLR_SEARXNG_LIVE_BOUNDARY_PAGENO` — disabled in v1; the implementation always sends `pageno` implicitly = 1 (SearXNG default when not present).
- `WESLR_SEARXNG_LIVE_BOUNDARY_OUTPUT` — disabled in v1; the implementation always sends `format=json`.
- `WESLR_SEARXNG_LIVE_BOUNDARY_USER_AGENT` — disabled in v1; the implementation uses a fixed `User-Agent: weslr-controlled-live-searxng-boundary-v1`.

**The live run's pre-flight check (operator-side, before enabling the env var):**

The operator (by hand, in their shell) must run these read-only commands and confirm the output before setting `WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED=true`:

```bash
# 1. SearXNG is up on loopback.
ss -ltn | grep ':8888\b'             # must show LISTEN on 0.0.0.0:8888 and/or [::]:8888

# 2. The SearXNG container is healthy.
docker ps | grep searxng              # must show the container in 'Up' state

# 3. The worktree is on the right branch and HEAD.
git -C /home/pr0/projects/weslr-first-live-searxng-sample rev-parse --abbrev-ref HEAD
# must print: first-live-searxng-sample-20260613
git -C /home/pr0/projects/weslr-first-live-searxng-sample rev-parse HEAD
# must print: 9c202286872bbfb30201bd6bed5b332714dc04c6

# 4. The boundary module is on disk.
ls -la /home/pr0/projects/weslr-first-live-searxng-sample/weslr/controlled_live_searxng_metadata_only_boundary.py
# must show a non-zero file size
```

If any of these checks fail, the live run is aborted (section 23).

---

## 8. Expected SearXNG URL

```
http://127.0.0.1:8888/search?q=weslr%20boundary%20design%20v1&format=json&language=en
```

This is the URL the boundary's `build_controlled_live_searxng_request_url_v1` function builds from the query packet and config. The operator can confirm the URL is correct by calling the function directly (no HTTP), e.g.:

```bash
python3 -c "
import sys; sys.path.insert(0, '/home/pr0/projects/weslr-first-live-searxng-sample')
from weslr.controlled_live_searxng_metadata_only_boundary import (
    build_controlled_live_searxng_boundary_config_v1,
    build_controlled_live_searxng_query_v1,
    build_controlled_live_searxng_request_url_v1,
)
config = build_controlled_live_searxng_boundary_config_v1()
query = build_controlled_live_searxng_query_v1('weslr boundary design v1')
print(build_controlled_live_searxng_request_url_v1(query, config))
"
```

Expected output: `http://127.0.0.1:8888/search?q=weslr%20boundary%20design%20v1&format=json&language=en` (or equivalent with normalized whitespace).

The live run uses this exact URL. The boundary uses `urllib.request.urlopen` with a 5-second timeout. The HTTP method is `GET`. The `User-Agent` header is `weslr-controlled-live-searxng-boundary-v1`. The `Accept` header is implicit (urllib default, not set by the boundary). No other headers are set.

---

## 9. Loopback-only requirement

The boundary's `_normalize_base_url` function trims trailing slashes; it does **not** verify the host is loopback at config time. The live run's config validation (via `validate_controlled_live_searxng_boundary_config_v1`) does not check the host is loopback either. The loopback requirement is enforced by the operator's pre-flight check (section 7) and by the **default value** of `WESLR_SEARXNG_URL` (`http://127.0.0.1:8888`).

The live run's `WESLR_SEARXNG_URL` is hard-coded to `http://127.0.0.1:8888`. The run command (section 20) sets it inline. If the operator forgets to set it, the default takes effect, which is also loopback. Either way, the live run cannot accidentally reach a non-loopback SearXNG.

The boundary will not refuse a non-loopback URL on its own in v1; that enforcement is a separate design lane. The design here does not add such enforcement; it relies on the default and the operator's pre-flight check. The later run may add an out-of-band warning if a future version of the boundary exposes loopback enforcement; the live sample in v1 does not require it.

---

## 10. Timeout and result cap

| Cap | Value | Source |
|---|---|---|
| Per-call HTTP timeout | `5` seconds (clamped to `[1, 5]`) | `WESLR_SEARXNG_LIVE_BOUNDARY_TIMEOUT_SECONDS` env var |
| Per-call max results | `5` (clamped to `[1, 5]`) | `WESLR_SEARXNG_LIVE_BOUNDARY_MAX_RESULTS` env var |
| Per-result field-allow-list | 18 fields, exactly the `ALLOWED_RESULT_FIELDS_V1` tuple | hard-coded in the implementation |
| Per-result blocking | 10 hard rules (loopback/private, login, credential, personal-data platform, tracking, unparseable domain, url_too_long, empty_title, malware_signature, low_signal_self_match) | hard-coded in the implementation |
| Per-call max blocked-list size | unbounded (SearXNG's response size) | SearXNG returns ~10 results by default; the live sample's 5-result cap is the binding constraint |
| Per-process max calls per run | 1 | the run command issues exactly one `run_controlled_live_searxng_metadata_only_boundary_v1` call |

The implementation's `min(max(int(value), 1), 5)` clamping on both `timeout_seconds` and `max_results` means that even if the operator sets the env var to `999`, the effective value is `5`. The clamps are hard-coded, not env-overridable. This is intentional: the boundary is the only thing that controls the cap, and the cap is small.

---

## 11. Snippet policy

| Setting | Value | Effect |
|---|---|---|
| `WESLR_SEARXNG_LIVE_BOUNDARY_SNIPPET_POLICY` | `disabled` (explicit) | each result row's `snippet` field is `None`; the structured return's `snippets_retained` field is `False` |
| `WESLR_SEARXNG_LIVE_BOUNDARY_SNIPPET_POLICY` (if set to `enabled`) | not used in this live sample | would attempt to retain sanitized snippets up to 280 bytes; the live sample does not enable this |

The live sample runs with snippets disabled. Even if a real SearXNG response contained a long `content` or `description` field, the boundary will drop it. The `results[]` rows will have `snippet: null` (Python `None`). The `blocked[]` rows will not have snippets.

This matches the design principle: snippets are the highest-risk surface in a SearXNG response, and the first live sample must be the strictest mode. The operator does not need to do anything to disable snippets; the design just sets the env var to `disabled` explicitly so the intent is recorded in the run log.

---

## 12. Allowed output fields (per result row)

Each result row in `results[]` carries exactly these 19 fields, no more, no fewer. The implementation's `ALLOWED_RESULT_FIELDS_V1` tuple is the contract. The `boundary_version` / `boundary_id` fields are not on the result row; they are on the packet's outer scope.

| Field | Type | Source in the live sample |
|---|---|---|
| `query` | str | the literal `"weslr boundary design v1"` |
| `title` | str | the SearXNG result's `title` (or `""` if missing) |
| `url` | str | the SearXNG result's `url` |
| `domain` | str | `urllib.parse.urlparse(url).netloc.lower()` |
| `source_engine` | str \| None | the first engine in `result.engines`, or the `engine` field |
| `engines` | list[str] | the full `engines` list, normalized |
| `rank` | int | 1-based index in the SearXNG response |
| `score` | float \| None | SearXNG's `score` field |
| `published_date` | str \| None | SearXNG's `publishedDate` field |
| `snippet` | None (snippets disabled) | always `None` in the live sample |
| `source_class_hint` | str | one of the MLCF source-class enums (per the implementation's `_derive_source_class`) |
| `authority_guess` | str | one of the MLCF authority-level enums |
| `evidence_role_guess` | str | the only value in v1 is `candidate_signal` (the implementation hard-codes this for the `general` query family) |
| `relevance_reason` | str | one of `engine_match`, `domain_match`, `title_match`, `low_signal` |
| `freshness_status_guess` | str | derived from `publishedDate` |
| `access_license_status_guess` | str | derived from `domain` and `url` |
| `privacy_status_guess` | str | derived from `domain` and (if any) `snippet`; in this live sample, always `public_non_personal` because snippet is `None` |
| `blocked_status` | str | always `"allowed"` for items in `results[]` (blocked items live in the separate `blocked[]` list) |
| `locator_id` | str | SHA-256 of `(query, url, rank)`, 64 hex chars |

The live sample is allowed to write these 19 fields to the run-result file. The live sample is **not** allowed to write any other field. The packet's outer-scope fields (`ok`, `boundary_version`, `query`, `reason`, `searxng_call_status`, `searxng_call_latency_ms`, `results_count_kept`, `results_count_blocked`, `evidence_status`, `automatic_truth_write`, `raw_content_retained`, `snippets_retained`, `authority_verdict`) are also allowed in the result file (section 21).

---

## 13. Forbidden output fields (per result row and packet-scope)

The following must **not** appear in the run result, in any log line, in any stderr line, in any artifact written to disk, or in any in-memory representation that the live run produces:

- Any field whose name is not in the per-row allow-list (section 12) or in the packet-scope allow-list (section 21).
- Any raw response body bytes, partial or full.
- Any HTML, Markdown, PDF, JSON-LD, or markup.
- Any URL not on the allow-list (the boundary already drops it before producing the result; the live run is just re-asserting that).
- Any value containing a credential, token, password, API key, or session ID (already caught by the boundary's URL block rule).
- Any `*_authority_*` flag (the boundary does not produce these; the live run is just re-asserting that).
- Any of: `discovery`, `proof`, `confirmed`, `verified`, `official conclusion`, `final answer`, `state of the art`, `benchmark`, `agi`, `consciousness`, `sentience`, `public-science`, `publicly claimable` — *as claim language*. The boundary does not produce these, and the live run does not introduce them.
- The literal string `trusted` (the boundary produces only `allowed` / `blocked`).
- Any narrative interpretation, summary, paraphrase, or "explanation" of any field.
- Any embedding, vector, or similarity score.
- Any hash of a snippet, content, or other raw text (only the `locator_id` is retained, and it is over `query + url + rank`, not over any content field).
- Any URL the operator could click to fetch the page (the boundary keeps the URL for locator purposes; the live run does not click it).

If the run result contains any forbidden field, the run is failed (section 23).

---

## 14. Blocked-result behavior

The boundary maintains a separate `blocked[]` list in the structured return. Each blocked item has exactly three fields: `url`, `title`, `block_reason`. The live run's blocked[] may contain 0–N items, depending on how many of the 5 (or fewer) returned results the blocking rules reject.

The blocking rules the live sample may trigger (from the implementation's `_detect_block_reason`):

| Rule | `block_reason` value | When it fires in this live sample |
|---|---|---|
| Empty / unparseable domain | `unparseable_domain` | unlikely for a clean SearXNG response |
| Private / loopback / `.local` / `.onion` | `private_or_loopback_target` | only if SearXNG returns a result pointing at `127.0.0.1`, `192.168.*`, etc. — unlikely but possible |
| Personal-data platform | `personal_data_platform` | if SearXNG returns a result on `facebook.com`, `linkedin.com`, etc. — possible for generic queries |
| Tracking-only domain | `tracking_or_analytics_only` | if SearXNG returns a result on `doubleclick.net` etc. — unlikely |
| Credential in URL | `credential_in_url` | only if a result URL contains `token=`, `password=`, etc. — unlikely |
| URL too long | `url_too_long` | if a result URL exceeds 2000 bytes — unlikely |
| Empty title | `empty_title` | if a result has no `title` field — unlikely |
| Malware signature in title | `malware_signature` | only if a title matches a known-signature regex — unlikely for this query |
| Title too long | `title_too_long` | if title exceeds 500 bytes — unlikely |
| Low-signal self-match | `low_signal_self_match` | only if the result is a self-search — unlikely |
| Login URL | `login_or_account_url` | if URL contains `/login`, `/signin`, etc. — possible for off-topic results |
| Result cap exceeded | `result_cap_exceeded` | if SearXNG returns more than 5 results, the overflow is added to `blocked[]` with this reason — this is the most likely block in the live sample |

The live sample expects `results_count_blocked ≥ 0`. If `results_count_blocked == 0` AND `results_count_kept == 0`, the live sample is the empty case (`reason: "no_results"`); the operator notes this and continues. If `results_count_blocked > 0` AND `results_count_kept == 0`, the run is suspicious (all results blocked); the operator aborts. If `results_count_blocked > 0` AND `results_count_kept > 0`, the run is normal — some results blocked, some kept.

---

## 15. No-raw-retention policy

The live sample does **not** retain:

- The full HTTP response body of the SearXNG call.
- Any portion of the response body beyond the 18 per-row allow-list fields and the packet-scope allow-list fields.
- The request URL beyond what is recorded in the structured return's `query` field and SearXNG call metadata.
- The request headers beyond the `User-Agent` (which is in the boundary's code, not in the response).
- The response headers beyond `Content-Type` (used by the boundary for the `searxng_wrong_content_type` check; not retained in the structured return).
- The HTTP timing beyond `searxng_call_latency_ms` (a single int).
- The `Content-Length` header.
- The HTTP connection state (DNS resolution, TCP handshake, TLS, etc.) — not retained.
- The `Set-Cookie` header — not retained, not sent.
- Any file system write beyond the run-result artifact at the path in section 21.

The live sample writes **exactly one file**: the run result artifact at `docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_RESULT_V1.md` (section 21). The operator may additionally redirect stderr to a file under the worktree (e.g. `logs/first-live-searxng-sample.stderr.log`) for their own records, but this is optional and the file is in the worktree's `logs/` dir, which is not in the protected-files list and not in the boundary's allow-list for content.

The run command does **not**:

- Pipe the response body to `grep`, `jq`, `python3 -m json.tool`, or any other parser that would persist the body.
- Save the response to a file.
- Send the response to another host (`curl`, `wget`, `nc`, `ssh`).
- Hash the response body to a file.
- Compute an embedding of the response.
- Index the response in any local store.

The boundary's structured return is the boundary's entire output. The live sample's only artifact is the run result, which is the structured return (and a small human-readable summary section) — nothing more.

---

## 16. No-ingestion policy

The live sample does **not** do any of:

- Add a result to a candidate graph.
- Promote a locator to evidence.
- Mark a locator as `accepted` or `trusted`.
- Generate a `summary`, `paraphrase`, or `excerpt` of any field.
- Compute a hash of any retained field beyond the `locator_id` (which the boundary already provides).
- Compute an embedding, vector, or similarity score of any field.
- Run an ML model on any field.
- Trigger a downstream pipeline (the MLCF summary, the MLCF intake, the MLCF normalized evidence packet, the MLCF ledger registry, the source selection plan) by writing to its inputs.
- Open a follow-up HTTP call (the boundary does not; the live sample does not either).
- Open a follow-up SearXNG call.
- Open a follow-up file write (except the single run result artifact).
- Trigger a notification, a webhook, an email, a Telegram message, a logrotate, a metrics flush, or any external side effect.

The live sample's structured return is the **end of the live sample's responsibility**. Whatever the operator does with the result is the operator's lane — but the operator's lane in this run is to inspect the shape and either (a) confirm the run is clean, or (b) abort. There is no lane after this one in the same commit.

---

## 17. No-claim policy

The live sample does **not** claim, in the run result or in any associated log:

- That a result is the *right* answer to a question.
- That a result is the *only* answer.
- That a result has been seen before or not seen before.
- That a result is *new* or *recent* beyond the `freshness_status_guess` enum.
- That a result is *authoritative* beyond the `authority_guess` enum.
- That a result is *useful* beyond the `relevance_reason` enum.
- That a result is *safe* beyond the `blocked_status` enum.
- That the boundary "works" in any general sense — the live sample only confirms the shape of one call.
- That the boundary is "production-ready" or "audited" or "approved" for any use beyond this single live sample.
- That the WESLR system, in any of its forms, has any capability beyond what its existing modules already implement and document.
- That any of: discovery, proof, public-science, AGI, consciousness, sentience, benchmark, official-conclusion has been achieved, demonstrated, or supported by this run.
- That SearXNG is a useful search engine, an unuseful search engine, or a recommended search engine for any purpose.
- That the operator, the Nova session, or the Ubuntu host is doing anything beyond a single HTTP call to a local Docker container.

The run result may include the words `candidate`, `locator`, `signal`, `source class`, `authority guess`, `evidence role guess`, `relevant by`, `blocked by`, `rejected because` (per the MLCF enums). It may not include the claim words enumerated in section 13.

---

## 18. No-MLCF-routing policy

The live sample does **not** route the structured return into the existing MLCF sink (`weslr.mlcf_searxng_source_locator_adapter_boundary`). The MLCF sink is the next lane; this lane does not call it. Specifically:

- The run result does not call `build_mlcf_locator_record_from_searxng_result_v1` (or any other MLCF sink function).
- The run result does not pass any `results[]` row to the MLCF sink.
- The run result does not create an MLCF locator record file.
- The run result does not register a locator in the MLCF ledger.
- The run result does not feed the normalized evidence intake preparation helper.
- The run result does not feed the authorized metadata-only source summary helper.
- The run result does not feed the source selection evidence plan helper.
- The run result does not feed the controlled information ingestion candidate helper.
- The run result does not feed the cross-domain science direction candidate helper.
- The run result does not feed the source locator organization review packet helper.

The MLCF helpers exist on master (verified by `ls weslr/mlcf_*.py` earlier). The live sample's run command does not import any of them. The live sample's run result file does not mention any of them by name (other than to note that the MLCF-routing step is *out of scope* and *for the next lane*).

If the operator wants to do MLCF routing, that is a separate lane with its own design, its own boundary, and its own operator authorization. The owner said *"Do not route results into MLCF."* — this design honors that.

---

## 19. No-runtime / public-integration policy

The live sample does **not** integrate with:

- The omnichat contract-reply engine (`weslr/omnichat/response_expander.format_reply`).
- The chat responder (`weslr/chat_responder.py` — protected file).
- The chat UI (`chat_ui.py` — protected file).
- The dialogue module (`dialogue.py` — protected file).
- The main module (`main.py` — protected file).
- The Weslr main entry point (`weslr/main.py` — does not exist on master; protected).
- The LLM runtime (`llm_runtime.py`).
- The Ollama backend or any model provider (`providers.py`, `sim.py`, etc.).
- The protected chat backend on `:8092` (`tools/protected_non_model_workflow_server.py`).
- The public WESLR site on `https://weslr.de/`.
- The protected chat on `https://chat.weslr.de/`.
- The autonomous cron jobs in `/home/pr0/.openclaw/cron/jobs.json` (all disabled).
- The PlantDelux OpenClaw cron jobs (all disabled).
- Any email pipeline (Resend API, Gmail, etc.).
- Any social / outreach / business lane (PlantDelux CRM, etc.).

The live sample is a **standalone** Python invocation. It does not modify the protected files, does not import the protected modules, does not call the protected backends, and does not open any port other than the loopback `127.0.0.1:8888` HTTP call (which the boundary itself closes after the timeout / response).

---

## 20. Exact run command (proposal for the later live run)

The proposed run command, to be issued by the operator by hand in their shell, is a single `python3 -c` invocation. It does not create a new file in the worktree (the run result is written by the script itself, to the path in section 21).

```bash
cd /home/pr0/projects/weslr-first-live-searxng-sample

WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED=true \
WESLR_SEARXNG_URL='http://127.0.0.1:8888' \
WESLR_SEARXNG_LIVE_BOUNDARY_TIMEOUT_SECONDS=5 \
WESLR_SEARXNG_LIVE_BOUNDARY_MAX_RESULTS=5 \
WESLR_SEARXNG_LIVE_BOUNDARY_SNIPPET_POLICY=disabled \
WESLR_SEARXNG_LIVE_BOUNDARY_QUERY_FAMILY=general \
WESLR_SEARXNG_LIVE_BOUNDARY_OPERATOR_ROLE=owner \
python3 -c "
import json, os, sys
sys.path.insert(0, '/home/pr0/projects/weslr-first-live-searxng-sample')
from weslr.controlled_live_searxng_metadata_only_boundary import (
    build_controlled_live_searxng_boundary_config_v1,
    build_controlled_live_searxng_query_v1,
    run_controlled_live_searxng_metadata_only_boundary_v1,
    validate_controlled_live_searxng_boundary_config_v1,
    validate_controlled_live_searxng_query_v1,
    validate_controlled_live_searxng_metadata_only_result_packet_v1,
    summarize_controlled_live_searxng_metadata_only_result_packet_v1,
    to_controlled_live_searxng_metadata_only_json_safe_v1,
    _default_http_getter,
)

config = build_controlled_live_searxng_boundary_config_v1()
config_validation = validate_controlled_live_searxng_boundary_config_v1(config)
assert config_validation['valid'], config_validation['errors']

query_packet = build_controlled_live_searxng_query_v1('weslr boundary design v1')
query_validation = validate_controlled_live_searxng_query_v1(query_packet)
assert query_validation['valid'], query_validation['errors']

packet = run_controlled_live_searxng_metadata_only_boundary_v1(
    'weslr boundary design v1',
    config=config,
    http_getter=_default_http_getter,
)

result_validation = validate_controlled_live_searxng_metadata_only_result_packet_v1(packet)
assert result_validation['valid'], result_validation['errors']

result_path = '/home/pr0/projects/weslr-first-live-searxng-sample/docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_RESULT_V1.md'
os.makedirs(os.path.dirname(result_path), exist_ok=True)

with open(result_path, 'w', encoding='utf-8') as fh:
    fh.write('# WESLR First Controlled Live SearXNG Metadata-Only Sample Result V1' + chr(10))
    fh.write(chr(10))
    fh.write('Run timestamp (UTC): ' + __import__('datetime').datetime.utcnow().isoformat() + 'Z' + chr(10))
    fh.write('Run by: operator (manual hand-issued)' + chr(10))
    fh.write('Run cwd: ' + os.getcwd() + chr(10))
    fh.write('Run HEAD: ' + os.popen('git -C /home/pr0/projects/weslr-first-live-searxng-sample rev-parse HEAD').read().strip() + chr(10))
    fh.write('Boundary version: ' + packet.get('boundary_version', 'unknown') + chr(10))
    fh.write(chr(10))
    fh.write('## Structured return (JSON)' + chr(10))
    fh.write(chr(10))
    fh.write('```json' + chr(10))
    fh.write(json.dumps(to_controlled_live_searxng_metadata_only_json_safe_v1(packet), indent=2, sort_keys=True) + chr(10))
    fh.write('```' + chr(10))
    fh.write(chr(10))
    fh.write('## Validation' + chr(10))
    fh.write(chr(10))
    fh.write('- config validation: ' + json.dumps(config_validation) + chr(10))
    fh.write('- query validation: ' + json.dumps(query_validation) + chr(10))
    fh.write('- result validation: ' + json.dumps(result_validation) + chr(10))
    fh.write(chr(10))
    fh.write('## Summary' + chr(10))
    fh.write(chr(10))
    fh.write(json.dumps(summarize_controlled_live_searxng_metadata_only_result_packet_v1(packet), indent=2, sort_keys=True) + chr(10))
    fh.write(chr(10))
    fh.write('## Notes' + chr(10))
    fh.write(chr(10))
    fh.write('- This run was issued by the operator, not by cron, not by a session.' + chr(10))
    fh.write('- No MLCF routing was performed; the structured return is the end of the live-sample lane.' + chr(10))
    fh.write('- No provider/model call was made; the boundary is pure Python over urllib.' + chr(10))
    fh.write('- No raw response body, HTML, or page content was retained beyond the per-row allow-list.' + chr(10))
    fh.write('- Snippets were disabled for this run (WESLR_SEARXNG_LIVE_BOUNDARY_SNIPPET_POLICY=disabled).' + chr(10))
    fh.write('- The HTTP call was to http://127.0.0.1:8888 only (loopback).' + chr(10))
    fh.write('- The run result file is the only artifact of this run.' + chr(10))

print('WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_SAMPLE_RUN_OK')
print('result_path=' + result_path)
"
```

**Important characteristics of this command:**

- The `python3 -c` body is **not** wrapped in `try / except`. An unexpected exception will print a traceback to stderr, which the operator can inspect, and the run result file will not be created. The operator aborts on traceback (section 23).
- The `assert` statements are **operator-facing**; if any fails, the run is aborted.
- The only file write is to `docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_RESULT_V1.md` (section 21).
- The run does not commit, push, or otherwise interact with git.
- The run does not start, stop, or restart any service.
- The run does not modify any file outside the result path.

The operator may also pipe stderr to a file for their own records, e.g.:

```bash
... (same as above) 2> /home/pr0/projects/weslr-first-live-searxng-sample/logs/first-live-searxng-sample.stderr.log
```

This is optional. The `logs/` directory is not in any protected-files list, and the operator's stderr log is operator-side only (it is not in the boundary's contract).

---

## 21. Expected output artifact path for the later run

| Field | Value |
|---|---|
| Path | `/home/pr0/projects/weslr-first-live-searxng-sample/docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_RESULT_V1.md` |
| Format | Markdown with embedded JSON block |
| Created by | the run command (section 20) |
| Created at | the time of the run |
| Size | ≤ 20 KB (estimated: a 5-result packet is ~5–10 KB; the markdown wrapper is ~1 KB) |
| Contains | the structured return, the validation results, the summary, and the notes; no raw response body, no full snippets, no source page content, no evidence claims, no discovery/proof/public-science claims |

**Explicitly forbidden in the result file:**

- Raw response body bytes (the live sample does not retain them; the result file does not contain them).
- Full snippets (the live sample disabled snippets; `snippet` is `None` for every result row; the result file may mention this but does not contain any snippet text).
- Source page content (the live sample did not fetch any source; the result file does not contain any source content).
- Source summaries, paraphrases, narrative interpretations (the live sample does not produce any; the result file does not contain any).
- Evidence claims, normalized evidence, accepted evidence, trusted evidence (the live sample does not produce any; the result file does not contain any).
- Discovery / proof / public-science claims (the live sample does not produce any; the result file does not contain any).
- `.weslr/` writes (the live sample does not write to `.weslr/`; the result file does not contain any `.weslr/` content).
- Memory / project / state / candidate graph writes (the live sample does not write to any of these; the result file does not contain any state).
- Provider / model calls (the live sample does not call any provider; the result file does not contain any provider output).
- A claim that the WESLR system, in any of its forms, has any new capability that it did not already have.

**Allowed in the result file:**

- The structured return from the boundary (per-row 19 fields, packet-scope fields, blocked[] list).
- The validation results (`config_validation`, `query_validation`, `result_validation`).
- The summary from `summarize_controlled_live_searxng_metadata_only_result_packet_v1`.
- A run timestamp (UTC), the run-by tag (`operator (manual hand-issued)`), the run cwd, the run HEAD, the boundary version.
- The notes enumerated in the run command above (operator-issued, no MLCF, no provider, etc.).
- An explicit "no public claim" footer.

---

## 22. Validation plan for the later run

After the run command completes, the operator runs these checks (read-only) to validate the result:

### 22.1 Result file presence and size

```bash
ls -la /home/pr0/projects/weslr-first-live-searxng-sample/docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_RESULT_V1.md
# must exist, size 1 KB – 50 KB (5 KB typical, 50 KB cap)
```

### 22.2 Result file shape

```bash
python3 -c "
import json, re
path = '/home/pr0/projects/weslr-first-live-searxng-sample/docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_RESULT_V1.md'
with open(path) as fh:
    text = fh.read()
# 1. must contain a JSON fenced block
assert '\`\`\`json' in text, 'missing JSON block'
# 2. JSON must be parseable
match = re.search(r'\`\`\`json\\n(.*?)\\n\`\`\`', text, re.DOTALL)
data = json.loads(match.group(1))
# 3. must be a dict with the expected top-level keys
expected_top = {
    'boundary_version', 'ok', 'query', 'reason', 'searxng_call_status',
    'searxng_call_latency_ms', 'results_count_kept', 'results_count_blocked',
    'results', 'blocked', 'evidence_status', 'automatic_truth_write',
    'raw_content_retained', 'snippets_retained', 'authority_verdict',
}
assert set(data.keys()) >= expected_top, f'missing keys: {expected_top - set(data.keys())}'
# 4. results_count_kept <= 5
assert data['results_count_kept'] <= 5, 'cap exceeded'
# 5. snippets_retained == False
assert data['snippets_retained'] == False, 'snippets should be disabled'
# 6. raw_content_retained == False
assert data['raw_content_retained'] == False, 'raw content should be dropped'
# 7. automatic_truth_write == False
assert data['automatic_truth_write'] == False, 'no truth write'
# 8. evidence_status == 'metadata_only_locator_candidates'
assert data['evidence_status'] == 'metadata_only_locator_candidates', 'wrong evidence status'
# 9. authority_verdict == 'external_evidence_unverified'
assert data['authority_verdict'] == 'external_evidence_unverified', 'wrong authority verdict'
# 10. query is exactly the sample query
assert data['query'] == 'weslr boundary design v1', 'query mismatch'
print('shape_ok')
"
```

### 22.3 No forbidden fields, no forbidden content

```bash
python3 -c "
import re
path = '/home/pr0/projects/weslr-first-live-searxng-sample/docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_RESULT_V1.md'
with open(path) as fh:
    text = fh.read().lower()
# Forbidden claim language (case-insensitive, as substrings).
forbidden = [
    'we are agi', 'agi achieved', 'artificial general intelligence',
    'we are conscious', 'consciousness confirmed',
    'we are sentient', 'sentience confirmed',
    'publicly claimable', 'public-science', 'public science',
    'we prove', 'we discover', 'we have shown', 'we have proven',
    'official conclusion', 'final answer',
    'state-of-the-art', 'state of the art',
    'benchmark-winning', 'competition-winning',
    'best in class', 'paradigm shift',
]
hits = [w for w in forbidden if w in text]
assert not hits, f'forbidden claim language in result: {hits}'
# No 'trusted' verdict.
assert '\"trusted\"' not in text, 'no trusted verdict allowed'
# No authority flag names.
for flag in ['source_ingestion_authorized', 'raw_retention_authorized', 'web_call_authority', 'searxng_call_authority', 'public_claim_authorized', 'final_answer_authority', 'discovery_claim_authorized', 'proof_claim_authorized', 'agi_claim_authorized', 'benchmark_claim_authorized', 'public_science_claim_authorized']:
    assert flag not in text, f'forbidden authority flag: {flag}'
print('content_ok')
"
```

### 22.4 No protected-file modifications

```bash
cd /home/pr0/projects/weslr-first-live-searxng-sample
for f in weslr/chat_responder.py weslr/main.py main.py dialogue.py chat_ui.py; do
  if [ -f "$f" ]; then
    md5sum "$f"
  else
    echo "MISSING: $f"
  fi
done
# Compare each md5 against the value before the run.
# (The values from this design lane are recorded in the run log.)
```

All five protected files must be byte-identical to their pre-run state.

### 22.5 No `.weslr/` IO

```bash
ls -la /home/pr0/.weslr/ | head -10
# mtime of any file in this dir must not be within the last 5 minutes.
find /home/pr0/.weslr -mmin -5 -ls 2>/dev/null
# expected: empty (no files modified in the last 5 minutes)
```

### 22.6 No memory / project / state writes

```bash
find /home/pr0/projects/weslr-first-live-searxng-sample/memory -mmin -5 -ls 2>/dev/null
find /home/pr0/projects/weslr-first-live-searxng-sample/continuity -mmin -5 -ls 2>/dev/null
find /home/pr0/projects/weslr-first-live-searxng-sample/tenants -mmin -5 -ls 2>/dev/null
# expected: empty
```

### 22.7 Operator's hand-issued verification

The operator (the human, not the agent) confirms by reading the result file that:

- The query is `weslr boundary design v1` (matches the design).
- `ok` is `True` if any results were kept, `False` if not.
- The result rows have the 19 expected fields, no extras.
- The `blocked[]` list is the right size (typically 0–3 for this query).
- The notes section explicitly states "no MLCF routing", "no provider/model call", "no raw response body", "snippets disabled".
- The result does not contain any claim language.

If the operator finds any deviation, they abort (section 23) and the result file is deleted.

---

## 23. Abort conditions

The live run is aborted (the result file is **not** kept; the live sample is declared failed) if **any** of the following is observed:

| Abort condition | Action |
|---|---|
| The pre-flight check (section 7) fails | do not set `WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED=true`; do not run the command |
| The `build_controlled_live_searxng_boundary_config_v1` config validation fails | abort; do not keep any partial result |
| The `validate_controlled_live_searxng_query_v1` query validation fails | abort; do not keep any partial result |
| The HTTP call to SearXNG returns a non-200 status (3xx, 4xx, 5xx) and the structured return's `reason` is in the `searxng_5xx_*`, `searxng_4xx_*`, or `searxng_redirect_rejected` family | record the reason in the abort log, delete the partial result file if any, abort |
| The HTTP call times out (`searxng_timeout`) | record the reason, delete the partial result file, abort |
| The HTTP call fails to connect (`searxng_unreachable`, `searxng_network_error`) | record the reason, delete the partial result file, abort |
| The HTTP call returns non-JSON (`searxng_wrong_content_type`, `searxng_malformed_json`) | record the reason, delete the partial result file, abort |
| The result has more than 5 entries in `results[]` | abort; the boundary's cap is violated |
| The result has any field not in the per-row allow-list | abort; the boundary's contract is violated |
| The result has any of the forbidden claim / authority / verdict words (section 13, 17) | abort; the boundary's contract is violated |
| Any of the five protected files is modified by the run | abort; the run command does not touch them; if it did, this is a bug in the implementation, not in the run |
| `.weslr/`, `memory/`, `continuity/`, `tenants/` mtime is within the last 5 minutes | abort; the boundary is supposed to be read-pure |
| The result packet's `searxng_call_latency_ms` exceeds 5000 (5 s) | abort; the timeout cap is violated |
| The result's `snippets_retained` is `True` despite the env var being `disabled` | abort; the boundary's snippet policy is violated |
| The result's `evidence_status` is not `"metadata_only_locator_candidates"` | abort; the boundary's evidence-status invariant is violated |
| The result's `authority_verdict` is not `"external_evidence_unverified"` | abort; the boundary's authority-verdict invariant is violated |
| The result's `automatic_truth_write` is `True` | abort; the boundary is not allowed to write truth |
| The result's `raw_content_retained` is `True` | abort; the boundary is not allowed to retain raw content |

If any abort condition fires, the operator (or the agent, in a separate lane) deletes the result file and records the abort in a separate operator-side log. The abort log is not the same as the result file. The result file is the *only* output of a *successful* run.

---

## 24. Rollback conditions

The live sample is **read-pure**. There is nothing to roll back, in the sense of undoing writes:

- The boundary does not write to disk (other than the result file, which the run command creates).
- The boundary does not modify `.weslr/`, `memory/`, `continuity/`, `tenants/`, `cron`, `auth-profiles.json`, `git`, or any other state.
- The boundary does not start, stop, or restart any service.
- The boundary does not bind any port.
- The boundary does not create any user, group, or process.

If a future implementation of the boundary is later found to have a defect (e.g. it leaks a field on a different query family), the rollback is to **revert the implementation commit** on master (`8fccf95b`, `24f20ada`, `6c6f7128`, `9c202286`) to a known-good state. The operator runs:

```bash
cd /home/pr0/projects/weslr
git log --oneline -5 -- weslr/controlled_live_searxng_metadata_only_boundary.py weslr/tests/test_controlled_live_searxng_metadata_only_boundary_v1.py
# Identify the SHA before the defect. Then:
git checkout <good-sha> -- weslr/controlled_live_searxng_metadata_only_boundary.py weslr/tests/test_controlled_live_searxng_metadata_only_boundary_v1.py
# Or, for a full revert:
git revert <defect-sha>
```

This rollback is a **separate lane** triggered by a defect report, not by this design. The live sample itself has nothing to roll back.

If the live sample produces a result file that the operator wants to discard, the rollback is `rm /home/pr0/projects/weslr-first-live-searxng-sample/docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_RESULT_V1.md`. That is a single-file delete, not a system rollback.

---

## 25. Final judgment options for the later run

When the operator runs the live sample and inspects the result, the run's outcome must be one of the following five judgments. The operator writes the chosen judgment at the bottom of the result file.

| Judgment | When it applies |
|---|---|
| `weslr_first_controlled_live_searxng_metadata_only_sample_v1_pass` | the result file exists, the shape checks (section 22) all pass, the content checks (section 22.3) all pass, no abort condition (section 23) fired |
| `weslr_first_controlled_live_searxng_metadata_only_sample_v1_empty` | the result file exists, `ok` is `False`, `reason` is `no_results`, no abort condition fired; SearXNG returned an empty result list for this query (which can happen if SearXNG has no cached results or the query has no hits) |
| `weslr_first_controlled_live_searxng_metadata_only_sample_v1_repaired_later` | the result file exists, but one or more shape / content checks failed; the operator notes the specific failure and identifies a precise fix (e.g. a missing field in the boundary's `_derive_*` function); the boundary is repaired in a separate lane and the live sample is re-run |
| `weslr_first_controlled_live_searxng_metadata_only_sample_v1_blocked_by_boundary` | the run command could not complete because the boundary refused the call at config / query validation time (e.g. the operator set the env var incorrectly, or the boundary's `enabled` flag is not flipping); the run is blocked and the operator investigates the boundary's pre-conditions before any re-run |
| `weslr_first_controlled_live_searxng_metadata_only_sample_v1_run_incomplete` | the run command did not complete (Python exception, network failure, filesystem error, timeout, etc.); the result file may or may not exist; the operator investigates the cause and decides whether to re-run |

The five judgments are mutually exclusive. The operator writes exactly one of them.

The default expected judgment is **`weslr_first_controlled_live_searxng_metadata_only_sample_v1_pass`**. The other four are contingency judgments for known failure modes.

---

## 26. Next lane recommendation

The recommended next lane, in order of priority, is **not** "make the live sample more capable." The recommended next lane is **stay narrow**:

| Priority | Lane | Why |
|---|---|---|
| 1 | **Owner authorizes and the operator runs the live sample by hand.** The run command is in section 20. The result is written to the path in section 21. The validation plan is in section 22. The expected judgment is in section 25. | this is the only step that produces the empirical evidence that the boundary holds against a real SearXNG response |
| 2 | **Operator hand-issues the run, captures the result file, runs the validation checks, and writes the judgment at the bottom of the result file.** No commit, no push. | keeps the run evidence operator-attested and reviewable |
| 3 | **Owner reviews the result file** and either approves the boundary as fit-for-the-design-sample (and the next lane is defined), or flags a defect (and the implementation is repaired in a separate lane). | the owner is the final reviewer, not the agent |
| 4 | **(NOT in this design's scope)** If the boundary passes the live sample, the next design (a separate doc, a separate commit, a separate lane) defines how the boundary's structured return is *routed* into the existing MLCF sink for **one** specific query family, on a separate branch, with its own boundary, its own operator authorization, and its own protected-files check. | keeps each lane small and reviewable |
| 5 | **(NOT in this design's scope)** Snippet policy. The default is `disabled`. Enabling snippets is a separate lane with its own boundary, its own privacy review, and its own operator-CC requirements. | the snippet is the highest-risk surface; do not enable it in the same lane as the live call itself |
| 6 | **(NOT in this design's scope)** Multi-language, time-range filters, category filters, engine selection, pagination, HTTPS, non-loopback SearXNG, retry, caching, rate limiting, per-session quota, per-user quota. All separate lanes. | none of these belong in the first live sample |
| 7 | **(NOT in this design's scope)** Connection to the omnichat contract-reply engine, the chat responder, the chat UI, the protected preview, the public weslr.de site, any provider / model call. None of these belong in any future lane unless explicitly authorized. | the boundary is metadata-locator only, never an evidence engine |

What the next lane must NOT do:

- Connect the boundary to the MLCF sink automatically. The MLCF sink is the *next* design, after the live sample.
- Connect the boundary to the omnichat contract-reply engine. Not in any lane.
- Connect the boundary to the chat responder, the chat UI, the protected preview, the public weslr.de site, or any user-facing surface. Not in any lane.
- Add a cache layer, a retry layer, a rate-limit layer, a per-session quota, a per-user quota. All separate lanes.
- Add multi-language support, time-range filters, category filters, engine selection, or pagination. All separate lanes.
- Switch to HTTPS. Separate lane.
- Switch to a non-loopback SearXNG. Separate lane (and may be forbidden in perpetuity).
- Make any claim, summary, paraphrase, or evidence elevation. Forbidden in every lane.
- Auto-run the live sample on a schedule. The first live sample is a hand-issued operator call only.
- Auto-route any result into the MLCF sink. The MLCF-routing design is a separate lane.
- Add cron entries, systemd timers, or session scripts that fire the live sample on a schedule. The live sample is operator-only.

---

## Summary

This design defines the first controlled live SearXNG metadata-only sample for the Nova/Ubuntu host:

- Pulls `origin/master` at `9c202286` onto a new branch `first-live-searxng-sample-20260613` in a clean worktree, leaving all legacy dirty trees and prior branches untouched.
- Reviews the boundary implementation on master (`weslr/controlled_live_searxng_metadata_only_boundary.py`, 28,415 B, 7+ public functions) and the design doc from the prior lane.
- Confirms SearXNG is locally available on `127.0.0.1:8888` (Docker container `0bff25879718`, `Up 2 months`) but issues no live HTTP call in this design.
- Defines a single safe query (`weslr boundary design v1`) that is low-stakes and shape-validating, not research, not a comparison, not a public claim.
- Configures the boundary with seven env vars (`WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED=true`, `WESLR_SEARXNG_URL=http://127.0.0.1:8888`, timeout 5 s, max results 5, snippet policy `disabled`, query family `general`, operator role `owner`).
- Specifies that the boundary's HTTP call goes only to `http://127.0.0.1:8888/search?q=weslr%20boundary%20design%20v1&format=json&language=en` with a fixed `User-Agent: weslr-controlled-live-searxng-boundary-v1`.
- Specifies the exact `python3 -c` run command, the expected output artifact path, the validation plan, the abort conditions, the rollback conditions, the final-judgment options, and the next-lane recommendation.
- Honors every owner directive: no live HTTP in this lane, no implementation, no live sample yet, no MLCF routing, no runtime / public integration, no provider / model call, no `.weslr/` IO, no public claims, no source summaries, no ingestion, no raw content retention, no evidence claims, no normalized evidence, no trusted / accepted evidence, no candidate membership, no proposal payloads.
- Honors the design's working principle: SearXNG is a metadata locator, not an evidence engine. The first live sample is a shape-validation call, not a research call.

The design is ready for owner review. The implementation, the live sample, the result artifact, the MLCF routing, and any future expansion are each a separate lane with their own owner authorization.
