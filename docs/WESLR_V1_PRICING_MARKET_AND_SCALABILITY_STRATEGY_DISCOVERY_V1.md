# WESLR V1 Pricing, Market, and Scalability Strategy Discovery V1

Date: 2026-05-29
Status: discovery / planning only
Grounding:
- `docs/WESLR_V1_MASTER_DEFINITION_AND_WEBSITE_STRUCTURE_V1.md`
- `docs/WESLR_V1_NON_LLM_IDENTITY_AND_OPTIONAL_MODEL_BOUNDARY_V1.md`
- `docs/WESLR_V1_PRODUCT_UX_AND_OPERATING_MODEL_V1.md`
- `docs/WESLR_V1_UPDATE_METHOD_AND_IMPLEMENTATION_FREEZE_V1.md`

## 1. Current pricing status

WESLR V1 pricing is **not finalized**.

Also not finalized:
- exact storage limits
- exact upload limits
- final hosted plan shapes
- final support model
- final model/API pass-through model

Public launch must not overpromise capacity.

Discovery is allowed:
- willingness-to-pay research
- invite-only pilot pricing discovery
- storage/usage observation
- support burden observation
- optional model cost observation

The first **50 invite-only users** may be used for pricing discovery.

Final paid plans require scalability and cost review first.

## 2. Market comparison

These are **market anchors only**. They do not define WESLR’s category.

### ChatGPT
Positioning: general-purpose chatbot / workspace AI / coding assistant

- Personal/free: Free available
- Pro/power-user: Plus is publicly listed at **$20/month**; Pro is publicly listed at **$200/month**
- Team/business: Business plans are per-user monthly; current public page shows business workspace pricing with annual/monthly billing
- Enterprise: custom pricing
- Files/storage/workspace: business/enterprise include larger context and workspace controls; exact file/storage caps are plan-specific and not treated as WESLR anchors here

### Claude
Positioning: general-purpose chatbot / coding assistant / workspace AI

- Personal/free: Free at **$0**
- Pro/power-user: **$17/month** annual, or **$20/month** billed monthly
- Max: from **$100/month**
- Team/business: **$20/seat/month** annual or **$25/month** billed monthly; higher-use seat tier shown at **$100/seat/month** annual or **$125/month** billed monthly
- Enterprise: custom pricing
- Files/storage/workspace: workspace and admin controls are included in team/enterprise tiers; exact caps are plan-specific

### Gemini / Google AI plans
Positioning: personal AI assistant / productivity AI / workspace AI

- Personal/free: Free at **€0/month** with Google account
- Personal/pro: **Google AI Plus €7.99/month**
- Power-user: **Google AI Pro €21.99/month**
- High-usage/premium: **Google AI Ultra** starts at **€99.99/month**, with a higher-usage tier shown at **€219.99/month**
- Team/business: Google Workspace Business Starter/Standard/Plus show public prices of **€3.40 / €6.80**, **€6.80 / €13.60**, and **€10.55 / €21.10** per user per month depending on billing mode
- Enterprise/custom: Enterprise is custom / contact sales
- Files/storage/workspace: Workspace tiers include pooled storage and Gemini in apps; exact limits vary by tier

### Perplexity
Positioning: research assistant / answer engine / search-first AI

- Personal/free: Free tier exists
- Pro/power-user: public search snippets currently surface **$20/month**
- Team/business: public search snippets surface **Enterprise Pro $40/user/month**
- Enterprise/custom: public search snippets surface **Enterprise Max $325/user/month** and enterprise pricing on request
- Files/storage/workspace: public materials emphasize research, uploads, and deeper sourcing; exact caps vary by plan

### Microsoft Copilot
Positioning: consumer assistant / productivity AI / enterprise workspace AI

- Personal/free: Copilot is publicly positioned as free to try on the consumer page
- Pro/power-user: the consumer page points to paid Microsoft 365 / Copilot bundles, but the fetched public excerpt did not expose a clean single consumer Copilot Pro price
- Team/business: Microsoft 365 Copilot business pricing pages exist; the public material shows business/enterprise packaging rather than a simple consumer chatbot tier
- Enterprise/custom: custom / sales-led
- Files/storage/workspace: Microsoft 365 Premium emphasizes extensive Copilot usage and up to 6 TB storage, but the exact price was not surfaced in the captured excerpt

### Other relevant anchors
- Google Workspace AI: relevant because it bundles AI into a business workspace
- Microsoft 365 Premium: relevant because it bundles AI into a productivity + storage offering
- Perplexity Max / enterprise tiers: relevant because they show premium research pricing above basic chatbot tiers

## 3. WESLR positioning

WESLR should be positioned as:
- a **governed continuity-first system**
- a **workspace / context / memory / evidence architecture**
- an **optional-model architecture**
- a **serious work / domain continuity layer**
- a **future private / institutional deployment candidate**

WESLR is not an ordinary chatbot subscription.

The model helps; WESLR governs.

## 4. Reliability / claims boundary

WESLR must **not** claim fewer mistakes than competitors without evidence.

Current status:
- WESLR reliability is still to be determined
- no official benchmark claim is allowed
- no official Turing claim is allowed
- no intelligence certification claim is allowed
- no public production-readiness claim is allowed
- pricing must not imply proven superiority

## 5. Cost model discovery

Before final pricing, WESLR must measure:
- average messages per user/day
- average optional model/provider cost per user
- no-model / governance-only usage cost
- average file upload size
- storage per user
- file parsing / indexing cost
- support / operator time
- infrastructure / server cost
- backup / retention cost
- abuse / spam / security cost
- failed / unsupported file handling cost

## 6. First 50 invite-only pilot model

Recommended discovery model:
1. website launches first
2. invite 50 users manually
3. restrict uploads and storage
4. track usage safely
5. collect qualitative feedback
6. ask willingness to pay after real usage
7. ask what job they would pay WESLR to do
8. ask whether they value WESLR as:
   - model/chat
   - workspace
   - governed continuity
   - file/context system
   - private deployment layer
9. ask whether they would bring their own API/model or expect WESLR-managed model access

## 7. Pilot pricing survey

Max 15 questions:
1. What would WESLR replace or reduce for you today?
2. What job would you pay WESLR to do?
3. Would you use WESLR personally, professionally, or both?
4. Is WESLR too cheap to trust at the current pilot description?
5. Is the pilot good value?
6. Is it getting expensive?
7. Is it too expensive?
8. Would you pay today?
9. What storage/file volume do you expect per month?
10. How often would you upload files?
11. How much model/API usage would you expect?
12. Would you bring your own API key/model?
13. Would you pay more for private deployment?
14. Would you pay more for stronger governance/continuity controls?
15. What would make WESLR clearly worth paying for?

## 8. Provisional pricing hypotheses

All of the following are **non-final**.

- Public website: no price yet, or “pilot by invitation”
- Public demo: free/read-only if approved
- First 50 invite-only users: free limited pilot or symbolic **€10–€20/month**
- Personal/pro: possible future range, not fixed
- Professional continuity workspace: possible future range, not fixed
- Heavy / industrial / private deployment: custom quote
- User-supplied model/API plan: possible early option
- WESLR-managed model plan: later option if cost structure supports it

## 9. Storage / quota hypotheses

All of the following are **conservative non-final hypotheses**.

- Public demo: no upload
- Invite pilot: small file / storage quota
- Paid hosted: higher quota only after infrastructure review
- Private deployment: customer-specific
- Enterprise: custom

No final quota should be promised yet.

## 10. Scalability plan

Before scaling, WESLR must understand:
- local Ubuntu storage is not enough for unbounded uploads
- uploads need quotas
- hosted plans need quota enforcement
- optional model costs need tracking
- future scaling likely needs external object storage or separate file storage
- backups and deletion / retention policy must be designed
- multi-server deployment must be planned before large outreach

## 11. Pricing strategy recommendation

Recommended strategy for WESLR V1:
- **no public price yet**
- **waitlist / pilot-interest model**
- **invite-only pilot**
- **user-supplied API/model option early**
- **WESLR-managed model option later**
- **custom quotes for industrial/private deployments**
- avoid freemium expansion until infrastructure and quotas exist

## 12. Website wording recommendation

Safe public wording:
- “Pilot access by invitation”
- “Pricing and plans are being evaluated with early users”
- “Storage and file-processing limits apply”
- “Models are optional capability providers; WESLR is the governed system”
- “Private / institutional deployments available by discussion”
- “No public production guarantee yet”

## 13. Risks

- underpricing expensive compute/storage
- overpricing before proven value
- promising reliability before evidence
- attracting too many users before infrastructure
- unlimited upload abuse
- legal/privacy exposure from files
- confusing WESLR with ordinary AI subscriptions
- confusing optional LLM capability with WESLR identity
- damaging trust through premature claims

## 14. Recommended next lane

`DESIGN_WESLR_V1_PRICING_AND_PILOT_RESEARCH_MODEL_V1`

## 15. Sources used

- `https://claude.com/pricing`
- `https://chatgpt.com/pricing/`
- `https://gemini.google/subscriptions/`
- `https://workspace.google.com/pricing.html`
- `https://www.microsoft.com/en-us/microsoft-copilot/for-individuals`
- Bing / DuckDuckGo search snippets for Perplexity and ChatGPT market anchors

## 16. Boundary reminders

- WESLR is **not an LLM**
- optional models are **capability providers**, not identity or authority
- actual run approval remains **not granted**
- actual run execution remains **not performed**
- `weslr/chat_responder.py` remains untouched
- `weslr/main.py` remains untouched
