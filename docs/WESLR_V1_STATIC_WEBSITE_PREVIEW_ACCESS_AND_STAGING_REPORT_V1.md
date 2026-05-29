# WESLR V1 Static Website Preview Access and Staging Report V1

**Created:** 2026-05-29 21:40 CEST
**Branch:** ocw-weslr-v1-ui-20260529
**Purpose:** Record preview access and staging preparation

---

## Phase A — LAN Preview

### Current Server Status

| Property | Value |
|----------|-------|
| Server | Running |
| PID | 2636717 |
| Command | `python3 -m http.server 8089 --directory site/` |
| Bind | `0.0.0.0:8089` (LAN-accessible) |
| Directory | `/home/pr0/projects/weslr-v1-ui-website/site/` |
| WESLR-only | YES |

### LAN Access

| Property | Value |
|----------|-------|
| LAN IP | `192.168.2.47` |
| LAN URL | `http://192.168.2.47:8089/` |
| Status | ✅ WORKING |
| Homepage | 200 OK |
| About page | 200 OK |
| Governance page | 200 OK |

### Protected Sites (UNTOUCHED)

| Port | Site | Status |
|------|------|--------|
| 8097 | e-qubs.de / photovoltaik | ✅ RUNNING |
| 8083 | plantdelux.ro | ✅ RUNNING |
| 8080 | Weslr demo server | ✅ RUNNING |
| 8082 | Webhook handler | ✅ RUNNING |
| 8085 | Webhook backend | ✅ RUNNING |

---

## Phase B — Cloudflare/Staging Discovery

### Cloudflare Zone

| Property | Value |
|----------|-------|
| Zone | `weslr.de` |
| Zone ID | `98d865ca5bb478dcd0b73cd5195b10dd` |
| Status | Active |
| Plan | Free Website |
| Nameservers | `chuck.ns.cloudflare.com`, `melany.ns.cloudflare.com` |

### Token Scope

| Property | Value |
|----------|-------|
| Token Scope | WESLR-only (weslr.de zone) |
| Permissions | DNS, Zone, SSL, Cache, Access, Workers, Logs |
| PlantDelux Zone | NOT accessible |
| Other Zones | NOT accessible |

### DNS Records

| Name | Type | Content | Proxied |
|------|------|---------|---------|
| `weslr.de` | MX | mx.plingest.com | No |
| `*.weslr.de` | MX | mx.plingest.com | No |
| `www.weslr.de` | CNAME | `46a75019-...cfargotunnel.com` | Yes |
| `staging.weslr.de` | CNAME | `46a75019-...cfargotunnel.com` | Yes |
| `_acme-challenge.weslr.de` | CNAME | `_acme-challenge.sslpluslogic.com` | Yes |

### Cloudflare Tunnel

| Property | Value |
|----------|-------|
| Tunnel ID | `46a75019-7268-4378-80b7-0f32b3004a42` |
| Status | Running (PID 1677) |
| Method | Token-based (no local config file) |
| Routes | `www.weslr.de`, `staging.weslr.de` |

### Current Staging State

| URL | Status | Content |
|-----|--------|---------|
| `https://www.weslr.de/` | 502 Bad Gateway | Tunnel not routing |
| `https://staging.weslr.de/` | 200 OK | Old WESLR chat demo (port 8080) |

**Note:** `staging.weslr.de` currently serves the old WESLR chat interface from April, not the new static site.

---

## Phase C — Protected Staging Preparation

### Staging Options

| Option | Pros | Cons |
|--------|------|------|
| **Cloudflare Access** | Enterprise-grade, no code changes | Requires Access plan (not on Free) |
| **Cloudflare Tunnel + Password Gate** | Uses existing tunnel | Requires nginx/app modification |
| **HTTP Basic Auth (nginx)** | Simple, proven | Requires nginx config change |

### Recommended Approach: HTTP Basic Auth

1. Create nginx config for `staging.weslr.de` → proxy to port 8089
2. Add HTTP Basic Auth with owner-provided password
3. Cloudflare Tunnel already routes `staging.weslr.de` to local machine
4. No code changes, no secrets in repo

### Required Owner Decision

**Before proceeding with staging, owner must provide:**

```
Please send the staging password now.
```

- Password will be used for HTTP Basic Auth
- Password will NOT be committed to repo
- Password will NOT be printed in logs
- Password will be stored in `/home/pr0/secrets/` only

### Staging Configuration (After Password Received)

1. Create `/etc/nginx/conf.d/weslr-staging.conf`:
   ```nginx
   server {
       listen 8091;
       server_name staging.weslr.de;
       
       auth_basic "WESLR Staging";
       auth_basic_user_file /etc/nginx/.htpasswd-weslr;
       
       location / {
           proxy_pass http://127.0.0.1:8089;
       }
   }
   ```
2. Create htpasswd file with owner password
3. Update Cloudflare Tunnel to route to port 8091
4. Verify `https://staging.weslr.de/` requires password

---

## Production Status

| Domain | Status | Notes |
|--------|--------|-------|
| `weslr.de` | NOT PRODUCTION | No A/AAAA record, MX only |
| `www.weslr.de` | 502 Bad Gateway | Tunnel not routing correctly |
| `staging.weslr.de` | OLD CHAT DEMO | Needs reconfiguration for static site |

**Production launch remains BLOCKED until:**
- Legal placeholders finalized (Impressum, Privacy, Terms, License)
- Contact email decided
- Owner review complete

---

## Validation Results

| Check | Result |
|-------|--------|
| LAN preview works | ✅ PASS |
| `http://192.168.2.47:8089/` accessible | ✅ PASS |
| Protected sites untouched | ✅ PASS |
| No DNS changes made | ✅ PASS |
| No secrets committed | ✅ PASS |
| chat_responder.py unchanged | ✅ PASS |
| main.py unchanged | ✅ PASS |
| Token scope WESLR-only | ✅ PASS |

---

## Next Steps

1. **Owner reviews LAN preview:** `http://192.168.2.47:8089/`
2. **Owner provides staging password:** Send via Telegram
3. **Configure protected staging:** After password received
4. **Owner reviews legal placeholders:** Impressum, Privacy, Terms, License
5. **Owner decides contact method:** Email, form, or other
6. **Production launch:** After all above complete

---

## Summary

| Item | Status |
|------|--------|
| LAN Preview | ✅ READY — `http://192.168.2.47:8089/` |
| Cloudflare Token Scope | ✅ WESLR-only |
| Cloudflare Tunnel | ✅ Running |
| staging.weslr.de | ⏳ OLD CONTENT — Needs reconfiguration |
| Password Protection | ⏳ WAITING — Owner password required |
| Production Launch | ⏳ BLOCKED — Legal/contact decisions pending |

---

**End of Report V1**