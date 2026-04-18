# Weslr Deployment Profiles

## Current Active Profile: public_test

| Setting | Value |
|---------|-------|
| Public Mode | Yes |
| Self-Improvement Public | No |
| Read-Only Tools | Yes |
| Max Input | 10,000 chars |
| Max Response | 100KB |
| Rate Limit | 10 req/5min/IP |

## Available Profiles

### public_test (default)
- Public-facing deployment
- Read-only tools only
- Self-improvement internal-only
- Strict rate limiting
- Output scrubbing required

### managed_customer
- Customer-facing deployment
- Read-only tools only
- Self-improvement internal-only
- Moderate rate limiting
- Output scrubbing required

### owner_sovereign
- Owner-only deployment
- Full tool access
- Self-improvement internal-only
- Minimal restrictions
- Full debug mode available

### development
- Internal development
- Full tool access
- Self-improvement internal-only
- No rate limits
- Debug mode enabled

## Setting Active Profile

```bash
# Set via environment variable
export WESLR_ACTIVE_PROFILE=public_test

# Or in .env file
WESLR_ACTIVE_PROFILE=public_test
```

## Profile Contract

Each profile defines:
1. **Security posture** - What is allowed/restricted
2. **Self-improvement visibility** - Who sees improvement proposals
3. **Feature access** - Which tools and features enabled
4. **Audit requirements** - What must be logged
