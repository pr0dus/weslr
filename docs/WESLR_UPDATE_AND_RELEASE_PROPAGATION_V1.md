# WESLR Update + Release Propagation Contract V1

Date: 2026-05-09
Status: release/deployment contract — no runtime or deployment implementation
Scope: how WESLR changes move from development to hosted production and self-hosted/private deployments

## Purpose

This document defines how WESLR updates should propagate across:

- GitHub development
- staging
- hosted WESLR
- self-hosted/private WESLR
- institutional deployments

The goal is to prevent silent, uncontrolled, or confusing updates once WESLR becomes a public and commercial product.

## Core principle

WESLR updates must be:

```text
versioned
reviewed
tested
staged
operator-approved
rollback-capable
visible to affected users/admins
```

Self-hosted and institutional deployments must never receive silent automatic updates that alter behavior, memory, governance, privacy, billing, or deployment state without an authorized administrator/operator decision.

## Canonical propagation path

Default release flow:

```text
branch / PR
  ↓
GitHub CI and release gates
  ↓
merge to master
  ↓
staging.weslr.de
  ↓
operator review
  ↓
hosted production: chat.weslr.de
  ↓
versioned release package / changelog for self-hosted customers
```

## Release environments

### Development / PR

Purpose:

- small changes
- reviewable diffs
- CI validation
- no public exposure

Rules:

- all changes via PR
- clear scope
- docs/contracts before risky implementation
- CI/release gates pass before merge when applicable

### Master

Purpose:

- canonical source state
- green merged changes
- release candidate source

Rules:

- master should stay releasable or close to releasable
- no known broken gates unless explicitly documented
- no unreviewed public behavior changes

### Staging

Canonical domain:

```text
staging.weslr.de
```

Purpose:

- validate current master or release candidate
- test public UX before hosted production
- verify deployment scripts
- verify rollback
- verify public mode flags

Rules:

- staging may be imperfect but must be isolated
- staging must not touch `e-qubs.de`
- staging must not contain production-only secrets unless specifically configured
- staging must be clearly labeled as staging

### Hosted production

Canonical domain:

```text
chat.weslr.de
```

Purpose:

- hosted WESLR service
- public demo/trial/paid user access

Rules:

- deploy only after staging validation
- operator approval required
- rollback path required
- version/changelog recorded
- no unannounced high-impact behavior changes

### Self-hosted/private deployments

Purpose:

- institution/company/lab/customer-owned deployment
- privacy-sensitive deployment
- organization-controlled runtime and data location

Rules:

- updates are versioned packages or documented update procedures
- customer/admin controls update timing
- no silent core update
- no silent memory migration
- no silent governance change
- rollback or backup required before high-impact updates

## Versioning model

Recommended version pattern:

```text
major.minor.patch
```

Examples:

```text
0.8.1 patch bug fix
0.9.0 feature release
1.0.0 stable commercial baseline
```

### Patch release

Examples:

- bug fix
- small UI copy change
- CI fix
- security hardening without behavior expansion

Expected review:

- normal PR
- CI green
- changelog entry if user/customer visible

### Minor release

Examples:

- new feature
- new onboarding step
- new product mode
- new tenant capability
- new deployment option

Expected review:

- PR
- CI/release gates
- staging validation
- changelog
- operator approval for production

### Major release

Examples:

- breaking API change
- memory schema migration
- governance model change
- billing model change
- public UX restructuring
- deployment architecture change

Expected review:

- design contract
- migration plan
- rollback plan
- staging validation
- customer/admin communication
- explicit operator approval

## Update classes

### Green updates

Low-risk updates that may be applied to hosted staging automatically after merge.

Examples:

- docs-only changes
- safe copy corrections
- test/CI additions
- non-public internal comments

Hosted production may still require manual approval if user-visible.

### Yellow updates

Require staging validation and operator approval.

Examples:

- UI behavior changes
- onboarding changes
- pricing page changes
- public copy changes
- API route changes
- new feature flags
- new dependency groups

### Red updates

Require explicit review, migration planning, and rollback.

Examples:

- memory schema changes
- identity/tenant access control changes
- billing enforcement
- deployment scripts
- security/auth changes
- operator permissions
- self-improvement/governance behavior
- data deletion/export behavior

## Hosted update policy

For hosted WESLR:

```text
merge to master does not automatically mean production deploy
```

Production deploy requires:

1. master commit selected
2. CI/release gates green
3. staging deployed
4. staging smoke test passed
5. rollback path confirmed
6. operator approval
7. production deploy
8. production smoke check
9. release note recorded

## Self-hosted update policy

For self-hosted customers:

Updates should be presented as:

```text
WESLR version X.Y.Z is available.
Review changelog.
Backup current data/configuration.
Apply update when ready.
Verify health checks.
Rollback if needed.
```

Institutional deployments may choose delayed update windows.

No self-hosted deployment should be forced to update silently.

## Changelog requirements

Every release that affects hosted or self-hosted users should include:

- version
- release date
- commit hash
- affected surfaces
- new features
- fixed bugs
- security changes
- breaking changes
- migration notes
- rollback notes

## Migration rules

Any migration touching memory, identity, tenants, billing, governance, or deployment config must include:

- pre-migration backup step
- dry-run or validation step where possible
- explicit migration script or documented procedure
- post-migration validation
- rollback notes

## Rollback rules

Every production deploy must answer:

```text
How do we return to the previous known-good version?
What data/config changes would remain after rollback?
Is rollback safe if a migration already ran?
```

If rollback is not clean, deployment requires extra operator approval and clear communication.

## Customer communication rules

Hosted users should be informed of major user-visible changes through release notes or in-app notices.

Self-hosted/institutional admins should receive clear update notes before applying:

- what changed
- whether update is recommended or required
- whether downtime is expected
- whether migration is required
- whether security-related changes are included

## Website/docs role

`weslr.de` should include:

- changelog/release notes
- supported versions
- installation/update docs
- hosted vs self-hosted explanation
- support contact

Do not publish unsupported update promises.

## V1 decisions

```text
1. Master is source of truth, not automatic production.
2. staging.weslr.de validates before hosted production.
3. hosted production deploy requires operator approval.
4. self-hosted updates are versioned and admin-controlled.
5. high-impact changes require migration and rollback planning.
6. no silent updates for institutional/private deployments.
```

## V1 verdict

```text
WESLR_UPDATE_AND_RELEASE_PROPAGATION_V1_DEFINED
```

Next recommended contracts:

1. Account / tenant / data ownership model.
2. Product mode matrix.
3. Then `weslr-ui` public demo hardening.
