# WESLR V1 Privacy Policy and Impressum Update Report V1

**Date:** 2026-05-30  
**Status:** PRIVACY_AND_IMPRESSUM_UPDATED_FOR_OWNER_REVIEW  
**Branch:** ocw-weslr-v1-ui-20260529

---

## Source Files Used

### Privacy Policy
**Source:** `/home/pr0/.openclaw/media/inbound/WESLR_Privacy_Policy_Draft_2026-05-30_vat_omitted_v5---5873947a-9dbc-4185-8dd5-014ee10ffad3.md`

- Draft version: v5
- Updated: 30 May 2026
- VAT ID: Omitted (Nebengewerbe)
- Status: Draft for owner/legal review — not final legal advice

### Impressum
**Source:** Owner-provided text via Telegram (message_id: 3211)

```
Impressum

Angaben gemäß § 5 DDG

e-qubs
Inhaber: Chirodea-Rosca Arthur-Robert
Mitterfeld 3
87719 Mindelheim
Deutschland

Kontakt

E-Mail: contact@weslr.de

Hinweis zum aktuellen Betriebsstatus von WESLR

WESLR befindet sich in Entwicklung. Öffentliche Selbstregistrierung, öffentlicher Pilotbetrieb, kostenpflichtige Nutzung, Datei-Uploads, Zahlungsfunktionen und Marktplatzfunktionen sind derzeit nicht öffentlich freigeschaltet, sofern nicht ausdrücklich anders angegeben.
```

---

## Files Changed

| File | Action | Changes |
|------|--------|---------|
| `site/privacy/index.html` | Updated | +676 lines, -23 lines (full privacy policy) |
| `site/impressum/index.html` | Updated | +45 lines, -31 lines (owner-provided content) |

---

## Privacy Policy Page Status

**URL:** https://weslr.de/privacy/  
**HTTP Status:** 200 OK  
**Last Modified:** Sat, 30 May 2026 08:20:13 GMT

### Content Verification

| Check | Status |
|-------|--------|
| Draft status shown | ✅ "Draft for owner/legal review" |
| Controller name | ✅ Chirodea-Rosca Arthur-Robert |
| Business name | ✅ e-qubs |
| Address | ✅ Mitterfeld 3, 87719 Mindelheim, Germany |
| Contact email | ✅ contact@weslr.de |
| Private Gmail hidden | ✅ Not present in HTML |
| VAT ID | ✅ Correctly omitted ("not currently provided / not applicable") |
| Minimum age | ✅ 16+ |
| Current status clear | ✅ Static site, pilot not live, uploads not enabled |
| Planned features marked | ✅ "Planned/future" language preserved |
| AI claims | ✅ No false AI/benchmark/Turing certification claims |
| Production claims | ✅ No false production-readiness claims |

### Technical Scan Results

| Category | Finding |
|----------|---------|
| Cookies set by JS | None |
| localStorage/sessionStorage | None |
| Third-party scripts | Google Fonts only |
| External fonts | Inter (Google Fonts) |
| Cloudflare Analytics | Planned, NOT active |
| Tracking pixels | None |
| Private Gmail exposed | No |
| Public contact correct | Yes (contact@weslr.de) |

---

## Impressum Page Status

**URL:** https://weslr.de/impressum/  
**HTTP Status:** 200 OK  
**Last Modified:** Sat, 30 May 2026 08:26:34 GMT

### Content Verification

| Check | Status |
|-------|--------|
| § 5 DDG reference | ✅ "Angaben gemäß § 5 DDG" |
| Business name | ✅ e-qubs |
| Owner name | ✅ Chirodea-Rosca Arthur-Robert |
| Address | ✅ Mitterfeld 3, 87719 Mindelheim, Deutschland |
| Contact email | ✅ contact@weslr.de |
| Private Gmail hidden | ✅ Not present in HTML |
| VAT ID | ✅ Not present (as intended) |
| Betriebsstatus-Hinweis | ✅ Included (pilot not live, uploads not enabled) |
| Language | ✅ German (as required for German Impressum) |

---

## Remaining Legal Blockers

### Immediate (Before Public Launch)

| Page | Status |
|------|--------|
| ~~Impressum~~ | ✅ Complete |
| ~~Privacy Policy~~ | ✅ Complete |
| Terms of Use | ⏳ Pending — needs update |
| Commercial License | ⏳ Pending — needs update |

### Before Feature Activation

| Document | Status | Required Before |
|----------|--------|-----------------|
| Pilot Terms | ⏳ Pending | Pilot accounts |
| Cookie Policy / Consent Settings | ⏳ Pending | Cloudflare Analytics activation |
| Marketplace Terms | ⏳ Pending | Marketplace launch |
| Upload/File Processing Policy | ⏳ Pending | File uploads |
| Payment/Subscription Terms | ⏳ Pending | Payments |

---

## Confirmation Checklist

| Check | Status |
|-------|--------|
| No DNS changes | ✅ Confirmed |
| No Cloudflare Tunnel changes | ✅ Confirmed |
| No nginx routing changes | ✅ Confirmed |
| No password protection changes | ✅ Confirmed |
| staging.weslr.de protected | ✅ HTTP 401 |
| chat.weslr.de protected | ✅ HTTP 401 |
| weslr.de public | ✅ HTTP 200 |
| No mobile nav changes | ✅ Confirmed |
| No brand asset changes | ✅ Confirmed |
| e-qubs.de untouched | ✅ Confirmed |
| plantdelux.ro untouched | ✅ Confirmed |
| No secrets committed | ✅ Confirmed |
| No weslr/chat_responder.py changes | ✅ Confirmed |
| No weslr/main.py changes | ✅ Confirmed |

---

## Protected Routes Verification

```
https://staging.weslr.de/ → HTTP/2 401 Authorization Required ✅
https://chat.weslr.de/ → HTTP/2 401 Authorization Required ✅
https://weslr.de/privacy/ → HTTP/2 200 OK ✅
https://weslr.de/impressum/ → HTTP/2 200 OK ✅
```

---

## Private Email Verification

| Page | Gmail/Googlemail | @artho | contact@weslr.de |
|------|------------------|--------|------------------|
| Privacy | 0 occurrences | 0 occurrences | 9 occurrences ✅ |
| Impressum | 0 occurrences | 0 occurrences | 1 occurrence ✅ |

**Result:** Private Gmail correctly hidden. Public contact email correctly shown.

---

## Mobile Readability

| Check | Status |
|-------|--------|
| Viewport meta tag | ✅ Present |
| Responsive CSS | ✅ Present |
| Mobile nav toggle | ✅ Present |
| Tables scrollable | ✅ Present |

---

## Git Commits

```
d069b77 WESLR: update Impressum with owner-provided content
0ac302d WESLR: update privacy policy legal page
```

---

## Summary

Both legal pages have been updated with owner-provided content:

1. **Privacy Policy** — Full draft v5 (30 May 2026) integrated
   - All 29 sections preserved
   - Legal bases table included
   - Retention table included
   - Current/planned status clearly marked
   - Draft status shown at top

2. **Impressum** — Owner-provided German text integrated
   - § 5 DDG compliant
   - Business/owner information complete
   - Contact email public
   - Betriebsstatus-Hinweis included

---

## Next Steps

1. Owner review of Privacy Policy and Impressum pages
2. Terms of Use update
3. Commercial License update
4. Cloudflare Analytics technical verification (before activation)
5. Pilot Terms (before pilot accounts)
6. Payment/subscription terms (before payments)

---

**Report Generated:** 2026-05-30  
**Generated By:** Nova (OpenClaw Agent)  
**Repository:** /home/pr0/projects/weslr-v1-ui-website  
**Branch:** ocw-weslr-v1-ui-20260529