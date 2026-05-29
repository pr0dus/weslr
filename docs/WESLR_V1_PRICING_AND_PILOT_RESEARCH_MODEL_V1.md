# WESLR V1 Pricing and Pilot Research Model V1

Date: 2026-05-29
Status: design / documentation only
Grounding:
- `docs/WESLR_V1_PRICING_MARKET_AND_SCALABILITY_STRATEGY_DISCOVERY_V1.md`
- `docs/WESLR_V1_MASTER_DEFINITION_AND_WEBSITE_STRUCTURE_V1.md`
- `docs/WESLR_V1_NON_LLM_IDENTITY_AND_OPTIONAL_MODEL_BOUNDARY_V1.md`
- `docs/WESLR_V1_PRODUCT_UX_AND_OPERATING_MODEL_V1.md`
- `docs/WESLR_V1_UPDATE_METHOD_AND_IMPLEMENTATION_FREEZE_V1.md`

## 1. Pricing status

WESLR pricing is **not finalized**.

Also not finalized:
- exact storage limits
- exact upload limits
- final hosted plan shapes
- final support model
- final model/API pass-through model

Public website wording may say:
- “pilot access by invitation”

Final paid plans require scalability and cost review first.

## 2. First-50-user pilot purpose

The first-50-user pilot exists to learn:
- who WESLR is useful for
- real usage patterns
- support / operator burden
- storage / file needs
- optional model / API expectations
- willingness to pay

Pilot learning must avoid overclaiming reliability.

## 3. Pilot phases

### Phase 0 — website / waitlist only
- public explanation only
- pilot-interest capture only
- no public price
- no open signup
- no upload promise

### Phase 1 — 10 trusted users
- small controlled invite set
- basic usage observation
- conservative file/storage limits
- support logs only

### Phase 2 — 25 users
- broader but still controlled invite set
- compare use cases and load patterns
- compare support burden by user type
- observe storage growth

### Phase 3 — 50 users
- final invite-only discovery set
- enough data to compare value patterns
- enough data to estimate support and storage pressure
- enough data to shape pricing hypotheses

### Phase 4 — pricing decision review
- owner review of evidence
- scalability and cost review
- survey synthesis
- pricing hypothesis selection
- no automatic pricing finalization

## 4. Invite criteria

Invite people who are likely to produce meaningful evidence:
- technical users
- professional users
- industrial / domain contacts
- researchers / evaluators
- users with real continuity / file / workspace needs

Do **not** use random mass signups as the main pilot source.

## 5. Pilot limits

Conservative non-final limits:
- no public demo upload
- invited pilot only
- small upload quota
- small storage quota
- no unlimited files
- no production guarantee
- no official intelligence / reliability claims
- no live deletion / export claims unless implemented and approved

## 6. Model/API modes

Pricing research should compare these modes:
- no-model / governance-only mode
- user-supplied API/model mode
- WESLR-managed model mode later
- private / institutional deployment mode
- hybrid mode

Optional models are capability providers, not WESLR identity or authority.

## 7. Usage metrics to collect

Safe metrics to collect:
- active days
- messages per day
- projects created
- files uploaded
- total storage used
- failed / unsupported uploads
- feature requests
- support requests
- model / API usage if applicable
- user-reported value

Avoid raw private content collection unless separately approved.

## 8. Cost metrics to estimate

Estimate the following before final pricing:
- server cost
- storage cost
- backup cost
- optional model/provider cost
- file parsing / indexing cost
- support / operator time
- security / abuse handling
- legal / privacy overhead

## 9. Pilot survey

Max 15 questions:
1. What job would you pay WESLR to do?
2. Would you use WESLR personally, professionally, or both?
3. Would you pay today?
4. Is WESLR too cheap to trust?
5. Is the pilot good value?
6. Is it getting expensive?
7. Is it too expensive?
8. What monthly storage do you expect?
9. How many files do you expect to upload?
10. Would you bring your own API key?
11. Would you pay more for WESLR-managed model access?
12. Would you pay more for private deployment?
13. Would you pay more for stronger governance / continuity?
14. What would make WESLR clearly worth paying for?
15. What would make you stop using WESLR?

## 10. Pricing hypotheses

All of the following are **non-final**.

- Public website: no public price
- First 50 users: free limited pilot or symbolic **€10–€20/month**
- Personal/pro later: range only
- Professional continuity workspace later: range only
- Private / institutional / industrial: custom quote
- User-supplied API plan vs WESLR-managed model plan

## 11. Decision rules

Before final pricing, WESLR should have:
- at least 20–50 users observed
- usage / cost estimates available
- support burden known
- storage needs known
- willingness-to-pay survey complete
- owner review complete
- scalability review complete

## 12. Website wording

Safe wording:
- “Pilot access by invitation”
- “Pricing and plans are being evaluated with early users”
- “Storage and file-processing limits apply”
- “Models are optional capability providers; WESLR is the governed system”
- “Private / institutional deployments available by discussion”

Forbidden:
- fixed final public price unless separately approved
- unlimited upload
- production-ready
- benchmark-proven
- more reliable than competitors
- official Turing / intelligence claims

## 13. Risks

- underpricing
- overpricing
- attracting too many users too early
- storage abuse
- optional model cost explosion
- support overload
- legal / privacy exposure
- confusing WESLR with LLM subscriptions
- premature public claims

## 14. Recommended next lane

`REVIEW_WESLR_V1_PRICING_AND_PILOT_RESEARCH_MODEL_V1`

## 15. Boundary reminders

- WESLR is **not an LLM**
- optional models remain **capability providers only**
- actual run approval remains **not granted**
- actual run execution remains **not performed**
- `weslr/chat_responder.py` remains untouched
- `weslr/main.py` remains untouched
