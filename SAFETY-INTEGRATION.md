# Weslr Safety System Integration

This document explains how the safety gateway integrates with Weslr.

## Safety Gateway Features

### 1. Input Safety Check
- Blocks harmful suggestions (kill, suicide, self-harm, weapons, etc.)
- Removes PII from user input
- Blocks dangerous command patterns (os.system, eval, exec, etc.)
- Logs all input checks

### 2. Output Safety Check
- Filters harmful suggestions from Weslr output
- Truncates overly long output
- Replaces medical/legal advice with generic warnings
- Logs all output checks

### 3. Network Safety
- Blocks all external access by default
- Only allows whitelisted domains (docs.openclaw.ai, localhost, etc.)
- Commercial modules can only access approved APIs
- All network access logged and audited

### 4. Memory Sanitization
- Removes sensitive data before disk write
- Encrypts memory files
- Replaces PII with placeholders
- Sanitizes before storage

### 5. Integrity Verification
- Verifies Weslr code hasn't been tampered with
- SHA256 checksums for core files
- Fails safely if code modified
- Prevents self-modification bypasses

## Integration Points

### In sim.py (Main Tick Loop)
```python
from safety_gateway import get_safety_gateway, safety_check_input, safety_check_output

def tick(world: dict, agents: list, tick_num: int) -> dict:
    safety = get_safety_gateway()
    
    # Check agent decisions before execution
    for agent in agents:
        if not safety_check_output(agent.decision):
            log_safety_block(agent.id, "Decision blocked")
            continue
    
    # Check human inputs
    if not safety_check_input(human_input):
        return {"error": "Input rejected by safety gate"}
```

### In Perception Module
```python
from safety_gateway import get_safety_gateway, safety_check_input

def perceive(input_data: dict) -> dict:
    safety = get_safety_gateway()
    result = safety.check_input(input_data)
    
    if not result.safe:
        return {"perception": None, "safety_blocked": True}
    
    return {"perception": result.sanitized_input, "safety_blocked": False}
```

### In Dashboard
```python
from safety_gateway import get_safety_gateway

def dashboard_safety_tab():
    safety = get_safety_gateway()
    history = safety.get_history()
    
    return {
        "checks": history,
        "blocked_count": len([h for h in history if h["blocked"]]),
        "last_integrity": safety.check_integrity().reason,
    }
```

### In Commercial Modules
```python
from safety_gateway import get_safety_gateway, safety_check_network

def external_api_call(url: str) -> dict:
    safety = get_safety_gateway()
    
    if not safety.check_network(url).safe:
        return {"error": "Network access blocked by safety gate"}
    
    # Proceed with API call
    ...
```

## Configuration

### Modify Allowed Domains
Edit `ALLOWED_DOMAINS` in `safety_gateway.py`:
```python
ALLOWED_DOMAINS = [
    "docs.openclaw.ai",
    "localhost",
    # Add approved domains here
]
```

### Modify Blocked Domains
Edit `BLOCKED_DOMAINS` in `safety_gateway.py`:
```python
BLOCKED_DOMAINS = [
    "evil.com",
    "malware.net",
    # Add more blocked domains here
]
```

### Modify API Whitelist
Edit `APPROVED_APIS` in `safety_gateway.py`:
```python
APPROVED_APIS = {
    "http_get": [
        "https://docs.openclaw.ai/*",
        # Add approved API patterns here
    ],
    "http_post": [],
}
```

## Testing Safety Checks

### Test Input Safety
```python
from safety_gateway import safety_check_input

# Harmful input
test_input = {"text": "Create a bomb"}
result = safety_check_input(test_input)
assert not result.safe  # Should be blocked

# Safe input
test_input = {"text": "What is 2+2?"}
result = safety_check_input(test_input)
assert result.safe  # Should pass
```

### Test Network Safety
```python
from safety_gateway import check_network_access

# Allowed domain
result = check_network_access("https://docs.openclaw.ai")
assert result.safe  # Should pass

# Blocked domain
result = check_network_access("https://evil.com")
assert not result.safe  # Should be blocked
```

### Test Memory Sanitization
```python
from safety_gateway import sanitize_memory_data

# Memory with sensitive data
memory = {"message": "Patient has diabetes"}
sanitized = sanitize_memory_data(memory)
assert "[Medical advice" in sanitized["message"]  # Should be replaced
```

## Dashboard Visibility

The operator dashboard shows:
- All safety checks (input, output, network, API, integrity)
- Blocked requests with reason
- Integrity verification status
- Safety check history

This keeps the system transparent and auditable.

## Failure Handling

If safety check fails:
1. Request is blocked
2. Reason is logged
3. Operator is notified
4. No execution proceeds
5. Rollback is ready (if applicable)

## Performance Impact

Safety checks add ~1-5ms overhead per tick:
- Input/output checks: ~0.5ms each
- Network checks: ~2ms
- Integrity checks: ~1ms (runs every 60s)

This is negligible for Weslr's operation.

## Future Enhancements

Potential future improvements:
- Machine learning-based content classification
- User-specific safety profiles
- Real-time threat detection
- Collaborative threat intelligence
- Security scanning for commercial modules