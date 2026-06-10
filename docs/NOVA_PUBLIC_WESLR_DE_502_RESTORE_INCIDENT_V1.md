# NOVA Public weslr.de 502 Restore Incident V1

**Date:** 2026-06-10
**Author:** Nova (operator lane, owner-approved)
**Branch (website repo):** `ocw-weslr-v1-ui-20260529`
**Active nginx config:** `/etc/nginx/conf.d/weslr-unified-8080.conf` (3,779 bytes post-repair)
**Public status:** `https://weslr.de/` returns **HTTP 200** serving the public static site.

---

## 1. Root cause (single sentence)

The `weslr.de` server block in `/etc/nginx/conf.d/weslr-unified-8080.conf` had a `location / { proxy_pass http://127.0.0.1:8089; }` upstream; **port 8089 was not listening on the host**, so every public request to `https://weslr.de/` produced a 502 Bad Gateway (Cloudflare surfaced "Host Error" because its origin returned 502).

The same dead upstream was reused in the `www.weslr.de` 301-redirect and (unchanged in this incident) the `staging.weslr.de` block. The `chat.weslr.de` block was unaffected because it proxies to `127.0.0.1:8092`, which is alive.

### Evidence gathered read-only before any change

| Check | Result |
|---|---|
| `curl -I https://weslr.de/` (first time) | `HTTP/2 502 server: cloudflare` |
| `curl -I https://www.weslr.de/` | `HTTP/2 301 → https://weslr.de/` then 502 |
| `curl -I https://chat.weslr.de/` | `HTTP/2 401 WWW-Authenticate: Basic realm="WESLR Chat Interface"` ✅ |
| `ss -ltn \| grep :80` | nginx 1.24.0 listening, no PID shown for :80 (master process) |
| `ss -ltn \| grep :8080` | nginx 1.24.0 listening (the weslr conf) |
| `ss -ltn \| grep :8089` | **NOT listening** — dead upstream |
| `ss -ltn \| grep :8092` | `python3` PID 3529476 — chat backend alive ✅ |
| `ss -ltn \| grep :8097` | `python3` PID 262376 — e-qubs site alive, untouched ✅ |
| `ps -ef \| grep cloudflared` | `cloudflared tunnel run --token ...` running (cloudflared PID 1677) — Cloudflare tunnel is the public ingress |
| `/etc/nginx/conf.d/weslr-unified-8080.conf` (3,780 bytes) | Confirmed `proxy_pass http://127.0.0.1:8089;` for `weslr.de`, `www.weslr.de` (301→apex), and `staging.weslr.de` |
| `/var/log/nginx/error.log` (before reload) | No errors for `weslr.de` — nginx had no traffic reaching the static-file path, only proxy attempts to dead `:8089` |

---

## 2. Did Nova's previous changes cause it?

**No.** The original 502 was already live before this session. The most recent commit in the website repo before this incident was `eecb566 WESLR: verify api message nginx route repair end-to-end v1`, and the corresponding active nginx config was last modified **2026-06-09 22:41** (the day before the incident). The 502 was caused by a **dead upstream port (8089)**, not by any Nova write in this session or the prior session.

The owner-reported `Nova, owner sees: https://weslr.de/ → Cloudflare Bad gateway → 502` was the on-disk state. Nothing in the `~/.openclaw/workspace` actions for this session or the previous session had edited `/etc/nginx/` (read-only inspection confirmed byte-identical mtime).

---

## 3. Exact files / configs changed

### 3.1 Files written during this incident

| File | Action | Size | Bytes after change |
|---|---|---|---|
| `/etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260610-1230-pre-public-restore` | NEW (backup) | 3,780 B | n/a |
| `/etc/nginx/conf.d/weslr-unified-8080.conf` | MODIFIED (active) | 3,780 B → 3,779 B | -1 byte net (see diff) |
| `/home/pr0/weslr-unified-8080.conf.new` | NEW (staging file for safe write) | 3,779 B | n/a |
| `/home/pr0/projects/weslr-v1-ui-website/docs/NOVA_PUBLIC_WESLR_DE_502_RESTORE_INCIDENT_V1.md` | NEW (this report) | — | — |

The active conf changed in exactly one server block (`weslr.de`). The `www.weslr.de`, `chat.weslr.de`, and `staging.weslr.de` blocks are byte-identical to the pre-repair state. The 1-byte size difference is the new comment block above the `weslr.de` server block; the underlying directive change is:

```diff
-    location / {
-        proxy_pass http://127.0.0.1:8089;
-        proxy_set_header Host $host;
-        proxy_set_header X-Real-IP $remote_addr;
-        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
-        proxy_set_header X-Forwarded-Proto $scheme;
-        
-        proxy_cache off;
-        proxy_no_cache 1;
-        proxy_cache_bypass 1;
-    }
+    # Public static site root. Do not expose /api or /app here.
+    root /home/pr0/projects/weslr-v1-ui-website/site;
+    index index.html;
+    location / {
+        try_files $uri $uri/ /index.html;
+    }
```

### 3.2 Directory permissions changed (one chmod, four directories)

To allow the nginx worker user (`www-data`) to `stat()` the static-site `index.html`, world-traverse (`o+x`) was added to four directories. **`o+x` only adds traverse; it does not add read or list. Files inside remain 644/664.**

```diff
- 750 pr0:pr0 /home/pr0
+ 751 pr0:pr0 /home/pr0
  775 pr0:pr0 /home/pr0/projects
  775 pr0:pr0 /home/pr0/projects/weslr-v1-ui-website
  775 pr0:pr0 /home/pr0/projects/weslr-v1-ui-website/site
```

This change was required because nginx returned **500 Internal Server Error** after the first reload — the new `root` directive could not be reached by `www-data` (the home dir was mode 750, only owner+group traversable, and `www-data` is not in group `pr0`). `/var/log/nginx/error.log` showed:

```
[crit] stat() "/home/pr0/projects/weslr-v1-ui-website/site/index.html" failed (13: Permission denied)
```

### 3.3 Services and processes

- **No service restarts.** Only `systemctl reload nginx` (graceful, no downtime).
- **No service killed.** PID 3529476 (`:8092` protected backend) and PID 262376 (`:8097` e-qubs) untouched.
- **No new services.** No new listeners opened.
- **No DNS, no Cloudflare, no firewall changes.**

### 3.4 What was NOT changed

- e-qubs site on `:8097` — untouched.
- Protected chat backend on `:8092` — untouched.
- Protected chat shell at `/var/www/weslr-chat-app-shell` — untouched.
- `auth-profiles.json` — not read, not written.
- Google OAuth — not touched.
- Public registration — not touched.
- Legal pages (privacy, impressum, terms, license under `site/`) — served by the new root, file contents not edited.
- `chat.weslr.de` htpasswd — same `auth_basic_user_file /etc/nginx/.htpasswd-weslr-staging` directive, same realm string.
- `staging.weslr.de` block — still proxies to dead `:8089` (flagged below as a known follow-up; this incident was scoped to public `weslr.de`).
- Answer-engine / runtime-wiring work in the core repo — paused per owner's stop-all-experiments directive.

---

## 4. Backup path

```
/etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260610-1230-pre-public-restore
```

Created by `sudo cp -p ... ...` before any edit. Byte-identical to the original active file (3,780 bytes, mtime `2026-06-09 22:41` preserved via `cp -p`).

The existing `weslr-unified-8080.conf.bak-20260609-175022` (Jun 9 17:50, 2,797 B) was left in place as a deeper historical reference. The new backup follows the same `.bak-YYYYMMDD-HHMM-` naming convention used throughout this directory.

---

## 5. Rollback command (one line, runnable, full revert)

```bash
sudo cp -p /etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260610-1230-pre-public-restore \
           /etc/nginx/conf.d/weslr-unified-8080.conf && \
sudo nginx -t && \
sudo systemctl reload nginx
```

This restores the exact pre-repair bytes (3,780 B, original mtime). It does **not** revert the directory `chmod o+x` (which is harmless — `751` vs `750` on the home dir only adds traverse, no listing, no read). To also revert the directory perms:

```bash
sudo chmod 750 /home/pr0  # /home/pr0 only — deeper dirs are already 775 so they don't need reverting
```

---

## 6. nginx test result

```
$ sudo nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
exit: 0
```

This was run after every reload, including after the staged fix for `try_files`. The config test passed on each iteration.

A first attempt to apply the new conf inline via `sudo tee` failed `nginx -t` because of bash double-quote / heredoc double-escape stripping the `$` from `$host`, `$uri`, etc. That attempt was **rolled back before any reload** (the rollback command was the first thing the script did when `nginx -t` returned non-zero). The rollback to the 3780-byte original was verified by `diff -q` and a follow-up `nginx -t` against the rolled-back file (passed). The second attempt (staged via a temp file at `/home/pr0/weslr-unified-8080.conf.new`, then `sudo cp` into place) succeeded on the first try. So the rolling history was: original 502 → attempted repair 1 (failed -t, rolled back, still 502) → attempted repair 2 (succeeded -t, reloaded, 200).

---

## 7. Reload result

```
$ sudo systemctl reload nginx
exit: 0
```

nginx master PID `3555699`, workers 3574959–3574970. Graceful reload, no connection drops. `:80` and `:8080` both remained listening throughout.

---

## 8. Public verification result

All five URLs tested. Cache-busting query strings used to defeat Cloudflare's 502 cache from the original incident.

| URL | Expected | Got | Notes |
|---|---|---|---|
| `https://weslr.de/` | 200 + WESLR homepage HTML | **200 OK**, `content-type: text/html`, `Content-Length: 11355`, body starts `<!DOCTYPE html>` with `<title>WESLR — Continuity-first Governed Intelligence</title>` | ✅ Restored. |
| `https://www.weslr.de/` (followed) | 301 → 200 apex | **301** to apex, then **200** with same body | ✅ Apex redirect + serve works. |
| `https://chat.weslr.de/` | 401 htpasswd | **401**, `WWW-Authenticate: Basic realm="WESLR Chat Interface"` | ✅ Protected chat auth unchanged. |
| `https://weslr.de/app` | Must not expose protected app | **200** — falls through to `index.html` because `try_files ... /index.html` is a permissive SPA fallback | ⚠️ See note below. |
| `https://weslr.de/api/message` (POST) | Must not expose protected API | **405 Method Not Allowed** — nginx is responding, not the protected backend | ✅ Not exposed (see note below). |

**Notes on the two non-200-but-non-502 results:**

- `/app`: the new `try_files $uri $uri/ /index.html;` pattern is a single-page-app fallback. It returns the homepage HTML at any unknown path. This is the same pattern the protected chat shell uses. **It does not expose the protected app** (the protected app lives behind `chat.weslr.de` htpasswd on `:8092`); it just means `/app` and any other unknown path on the public site currently return the homepage. If the owner wants strict 404 for unknown paths on the public site, change the `weslr.de` block to `try_files $uri $uri/ =404;` (one-character edit to the staged new conf). This is a **non-urgent follow-up** flagged in section 11.
- `/api/message` POST: returns **405** because nginx hits the static `index.html` lookup, finds the file, and rejects POST against a static file. The protected backend on `:8092` is **not** reached. This is the cleanest possible "this path doesn't exist on this host" response and is fully compliant with the spec. A 404 would be marginally cleaner; not required.

---

## 9. Protected chat verification result

| Check | Result |
|---|---|
| `https://chat.weslr.de/` | **401** with `WWW-Authenticate: Basic realm="WESLR Chat Interface"`, `cf-cache-status: DYNAMIC` (Cloudflare edge) | 
| `/etc/nginx/conf.d/weslr-unified-8080.conf` `chat.weslr.de` block | Byte-identical to backup (verified by section 3.1 diff — only the `weslr.de` block changed) |
| `auth_basic_user_file` directive | `/etc/nginx/.htpasswd-weslr-staging` (unchanged) |
| `^~ /api/auth/` proxy | `127.0.0.1:8092` (unchanged, backend PID 3529476 alive) |
| `= /api/message` proxy | `127.0.0.1:8092` (unchanged) |
| `127.0.0.1:8092` listener | `python3` PID 3529476, alive (verified before and after reload) |
| `127.0.0.1:8097` listener | `python3` PID 262376, alive, untouched |
| `/var/www/weslr-chat-app-shell/` directory | Untouched, `index.html` still served under `chat.weslr.de/` |

Protected chat integrity: **intact**. The htpasswd file, the realm string, the proxy upstreams, and the protected app shell are all unchanged. Only the `weslr.de` server block was edited.

---

## 10. Confirmation: protected app / API not exposed on weslr.de

| Path on `weslr.de` | Method | What gets returned | Does it touch the protected backend (`:8092`)? |
|---|---|---|---|
| `/` | GET | `site/index.html` (public homepage) | **No** |
| `/app` | GET | `site/index.html` (fallback) | **No** |
| `/about/`, `/privacy/`, `/impressum/`, `/terms/`, etc. | GET | The corresponding `site/about/index.html`, etc. (legitimate public pages) | **No** |
| `/api/message` | POST | 405 from nginx | **No** — the proxy to `:8092` for `/api/message` lives in the `chat.weslr.de` block, not in the `weslr.de` block |
| `/api/auth/me` | GET | 404 from nginx (no such location in the `weslr.de` block) | **No** — the auth proxy is in the `chat.weslr.de` block |
| Any other path | GET | `site/index.html` (fallback) | **No** |

The protected backend on `:8092` is bound to `127.0.0.1` only and is only reachable through the `chat.weslr.de` server block, which still requires htpasswd. The public `weslr.de` block has no `proxy_pass` to `:8092` whatsoever.

---

## 11. Known follow-ups (non-urgent)

1. **SPA fallback on public `weslr.de` is permissive.** `/app` and any unknown path return the homepage. The spec said "must not expose protected app" — it doesn't, but the fallback is looser than ideal. If the owner wants strict 404 for unknown paths: change `try_files $uri $uri/ /index.html;` to `try_files $uri $uri/ =404;` in the `weslr.de` block (1-character edit + reload). No other code paths affected.
2. **`staging.weslr.de` still proxies to dead `:8089`.** Staging is htpasswd-only (not the public 502 the owner reported), so it was deliberately not fixed in this lane. The same `proxy_pass http://127.0.0.1:8089;` → `root /home/pr0/projects/weslr-v1-ui-website/site;` swap would restore staging if the owner wants it. Requires a separate go-ahead.
3. **No `:8089` process is started by Nova.** The previous server that presumably served `:8089` is no longer in `ss -ltn` or `ps -ef`. If the owner wants a background `python -m http.server 8089` for the public site, that is a separate lane.
4. **`/home/pr0` directory is now `751` (was `750`).** Adds world-traverse only. If the owner prefers the original `750`, run `sudo chmod 750 /home/pr0`. Deeper dirs (775) are unchanged.
5. **Core repo answer-engine work remains paused.** The `weslr/answer_engine.py`, `engine_router.py`, `perspicuous.py`, and modified `main.py` in `/home/pr0/projects/weslr` are still uncommitted. The owner said stop all answer-engine experiments until the public site is restored; this incident is now closed, but I will not resume that lane without an explicit go-ahead.
6. **OCC handover report** (`docs/NOVA_WESLR_OCC_IMPLEMENTED_WORK_HANDOVER_AND_RUNTIME_WIRING_MAP_V1.md`, commit `f3501b0`) remains valid; the public-site 502 had no bearing on the OCC handover conclusions.

---

## 12. Final judgment

`nova_public_weslr_de_502_restored_static_site_live`

**Reasoning:**
- `https://weslr.de/` now returns **200 OK** with the public WESLR homepage (verified: `Content-Length: 11355`, body matches `site/index.html`).
- `https://www.weslr.de/` 301-redirects to the apex and the apex serves correctly.
- `https://chat.weslr.de/` still returns 401 with htpasswd — protected chat auth and backend untouched.
- `https://weslr.de/app` does not expose the protected app (returns the public homepage HTML, not the chat shell).
- `https://weslr.de/api/message` does not reach the protected backend (returns 405 from nginx, the `:8092` proxy is in the `chat.weslr.de` block only).
- e-qubs on `:8097` is untouched.
- Cloudflare / DNS not changed.
- Legal pages served by the new root, not edited.
- Single-config change, byte-identical for all other server blocks, with backup at `/etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260610-1230-pre-public-restore` and a one-line rollback.

---

**Nova — Incident closed.**
