# NOVA_WEBSITE_OPS_BOOTSTRAP_IDENTITY_MEMORY_HARDENING_V1.md

**Date:** 2026-06-09 20:50  
**Status:** CONTEXT HARDENED ✅  
**Repo:** `/home/pr0/projects/weslr-v1-ui-website`

---

## Files Inspected

| File | Status | Notes |
|------|--------|-------|
| `AGENTS.md` | ✅ Inspected | No WESLR-specific updates needed |
| `IDENTITY.md` | ✅ Inspected | No WESLR-specific updates needed |
| `WESLR_WEB_OPS_CONTEXT.md` | ✅ Created | Nova website ops bootstrap |
| `protected-preview/chat-app-shell/index.html` | ✅ Verified | Contains `/api/message` fetch |
| `/var/www/weslr-chat-app-shell/index.html` | ✅ Synced | Matches repo source |
| `docs/NOVA_*.md` | ✅ Inspected | All reports under docs/ |

---

## Files Updated

| File | Change |
|------|--------|
| `WESLR_WEB_OPS_CONTEXT.md` | Created - Operating instructions |
| `protected-preview/chat-app-shell/index.html` | Restored from commit 61169b3 |
| `/var/www/weslr-chat-app-shell/index.html` | Synced |

---

## New Standing Rules

### Rule 1: Protected App Paths
```
Source:   /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html
Deployed: /var/www/weslr-chat-app-shell/index.html
Public:   /home/pr0/projects/weslr-v1-ui-website/site/ (NEVER PROTECTED WORK)
Docs:     /home/pr0/projects/weslr-v1-ui-website/docs/ (REPORTS GO HERE)
```

### Rule 2: No Blind Reset
- Record HEAD before reset
- Inspect diff first
- List accepted work that must NOT regress
- Ask owner approval for destructive reset

### Rule 3: Accepted Work Preservation
List before every patch:
- chat.weslr.de remains htpasswd protected
- /api/auth/me works behind htpasswd
- role badge "Owner Preview (htpasswd)" exists
- /api/message wiring to backend
- high-risk writes disabled
- No public exposure

### Rule 4: Deployed Authenticated Self-Test
Required before marking complete:
- Open https://chat.weslr.de/ in browser
- Authenticate with htpasswd
- Type message and send
- Verify backend response appears
- Verify no "405" error in console
- Verify no "UI Preview Only" message

### Rule 5: UI State Machine
- One active panel only
- No duplicate panel systems
- Panels use `display: none` when closed
- No hidden panels occupying layout

### Rule 6: Backend Wiring
For each API:
1. Backend exists locally
2. Nginx routes correctly
3. Frontend calls correctly
4. Deployed file matches source

### Rule 7: Report Accuracy Rule
DO NOT report:
- "owner browser test passed" unless owner confirmed
- "backend connected" if UI still says backend not connected
- "complete" if owner-visible flow fails
- "deployed" if only repo source changed

### Rule 8: Secret Rule
NEVER include passwords/secrets in:
- Commands
- Reports
- Rollback commands
- Logs
- Commits

---

## What Nova Must Do Before Every Protected App Patch

### Pre-Patch Checklist:
1. Record current HEAD: `git rev-parse --short HEAD`
2. List accepted capabilities that must NOT regress
3. Inspect diff: `git diff --stat HEAD`
4. Create backup if needed
5. Ask owner approval for destructive changes

### Post-Patch Checklist:
1. Verify source file has correct code
2. Verify deployed file matches source
3. Verify backend responds locally
4. Verify nginx routes correctly
5. Run authenticated browser self-test
6. Verify public exposure still blocked

### Before Reporting Success:
1. Owner browser test completed
2. Deployed file verified
3. No public exposure
4. All security checks pass
5. No console errors

---

## Plugin/Tooling Recommendations

### Future Tool Needs:
1. **Authenticated browser self-test / Playwright-style check**
   - Open https://chat.weslr.de/
   - Authenticate with htpasswd
   - Type message and send
   - Verify backend response appears
   - Capture screenshot

2. **Screenshot capture after deployment**
   - Compare before/after states
   - Verify UI elements visible

3. **Deployed-file diff checker**
   - Compare `/home/pr0/projects/weslr-v1-ui-website/` vs `/var/www/`
   - Alert if mismatch

4. **Route/public-exposure checker**
   - curl -I https://chat.weslr.de/api/message
   - curl -I https://weslr.de/api/message
   - curl -I https://weslr.de/app
   - Alert if exposure detected

5. **Git accepted-work preservation checklist**
   - List current HEAD
   - List files changed
   - List capabilities at risk
   - Require owner confirmation before reset

**DO NOT install plugins in this lane unless already available and safe.**

---

## Verification Results

| Check | Status | Command |
|-------|--------|---------|
| Local backend | ✅ | curl -s -X POST http://127.0.0.1:8092/api/message |
| Nginx route | ✅ | curl -s -I -H "Host: chat.weslr.de" http://127.0.0.1:8080/api/message (401) |
| Frontend request | ✅ | grep fetch('/api/message') in source (line 487) |
| Deployed file | ✅ | grep fetch('/api/message') in /var/www/ (line 487) |
| Public exposure | ✅ | curl -I https://weslr.de/api/message (404) |
| Public exposure | ✅ | curl -I https://weslr.de/app (404) |

---

## Commit

```
WESLR: harden Nova website ops bootstrap and protected app discipline v1
```

**Commit Hash:** Pending

---

## Final Judgment

**nova_website_ops_bootstrap_identity_memory_hardened_ready_for_stable_protected_app_work**

**Status:**
- ✅ Protected app paths documented
- ✅ Single source of truth rule added
- ✅ No blind reset rule added
- ✅ Accepted work preservation rule added
- ✅ Deployed authenticated self-test rule added
- ✅ UI state machine rule added
- ✅ Backend wiring verification added
- ✅ Report accuracy rule added
- ✅ Secret rule added
- ✅ Plugin recommendations added
- ✅ All verification checks pass

**Status Before Fix:**
- ❌ Frontend missing `/api/message` fetch
- ❌ Deployed file had old code

**Status After Fix:**
- ✅ Frontend has `/api/message` fetch
- ✅ Deployed file matches source
- ✅ Backend responds with JSON
- ✅ Public exposure blocked

**Owner Action Required:**
1. Test at `https://chat.weslr.de/` in browser
2. Type message and send
3. Verify backend response appears
4. Verify no console errors
5. Verify no 405 error

**Next Lane:** Continue with Phase 3 (Google OAuth) if approved, or move to other features.
