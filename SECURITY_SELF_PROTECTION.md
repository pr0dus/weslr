# Security Self-Protection Layer — Design Specification

## Overview

**Platform:** OpenClaw (Weslr)  
**Version:** v1  
**Status:** Design Phase  
**Last Updated:** 2026-04-03  

This document defines the Security Self-Protection Layer — a critical infrastructure module that ensures platform integrity, prevents unauthorized self-modification, detects malicious patterns, and enables safe self-evolution.

---

## SECTION 1 — SELF-PROTECTION ARCHITECTURE

### 1.1 Module Responsibility Matrix

| Module | Responsibility | Non-Bypassable? |
|--------|----------------|-----------------|
| `security/self-protection/index.js` | Core orchestration, rule evaluation, enforcement | YES |
| `security/detector/` | Threat detection layer (malicious patterns, privilege escalation) | YES |
| `security/risk-engine/index.js` | Risk scoring engine (weighted scoring across threat types) | YES |
| `security/gate/self-code-review.js` | Self-code review gate (pre-commit validation) | YES |
| `security/gate/self-evolution.js` | Self-evolution validation gate | YES |
| `security/rollback/index.js` | Rollback enforcement and state recovery | YES |
| `security/audit/index.js` | Immutable audit trail (write-only, append-only) | YES |
| `security/continuity/index.js` | Anomaly detection across continuity and memory | YES |
| `security/policy/index.js` | Policy storage and rule validation | YES |

### 1.2 Enforcement Points

| Layer | Enforcement | Method |
|-------|-------------|--------|
| **Pre-Write** | File system modifications | `fs.write*` wrappers + boundary checks |
| **Pre-Exec** | Command execution | Hook into `exec`, `spawn`, `child_process` |
| **Pre-Evolution** | Self-modification | Hook into `require`, dynamic imports |
| **Runtime** | Tool invocation | Plugin tool pipeline interception |
| **Persistence** | Audit logging | Write-only append with cryptographic chaining |

### 1.3 Data Flow

```
[Self-Mod Attempt] → [Self-Code-Review Gate] → [Risk Scoring] → [Policy Evaluation] → [Enforcement]
                                     ↓
                       [Threat Detector] → [Risk Score + Threat Tags]
                                     ↓
                    [Audit Trail] → [Write-Only Log (Cryptographically Chained)]
```

---

## SECTION 2 — SAFE SELF-EVOLUTION RULES

### 2.1 Evolution Taxonomy

| Type | Description | Approval Required? | Reversible? |
|------|-------------|-------------------|-------------|
| **Additive** | New files, functions, types | NO (if < 500 lines) | YES (delete) |
| **Modificative** | Changes to existing code | YES | YES (git checkout) |
| **Deletive** | Removal of files/functions | YES | MAYBE (if history preserved) |
| **Reconfig** | Configuration changes | IF affects security | YES (config rollback) |
| **Dependency** | npm package installs | IF new binary exec | YES (uninstall) |

### 2.2 Hard Constraints (Never Self-Modifiable)

```javascript
// These files are ALWAYS protected
const IMMUTABLE_PATTERNS = [
  "security/**/*",              // Self-protection modules
  "dist/*.mjs",                 // Compiled entry points
  "package.json",               // Dependency manifest
  "openclaw.mjs",               // CLI entry point
  "dist/index.js",              // Main distribution
  ".openclaw/workspace/**/*",  // User workspace (unless explicit user grant)
];
```

### 2.3 Reversibility Requirements

| Change Type | Mechanism | Timeout |
|-------------|-----------|---------|
| Additive | Git LFS blob storage | 72h |
| Modificative | Git diff patch | 24h |
| Reconfig | Config snapshot + diff | 1h |
| Dependency | npm lock revert | Immediate |

### 2.4 Self-Evolution Workflow

```
1. Agent proposes change (via self-modify tool)
2. Self-Code-Review Gate: Static analysis, pattern detection
3. Risk Engine: Calculate risk score (0-100, weighted by threat type)
4. Policy Engine: Compare against policy thresholds
5. If score < threshold:
   - Apply change
   - Log audit trail (append-only)
   - Create rollback artifact
6. If score >= threshold:
   - Reject change
   - Notify operator
   - Log security event
```

---

## SECTION 3 — THREAT & MALICIOUS CODE DETECTION

### 3.1 Detection Categories

| Category | Detection Logic | False-Positive Rate | Response |
|----------|----------------|---------------------|----------|
| **Code Injection** | AST pattern matching for `eval`, `new Function`, `child_process` | Low | Block + Alert |
| **Privilege Escalation** | Look for `--no-sandbox`, `sudo`, `setuid`, `chmod +s` | Medium | Block + Alert |
| **Prompt Poisoning** | Anomaly detection in system prompts (KL divergence) | High | Monitor |
| **Plugin Compromise** | Signature verification, hash comparison | Low | Block + Revoke |
| **Continuity Corruption** | Memory state deviation (chi-squared test) | Medium | Rollback |
| **Persistence Attacks** | Cron entries, systemd units, launchd configs | Medium | Block + Audit |
| **Data Exfiltration** | Network calls to non-allowlisted hosts | Low | Block + Alert |

### 3.2 Risk Scoring Formula

```
risk_score = 
    (code_injection * 0.35) +
    (privilege_escalation * 0.30) +
    (continuity_corruption * 0.20) +
    (plugin_compromise * 0.15) +
    (base_complexity * 0.10)

Where:
  - code_injection: binary (0/1) from AST scan
  - privilege_escalation: binary from command analysis
  - continuity_corruption: continuous (0-1) from state deviation
  - plugin_compromise: binary from signature verification
  - base_complexity: token count normalization (0-1)
```

### 3.3 Detection Modules

#### `security/detector/malicious-code.js`

```javascript
const MALICIOUS_PATTERNS = [
  { name: "eval_injection", pattern: /(?:\beval\b|\bFunction\b|\bescape\b)/ },
  { name: "child_process_rce", pattern: /(?:child_process\.(?:exec|spawn|execSync)|spawnSync)/ },
  { name: "fs_write_anywhere", pattern: /(?:fs\.writeFileSync|fs\.writeFile)\s*\(\s*["'](?:\/|[a-zA-Z]:)/ },
  { name: "eval_via_proxy", pattern: /(?:import\(\s*["']|import\(\s*process\.env|import\(\s*require\.resolve)/ },
  { name: "setuid_sudo", pattern: /(?:sudo|setuid|chmod\s+\+s)/ },
  { name: "network_exfiltration", pattern: /(?:fetch|axios|request)\s*\([^)]*https?:\/\/[^\s"'&]+[?&]data=|[?&]token=|[?&]key=/ },
];
```

#### `security/detector/continuity.js`

```javascript
// Continuity anomaly detection
function detectContinuityAnomaly(stateSnapshot, baseline) {
  const deviation = calculateKLDeviation(stateSnapshot, baseline);
  return {
    isAnomaly: deviation > 0.25, // Threshold
    deviationScore: deviation,
    affectedModules: identifyChangedModules(stateSnapshot, baseline),
  };
}
```

---

## SECTION 4 — IMPLEMENTATION PLAN

### 4.1 Phase 1: Core Infrastructure (Lowest Risk)

**Goal:** Establish audit trail and detection primitives.

**Deliverables:**

1. **`security/audit/index.js`** — Immutable audit trail
   - Write-only append to `.openclaw/audit/`
   - Each entry: `{ timestamp, type, hash, prevHash, dataHash }`
   - SHA-256 chaining

2. **`security/detector/index.js`** — Detection primitives
   - Pattern matching (AST and regex)
   - Baseline comparison
   - Anomaly scoring

3. **`security/risk-engine/index.js`** — Risk scoring
   - Weighted scoring
   - Threshold configuration
   - Logging integration

**Rollback:** Delete `security/` directory and restart gateway.

### 4.2 Phase 2: Self-Code Review Gate (Medium Risk)

**Goal:** Prevent unsafe self-modification.

**Deliverables:**

1. **`security/gate/self-code-review.js`**
   - Hook `require`, dynamic imports
   - Static analysis of proposed changes
   - Policy enforcement

2. **Integration with Gateway CLI**
   - Intercept `self-modify` tool calls
   - Route through gate before execution

**Rollback:** Update `gateway-cli.js` to remove gate integration.

### 4.3 Phase 3: Self-Evolution Validation (Medium Risk)

**Goal:** Enable safe self-evolution.

**Deliverables:**

1. **`security/gate/self-evolution.js`**
   - Version migration validation
   - Compatibility checks
   - Rollback artifact creation

2. **Rollback System**
   - Git-based state snapshots
   - Timestamped rollback points
   - Recovery commands (`openclaw security rollback --to <timestamp>`)

**Rollback:** Remove evolution gate and restore previous gateway CLI.

### 4.4 Phase 4: Continuity Protection (Medium Risk)

**Goal:** Detect continuity poisoning.

**Deliverables:**

1. **`security/continuity/index.js`**
   - Memory state checksums
   - Session transcript integrity
   - Anomaly alerts

2. **Recovery**
   - Automatic rollback on anomaly
   - Operator notification

**Rollback:** Disable continuity module and restart.

---

## SECTION 5 — POLICY CONFIGURATION

### 5.1 Policy Schema

```json
{
  "selfEvolution": {
    "maxAdditiveLines": 500,
    "maxModificativeLines": 100,
    "requiresApproval": ["modificative", "deletive"],
    "forbiddenPatterns": ["eval(", "child_process", "setuid"]
  },
  "riskThresholds": {
    "autoBlock": 80,
    "alertOnly": 50,
    "allow": 0
  },
  "audit": {
    "enabled": true,
    "retentionDays": 30,
    "encrypted": true
  }
}
```

### 5.2 Policy Storage

- **Location:** `.openclaw/config/security-policy.json`
- **Permissions:** `0600`
- **Validation:** JSON schema validation on load

---

## SECTION 6 — COMMAND-LINE INTERFACE

### 6.1 Security Commands

```bash
# Audit trail inspection
openclaw security audit [--follow] [--since <date>]

# Risk status
openclaw security risk [--module <name>]

# Rollback
openclaw security rollback [--to <timestamp>] [--dry-run]

# Self-evolution review
openclaw security evolve [--list] [--apply <id>]

# Continuity health
openclaw security continuity [--check] [--reset]
```

---

## SECTION 7 — TESTING STRATEGY

### 7.1 Unit Tests

- Detection pattern matching accuracy
- Risk score calculation
- Audit trail chaining
- Rollback artifact creation

### 7.2 Integration Tests

- Gateway CLI integration
- Self-modification blocking
- Policy enforcement
- Recovery workflow

### 7.3 Penetration Tests

- Attempt to bypass self-code review
- Inject malicious patterns
- Modify audit trail (should fail)
- Corrupt continuity state (should rollback)

---

## SECTION 8 — ROLLBACK STRATEGY

### 8.1 Immediate Rollback (Emergency)

```bash
# Stop gateway
openclaw gateway stop

# Delete security module
rm -rf src/security dist/security

# Restart
openclaw gateway start
```

### 8.2 Config Rollback

```bash
# Restore previous policy
cp .openclaw/config/security-policy.json.bak .openclaw/config/security-policy.json
```

### 8.3 State Rollback

```bash
# Restore from audit log
openclaw security rollback --to 2026-04-03T12:00:00Z
```

---

## IMPLEMENTATION CHECKLIST

- [ ] Phase 1: Core Infrastructure
  - [ ] Audit trail module (append-only)
  - [ ] Detection primitives (AST scanning)
  - [ ] Risk scoring engine

- [ ] Phase 2: Self-Code Review Gate
  - [ ] Hook `require`, dynamic imports
  - [ ] Static analysis
  - [ ] Policy enforcement

- [ ] Phase 3: Self-Evolution Validation
  - [ ] Version migration checks
  - [ ] Rollback artifact creation
  - [ ] Recovery commands

- [ ] Phase 4: Continuity Protection
  - [ ] Memory state checksums
  - [ ] Session transcript integrity
  - [ ] Anomaly alerts

- [ ] Documentation
  - [ ] User guide
  - [ ] Operator playbooks
  - [ ] Incident response procedures

---

**END OF SPECIFICATION**
