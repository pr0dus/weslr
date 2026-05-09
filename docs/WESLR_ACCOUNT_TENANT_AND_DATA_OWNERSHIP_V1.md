# WESLR Account, Tenant + Data Ownership Contract V1

Date: 2026-05-09
Status: product/data-governance contract — no runtime/account implementation
Scope: accounts, tenants, organizations, roles, memory/data ownership, exports, deletion, user departure, onboarding implications

## Purpose

This document defines the ownership and authority model that WESLR should follow before implementing onboarding, hosted accounts, private deployments, team workspaces, or institutional users.

The goal is to avoid later ambiguity around who owns memory, who can invite users, who can export/delete data, and who can approve system-changing actions.

## Core principle

WESLR must distinguish:

```text
person identity
account access
workspace membership
tenant ownership
memory scope
role authority
data ownership
operator authority
```

A person using WESLR does not automatically own every memory they can see. A company/institution tenant does not automatically own a person's private memory unless the memory was created inside the tenant scope under agreed terms.

## Core entities

### Person

A human user.

Examples:

- individual user
- researcher
- engineer
- operator
- company employee
- lab member

### Account

The login/access identity used to access WESLR.

A person may have one or more accounts over time, but account duplication should be minimized.

### Tenant

A data/control boundary.

Examples:

- individual tenant
- company tenant
- university tenant
- lab tenant
- team tenant
- private self-hosted deployment tenant

### Workspace

A working context inside a tenant.

Examples:

- project workspace
- research workspace
- industrial/TIA workspace
- Scatti/materials workspace
- deployment workspace

### Memory scope

The boundary for stored WESLR memory.

Examples:

- personal memory
- project memory
- company memory
- institution/lab memory
- team memory
- deployment memory

### Operator

A trusted role allowed to review governance, deployment, release, system-changing, or high-risk actions.

Operator is not the same as normal admin.

## Tenant types

### Individual tenant

Owned/controlled by one user.

Use cases:

- personal continuity
- independent research
- personal project memory

Default owner:

```text
individual user
```

### Team tenant

Owned/controlled by a group or team admin.

Use cases:

- small team project memory
- shared work context

Default owner:

```text
team owner/admin
```

### Company tenant

Owned/controlled by an organization.

Use cases:

- industrial workflows
- company project memory
- internal documents/context

Default owner:

```text
company / authorized admin
```

### Institution / lab / university tenant

Owned/controlled by an institution or authorized unit.

Use cases:

- research workflows
- laboratory context
- university/private data

Default owner:

```text
institution / authorized admin
```

### Hosted WESLR tenant

Runs on WESLR-hosted infrastructure.

Data is governed by hosted terms, privacy policy, and user/tenant settings.

### Self-hosted WESLR tenant

Runs inside customer-controlled infrastructure.

Customer/institution controls runtime, storage, access policy, backups, update timing, and local admin roles.

## Role model

Minimum future roles:

| Role | Meaning |
|---|---|
| Owner | controls tenant/workspace billing, admins, export/deletion policy |
| Admin | manages users, workspace settings, permissions |
| Operator | approves high-impact WESLR actions and deployment/governance operations |
| Member | normal workspace participant |
| Viewer | read-only participant |
| External collaborator | limited scoped access |
| Support | temporary support access, explicitly granted and audited |

## Authority separation

Owner/admin/operator are different powers.

An admin may manage users but should not automatically approve WESLR self-modification, deployment, or governance changes.

An operator may review high-impact WESLR actions but should not automatically own business billing or legal account ownership.

## Memory ownership rules

### Personal memory

Owned by the individual user unless explicitly moved/shared.

Examples:

- user preferences
- personal working style
- personal context

Default export/delete authority:

```text
individual user
```

### Project memory

Owned by the project workspace/tenant owner, with contributor access according to role.

Examples:

- project goals
- decisions
- tasks
- evidence summaries

Default export/delete authority:

```text
workspace owner/admin, subject to policy
```

### Company/institution memory

Owned by the organization tenant.

Examples:

- company docs
- lab documents
- industrial project context
- organization knowledge

Default export/delete authority:

```text
authorized tenant owner/admin
```

### Operator memory

Internal WESLR/operator governance memory.

Examples:

- release notes
- governance decisions
- system improvement proposals
- deployment approvals

Default access:

```text
operator-only
```

Should not be exposed to public users.

## Data access rules

A user can access data only if:

1. they are authenticated,
2. they belong to the tenant/workspace,
3. their role allows the action,
4. the memory/data scope permits it,
5. no higher governance rule blocks it.

Membership alone is not enough for all access.

## Data export rules

Future export capability must distinguish:

- personal export
- workspace export
- tenant export
- admin export
- legal/compliance export

Default rule:

```text
users can export their personal data;
tenant owners/admins can export tenant/workspace data according to policy;
operator-only data is not exported to normal users.
```

Exports must avoid leaking another user's private personal memory unless tenant policy explicitly covers that data scope.

## Data deletion rules

Deletion must be careful because WESLR memory may be linked to proposals, audit trails, evidence, and governance records.

Future deletion should distinguish:

- delete personal profile data
- remove user from tenant
- delete personal memory
- delete project/workspace memory
- archive tenant
- purge tenant
- retain audit records required for security/compliance

Deletion requests must not silently corrupt shared memory, audit trails, or institutional records.

## User leaving an organization

When a user leaves an organization:

- access to organization tenant should be removed
- personal memory should remain with the person if separate
- organization memory remains with the organization
- shared contributions remain in project/tenant records unless policy says otherwise
- operator/admin should review exceptional cases

## Invitation model

Future institutions/teams should invite users through controlled invite flows.

Possible invite channels:

- email invite
- invite code
- admin-created account
- domain-based invitation later

Invite should define:

- tenant
- workspace
- role
- expiration
- inviter
- allowed scopes

## Onboarding implications

Onboarding must ask:

```text
Are you using WESLR as an individual, for a project, for a company, or for an institution?
```

For organization use, onboarding must establish:

- tenant name
- organization type
- user's role
- memory scope
- who owns the workspace
- whether data is hosted or self-hosted

## Hosted vs self-hosted data ownership

### Hosted

WESLR operates the infrastructure. Tenant/user data is stored in hosted systems according to terms and privacy policy.

### Self-hosted

Customer operates the infrastructure. Customer controls local storage, backups, admin access, and update timing.

WESLR may provide software/support, but customer environment ownership must be clear.

## Support access

Support access must be explicit and audited.

Support should not silently access tenant data.

Future support access should include:

- tenant approval
- time limit
- scope limit
- audit log
- revocation path

## Billing ownership

Billing owner may differ from workspace operator.

Example:

- company finance/admin owns billing
- technical operator manages deployment
- team lead manages workspace

Do not assume one role covers all authority.

## Governance approval rules

High-impact actions require appropriate authority.

Examples:

| Action | Approval needed |
|---|---|
| save personal memory | user consent / policy |
| save organization memory | role/policy-controlled |
| invite user | admin/owner |
| export tenant data | owner/admin |
| delete tenant | owner + confirmation |
| deploy/update self-hosted | deployment operator/admin |
| change governance behavior | operator |
| expose public endpoint | operator |
| modify core WESLR behavior | operator/governance approval |

## Product UX requirements

The UI must always make the current scope clear:

```text
Personal workspace
Project workspace
Company workspace
Institution workspace
Operator workspace
Read-only demo
```

The UI should show simple badges like:

```text
Personal memory
Organization memory
Read-only
Private deployment
Hosted workspace
Operator mode
```

## V1 decisions

```text
1. WESLR needs tenant-aware account ownership before serious onboarding.
2. Personal, project, company, institution, and operator memory are different scopes.
3. Membership does not grant universal access.
4. Owner, admin, operator, member, viewer, and support are separate roles.
5. Self-hosted tenants control their own infrastructure and update timing.
6. Support access must be explicit and audited.
7. UI must show active workspace/memory scope clearly.
```

## V1 verdict

```text
WESLR_ACCOUNT_TENANT_AND_DATA_OWNERSHIP_V1_DEFINED
```

Next recommended contract:

```text
docs/WESLR_PRODUCT_MODE_MATRIX_V1.md
```
