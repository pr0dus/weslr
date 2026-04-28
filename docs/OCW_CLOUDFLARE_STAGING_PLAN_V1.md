# OCW Cloudflare Staging Plan V1

**Purpose**: Protected staging access for operator review before public release.

---

## SECTION 1 — Purpose

Protected staging access for operator review before public release.

- **Do not expose** to public internet
- **Do not modify** production nginx/Cloudflare until explicitly approved
- **Do not touch** e-qubs.de (port 8097)
- **Local demo validated** on 127.0.0.1:8090 only

---

## SECTION 2 — Proposed URL

**Recommended hostname**: `staging.weslr.de`

**Alternative**: `demo-staging.weslr.de`

---

## SECTION 3 — Cloudflare Tunnel Rule

```
staging.weslr.de → http://127.0.0.1:8090
```

DNS type: A record pointing to server IP, proxied through Cloudflare.

---

## SECTION 4 — Protection Requirement

**Must use Cloudflare Access or equivalent protection before enabling route.**

Allowed:
- one-time PIN to operator email
- allowlist operator email
- temporary password if Access unavailable

Forbidden:
- open public route
- no-auth tunnel
- exposing raw backend

---

## SECTION 5 — Safety Preconditions

Before enabling:

- [x] release gate passes (`python3 weslr/tests/release_gate_v1.py`)
- [x] public readiness tests pass (`python3 weslr/tests/public_readiness_tests.py`)
- [x] local demo validated (127.0.0.1:8090)
- [x] WESLR mode `public_demo_readonly` enforced
- [x] write handlers blocked (`write_confirmed: false`)
- [x] server bound to `127.0.0.1` only
- [x] rollback command prepared

---

## SECTION 6 — Rollback Plan

1. Remove Cloudflare hostname route (`staging.weslr.de` → `http://127.0.0.1:8090`)
2. Stop demo process PID (`pkill -f "http.server 8090"`)
3. Verify `127.0.0.1:8090` closed (`ss -ltnp | grep :8090`)
4. Confirm `e-qubs.de` still active (`curl -s http://localhost:8097`)

---

## SECTION 7 — Validation After Enablement

Test externally via `staging.weslr.de`:

1. `show system overview` → `operator_overview`
2. `show diagnostics` → `ISS_query_all`
3. `convert iss suggestion iss.not_integrated` → `write_confirmed: false`
4. unknown prompt → `fallback_safe`

---

## SECTION 8 — Do Not Touch

- `e-qubs.de` (port 8097)
- existing e-qubs service (PID 262376, python3)
- nginx production routes unless explicitly approved
- Cloudflare production zones without operator approval

---

## SECTION 9 — Recommended Implementation Step

After operator approval:

1. Create protected Cloudflare Access route: `staging.weslr.de`
2. Route to `http://127.0.0.1:8090`
3. Enable only one-time PIN or email allowlist
4. Test externally (no direct server access)

---

## SECTION 10 — Verdict

`CLOUDFLARE_STAGING_PLAN_READY`

**Current state**:
- Local demo: ✅ validated on 127.0.0.1:8090
- Release gate: ✅ passed
- Public readiness: ✅ passed
- Write protection: ✅ enforced
- e-qubs.de: ✅ untouched (port 8097)

---

**Next step**: Operator approval required before Cloudflare change.
