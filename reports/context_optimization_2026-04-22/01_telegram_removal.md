# Telegram Removal — OCC Context Optimization

## Telegram Entries Found

### In `openclaw.json`:

| Location | Entry | Value |
|----------|-------|-------|
| `channels.telegram.enabled` | bool | `true` |
| `channels.telegram.botToken` | string | `8503793094:AAGp9-j1nKtJ4SSSkVNAwF7CJe05bca_WwQ` |
| `channels.telegram.allowFrom` | array | `["*"]` |
| `channels.telegram.dmPolicy` | string | `"open"` |
| `channels.telegram.groupPolicy` | string | `"allowlist"` |
| `channels.telegram.streaming.mode` | string | `"partial"` |
| `plugins.allow[]` | array entry | `"telegram"` |
| `plugins.entries.telegram.enabled` | bool | `true` |

### Leftover Files (harmless, not touched):
- `/data/data/com.termux/files/home/.openclaw/telegram/update-offset-default.json` — state file, harmless

---

## Changes Made

**File:** `/data/data/com.termux/files/home/.openclaw/openclaw.json`

1. `channels.telegram.enabled` → `false`
2. `plugins.entries.telegram.enabled` → `false`

**NOT removed from `plugins.allow`:** Entry retained for reversibility. Can be removed in a future cleanup pass.

**Bot token retained:** Preserved for potential re-enablement.

---

## Result

- Telegram is **disabled** in active OCC configuration
- No files deleted
- Changes are fully reversible (re-enable by flipping booleans back to `true`)
- Telegram state file at `/data/data/com.termux/files/home/.openclaw/telegram/` untouched — harmless
