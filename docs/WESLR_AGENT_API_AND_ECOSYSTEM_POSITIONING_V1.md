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

## Context and token efficiency

A major practical advantage of connecting agents to WESLR is more efficient context use.

Many model agents spend large amounts of context window and tokens repeatedly reconstructing:

- project background
- prior decisions
- file state
- user preferences
- unresolved tasks
- evidence history
- safety/governance constraints
- what has already been tried

WESLR should reduce that repeated context burden by providing compact, structured, governed context packets instead of requiring every connected agent to rediscover or re-read everything on every session.

Preferred public wording:

```text
WESLR can help connected agents use context more efficiently by supplying structured project memory, evidence, and governance state instead of repeatedly rebuilding context from scratch.
```

Technical wording:

```text
WESLR can act as a compact context provider for compatible agents: retrieving only the relevant tenant, workspace, memory, evidence, and approval state needed for a task.
```

Important limitation:

```text
WESLR may reduce unnecessary context and token use in many workflows, but token savings depend on the connected agent, model, task, integration design, and how much context is actually needed.
```

Do not overclaim:

```text
WESLR always uses fewer tokens.
WESLR guarantees lower model costs.
WESLR makes every agent cheaper automatically.
```

Use:

```text
WESLR is designed to reduce repeated context rebuilding and improve context efficiency for compatible agents.
```

## Context efficiency validation plan

This theory must be tested before WESLR makes strong public or sales claims about token savings.

Hypothesis:

```text
For long-running tasks, connected agents using WESLR compact context packets will require fewer repeated prompt/context tokens than agents that repeatedly reconstruct project state from raw conversation, files, or prior logs.
```

Null hypothesis:

```text
WESLR does not reduce total context/token use, or any reduction is too small or inconsistent to claim.
```

### What to measure

For each benchmark task, measure both baseline and WESLR-assisted runs:

- input tokens
- output tokens
- total tokens
- number of turns
- wall-clock time
- task success
- number of repeated context explanations
- number of forgotten constraints
- number of corrections needed
- quality of final result

### Baseline condition

The agent receives context in the normal way:

- raw conversation history
- copied summaries
- file snippets
- manual operator explanations
- repeated prompts across sessions

### WESLR-assisted condition

The agent receives a compact WESLR context packet containing only relevant:

- project state
- memory summary
- active constraints
- unresolved tasks
- prior decisions
- relevant evidence
- governance rules
- current task objective

### Benchmark task families

Use several realistic long-running workflows:

1. coding continuation after context reset
2. research/literature synthesis continuation
3. product/UX planning continuation
4. deployment/debugging continuation
5. industrial/TIA project continuation
6. Scatti/materials validation continuation

### Minimum acceptance criteria

Do not claim token savings publicly unless tests show:

- lower total input/context tokens in WESLR-assisted runs
- equal or better task success
- fewer repeated explanations or corrections
- no hidden loss of important context
- results repeat across multiple task families

### Reporting rule

Allowed after validation:

```text
In our benchmark tasks, WESLR-assisted context reduced repeated context rebuilding while preserving task quality.
```

Only if measured:

```text
In tested workflows, WESLR-assisted agents used X% fewer input/context tokens on average.
```

Not allowed without broad proof:

```text
WESLR always reduces token costs.
WESLR guarantees lower bills.
WESLR makes all agents more efficient.
```

## Relationship to Claude, ChatGPT, Hermes, OpenClaw, and other agents

Public positioning should be careful:

- Claude, ChatGPT, Hermes, OpenClaw, coding agents, research agents, and internal automation systems may be powerful reasoning or action systems.
- WESLR should not claim to replace all of them.
- WESLR can provide the surrounding continuity/governance layer those systems often lack.
- WESLR can also help connected agents avoid repeatedly consuming large context windows to rediscover already-known project state.

Preferred wording:

```text
WESLR can work alongside compatible AI agents and tools by providing governed memory, project context, evidence, approval-aware workflows, and compact task-specific context.
```

Acceptable examples for technical/institutional pages:

```text
Model assistants such as Claude or ChatGPT can generate responses. Agent systems such as OpenClaw or Hermes can operate tools. WESLR is designed to preserve context, memory, evidence, governance, and compact task state around that work.
```

Avoid overclaiming:

```text
WESLR is better than Claude.
WESLR replaces all agents.
WESLR can control any agent automatically.
WESLR makes any agent safe.
WESLR guarantees lower token cost for every agent.
```

## Website section proposal

Section title:

```text
Use WESLR directly — or connect it to your agents.
```

Public copy:

```text
WESLR can be used as a standalone reasoning workspace, privately deployed inside an organization, or connected to compatible AI agents and automation tools. Instead of replacing every assistant, WESLR provides the continuity, memory, evidence, governance, and compact context layer those systems usually lack.
```

Shorter copy:

```text
Bring continuity, governance, and compact context to your agents.
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
- compact task context packet
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
- context efficiency can reduce repeated model work across long-running institutional projects when validated

### Self-hosted admin/operator

May configure agent integrations later, subject to deployment policy.

## Difference matrix

| System type | Primary role | What WESLR adds |
|---|---|---|
| Chat assistant | answers questions | long-term continuity, scoped memory, evidence, governance, compact context |
| Coding agent | edits/runs code | project memory, approval gates, release discipline, traceability, reduced context rebuilding |
| Research agent | gathers/summarizes evidence | provenance, memory consolidation, confidence boundaries, evidence packets |
| Automation agent | performs actions | operator approval, audit trail, policy enforcement, scoped task state |
| Enterprise agent platform | orchestrates workflows | tenant-aware continuity and governance model |

## Public copy examples

### Simple

```text
WESLR is not just another assistant. It is the continuity and governance layer that can help people and compatible agents work across long-running projects.
```

### Context efficiency

```text
WESLR helps compatible agents avoid rebuilding the same context repeatedly by providing structured memory, evidence, and task state when needed.
```

### Institutional

```text
For organizations, WESLR can be deployed privately and connected to approved internal agents or tools so they operate with scoped memory, evidence, permissions, compact context, and audit trails.
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
Guaranteed token savings
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
4. WESLR's distinction is continuity, governed memory, evidence, proposals, roles, approval-aware workflows, and compact context delivery.
5. Agent/API integrations are primarily an institutional/private deployment feature until implemented and productized.
6. No public API availability should be claimed before implementation.
7. WESLR may improve context/token efficiency by reducing repeated context rebuilding, but should not guarantee universal token savings.
8. Context/token efficiency must be benchmarked before strong public or sales claims are made.
```

## V1 verdict

```text
WESLR_AGENT_API_AND_ECOSYSTEM_POSITIONING_V1_DEFINED
```
