# WESLR Agent API + Ecosystem Positioning V1

Date: 2026-05-09
Status: product/website/API positioning contract — no implementation changes
Scope: how WESLR is positioned alongside Claude, Hermes, OpenClaw, custom agents, and other AI/automation tools

## Purpose

This document defines how WESLR should be explained publicly when discussing other agents and AI systems.

WESLR should not be presented only as another chatbot or model. WESLR should be positioned as a continuity, memory, evidence, governance, and workflow layer that can be used directly by humans or connected to compatible agents and tools.

## Public rule: avoid internal shorthand

Public website copy must not rely on internal acronyms or private project names that normal users do not understand.

Avoid public wording like:

```text
OCC/OCW workflows
```

Use public wording like:

```text
compatible AI agents and automation tools
```

or:

```text
external assistants, coding agents, research agents, and institutional automation systems
```

## Three public access paths

WESLR should be explained as usable in three ways:

```text
1. Use WESLR directly.
2. Deploy WESLR privately.
3. Connect other agents and tools to WESLR.
```

### 1. Use WESLR directly

For normal users and professionals.

```text
Use WESLR as a hosted reasoning workspace with chat, continuity, governed memory, and project context.
```

### 2. Deploy WESLR privately

For institutions, companies, universities, laboratories, and privacy-sensitive teams.

```text
Run WESLR inside your own environment so your organization controls data location, access, runtime, updates, and integrations.
```

### 3. Connect other agents and tools to WESLR

For advanced customers and institutional/private deployments.

```text
Connect compatible agents and tools to WESLR so they can use governed memory, project context, evidence records, proposals, and operator-approved workflows.
```

## How WESLR differs from model agents

Most AI assistants and agents are primarily response/action engines.

Simplified model:

```text
input → reasoning/model/tool call → output
```

WESLR's intended role is different:

```text
user or agent input
  → tenant/workspace scope
  → continuity context
  → governed memory
  → evidence and provenance
  → proposal/action policy
  → operator/user approval if needed
  → traceable result
```

WESLR is therefore not only a model interface. It is the system that can hold continuity, policy, memory boundaries, evidence, and governed workflow around models and agents.

## Relationship to Claude, ChatGPT, Hermes, OpenClaw, and other agents

Public positioning should be careful:

- Claude, ChatGPT, Hermes, OpenClaw, coding agents, research agents, and internal automation systems may be powerful reasoning or action systems.
- WESLR should not claim to replace all of them.
- WESLR can provide the surrounding continuity/governance layer those systems often lack.

Preferred wording:

```text
WESLR can work alongside compatible AI agents and tools by providing governed memory, project context, evidence, and approval-aware workflows.
```

Acceptable examples for technical/institutional pages:

```text
Model assistants such as Claude or ChatGPT can generate responses. Agent systems such as OpenClaw or Hermes can operate tools. WESLR is designed to preserve context, memory, evidence, and governance around that work.
```

Avoid overclaiming:

```text
WESLR is better than Claude.
WESLR replaces all agents.
WESLR can control any agent automatically.
WESLR makes any agent safe.
```

## Website section proposal

Section title:

```text
Use WESLR directly — or connect it to your agents.
```

Public copy:

```text
WESLR can be used as a standalone reasoning workspace, privately deployed inside an organization, or connected to compatible AI agents and automation tools. Instead of replacing every assistant, WESLR provides the continuity, memory, evidence, and governance layer those systems usually lack.
```

Shorter copy:

```text
Bring continuity and governance to your agents.
```

CTA options:

```text
Start hosted trial
Request private deployment
Discuss agent/API integration
```

## Agent/API product direction

Future product name:

```text
WESLR Agent API
```

Alternative:

```text
WESLR Continuity API
```

Possible future API surfaces:

- tenant/workspace context lookup
- governed memory read
- governed memory write proposal
- evidence record creation
- source/provenance attachment
- proposal creation
- operator approval status
- task/workflow state
- audit trail query
- mode/capability discovery

## API governance rule

An agent API must not become an unrestricted memory-write or execution bypass.

All API access must respect:

- tenant scope
- workspace scope
- user/agent identity
- role permissions
- memory scope
- product mode
- governance policy
- audit requirements

## Agent identity

Connected agents must eventually have explicit identity.

Examples:

```text
agent_id
agent_type
provider/tool name
workspace scope
allowed actions
approval requirements
audit label
```

A connected agent should never inherit full operator authority by default.

## Integration tiers

### Public hosted user

Usually no direct agent API access in V1.

Public hosted use should focus on the WESLR chat workspace.

### Hosted paid professional

Possible future limited integrations:

- personal productivity agents
- developer tools
- document tools

Still requires safe scopes.

### Private / institutional deployment

Best fit for Agent/API integrations.

Reason:

- organization can control infrastructure
- organization can define agent permissions
- data remains within chosen environment
- integrations can be reviewed and governed

### Self-hosted admin/operator

May configure agent integrations later, subject to deployment policy.

## Difference matrix

| System type | Primary role | What WESLR adds |
|---|---|---|
| Chat assistant | answers questions | long-term continuity, scoped memory, evidence, governance |
| Coding agent | edits/runs code | project memory, approval gates, release discipline, traceability |
| Research agent | gathers/summarizes evidence | provenance, memory consolidation, confidence boundaries |
| Automation agent | performs actions | operator approval, audit trail, policy enforcement |
| Enterprise agent platform | orchestrates workflows | tenant-aware continuity and governance model |

## Public copy examples

### Simple

```text
WESLR is not just another assistant. It is the continuity and governance layer that can help people and compatible agents work across long-running projects.
```

### Institutional

```text
For organizations, WESLR can be deployed privately and connected to approved internal agents or tools so they operate with scoped memory, evidence, permissions, and audit trails.
```

### Developer/API

```text
Future WESLR APIs will expose context, memory, evidence, proposals, and approval state through governed, tenant-scoped interfaces.
```

## What not to expose yet

Do not promise immediate public API availability until implemented.

Avoid:

```text
Public Agent API available now
Connect any agent instantly
Unlimited integrations
Full autonomous orchestration
Safe control of any model or agent
```

Use:

```text
Agent/API integrations are planned for private and institutional deployments.
```

## Relationship to commercial model

The Agent/API layer is mainly for:

```text
private deployments
institutional customers
enterprise/lab/company environments
advanced hosted plans later
```

It should not be bundled into the first simple hosted individual plan by default.

Potential commercial treatment:

- included in institutional quote
- custom integration project
- paid add-on
- advanced/private deployment feature

## Relationship to website navigation

Public website can include:

```text
Product
Hosted
Private deployment
Agent/API
Docs
Pricing
Contact
```

If navigation must stay simple:

```text
Product
Hosted
Private
Agents
Docs
Contact
```

## Relationship to onboarding

Onboarding can later ask:

```text
Do you want to use WESLR directly or connect it to existing tools/agents?
```

Options:

```text
Use WESLR directly
Use WESLR with my team/institution
Connect WESLR to tools or agents
I am evaluating private deployment
```

## V1 decisions

```text
1. Public copy must avoid unexplained internal acronyms.
2. WESLR can be positioned as usable directly, privately deployed, or connected to other agents/tools.
3. Claude, Hermes, OpenClaw, and similar systems should be treated as examples of model/agent systems WESLR can complement, not replace.
4. WESLR's distinction is continuity, governed memory, evidence, proposals, roles, and approval-aware workflows.
5. Agent/API integrations are primarily an institutional/private deployment feature until implemented and productized.
6. No public API availability should be claimed before implementation.
```

## V1 verdict

```text
WESLR_AGENT_API_AND_ECOSYSTEM_POSITIONING_V1_DEFINED
```
