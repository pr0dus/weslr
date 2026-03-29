# Session: 2026-03-30 - TIA Bridge Privacy & Commercial Handling

## Issue
User wanted the TIA bridge plugin kept secret:
- Already private on GitHub (`github.com/pr0dus/weslr-tia-openness-bridge`)
- Was incorrectly referenced in main Weslr repo as submodule
- Needed to be completely removed from main repo history

## Solution Implemented
- Removed `weslr-tia-openness-bridge` gitlink reference from main repo
- Removed `tia-collector/` directory (50 C#/.NET files)
- Committed with message: "Remove TIA bridge reference - now in separate private repo, commercial for www.weslr.de"
- Pushed to GitHub: `github.com/pr0dus/weslr` (master branch)

## Repository Status After Cleanup
| Repo | Status | Visibility |
|------|--------|------------|
| `github.com/pr0dus/weslr` | Main Weslr | Public (contains only Weslr code) |
| `github.com/pr0dus/weslr-tia-openness-bridge` | TIA bridge plugin | Private (commercial) |

## What Was Removed from Main Repo
1. `weslr-tia-openness-bridge/` - 50 files (gitlink reference)
2. `tia-collector/` - 50 C#/.NET files (full collector implementation)
   - FailureInvestigator/
   - TiaCollector.* (Cli, Config, Core, Export, Normalizer, TiaApi)
   - samples/
3. Total: 100 files removed from main repo

## Commercial Use
- **Product site:** https://www.weslr.de
- **TIA bridge:** Included as commercial premium feature
- **Availability:** For sale via weslr.de
- **Access:** Private repo, only owner and invited collaborators can view

## TIA Bridge Purpose
Extracts engineering data from Siemens TIA Portal V20 projects:
- **What it does:** Reads TIA project offline, exports normalized JSON
- **What it doesn't do:** Modify original project, communicate with SPS/IO
- **Platform:** Windows-only (TIA Portal V20 integration)
- **Output:** JSON matching Weslr entity graph model

## Files Created
- `TIA-BRIDGE-README.md` (2,232 bytes) — Commercial documentation
- Updated `MEMORY.md` with TIA bridge privacy session

## Key Points for Future Reference
1. **TIA bridge is PRIVATE** — Not in main repo, separate private GitHub repo (`github.com/pr0dus/weslr-tia-openness-bridge`)
2. **Commercial product** — Sold via www.weslr.de as premium feature
3. **Access control** — Only owner + invited collaborators can see the private repo
4. **Integration method** — Plugin system (runtime), not embedded in main repo
5. **No data leakage** — All code stays on user's local Windows PC

## Main Weslr GitHub Repo Contains
- ✅ Weslr Python modules (weslr_*.py, entity_*.py, consciousness_*.py, etc.)
- ✅ Commands directory (commands/)
- ✅ Documentation (docs/)
- ❌ NO TIA bridge code (removed `tia-collector/`, `collector/tia_openness_bridge/`)
- ❌ NO C# collector code (removed 50 .NET files)
- ✅ Only commercial docs reference (`docs/tia-bridge/README.md`)
- ✅ Only session memory reference (`memory/2026-03-30-tia-bridge-private.md`)

## Private TIA Bridge Repo
- `github.com/pr0dus/weslr-tia-openness-bridge` — Private, commercial
- Contains full C#/.NET TIA collector implementation
- Accessible only to owner and invited collaborators
- Used for Windows-specific TIA Portal V20 integration
