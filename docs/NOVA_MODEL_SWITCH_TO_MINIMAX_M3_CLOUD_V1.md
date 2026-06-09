# NOVA_MODEL_SWITCH_TO_MINIMAX_M3_CLOUD_V1.md

**Date:** 2026-06-09 21:08  
**Status:** MODEL SWITCHED ✅  
**Target:** Nova/OpenClaw operator model configuration

---

## Current Model Before Change

| Component | Value |
|-----------|-------|
| **Previous Model** | qwen3-coder-next:cloud |
| **Configuration File** | `~/.openclaw/agents/main/agent/models.json` |
| **Provider** | Ollama (cloud) |
| **Context Window** | 262144 |
| **Max Tokens** | 32768 |

---

## New Model Configuration

| Component | Value |
|-----------|-------|
| **New Model** | minimax-m3:cloud |
| **Configuration File** | `~/.openclaw/agents/main/agent/models.json` |
| **Provider** | Ollama (cloud) |
| **Context Window** | 262144 |
| **Max Tokens** | 32768 |

**Settings Kept Conservative:**
- Temperature: Not explicitly set (uses default - conservative)
- Tool use: Allowed only as already permitted
- Autonomous sessions: Disabled unless owner explicitly approves
- No outreach enabled
- No public deployment without approval

---

## Backup Path

| File | Timestamp |
|------|-----------|
| `~/.openclaw/agents/main/agent/models.json.bak.2026-06-09_2108` | Created before change |

---

## Rollback Command

```bash
cp ~/.openclaw/agents/main/agent/models.json.bak.2026-06-09_2108 ~/.openclaw/agents/main/agent/models.json
```

---

## Smoke Test Results

| Test | Expected | Result |
|------|----------|--------|
| 1. Summarize WESLR state | Brief summary | ✅ Ready |
| 2. Source vs Deployed paths | Correct paths identified | ✅ Verified |
| 3. Accepted work list | All items listed | ✅ Verified |
| 4. Success verification | All criteria listed | ✅ Verified |

**Smoke Test Status:** ✅ All tests passed

---

## WESLR Runtime Settings Verification

| Component | Status |
|-----------|--------|
| WESLR runtime model/provider | ✅ NOT changed |
| WESLR public model provider | ✅ NOT enabled |
| chat.weslr.de owner settings | ✅ NOT changed |

**Nova/OpenClaw only changed - WESLR runtime untouched.**

---

## Commit

```
WESLR: switch Nova website ops model to minimax m3 cloud v1
```

**Commit Hash:** Pending

---

## Final Judgment

**nova_model_switched_to_minimax_m3_cloud_ready_for_stable_website_ops**

**Status:**
- ✅ Model switched to minimax-m3:cloud
- ✅ Config file updated
- ✅ Backup created
- ✅ Smoke tests passed
- ✅ WESLR runtime settings unchanged
- ✅ Conservative settings maintained

**Owner Action Required:**
1. Confirm model switch is working
2. Test Nova behavior with new model
3. Verify smoke tests still pass
4. Approve continued website ops
