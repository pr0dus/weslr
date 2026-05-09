# WESLR Product Mode Matrix V1

Date: 2026-05-09
Status: product/UX/runtime contract — no implementation changes
Scope: public demo, hosted trial, paid hosted, team, private institution, staging, operator/dev modes

## Purpose

This document defines what WESLR features are visible or allowed in each product mode.

The goal is to prevent the UI from accidentally exposing file upload, memory writes, operator controls, deployment controls, billing features, API keys, or governance internals in the wrong environment.

## Core principle

Every WESLR UI surface must know its current product mode before showing features.

```text
Mode determines visible capabilities.
Backend enforcement remains mandatory.
Frontend flags are convenience and UX only, not security boundaries.
```

## Canonical modes

V1 modes:

```text
public_demo_readonly
hosted_trial
hosted_paid_individual
hosted_team
private_institution
self_hosted_admin
operator_dev
staging
```

## Feature columns

This matrix tracks whether each mode allows:

- chat
- onboarding
- persistent memory
- file upload
- operator panel
- proposal review
- execution/deployment controls
- LLM/provider usage
- API key workflows
- billing/subscription UI
- organization/team admin
- public visibility

## Mode matrix

| Mode | Chat | Onboarding | Memory writes | File upload | Operator panel | Proposal review | Execution/deploy controls | LLM/provider | API key workflows | Billing UI | Org/admin | Public route |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| public_demo_readonly | limited | no | no | no | no | no | no | no by default | no | no | no | yes |
| hosted_trial | yes | required | limited/confirmed | limited later | no | no | no | guarded | no user keys | trial status only | no/team later | yes |
| hosted_paid_individual | yes | required | yes/confirmed | controlled | no | user-safe proposals only | no | guarded | server-side only | yes | no | yes |
| hosted_team | yes | required | scoped | controlled | no | admin/team-safe later | no | guarded | server-side only | yes | yes | yes |
| private_institution | yes | required | scoped by tenant | controlled by policy | admin/operator only | yes if authorized | admin/operator only | deployment policy | customer/server-side | contract/admin | yes | no/public optional |
| self_hosted_admin | yes | required | scoped by tenant | controlled by policy | yes | yes | yes with safeguards | customer policy | customer-owned | license/support | yes | no |
| operator_dev | yes | optional | yes | yes | yes | yes | yes | yes | dev/operator only | no/optional | yes | no |
| staging | yes | as-needed | test only | test only | restricted | restricted | restricted | guarded/test | staging secrets only | no real billing | test/admin | private |

## Mode definitions

### public_demo_readonly

Purpose:

- public first contact
- safe explanation/demo
- no account required

Allowed:

- read-only chat routes
- WESLR explanation
- hosted/private deployment explanation
- safe status/demo prompts

Blocked:

- file upload
- memory writes
- operator panel
- proposal review
- deployment controls
- API key workflows
- billing actions
- private data handling

Required UI:

- read-only banner
- limitations footer
- safe example prompts
- no upload button
- no operator panel

### hosted_trial

Purpose:

- trial for individual users
- evaluate WESLR before paid subscription

Allowed:

- onboarding
- chat
- limited/confirmed memory
- trial status display
- basic workspace features

Blocked initially:

- operator panel
- deployment controls
- user-provided API keys
- organization admin unless team trial exists

Required UI:

- trial status
- days remaining later
- memory consent prompts
- upgrade path to paid

### hosted_paid_individual

Purpose:

- paid individual hosted use

Allowed:

- chat
- personal/project workspace
- confirmed memory
- controlled file handling after audit
- billing/subscription view

Blocked:

- operator internals
- deployment controls
- institution admin
- raw self-improvement queue

Required UI:

- personal scope badge
- memory scope badge
- subscription/account settings

### hosted_team

Purpose:

- hosted team use

Allowed:

- team onboarding
- shared workspaces
- role-based memory scopes
- team/admin management
- billing/admin view

Blocked:

- operator internals by default
- deployment controls
- unrestricted access to all memories

Required UI:

- tenant/team badge
- role badge
- workspace switcher
- admin settings for authorized users

### private_institution

Purpose:

- institution/company/lab/private deployment

Allowed:

- tenant-scoped chat
- organization/institution memory
- private documents according to policy
- admin/operator functions for authorized users
- deployment-specific settings if implemented

Blocked:

- public demo assumptions
- WESLR-hosted billing checkout by default
- unsupported update automation

Required UI:

- private deployment badge
- tenant name/scope
- role and permission visibility
- support/contact path

### self_hosted_admin

Purpose:

- local institutional/customer admin
- deployment owner/operator

Allowed:

- tenant admin
- user management
- deployment status
- update/changelog review
- backup/rollback guidance later
- local secret/config management later

Blocked:

- silent remote updates
- uncontrolled public exposure
- unsupported auto-migrations

Required UI:

- self-hosted badge
- update status
- deployment health
- admin warnings

### operator_dev

Purpose:

- trusted WESLR development/operator use

Allowed:

- broad internal surfaces
- proposal review
- diagnostics
- operator panel
- development tools

Blocked:

- public anonymous access

Required UI:

- clear operator/dev badge
- environment warning
- no confusion with public mode

### staging

Purpose:

- validation before production

Allowed:

- test chat
- test UI
- staging-only settings
- restricted operator/admin review

Blocked:

- real billing
- public claims of production readiness
- uncontrolled production secrets

Required UI:

- staging badge
- test-data warning
- environment indicator

## Frontend feature flags

Suggested frontend config shape:

```typescript
productMode: 'public_demo_readonly',
features: {
  chat: true,
  onboarding: false,
  memoryWrites: false,
  fileUpload: false,
  operatorPanel: false,
  proposalReview: false,
  deploymentControls: false,
  billing: false,
  organizationAdmin: false,
  showReadOnlyBanner: true,
  showLimitationsFooter: true,
  showExamplePrompts: true,
}
```

Important:

```text
Frontend flags do not provide security.
Backend must enforce the same restrictions.
```

## First UI patch mode target

The first coding PR should target only:

```text
public_demo_readonly
```

It should not implement paid user mode, onboarding, billing, tenant admin, private deployment UI, or operator functionality.

Required first patch:

- set public demo defaults
- hide operator panel
- hide/disable file upload
- show read-only demo banner
- show example prompts
- show limitations footer
- sanitize public errors

## Product mode badges

Required badges by mode:

| Mode | Badge |
|---|---|
| public_demo_readonly | Read-only demo |
| hosted_trial | Trial |
| hosted_paid_individual | Personal workspace |
| hosted_team | Team workspace |
| private_institution | Private deployment |
| self_hosted_admin | Self-hosted admin |
| operator_dev | Operator/dev |
| staging | Staging |

## Backend enforcement requirements

Eventually the backend must expose or enforce mode via a trusted server-side source.

The frontend may read mode from config or API, but users must not be able to elevate mode through browser manipulation.

Backend must block:

- write handlers in public demo
- memory writes without authorization
- file upload when disabled
- operator review endpoints without authority
- deployment controls without operator/admin role
- API key workflows in public/unauthorized contexts

## Public demo invariant

For `public_demo_readonly`, this invariant must hold:

```text
No user-visible action can write memory, upload files, expose operator internals, execute commands, mutate state, access secrets, or trigger deployment.
```

## V1 decisions

```text
1. Product mode controls visible UX.
2. Backend enforcement is still mandatory.
3. First coding patch targets public_demo_readonly only.
4. Paid/tenant/onboarding/billing/private deployment UI comes later.
5. Operator panel must not be visible in public demo.
6. File upload must not be available in public demo.
```

## V1 verdict

```text
WESLR_PRODUCT_MODE_MATRIX_V1_DEFINED
```

After this document is merged, the next safe step is:

```text
WESLR: harden weslr-ui public demo shell
```
