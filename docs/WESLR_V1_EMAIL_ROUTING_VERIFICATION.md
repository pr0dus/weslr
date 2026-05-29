# WESLR V1 Email Routing Verification Note

**Created:** 2026-05-29 23:40 CEST
**Status:** VERIFIED WORKING

---

## Cloudflare Email Routing Configuration

| Email Address | Destination | Status |
|---------------|-------------|--------|
| `contact@weslr.de` | `arthrobert@gmail.com` | ✅ VERIFIED WORKING |
| `info@weslr.de` | `arthrobert@gmail.com` | ✅ CONFIGURED |
| `pilot@weslr.de` | `arthrobert@gmail.com` | ✅ CONFIGURED |

---

## DNS Records (Cloudflare-managed)

| Type | Name | Content | Priority |
|------|------|---------|----------|
| MX | `weslr.de` | `route1.mx.cloudflare.net` | 85 |
| MX | `weslr.de` | `route2.mx.cloudflare.net` | 22 |
| MX | `weslr.de` | `route3.mx.cloudflare.net` | 97 |
| TXT | `weslr.de` | `v=spf1 include:_spf.mx.cloudflare.net ~all` | — |
| TXT | `cf2024-1._domainkey.weslr.de` | DKIM key | — |

---

## Website Contact Email

**Public contact shown on website:** `contact@weslr.de`

**Privacy:** Owner Gmail address is NOT exposed publicly. Cloudflare Email Routing obfuscates emails in HTML.

---

## Verified By

Owner tested: `contact@weslr.de` → Gmail delivery successful (2026-05-29 23:38 CEST)

---

## No Further Changes Needed

Email routing is complete. No additional Cloudflare changes required unless owner requests.

---

**End of Note**