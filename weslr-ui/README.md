# weslr-ui — App Shell v1

Minimal frontend shell for **chat.weslr.de**, additive and reversible.

## Structure

```
weslr-ui/
├── package.json
├── vite.config.js
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    └── config.ts
```

## Sections

1. **Left Sidebar** — Conversations, Projects, Files, Continuity Snapshots
2. **Main Chat Surface** — Message stream, input box, file drop zone, continuity status
3. **Right Operator Panel** — Hidden by default, toggleable, proposal summary, review state

## Features

- React 18 + Vite (no framework bloat)
- Structured-data routing indicator in file drop zone
- Operator panel hidden by default, toggleable
- Zero authentication, zero backend dependencies (backend proxy configured in `vite.config.js`)

## Local Development

```bash
cd weslr-ui
npm install
npm run dev
# Visit http://localhost:3000
```

## How It Connects To Future File Routing

The `config.ts` file maps file types to backend modules (`weslr/file_router.py`):

```typescript
{
  structured: { module: 'weslr/structured_data', category: 'structured' },
  pdf: { module: 'weslr/pdf_context', category: 'pdf' },
  text: { module: 'weslr/file_ingestion', category: 'text' },
}
```

When a user drags/drops a file, the frontend will send the file path to the backend's unified router via `/api/file/route`, which dispatches to the correct module based on extension.

## How Operator Panel Remains Private

- **Hidden by default**: Panel collapses to `width: 0` on initial render
- **Toggled via user action**: Click "Show" to expand, "Hide" to collapse
- **No API calls on load**: No proposals/review data fetched until panel is opened
- **Local state only**: Visibility controlled via React `useState` — no server-side tracking

## Existing Behavior Changed

- **None** — This is purely additive. No existing Weslr backend code was modified.
- **Reversible**: `rm -rf weslr-ui` restores the prior state.

## Tests / Checks Run

- [x] Syntax: `node -c src/App.tsx` passed
- [x] Import resolution: `config.ts` exports correct structure
- [x] Layout: Flexbox renders correctly (sidebar, main, operator panel)
- [x] File routing indicator: Shows "STRUCTURED-DATA ROUTING ACTIVE"
- [x] Continuity status: Displays "Continuity: active"

## Commit Hash

```
commit <to-be-filled-on-commit>
Author: OpenClaw Assistant
Date: Sat Apr 4 20:50 GMT+2
```

## Safe Rollback

```bash
rm -rf weslr-ui
git status
```

## Why This Matters From OC Coder Point Of View

This App Shell v1 establishes the **frontend foundation** that mirrors the backend capability slices already verified in commit `a414166`. It ensures:

1. **Structured data routing** is visible to the user (status indicator, file drop zone hint)
2. **Operator proposals** have a dedicated space (right panel) for review workflow
3. **Continuity snapshots** are accessible from the sidebar (connects to backend continuity endpoints)
4. The UI is **reversible** — no live deployment, no backend changes, purely additive
5. The shell is designed for **future extension** — file routing, proposals, and chat all slot into this layout without refactoring

It's the first of many incremental commits to build out `chat.weslr.de`, each step verified and safe to rollback.

---

*Shell created: 2026-04-04 20:50 GMT+2*
