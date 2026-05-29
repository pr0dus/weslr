# WESLR V1 Website Operations Boundary and Process Inventory V1

Date: 2026-05-29
Status: operations discovery / boundary report only
Repository: `/home/pr0/projects/weslr-v1-ui-website`
Branch: `ocw-weslr-v1-ui-20260529`

---

## 1. Purpose

Before any WESLR website implementation, this document records the current server, process, domain, cron, and tunnel state and defines strict off-limits boundaries.

**This document does NOT:**
- Implement website code
- Edit website files
- Change DNS
- Change Cloudflare tunnels
- Stop processes
- Delete cronjobs
- Touch e-qubs.de
- Touch plantdelux.ro
- Modify WESLR runtime files
- Modify weslr/chat_responder.py
- Modify weslr/main.py

---

## 2. Hard Boundaries (OFF LIMITS)

### 2.1 Domains OFF LIMITS

| Domain | Status | Reason |
|--------|--------|--------|
| e-qubs.de | OFF LIMITS | User's main business website |
| www.e-qubs.de | OFF LIMITS | User's main business website |
| plantdelux.ro | OFF LIMITS | Active PlantDelux venture site |
| www.plantdelux.ro | OFF LIMITS | Active PlantDelux venture site |
| plant.plantdelux.ro | OFF LIMITS | Active PlantDelux secondary site |

### 2.2 Ports OFF LIMITS

| Port | Process | Domain | Status |
|------|---------|--------|--------|
| 8097 | Python http.server | e-qubs.de (via Cloudflare) | OFF LIMITS |
| 8083 | Python http.server | plantdelux.ro | OFF LIMITS |
| 8085 | Python (inbound-email-handler) | PlantDelux webhook | OFF LIMITS |
| 8888 | SearXNG (Docker) | Internal search | OFF LIMITS |
| 11434 | Ollama | Local AI inference | OFF LIMITS |

### 2.3 Processes OFF LIMITS

| PID | Process | Purpose | Status |
|-----|---------|---------|--------|
| 262376 | Python http.server (8097) | e-qubs.de static site | OFF LIMITS |
| 1418101 | Python http.server (8083) | plantdelux.ro static site | OFF LIMITS |
| 1673516 | Python inbound-email-handler | PlantDelux email handling | OFF LIMITS |
| 993439 + workers | nginx master/workers | Reverse proxy | OFF LIMITS |
| 1677 | cloudflared | Cloudflare tunnel | OFF LIMITS |

### 2.4 Services OFF LIMITS

| Service | Status |
|---------|--------|
| nginx.service | OFF LIMITS |
| cloudflared.service | OFF LIMITS |
| plantdelux-site.service | OFF LIMITS (if exists) |
| ollama.service | OFF LIMITS |
| docker.service | OFF LIMITS |
| containerd.service | OFF LIMITS |

### 2.5 Cloudflare Tunnels OFF LIMITS

| Tunnel | Domain | Status |
|--------|--------|--------|
| Tunnel token in cloudflared process | e-qubs.de, plantdelux.ro | OFF LIMITS |

The cloudflared process (PID 1677) is running with a tunnel token that serves e-qubs.de and plantdelux.ro traffic. **DO NOT touch this tunnel.**

---

## 3. Repo State

### 3.1 Current Repository

| Field | Value |
|-------|-------|
| Path | `/home/pr0/projects/weslr-v1-ui-website` |
| Branch | `ocw-weslr-v1-ui-20260529` |
| HEAD | `49b96c6` |
| Status | 1 untracked file (UI spec doc) |

### 3.2 Git Status

```
?? docs/WESLR_V1_UI_COMPONENT_AND_VISUAL_INTERACTION_SPEC_V1.md
```

### 3.3 Related Repositories

| Path | Purpose | Status |
|------|---------|--------|
| `/home/pr0/weslr-landing/` | Static landing page for www.weslr.de | WESLR-related |
| `/home/pr0/projects/weslr/` | WESLR core + demo server | WESLR-related |
| `/home/pr0/projects/weslr-tia-openness-bridge/` | TIA Portal integration | WESLR-related |
| `/home/pr0/projects/plantdelux-site/` | PlantDelux static site | OFF LIMITS |
| `/home/pr0/plantdelux_lab/` | PlantDelux venture docs | OFF LIMITS |

---

## 4. Running Processes Inventory

### 4.1 Full Process List (Relevant)

| PID | Process | Command | Classification |
|-----|---------|---------|----------------|
| 1677 | cloudflared | `/usr/bin/cloudflared --no-autoupdate tunnel run --token ...` | OFF LIMITS (serves e-qubs, plantdelux) |
| 262376 | Python http.server | `/usr/bin/python3 -m http.server 8097 --bind 0.0.0.0` | OFF LIMITS (e-qubs) |
| 1418101 | Python http.server | `/usr/bin/python3 -m http.server 8083 --bind 0.0.0.0` | OFF LIMITS (plantdelux) |
| 1673516 | Python | `python3 inbound-email-handler.py` | OFF LIMITS (plantdelux webhook) |
| 3595174 | Python | `python3 /home/pr0/projects/weslr/deploy/staging/weslr_demo_server.py` | WESLR-related |
| 3515 | Python (searxng) | `/usr/local/searxng/.venv/bin/python3 -c from multiprocessing...` | OFF LIMITS (internal) |
| 993439 | nginx master | `/usr/sbin/nginx -g daemon on; master_process on;` | OFF LIMITS |
| 1559893-1559910 | nginx workers | 18 worker processes | OFF LIMITS |
| 431589 | openclaw-gateway | OpenClaw gateway process | OFF LIMITS |

### 4.2 Classification Summary

| Classification | Count | Action |
|----------------|-------|--------|
| OFF LIMITS | 30+ | Do not touch |
| WESLR-related | 1 | Safe to investigate, requires approval to modify |
| Safe/Unknown | 0 | N/A |

---

## 5. Listening Ports

### 5.1 Port Inventory

| Port | Process | Local Address | Likely Service | Classification |
|------|---------|---------------|----------------|----------------|
| 80 | nginx | 0.0.0.0 | Reverse proxy (Ollama/webhook) | OFF LIMITS |
| 5353 | mDNS/Avahi | 0.0.0.0 / :: | mDNS discovery | System (ignore) |
| 631 | cups | 127.0.0.1 | Print server | System (ignore) |
| 8080 | Python (weslr_demo_server) | 0.0.0.0 | WESLR demo server | WESLR-related |
| 8082 | nginx | 0.0.0.0 | Webhook proxy | OFF LIMITS |
| 8083 | Python http.server | 0.0.0.0 | plantdelux.ro | OFF LIMITS |
| 8085 | Python inbound-email | 0.0.0.0 | PlantDelux webhook handler | OFF LIMITS |
| 8097 | Python http.server | 0.0.0.0 | e-qubs.de | OFF LIMITS |
| 8888 | Docker (searxng) | 0.0.0.0 / :: | SearXNG search | OFF LIMITS |
| 11434 | Ollama | 127.0.0.1 | Local AI inference | OFF LIMITS |
| 18789 | openclaw-gateway | 127.0.0.1 / ::1 | OpenClaw internal | OFF LIMITS |
| 20241 | unknown | 127.0.0.1 | Unknown | Investigate later |

### 5.2 Port Classification

| Port | Domain/Service | Status |
|------|----------------|--------|
| 8097 | e-qubs.de | OFF LIMITS |
| 8083 | plantdelux.ro | OFF LIMITS |
| 8085 | PlantDelux webhook | OFF LIMITS |
| 8082 | nginx webhook proxy | OFF LIMITS |
| 8888 | SearXNG | OFF LIMITS |
| 11434 | Ollama | OFF LIMITS |
| 80 | nginx (Ollama/webhook) | OFF LIMITS |
| 8080 | WESLR demo server | WESLR-related (investigate) |

---

## 6. Systemd Services

### 6.1 Running Services (Relevant)

| Service | Status | Classification |
|---------|--------|----------------|
| nginx.service | running | OFF LIMITS |
| cloudflared.service | running | OFF LIMITS |
| ollama.service | running | OFF LIMITS |
| docker.service | running | OFF LIMITS |
| containerd.service | running | OFF LIMITS |
| fail2ban.service | running | System (OFF LIMITS) |
| cron.service | running | System (OFF LIMITS) |
| plantdelux-site.service | running? | OFF LIMITS (if exists) |

### 6.2 Systemd Timers

| Timer | Next Run | Status |
|-------|----------|--------|
| anacron.timer | Fri 2026-05-29 17:32 | System |
| sysstat-collect.timer | Fri 2026-05-29 17:40 | System |
| fwupd-refresh.timer | Fri 2026-05-29 18:27 | System |
| Others | Various | System timers |

**No custom WESLR timers found.**

---

## 7. Cronjobs

### 7.1 User Crontab

```
No user crontab
```

### 7.2 Root Crontab

```
No root crontab (or no sudo access)
```

### 7.3 System Cron Directories

| Directory | Contents |
|-----------|----------|
| /etc/cron.d | anacron, e2scrub_all, sysstat (system) |
| /etc/cron.daily | Standard Ubuntu daily tasks |
| /etc/cron.hourly | Placeholder only |
| /etc/cron.weekly | Standard Ubuntu weekly tasks |
| /etc/cron.monthly | Standard Ubuntu monthly tasks |

### 7.4 Cron Classification

| Cron | Related To | Status |
|------|-----------|--------|
| anacron | System | OFF LIMITS |
| e2scrub_all | System | OFF LIMITS |
| sysstat | System | OFF LIMITS |
| apt-compat | System | OFF LIMITS |
| logrotate | System | OFF LIMITS |

**No WESLR-related cronjobs found.**

**No PlantDelux-related cronjobs found in system cron.**

**No e-qubs-related cronjobs found.**

---

## 8. Cloudflared/Tunnel State

### 8.1 Running Tunnel

| Field | Value |
|-------|-------|
| PID | 1677 |
| Process | `/usr/bin/cloudflared --no-autoupdate tunnel run --token ...` |
| Token | eyJhIjoiNmUzMzY1OTk1MTEwNTc2NjNhOTA4NzI3MGI2NjhmNWEiLCJ0IjoiNDZhNzUwMTktNzI2OC00Mzc4LTgwYjctMGYzMmIzMDA0YTQyIiwicyI6Ik5XVmxaRE5rTWpZdE1EZzBOeTAwTWpkakxXRXhObU10TW1KaE1UZzRaamt4TmpVdyJ9 |

### 8.2 Tunnel Classification

| Tunnel | Domains Served | Status |
|--------|----------------|--------|
| Account token tunnel | e-qubs.de, plantdelux.ro (likely) | OFF LIMITS |

### 8.3 Config Directories

| Directory | Status |
|-----------|--------|
| ~/.cloudflared | Not found |
| /etc/cloudflared | Not found |

The cloudflared tunnel is running via token (not config file). **DO NOT touch this process or its token.**

---

## 9. Nginx/Static Hosting Inventory

### 9.1 Nginx Config Files

| File | Purpose | Status |
|------|---------|--------|
| /etc/nginx/nginx.conf | Main config | OFF LIMITS |
| /etc/nginx/sites-available/default | Default site | OFF LIMITS |
| /etc/nginx/sites-enabled/* | Empty (no sites-enabled) | N/A |
| /etc/nginx/conf.d/ollama-proxy.conf | Ollama + webhook proxy | OFF LIMITS |
| /etc/nginx/conf.d/webhook.conf | Webhook config | OFF LIMITS |

### 9.2 Active Nginx Configuration

**ollama-proxy.conf:**

| Listen Port | Server Name | Proxy Target | Purpose |
|-------------|-------------|--------------|---------|
| 80 | localhost | ollama_backend (127.0.0.1:11434) | Ollama API proxy |
| 80 | localhost | /api/webhook/ → 127.0.0.1:8085 | PlantDelux webhook |
| 8082 | _ | /api/webhook/ → 127.0.0.1:8085 | Webhook fallback |

**No WESLR-specific nginx config found.**

### 9.3 Static Sites

| Port | Directory | Domain | Status |
|------|-----------|--------|--------|
| 8097 | Unknown (served by Python) | e-qubs.de | OFF LIMITS |
| 8083 | /home/pr0/projects/plantdelux-site | plantdelux.ro | OFF LIMITS |
| 8080 | /home/pr0/projects/weslr/deploy/staging | WESLR demo | WESLR-related |

---

## 10. Domain/DNS Intent

### 10.1 Intended Domain Policy

| Domain | Intent | Status |
|--------|--------|--------|
| weslr.de | Primary public website | WESLR-related (investigate) |
| www.weslr.de | Redirect to weslr.de | WESLR-related |
| staging.weslr.de | Private preview | Should be protected |
| chat.weslr.de | Future pilot/app interface | Not public unless approved |
| api.weslr.de | Future backend/API | Not public unless approved |

### 10.2 Current DNS State

| Domain | DNS Result | Status |
|--------|------------|--------|
| weslr.de | No A record (NXDOMAIN) | Needs DNS setup |
| www.weslr.de | 104.21.83.19, 172.67.166.251 (Cloudflare) | Active via Cloudflare |
| plantdelux.ro | 104.21.80.254, 172.67.155.165 (Cloudflare) | OFF LIMITS |

### 10.3 Off-Limits Domains

| Domain | DNS | Status |
|--------|-----|--------|
| e-qubs.de | Not checked (OFF LIMITS) | OFF LIMITS |
| plantdelux.ro | 104.21.80.254, 172.67.155.165 | OFF LIMITS |
| www.plantdelux.ro | Not checked (OFF LIMITS) | OFF LIMITS |
| plant.plantdelux.ro | Not checked (OFF LIMITS) | OFF LIMITS |

---

## 11. WESLR-Related Inventory Summary

### 11.1 WESLR Processes

| PID | Process | Port | Path |
|-----|---------|------|------|
| 3595174 | weslr_demo_server.py | 8080 | /home/pr0/projects/weslr/deploy/staging/ |

### 11.2 WESLR Repositories

| Path | Purpose |
|------|---------|
| /home/pr0/projects/weslr-v1-ui-website | UI spec documentation (current repo) |
| /home/pr0/projects/weslr | Core WESLR + demo server |
| /home/pr0/weslr-landing | Static landing page for www.weslr.de |
| /home/pr0/projects/weslr-tia-openness-bridge | TIA Portal integration |

### 11.3 WESLR DNS

| Domain | Status |
|--------|--------|
| www.weslr.de | Active (Cloudflare) |
| weslr.de | No A record (needs setup) |

### 11.4 WESLR Ports

| Port | Process | Status |
|------|---------|--------|
| 8080 | weslr_demo_server.py | WESLR-related (running) |

---

## 12. PlantDelux/e-qubs Inventory Summary (OFF LIMITS)

### 12.1 PlantDelux Processes

| PID | Process | Port | Purpose |
|-----|---------|------|---------|
| 1418101 | Python http.server | 8083 | plantdelux.ro static site |
| 1673516 | Python inbound-email-handler | 8085 | Email webhook |

### 12.2 e-qubs Processes

| PID | Process | Port | Purpose |
|-----|---------|------|---------|
| 262376 | Python http.server | 8097 | e-qubs.de static site |

### 12.3 Shared Infrastructure (OFF LIMITS)

| Component | Purpose |
|-----------|---------|
| nginx (port 80) | Reverse proxy for Ollama + webhook |
| nginx (port 8082) | Webhook fallback |
| cloudflared (PID 1677) | Cloudflare tunnel for public sites |
| SearXNG (port 8888) | Internal search |

---

## 13. Safe Actions for WESLR Website Implementation

### 13.1 Safe to Do (Requires Owner Approval)

| Action | Notes |
|--------|-------|
| Create DNS records for weslr.de | If not conflicting with existing |
| Create DNS records for staging.weslr.de | Should be protected |
| Create DNS records for chat.weslr.de | Not public unless approved |
| Create DNS records for api.weslr.de | Not public unless approved |
| Deploy static site to new port | e.g., 8081, 8084, 8086 |
| Configure nginx for WESLR domain | New config, don't modify existing |
| Create new Cloudflare tunnel for WESLR | Separate from existing tunnel |

### 13.2 Forbidden Actions

| Action | Reason |
|--------|--------|
| Stop any process on port 8097, 8083, 8085 | OFF LIMITS |
| Modify nginx config for port 80, 8082 | OFF LIMITS |
| Touch cloudflared process (PID 1677) | OFF LIMITS |
| Modify plantdelux-site files | OFF LIMITS |
| Modify e-qubs static site files | OFF LIMITS |
| Change DNS for plantdelux.ro, e-qubs.de | OFF LIMITS |
| Modify ollama-proxy.conf | OFF LIMITS |
| Modify webhook.conf | OFF LIMITS |

---

## 14. Open Questions for Owner

### 14.1 DNS Questions

| Question | Options |
|----------|---------|
| Should weslr.de have an A record? | Currently NXDOMAIN |
| Should weslr.de redirect to www.weslr.de? | Common pattern |
| Who manages the Cloudflare account for weslr.de? | Need access for DNS changes |
| Should staging.weslr.de be password-protected? | Recommended for preview |

### 14.2 Hosting Questions

| Question | Options |
|----------|---------|
| Where should the WESLR V1 website be hosted? | New port? New server? Cloudflare Pages? |
| Should WESLR use the same cloudflared tunnel? | Or separate tunnel? |
| What's the intended domain for the public site? | weslr.de? www.weslr.de? Both? |

### 14.3 Process Questions

| Question | Options |
|----------|---------|
| Is the WESLR demo server (port 8080) still needed? | Running since May 2 |
| Should we stop weslr_demo_server.py? | Requires approval |

---

## 15. Recommended Next Lane

`REVIEW_WESLR_V1_WEBSITE_OPERATIONS_BOUNDARY_AND_PROCESS_INVENTORY_V1`

---

## 9. Cronjob Deactivation/Deletion Plan

### 9.1 Cronjob Classification Summary

| Category | Cronjobs | Action |
|----------|----------|--------|
| WESLR-related | None found | No action needed |
| PlantDelux-related | None found | OFF LIMITS |
| e-qubs-related | None found | OFF LIMITS |
| System cronjobs | anacron, e2scrub_all, sysstat, apt-compat, logrotate, etc. | OFF LIMITS (system) |
| Unknown | None found | N/A |

### 9.2 WESLR-Related Cronjobs

**Result: No WESLR-related cronjobs found.**

| Cron Location | Command | Status |
|---------------|---------|--------|
| User crontab | None | N/A |
| Root crontab | None | N/A |
| /etc/cron.d | None WESLR-related | N/A |
| /etc/cron.daily | None WESLR-related | N/A |
| /etc/cron.hourly | None WESLR-related | N/A |
| /etc/cron.weekly | None WESLR-related | N/A |
| /etc/cron.monthly | None WESLR-related | N/A |

### 9.3 Cronjobs That Must Be Preserved (OFF LIMITS)

| Cron Location | Purpose | Status |
|---------------|---------|--------|
| /etc/cron.d/anacron | System anacron | OFF LIMITS |
| /etc/cron.d/e2scrub_all | Filesystem scrub | OFF LIMITS |
| /etc/cron.d/sysstat | System statistics | OFF LIMITS |
| /etc/cron.daily/* | Daily system tasks | OFF LIMITS |
| /etc/cron.weekly/* | Weekly system tasks | OFF LIMITS |
| /etc/cron.monthly/* | Monthly system tasks | OFF LIMITS |
| systemd timers | Various system timers | OFF LIMITS |

### 9.4 Unknown Cronjobs Needing Owner Decision

**Result: None found.**

All cronjobs inspected are system-level and should be preserved.

### 9.5 Proposed Deactivation/Deletion Plan

**No WESLR-related cronjobs found. No deletion required.**

If WESLR-related cronjobs are discovered later, the following approach is recommended:

#### 9.5.1 Backup Before Deletion

```bash
# Backup current crontab
crontab -l > ~/crontab-backup-$(date +%Y%m%d).txt

# Backup root crontab (if accessible)
sudo crontab -l > ~/root-crontab-backup-$(date +%Y%m%d).txt 2>/dev/null || echo "No root crontab"

# Backup system cron directories
sudo tar -czvf ~/cron-backup-$(date +%Y%m%d).tar.gz /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.weekly /etc/cron.monthly
```

#### 9.5.2 Disable-Before-Delete Approach

```bash
# Step 1: Comment out the cronjob (disable)
# Edit crontab and prefix the line with #

# Step 2: Monitor for issues
# Wait 24-48 hours to ensure nothing breaks

# Step 3: Delete the cronjob (after confirmation)
# Remove the commented line from crontab
```

#### 9.5.3 Verification After Deletion

```bash
# Verify crontab is clean
crontab -l

# Verify no WESLR processes are running from cron
ps auxww | grep -i weslr

# Check system logs for cron-related errors
grep CRON /var/log/syslog | tail -50
```

---

## 10. Required Cloudflare Access

### 10.1 Cloudflare Access Requirements for OCW

| Requirement | Value | Reason |
|-------------|-------|--------|
| Scope | weslr.de zone only | Prevents accidental changes to other domains |
| Token Type | Scoped API token | Never use global API key |
| PlantDelux Access | NONE | OFF LIMITS |
| e-qubs Access | NONE | OFF LIMITS |
| DNS Read | YES | Required to inspect current DNS state |
| DNS Edit | YES | Required for weslr.de DNS changes |
| Analytics Read | CONDITIONAL | Only if traffic inspection needed |
| Tunnel Read | CONDITIONAL | Only if tunnel changes required |
| Tunnel Write | CONDITIONAL | Requires separate approval |

### 10.2 Recommended Cloudflare Token Scopes

| Scope | Permissions | Resources |
|-------|-------------|-----------|
| Zone | DNS:Read, DNS:Edit | weslr.de only |
| Zone | Zone:Read | weslr.de only |
| Zone | Analytics:Read (optional) | weslr.de only |
| Account | Tunnel:Read (optional) | Requires separate approval |
| Account | Tunnel:Edit (optional) | Requires separate approval |

### 10.3 Cloudflare Token Creation

**Recommended approach:**

1. Log into Cloudflare dashboard
2. Go to My Profile > API Tokens
3. Create Token > Edit zone DNS
4. Select specific zone: weslr.de
5. Include permissions:
   - Zone > DNS > Edit
   - Zone > Zone > Read
6. Exclude all other zones (PlantDelux, e-qubs)
7. Copy token and store securely

**Token format example:**
```
cfat_G7pPx8E35IX5F27y2uGa9x8iwKvuUkaTujTPCKWv6a9fdb48
```

### 10.4 What NOT to Request

| Forbidden Access | Reason |
|------------------|--------|
| Global API Key | Too permissive |
| All zones access | Risk to PlantDelux and e-qubs |
| PlantDelux zone access | OFF LIMITS |
| e-qubs zone access | OFF LIMITS |
| Account settings access | Unnecessary |
| Billing access | Unnecessary |
| Member management | Unnecessary |

### 10.5 Staging Protection

| Domain | Protection | Approval Required |
|--------|------------|-------------------|
| staging.weslr.de | Password protection recommended | Yes, separate approval |
| chat.weslr.de | Not public unless approved | Yes, before going live |
| api.weslr.de | Not public unless approved | Yes, before going live |

### 10.6 Cloudflare Tunnel Considerations

**Current state:**
- One cloudflared tunnel running (PID 1677)
- Tunnel token embedded in process
- Serves e-qubs.de and plantdelux.ro (OFF LIMITS)

**WESLR tunnel options:**

| Option | Description | Approval Required |
|--------|-------------|-------------------|
| Create new tunnel | Separate tunnel for weslr.de | Yes |
| Use existing tunnel | Add weslr.de to existing tunnel | NO (OFF LIMITS) |
| Cloudflare Pages | Use Cloudflare Pages for static site | Yes |
| Cloudflare Workers | Use Workers for dynamic content | Yes |

**Recommendation:** Create a new, separate tunnel for weslr.de to avoid touching the existing tunnel that serves PlantDelux and e-qubs.

---

## 11. Safety Conclusion

### 11.1 Safe to Proceed?

**Status: CONDITIONALLY SAFE**

WESLR V1 UI spec review and build planning can proceed with the following conditions:

### 11.2 What Must Be Resolved Before Implementation

| Issue | Required Action |
|-------|-----------------|
| DNS for weslr.de | Currently NXDOMAIN. Needs A record or Cloudflare tunnel |
| Cloudflare access | Need scoped token for weslr.de zone only |
| Hosting decision | Where will WESLR V1 website be hosted? |
| Staging protection | staging.weslr.de should be password-protected |
| WESLR demo server | Decide if port 8080 process should continue |

### 11.3 What Is Off-Limits

| Category | Components | Reason |
|----------|------------|--------|
| Domains | e-qubs.de, plantdelux.ro, www.plantdelux.ro, plant.plantdelux.ro | Active business sites |
| Ports | 8097, 8083, 8085, 8888, 11434 | Critical services |
| Processes | 262376, 1418101, 1673516, 993439, 1677 | Active services |
| Services | nginx, cloudflared, ollama, docker | Infrastructure |
| Configs | /etc/nginx/*, /etc/cloudflared/* | System configs |
| Cronjobs | All system cronjobs | System stability |

### 11.4 Safe Actions (Require Owner Approval)

| Action | Risk Level | Approval Required |
|--------|------------|-------------------|
| Create DNS for weslr.de | Low | Yes |
| Create new Cloudflare tunnel for WESLR | Medium | Yes |
| Deploy to new port (8081, 8084, 8086) | Low | Yes |
| Create nginx config for WESLR domain | Medium | Yes |
| Stop weslr_demo_server.py (port 8080) | Medium | Yes |

### 11.5 Pre-Implementation Checklist

Before any WESLR website implementation:

- [ ] DNS for weslr.de resolved (A record or tunnel)
- [ ] Cloudflare scoped token created for weslr.de only
- [ ] Hosting location decided (new port, Cloudflare Pages, etc.)
- [ ] Staging protection planned (password protection)
- [ ] Decision on weslr_demo_server.py (port 8080)
- [ ] Owner approval for build phase
- [ ] No changes to e-qubs.de infrastructure
- [ ] No changes to plantdelux.ro infrastructure
- [ ] No changes to existing cloudflared tunnel

### 11.6 Safety Summary

| Check | Status |
|-------|--------|
| e-qubs.de protected | ✅ OFF LIMITS |
| plantdelux.ro protected | ✅ OFF LIMITS |
| No processes stopped | ✅ Confirmed |
| No cronjobs deleted | ✅ Confirmed |
| No DNS changes made | ✅ Confirmed |
| No tunnel changes made | ✅ Confirmed |
| No website code edited | ✅ Confirmed |
| chat_responder.py unchanged | ✅ Confirmed |
| main.py unchanged | ✅ Confirmed |
| Operations discovery only | ✅ Confirmed |

---

## 16. Validation Commands

```bash
# Verify repo state
cd /home/pr0/projects/weslr-v1-ui-website
pwd
git branch --show-current
git rev-parse --short HEAD
git status --short

# Verify no changes to runtime files
git diff --quiet HEAD -- weslr/chat_responder.py
git diff --quiet HEAD -- weslr/main.py

# Verify processes still running
ps auxww | grep -E "http.server|cloudflared|nginx" | grep -v grep
```

---

## 17. Boundary Confirmations

- No website code implemented ✅
- No website files edited ✅
- No DNS changes ✅
- No Cloudflare tunnel changes ✅
- No processes stopped ✅
- No cronjobs deleted ✅
- e-qubs.de untouched ✅
- plantdelux.ro untouched ✅
- No WESLR runtime file changes ✅
- weslr/chat_responder.py unchanged ✅
- weslr/main.py unchanged ✅
- This is operations discovery only ✅

---

## 18. Document Status

**Status:** Operations discovery / boundary report only
**Implementation:** Requires separate approval
**Changes Made:** None (documentation only)

---

## 19. Final Report

### 19.1 Handshake Result

**Result:** OPS_INVENTORY_COMPLETE

### 19.2 Repo State

| Field | Value |
|-------|-------|
| Repo Path | `/home/pr0/projects/weslr-v1-ui-website` |
| Branch | `ocw-weslr-v1-ui-20260529` |
| Start HEAD | `49b96c6` |
| End HEAD | `49b96c6` (no commit made) |
| Files Changed | `docs/WESLR_V1_UI_COMPONENT_AND_VISUAL_INTERACTION_SPEC_V1.md` (untracked) |
| | `docs/WESLR_V1_WEBSITE_OPERATIONS_BOUNDARY_AND_PROCESS_INVENTORY_V1.md` (untracked) |

### 19.3 Process Inventory Summary

| Classification | Count | Action |
|----------------|-------|--------|
| OFF LIMITS (e-qubs) | 1 process (port 8097) | Do not touch |
| OFF LIMITS (PlantDelux) | 2 processes (ports 8083, 8085) | Do not touch |
| OFF LIMITS (infrastructure) | nginx, cloudflared, ollama, docker | Do not touch |
| WESLR-related | 1 process (port 8080) | Investigate, requires approval |

### 19.4 Port Inventory Summary

| Port | Process | Classification |
|------|---------|----------------|
| 80 | nginx reverse proxy | OFF LIMITS |
| 8080 | weslr_demo_server.py | WESLR-related |
| 8082 | nginx webhook proxy | OFF LIMITS |
| 8083 | plantdelux.ro static site | OFF LIMITS |
| 8085 | PlantDelux email webhook | OFF LIMITS |
| 8097 | e-qubs.de static site | OFF LIMITS |
| 8888 | SearXNG search | OFF LIMITS |
| 11434 | Ollama AI inference | OFF LIMITS |

### 19.5 Cronjob Classification Summary

| Category | Count | Action |
|----------|-------|--------|
| WESLR-related cronjobs | 0 | None found |
| System cronjobs | All | OFF LIMITS |
| PlantDelux cronjobs | 0 | None found |
| e-qubs cronjobs | 0 | None found |
| Unknown cronjobs | 0 | None found |

**No WESLR-related cronjobs found. No deletion required.**

### 19.6 Cloudflared/Tunnel Summary

| Field | Value |
|-------|-------|
| PID | 1677 |
| Process | `/usr/bin/cloudflared --no-autoupdate tunnel run --token ...` |
| Config | Token-based (no config file) |
| Domains Served | e-qubs.de, plantdelux.ro (likely) |
| Classification | OFF LIMITS |

### 19.7 Off-Limits Confirmation

| Domain | Status |
|--------|--------|
| e-qubs.de | ✅ OFF LIMITS |
| plantdelux.ro | ✅ OFF LIMITS |
| www.plantdelux.ro | ✅ OFF LIMITS |
| plant.plantdelux.ro | ✅ OFF LIMITS |

### 19.8 Process Safety Confirmation

| Check | Result |
|-------|--------|
| No processes stopped | ✅ Confirmed |
| No processes modified | ✅ Confirmed |
| No processes restarted | ✅ Confirmed |

### 19.9 Cronjob Safety Confirmation

| Check | Result |
|-------|--------|
| No cronjobs deleted | ✅ Confirmed |
| No cronjobs disabled | ✅ Confirmed |
| No cronjobs modified | ✅ Confirmed |

### 19.10 DNS/Tunnel Safety Confirmation

| Check | Result |
|-------|--------|
| No DNS changes made | ✅ Confirmed |
| No Cloudflare tunnel changes made | ✅ Confirmed |
| No Cloudflare API calls made | ✅ Confirmed |

### 19.11 Code Safety Confirmation

| Check | Result |
|-------|--------|
| No website code edited | ✅ Confirmed |
| No weslr-ui/ changes | ✅ Confirmed |
| No dashboard changes | ✅ Confirmed |
| No runtime file changes | ✅ Confirmed |
| chat_responder.py unchanged | ✅ Confirmed |
| main.py unchanged | ✅ Confirmed |

### 19.12 Required Cloudflare Access

| Access | Required | Approval |
|---------|----------|----------|
| DNS read (weslr.de) | Yes | Yes |
| DNS edit (weslr.de) | Yes | Yes |
| Analytics read | Conditional | If needed |
| Tunnel read/write | Conditional | Separate approval |

### 19.13 Pre-Implementation Requirements

Before any WESLR website implementation:

1. **DNS Resolution**: weslr.de currently returns NXDOMAIN
2. **Cloudflare Token**: Need scoped token for weslr.de only
3. **Hosting Decision**: Where will WESLR V1 be hosted?
4. **Staging Protection**: Password-protect staging.weslr.de
5. **Owner Approval**: Build phase requires approval

### 19.14 Safety Conclusion

**Status: CONDITIONALLY SAFE**

- WESLR V1 UI spec review can proceed
- Build planning can proceed
- Implementation requires owner approval and DNS/hosting decisions
- e-qubs.de and plantdelux.ro remain fully protected
- No changes made to any running services

---

## 20. Recommended Next Lane

`REVIEW_WESLR_V1_WEBSITE_OPERATIONS_BOUNDARY_AND_PROCESS_INVENTORY_V1`

---

*End of WESLR V1 Website Operations Boundary and Process Inventory V1*