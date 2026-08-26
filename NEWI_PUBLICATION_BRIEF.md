# NEWI Public Research Publication Brief

## Purpose

This branch is the public-publication lane for NEWI material on Weslr. It is intentionally separate from the private NEWI research/development issue chain.

Current branch: `research/newi-kernel0-publication-v1`
Base: exact deployed Weslr public-site commit `090e98ad94e923d132aed0a79a1e6a9db7312b7f`.

## Privacy boundary

The NEWI repository is private.

Do not expose:
- private repository URLs
- private issue URLs or issue numbers unless separately approved
- source code
- internal branch names, commit SHAs, tree SHAs, hashes, filesystem paths, credentials, tokens, infrastructure details, or evaluator internals
- implementation details not necessary for the public scientific explanation

Do not claim evidence you have not been explicitly given.

## Current publication objective

Prepare a minimal, credible public research section at:

`/research/newi/`

The publication should explain:
1. the NEWI research objective
2. the developmental and falsification methodology
3. Kernel 0 as the current internal research target
4. the strongest demonstrated result so far (K1A) with strict claim limits
5. K2B as an active unresolved investigation, not a demonstrated capability
6. selected negative/falsification results in public-safe language

This is not a launch announcement, not an AGI claim, and not a finished academic paper.

## Scientific language

Use standard scientific wording in public prose.

Internal shorthand may be translated as:
- GREEN = predefined experimental criterion satisfied
- RED = predefined experimental criterion not satisfied
- gate = predefined evaluation stage/criterion
- claim ceiling = maximum warranted scope of a result

If RED/GREEN appears publicly, define it once and do not use it as if it were established scientific terminology.

## K1A public-safe claim

Safe characterization:

> NEWI acquired from prior anonymous experience a reusable temporal/structural continuation regularity and used the acquired regularity prospectively on previously unseen anonymous situations before observing their futures.

Do not inflate this into claims of general intelligence, general world modeling, object permanence, causal reasoning, consciousness, autonomous science, or human-level cognition.

## K2B public status

K2B is NOT demonstrated.

The active question is whether heterogeneous unlabeled prior experience can produce more than one genuinely distinct predictive content with corresponding distinct behavior on fresh anonymous situations.

A recent diagnostic showed that multiple retained model objects can still reduce to one observed functional predictive behavior. Later heterogeneous experience generated additional qualified structural candidates, but current evidence does not yet distinguish whether functional diversity fails to qualify or qualifies and is lost before authoritative retention under bounded frontier updating.

Public status: criterion not satisfied / unresolved; further diagnostic evidence required.

## Kernel 0

`Kernel 0` is NEWI's internal name for the current foundational research target. It is not established scientific terminology.

Public working definition:

> Kernel 0 is the minimum continuous developmental chain NEWI aims to demonstrate before making broader architectural claims.

Do not state that Kernel 0 has been achieved.

## Weslr implementation constraints

The public site is static HTML/CSS/JS served from `site/`.

Target path for the eventual page:

`site/research/newi/index.html`

No nginx change is required merely to add this static route.

Do not touch nginx, ports, chat services, e-qubs, PlantDelux, Ollama proxying, or unrelated Weslr routes for this publication task.

## Git safety

The current host checkout has local divergence and untracked files. Do not use it as the publication work surface by checking out this branch in place.

Use a separate clean Git worktree or a fresh clone for this branch, based on the remote branch `research/newi-kernel0-publication-v1`.

Do not delete, clean, stash, overwrite, or otherwise alter the existing Weslr working tree or its untracked files.

## Staging-first workflow

Do not publish directly to production.

1. Work only on the dedicated publication branch in a clean worktree/clone.
2. Build the NEWI page and any necessary navigation changes there.
3. Prepare a reviewable staging copy without altering production.
4. Report exact changed files and provide the rendered/public text for owner review.
5. Stop for owner approval.
6. Only after explicit approval may the approved files be promoted to the live `site/` tree.

## Immediate task for Nova

Read this file from GitHub and then do the following:

- create or use a separate clean worktree for `research/newi-kernel0-publication-v1`
- do NOT modify the existing `/home/pr0/projects/weslr-v1-ui-website` working tree
- inspect the existing site's visual/navigation conventions from the clean publication worktree
- draft the first `/research/newi/` page and only the minimum navigation changes required to reach it
- keep all content public-safe and scientifically conservative
- do not deploy to production
- do not modify nginx or services
- do not merge
- return the changed-file list, local commit SHA if committed, and a concise description of the page for owner review

Stop after preparing the review candidate.