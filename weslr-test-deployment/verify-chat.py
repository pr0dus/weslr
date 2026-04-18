#!/usr/bin/env python3
"""Verify Weslr chat endpoint with provider-backed reply."""

import sys
import os
import json
import urllib.request
from pathlib import Path

# Add workspace to path
WORKSPACE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE))

def verify_openai_auth():
    """Check if OpenAI auth token is valid."""
    auth_paths = [
        WORKSPACE / "agents" / "main" / "agent" / "auth-profiles.json",
        Path.home() / ".openclaw" / "agents" / "main" / "agent" / "auth-profiles.json",
    ]
    
    for auth_path in auth_paths:
        if not auth_path.exists():
            continue
        
        print(f"Checking: {auth_path}")
        
        with open(auth_path, 'r') as f:
            auth_data = json.load(f)
        
        profiles = auth_data.get("profiles", {})
        codex_profile = profiles.get("openai-codex:default")
        
        if not codex_profile:
            print("  No openai-codex profile found")
            continue
        
        if codex_profile.get("type") != "oauth":
            print(f"  Profile type: {codex_profile.get('type')} (expected 'oauth')")
            continue
        
        token = codex_profile.get("access", "")
        if not token:
            print("  No access token found")
            continue
        
        print(f"  Token found (length: {len(token)})")
        
        # Decode and check expiration
        import base64
        payload_b64 = token.split('.')[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        payload = json.loads(base64.b64decode(payload_b64))
        
        exp = payload.get('exp', 0)
        import datetime
        exp_time = datetime.datetime.fromtimestamp(exp).isoformat()
        now = datetime.datetime.now().timestamp()
        is_expired = now > exp
        
        print(f"  Token expires: {exp_time}")
        print(f"  Token expired: {'YES - needs refresh' if is_expired else 'NO'}")
        
        return token, auth_path, not is_expired
    
    print("No auth profiles found")
    return None, None, False

def test_chat_endpoint():
    """Test the chat endpoint directly."""
    try:
        from weslr_backend_contract import chat
        
        print("\n=== Testing /api/chat ===")
        
        test_messages = [
            "hey",
            "How are you?",
            "Tell me about yourself",
        ]
        
        for msg in test_messages:
            result = chat(msg)
            source = result.get('source', 'unknown')
            success = result.get('success', False)
            reply = result.get('reply', '')[:150]
            
            print(f"\nMessage: {msg!r}")
            print(f"  Source: {source}")
            print(f"  Success: {success}")
            print(f"  Reply: {reply}...")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_direct_openai_api():
    """Test direct OpenAI API call."""
    token, auth_path, is_valid = verify_openai_auth()
    
    if not token or not is_valid:
        print("\nSkipping direct API test - token expired or not found")
        return
    
    url = "https://chatgpt.com/backend-api/codex/responses"
    print(f"\n=== Testing direct OpenAI API ===")
    print(f"URL: {url}")
    
    body = json.dumps({
        "model": "gpt-4o",
        "stream": False,
        "input": [{"role": "user", "content": "Say hello in 5 words"}],
    }).encode()
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
            print("✅ SUCCESS!")
            print(json.dumps(payload, indent=2)[:800])
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} {e.reason}")
        print(e.read().decode()[:500])
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)[:500]}")

if __name__ == "__main__":
    print("=" * 60)
    print("WESLR CHAT VERIFICATION")
    print("=" * 60)
    
    print("\n--- Checking OpenAI Auth ---")
    verify_openai_auth()
    
    test_direct_openai_api()
    test_chat_endpoint()
    
    print("\n" + "=" * 60)
    print("Verification complete")
    print("=" * 60)
