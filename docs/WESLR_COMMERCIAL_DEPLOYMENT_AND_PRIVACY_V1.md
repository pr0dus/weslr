# WESLR Commercial Deployment + Privacy Model V1

Date: 2026-05-09
Status: product/commercial contract — no runtime, billing, or deployment implementation
Scope: hosted WESLR, self-hosted/institutional WESLR, pricing direction, privacy positioning, website access model

## Purpose

This document defines WESLR's commercial access model and privacy/deployment positioning before website UX and pricing pages are implemented.

WESLR is not intended to be a free unlimited public service. It should be offered as a serious paid continuity-first intelligence platform with two official access paths:

1. Hosted WESLR
2. Self-hosted / institutional WESLR

The website must clearly explain both paths.

## Core commercial principle

WESLR may provide a trial, but long-term use is paid.

Baseline individual hosted offer:

```text
1 month free trial
then €80/month per user
```

Institutional/private deployments are not fixed-price public checkout products by default. They should be handled by quote.

```text
Institutional / private deployment: ask for quote
```

## Why paid from the start

WESLR is not only a chat interface. It is intended to provide:

- continuity across long-running work
- governed memory
- project/institution context
- proposal and review flows
- domain workflows
- deployment support
- privacy-oriented hosting options
- possible future self-hosted/institutional deployment

This creates infrastructure, support, compute, maintenance, and trust costs.

The website should not train users to expect WESLR as a free toy.

## Access paths

### Path A — Hosted WESLR

Public route:

```text
chat.weslr.de
```

Purpose:

- public/pilot user access
- individual paid users
- small teams
- WESLR-owned hosted product
- fast trial experience
- operator/test workflows

Default commercial model:

```text
1 month free trial
€80/month per user after trial
```

Hosted WESLR is convenient, but users must understand that data is processed on WESLR-controlled infrastructure.

### Path B — Self-hosted / institutional WESLR

Purpose:

- companies
- universities
- laboratories
- public institutions
- industrial automation teams
- research teams
- privacy-sensitive deployments

Commercial model:

```text
Price by quote
```

The institution asks for an offer based on:

- number of users
- deployment environment
- support expectations
- data sensitivity
- required integrations
- uptime requirements
- customization level
- training/onboarding needs

## Privacy positioning

Many users and institutions do not want sensitive data processed by an external hosted system.

WESLR should clearly explain:

```text
Hosted WESLR is easiest to start.
Self-hosted WESLR gives your organization control over where WESLR runs and where data is stored.
```

Do not overpromise absolute privacy or security.

Good wording:

```text
For sensitive environments, WESLR can be deployed inside your own infrastructure so your organization controls where documents, memory, and user data are stored.
```

Avoid:

```text
Your data is 100% safe.
Nobody can ever access your data.
Completely private forever.
```

## Token/data confusion UX

Some users misunderstand how AI services process data, tokens, memory, and hosted infrastructure.

Website language should avoid jargon where possible.

Simple explanation:

```text
In hosted mode, your messages are processed by WESLR's hosted service.
In self-hosted mode, WESLR runs inside your organization's environment.
```

For non-technical users:

```text
If your organization has strict privacy rules, choose self-hosted deployment.
```

For technical users:

```text
Self-hosted deployment allows your organization to control runtime, storage, network access, backups, and integration boundaries.
```

## Proposed pricing ladder

### Individual Hosted

```text
Free trial: 1 month
Then: €80/month per user
```

Intended for:

- individual professionals
- independent researchers
- serious builders/operators
- power users

Includes, conceptually:

- hosted WESLR chat workspace
- project continuity
- governed memory after onboarding/consent
- limited support/documentation
- standard hosted resource limits

### Team Hosted

Recommended future tier:

```text
€250–€500/month starting package
or €80/user/month with minimum seat count
```

This is not locked as public pricing yet.

Intended for:

- small teams
- small companies
- project groups

Possible features:

- shared project memory
- role-based access
- team onboarding
- shared files/context after governance
- admin controls

### Institution / Enterprise / Laboratory

Public pricing:

```text
Ask for quote
```

Intended for:

- universities
- research labs
- industrial organizations
- public institutions
- companies with privacy/security needs

Possible pricing basis:

- annual license
- deployment fee
- support contract
- per-seat or site license
- integration/customization fee
- training/onboarding package

### Self-hosted Professional / Private Server

Future possible tier:

```text
Ask for quote or annual license
```

Do not publish a simple low price until install/update/support burden is understood.

## Website CTAs

The public site should show two primary paths:

```text
Try Hosted WESLR
Install / Deploy WESLR Privately
```

Alternative wording:

```text
Start hosted trial
Request private deployment
```

Recommended CTAs:

- Start 1-month hosted trial
- Request institutional deployment
- View installation options
- Read privacy model
- Contact for quote

## Website navigation recommendation

First simple navigation:

```text
Product
Hosted
Self-hosted
Docs
Research
Contact
```

Or shorter:

```text
WESLR
Demo
Install
Docs
Pricing
Contact
```

## Installation path direction

WESLR should eventually support an official install path for major environments, but the first public install instructions must prioritize transparency and operator review.

Safer first public install path:

```text
1. Clone the WESLR repository.
2. Review the installation script.
3. Run the documented installer for the supported environment.
4. Verify service status and configuration.
```

Before publishing a one-command installer, WESLR needs:

- supported environment list
- dependency checks
- config generation
- secret handling
- backup path
- update path
- uninstall path
- service setup
- documentation
- support policy

## Supported environments

First supported targets should be conservative:

```text
Ubuntu 22.04 / 24.04 server
Docker on Linux
Proxmox VM running Ubuntu
```

Later targets:

```text
Windows 11 / WSL2
macOS
Kubernetes
air-gapped institutional install
managed customer deployment
```

Do not claim install-anywhere support until verified.

## Hosted vs self-hosted feature messaging

| Feature | Hosted WESLR | Self-hosted / institutional WESLR |
|---|---|---|
| Setup speed | fastest | requires deployment |
| Data location | WESLR-controlled infrastructure | customer's infrastructure |
| Privacy control | standard hosted controls | organization-controlled |
| Updates | WESLR-managed | controlled by deployment policy |
| Support | standard/premium later | contract/support agreement |
| Customization | limited | higher |
| Integrations | standard | project-specific |
| Pricing | public per-user | quote |

## Public wording for pricing

Good:

```text
Start with a 1-month hosted trial. Continue for €80/month per user.
```

```text
For institutions, laboratories, universities, and companies that need private deployment, contact us for a quote.
```

```text
Self-hosted WESLR is designed for organizations that need control over data location, access, and infrastructure.
```

Avoid:

```text
Free forever
Unlimited usage
Enterprise-grade security without validation
Guaranteed privacy
Install anywhere instantly
```

## Billing implementation status

No billing implementation exists in this document.

Future billing implementation will need:

- account model
- trial start/end tracking
- seat count
- subscription status
- payment provider decision
- invoice/VAT handling
- cancellation flow
- grace period policy
- admin billing view
- terms/privacy/legal review

Do not add frontend pricing checkout until legal/billing basics are ready.

## Trial rules

V1 commercial assumption:

```text
trial duration: 1 month
trial price: €0
post-trial price: €80/month per user
```

Trial should require enough identity/contact information to prevent abuse, but implementation details are future work.

Possible future trial constraints:

- one trial per verified email/domain/payment method
- fair-use limits
- no public write/action features during early trial
- memory/export retention policy after trial ends
- clear cancellation path

## Institutional quote intake

Website should include an institutional request form.

Fields may include:

- organization name
- contact person
- email
- country
- organization type
- expected users
- preferred deployment mode
- target environment
- data sensitivity level
- required integrations
- desired timeline
- support expectations

Do not require sensitive details in the first contact form.

## Relationship to UX contracts

This document modifies the public UX direction:

The website should not only say:

```text
Try demo
```

It should say:

```text
Start hosted trial
or
Request private/self-hosted deployment
```

The first public UX coding patch should therefore include visible hosted/self-hosted positioning when appropriate.

## Relationship to API/security doctrine

External API keys, model provider keys, customer secrets, and institutional secrets must not be placed in public frontend code.

Secrets must remain:

- server-side
- environment/secret-manager backed
- never logged
- never committed
- scoped to deployment mode

Self-hosted deployments should make secret ownership explicit.

## V1 decisions

```text
Hosted WESLR: 1 month free trial, then €80/month per user.
Institutional/private/self-hosted WESLR: ask for quote.
Website must show both paths.
Self-hosting is a privacy/trust feature, not a free alternative.
Install command is future, not immediate public promise.
```

## V1 verdict

```text
WESLR_COMMERCIAL_DEPLOYMENT_AND_PRIVACY_MODEL_V1_DEFINED
```

Next recommended PRs:

1. Update UX doctrine/copy direction to include hosted/self-hosted split.
2. Create Public Copy Contract V1 with pricing and privacy wording.
3. Then harden `weslr-ui` public demo shell with correct hosted/self-hosted language.
