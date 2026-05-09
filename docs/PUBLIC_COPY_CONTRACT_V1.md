# WESLR Public Copy Contract V1

Date: 2026-05-09
Status: public/product copy contract — no frontend, billing, runtime, or deployment changes
Scope: website wording, hosted/self-hosted positioning, pricing copy, privacy copy, demo/onboarding text

## Purpose

This document defines the first canonical wording direction for WESLR's public website and chat surface.

It follows:

- `docs/PUBLIC_SURFACE_UX_AUDIT_V1.md`
- `docs/WESLR_UX_DOCTRINE_AND_ONBOARDING_V1.md`
- `docs/PUBLIC_SURFACE_INVENTORY_V1.md`
- `docs/WESLR_COMMERCIAL_DEPLOYMENT_AND_PRIVACY_V1.md`

The goal is to avoid vague, overclaimed, or confusing public language before UI implementation.

## Core public positioning

Canonical short description:

```text
WESLR is a continuity-first reasoning platform for long-running work, governed memory, evidence, proposals, and domain workflows.
```

Shorter variant:

```text
WESLR is a continuity-first workspace for reasoning, memory, and governed action.
```

Plain-language variant:

```text
WESLR helps people and organizations keep context across long-running work, organize evidence, and turn ideas into reviewed next steps.
```

## Hero section copy

Preferred hero headline:

```text
Continuity-first intelligence for long-running work.
```

Preferred hero subheadline:

```text
WESLR combines chat, memory, evidence, proposals, and governed workflows so people and organizations can reason across projects without losing context.
```

Primary CTAs:

```text
Start hosted trial
Request private deployment
```

Secondary CTAs:

```text
View docs
Explore WESLR
Contact us
```

## Hosted vs private deployment copy

### Hosted WESLR

Headline:

```text
Hosted WESLR
```

Description:

```text
Start quickly with WESLR running on hosted infrastructure. Use the hosted workspace for personal or professional continuity, project reasoning, and governed memory.
```

Pricing line:

```text
1 month free trial, then €80/month per user.
```

CTA:

```text
Start hosted trial
```

### Private / institutional WESLR

Headline:

```text
Private deployment
```

Description:

```text
For companies, laboratories, universities, and institutions that need control over data location, WESLR can be deployed inside your own environment.
```

Pricing line:

```text
Quote-based for institutions and private deployments.
```

CTA:

```text
Request a quote
```

## Privacy explanation for normal users

Use simple language:

```text
Hosted WESLR is the fastest way to start. Your messages are processed by WESLR's hosted service.
```

```text
Private deployment is for organizations that need WESLR to run inside their own infrastructure.
```

```text
If your work involves sensitive documents, internal company data, laboratory data, or strict privacy rules, private deployment may be the better path.
```

Avoid technical jargon like tokens unless the page is specifically for technical users.

## Privacy explanation for technical/institutional users

```text
Private deployment allows your organization to control runtime, storage, network access, backups, access policy, and integration boundaries.
```

```text
WESLR can be evaluated for deployment on supported infrastructure such as Ubuntu servers, Docker-based Linux environments, or Proxmox-hosted Ubuntu VMs.
```

Do not claim support for every environment until validated.

## Pricing copy

Canonical individual pricing copy:

```text
Start with a 1-month free trial. Continue for €80/month per user.
```

Canonical institutional pricing copy:

```text
Private and institutional deployments are quote-based.
```

Pricing page structure:

| Plan | Copy |
|---|---|
| Hosted Individual | 1 month free trial, then €80/month per user |
| Hosted Team | Contact us / planned team pricing |
| Private / Institutional | Quote-based deployment and support |

Do not publish fake exact enterprise numbers until support and deployment scope are understood.

## Product track copy

### Core WESLR

```text
A continuity-first reasoning workspace for memory, context, evidence, proposals, and governed workflows.
```

### Industrial / TIA track

```text
A track for industrial engineering workflows, Siemens/TIA data normalization, and long-running automation project context.
```

### Scatti / materials track

```text
A research-support track for computational materials candidates, screening workflows, and evidence-backed validation planning.
```

Required limitation:

```text
Materials outputs are screening and research-support artifacts, not final scientific proof.
```

### Deployment Forge

```text
A controlled path for staging, validating, and deploying WESLR environments.
```

## Public demo copy

Read-only banner:

```text
Read-only WESLR demo
```

Banner subtitle:

```text
This demo can explain WESLR and show selected safe workflows. It does not write memory, execute actions, or expose operator controls.
```

Status badges:

```text
Read-only
No memory writes
No execution
Operator-reviewed changes
Experimental
```

Limitations footer:

```text
This public demo is limited. Real memory, private deployment, team workflows, file handling, and operator features require onboarding or a private deployment agreement.
```

## Onboarding copy

Opening line:

```text
Set up WESLR around how you work.
```

Short explanation:

```text
Before WESLR can keep useful continuity, it needs to know whether you are working as an individual, a project owner, a team, or an organization.
```

Mode question:

```text
How will you use WESLR?
```

Options:

```text
Individual
Project
Company
Institution / laboratory / university
Operator / developer
```

Memory question:

```text
What may WESLR remember?
```

Options:

```text
Nothing yet
Only this project context
My preferences and working style
Organization or team context
Uploaded documents after review
```

Governance explanation:

```text
Important memory and system-changing actions require review. WESLR does not silently change its core behavior.
```

## First chat copy

First message for public demo:

```text
This is a read-only WESLR demo. You can ask what WESLR is, how governed memory works, or why private deployment matters.
```

First message after onboarding:

```text
Your WESLR workspace is ready. I can help organize context, compare evidence, preserve project continuity, or propose reviewed next steps.
```

Example prompts:

```text
What is WESLR?
Why is WESLR different from normal chat?
How does governed memory work?
What is the difference between hosted and private WESLR?
What can the public demo do?
What requires onboarding?
```

## Fallback and error copy

Public fallback:

```text
This public demo only supports selected read-only WESLR routes. I can explain WESLR, describe hosted or private deployment, or show safe status information.
```

Hosted/private clarification:

```text
For sensitive data or institutional use, request private deployment so WESLR can run inside your organization's environment.
```

Generic safe error:

```text
Something went wrong while processing this request. No action was executed. Please try again or contact support.
```

Do not show:

- stack traces
- internal file paths
- secrets
- handler names
- raw provider errors
- internal governance objects

## Claims allowed

Allowed public claims:

```text
continuity-first
governed memory
traceable state
operator-reviewed changes
hosted or private deployment
project and institution context
screening support for research workflows
read-only public demo
```

## Claims forbidden

Do not claim:

```text
AGI
ASI
conscious AI
sentient AI
unhackable
fully secure
free forever
unlimited usage
replaces experts
automatically self-improves without review
scientific proof from screening workflows
install anywhere instantly
```

## Support/wiki/docs copy

Docs entry copy:

```text
Learn how WESLR works, how hosted and private deployments differ, and what is currently supported.
```

Support copy:

```text
Need help choosing between hosted and private WESLR? Contact us with your organization type, expected users, and deployment requirements.
```

## Institutional quote form copy

Intro:

```text
Tell us what kind of private WESLR deployment you need. Do not include sensitive documents or confidential data in this form.
```

Fields:

```text
Organization name
Contact person
Email
Country
Organization type
Expected users
Preferred deployment mode
Target environment
Required integrations
Desired timeline
Support expectations
```

Submit button:

```text
Request quote
```

## Legal/commercial caveat

Before accepting paid customers, WESLR needs review for:

- terms of service
- privacy policy
- refund/cancellation policy
- trial rules
- invoicing and VAT handling
- data processing terms for institutions
- support scope

This copy contract does not implement billing or legal terms.

## V1 verdict

```text
PUBLIC_COPY_CONTRACT_V1_DEFINED
```

This document should be used before coding landing-page copy, public-demo copy, onboarding text, pricing cards, and institutional/private deployment CTAs.
