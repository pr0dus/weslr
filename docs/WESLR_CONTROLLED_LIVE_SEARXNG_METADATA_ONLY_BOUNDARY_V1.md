# WESLR Controlled Live SearXNG Metadata-Only Boundary V1

**Date:** 2026-06-13
**Branch:** `mlcf-master-pull-20260613` (created from `origin/master` @ `f7acdb15`)
**Pulled HEAD:** `f7acdb15f27bde4e84b778c803a10ec859073032`
**Scope:** Design only. No live searches run. No ingestion, no claims, no writes, no provider calls.
**Working principle:** SearXNG is a *metadata locator*, not an evidence engine. The live boundary must never become a content-fetching, claim-authoring, or evidence-elevating surface.

---

## 1. Repo / head status after pull

| Field | Value |
|---|---|
| Repo root | `/home/pr0/projects/weslr` |
| Remote | `git@github.com:pr0dus/weslr.git` (origin) |
| Upstream `master` pushed commit (owner-confirmed) | `f7acdb15f27bde4e84b778c803a10ec859073032` |
| Pulled local HEAD on new branch | `f7acdb15` (byte-identical to upstream master) |
| Working branch for this design | `mlcf-master-pull-20260613` |
| Working tree state | HEAD clean for tracked files. One **uncommitted** tracked-file modification (`main.py`, +63 LOC) and several untracked files (`answer_engine.py`, `engine_router.py`, `perspicuous.py`, `_demo_answer.py`, `_smoke_weslr_answer.py`, `_verify_full.py`, `weslr/weslr_answer.py`, `data/`, `logs/`, `.venv-scatti/`, `.weslr/.env.local`, `.weslr/credentials.json`) are carried over from the prior `scatti-audit-bundle-v2` working tree. **None of these are part of this design commit.** |
| `git status --short` (post-pull, pre-commit) | ` M main.py` plus the untracked list above |
| `git status --short` (post-commit) | only the untracked list above (the design doc will move from untracked to committed, leaving the others untouched) |

The `main.py` modification and the untracked files are explicitly out of scope. They remain in the working tree for the next lane (the next lane being the answer-engine wiring that the owner paused earlier). This design commit does not advance them and does not regress them.

### Why a new branch

I did **not** pull `master` onto the existing `scatti-audit-bundle-v2` branch. The existing branch had `main.py` modified (+63 LOC) and nine untracked files that are not part of upstream master. Mixing a pull onto that branch would have either (a) forced a dirty three-way merge, or (b) discarded the working changes. The owner said *"pull the latest master on the Ubuntu/Nova host and prepare the controlled live SearXNG metadata-only boundary design"* — i.e. master must land cleanly, and the design must be reviewable on top of it without dragging in unrelated answer-engine experiments.

The new branch is the cleanest, smallest-blast-radius way to satisfy that.

### Recent master commits this design sits on top of

```
f7acdb15 WESLR: review MLCF metadata to evidence vertical slice
90706cdb WESLR: run first MLCF normalized evidence packet from intake preparation sample
2f0b7ee0 WESLR: review MLCF normalized evidence packet from intake preparation helper
b1a26bd0 WESLR: implement normalized evidence intake preparation helper
12b4a75d WESLR: run first MLCF evidence intake packet from metadata summary sample
7e20a721 WESLR: implement and review MLCF evidence intake packet from metadata summary helper
4fc0dade WESLR: tighten authorized metadata-only source summary validation
0f831ece WESLR: run first MLCF authorized metadata-only source summary sample
2f08f21e WESLR: review MLCF authorized metadata-only source summary helper
ea8ef151 WESLR: add authorized metadata-only source summary helper
... (deeper MLCF ledger / cross-domain / controlled-ingestion chain) ...
f1665af4 WESLR: implement SearXNG source locator adapter boundary
8ca62403 WESLR: implement metadata-only source locator record helper
```

Crucially, the master branch **already contains** `weslr/mlcf_searxng_source_locator_adapter_boundary.py` and `weslr/mlcf_metadata_only_source_locator_record.py` — these are the *sink* modules. The live SearXNG boundary this design specifies is the *source* wrapper that will call SearXNG (when authorized), normalize the response to a strict allow-list, and hand the result to those existing sink modules. The live boundary is the missing link; the sink already exists.

---

## 2. Local SearXNG availability status

| Check | Result |
|---|---|
| SearXNG Docker container | `searxng/searxng:latest`, container ID `0bff25879718`, status `Up 2 months`, mapped `0.0.0.0:8888->8080/tcp`, `[::]:8888->8080/tcp` |
| Port 8888 listening | `LISTEN 0 4096 0.0.0.0:8888` and `[::]:8888` (IPv4 + IPv6) |
| Local CLI helper | `/home/pr0/.local/bin/searxng-search` (460 B bash script, calls `http://127.0.0.1:8888/search` with `format=json`) |
| Process | `docker ps` confirms the searxng container is running; no rogue python process is impersonating SearXNG |
| Authentication | None — local Docker with no key |
| Default URL | `http://127.0.0.1:8888` (loopback only, not reachable from public internet) |
| Override | `WESLR_SEARXNG_URL` env var already supported by the existing `weslr/searxng_search_adapter.py` |

**No live search was issued during this design.** The availability check above is process / port / binary only — no HTTP call to `/search`. That is the literal first principle of this design: the boundary is *available for review*, not *actively used*.

The existing `weslr/searxng_search_adapter.py` (340 lines, May 1) is a **disabled-by-default** adapter (default `WESLR_SEARXNG_ENABLED=false`) with safe config, a `_UNSAFE_FIELDS` filter (`cookies`, `useragent`, `user_id`, `username`, `ip`, …), a `normalize_searxng_result` that strips HTML and caps fields, and a structured response with `automatic_truth_write: False` and `authority: external_evidence_unverified`. That adapter is the *implementation surface*; the design below is the *boundary contract* that wrapper must obey. The two are not in tension; the design is what we *wish the adapter to guarantee* so the next lane can make the adapter's behavior even more constrained.

---

## 3. Allowed endpoint shape

The boundary talks to SearXNG through one and only one HTTP shape:

```
GET http://127.0.0.1:8888/search
    ?q=<urlencoded query>
    &format=json
    &language=en
    &safesearch=0
    &time_range=
    &categories=
```

**Required parameters**

| Parameter | Value | Why |
|---|---|---|
| `q` | urlencoded query string | the only field SearXNG needs to return anything |
| `format` | `json` | we never want HTML; HTML is the foot-gun for raw retention |

**Optional parameters (cap-bounded)**

| Parameter | Allowed values | Default | Why |
|---|---|---|---|
| `language` | `en` only for the first safe sample | `en` | prevent per-call language expansion; later lanes may widen the enum after policy review |
| `safesearch` | `0` | `0` | SearXNG default; changing this requires an explicit design revision |
| `time_range` | empty only for the first safe sample | empty | year/month/day filters are *not* enabled in v1 — adding them broadens the surface area for an unsafe lane |
| `categories` | empty only for the first safe sample | empty | category filter is *not* enabled in v1 |

**Forbidden parameters (must 400 / 5xx out)**

| Parameter | Why |
|---|---|
| `engines` | selecting specific engines is fine, but **not in v1** — we want SearXNG to pick the default engine list so the boundary is the only thing that controls result shape |
| `pageno` | pagination beyond 1 is **explicitly forbidden**; the boundary always asks for page 1 only and the result-count cap (section 7) is enforced before any return |
| `output` | anything other than `json` is **forbidden**; the response parser only accepts `application/json` |
| any URL with a username / password / non-loopback host | **forbidden**; the boundary is hard-coded to `127.0.0.1:8888` (or the value of `WESLR_SEARXNG_URL` if it is a loopback URL; non-loopback URLs are rejected at config time) |

**Transport constraints**

- `http://` only (not `https://`) in v1 because the local container does not terminate TLS and the boundary never crosses a network boundary. If the deployment later moves to TLS, that is a new boundary version.
- No cookies, no `Authorization` header, no custom headers, no proxies.
- No redirects followed: if the response is a 3xx, the boundary returns a structured `error: "searxng_redirect_rejected"` and aborts.
- Response `Content-Type` must be `application/json`; anything else aborts.
- Response body parsed as JSON, then **field-allow-list filtered** before any value is retained.

---

## 4. Allowed metadata fields (strict allow-list)

For each result, the boundary may retain **only** the following fields. Everything else from the SearXNG response is dropped at parse time, not at usage time, so the boundary cannot accidentally surface a forbidden field even if a later code path is added.

| Field | Source in SearXNG response | Cap | Purpose |
|---|---|---|---|
| `query` | the `q` parameter we sent | 500 B | the only provenance field we need to bind a result to a question |
| `title` | `result.title` | 500 B | locator signal; no claim |
| `url` | `result.url` | 2000 B | locator signal; no fetch |
| `domain` | `urllib.parse.urlparse(url).netloc.lower()` | 255 B | derived; for `source_class_hint`, `authority_guess`, blocking rules |
| `source_engine` | `result.engine` (or first element of `result.engines`) | 100 B | the upstream engine SearXNG used; not the boundary's engine |
| `engines` | full list from `result.engines` if present | list[str], each ≤ 100 B, max 10 entries | corroboration signal |
| `rank` | 1-based index in the SearXNG response | int | used by the sink adapter's `evidence_role_guess` and `relevance_reason` |
| `score` | `result.score` (SearXNG's own ranking score) | float, `0.0 ≤ score ≤ 100.0`, or `None` | ranking signal, **not** an authority or trust signal |
| `published_date` | `result.publishedDate` if present | ISO-8601 string ≤ 50 B, or `None` | freshness; used by `freshness_status_guess` |
| `snippet` | `result.content` or `result.description` (whichever is present) | ≤ 280 B **only if** the `snippet_policy` config flag is `enabled` (default: `disabled`) | optional; the only place raw-page content could leak in. See section 4.1. |
| `source_class_hint` | derived (see section 4.2) | enum string | maps into the existing MLCF locator's `source_class_guess` field |
| `authority_guess` | derived (see section 4.2) | enum string | maps into the locator's `authority_level_guess` |
| `evidence_role_guess` | derived (see section 4.2) | enum string | maps into the locator's `evidence_role_guess` |
| `relevance_reason` | short string from a closed enum | enum string | why the boundary kept this result; never a narrative |
| `freshness_status_guess` | derived (see section 4.2) | enum string | `fresh`, `recent`, `stale`, `unknown`, `blocked` |
| `access_license_status_guess` | derived (see section 4.2) | enum string | `open_access`, `registration_required`, `paywalled`, `unknown`, `blocked` |
| `privacy_status_guess` | derived (see section 4.2) | enum string | `public_non_personal`, `mixed_personal_signals`, `personal_data_present`, `unknown`, `blocked` |
| `blocked_status` | `allowed` / `blocked` | enum string | the only top-level verdict; the boundary never returns a `trusted` verdict |
| `block_reason` | short string from a closed enum (only when `blocked_status == "blocked"`) | enum string | which rule fired |

**No other field may be retained.** The parser drops everything else, including but not limited to: `content`, `description`, `parsed_content`, `cookies`, `category`, `tags`, `template`, `thumbnail`, `thumbnail_src`, `priority`, `iframe_src`, `opengroup`, `closegroup`, `suggestion`, `corrections`, `answers`, `infoboxes`, `related_topics`, `unresponsive_engines`, `engines_disabled`, `timings`, anything containing the strings `user_id`, `username`, `ip`, `cookie`, `useragent`.

### 4.1 Snippet policy (the only field that touches raw-page language)

A snippet is the single highest-risk surface in the response: it is the only piece of result text that came from the upstream page. We retain it **only** if all of the following hold, and **only** at the cap of 280 bytes:

1. `WESLR_SEARXNG_SNIPPET_POLICY` env var is set to `enabled` in the runtime that issues the call.
2. The snippet is plain text (no HTML tags, no `&` HTML entities, no `data:` / `javascript:` schemes). The boundary strips any tag-like fragment and any HTML entity before length check.
3. The snippet does not contain any of: an email-like substring, a phone-like substring, a credit-card-like substring, an IPv4-like substring.
4. The snippet does not exceed 280 bytes after sanitization.
5. The locator record that holds the snippet also has `snippet_policy_applied: true` set explicitly, and the `source_class_hint` and `privacy_status_guess` are both `blocked`-eligible if the snippet contains the word `login`, `password`, `sign in`, `subscribe`, `pay`, `cookie`, or `gdpr`.

If any of (1)–(5) fails, the snippet is dropped to `None` and the boundary proceeds without it. The default is `disabled`, which means **for the first safe sample, snippets are not retained at all.** This is the conservative posture and matches the design's working principle.

### 4.2 Derived fields (the only "smart" the boundary is allowed to do)

The boundary may compute a small number of derived fields, each from a closed enum, by applying a documented rule. It may not invent categories, learn from results, or carry state across calls.

| Field | Rule |
|---|---|
| `source_class_hint` | `domain in OFFICIAL_DOMAIN_LIST` → `official_standard`; `domain.endswith(".gov")` or in `GOV_DOMAIN_LIST` → `official_government_or_agency_data`; `domain in VENDOR_DOCS_DOMAIN_LIST` → `official_vendor_documentation`; `domain.endswith("github.com")` or in `GITHUB_DOMAIN_LIST` → `github_repository`; matches the MLCF `*public_*` set → the corresponding enum; everything else → `unknown_authority`. |
| `authority_guess` | derived from `source_class_hint` per a small fixed lookup (e.g. `official_standard` → `official_primary`, `github_repository` → `community_signal`, `public_dataset` → `public_primary`, else `unknown_authority`). |
| `evidence_role_guess` | default `candidate_signal`; may be downgraded to `prior_art` only when the query family is one of a fixed allow-list (e.g. `["standard", "spec", "rfc", "isbn"]`); otherwise stays `candidate_signal`. Never `measurement_data`, `definition_or_standard`, `replication_target`, or any role that would let the locator be misread as evidence. |
| `relevance_reason` | one of: `engine_match`, `domain_match`, `title_match`, `low_signal`. The boundary does not score relevance; it only tags which cheap rule the result triggered. |
| `freshness_status_guess` | `published_date` within last 12 months → `fresh`; 12–36 months → `recent`; older → `stale`; missing → `unknown`; date is in the future or unparseable → `unknown`. |
| `access_license_status_guess` | `domain` is in `OPEN_ACCESS_LIST` (e.g. `arxiv.org`, `github.com`, `*.gov`, `doi.org`, `pubmed.ncbi.nlm.nih.gov`, `europepmc.org`) → `open_access`; matches a small `PAYWALLED_LIST` (e.g. `nature.com`, `sciencedirect.com`, `ieee.org`, `acm.org`) → `paywalled`; the locator's URL contains a substring like `login`, `signin`, `account` → `registration_required`; else `unknown`. |
| `privacy_status_guess` | default `public_non_personal`; promoted to `mixed_personal_signals` if the snippet (when retained) contains a first-name + last-name pattern, or a personal-domain pattern (`linkedin.com/in/`, `twitter.com/`, `facebook.com/`); promoted to `personal_data_present` if the URL itself looks like a personal page AND the snippet contains email-like content (caught at snippet policy step 3 anyway). For first safe sample, this is always `public_non_personal` because snippet is disabled. |
| `blocked_status` | one of: `allowed`, `blocked`. Default `allowed`. The block rules in section 9 flip it to `blocked`. There is no `trusted` value. |

All enums are tight. No free-text fields beyond `query` (which is exactly what we sent) and `title` (which we cap). The boundary does not generate narratives.

---

## 5. Forbidden fields / content

The following are **explicitly forbidden** and must not appear in any field of the boundary's output, in any log line, in any in-memory representation, or in any locator record handed to the MLCF sink:

- Raw response body bytes (any portion of the response not on the allow-list).
- HTML, Markdown, PDF, JSON-LD, RDF, or any markup the boundary could have rendered from.
- Any field whose key contains: `content`, `description`, `parsed_content`, `cookies`, `useragent`, `user_id`, `username`, `ip_`, `ip$`, `password`, `token`, `session`.
- Any value that is a URL to a login, account, signup, paywall, captcha, or rate-limited page (these are blocked at the URL level by section 9).
- Source-content summaries, paraphrases, embeddings, vector encodings, hashes of the snippet, hashes of the content, or any downstream artifact that *contains* the snippet.
- Claim language: `discovery`, `proof`, `confirmed`, `verified`, `official conclusion`, `final answer`, `state of the art`, `benchmark`, `agi`, `consciousness`, `sentience`, `public-science`, `publicly claimable`. The boundary's output must use neutral locator language: `candidate`, `locator`, `signal`, `source class`, `authority guess`, `evidence role guess`, `relevant by`, `blocked by`, `rejected because`.
- `trusted` verdict: the boundary never produces a `trusted` or `accepted-as-evidence` verdict. The most it produces is `allowed` (a locator may exist) or `blocked` (a locator must not exist). The elevation from `allowed` to `evidence-accepted` happens (or does not) in a *separate* lane that is not part of this design.
- The boundary never produces a `source_ingestion_authorized`, `raw_retention_authorized`, `web_call_authority`, `github_call_authority`, `searxng_call_authority`, `source_fetching_authority`, `source_summary_authority`, `source_access_authorized`, `public_claim_authorized`, `final_answer_authority`, `discovery_claim_authorized`, `proof_claim_authorized`, `agi_claim_authorized`, `benchmark_claim_authorized`, `public_science_claim_authorized`, `behavior_pack_promotion_authorized`, `database_write_authorized`, `memory_mutation_authorized`, `project_mutation_authorized`, `cross_user_leakage_authorized`, or `hidden_private_protected_authorized` flag. These are *forbidden outputs*, not just unused ones. If a future module wants any of these, it must be a different lane with its own boundary.

The boundary must not call any of:

- `urllib.request.urlopen` with the response URL (i.e. **no following result links**).
- `wget`, `curl`, `requests`, `aiohttp` against any URL other than the exact one SearXNG request shape.
- `git clone`, `pip install`, `apt-get`, `npm install`, `docker pull` triggered by a result.
- `pdfminer`, `PyPDF2`, `pdfplumber`, `beautifulsoup4` against any result.
- `requests_cache`, `aiohttp_client_cache`, `cachecontrol`, or any persistent cache.
- The Ollama, OpenAI, Anthropic, Gemini, OpenRouter, or any model provider's API.
- The `auth-profiles.json` file.
- The `~/.openclaw/agents/main/sessions/` write path.
- The `/home/pr0/.openclaw/sessions/` write path.
- The `.weslr/` write path.
- The `memory/`, `continuity/`, `tenant_*` write path.
- The `chat_responder`, `chat_ui`, `dialogue`, or `main` modules.
- The `provider`, `llm_runtime`, or `sim` modules.
- The `interpretation`, `self_improvement_*`, `self_model`, `self_referential` modules.

The boundary may **read** but not **write** to any of: the existing `weslr/searxng_search_adapter.py`, the MLCF sink modules, the MLCF locator record module. It may not import the existing `weslr.chat_responder` module under any name.

---

## 6. Query authorization rules

The boundary only accepts a query if **all** of the following hold:

1. The query is a non-empty string after `urllib.parse.quote(query, safe="")` and the post-quote length is ≤ 200 bytes. (Reason: keep query shape predictable; rejects the obvious "send a 10 KB blob" attack.)
2. The query contains no control characters (regex `[\x00-\x1f\x7f]` must not match). (Reason: control chars are a sign of injection attempts or paste accidents; safer to reject.)
3. The query is not a URL (does not start with `http://`, `https://`, `ftp://`, `file://`, `data:`, `javascript:`). (Reason: a URL is not a "question"; if a caller wants to test a URL, they should use a different tool. The boundary is for question-style queries.)
4. The query is on the **first-safe-sample allow-list** in the first safe sample. See section 15. The allow-list is small, fixed, and replaces no other query.
5. The query family (a closed enum: `general`, `standard`, `rfc`, `isbn`, `paper-id`, `domain-glossary`) is one the runtime was explicitly configured to allow. The first safe sample uses `general` only. Other families are gated by future lanes.
6. The caller's role is one of `owner`, `maintainer`, or `metadata-locator-runner`. **Not** `public`, `anonymous`, or any other role. (Reason: this is a controlled lane, not a public service.)
7. The call rate is bounded to ≤ 1 call per 60 seconds and ≤ 5 calls per hour per session. (Reason: the first safe sample is a manual exercise, not a load test.)
8. The boundary is invoked from a registered operator lane (the MLCF sink or the owner CLI), not from the omnichat contract-reply engine, not from the chat responder, not from the protected preview, and not from the public weslr.de site.

The first safe sample, in this lane, is run only in response to an explicit owner invocation. There is no cron, no heartbeat, no autonomous session, no growth session, and no production cron-job that can trigger it.

---

## 7. Result count limits

| Limit | Value | Why |
|---|---|---|
| `max_results_per_call` | 5 | The sink adapter's `evidence_role_guess` is a per-result field. Five gives the sink enough to compare without forcing a paginated boundary. |
| `min_results_per_call` | 0 | Empty results are valid; the boundary returns them rather than retrying. |
| `result_count_in_response` | the actual count returned by SearXNG, **capped at 5** | the boundary does not pad, does not synthesize, does not retry with different terms. |
| `total_results_estimate` | not retained | SearXNG sometimes returns an approximate total; the boundary drops it. |
| `time_range_window` | n/a (disabled in v1) | see section 3 |

The boundary must not make a second HTTP call within the same `build_locator_records_from_searxng_live_v1` invocation, even if the first call returned zero or one result. One call per invocation. Period.

---

## 8. Timeout / error handling

| Failure mode | Boundary behavior |
|---|---|
| HTTP timeout (SearXNG did not respond in ≤ 5 seconds) | structured return with `ok: False`, `reason: "searxng_timeout"`, `results: []`, no retry |
| HTTP 5xx from SearXNG | structured return with `ok: False`, `reason: "searxng_5xx_<status>"`, `results: []` |
| HTTP 4xx from SearXNG (except 401/403 which the boundary treats as `searxng_unreachable`) | structured return with `ok: False`, `reason: "searxng_4xx_<status>"`, `results: []` |
| HTTP 3xx | structured return with `ok: False`, `reason: "searxng_redirect_rejected"`, `results: []` (no redirect followed) |
| HTTP 2xx with `Content-Type` not `application/json` | structured return with `ok: False`, `reason: "searxng_wrong_content_type"`, `results: []` |
| HTTP 2xx with non-parseable JSON | structured return with `ok: False`, `reason: "searxng_malformed_json"`, `results: []` |
| HTTP 2xx with valid JSON but a result object missing `title` or `url` | that result is dropped, the others proceed; if all results are missing these fields, `reason: "searxng_results_incomplete"` |
| SearXNG container down (connection refused) | structured return with `ok: False`, `reason: "searxng_unreachable"` |
| DNS failure, network failure | structured return with `ok: False`, `reason: "searxng_network_error"` |
| Unexpected exception in the boundary itself | structured return with `ok: False`, `reason: "boundary_internal_error"`, **the exception is logged to stderr but the traceback is not returned in the structured response** |

The boundary never raises an exception to its caller. The caller always gets a structured dict with at least `ok: bool`, `reason: str`, `results: list`, `boundary_version: str`. This matches the pattern already used by `weslr/searxng_search_adapter.py::search_searxng`.

The boundary never retries. It never falls through to a different upstream. It never returns a default-result or a cached-result or a fake-result. If the call fails, the result is empty. The next lane (the MLCF sink) sees `results: []` and must handle that gracefully (and the existing MLCF sink already does — it does not synthesize, it returns a structured `result_status: "rejected"` with `reason: "no_results"`).

The structured return is the only output channel. The boundary never prints, never logs to a file (other than stderr at the level the caller's runtime already configures), never writes to a database, never emits a webhook.

---

## 9. Privacy / source-safety blocking rules

The boundary sets `blocked_status: "blocked"` and excludes the result from `results[]` if **any** of the following are true. The block reason is one of the closed enum values listed below.

| Rule | Block reason | Why |
|---|---|---|
| `domain` is empty or unparseable | `unparseable_domain` | we cannot evaluate any other rule without a domain |
| `domain` matches a hard blocklist: `localhost`, `127.`, `::1`, `0.0.0.0`, `.local`, `.onion`, `10.`, `192.168.`, `172.16.`–`172.31.`, any non-IPv4-non-DNS hostname | `private_or_loopback_target` | the boundary must never help a caller reach private network resources via SearXNG |
| `domain` matches a personal-data list: `facebook.com`, `instagram.com`, `tiktok.com`, `linkedin.com`, `twitter.com`, `x.com`, `reddit.com/user/`, `reddit.com/r/` (only user pages), `quora.com` | `personal_data_platform` | not a *forbidden* platform in general, but a SearXNG result pointing at a personal-data page is a privacy footgun for the metadata-only lane |
| `domain` is in a known-tracking-only list: `doubleclick.net`, `googlesyndication.com`, `googleadservices.com`, `facebook.net`, `scorecardresearch.com`, `quantserve.com`, `hotjar.com`, `mixpanel.com`, `segment.io`, `amplitude.com` | `tracking_or_analytics_only` | not source content |
| `url` contains a query string with `token=`, `session=`, `auth=`, `key=`, `api_key=`, `password=`, or any URL parameter that looks like a credential | `credential_in_url` | accidentally-leaked credential URLs must not be retained as locators |
| `url` is longer than 2000 bytes | `url_too_long` | the URL was truncated at the cap, so the locator is unusable |
| `title` is empty | `empty_title` | we cannot form a useful locator record without a title |
| `title` matches a known-malware-signature regex (the same list the MLCF summary helper uses) | `malware_signature` | not a content claim — we are not claiming the page is malicious, only refusing to retain a locator whose title alone matches a known-signature string |
| `title` is more than 500 bytes after UTF-8 encoding | `title_too_long` | probably a spammy or autogenerated page |
| the `query` was the only thing that put the result on the page (i.e. the title is just the query verbatim) **and** the result is in the bottom half of the returned list | `low_signal_self_match` | the result is likely a search-results page itself, not a source |
| the result URL is a known-login URL: matches `(/login|/signin|/sign-in|/signup|/sign-up|/account|/auth|/sso|/oauth|/captcha)` | `login_or_account_url` | login pages are never sources |

If a result is blocked, the boundary returns the `block_reason` in the per-result `block_reason` field and excludes the result from the locator records. The caller may ask for the `blocked_count` separately. The boundary does not retain a "blocked but interesting" cache. A blocked result is gone.

The hard blocklists are stored as plain Python tuples in the boundary module. They are not loaded from disk, not loaded from a URL, and not updated without a code change. There is no admin UI to add to them. This is intentional: a boundary that takes its own rules from a network source is not a boundary.

---

## 10. No raw-content retention policy

The boundary does not write any of the following to disk, in any format, in any location:

- The full HTTP response body of the SearXNG call.
- Any field of the response that is not on the allow-list.
- The request URL or headers.
- The request timestamp beyond what is included in the structured return.
- The SearXNG version, the docker image ID, the engine list, or any other metadata about the SearXNG server.

The boundary does not write to:

- `/home/pr0/.openclaw/sessions/` (operator sessions)
- `~/.openclaw/agents/main/sessions/` (agent sessions)
- `memory/`, `continuity/`, `tenant_*` (operator state)
- `.weslr/` (WESLR runtime state)
- Any `*.jsonl` or `*.log` file in the repo
- Any database, sqlite, redis, postgres, or vector store
- Any cache layer (filesystem, in-memory LRU that survives a process exit, or distributed)

The boundary does not accumulate results across calls. Each call is independent. There is no per-process "seen URLs" set. There is no per-session "this query was asked before" check. There is no "previous result for this URL" cache.

The boundary may write the structured return to **stderr** (one line, JSON-serialized) so the calling operator can see the outcome in their terminal. It must not write to a file, even temporarily. The stderr line is the only persistent artifact of a call.

The boundary's structured return contains **only** the allow-list fields. A caller that wants to log the return is responsible for that; the boundary does not log on the caller's behalf.

The boundary module is **read-pure**: it reads from the SearXNG container and the env, writes nothing.

---

## 11. No-ingestion / no-claim policy

The boundary does not:

- Add a result to a candidate graph.
- Promote a locator to evidence.
- Mark a locator as `accepted` or `trusted`.
- Generate a `summary` or `paraphrase` or `excerpt` of any field.
- Compute a hash of any retained field beyond the locator-id, which is the SHA-256 of `(query, url, rank)` (a deterministic, non-content-bearing identifier used only for cross-reference in the structured return).
- Compute an embedding, vector, or similarity score of any field.
- Run an ML model on any field.
- Trigger a downstream pipeline (the MLCF summary, the MLCF intake, the MLCF normalized evidence packet, the MLCF ledger registry, the source selection plan) by writing to its inputs.
- Open a follow-up HTTP call.
- Open a follow-up SearXNG call.
- Open a follow-up file write.
- Trigger a notification, a webhook, an email, a Telegram message, a logrotate, a metrics flush, or any external side effect.

The boundary's structured return is the **end of the boundary's responsibility**. Whatever the caller does with it is the caller's lane. The boundary does not constrain the caller (the MLCF sink is what constrains the caller), but the boundary does not *enable* a caller to do the wrong thing either: by not producing raw content, claim language, `trusted` verdicts, or `*_authority` flags, the boundary makes it impossible for a downstream caller to accidentally elevate a SearXNG result to evidence without going through the MLCF sink's own validation. The MLCF sink is the only place that may *validate* a locator and produce a `result_status: "accepted"` verdict; this boundary never does.

The boundary never claims:

- That a result is the *right* answer to a question.
- That a result is the *only* answer.
- That a result has been seen before or not seen before.
- That a result is *new* or *recent* beyond the `freshness_status_guess` enum.
- That a result is *authoritative* beyond the `authority_guess` enum.
- That a result is *useful* beyond the `relevance_reason` enum.
- That a result is *safe* beyond the `blocked_status` enum.

The boundary never claims anything that is not an enum from section 4.2. There is no narrative.

---

## 12. Adapter packet shape

The structured return from the boundary, given a query `q` and a SearXNG response (or a SearXNG error), is:

```python
{
    "boundary_version": "weslr_controlled_live_searxng_metadata_only_boundary_v1",
    "ok": bool,                                    # True iff at least one result was retained
    "query": str,                                  # the query that was sent (echo)
    "reason": str,                                 # one of the closed enum from section 8
    "searxng_call_status": int | None,             # the HTTP status code, or None if no call was made
    "searxng_call_latency_ms": int | None,         # wall clock for the HTTP call, or None
    "results_count_kept": int,                     # count of results in `results[]` after blocking
    "results_count_blocked": int,                  # count of results dropped by blocking rules
    "results": [
        {
            "query": str,
            "title": str,
            "url": str,
            "domain": str,
            "source_engine": str | None,
            "engines": list[str],
            "rank": int,
            "score": float | None,
            "published_date": str | None,
            "snippet": str | None,                  # None unless snippet policy is enabled
            "source_class_hint": str,               # enum
            "authority_guess": str,                 # enum
            "evidence_role_guess": str,             # enum (always candidate_signal in v1)
            "relevance_reason": str,                # enum
            "freshness_status_guess": str,          # enum
            "access_license_status_guess": str,     # enum
            "privacy_status_guess": str,            # enum
            "blocked_status": "allowed",            # the only allowed value in results[]
            "locator_id": str,                      # SHA-256 of (query, url, rank), 64 hex chars
            "boundary_id": "weslr_controlled_live_searxng_metadata_only_boundary_v1",
        }
    ],
    "blocked": [
        {
            "url": str,                             # the URL that was blocked
            "title": str,                           # may be empty
            "block_reason": str,                    # enum from section 9
        }
    ],
    "evidence_status": "metadata_only_locator_candidates",  # always this exact string
    "automatic_truth_write": False,                # always False
    "raw_content_retained": False,                 # always False
    "snippets_retained": bool,                     # whether the snippet policy was enabled for this call
    "authority_verdict": "external_evidence_unverified",  # always this exact string
}
```

This dict is the boundary's entire output. The caller hands it to the MLCF sink (`weslr.mlcf_searxng_source_locator_adapter_boundary.build_mlcf_locator_record_from_searxng_result_v1`) one result at a time, with the `blocked[]` list kept on the side. The MLCF sink will validate the field values against its own enums, run the locator-record validator, and produce a `result_status` per result. If a result's field is not in the MLCF enum (e.g. an `evidence_role_guess` we did not anticipate), the MLCF sink is responsible for rejecting it; the boundary does not pre-filter against the MLCF enums because that would couple the two.

The boundary is intentionally a thin shim between SearXNG and the MLCF sink. It does the HTTP call, the field-allow-list filter, the field cap enforcement, the per-result blocking rules, the enum derivations, and the structured return. The MLCF sink does the MLCF-side validation, the per-locator rationale, the evidence-role mapping, the cross-locator consistency check, the ledger registration, and any other MLCF-side reasoning.

---

## 13. Mapping into the existing metadata-only source locator records

Each entry in the boundary's `results[]` is mapped into the existing MLCF locator record via the existing MLCF sink. The mapping is **one result in, one locator candidate out, no batching**. The mapping is delegated to the sink's existing function:

```python
from weslr.mlcf_searxng_source_locator_adapter_boundary import (
    build_mlcf_locator_record_from_searxng_result_v1,
)

locator_record = build_mlcf_locator_record_from_searxng_result_v1(
    searxng_result=boundary_result["results"][i],   # one entry
    query=boundary_result["query"],
    boundary_version="weslr_controlled_live_searxng_metadata_only_boundary_v1",
)
```

The boundary does not call this function itself. The caller does. The caller is the operator CLI or the controlled-runner, not the boundary. The boundary's job ends when it produces the structured return.

The mapping the caller does, by calling the sink, has the following shape:

| Boundary field | MLCF locator record field |
|---|---|
| `query` | `query` |
| `title` | `title` |
| `url` | `url` |
| `domain` | `domain` |
| `source_engine` | `source_engine` |
| `engines` | `engines` |
| `rank` | `rank` |
| `score` | `score` |
| `published_date` | `published_date` |
| `snippet` | `snippet` (only if the sink accepts the boundary's snippet-policy-applied bool) |
| `source_class_hint` | `source_class_guess` |
| `authority_guess` | `authority_level_guess` |
| `evidence_role_guess` | `evidence_role_guess` |
| `relevance_reason` | `relevance_reason` |
| `freshness_status_guess` | `freshness_status_guess` |
| `access_license_status_guess` | `access_license_status_guess` |
| `privacy_status_guess` | `privacy_status_guess` |
| `blocked_status` | `blocked_status` (always `"allowed"` for results in `results[]`) |
| `locator_id` | `locator_id` (preserved as-is; the sink does not regenerate it) |
| `boundary_id` | the sink's `source_boundary_id` field |

The MLCF sink validates the locator record with `validate_mlcf_metadata_only_source_locator_record_v1`. If validation fails, the locator is rejected. The boundary does not retry. The caller (the operator CLI) surfaces the rejection to the operator. The operator decides whether to re-run with a different query or to accept the empty set.

The boundary never calls the MLCF sink. The boundary's contract ends at the structured return.

---

## 14. Validation plan

The boundary's correctness is validated by:

### 14.1 Unit tests (no live HTTP, mocked SearXNG)

| Test name | Asserts |
|---|---|
| `test_disabled_by_default` | `WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED` unset → every call returns `ok=False, reason="disabled"` and the boundary does not issue an HTTP call |
| `test_query_length_cap` | a 201-byte query is rejected with `reason="query_too_long"` |
| `test_query_control_chars` | a query with `\x00` is rejected with `reason="control_chars_in_query"` |
| `test_query_url_rejected` | a query starting with `https://` is rejected with `reason="url_as_query"` |
| `test_only_json_response_accepted` | a mocked response with `Content-Type: text/html` returns `reason="searxng_wrong_content_type"` |
| `test_redirect_rejected` | a mocked 301 response returns `reason="searxng_redirect_rejected"` |
| `test_timeout_returns_structured` | a mocked timeout returns `reason="searxng_timeout"` |
| `test_5xx_returns_structured` | a mocked 503 returns `reason="searxng_5xx_503"` |
| `test_4xx_returns_structured` | a mocked 404 returns `reason="searxng_4xx_404"` |
| `test_field_allow_list_enforced` | a mocked SearXNG response with 20 fields per result keeps only the 18 allow-listed fields |
| `test_snippet_default_disabled` | default config → `snippets_retained=False` in the structured return, `snippet=None` in every result |
| `test_snippet_enabled_strips_html` | `WESLR_SEARXNG_SNIPPET_POLICY=enabled` + snippet with `<b>` → `snippet` has the tag stripped, `snippets_retained=True` |
| `test_snippet_rejected_for_login_text` | snippet with the word `login` → `snippet=None`, the result's `snippet_policy_applied=True`, and the sink mapping would mark the result blocked by the snippet policy |
| `test_url_field_capped_at_2000` | a result with a 2500-byte URL → URL truncated, result dropped with `block_reason="url_too_long"` |
| `test_loopback_domain_blocked` | a result whose URL is `http://192.168.1.5/x` → blocked with `block_reason="private_or_loopback_target"` |
| `test_credential_in_url_blocked` | URL containing `?token=ABC` → blocked with `block_reason="credential_in_url"` |
| `test_login_url_blocked` | URL containing `/login` → blocked with `block_reason="login_or_account_url"` |
| `test_personal_data_platform_blocked` | result on `facebook.com` → blocked with `block_reason="personal_data_platform"` |
| `test_tracking_domain_blocked` | result on `doubleclick.net` → blocked with `block_reason="tracking_or_analytics_only"` |
| `test_no_narrative_fields_in_output` | the structured return's keys are exactly the allow-listed set in section 12 (no `summary`, `explanation`, `interpretation`, `claim`, `evidence`, etc.) |
| `test_authority_false_flags_absent` | the structured return's keys do not include any of the `_AUTHORITY_FALSE_FLAGS_V1` set from the existing MLCF adapter |
| `test_max_results_capped` | a mocked response with 50 results → `results_count_kept ≤ 5`, `results_count_blocked ≥ 45` (or however many were blocked by other rules) |
| `test_no_retry_on_first_call_failure` | a mocked timeout → no second call to the URL, `searxng_call_latency_ms` reflects the single call only |
| `test_no_write_to_disk` | after a call, the boundary module has not created any new file in `/tmp/`, `.weslr/`, `memory/`, `continuity/`, `tenant_*`, `~/.openclaw/agents/`, `~/.openclaw/sessions/`, or any repo path |
| `test_disabled_no_http_call_at_all` | with the env var unset, the boundary does not even open a socket to `127.0.0.1:8888` (verified by a socket-level mock) |
| `test_protected_modules_not_imported` | the boundary module's `sys.modules` after import does not include `chat_responder`, `chat_ui`, `dialogue`, `main`, `interpretation`, `llm_runtime`, `sim`, `providers`, `self_improvement_chat`, `auth-profiles.json` |
| `test_blocked_results_excluded_from_results` | a response that has 3 allowed + 2 blocked → `results_count_kept=3`, `results_count_blocked=2`, `len(results)==3`, `len(blocked)==2` |

### 14.2 Integration test (mocked SearXNG, one real boundary call)

A single integration test issues a real call to the boundary (with the env var enabled, with a mocked SearXNG fixture, with a small fixture query), parses the structured return, and asserts the output shape. No real HTTP. No real network. No real SearXNG.

### 14.3 Live test (the first safe sample)

A single, owner-authorized, hand-issued live call to the actual SearXNG container with the boundary in the "first safe sample" mode (see section 15). Output captured to stderr, then discarded. **No locator records written to any MLCF sink in this test.** The live test is purely a "does the boundary hold its shape against a real SearXNG response" check.

### 14.4 Regression against the WESLR release gate

Before commit, the design must be compatible with the existing `weslr/tests/release_gate_v1.py` and the existing `scripts/weslr_release_check.sh`. Specifically:

- G1 (test harness passes) — the boundary module must not break the harness. The harness is untouched; this is a sanity check, not a feature.
- G2 (staged files in allowed scope) — the design doc lives at `docs/WESLR_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_BOUNDARY_V1.md`, which is in the allowed scope. The gate's allowed-prefix list is `weslr/**` and `interpretation.py`, so a `docs/` path is technically *outside* the prefix list. **Section 14.5 below** records this and the resolution.
- G3 (no `execution_allowed=True` in production) — the boundary module does not introduce this. Confirmed by reading the design.
- G4 (no OpenClaw / TIA C# in staged scope) — not applicable, the doc has no code.
- G5 (handler registry metadata completeness) — the boundary is a pure function, not a handler registry entry. Not applicable.

### 14.5 Gate-2 scope reconciliation

The release gate's allowed-scope rule (G2) is `path.startswith("weslr/") or path == "interpretation.py"`. A `docs/WESLR_...` path is outside that list. There are three options:

1. **Move the design to `weslr/docs/WESLR_...`** — but that path doesn't exist as a real directory; `weslr/docs/` does exist on master and is where MLCF docs live. Wait, let me re-check.

Actually, on the master branch, there is both a top-level `docs/` directory (the operator docs, MLCF summaries, etc.) and a `weslr/docs/` directory (the MLCF implementation-side docs). The release gate's `FORBIDDEN_PREFIXES = ["openclaw/", "plugins/", "memory/", "continuity/"]` does not forbid `docs/`, but the allowed-scope check is `path.startswith("weslr/") or path == "interpretation.py"`, which `docs/WESLR_...` does not satisfy.

The historical record (`docs/WESLR_CONTROLLED_PRIVATE_PROJECT_CHAT_RUNTIME_WIRING_IMPLEMENTATION_REPORT_V1.md` and similar `*_REPORT_V1.md` files in top-level `docs/`) shows that design and review docs *have* been committed to the top-level `docs/` directory on this branch. The release gate's check is a per-commit check of staged files, not a retroactive audit of all files in the repo. If a `docs/WESLR_...` path is staged, G2 will fail.

Resolution: **the design doc is committed via `git commit` after `git add` of just that file, in a way the operator commits the file with intent.** The release gate is a pre-commit-style check that is run by the operator, not by the agent. The owner has, in the past, committed similar top-level `docs/WESLR_*.md` files. If G2 rejects the file, the resolution is one of:

- (a) run the gate with a documented narrow scope exception for this design doc (the operator's call, not the boundary's), or
- (b) move the file under `weslr/docs/` where it satisfies the gate.

I will not pre-empt this. The design will be staged as `docs/WESLR_...md` and the operator will run the gate. If G2 fails, the operator can move the file or pass the narrow-exception flag. I will record this in the final report.

(Note for the operator: the master branch has 200+ existing `docs/WESLR_*.md` files; the release gate's "staged files in allowed scope" rule is a forward-looking guardrail, and the `docs/` path is a long-established convention for design docs. The gate does not retroactively reject the existing 200 files; the gate rejects new staged additions. The decision to relax G2 for `docs/WESLR_*.md` is a one-line change in the gate; that's the operator's lane, not the boundary's.)

### 14.6 Protected-file check

Before any commit, the operator (or the agent on the operator's behalf) must verify that none of the following files have been modified:

- `weslr/chat_responder.py`
- `weslr/main.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`

This is also enforced by the MLCF test suite (`PROTECTED_FILES` constant in `test_mlcf_searxng_source_locator_adapter_boundary_v1.py`). The boundary's commit MUST NOT touch any of these. The validation step explicitly runs `git diff --name-only HEAD~1..HEAD` and asserts the protected-files set is not in the diff.

---

## 15. First safe sample proposal

The first live call to SearXNG under this boundary design is the *first safe sample*. It is a single, owner-authorized, hand-issued call. Its purpose is to confirm the boundary holds its shape against a real SearXNG response, not to collect results.

**Query:** `weslr boundary design v1`

**Configuration:**

| Env var | Value | Why |
|---|---|---|
| `WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED` | `true` | enable the live call (default is `false`) |
| `WESLR_SEARXNG_LIVE_BOUNDARY_SNIPPET_POLICY` | `disabled` | no snippets retained; first sample is the strictest mode |
| `WESLR_SEARXNG_URL` | `http://127.0.0.1:8888` | loopback only; non-loopback URLs are rejected by the boundary |
| `WESLR_SEARXNG_LIVE_BOUNDARY_TIMEOUT_SECONDS` | `5` | the timeout cap |
| `WESLR_SEARXNG_LIVE_BOUNDARY_MAX_RESULTS` | `5` | the result count cap |
| `WESLR_SEARXNG_LIVE_BOUNDARY_QUERY_FAMILY` | `general` | only family allowed in v1 |
| `WESLR_SEARXNG_LIVE_BOUNDARY_OPERATOR_ROLE` | `owner` | only role allowed in v1 |

**Expected output shape (5 entries):**

The boundary returns 0–5 `results[]` entries, each with the field set in section 4. Most or all will have `source_class_hint: "github_repository"` (since `weslr boundary design v1` matches the WESLR repo's own docs) or `source_class_hint: "unknown_authority"`. The boundary may also return `results_count_blocked > 0` if SearXNG returns personal-data-platform or tracking-domain URLs (it shouldn't, for this query, but the boundary's blocking rules are general, not query-specific).

**After the call:**

1. The operator inspects the structured return. They do not pass the result to the MLCF sink. They do not write a locator record. They do not run the MLCF summary, the MLCF intake, the MLCF normalized evidence packet, or any other downstream pipeline.
2. The operator confirms the output shape matches section 12. If any field is missing, extra, or in a value the boundary should not have produced, the boundary is repaired before any second sample.
3. The operator deletes the stderr line that captured the structured return. The first safe sample is ephemeral.
4. The operator records the outcome (pass / fail) in a separate operator-side log, not in the boundary's structured return.

**What the first safe sample is NOT:**

- Not a research sample. The query is a literal phrase, not a real question.
- Not a benchmark. There is no scoring.
- Not a comparison sample. There is no "before / after".
- Not a load test. One call, five results, ≤ 5 seconds.
- Not a public-facing test. The operator is the only caller.
- Not a "first mover" or "proof of capability" sample. It is a shape-validation call.

A second safe sample, after the first one passes shape validation, is a separate lane with a separate owner authorization. It is not pre-approved by this design.

---

## 16. Rollback / abort conditions

The boundary must be considered failed and rolled back if **any** of the following are observed:

| Abort condition | Action |
|---|---|
| `WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED=true` and a call returns a `searxng_call_status` of 200 but the response body contains a field the allow-list missed | rollback the boundary module to the previous commit, file an incident, do not re-enable until the missed field is on the allow-list |
| the boundary's stderr line contains any of: `cookies`, `useragent`, `user_id`, `username`, a `@` followed by an email-like pattern, a `/login`, a `/signin`, a `token=`, a `password=`, an `api_key=` | rollback immediately; the boundary is leaking |
| the boundary is called from a path that is not on the operator allow-list (e.g. the omnichat contract-reply engine, the protected preview, the public weslr.de site) | rollback; the boundary was wired into a forbidden caller |
| a call to the boundary produces a `blocked[]` list that is empty AND the response body has 0 results AND the response body has 0 errors AND `searxng_call_status` is 200 | the boundary is silently returning empty; investigate before re-enabling |
| the `searxng_call_latency_ms` is greater than the timeout cap | the boundary is timing out *after* the timeout; rollback |
| the boundary writes any file outside `/dev/stderr` | rollback; the boundary is not read-pure |
| the boundary imports any module on the forbidden-imports list (section 5) | rollback; the boundary's import surface is wrong |
| the boundary produces a `trusted` verdict, a `discovery` flag, a `proof` flag, an `agi_claim_authorized` flag, or any other "elevation" verb | rollback; the boundary is producing forbidden output |
| the boundary's structured return's keys include anything not in section 12 | rollback; the schema drifted |

**Rollback procedure:**

```bash
# 1. Disable the env var in the operator's runtime.
unset WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED

# 2. Revert the boundary module commit.
git revert <boundary-design-commit-sha>

# 3. If the boundary is already imported by another module, also remove that import.
git grep -n "weslr_controlled_live_searxng" -- weslr/

# 4. Verify the protected files are untouched.
git diff HEAD~1..HEAD --stat -- weslr/chat_responder.py weslr/main.py main.py dialogue.py chat_ui.py
# expected: empty diff

# 5. Re-run the release gate.
python3 weslr/tests/release_gate_v1.py
bash scripts/weslr_release_check.sh
```

**Operator-only abort:** The operator (or the owner) may set `WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED=false` at any time, with no commit, and the boundary will refuse to make HTTP calls. The boundary has a `disabled` reason for this; the caller sees a structured return with `ok=False, reason="disabled"`.

**Self-abort:** The boundary's `boundary_self_abort()` function (called from inside the boundary) sets a process-global flag that makes every subsequent call in the same process return `ok=False, reason="boundary_self_aborted"`. This is the "I just noticed I leaked, stop calling me" lever. It is not a substitute for a code fix.

---

## 17. Next lane recommendation

The recommended next lane, in order of priority, is **not** "make the live boundary bigger." The recommended next lane is **shrink**: prove the design is correct by making the live boundary *do less*.

| Priority | Lane | Why |
|---|---|---|
| 1 | **Implement the `weslr_controlled_live_searxng_metadata_only_boundary_v1` module** as a pure-Python function in a new file `weslr/controlled_live_searxng_metadata_only_boundary.py`. The implementation is a 250-line module: HTTP call, field allow-list, per-result blocking, derived enums, structured return. | this is the smallest surface that exercises the design |
| 2 | **Add the unit tests from section 14.1** to `weslr/tests/test_controlled_live_searxng_metadata_only_boundary_v1.py`. All 27 tests must pass without a live HTTP call. | proves the module is correct before any live call |
| 3 | **Add the live-test fixture** to the test file. One test issues a real call to the actual SearXNG container, with `WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED=true` and the env-var allow-list from section 15. The test is gated behind a `pytest.mark.live_searxng` marker so it does not run by default. | proves the boundary holds against a real SearXNG response |
| 4 | **Hand the first safe sample to the operator.** The operator runs the live test by hand, captures the stderr line, inspects the shape, and decides whether to proceed. | this is the owner-approval checkpoint, not a code lane |
| 5 | **(NOT in scope for this design)** Once the live test passes, the *next* design (a separate doc, a separate commit) may define how the boundary's structured return is *routed* into the existing MLCF sink for one specific query family. That is a separate lane with its own boundary. | keeps each lane small and reviewable |
| 6 | **(NOT in scope for this design)** Snippet policy. The default is `disabled`. Enabling snippets is a separate lane with its own boundary, its own privacy review, and its own operator-CC requirements. | the snippet is the highest-risk surface; do not enable it in the same lane as the live call itself |

What the next lane must NOT do:

- Connect the boundary to the MLCF sink automatically. The MLCF sink is the *next* lane.
- Connect the boundary to the omnichat contract-reply engine. Not in any lane; the boundary is not a user-facing feature.
- Connect the boundary to the chat responder, the chat UI, the protected preview, or the public weslr.de site. Not in any lane.
- Add a cache layer, a retry layer, a rate-limit layer, a per-session quota, a per-user quota. All of these are separate lanes.
- Add multi-language support, time-range filters, category filters, engine selection, or pagination. All separate lanes.
- Switch to HTTPS. Separate lane.
- Switch to a non-loopback SearXNG. Separate lane (and may be forbidden in perpetuity).
- Make any claim, summary, paraphrase, or evidence elevation. Forbidden.

---

## Summary

This design defines a controlled live SearXNG boundary that:

- Pulls `origin/master` (`f7acdb15`) onto a new branch `mlcf-master-pull-20260613` without touching the existing `scatti-audit-bundle-v2` working tree.
- Confirms SearXNG is locally available on `127.0.0.1:8888` but issues no live call in this design lane.
- Restricts the HTTP shape to one GET with `q`, `format=json`, and a small set of optional parameters.
- Enforces a strict allow-list of metadata fields; drops everything else at parse time.
- Derives a small set of enum-valued fields (no narratives, no claim language).
- Blocks at the URL level: loopback/private networks, login pages, credential URLs, personal-data platforms, tracking-only domains.
- Does not retain raw content, snippets by default, or any of the forbidden fields.
- Produces a structured return whose keys are exactly the allow-list in section 12; no `summary`, no `evidence`, no `trusted`, no `*_authority` flags.
- Never retries, never caches, never writes to disk (other than stderr), never accumulates state across calls.
- Does not call the MLCF sink itself; the operator routes the result to the sink in a separate lane.
- Is validated by 27 unit tests (mocked SearXNG), 1 integration test (mocked HTTP), and 1 live test (the first safe sample, owner-authorized, hand-issued).
- Is compatible with the WESLR release gate subject to the `docs/WESLR_*.md` scope-exception note in section 14.5.
- Does not modify any of the protected files.
- Defines a clear rollback path and a clear "what next lane is" recommendation that does not include making the live boundary bigger.

The working principle holds: SearXNG is a metadata locator, not an evidence engine. This design enforces that at the HTTP layer, the field layer, the enum layer, the call-shape layer, the caller layer, and the storage layer.
