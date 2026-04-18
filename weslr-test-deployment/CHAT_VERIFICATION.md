# Weslr Chat Verification (PRIVATE EXPERIMENTAL ONLY)

## Status: Token Expired

The OpenAI JWT token in auth-profiles.json has expired (expired 2026-04-04).

## What Was Tested

1. **OpenAI Auth Path Reuse** ✅
   - Weslr reads token from same `auth-profiles.json` as OpenClaw
   - Sets `OPENAI_API_KEY` env var before llm_runtime import
   - Uses `openai_compatible` provider with `https://chatgpt.com/backend-api`
   - Same provider and endpoint as OpenClaw

2. **Current Result** ❌
   - Token expired → falls back to local simulator
   - Source: `fallback` (not `openai` or `openai_compatible`)
   - Reply from local simulator, not LLM

## Verification Commands

After re-authenticating OpenClaw, run:

```bash
# Test chat endpoint
curl -s -X POST http://127.0.0.1:8091/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hey"}'

# Check source field - should be "openai" or "openai_compatible"
# Currently shows "fallback" because token is expired
```

## Current /api/chat Endpoint

```python
def chat(message: str) -> Dict[str, Any]:
    """Process a chat message and return LLM-backed reply.
    
    To reuse OpenClaw's OpenAI auth path:
    - Read JWT token from auth-profiles.json
    - Set as OPENAI_API_KEY temporarily
    - Change provider to "openai_compatible"
    
    Returns:
        { success: bool, reply: str, intent: dict, source: str }
    """
```

## After Token Refresh

When you re-authenticate with OpenAI via OpenClaw UI:

1. New token will be written to `auth-profiles.json`
2. Token will have future `exp` timestamp
3. Restart Weslr test deployment
4. `/api/chat` should show `source: "openai_compatible"` or similar
5. Reply should come from actual LLM, not fallback

## PRIVATE EXPERIMENTAL WARNING

This setup is:
- ✅ Private test deployment only
- ✅ No production code modified
- ✅ No public website changes
- ⚠️ NOT production-ready
- ⚠️ Uses OpenAI OAuth without refresh mechanism
- ⚠️ No token rotation

## Long-term Production Auth Path (To Be Proposed)

After verifying this works with fresh token, we'll propose:
- Secure token storage (encrypted)
- Automatic token refresh
- Session management
- Rate limiting
- Error handling
- Production logging
