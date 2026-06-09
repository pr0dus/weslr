# NOVA_WESLR_PROTECTED_WORKSPACE_MODERN_UI_DIRECTION_V1.md

**Date:** 2026-06-09 21:59  
**Status:** DESIGN DISCOVERY COMPLETE ✅  
**Mode:** Documentation only — no source edits, no deploys, no behavior change  
**Scope:** Strategic design direction for the protected workspace shell (`chat.weslr.de`)

---

## 0. Important Framing

This report is a **direction document**, not a pixel-perfect spec or an implementation patch. It captures intent, structure, and visual language so that future UI work (Step B and beyond) has a coherent target to converge on.

**This report does NOT copy Perplexity or Cursor.** It draws only on the modern interaction principles those products are known for, then reinterprets them through WESLR's identity:

> Continuity-first operational intelligence. Governed, traceable, operator-approved. Project-based workspace. Protected/private by default. Evidence/context aware. Artifact-oriented. Owner-controlled environment settings. German/engineering-grade trust — not magic chatbot.

WESLR is a **governed operator cockpit**, not a public AI playground. The direction below reflects that.

---

## A. Current UI Problems (Audit of `protected-preview/chat-app-shell/index.html`)

After reading the full file, here is a concrete list of what is working directionally but feels dated or rigid.

### A1. Outdated bottom action buttons
- The composer-actions row uses **5 separate `icon-btn` controls** (⚙, 📄, 🔍, ⚙️, ☰) plus a Send button. Two of them render as ⚙ / ⚙️ with the same glyph but different actions — easy to confuse.
- Visual style: 34×34 hard-bordered squares, `border-radius: 8px`, dark slate background. Reads as "form controls", not as primary action affordances.
- Layout: `flex-wrap: wrap` is allowed. On narrow widths the chips wrap awkwardly, breaking the visual rhythm.
- No action labels on desktop. The same icons must be inferred.

### A2. Rigid mobile layout
- The sidebar at `<768px` collapses to a **70px-tall horizontal strip**, so the entire project list becomes a tappable row. Project names truncate and there is no indication of active selection beyond hover color.
- The composer still occupies the bottom on mobile with the same button row, which is too tall.
- The `mobile-drawer` (`.mobile-drawer`) slides in from the right and **has no explicit close button** — only outside-tap or back navigation closes it.
- The `mobile-tabs` row duplicates the icon buttons. Two parallel navigation systems for the same panels.

### A3. Overlapping panels
- The `.right-panel` (desktop) and `.mobile-drawer` (mobile) carry the **same content model** but are not coordinated. On mobile, you can have `right-panel` (inherited from desktop) and `mobile-drawer` both present in the DOM.
- Multiple panels can be opened sequentially without explicit close.

### A4. Unclear backend status
- The static "Backend not connected" banner (line 354) is **always shown** even when `/api/auth/me` returns a valid session. It needs to be conditional on actual backend reachability, not on a developer placeholder.
- "UI Preview Only" is still referenced in the source (line 475 — removed in Step A reconciliation, but the surrounding warning text was preserved). After Step A, that string is gone from the source — but the visual language of "preview-only" still leaks through other status pills.

### A5. Unclear project / sidebar structure
- The sidebar has no header, no grouping, no role badge, no environment status, no continuity indicator.
- Projects are a flat list of two with a "+ New Project" button that only triggers a toast.

### A6. Settings not clearly owner-only
- The Settings panel exists, but its content is generic. There is no "owner-only" lock, no environment state, no approval gating visible.

### A7. Too much "preview" language
- "Protected Workspace Preview", "UI only preview", "Backend not connected", "Local UI preview only" — all of these belong in a development placeholder, not a live protected operator cockpit. After backend wiring lands, this language should be retired.

### A8. No streaming/pending feedback
- The fixed `sendMessage()` shows a hard "Sending..." pending message and replaces it with the result. No streaming dots, no cursor, no progressive reveal. Feels old.

### A9. No role / security state visibility
- A role badge is missing from the topbar. There is a "Protected • Internal" pill, but no `Owner / Admin / Tester / Viewer` indicator. No `writes_enabled: true/false` chip. No `google_auth_enabled` chip.

### A10. Toast system is functional but rough
- `toast-container` is fixed at `bottom: 1rem; right: 1rem;`. The visual is decent, but there is no type system (success/info/warning/error) and no keyboard close.

---

## B. Modern UI Principles for WESLR

These are the principles to converge on. None of them are new inventions — they are distillations of what makes modern operator tools feel modern.

### B1. Answer / chat is the center
- The conversational surface is the **primary canvas**. Everything else is supporting cast.
- Empty state should not be a banner — it should be a low-density **suggested start** with a couple of prompt chips, not a warning box.

### B2. Project rail, not sidebar blob
- A **dedicated project rail** (left column on desktop, top selector on mobile) is the navigation entry point. Each project is a chip, not a list item.
- Active project is visually distinct: filled accent + label. Inactive projects are low-contrast.

### B3. Evidence / Artifact / Settings drawers
- Right side opens **at most one** of: Evidence, Artifacts, Settings, or Memory/Continuity. Closing one is required to open another.
- Drawers are full-height on desktop, **bottom sheet** on mobile.
- Drawer header carries a clear close (×) button.

### B4. Status chips, not status banners
- Replace the static "Backend not connected" warning with a **status chip row** in the topbar: `Backend: connected | writes: off | google_auth: off | role: owner`.
- Chips are color-coded (green/amber/red). Tapping a chip opens the relevant drawer with full context.

### B5. Command / action bar
- The current bottom composer button row is replaced with a **horizontal action chip row** above the input. Chips: `Project options`, `Evidence`, `Artifacts`, `Settings`, `Memory`, `Command palette`.
- Send is a single primary button at the right of the input, not a chip.

### B6. Owner environment controls
- Settings drawer surfaces only what the current role can actually change. For owner: all toggles. For viewer: read-only labels.
- High-risk writes have a clear approval gate (currently `writes_enabled: false`).

### B7. Mobile bottom sheet behavior
- On mobile, drawers come up from the **bottom** as a sheet with a drag handle and explicit close button.
- One sheet at a time. Opening a new one closes the previous.

### B8. No hidden panels occupying layout
- Layout reserves space for visible panels only. Drawers overlay — they do not push content.
- Composer is always docked to the bottom of the viewport (or just above the keyboard on mobile).

### B9. Streaming / pending feedback
- Replace hard "Sending..." with **typing dots** in the assistant bubble, optionally streaming tokens if the backend supports it.
- Pending state should be visually subtle, not blocky.

### B10. WESLR identity throughout
- Dark navy base, refined blue accent, restrained amber/red for warnings.
- No emojis as primary action affordances — use them only as secondary decoration.
- No marketing flourishes. Tone: engineering, controlled, traceable.

---

## C. Proposed Layout

### C1. Desktop (≥ 1024px)

```
┌──────────────────────────────────────────────────────────────────┐
│  W  Protected Workspace          [role] [writes] [auth] [backend] │ ← topbar (48px)
├──────────┬──────────────────────────────────────┬────────────────┤
│          │                                      │                │
│ Projects │       Chat / Workspace               │   Drawer       │
│          │                                      │   (Evidence /  │
│ ▣ WESLR  │  ┌──────────────────────────────┐    │    Artifacts / │
│   Web    │  │  user message bubble        │    │    Settings /  │
│          │  └──────────────────────────────┘    │    Memory)     │
│ ▢ Artif  │  ┌──────────────────────────────┐    │                │
│   Test   │  │  WESLR response card         │    │                │
│          │  │  • evidence chips            │    │                │
│ ▢ + New  │  │  • artifact preview          │    │                │
│          │  └──────────────────────────────┘    │                │
│          │  ┌──────────────────────────────┐    │                │
│          │  │  ● ● ●  (pending state)      │    │                │
│          │  └──────────────────────────────┘    │                │
│          │                                      │                │
│          │  ┌──────────────────────────────┐    │                │
│          │  │ [Project][Evidence][Artifact]│    │                │
│          │  │ [Settings][Memory]  ⌘  [Send]│    │                │
│          │  └──────────────────────────────┘    │                │
├──────────┴──────────────────────────────────────┴────────────────┤
│  © WESLR — Protected • Internal • Owner Preview                   │ ← status footer
└──────────────────────────────────────────────────────────────────┘
```

**Three columns:**
- **Left rail:** project list (240px)
- **Center:** chat / workspace (flex, max 800px content, centered)
- **Right drawer:** context panel (320px, can collapse to icon rail)

**Top bar chips:** role, writes, auth, backend — at most 4 small chips, never wrapping.

### C2. Mobile (< 768px)

```
┌──────────────────────────────────────┐
│  W  [WESLR Website Review ▾]    ⋯     │ ← topbar (44px)
├──────────────────────────────────────┤
│                                      │
│   ┌────────────────────────────┐     │
│   │  user message              │     │
│   └────────────────────────────┘     │
│   ┌────────────────────────────┐     │
│   │  WESLR response card       │     │
│   └────────────────────────────┘     │
│                                      │
├──────────────────────────────────────┤
│  [Project][Evidence][Artifact][Set]   │ ← horizontal chip rail
├──────────────────────────────────────┤
│  Type a message...           [Send]   │ ← composer
├──────────────────────────────────────┤
│  [status chips: role • backend]      │ ← status footer
└──────────────────────────────────────┘
```

**Bottom sheet (when triggered):**
```
        ─────  (drag handle)
   Evidence                              ×
   ──────────────────────────────
   Project: WESLR Website Review
   Continuity: active
   Source A · source_1.md
   Source B · source_2.md
```

**Mobile rules:**
- One bottom sheet at a time, with explicit × close.
- No side columns.
- Horizontal chip rail is the navigation, replaces sidebar+tabs+icon-buttons.
- Topbar project selector opens a project picker sheet.

### C3. Tablet (768–1023px)

- Two-column: project rail (collapsible icon-rail) + chat. Drawer opens as overlay sheet, not a fixed right column.
- Composer remains docked bottom.

---

## D. Component System

A modular inventory of components the new UI will use. Each has a defined role, visual style, and interaction contract.

| Component | Purpose | Visual style | Interaction |
|-----------|---------|--------------|-------------|
| **Topbar** | App identity + global status | 48px, sticky, dark navy, subtle bottom border | None (display only) |
| **Status chip** (role/writes/auth/backend) | Surface runtime state | Pill, 22px tall, color-coded | Tap opens relevant drawer |
| **Project rail** | Project list | 240px left column, dark slate, active = accent fill | Tap switches active project |
| **Project chip (mobile)** | Project selector | Pill in topbar, label + caret | Tap opens project picker sheet |
| **Chat message bubble (user)** | User-typed message | Right-aligned, accent-tinted background, 16px radius | None |
| **Chat message bubble (WESLR response)** | Assistant reply | Left-aligned, dark slate, evidence chips below | None (display) |
| **Pending state (typing dots)** | Live feedback during fetch | Three animated dots in assistant bubble | None |
| **Evidence chip** | Inline source marker | Small pill, monospace font, link-style | Tap scrolls/highlights evidence in drawer |
| **Artifact card** | Generated file preview | Card with icon, name, size, action | Tap opens artifact detail |
| **Backend status chip** | System health | Topbar or footer, green/amber/red | Tap → Settings drawer |
| **Role chip** | Identity indicator | Topbar, accent border, role text | Read-only |
| **Owner setting card** | Toggled setting | Card with title, description, switch | Switch (owner only) |
| **Action chip** (Project/Evidence/Artifact/Settings/Memory) | Primary navigation | Pill, 32px tall, icon + label | Tap opens drawer |
| **Send button** | Submit composer | Filled accent, 36px, right of input | Tap submits |
| **Bottom sheet** | Drawer on mobile | Slides up, drag handle, explicit × close | Swipe down to dismiss |
| **Toast / snackbar** | Ephemeral feedback | Bottom center, type-colored, auto-dismiss | Optional action button |
| **Command palette** (placeholder) | Quick actions | Modal overlay, search field, action list | Cmd/Ctrl+K opens |
| **Empty state** | First-run / no project | Centered icon, suggested prompts | Tap prompt to send |

---

## E. Visual Style

### E1. Color tokens
```
--bg-primary:      #071018   (deep navy)
--bg-secondary:    #0b111b   (panel)
--bg-tertiary:     #0f172a   (raised card)
--border-subtle:   rgba(148,163,184,0.18)
--border-muted:    rgba(148,163,184,0.12)
--text-primary:    #e7eef8
--text-secondary:  #cbd5e1
--text-muted:      #94a3b8
--accent-blue:     #38bdf8   (refined — not electric)
--accent-blue-500: #0ea5e9
--accent-amber:    #f59e0b   (warnings only)
--accent-red:      #ef4444   (errors only)
--accent-green:    #22c55e   (success / connected)
```

**Direction:** Dark navy with restrained blue accent. Amber and red appear only on warnings and errors. Green only on "connected" or "approved" states. No glassmorphism beyond a subtle 1px border + low-opacity fill.

### E2. Radii & spacing
- **Radius scale:** `4 / 8 / 12 / 16 / 24` (rounded but not pillowy)
- **Spacing scale:** `4 / 8 / 12 / 16 / 24 / 32 / 48` (8-point baseline)
- **Composer height:** 56px standard, 64px on focus (subtle grow)
- **Chip height:** 32px standard
- **Topbar height:** 48px desktop, 44px mobile
- **Drawer width:** 320px desktop, full-width bottom sheet mobile

### E3. Typography
- **Font:** Inter, system-ui fallback. (Already in use.)
- **Weights:** 400 (body), 500 (label), 600 (heading), 700 (action)
- **Sizes:** 11 / 12 / 13 / 14 / 16 / 18 / 22 / 28 (compact, modern)
- **Line height:** 1.5 body, 1.2 headings, 1.0 in chips
- **Letter spacing:** -0.01em on display, 0.04em on uppercase labels
- **Monospace:** JetBrains Mono or system mono for code, evidence IDs

### E4. Surfaces
- **Less bulky cards:** replace chunky 24px-radius cards with 12-16px and a 1px border.
- **Less old button styling:** remove 1px solid borders on every action — use a fill or an underline instead.
- **Modern rounded controls:** 8–12px on inputs, 12px on chips, 16px on cards.
- **Strong spacing consistency:** 8-point baseline everywhere; no `padding: 0.85rem` ad-hoc values.

### E5. Elevation
- Use **1px borders** as the primary depth signal, not box-shadows.
- One allowed shadow level for toasts and the command palette: `0 8px 24px rgba(0,0,0,0.4)`.
- No drop shadows on cards or chips.

---

## F. Interaction Model

The new shell's interaction grammar:

| Action | Trigger | Result |
|--------|---------|--------|
| Send message | Enter / Send button | Pending dots → response card with evidence chips |
| Cancel pending | Tap "×" in pending bubble | Removes pending state, no message sent |
| Open drawer | Tap status chip or action chip | Drawer slides in (right on desktop, bottom on mobile) |
| Close drawer | Tap ×, swipe down (mobile), or Esc | Drawer slides out |
| Switch drawer | Tap a different action chip | Old drawer closes, new one opens |
| Switch project | Tap project rail item / project chip | Project context reloads, evidence/artifact scope updates |
| Open command palette | ⌘K / Ctrl+K / Tap "⌘" chip | Modal opens, search-as-you-type |
| Toggle owner setting | Tap switch in Settings drawer | Local state change + chip color update; requires writes_enabled |
| Stream response | Backend supports it | Tokens append progressively in the assistant bubble |
| View artifact | Tap artifact card | Artifact drawer opens with full preview |
| View evidence | Tap evidence chip | Evidence drawer opens, scrolls to source |
| Toast dismiss | Auto after 3s, or tap | Toast fades out |
| Empty-state prompt | Tap suggested prompt chip | Composer prefills, focus stays |

### Hidden rules
- **One drawer open at a time.** Always.
- **No "preview" language** appears in any visible surface once `/api/auth/me` returns a real session.
- **Role determines visible settings.** Viewer sees no toggles. Owner sees all.
- **High-risk writes** (artifact creation, settings change, project mutation) require `writes_enabled: true` AND a confirmation toast.
- **No public-chat affordances.** No "share", no "invite", no public link generation.

---

## G. Implementation Plan (Phased)

This is a multi-phase effort. **Step A (source/deployed reconciliation) is the only thing shipped so far.** Everything below is forward-looking.

### Phase 0 — Stabilize (DONE in Step A)
- ✅ Source matches deployed
- ✅ /api/message fetch is in source
- ✅ Backup of pre-Step-A source preserved

### Phase 1 — Component foundation
- Establish CSS custom-property tokens (colors, radii, spacing, typography)
- Refactor `index.html` to use the new component classes
- Keep `sendMessage()` working unchanged
- **Do not change behavior. Do not change content. Do not deploy.**

### Phase 2 — Drawer consolidation
- Replace `.right-panel` + `.mobile-drawer` with a single `.drawer` component
- Add explicit × close, Esc-to-close, focus trap
- Wire one-drawer-at-a-time logic
- Mobile: bottom sheet behavior
- **Behavior parity check:** all current panel functions still work.

### Phase 3 — Composer refresh
- Replace 5-icon button row with horizontal action chip rail
- Action chip set: Project, Evidence, Artifact, Settings, Memory
- Add ⌘K command palette placeholder (disabled stub is fine for v1)
- Send is a single primary button
- **No change to sendMessage() behavior.**

### Phase 4 — Status chips
- Replace static "Backend not connected" banner with conditional status chip row
- Read `/api/auth/me` response to determine role/writes/auth chips
- Real `connected` / `disconnected` state from a health endpoint
- **Wiring depends on backend health endpoint, not in scope for UI-only phase.**

### Phase 5 — Visual polish
- Reduce card bulk
- Refine spacing scale to 8-point baseline
- Refine typography to compact modern scale
- Replace ad-hoc padding values

### Phase 6 — Mobile pass
- Tablet layout: collapsible project rail
- Mobile: project chip in topbar, bottom-sheet drawers
- Explicit close buttons
- Safe-area-inset for composer

### Phase 7 — Owner settings UX
- Settings drawer shows role-gated controls
- Switch components for owner-toggled values
- Confirmation toasts for high-risk writes
- "View as: Owner / Admin / Tester / Viewer" preview switch (owner only)

### Phase 8 — Streaming response
- Backend support for streaming
- Replace hard "Sending..." with progressive token append
- Cursor blink in last assistant bubble

### Phase 9 — Authenticated end-to-end verification
- Owner-supplied htpasswd credentials
- Authenticated curl + browser smoke test
- Confirm /api/message returns role/writes/auth/owner correctly
- Confirm UI shows "Role: Owner" chip
- Confirm no "preview" text appears

---

## H. Open Questions for Owner

1. **Backend `/api/auth/me` contract:** What does the response actually contain today? The rehydration report did not see `writes_enabled` or `google_auth_enabled` fields — only `role` is referenced. Should I curl with creds to confirm?
2. **Drawer scope priority:** Is the Evidence / Artifact / Settings / Memory drawer set the right four? WESLR-specific (continuity, artifact) — should one be split into "Memory" and "Continuity"?
3. **Command palette:** Build a real one, or keep a stub for v1? Cursor's ⌘K is a major differentiator.
4. **Streaming:** Does the backend support SSE / WebSocket / chunked responses, or is the current implementation a single JSON response?
5. **Owner role-switch preview:** Some operator tools (Linear, Vercel) let the owner preview the UI "as Admin" or "as Viewer". Is that in scope?
6. **Brand mark:** The current logo is a flat "W" square. Is there a Weslr logomark I should be using instead?
7. **No emoji as action:** I am proposing to drop emojis (📄 🔍 ⚙️ ☰) from primary action affordances. Owner approval?

---

## I. What This Report Does NOT Change

- ❌ No source code edits
- ❌ No deploys
- ❌ No nginx / auth / Cloudflare / DNS changes
- ❌ No model changes
- ❌ No Google OAuth
- ❌ No public chat / public registration
- ❌ No high-risk writes enabled
- ❌ No backend contract changes
- ❌ No removal of existing functionality (everything works, the new look layers on top)

This is a **direction document**. Phased implementation requires separate dispatches with owner approval at each phase.

---

## J. Rollback / Forward Path

If this direction is approved, the next dispatch would be **Phase 1 — Component foundation**, which is a CSS + markup refactor with **zero behavior change**. The current working `sendMessage()`, `/api/message` fetch, and all panel toggles would remain functional throughout.

If this direction is **not** approved, the working `index.html` from Step A reconciliation remains untouched and live.

---

## K. Final Judgment

`nova_weslr_protected_workspace_modern_ui_direction_v1_documented_ready_for_owner_review`

Direction captured. No code, no deploy, no behavior change. Awaiting owner review and approval to begin Phase 1 (component foundation, CSS refactor, behavior-preserving).

---

**Report author:** Nova (Telegram dispatcher, WESLR ops context)  
**Active model during report:** `minimax-m3:cloud`  
**Owner-visible next actions:**
1. Review the direction above
2. Answer the open questions in section H (especially the `/api/auth/me` contract and the streaming question)
3. Approve Phase 1 as the next dispatch
4. Or amend the direction before any implementation begins
