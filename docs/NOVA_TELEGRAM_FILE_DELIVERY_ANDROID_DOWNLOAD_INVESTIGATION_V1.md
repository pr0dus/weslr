# Nova Telegram File Delivery / Android Download Location Investigation V1

Date: 2026-06-07
Repo checked: `/data/data/com.termux/files/home/weslr-pr47-clean`
Branch: `master`
HEAD: `e6ff217`

## What I checked
- Repo boundary and git state
- OpenClaw Telegram send path in:
  - `dist/extensions/telegram/send-trgrTBon.js`
  - `dist/extensions/telegram/channel-DQZFZGBt.js`
  - `dist/extensions/telegram/load-options-DwJc4uJu.js`
  - `dist/web-media-DdWWH3Rl.js`
  - `dist/extensions/telegram/delivery-Dt6oBgpk.js`
- Local storage dirs:
  - `~/.openclaw/media`
  - `~/.openclaw/tmp`

## Findings
1. Nova/OpenClaw Telegram media sends are document-style outbound attachments when `forceDocument` / `asDocument` is set, and the adapter ultimately calls `api.sendDocument(...)`.
2. The send path loads the source file directly from the provided path via `loadWebMedia(...)` → `readLocalFileSafely(...)` and wraps the bytes in an `InputFileCtor(media.buffer, fileName)`.
3. I found no Telegram-specific outgoing copy folder or sent-file cache in the send path. The only visible local media store contains inbound samples, and `~/.openclaw/tmp` is generic temp space.
4. I could not verify the requested repo path `/home/pr0/projects/weslr-v1-ui-website` on this host; the accessible repo here is `weslr-pr47-clean`. The exact `site/docs/index.html` and `site/index.html` source paths/timestamps were therefore not confirmable in this environment.

## Likely root cause
This looks like Telegram Android behavior, not a Nova delivery failure:
- “Delivered/downloaded in Telegram” usually means the file exists inside Telegram’s own app storage/cache or is available in-chat.
- That does **not** mean Android has placed a copy into the public `Downloads/` folder.
- On Android, the user typically must use Telegram’s file menu / Save action to copy into public storage.

## Verdict
- Nova delivery issue: **unclear / not evidenced**
- Telegram Android behavior: **likely root cause**
- Public Downloads placement: **not guaranteed by Telegram**

## Owner-safe retrieval workflow
Best options:
1. Telegram file menu → **Save to Downloads** (if available)
2. Telegram → **Share** → ChatGPT / project chat
3. Send a `.zip` bundle instead of only loose files
4. Include a small manifest with:
   - exact filename
   - source path
   - commit hash
   - modified timestamp
   - Telegram message ID
5. If browser download is needed, use a separately approved known server path

## Recommended permanent Nova delivery rule
- Always send files as documents
- Always include exact filename, source path, commit hash, modified timestamp, and Telegram message ID
- Prefer `.zip` bundles for multi-file handoffs
- Never treat “Telegram delivered” as proof the owner can find the file in Android Downloads

## Commands inspected
- `pwd`
- `git rev-parse --show-toplevel`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git status --short`
- `find /data/data/com.termux/files/home -maxdepth 3 -type d -name 'weslr-v1-ui-website' -o -type d -name 'weslr-pr47-clean'`
- `find /data/data/com.termux/files/home/.openclaw/media -maxdepth 2 -type f`
- `find /data/data/com.termux/files/home/.openclaw/tmp -maxdepth 2 -type f`
- Grep/read inspection of the Telegram send/runtime code paths listed above
