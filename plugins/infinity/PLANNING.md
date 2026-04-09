# Infinity Productization — Phase 1 Licensing Core

**Status:** PLANNING — NO IMPLEMENTATION YET  
**Focus:** Licensing foundation only (no continuity logic, no restore hooks, no website)  
**Constraints:** 1 OC, 3 OC, 7 OC, Unlimited OC tiers  
**Duration:** 12 months  

---

## 1. EXACT FILE PLAN

### New Files (Licensing Core)

| File | Purpose | Lines |
|------|---------|-------|
| `plugins/infinity/licensing/schema.js` | License schema definitions | ~100 |
| `plugins/infinity/licensing/validator.js` | License validation logic | ~150 |
| `plugins/infinity/licensing/signer.js` | License signing/verification | ~120 |
| `plugins/infinity/licensing/inspector.js` | License file inspection | ~80 |
| `plugins/infinity/licensing/enforcer.js` | Instance limit enforcement | ~180 |

### Modified Files

| File | Purpose | Lines |
|------|---------|-------|
| `plugins/infinity/config.js` | Add `licensing` config section | ~30 |

### No Other Files Modified

**Rationale:** Focus on licensing core only. No continuity, no restore, no website changes.

---

## 2. EXACT IMPLEMENTATION SCOPE

### What Licensing Core Does

1. **License File Format:** Define `.openclaw/licenses/infinity-license.json` structure
2. **License Validation:** Verify license integrity (signature, expiration, instance limit)
3. **Instance Enforcement:** Count active instances and enforce limits per tier
4. **Renewal Tracking:** Track license renewal status and update entitlements
5. **Tier Definitions:** Implement 1 OC, 3 OC, 7 OC, Unlimited tiers

### What Licensing Core Does NOT Do

- ❌ No continuity logic (v1 scope maintained)
- ❌ No restore hooks (v1 scope maintained)
- ❌ No website integration (external to Infinity scope)
- ❌ No CLI commands (licensing is internal)
- ❌ No user prompts (silent-first)
- ❌ No background workers (no scheduler, per v1 scope)

### Licensing Core Scope

- ✅ License file format and structure
- ✅ License validation (signature, expiration, instance limit)
- ✅ Instance counting and enforcement
- ✅ License signing and verification
- ✅ Renewal tracking and update entitlements
- ✅ Tier definitions and limits

---

## 3. EXACT TOKEN/LICENSE SCHEMA

### License File Format

```json
{
  "meta": {
    "formatVersion": "1.0",
    "type": "infinity-license"
  },
  "license": {
    "id": "license-uuid",
    "tier": "1oc" | "3oc" | "7oc" | "unlimited",
    "issuedAt": "2026-04-09T00:00:00Z",
    "expiresAt": "2027-04-09T00:00:00Z",
    "renewable": true,
    "maxInstances": 1 | 3 | 7 | -1
  },
  "instance": {
    "id": "instance-uuid",
    "installedAt": "2026-04-09T00:00:00Z",
    "lastActive": "2026-04-09T08:00:00Z",
    "hostname": "machine-hostname",
    "openclawVersion": "2026.3.13",
    "workspace": "/data/data/com.termux/files/home/.openclaw/workspace"
  },
  "signature": {
    "algorithm": "RSA-SHA256",
    "publicKey": "base64-encoded-public-key",
    "signature": "base64-encoded-signature"
  },
  "entitlements": {
    "updateEligibleUntil": "2027-04-09T00:00:00Z",
    "supportsRenewal": true,
    "supportLevel": "standard"
  },
  "audit": {
    "createdBy": "license-server",
    "createdAt": "2026-04-09T00:00:00Z",
    "lastValidated": "2026-04-09T08:00:00Z"
  }
}
```

### Tier Definitions

| Tier | `tier` Value | `maxInstances` | `description` |
|------|--------------|----------------|---------------|
| 1 OC | `1oc` | 1 | Single instance license |
| 3 OC | `3oc` | 3 | Up to 3 instances |
| 7 OC | `7oc` | 7 | Up to 7 instances |
| Unlimited | `unlimited` | -1 | No instance limit |

### Instance Metadata Format

```json
{
  "instanceId": "uuid",
  "workspace": "absolute-path",
  "installedAt": "ISO-8601-timestamp",
  "lastActive": "ISO-8601-timestamp",
  "hostname": "machine-name",
  "openclawVersion": "2026.3.13"
}
```

---

## 4. EXACT VALIDATION STRATEGY

### Validation Checklist

1. **File Existence:** License file must exist at `.openclaw/licenses/infinity-license.json`
2. **Format Valid:** JSON parseable with required fields
3. **Signature Valid:** RSA-SHA256 signature matches content
4. **Not Expired:** `expiresAt` > current time
5. **Instance Limit:** Current instances ≤ `maxInstances`
6. **Entitlement Active:** `updateEligibleUntil` > current time (if renewal required)
7. **Workspace Match:** Workspace path matches license (`workspace` field)
8. **OpenClaw Version:** Version compatibility check (optional, for future-proofing)

### Validation Flow

```
License Loaded
    ↓
1. Parse JSON
    ↓
2. Validate required fields
    ↓
3. Verify signature (public key + signature + content)
    ↓
4. Check expiration
    ↓
5. Count active instances
    ↓
6. Check instance limit
    ↓
7. Check update entitlement
    ↓
8. Check workspace match
    ↓
9. Check OpenClaw version compatibility
    ↓
Result: VALID / INVALID + reason
```

### Validation Response Format

```json
{
  "valid": true | false,
  "reason": "valid" | "expired" | "invalid-signature" | "instance-limit-exceeded" | ...,
  "details": {
    "licenseId": "uuid",
    "currentInstances": 3,
    "maxInstances": 3,
    "expiresAt": "2027-04-09T00:00:00Z",
    "currentInstance": { /* instance metadata */ }
  }
}
```

---

## 5. EXACT SIGNING STRATEGY

### Signing Algorithm

- **Algorithm:** RSA-SHA256
- **Key Length:** 2048-bit minimum
- **Format:** PKCS#8 PEM for private key, PKCS#1 PEM for public key

### Signing Process

1. **License Generation:**
   - Create license JSON (without signature)
   - Compute SHA-256 hash of content
   - Sign hash with private key
   - Embed signature + public key in license

2. **Verification:**
   - Extract signature + public key from license
   - Recompute SHA-256 hash of content
   - Verify signature with public key

### Key Management

| Key Type | Location | Permissions | Purpose |
|----------|----------|-------------|---------|
| Private Key | `.openclaw/keys/infinity-private.pem` | 600 | Sign licenses (build-time only) |
| Public Key | `.openclaw/keys/infinity-public.pem` | 644 | Verify licenses (runtime) |

### Key Generation (Build-Time)

```bash
# Generate RSA key pair
openssl genrsa -out infinity-private.pem 2048
openssl rsa -pubout -in infinity-private.pem -out infinity-public.pem

# Embed public key in license during generation
# Store private key securely (not shipped)
```

### Signature Inclusion

Signature is included in license JSON as:

```json
"signature": {
  "algorithm": "RSA-SHA256",
  "publicKey": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
  "signature": "base64-encoded-signature-here"
}
```

---

## 6. EXACT INSTANCE-LIMIT ENFORCEMENT DESIGN

### Instance Detection

**Instance = Unique workspace + unique identifier**

- **Workspace ID:** Absolute path to `.openclaw/workspace`
- **Instance ID:** Machine-specific identifier (hostname + system ID)

### Instance Counting

1. **Scan License Directory:**
   - Find all license files in `.openclaw/licenses/`
   - Extract instance metadata from each

2. **Filter Active Instances:**
   - Check `lastActive` timestamp (recent = active)
   - Verify workspace exists
   - Verify instance matches current machine

3. **Count by Tier:**
   - Count instances per license tier
   - Compare to `maxInstances` from license

### Instance Limit Enforcement

| Tier | Current Instances | Max Instances | Result |
|------|-------------------|---------------|--------|
| 1 OC | 0 | 1 | ✅ OK |
| 1 OC | 1 | 1 | ✅ OK |
| 1 OC | 2 | 1 | ❌ Exceeded |
| 3 OC | 0 | 3 | ✅ OK |
| 3 OC | 3 | 3 | ✅ OK |
| 3 OC | 4 | 3 | ❌ Exceeded |
| 7 OC | 0 | 7 | ✅ OK |
| 7 OC | 7 | 7 | ✅ OK |
| 7 OC | 8 | 7 | ❌ Exceeded |
| Unlimited | 0 | -1 | ✅ OK (always) |

### Enforcement Response

**If Instance Limit Exceeded:**
- Set `license.valid = false`
- Set `reason = "instance-limit-exceeded"`
- Include `currentInstances` and `maxInstances` in details
- No error thrown (silent-first)

---

## 7. EXACT RENEWAL / UPDATE ENTITLEMENT DESIGN

### Entitlement Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `updateEligibleUntil` | ISO-8601 | License `expiresAt` | Until when updates are free |
| `supportsRenewal` | Boolean | `true` | Can license be renewed? |
| `supportLevel` | Enum | "standard" | Support access level |

### Renewal Scenarios

#### Scenario 1: License Active, Updates Eligible
- `expiresAt` > now
- `updateEligibleUntil` > now
- `supportsRenewal` = true
- **Result:** License valid, updates allowed, renewal available

#### Scenario 2: License Expired, No Renewal
- `expiresAt` < now
- `supportsRenewal` = false
- **Result:** License invalid, no updates, no renewal

#### Scenario 3: License Expired, Renewable
- `expiresAt` < now
- `supportsRenewal` = true
- **Result:** License invalid, renew to continue

#### Scenario 4: Updates Expired, Renewed
- `expiresAt` > now
- `updateEligibleUntil` < now
- **Result:** License valid, updates expired, renewal needed for updates

### Update Entitlement Check

```
If updateEligibleUntil < now:
    - Updates not included in current license
    - User must renew for updates
    - License still valid if expiresAt > now
Else:
    - Updates included
    - License fully functional
```

---

## 8. EXACT TEST PLAN

### Test Categories

| Category | Files | Tests | Coverage |
|----------|-------|-------|----------|
| Schema tests | `test_licensing_schema.js` | 10 | License JSON structure |
| Validation tests | `test_licensing_validation.js` | 20 | All validation checks |
| Signing tests | `test_licensing_signer.js` | 15 | Signature generation/verification |
| Instance tests | `test_licensing_inspector.js` | 10 | Instance detection/counting |
| Enforcement tests | `test_licensing_enforcer.js` | 20 | Instance limit enforcement |
| Renewal tests | `test_licensing_renewal.js` | 15 | Renewal/update scenarios |
| Integration tests | `test_licensing_integration.js` | 10 | End-to-end workflow |
| **Total** | 7 files | **100** | 100% |

### Test Focus Areas

**Schema Tests:**
- License JSON structure validation
- Required field checks
- Optional field defaults
- Tier value validation

**Validation Tests:**
- Format validity
- Signature verification
- Expiration checks
- Instance limit checks
- Entitlement checks
- Workspace match checks

**Signing Tests:**
- Key generation
- Signature generation
- Signature verification
- Public key embedding
- Tamper detection

**Instance Tests:**
- Instance detection
- Instance counting
- Workspace matching
- Hostname verification

**Enforcement Tests:**
- Instance limit exceeded
- Unlimited tier (always OK)
- Edge cases (exact limit, over limit)
- Multiple licenses

**Renewal Tests:**
- Active license, updates included
- Expired license, renewable
- Expired license, not renewable
- Updates expired, license valid

**Integration Tests:**
- End-to-end license generation
- Full validation flow
- Instance limit enforcement
- Renewal workflow

---

## 9. STOP

**Status:** Planning complete. No implementation yet.

**Ready for:** Infinity Productization — Phase 1 Licensing Core implementation (after explicit user approval)

**Constraints Maintained:**
- ✅ No continuity logic changes
- ✅ No restore hooks modified
- ✅ No website changes
- ✅ Focus on licensing core only

**Next Step:** Implement Phase 1 licensing core files (schema, validator, signer, inspector, enforcer)
