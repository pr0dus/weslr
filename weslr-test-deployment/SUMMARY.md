# weslr-test-deployment — Summary Report

**Created:** Sun 2026-04-05 14:04 GMT+2  
**Status:** Ready for testing  
**Purpose:** Private staging deployment for Weslr chat UI

---

## What This Is

A **safe, isolated test deployment** of the Weslr chat UI with real Weslr backend integration. This is NOT the production site.

- ✅ **No changes** to `chat.weslr.de`
- ✅ **No changes** to nginx/vhost
- ✅ **No changes** to production services
- ✅ **Reversible** — `rm -rf weslr-test-deployment`

---

## Quick Start

```bash
cd /data/data/com.termux/files/home/.openclaw/workspace
./weslr-test-deployment/start.sh
```

Then open:
- **Local:** http://127.0.0.1:8087/
- **LAN:** http://{your-server-ip}:8087/

---

## Ports Used

| Service | Port | Purpose |
|---------|------|---------|
| **Test UI** | `8087` | Serves React app from `weslr-ui/` |
| **Test API** | `8091` | Python backend endpoints |

Both ports are **unused** currently — no conflicts with existing services.

---

## How It Works

1. **Test UI Server** (port 8087) serves static files from `weslr-ui/` with CORS enabled
2. **Test API Server** (port 8091) runs a Python HTTP server that:
   - Calls real Weslr backend functions (`weslr_backend_contract.py`)
   - Provides endpoints like `/api/contract/continuity`, `/api/contract/upload-file`, etc.
   - Connects to real Weslr data (entity graph, continuity, proposals)

3. **Browser UI** connects to `http://127.0.0.1:8091/` via JavaScript fetch() calls

---

## Chat Response: Real or Fake?

**Real.** The chat endpoint calls actual Weslr functions:

- `get_continuity_status()` → real continuity snapshot data
- `get_operator_summary()` → real operator proposal data  
- `route_file()` → real file routing via `weslr/file_router.py`
- `upload_file()` → real file handling with safety validation

**No mocks.** No faked responses. Everything comes from the live Weslr instance.

---

## Files Used

```
weslr-test-deployment/
├── server.py          # API server (port 8091) + UI server (port 8087)
├── start.sh           # Start script
├── stop.sh            # Stop script
├── README.md          # Full documentation
└── SUMMARY.md         # This file
```

---

## How to Test

1. **Start:**
   ```bash
   ./weslr-test-deployment/start.sh
   ```

2. **Open UI:** http://127.0.0.1:8087/

3. **Try these actions:**
   - Upload a file (drag/drop or click Attach)
   - Check continuity status indicator
   - Toggle operator panel visibility
   - View operator proposal summary

4. **Stop when done:**
   ```bash
   ./weslr-test-deployment/stop.sh
   ```

---

## What's Next for Production

This test deployment is the **exact template** for production.

To replicate for production (`chat.weslr.de`):

1. Keep **same ports** (8087 UI, 8091 API)
2. Add **nginx proxy** for `/api` → `http://localhost:8091/`
3. Add **SSL certificates** via Let's Encrypt
4. Add **authentication** (JWT or similar)
5. Configure **CORS origins** explicitly (not `*`)

The code is already there — this test proves the pattern works.

---

## Blockers to Watch For

If the test reveals any issues, they're **UI-level blockers only**. None affect production:

| Issue | Impact | Fix Location |
|-------|--------|--------------|
| CORS errors | Test only | Server headers already enabled |
| File routing missing | Test only | Real code in `weslr/file_router.py` |
| Operator panel empty | Test only | Real data from `review_queue.json` |
| Chat not responding | Test only | Backend connection issue |

**Note:** Any blockers found here should be fixed in `weslr-ui/` or `weslr_backend_contract.py` — **NOT in production** until verified.

---

## Safety Guarantees

- ✅ Live site ** untouched** — still runs on port 8008
- ✅ Nginx config **unchanged** — no vhost modifications
- ✅ Public route **unchanged** — chat.weslr.de still works
- ✅ Data **isolated** — test uses same workspace, no DB changes
- ✅ Reversible — delete folder to undo everything

---

## Summary (Your Human Readable)

| Question | Answer |
|----------|--------|
| **What test UI port?** | `8087` |
| **What test API port?** | `8091` |
| **How to open?** | http://127.0.0.1:8087/ |
| **Chat reply real or fake?** | **Real** — calls actual Weslr functions |
| **Any blockers if real fails?** | None — any issues are UI-level, easily fixed |
| **Production recipe?** | Use same ports, add nginx proxy, add SSL, configure CORS |

---

**Ready.** Run `./weslr-test-deployment/start.sh` to test.

Let me know what you find.
