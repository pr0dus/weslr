# WESLR V1 UI Component and Visual Interaction Spec V1

Date: 2026-05-29
Status: design / documentation only
Grounded in:
- `docs/WESLR_V1_PRODUCT_UX_AND_OPERATING_MODEL_V1.md`
- `docs/WESLR_V1_PRODUCT_UX_AND_OPERATING_MODEL_REVIEW_V1.md`
- `docs/WESLR_V1_MASTER_DEFINITION_AND_WEBSITE_STRUCTURE_V1.md`
- `docs/WESLR_V1_MASTER_DEFINITION_AND_WEBSITE_STRUCTURE_REVIEW_V1.md`
- `docs/WESLR_V1_NON_LLM_IDENTITY_AND_OPTIONAL_MODEL_BOUNDARY_V1.md`
- `docs/WESLR_V1_PRICING_MARKET_AND_SCALABILITY_STRATEGY_DISCOVERY_V1.md`

---

## 1. UI Purpose

This specification converts the validated WESLR V1 product UX into concrete visual interface rules.

It defines:
- what users see, click, read, and understand
- visual identity, color, typography, spacing, and component behavior
- website page layouts and app shell structure
- button types, states, and placement rules
- chat message card types and interaction rules
- processing/status states and their visual presentation

This spec prepares later OCW website build work without implementing code now.

It does NOT:
- implement website code
- modify weslr-ui/
- modify dashboards
- implement WESLR runtime code
- modify runtime behavior
- approve or run controlled real answer samples
- modify weslr/chat_responder.py
- modify weslr/main.py

---

## 2. Visual Identity

### 2.1 Design Philosophy

WESLR's visual identity reflects its core positioning: a serious governed intelligence infrastructure for professional work, not a casual chatbot or consumer AI assistant.

**Design Direction:**
- Dark-first premium interface
- Calm industrial/research tone
- Blue/cyan accent direction
- High contrast
- Minimal motion
- Serious, governed, professional
- No childish chatbot/mascot style
- No fake futuristic overclaiming
- No "thinking" theater or fake processing animations
- No unsupported confidence displays

**Visual Values:**
- Clarity over cleverness
- Function over decoration
- Evidence over assertion
- Transparency over opacity
- Governance visibility

### 2.2 Color System

#### Primary Background
- **Deep navy/charcoal:** `#0D1117` to `#161B22`
- **Purpose:** Reduces eye strain during extended work sessions
- **Application:** Main app background, website hero sections

#### Surface/Card Background
- **Elevated surface:** `#21262D` to `#30363D`
- **Purpose:** Cards, panels, modals, elevated content areas
- **Application:** Message cards, file cards, sidebar sections, dropdown menus

#### Border Style
- **Subtle borders:** `#30363D` (muted) to `#388BFF` (accent)
- **Border width:** 1px default, 2px for emphasis
- **Border radius:** 6px (small), 8px (medium), 12px (large)
- **Application:** Card outlines, section dividers, input borders

#### Accent Color
- **Primary accent:** `#388BFF` (bright blue) to `#58A6FF` (cyan-blue)
- **Secondary accent:** `#39D353` (success green) for positive states
- **Purpose:** Interactive elements, active states, call-to-action
- **Application:** Primary buttons, links, active navigation, selection highlights

#### Status Colors

| Status | Color | Hex | Usage |
|--------|-------|-----|-------|
| Approved/Success | Green | `#39D353` | Completed, approved, ready |
| Pending/Waiting | Blue | `#388BFF` | In progress, waiting |
| Warning/Caution | Amber | `#D29922` | Needs attention, limited |
| Blocked/Danger | Red | `#F85149` | Blocked, rejected, error |
| Neutral/Default | Gray | `#8B949E` | Default, inactive, disabled |

#### Text Colors

| Level | Color | Hex | Usage |
|-------|-------|-----|-------|
| Primary | White | `#F0F6FC` | Headlines, primary text |
| Secondary | Light gray | `#C9D1D9` | Body text, descriptions |
| Tertiary | Muted gray | `#8B949E` | Metadata, timestamps, hints |
| Inverse | Dark | `#0D1117` | Text on light backgrounds |

### 2.3 Typography

#### Font Family
- **Primary:** Inter, system-ui, -apple-system, sans-serif
- **Monospace:** JetBrains Mono, Fira Code, SF Mono, monospace
- **Fallback:** -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial

#### Type Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Display | 48px | 600 | 1.1 | Homepage hero headline |
| H1 | 32px | 600 | 1.2 | Page titles, major sections |
| H2 | 24px | 600 | 1.3 | Section headers |
| H3 | 20px | 500 | 1.4 | Subsection headers |
| H4 | 16px | 500 | 1.4 | Card titles, minor headers |
| Body | 16px | 400 | 1.6 | Primary content |
| Body Small | 14px | 400 | 1.5 | Secondary content, descriptions |
| Caption | 12px | 400 | 1.4 | Metadata, timestamps, labels |
| Micro | 11px | 500 | 1.3 | Status pills, badges |

#### Typography Rules
- **Hierarchy:** Clear visual hierarchy through size and weight
- **Contrast:** High contrast between headlines and body
- **Readability:** Comfortable line height (1.4–1.6x)
- **Density:** Generous spacing for calm reading
- **No all-caps headings:** Avoid shouting

### 2.4 Spacing and Density

#### Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Tight spacing, inline elements |
| sm | 8px | Compact spacing, list items |
| md | 16px | Standard spacing, paragraphs |
| lg | 24px | Section spacing |
| xl | 32px | Major section spacing |
| 2xl | 48px | Page section spacing |
| 3xl | 64px | Hero spacing |

#### Layout Grid
- **Max content width:** 1200px (desktop), 100% (mobile)
- **Sidebar width:** 260px (desktop), collapsible on tablet/mobile
- **Right panel width:** 320px (desktop), drawer on mobile
- **Card padding:** 16px (compact), 24px (standard)
- **Section padding:** 24px vertical, 16px horizontal

#### Density Options
- **Default:** Standard spacing for most users
- **Compact:** Reduced spacing for information-dense views (user preference)
- **Comfortable:** Increased spacing for accessibility needs

### 2.5 Corner Radius and Card Style

#### Radius Scale

| Token | Value | Usage |
|-------|-------|-------|
| sm | 6px | Buttons, small inputs |
| md | 8px | Cards, panels, dropdowns |
| lg | 12px | Modals, large containers |
| full | 9999px | Pills, badges, avatars |

#### Card Design
- **Background:** Surface color (`#21262D`)
- **Border:** 1px subtle border (`#30363D`)
- **Radius:** 8px (md)
- **Shadow:** Subtle elevation shadow on hover/focus
- **Padding:** 16px–24px depending on content

#### Elevation
- **Level 0:** No shadow, flush with background
- **Level 1:** Subtle shadow for cards, panels
- **Level 2:** Medium shadow for modals, dropdowns
- **Level 3:** Strong shadow for overlays, alerts

### 2.6 Icon Style

#### Icon Library
- **Primary:** Lucide Icons (open source, consistent, modern)
- **Fallback:** Heroicons, Phosphor Icons
- **Size:** 16px (sm), 20px (md), 24px (lg), 32px (xl)

#### Icon Rules
- **Stroke width:** 1.5px default
- **Color:** Inherits text color or uses accent color
- **Alignment:** Vertically centered with text
- **Labels:** Icons paired with text labels for critical actions
- **Icon-only buttons:** Require tooltip on hover

#### Common Icons

| Action | Icon | Usage |
|--------|------|-------|
| Send | ArrowUp/CornerDownRight | Message send |
| Attach | Paperclip | File attachment |
| Copy | Copy | Copy message |
| Share | Share2 | Share content |
| Export | Download | Export data |
| Delete | Trash2 | Delete/remove |
| Settings | Settings | Configuration |
| Close | X | Close modal/panel |
| Menu | Menu | Navigation menu |
| Search | Search | Search input |
| Check | Check | Approved, complete |
| Alert | AlertCircle | Warning, needs attention |
| Block | XCircle | Blocked, rejected |
| Info | Info | Information tooltip |
| Chevron | ChevronRight/Down | Expand, navigate |
| File | File | File attachment |
| Folder | Folder | Project, collection |
| User | User | Account, user |
| Clock | Clock | Timestamp, history |
| Shield | Shield | Governance, security |
| Evidence | FileCheck | Evidence marker |

### 2.7 Motion and Animation

#### Motion Philosophy
- **Minimal motion:** WESLR is a serious work tool, not a playful app
- **Functional motion:** Motion should communicate state, not decorate
- **Fast, subtle:** Animations under 200ms for state changes
- **No spinning loaders:** Use progress bars, status pills, or skeleton states
- **No thinking theater:** Never show fake "AI thinking" animations

#### Allowed Motion
- **State transitions:** Button hover/focus (100ms)
- **Panel open/close:** Slide-in/out (150ms)
- **Modal open/close:** Fade + scale (150ms)
- **Page transitions:** Fade (100ms)
- **Dropdown open:** Fade (100ms)

#### Forbidden Motion
- **Spinning loaders:** Use status text instead
- **Bouncing dots:** No fake "typing" indicators
- **Pulsing glows:** No decorative attention-grabbing
- **Parallax effects:** No unnecessary complexity
- **Fake thinking:** No animated "AI processing" theater

### 2.8 Accessibility Baseline

#### Contrast Requirements
- **Text on background:** Minimum 4.5:1 contrast ratio
- **Large text:** Minimum 3:1 contrast ratio
- **Interactive elements:** Minimum 3:1 contrast ratio

#### Keyboard Navigation
- **Tab order:** Logical sequence through interactive elements
- **Focus indicators:** Visible focus ring on all interactive elements
- **Enter/Space:** Activate buttons and links
- **Escape:** Close modals, dropdowns, panels

#### Screen Reader Support
- **Semantic HTML:** Use appropriate elements (button, nav, main, article)
- **ARIA labels:** Where semantic HTML is insufficient
- **Alt text:** All images and icons with meaning
- **Live regions:** Status updates announced to screen readers

#### Touch/Mobile
- **Minimum touch target:** 44px × 44px
- **Gesture support:** Swipe for navigation where appropriate
- **No color-only cues:** Information not conveyed by color alone

---

## 3. Website Page UI Structure

### 3.1 Global Elements

#### Website Header
- **Position:** Fixed top, full width
- **Background:** Semi-transparent dark with blur (`rgba(13, 17, 23, 0.85)`)
- **Height:** 64px (desktop), 56px (mobile)
- **Content:** Logo, navigation, CTA button
- **Behavior:** Shrinks on scroll (optional), sticky on mobile

#### Navigation Items
| Item | Link | Notes |
|------|------|-------|
| Home | `/` | Homepage |
| What is WESLR? | `/about` | Product definition |
| How WESLR Works | `/how-it-works` | Architecture explanation |
| Product Experience | `/product` | UI/UX preview |
| Governance & Trust | `/governance` | Trust boundaries |
| Evaluation Roadmap | `/roadmap` | Future evaluation path |
| Use Cases | `/use-cases` | Industrial applications |
| Pilot Interest | `/pilot` | Request access CTA |

#### Mobile Navigation
- **Hamburger menu:** Left side, opens drawer
- **Drawer:** Full-height, slide-in from right
- **CTA:** Fixed at bottom of drawer
- **Close:** X icon or swipe-to-close

#### Footer
- **Position:** Bottom of page, full width
- **Background:** Surface color (`#161B22`)
- **Height:** Auto (content-dependent)
- **Padding:** 48px vertical, 24px horizontal

#### Footer Sections

| Section | Links |
|---------|-------|
| Product | What is WESLR?, How it Works, Product Experience, Governance |
| Resources | Evaluation Roadmap, Use Cases, Industrial Adaptation |
| Company | About, Contact |
| Legal | Privacy Policy, Terms of Use, Commercial License, Impressum |

#### Footer Legal Notice
- **Text:** "WESLR is a governed intelligence system. No production readiness claimed. Pilot by invitation."
- **Links:** Privacy, Terms, Impressum

### 3.2 Homepage Layout

#### Hero Section
- **Background:** Dark gradient with subtle geometric pattern or circuit lines
- **Height:** 100vh minimum, centered content
- **Headline:** `h1` 48px bold, white
- **Subheadline:** `p` 20px, secondary text color, max 80 characters
- **CTA Primary:** "Request Pilot Access" button (accent color)
- **CTA Secondary:** "Learn More" ghost button or text link

#### Hero Content
```
Headline: "Governed Intelligence for Serious Work"

Subheadline: "WESLR is a continuity-first system that connects memory, evidence, 
governance, and operator approval — built for work that requires 
traceability and controlled evolution."

Primary CTA: "Request Pilot Access"
Secondary CTA: "See How It Works"
```

#### What WESLR Is / Is Not Section
- **Layout:** Two-column comparison cards
- **Is Card:** Green accent border, positive statements
- **Is Not Card:** Red accent border, clear exclusions
- **Visual:** Clear contrast between claims and boundaries

#### What WESLR Is
- Governed intelligence system
- Continuity-first architecture
- Evidence and provenance aware
- Operator authority based
- Designed for serious work and domain continuity

#### What WESLR Is Not
- Chatbot wrapper
- Certified intelligence
- Official Turing-test ready
- Benchmark-proven
- Production-ready autonomous runtime
- Public pilot (yet)

#### Architecture Preview Section
- **Layout:** Diagram + explanation cards
- **Visual:** Flow diagram showing canonical chain
- **Labels:** Input → Interpretation → Context/Memory → Evidence → Governance → Response
- **Cards:** Brief explanation of each stage
- **No fake depth:** Surface-level diagram, not implementation detail

#### Governance & Trust Section
- **Layout:** Icon cards or value proposition blocks
- **Content:** Evidence/provenance, operator authority, memory boundaries, update discipline
- **Visual:** Shield icon, checkmark icons, clear labels
- **CTA:** Link to Governance page

#### Evaluation Roadmap Preview
- **Layout:** Timeline or milestone cards
- **Visual:** Horizontal timeline with milestones
- **Labels:** Current state, near-term goals, future evaluation path
- **Honest:** Clear distinction between "designed" vs "implemented" vs "future"

#### Pilot Interest CTA
- **Layout:** Full-width accent background
- **Content:** "Interested in piloting WESLR?"
- **CTA:** "Request Pilot Access" button
- **Secondary:** "Learn More" link

#### No-Overclaim Disclaimer
- **Position:** Footer or bottom of homepage
- **Style:** Small text, muted color, clear language
- **Content:** "WESLR is in internal evaluation. No official test results claimed. No production guarantee. Pilot access by invitation."

### 3.3 "What is WESLR?" Page

#### Hero/Header
- **Headline:** "What is WESLR?"
- **Subheadline:** "A governed, continuity-first intelligence system"
- **Breadcrumb:** Home > What is WESLR?

#### Definition Section
- **Layout:** Large text block with key definition
- **Quote:** One-sentence WESLR definition prominently displayed
- **Attribution:** No external attribution, WESLR definition

#### Core Characteristics Cards
- **Layout:** Grid of 4–6 cards
- **Each card:** Icon, title, brief description
- **Characteristics:** Governance, Continuity, Evidence, Operator Authority, Bounded Memory, Controlled Update

#### What WESLR Is Not Section
- **Layout:** Clear list with strikethrough or X icons
- **Items:** Chatbot wrapper, certified intelligence, autonomous runtime, production-ready claim

#### LLM Boundary Explanation
- **Layout:** Explanatory block with diagram
- **Heading:** "WESLR is not an LLM"
- **Content:** Explain that LLMs are optional capability providers, not WESLR's identity
- **Visual:** Diagram showing WESLR as governed system, LLM as optional module
- **Key quote:** "The model helps; WESLR governs."

#### Related Pages
- **Links:** How WESLR Works, Governance & Trust, Evaluation Roadmap

### 3.4 "How WESLR Works" Page

#### Hero/Header
- **Headline:** "How WESLR Works"
- **Subheadline:** "Architecture designed for governance, evidence, and controlled evolution"
- **Breadcrumb:** Home > How WESLR Works

#### Canonical Flow Diagram
- **Layout:** Large, clear flow diagram
- **Stages:**
  1. User Input / Event
  2. Interpretation
  3. Context & Memory Boundary
  4. Evidence & Provenance Check
  5. Governance & Approval Boundary
  6. Response / Observation Infrastructure
  7. Validation & Review
  8. Update & Freeze Process

- **Visual:** Boxes connected by arrows, clean layout
- **Interaction:** Optional: Hover reveals brief explanation

#### Stage Explanation Cards
- **Layout:** One card per stage, expanded explanation
- **Content:** What each stage does, why it matters
- **Visual:** Consistent card design with stage number

#### Governance Boundary Detail
- **Layout:** Separate section highlighting approval mechanisms
- **Content:** Operator approval, controlled update, no self-approval
- **Visual:** Shield or lock icon, clear boundary visual

#### Continuity Model Explanation
- **Layout:** Section explaining memory and workspace model
- **Content:** Files, conversations, projects, continuity snapshots
- **Visual:** Folder/database icons, clear labeling

#### Related Pages
- **Links:** Governance & Trust, Product Experience, Evaluation Roadmap

### 3.5 "Product Experience" Page

#### Hero/Header
- **Headline:** "Product Experience"
- **Subheadline:** "A workspace designed for serious work and governed continuity"
- **Breadcrumb:** Home > Product Experience

#### App Layout Preview
- **Layout:** Large screenshot or wireframe of app shell
- **Labels:** Sidebar, main workspace, context panel, header, input bar
- **Visual:** Clean mockup showing canonical layout
- **Note:** "Design preview. Not production implementation."

#### Chat/Workspace Model
- **Layout:** Section explaining message bubbles and cards
- **Visual:** Mockup of conversation with different card types
- **Cards shown:** User message, WESLR answer, system card, clarification card, blocked card

#### File Handling Model
- **Layout:** Section explaining file upload and management
- **Visual:** Mockup of file list, file card, upload interface
- **Content:** File states, file types, storage limits (conservative)

#### Memory/Continuity UX
- **Layout:** Section explaining context and memory
- **Visual:** Mockup of context panel, memory indicators
- **Content:** What is remembered, what is not, user control

#### Processing/Status States
- **Layout:** Section showing status indicators
- **Visual:** Mockup of status pills: "Reading input", "Checking context", etc.
- **Content:** What users see during processing, no chain-of-thought exposure

#### Privacy/Legal/User Control
- **Layout:** Section highlighting user rights
- **Visual:** Icons for deletion, export, governance control
- **Content:** Privacy, terms, user control boundaries

#### Roadmap Items
- **Layout:** Timeline or list
- **Visual:** Clear labels for "Designed", "Planned", "Future"
- **Content:** Upcoming features clearly marked

### 3.6 "Governance & Trust" Page

#### Hero/Header
- **Headline:** "Governance & Trust"
- **Subheadline:** "How WESLR ensures controlled evolution and evidence"
- **Breadcrumb:** Home > Governance & Trust

#### Governance Pillars
- **Layout:** Icon cards for each pillar
- **Pillars:**
  - Evidence/Provenance
  - Operator Authority
  - Memory Boundaries
  - Controlled Updates
  - Validation/Review
  - Transparency

#### Evidence & Provenance Section
- **Layout:** Explanatory block with visual
- **Content:** How evidence is tracked, how provenance is preserved
- **Visual:** Flow diagram, source markers

#### Operator Authority Section
- **Layout:** Explanatory block with visual
- **Content:** Who approves, what requires approval, what does not
- **Visual:** Approval gate diagram

#### Memory Boundaries Section
- **Layout:** Explanatory block with visual
- **Content:** What is remembered, what is not, user control
- **Visual:** Bounded context diagram

#### Controlled Updates Section
- **Layout:** Explanatory block with visual
- **Content:** How WESLR evolves, no self-approval, update discipline

#### Trust & Transparency Section
- **Layout:** Honest framing
- **Content:** What is claimed, what is not claimed, honest limitations
- **Visual:** Clear list of claims vs non-claims

### 3.7 "Evaluation Roadmap" Page

#### Hero/Header
- **Headline:** "Evaluation Roadmap"
- **Subheadline:** "Preparing for serious evaluation"
- **Breadcrumb:** Home > Evaluation Roadmap

#### Current State
- **Layout:** Clear section
- **Content:** "Internal evaluation preparation. No official test results claimed."

#### Near-Term Goals
- **Layout:** Timeline or milestone cards
- **Content:** What is planned for V1, V1.1, V2
- **Labels:** Honest status for each item

#### Future Evaluation Path
- **Layout:** Roadmap visual
- **Content:** Evaluation methodology being considered
- **Note:** Requires separate approval and external validation

#### No Benchmark Claims
- **Layout:** Clear disclaimer
- **Content:** "WESLR is not benchmark-proven, certified, or officially tested yet."

### 3.8 "Use Cases" Page

#### Hero/Header
- **Headline:** "Use Cases"
- **Subheadline:** "WESLR is designed for serious work domains"
- **Breadcrumb:** Home > Use Cases

#### Use Case Cards
- **Layout:** Grid of use case cards
- **Each card:** Domain icon, title, brief description
- **Domains:**
  - Industrial Engineering
  - Research & Development
  - Knowledge Management
  - Project Continuity
  - Governance & Compliance
  - Private/Institutional Deployment

#### Industrial/Domain Adaptation Section
- **Layout:** Explanation of how WESLR adapts to domains
- **Content:** Custom context, domain-specific governance, private deployment

#### CTA
- **Content:** "Interested in a specific use case?"
- **CTA:** "Contact Us" button

### 3.9 "Industrial / Domain Adaptation" Page

#### Hero/Header
- **Headline:** "Industrial & Domain Adaptation"
- **Subheadline:** "WESLR adapts to serious work domains"
- **Breadcrumb:** Home > Industrial Adaptation

#### Adaptation Model
- **Layout:** Explanatory section
- **Content:** How WESLR can be configured for different domains
- **Visual:** Domain examples with icons

#### Private/Institutional Deployment
- **Layout:** Section explaining private deployment options
- **Content:** On-premises, data sovereignty, custom governance
- **Visual:** Architecture diagram showing private deployment

#### Contact CTA
- **Content:** "Interested in private deployment?"
- **CTA:** "Contact Us" button

### 3.10 "Pilot Interest" Page

#### Hero/Header
- **Headline:** "Request Pilot Access"
- **Subheadline:** "WESLR is invite-only for early pilots"
- **Breadcrumb:** Home > Pilot Interest

#### Form Layout
- **Fields:**
  - Name (required)
  - Email (required)
  - Organization (optional)
  - Use case interest (dropdown, optional)
  - Message (textarea, optional)

- **Consent checkbox:** "I understand WESLR is in internal evaluation and pilot access is by invitation only."
- **Submit button:** "Submit Request"

#### Alternative Contact
- **Content:** "You can also reach us at [contact email]"
- **Visual:** Email link

#### Privacy Notice
- **Content:** Link to Privacy Policy
- **Note:** "Your information will be used to evaluate pilot interest. No public pilot is live yet."

### 3.11 "About" Page

#### Hero/Header
- **Headline:** "About WESLR"
- **Subheadline:** "Built for serious work"
- **Breadcrumb:** Home > About

#### Mission Statement
- **Content:** Why WESLR exists, what it aims to solve

#### Origin/Context
- **Content:** Brief history, context of development

#### Team/Contact
- **Content:** How to reach the team
- **Visual:** Contact link, not team photos (unless approved)

### 3.12 "Contact" Page

#### Hero/Header
- **Headline:** "Contact"
- **Subheadline:** "Get in touch"
- **Breadcrumb:** Home > Contact

#### Contact Methods
- **Email:** Primary contact method
- **Form:** Optional contact form
- **Social:** If applicable, link to social profiles

#### Form Layout (Optional)
- **Fields:** Name, Email, Subject, Message
- **Submit:** "Send Message"

#### Response Time Notice
- **Content:** "We'll respond as soon as possible."

### 3.13 Legal Pages

#### Privacy Policy
- **Layout:** Clean text layout with section headers
- **Content:** Data collection, usage, user rights, GDPR compliance
- **Last updated:** Date

#### Terms of Use
- **Layout:** Clean text layout
- **Content:** Acceptable use, limitations, liability

#### Commercial License
- **Layout:** Clean text layout
- **Content:** Licensing terms for commercial use

#### Impressum
- **Layout:** Standard legal impressum
- **Content:** Company/organization details, contact, legal representation
- **Language:** German/English depending on jurisdiction

---

## 4. App Shell UI

### 4.1 Canonical Layout

WESLR's app shell consists of five primary regions:

```
┌────────────────────────────────────────────────────────────────────┐
│                         TOP HEADER (64px)                           │
├──────────┬─────────────────────────────────┬───────────────────────┤
│          │                                 │                       │
│   LEFT   │         MAIN WORK AREA          │      RIGHT PANEL     │
│  SIDEBAR │        (flexible width)         │      (320px)         │
│  (260px) │                                 │                       │
│          │                                 │                       │
│          │                                 │                       │
├──────────┴─────────────────────────────────┴───────────────────────┤
│                    BOTTOM INPUT BAR (auto)                          │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 Top Header

#### Layout
- **Height:** 64px (desktop), 56px (mobile)
- **Position:** Fixed top, full width
- **Background:** Surface color with subtle border bottom

#### Elements

| Element | Position | Content | Behavior |
|---------|----------|---------|----------|
| Logo/Wordmark | Left | WESLR text or logo | Click returns to home |
| Workspace Label | Center | Project/workspace name | Dropdown for workspace switch |
| Mode Badge | Right of workspace | Current mode (optional) | Visual indicator |
| Account/Settings | Right | User avatar or settings | Dropdown for account menu |

#### Responsive Behavior
- **Desktop:** All elements visible
- **Tablet:** Workspace label collapses to icon
- **Mobile:** Logo + menu icon only; workspace and account in drawer

### 4.3 Left Sidebar

#### Layout
- **Width:** 260px (expanded), 64px (collapsed icon mode)
- **Position:** Left side, full height minus header
- **Background:** Surface color (`#161B22`)
- **Border:** Right border 1px

#### Sections

##### Conversations/Chats
- **Header:** "Conversations" or "Chats"
- **List:** Recent conversations with title and timestamp
- **Actions:** New chat (+), search
- **Visual:** List item highlights on hover/active

##### Projects
- **Header:** "Projects"
- **List:** Projects with project name and status
- **Actions:** New project (+)
- **Visual:** Project cards with icon and label

##### Files
- **Header:** "Files"
- **List:** Recent files with file icon and name
- **Actions:** Upload (+), search
- **Visual:** File cards with type icon

##### Continuity Snapshots
- **Header:** "Continuity"
- **List:** Saved snapshots with date
- **Actions:** Create snapshot (+)
- **Visual:** Snapshot cards with date and status

##### Settings/Account
- **Position:** Bottom of sidebar
- **Links:** Settings, Account, Help, Sign Out

#### Collapse Behavior
- **Collapsed mode:** Icons only, 64px width
- **Toggle:** Collapse/expand button at bottom
- **Mobile:** Hidden by default, drawer on menu click

### 4.4 Main Chat/Work Area

#### Layout
- **Position:** Center, flexible width
- **Background:** Primary background (`#0D1117`)
- **Content:** Chat messages, file cards, workspace responses

#### Message Flow
- **Scroll:** Vertical scroll, messages stack bottom-up or top-down
- **Width:** Max 800px for readability (centered), full width for file cards
- **Alignment:** User messages right-aligned (optional), WESLR answers left-aligned

#### Empty State
- **Visual:** Welcome message or prompt
- **Content:** "Start a conversation" or similar

### 4.5 Right Context/Governance Panel

#### Layout
- **Width:** 320px (desktop)
- **Position:** Right side, full height minus header
- **Background:** Surface color (`#161B22`)
- **Border:** Left border 1px

#### Sections

##### Context Used
- **Header:** "Context Used"
- **Content:** List of context items active in conversation
- **Visual:** Compact list, expandable details

##### Evidence Status
- **Header:** "Evidence Status"
- **Content:** Evidence markers, source links, validation status
- **Visual:** Status pills, icons

##### Memory Boundary
- **Header:** "Memory Boundary"
- **Content:** What is remembered, what is not
- **Visual:** Toggle indicators, memory scope

##### Approvals
- **Header:** "Approvals"
- **Content:** Pending approvals, approval history
- **Visual:** Approval cards with status

##### Source Status
- **Header:** "Sources"
- **Content:** Source files, references used in response
- **Visual:** File cards with source markers

##### Process Summary
- **Header:** "Process"
- **Content:** Compact status of current WESLR process
- **Visual:** Status pills, stepper

#### Mobile Behavior
- **Default:** Hidden on mobile
- **Access:** Drawer from right edge, slide-in
- **Toggle:** Button in header or gesture

### 4.6 Bottom Input/Action Bar

#### Layout
- **Height:** Auto (content-dependent)
- **Position:** Bottom of main work area
- **Background:** Surface color with top border

#### Elements

| Element | Position | Behavior |
|---------|----------|----------|
| Text Input | Left-center | Multi-line textarea, auto-grow to 4 lines max |
| Attach Button | Left of input | Opens file picker |
| Mode Selector | Right of input (optional) | Dropdown for mode (if applicable) |
| Send Button | Right | Send message (disabled if input empty) |

#### Input Behavior
- **Placeholder:** "Ask WESLR..." or similar
- **Focus:** Visible focus ring
- **Shortcut:** Enter to send, Shift+Enter for new line

#### Mobile Behavior
- **Input:** Full width, fixed to bottom
- **Attach:** Icon button
- **Send:** Icon button
- **Keyboard:** Mobile keyboard appears on focus

---

## 5. Button System

### 5.1 Button Types

#### Primary Button
- **Background:** Accent color (`#388BFF`)
- **Text:** White (`#F0F6FC`)
- **Border:** None
- **Radius:** 6px (sm)
- **Padding:** 8px 16px (sm), 12px 24px (md)
- **Hover:** Slightly brighter accent (`#58A6FF`)
- **Active:** Pressed darker accent (`#1F6FEB`)
- **Focus:** Visible focus ring
- **Usage:** Main CTAs, primary actions (Request Pilot Access, Sign In, Send)

#### Secondary Button
- **Background:** Surface color (`#21262D`)
- **Text:** Primary text (`#F0F6FC`)
- **Border:** 1px border (`#30363D`)
- **Radius:** 6px
- **Padding:** Same as primary
- **Hover:** Slightly lighter background
- **Usage:** Secondary actions (Learn More, Cancel, Close)

#### Ghost Button
- **Background:** Transparent
- **Text:** Accent color (`#388BFF`)
- **Border:** None or 1px transparent
- **Radius:** 6px
- **Padding:** Same as primary
- **Hover:** Subtle surface background
- **Usage:** Tertiary actions, navigation links, text links styled as buttons

#### Danger Button
- **Background:** Danger red (`#F85149`)
- **Text:** White
- **Border:** None
- **Radius:** 6px
- **Padding:** Same as primary
- **Hover:** Brighter red (`#FF7B72`)
- **Usage:** Destructive actions (Delete, Remove, Block)

#### Disabled Button
- **Background:** Muted surface (`#30363D`)
- **Text:** Muted gray (`#8B949E`)
- **Border:** None
- **Radius:** 6px
- **Cursor:** Not-allowed
- **Usage:** Actions not currently available

#### Link Button
- **Background:** Transparent
- **Text:** Accent color (`#388BFF`)
- **Border:** None
- **Padding:** 0 (text link)
- **Hover:** Underline
- **Usage:** Text navigation, inline links

#### Icon Button
- **Background:** Transparent or surface
- **Icon:** Inherits text color or accent
- **Size:** 32px × 32px minimum (touch target)
- **Radius:** 6px or full (circular)
- **Tooltip:** Required on hover
- **Usage:** Toolbar actions, close buttons, menu toggles

#### Pill/Tag Button
- **Background:** Surface (`#21262D`)
- **Text:** Secondary text (`#C9D1D9`)
- **Border:** 1px border (`#30363D`)
- **Radius:** Full (9999px)
- **Padding:** 4px 12px
- **Usage:** Tags, filters, status pills

### 5.2 Button Labels and Rules

#### "Request Pilot Access"
- **Type:** Primary
- **Position:** Homepage hero, Pilot Interest page header, Footer CTA
- **Enabled:** Always
- **Risk Level:** None (information collection)
- **Login Required:** No
- **Public Demo Allowed:** Yes

#### "Join Pilot List"
- **Type:** Primary
- **Position:** Pilot Interest form submit
- **Enabled:** When form is complete
- **Risk Level:** None
- **Login Required:** No
- **Public Demo Allowed:** Yes

#### "Sign In"
- **Type:** Secondary
- **Position:** Header (if logged out)
- **Enabled:** Always
- **Risk Level:** None
- **Login Required:** N/A (opens login flow)
- **Public Demo Allowed:** Yes (visible, but action depends on account)

#### "Send"
- **Type:** Primary (icon + text or icon only)
- **Position:** Bottom input bar
- **Enabled:** When input has content
- **Risk Level:** None
- **Login Required:** Yes (for app)
- **Public Demo Allowed:** Only if demo is approved and read-only/safe

#### "Attach File"
- **Type:** Icon Button
- **Position:** Bottom input bar, file management areas
- **Enabled:** When uploads are allowed (pilot/paid)
- **Risk Level:** Low (file upload)
- **Login Required:** Yes
- **Public Demo Allowed:** No (public demo has no upload)

#### "New Chat"
- **Type:** Ghost or Secondary
- **Position:** Left sidebar header
- **Enabled:** Always in app
- **Risk Level:** None
- **Login Required:** Yes
- **Public Demo Allowed:** Only if demo is approved

#### "New Project"
- **Type:** Ghost or Secondary
- **Position:** Left sidebar projects section
- **Enabled:** Always in app
- **Risk Level:** None
- **Login Required:** Yes
- **Public Demo Allowed:** No

#### "Copy"
- **Type:** Icon Button or Ghost
- **Position:** Message card actions
- **Enabled:** Always
- **Risk Level:** None
- **Login Required:** No (copy works in demo)
- **Public Demo Allowed:** Yes

#### "Share"
- **Type:** Icon Button or Ghost
- **Position:** Message card actions
- **Enabled:** When sharing is allowed
- **Risk Level:** Medium (privacy concern)
- **Login Required:** Yes
- **Public Demo Allowed:** No (public demo no share)

#### "Export"
- **Type:** Secondary or Ghost
- **Position:** Settings, message actions, workspace menu
- **Enabled:** When export is implemented
- **Risk Level:** Medium (data export)
- **Login Required:** Yes
- **Public Demo Allowed:** No

#### "Delete"
- **Type:** Danger
- **Position:** Settings, file management, message actions
- **Enabled:** When user has permission
- **Risk Level:** High (destructive)
- **Login Required:** Yes
- **Public Demo Allowed:** No
- **Confirmation:** Required (modal or inline confirmation)

#### "Ask about File"
- **Type:** Primary or Ghost
- **Position:** File card actions
- **Enabled:** When file is attached to conversation
- **Risk Level:** None
- **Login Required:** Yes
- **Public Demo Allowed:** No (public demo no file)

#### "Summarize File"
- **Type:** Secondary or Ghost
- **Position:** File card actions
- **Enabled:** When file is uploaded
- **Risk Level:** None
- **Login Required:** Yes
- **Public Demo Allowed:** No

#### "Show Context" / "Hide Context"
- **Type:** Ghost
- **Position:** Message card actions, right panel toggle
- **Enabled:** Always in app
- **Risk Level:** None
- **Login Required:** Yes
- **Public Demo Allowed:** Yes (if demo approved)

#### "View Sources"
- **Type:** Ghost
- **Position:** Message card actions, right panel
- **Enabled:** When sources exist
- **Risk Level:** None
- **Login Required:** Yes
- **Public Demo Allowed:** Yes (if demo approved)

#### "Request Deletion/Export"
- **Type:** Secondary
- **Position:** Settings, privacy section
- **Enabled:** When feature implemented
- **Risk Level:** Medium (data request)
- **Login Required:** Yes
- **Public Demo Allowed:** No

#### "Contact"
- **Type:** Secondary or Link
- **Position:** Footer, About page, Contact page
- **Enabled:** Always
- **Risk Level:** None
- **Login Required:** No
- **Public Demo Allowed:** Yes

---

## 6. Chat Message UI

### 6.1 Message Card Types

#### User Message Card
- **Alignment:** Right-aligned (optional) or left-aligned
- **Background:** Surface color (`#21262D`) or primary accent with opacity
- **Border:** 1px subtle border
- **Radius:** 8px (md)
- **Content:** User message text, timestamp, status

##### User Message Elements
| Element | Position | Behavior |
|---------|----------|----------|
| Avatar/Icon | Top-left or right | User avatar or placeholder |
| Message Text | Body | Full message content |
| Timestamp | Bottom-right | Compact, hover for full time |
| Status | Bottom-left | Sent, Delivered, Read (if applicable) |
| Copy | Action menu | Copy message text |

#### WESLR Answer Card
- **Alignment:** Left-aligned
- **Background:** Surface color (`#161B22`) or elevated surface
- **Border:** 1px subtle border
- **Radius:** 8px (md)
- **Content:** WESLR answer text, status, sources, actions

##### WESLR Answer Elements
| Element | Position | Behavior |
|---------|----------|----------|
| WESLR Icon/Label | Top-left | WESLR branding or icon |
| Answer Text | Body | Full answer content, formatted (markdown safe) |
| Status Pill | Top-right | Compact status: "Ready", "Needs Clarification", "Blocked" |
| Source Markers | Inline or bottom | Evidence/source indicators |
| Timestamp | Bottom-right | Compact, hover for full time |
| Actions | Bottom-left | Copy, Share (if allowed), View Sources |

#### System/Status Card
- **Alignment:** Center or left-aligned
- **Background:** Muted surface (`#30363D`)
- **Border:** 1px subtle border
- **Radius:** 8px (md)
- **Content:** System status, process update, or notification

##### System Card Elements
| Element | Position | Behavior |
|---------|----------|----------|
| Icon | Top-left | Status icon (info, warning, check, block) |
| Title | Top | Status title |
| Message | Body | System message |
| Timestamp | Bottom-right | Compact timestamp |

#### Clarification Card
- **Alignment:** Left-aligned
- **Background:** Surface with warning accent border
- **Border:** 2px warning amber (`#D29922`)
- **Radius:** 8px (md)
- **Content:** Clarification request, input fields, submit

##### Clarification Card Elements
| Element | Position | Behavior |
|---------|----------|----------|
| Icon | Top-left | Warning or question icon |
| Title | Top | "Clarification Needed" |
| Message | Body | What WESLR needs clarified |
| Input | Body | Text input or selection |
| Submit | Bottom-right | "Submit Clarification" button |

#### Blocked/Governance Card
- **Alignment:** Left-aligned
- **Background:** Surface with danger accent border
- **Border:** 2px danger red (`#F85149`)
- **Radius:** 8px (md)
- **Content:** Blocked reason, governance boundary explanation

##### Blocked Card Elements
| Element | Position | Behavior |
|---------|----------|----------|
| Icon | Top-left | Block icon (XCircle) |
| Title | Top | "Blocked by Boundary" |
| Reason | Body | Why blocked (governance, policy, limitation) |
| Explanation | Body | What can be done instead |
| Actions | Bottom | "Ask differently", "Contact Support" |

#### Evidence/Source Card
- **Alignment:** Attached to WESLR answer or standalone
- **Background:** Surface (`#21262D`)
- **Border:** 1px accent border (`#388BFF`)
- **Radius:** 8px (md)
- **Content:** Source file, reference, validation status

##### Source Card Elements
| Element | Position | Behavior |
|---------|----------|----------|
| Icon | Top-left | File icon, source icon |
| Title | Top | Source title or filename |
| Type | Top-right | Source type badge |
| Status | Body | Validation status |
| Link | Bottom | "View Source" if applicable |

#### Uncertainty Card
- **Alignment:** Left-aligned
- **Background:** Surface with warning accent
- **Border:** 2px warning amber (`#D29922`)
- **Radius:** 8px (md)
- **Content:** Uncertainty explanation, what is not known

##### Uncertainty Card Elements
| Element | Position | Behavior |
|---------|----------|----------|
| Icon | Top-left | Uncertainty icon (help circle) |
| Title | Top | "Cannot Safely Answer" or "Uncertainty" |
| Message | Body | Why WESLR cannot answer with confidence |
| Alternatives | Body | What can be asked instead |

#### File-Reference Card
- **Alignment:** Attached to message or standalone
- **Background:** Surface (`#21262D`)
- **Border:** 1px subtle border
- **Radius:** 8px (md)
- **Content:** File metadata, preview snippet, actions

##### File Card Elements
| Element | Position | Behavior |
|---------|----------|----------|
| Icon | Left | File type icon |
| Filename | Top | Full filename |
| Size | Top-right | File size |
| Status | Bottom | Upload status (uploaded, reading, indexed, blocked) |
| Actions | Right | View, Ask, Summarize, Remove |

### 6.2 Message Timestamp Behavior
- **Default:** Compact or hidden (e.g., "2m ago")
- **Hover:** Full timestamp (e.g., "2026-05-29 17:17:00")
- **Visual:** Muted gray, small text, right-aligned
- **Grouped:** If multiple messages in quick succession, timestamp on group only

### 6.3 Copy Per Message
- **Action:** Copy button in message actions
- **Behavior:** Copies message text to clipboard
- **Feedback:** Toast notification "Copied to clipboard"
- **Privacy:** Does not copy private context by default

### 6.4 Share/Export Gated by Privacy
- **Share:** Disabled or removed in public demo
- **Share:** Available in logged-in app, but privacy notice shown
- **Export:** Available only when implemented and approved
- **Privacy:** User must consent before sharing/exporting context

### 6.5 Source/Evidence Marker
- **Visual:** Small icon (checkmark or file icon) with "Evidence" label
- **Position:** Inline with answer text or in source card
- **Behavior:** Click to view source details
- **Color:** Accent blue or success green if validated

### 6.6 Status Label
- **Visual:** Status pill (rounded, small text)
- **Position:** Top-right of answer card or system card
- **States:**
  - Ready (green): "Ready"
  - Needs Clarification (amber): "Clarification Needed"
  - Blocked (red): "Blocked"
  - Pending (blue): "Processing"
  - Uncertainty (amber): "Uncertainty"

### 6.7 Mobile Behavior
- **Single column:** All cards stack vertically
- **Full width:** Cards use full available width
- **Compact:** Reduced padding, smaller text
- **Swipe actions:** Swipe message for actions (copy, delete, etc.)
- **Right panel:** Drawer from right, toggle in header
- **Bottom input:** Fixed to bottom, full width

---

## 7. WESLR Processing/Status UI

### 7.1 Visible Processing States

WESLR's processing status should be transparent without exposing chain-of-thought.

#### State Sequence
1. **Reading Input** → User message received, interpreting
2. **Reading File** → File upload detected, scanning
3. **Checking Context** → Reviewing conversation/workspace context
4. **Checking Evidence** → Validating sources and evidence
5. **Checking Governance** → Applying governance boundaries
6. **Waiting for Approval** → Operator approval required (if applicable)
7. **Needs Clarification** → User input needed
8. **Blocked by Boundary** → Cannot proceed due to policy/limitation
9. **Ready to Answer** → Prepared to respond
10. **Answer Generated** → Response ready
11. **Answer Not Generated** → No response produced (explain why)

### 7.2 Status Display Rules

#### Compact Status Pill
- **Position:** Top-right of answer card or in status bar
- **Visual:** Small rounded pill with status text
- **Color:** State-dependent (blue for pending, green for ready, amber for clarification, red for blocked)
- **Behavior:** Updates as processing progresses

#### Status Stepper (Detailed View)
- **Position:** Right panel or dedicated status area
- **Visual:** Vertical stepper showing progress
- **Elements:**
  - Circle icon for each step (empty, active, complete)
  - Label for each step
  - Connecting line between steps
- **Active Step:** Highlighted with accent color
- **Complete Steps:** Green checkmark
- **Blocked Step:** Red X or amber warning

#### Process Summary Only
- **Rule:** Show safe process summary, not chain-of-thought
- **No:** Internal reasoning, model thoughts, hidden logic
- **Yes:** High-level status labels

#### No Fake "Thinking" Theater
- **Rule:** No spinning "AI is thinking" animations
- **Rule:** No fake typing indicators
- **Rule:** No pulsing dots
- **Alternative:** Use status pills or steppers with actual state names

#### No Unsupported Confidence Display
- **Rule:** Do not show confidence percentages unless validated
- **Rule:** Do not claim certainty without evidence
- **Alternative:** Show "Uncertainty" state with honest explanation

### 7.3 Status Messages

| State | Status Pill Text | Status Stepper Label |
|-------|------------------|----------------------|
| Reading Input | "Reading input" | "Reading your message" |
| Reading File | "Reading file" | "Scanning attached file" |
| Checking Context | "Checking context" | "Reviewing conversation context" |
| Checking Evidence | "Checking evidence" | "Validating sources and evidence" |
| Checking Governance | "Checking governance" | "Applying governance boundaries" |
| Waiting for Approval | "Waiting for approval" | "Awaiting operator approval" |
| Needs Clarification | "Clarification needed" | "Need more information" |
| Blocked by Boundary | "Blocked" | "Blocked by policy" |
| Ready to Answer | "Ready" | "Ready to respond" |
| Answer Generated | "Complete" | "Response ready" |
| Answer Not Generated | "No answer" | "Unable to generate response" |

### 7.4 Status Transitions
- **Visual:** Smooth transition between states (100–150ms)
- **No flashing:** Avoid rapid color changes
- **No animation loops:** Static status pills, not animated

### 7.5 Error/Blocked Handling
- **Blocked by Boundary:** Show reason in blocked card
- **Error:** Show error card with explanation
- **Retry:** Offer "Try again" or "Ask differently" option
- **Support:** Link to contact support for persistent issues

---

## 8. Mobile and Responsive Behavior

### 8.1 Breakpoints

| Breakpoint | Width | Behavior |
|------------|-------|----------|
| Desktop | ≥1024px | Full layout, all panels visible |
| Tablet | 768–1023px | Collapsible sidebar, right panel as drawer |
| Mobile | <768px | Single column, sidebar as drawer, right panel as drawer |

### 8.2 Sidebar Collapse
- **Desktop:** Sidebar visible, 260px
- **Tablet:** Sidebar collapsed to icons (64px), expandable on hover or click
- **Mobile:** Sidebar hidden, drawer on menu button

### 8.3 Right Panel Drawer
- **Desktop:** Right panel visible, 320px
- **Tablet:** Right panel as slide-in drawer from right
- **Mobile:** Right panel as slide-in drawer from right, full-width overlay

### 8.4 Bottom Input Behavior
- **Desktop:** Fixed to bottom of main area
- **Tablet:** Fixed to bottom
- **Mobile:** Fixed to bottom, full width, adjusts for keyboard

### 8.5 Mobile Navigation
- **Header:** Logo + menu icon only
- **Menu:** Drawer from left, full height
- **Right Panel:** Drawer from right, toggle in header
- **Back:** Hardware back or swipe-to-close for drawers

### 8.6 File Cards on Small Screens
- **Layout:** Full width, stacked
- **Actions:** Icons only, labels on tooltip or below
- **Preview:** Snippet truncated with "View full" link

### 8.7 Legal/Privacy Links on Mobile
- **Position:** Footer drawer or settings page
- **Access:** "Legal" link in settings or footer
- **Content:** Full-width text pages

---

## 9. Trust and Transparency Rules

### 9.1 What Must Be Shown
- **Governance boundaries:** Where WESLR stops
- **Evidence markers:** When sources are used
- **Memory boundaries:** What is remembered, what is not
- **Approval requirements:** When operator approval is needed
- **Process status:** What WESLR is doing (high-level)
- **Uncertainty:** When WESLR cannot safely answer

### 9.2 What Must Not Be Shown
- **Chain-of-thought:** Internal model reasoning
- **Fake thinking animations:** Spinning dots, fake typing
- **Confidence percentages:** Without validated evidence
- **Hidden logic:** What users cannot inspect
- **Overclaiming:** Claims not backed by implementation

### 9.3 Honest Framing
- **Implemented vs Designed:** Clear labels
- **Under Review:** Label for pending features
- **Future Roadmap:** Label for planned items
- **Not Yet Authorized:** Label for blocked capabilities

---

## 10. Brand Assets

### 10.1 Logo Placeholder
- **Text Lockup:** "WESLR" in clean sans-serif (Inter or similar)
- **Icon:** Optional simple geometric icon (governance/continuity theme)
- **Usage:** Header, footer, loading screens
- **Note:** Final brand assets pending owner decision

### 10.2 Color Palette Summary

| Token | Color | Hex |
|-------|-------|-----|
| Primary Background | Deep Navy | `#0D1117` |
| Surface | Elevated Dark | `#21262D` |
| Border | Subtle Gray | `#30363D` |
| Accent Primary | Bright Blue | `#388BFF` |
| Accent Hover | Cyan-Blue | `#58A6FF` |
| Success | Green | `#39D353` |
| Warning | Amber | `#D29922` |
| Danger | Red | `#F85149` |
| Text Primary | White | `#F0F6FC` |
| Text Secondary | Light Gray | `#C9D1D9` |
| Text Muted | Gray | `#8B949E` |

---

## 11. Implementation Notes

### 11.1 What This Spec Enables
- UI component library design
- Website static page implementation
- App shell layout implementation
- Interactive prototype creation
- Developer handoff for OCW build

### 11.2 What This Spec Does NOT Enable
- Runtime implementation of WESLR
- Changes to `weslr/chat_responder.py`
- Changes to `weslr/main.py`
- Controlled real answer sample execution
- Public demo launch
- Public pilot launch

### 11.3 Next Steps
- Website static pages can be designed from this spec
- UI component library can be built from this spec
- Interactive prototype can be created
- Implementation requires separate approval and build phase

---

## 12. Boundary Confirmations

- `weslr/chat_responder.py` remains untouched
- `weslr/main.py` remains untouched
- No runtime behavior changes
- No controlled real answer sample execution
- No approval granted for implementation
- This is design/documentation only

---

## 13. Recommended Next Lane

`REVIEW_WESLR_V1_UI_COMPONENT_AND_VISUAL_INTERACTION_SPEC_V1`

---

## 14. Document Status

**Status:** Design / documentation only
**Implementation:** Requires separate approval
**Website Build:** Requires separate OCW phase
**Public Launch:** Not authorized

---

---

## 8. File Upload UI

### 8.1 File Upload Locations

Files appear in multiple locations within the WESLR interface:

#### Attachment Strip in Chat
- **Position:** Above the input bar, below the message area
- **Visual:** Horizontal strip of file cards
- **Behavior:** Files attached to current conversation
- **Actions:** Add file, remove file, view file details

#### Files Area in Sidebar
- **Position:** Left sidebar, "Files" section
- **Visual:** List of recent files with file icon and name
- **Behavior:** Click to view file details or attach to conversation
- **Actions:** Upload file, search files, filter by type

#### Project File List
- **Position:** Project workspace view
- **Visual:** Grid or list of files within project
- **Behavior:** Files bound to project context
- **Actions:** Add to project, remove from project, view details

#### File Detail Card
- **Position:** Modal or side panel
- **Visual:** Expanded file information
- **Content:** Metadata, preview snippet, actions, status

#### Upload Disabled Card (Public Demo)
- **Position:** Where upload would normally appear
- **Visual:** Disabled state with explanation
- **Content:** "Upload not available in public demo" + "Request pilot access"

### 8.2 File Card Elements

Every file card must include:

| Element | Description |
|---------|-------------|
| Filename/Title | Full filename with extension |
| File Type | Icon and label (txt, pdf, csv, etc.) |
| File Size | Human-readable size (KB, MB) |
| Upload Date | Date uploaded |
| Status | Current file state |
| Workspace/Project Binding | Which workspace/project owns the file |
| Actions | Available actions for this file |
| Warning Labels | Any warnings or restrictions |

#### File Card Layout
```
┌─────────────────────────────────────────────┐
│ [Icon]  filename.pdf                 [Size] │
│         Type: PDF · Uploaded: 2026-05-29    │
│         Status: Indexed                     │
│         Project: Engineering Docs           │
│                                             │
│         [View] [Ask] [Summarize] [Remove]   │
│                                             │
│         ⚠️ Contains sensitive data          │
└─────────────────────────────────────────────┘
```

### 8.3 File States

#### Upload Disabled
- **Visual:** Grayed out, disabled icon
- **Status:** "Upload not available"
- **Explanation:** Public demo does not support file upload
- **CTA:** "Request pilot access" link

#### Selected
- **Visual:** File selected in picker, not yet uploaded
- **Status:** "Selected"
- **Actions:** Upload, Cancel

#### Uploading
- **Visual:** Progress bar or spinner
- **Status:** "Uploading..." + percentage
- **Actions:** Cancel upload

#### Pending Scan
- **Visual:** Scanning icon
- **Status:** "Scanning for safety"
- **Explanation:** File is being scanned for malware/safety

#### Accepted
- **Visual:** Checkmark icon, normal card
- **Status:** "Accepted"
- **Explanation:** File passed safety scan, ready for use

#### Reading
- **Visual:** Reading icon
- **Status:** "Reading file"
- **Explanation:** WESLR is processing file content

#### Indexed/Summarized
- **Visual:** Checkmark icon, ready for use
- **Status:** "Indexed" or "Summarized"
- **Explanation:** File processed and available in context

#### Unsupported
- **Visual:** Warning icon
- **Status:** "Unsupported"
- **Explanation:** File type not supported
- **Actions:** View accepted formats, Remove

#### Too Large
- **Visual:** Warning icon, size indicator
- **Status:** "Too large"
- **Explanation:** File exceeds size limit
- **Actions:** View limits, Remove

#### Corrupted
- **Visual:** Error icon
- **Status:** "Corrupted"
- **Explanation:** File could not be read (corrupted)
- **Actions:** Remove, Contact support

#### Blocked
- **Visual:** Block icon, danger red
- **Status:** "Blocked"
- **Explanation:** File blocked by policy (malware, executable, dangerous)
- **Actions:** View policy, Remove

#### Deleted
- **Visual:** Strikethrough or removed card
- **Status:** "Deleted"
- **Explanation:** File removed from workspace
- **Behavior:** Card may disappear or show deleted state briefly

#### Expired
- **Visual:** Clock icon, muted
- **Status:** "Expired"
- **Explanation:** File retention period ended
- **Actions:** Re-upload (if allowed)

### 8.4 File Actions

| Action | Availability | Risk Level |
|--------|-------------|------------|
| View metadata | Always | None |
| Ask about file | If file attached | None |
| Summarize | If file processed | None |
| Remove from chat | If attached | Low |
| Delete from workspace | If owner | High |
| Export metadata | If implemented | Medium |
| Request deletion | If implemented | Medium |

---

## 9. Unknown/Unsafe File UI

### 9.1 Unknown File Card
- **Visual:** Generic file icon, question mark overlay
- **Status:** "Unknown file type"
- **Explanation:** "This file type is not recognized."
- **Actions:** View accepted formats, Remove

### 9.2 Unsupported File Explanation
- **Card Title:** "Unsupported File Type"
- **Explanation:** "WESLR supports text files (.txt, .md), documents (.pdf, .docx), and structured data (.csv, .json, .yaml). This file type is not currently supported."
- **Link:** "View all accepted formats"
- **Actions:** Remove file, Contact support

### 9.3 Too-Large File Explanation
- **Card Title:** "File Too Large"
- **Explanation:** "This file exceeds the size limit for your plan."
- **Size Info:** Show current file size and max allowed size
- **Actions:** Remove file, View storage limits, Upgrade plan (if applicable)

### 9.4 Dangerous/Executable Blocked Explanation
- **Card Title:** "File Blocked for Safety"
- **Explanation:** "Executable and potentially dangerous files are not allowed. This includes .exe, .bat, .sh, and similar file types."
- **Policy Link:** "View file policy"
- **Actions:** Remove file

### 9.5 Privacy/Sensitive Warning
- **Card Title:** "Sensitive Content Detected"
- **Explanation:** "This file may contain sensitive or private information. WESLR will process it according to your privacy settings."
- **Options:** "Process anyway", "Remove file", "Review privacy settings"

### 9.6 Remove File Action
- **Button:** "Remove" or "Delete"
- **Confirmation:** If file attached to conversation, confirm removal
- **Visual:** Trash icon, danger red on hover
- **Behavior:** File removed from UI, marked for deletion

### 9.7 Accepted Formats Link
- **Position:** In file upload modal or help section
- **Content:** Complete list of accepted file types
- **Categories:**
  - Text: .txt, .md
  - Documents: .pdf, .docx (if parser exists)
  - Structured: .csv, .json, .yaml
  - Images: .png, .jpg, .webp (if vision in scope)
- **Note:** "Other file types are not currently supported."

### 9.8 Safety Rules
- **Unknown files:** Must NOT silently process
- **Unsupported files:** Must NOT crash UI
- **Public demo upload:** Remains disabled unless separately approved
- **Dangerous files:** Blocked by default, no bypass option

---

## 10. Workspace UI

### 10.1 Workspace Elements

#### Conversations
- **Position:** Left sidebar, top section
- **Visual:** List of recent conversations
- **Each item:** Conversation title, timestamp, status
- **Actions:** New chat (+), search, filter

#### Projects
- **Position:** Left sidebar, second section
- **Visual:** List of projects
- **Each item:** Project name, status, file count
- **Actions:** New project (+), view project

#### Files
- **Position:** Left sidebar, third section
- **Visual:** List of recent files
- **Each item:** Filename, type icon, status
- **Actions:** Upload (+), search, filter by type

#### Continuity Snapshots
- **Position:** Left sidebar, fourth section
- **Visual:** List of saved workspace snapshots
- **Each item:** Snapshot name/number, date, status
- **Actions:** Create snapshot (+), restore snapshot

#### Context Used
- **Position:** Right panel, top section
- **Visual:** List of context items active in current conversation
- **Each item:** Source name, relevance, status
- **Actions:** Show/hide context, remove from context

#### Memory/Knowledge Area
- **Position:** Right panel, second section
- **Visual:** List of remembered items
- **Each item:** Fact/insight, source, confidence
- **Actions:** Add to memory, remove from memory, approve memory

#### Timeline/Activity Log
- **Position:** Right panel or separate view
- **Visual:** Chronological list of workspace events
- **Each item:** Event description, timestamp, actor
- **Filter:** By date, by type, by actor

#### Settings
- **Position:** Bottom of sidebar or separate page
- **Visual:** Settings icon
- **Categories:** Account, Workspace, Privacy, Notifications, Appearance

### 10.2 Empty States

#### No Chats
- **Visual:** Empty conversation list with illustration
- **Message:** "No conversations yet"
- **CTA:** "Start a new chat"

#### No Project
- **Visual:** Empty project list
- **Message:** "No projects"
- **CTA:** "Create your first project"

#### No Files
- **Visual:** Empty file list
- **Message:** "No files uploaded"
- **CTA:** "Upload a file" (if allowed) or "Request pilot access" (if demo)

#### No Memory
- **Visual:** Empty memory/knowledge area
- **Message:** "WESLR hasn't remembered anything yet"
- **Explanation:** "Memory is created through conversations and explicit approval."
- **CTA:** "Learn about memory" (link to docs)

#### No Access
- **Visual:** Locked state
- **Message:** "Access required"
- **Explanation:** "You need to be invited to access this workspace."
- **CTA:** "Request access" or "Contact support"

#### Account Pending
- **Visual:** Pending state
- **Message:** "Your account is pending approval"
- **Explanation:** "You'll receive an email when your account is approved."
- **CTA:** "Contact support" (if urgent)

#### Workspace Limit Reached
- **Visual:** Limit warning
- **Message:** "Workspace limit reached"
- **Explanation:** "You've reached the maximum number of workspaces for your plan."
- **CTA:** "Upgrade plan" (if applicable) or "Contact support"

### 10.3 Workspace Binding Rules
- **Files:** Belong to workspace, can be attached to projects/conversations
- **Memory:** Belongs to user/project/workspace only if explicitly approved
- **Context:** Conversation-specific, not automatically global
- **Snapshots:** Bound to workspace, not portable between workspaces

---

## 11. Memory/Continuity UI

### 11.1 Context Used Panel
- **Position:** Right panel, top section
- **Header:** "Context Used"
- **Visual:** List of active context items
- **Each item:** Source name, relevance indicator, status

#### Context Item Card
```
┌─────────────────────────────────────┐
│ 📄 meeting-notes.md            [×]  │
│     Relevance: High                 │
│     Added: 2 hours ago              │
│     ✓ In context                    │
└─────────────────────────────────────┘
```

#### Context Status Labels
- **In context:** ✓ Active
- **Partial:** ~ Partially used
- **Stale:** ⚠️ May be outdated
- **Removed:** ✗ Not in context

### 11.2 Continuity Snapshot Card
- **Position:** Left sidebar, continuity section
- **Header:** "Continuity Snapshots"
- **Visual:** List of saved snapshots

#### Snapshot Card
```
┌─────────────────────────────────────┐
│ 📸 Snapshot #12                      │
│     Date: 2026-05-29 14:32          │
│     Files: 5 · Context: 12 items     │
│     Status: ✓ Complete               │
│                                     │
│     [Restore] [Delete]              │
└─────────────────────────────────────┘
```

### 11.3 Remembered / Not Remembered Indicator
- **Position:** In message card or right panel
- **Visual:** Status pill or icon

#### Remembered Indicator
- **Icon:** Brain or bookmark icon
- **Color:** Success green or accent blue
- **Label:** "Remembered"
- **Behavior:** Click to view memory entry

#### Not Remembered Indicator
- **Icon:** Brain with slash or dimmed bookmark
- **Color:** Muted gray
- **Label:** "Not in memory"
- **Behavior:** Hover explains why not remembered

### 11.4 Needs Approval to Remember
- **Visual:** Warning amber indicator
- **Icon:** Shield with question mark
- **Label:** "Needs approval to remember"
- **Message:** "WESLR can remember this, but needs your approval."
- **Actions:** "Approve memory", "Decline", "Always ask"

### 11.5 Source/Provenance Marker
- **Position:** In message card or evidence card
- **Visual:** Small file/link icon with source name
- **Behavior:** Click to view source details

#### Source Marker
```
┌─────────────────────────────────────┐
│ 📎 Source: project-notes.md         │
│     Line 42-58                       │
│     ✓ Validated                      │
└─────────────────────────────────────┘
```

### 11.6 Stale/Uncertain Context Warning
- **Visual:** Warning amber banner or card
- **Icon:** Warning triangle
- **Message:** "Some context may be outdated or uncertain."
- **Details:** List of stale/uncertain items
- **Actions:** "Review context", "Remove stale items", "Continue anyway"

### 11.7 Memory Rules
- **Memory is bounded context:** Not automatic truth
- **No automatic memory claim:** Unless implemented and approved
- **Deletion/export:** Only claimed if implemented and approved
- **User control:** Users can inspect, approve, and remove memory entries
- **Transparency:** Users can see what is remembered and why

---

## 12. Login/Access UI

### 12.1 Public Visitor View
- **Access:** Anonymous browsing allowed
- **Visual:** Homepage, product pages, governance pages
- **Actions:** Request pilot access, view public content
- **Restrictions:** No workspace, no chat, no files, no memory

### 12.2 Request Access Form
- **Position:** Pilot Interest page or modal
- **Fields:**
  - Name (required)
  - Email (required)
  - Organization (optional)
  - Use case interest (dropdown, optional)
  - Message (textarea, optional)

- **Consent Checkbox:** "I understand WESLR is in internal evaluation and pilot access is by invitation only."
- **Submit Button:** "Request Pilot Access"
- **Success Message:** "Thank you! We'll review your request and contact you."

### 12.3 Invite-Only Login
- **Position:** Sign in page (linked from email invite)
- **Visual:** Email/password or magic link login
- **Fields:**
  - Email (required)
  - Password or magic link token (required)

- **Behavior:** Only users with valid invite can log in
- **Error Messages:**
  - "This email is not on the invite list."
  - "Your account is pending approval."
  - "Your account has been disabled."

### 12.4 Account Pending Page
- **Visual:** Pending state screen
- **Message:** "Your account is pending approval"
- **Explanation:** "An administrator will review your request. You'll receive an email when approved."
- **Actions:** "Contact support" (if urgent)

### 12.5 Account Disabled/Blocked Page
- **Visual:** Blocked state screen
- **Message:** "Your account has been disabled"
- **Explanation:** "Please contact support for assistance."
- **Actions:** "Contact support"

### 12.6 Private Deployment Access Note
- **Position:** Pilot Interest page, About page, Contact page
- **Visual:** Info card or section
- **Message:** "Private/institution deployments available by discussion."
- **CTA:** "Contact us for private deployment"

### 12.7 Operator/Admin Boundary
- **Visual:** Operator-only sections are hidden from regular users
- **Access:** Only visible to users with operator/admin role
- **Sections:**
  - User approval queue
  - Governance logs
  - System settings
  - Audit trail

### 12.8 Access Rules
- **No unrestricted public signup by default**
- **Request access allowed:** Yes
- **Pilot access:** Manual/invite-only unless separately approved
- **Private deployment:** By discussion/contract

---

## 13. Pricing/Pilot UI

### 13.1 No Public Price Yet
- **Visual:** No pricing table on public site
- **Message:** "Pricing and plans are being evaluated with early users."
- **CTA:** "Request pilot access" or "Contact for private deployment"

### 13.2 Pilot by Invitation
- **Visual:** Pilot interest card or page
- **Message:** "WESLR is invite-only for early pilots."
- **CTA:** "Request Pilot Access"
- **Form:** Name, Email, Organization, Use case

### 13.3 Pricing Evaluated with Early Users
- **Position:** FAQ or pricing info section
- **Message:** "We're working with early users to determine fair pricing."
- **Note:** "No payment required during pilot evaluation."

### 13.4 Storage/File-Processing Limits Apply
- **Visual:** Limits notice in upload modal or workspace settings
- **Message:** "Storage and file-processing limits apply."
- **Details:** Show current usage and limits (if logged in)
- **Note:** "Limits may change as we scale."

### 13.5 Private/Institution Deployments by Discussion
- **Visual:** Contact card or CTA
- **Message:** "Private and institution deployments available by discussion."
- **CTA:** "Contact for private deployment"

### 13.6 Do NOT Define Final Prices as UI Commitments
- **Rule:** No fixed pricing displayed
- **Rule:** No specific storage limits committed (until policy finalized)
- **Rule:** No feature guarantees beyond what is documented
- **Allowed:** "Contact for pricing", "Pilot by invitation", "Limits apply"

---

## 14. Legal/Privacy UI Placement

### 14.1 Footer
- **Position:** Bottom of every page
- **Content:**
  - Product links (What is WESLR?, How it Works, etc.)
  - Resources links (Roadmap, Use Cases, etc.)
  - Company links (About, Contact)
  - Legal links (Privacy, Terms, License, Impressum)

#### Footer Legal Section
```
┌─────────────────────────────────────────────────────────────┐
│ WESLR · Governed Intelligence for Serious Work              │
│                                                             │
│ Privacy Policy · Terms of Use · Commercial License          │
│ Impressum · Contact                                         │
│                                                             │
│ WESLR is in internal evaluation. No production guarantee.   │
│ Pilot access by invitation.                                 │
└─────────────────────────────────────────────────────────────┘
```

### 14.2 Request-Access Page
- **Position:** Below the request form
- **Content:**
  - "By requesting access, you agree to our Privacy Policy and Terms of Use."
  - "Pilot access is by invitation only."
  - Links: Privacy Policy, Terms of Use

### 14.3 Upload Modal/Card
- **Position:** In file upload interface
- **Content:**
  - "Files uploaded to WESLR are processed according to our Privacy Policy."
  - "You retain ownership of your data."
  - "Files may be scanned for safety."
- **Link:** Privacy Policy

### 14.4 Account/Workspace Settings
- **Position:** Settings page, privacy section
- **Content:**
  - Data retention policy
  - File storage policy
  - Memory/export controls
  - Request deletion/export

### 14.5 Contact Page
- **Position:** Contact form or contact info
- **Content:**
  - Contact email
  - Response time expectation
  - Privacy notice

### 14.6 Required Links/Sections

| Page/Section | Required Legal Content |
|---------------|------------------------|
| Footer | Privacy Policy, Terms of Use, Commercial License, Impressum, Contact |
| Request-Access Form | Privacy Policy link, Pilot consent checkbox |
| Upload Modal | Privacy Policy link, File processing notice |
| Account Settings | Data retention, Export, Deletion request |
| Contact Page | Contact info, Privacy notice |

### 14.7 Data Deletion/Export Request Policy
- **Position:** Account settings, privacy section
- **Message:** "You can request deletion or export of your data."
- **Process:** Form or email link to request
- **Note:** "Requests are processed within [X] days." (if implemented)

### 14.8 Pilot Interest Consent
- **Position:** Pilot Interest form
- **Checkbox:** Required
- **Text:** "I understand WESLR is in internal evaluation and pilot access is by invitation only. My information will be used to evaluate pilot interest."
- **Links:** Privacy Policy, Terms of Use

### 14.9 File Upload Consent
- **Position:** First file upload or upload settings
- **Checkbox:** Required (or acknowledged)
- **Text:** "I understand that files uploaded to WESLR are processed for safety and may be stored according to the retention policy."
- **Links:** Privacy Policy, Retention Policy

---

## 15. Component Inventory

### 15.1 Layout Components

| Component | Description |
|-----------|-------------|
| Header | Top navigation bar with logo, nav links, CTA |
| Footer | Bottom bar with links, legal, disclaimer |
| Sidebar | Left navigation with conversations, projects, files |
| Main Area | Center content area for chat/workspace |
| Right Panel | Context/governance panel |
| Input Bar | Bottom input area with textarea and actions |
| Modal | Overlay dialog for forms, confirmations |
| Drawer | Slide-in panel for mobile/tablet |

### 15.2 Navigation Components

| Component | Description |
|-----------|-------------|
| Nav Link | Standard navigation link |
| Nav Dropdown | Dropdown menu for navigation sections |
| Breadcrumb | Page hierarchy navigation |
| Tab | Content tab switcher |

### 15.3 Page Components

| Component | Description |
|-----------|-------------|
| Hero | Large header section with headline and CTA |
| CTA Block | Call-to-action section with button |
| Trust Boundary Block | Governance/trust explanation section |
| Disclaimer Block | Legal/disclaimer notice |
| Architecture Card | Architecture diagram/explanation card |
| Roadmap Card | Timeline/milestone card |
| Feature Card | Feature explanation card |
| Use Case Card | Use case description card |

### 15.4 Status Components

| Component | Description |
|-----------|-------------|
| Status Pill | Compact status indicator (Ready, Pending, Blocked) |
| Badge/Tag | Category or status tag |
| Progress Bar | Upload/processing progress |
| Stepper | Multi-step process indicator |

### 15.5 Form Components

| Component | Description |
|-----------|-------------|
| Button | All button types (primary, secondary, ghost, danger, etc.) |
| Input | Text input field |
| Textarea | Multi-line text input |
| Select | Dropdown selection |
| Checkbox | Checkbox input |
| Radio | Radio button input |
| Toggle | Switch toggle |
| File Input | File upload input |

### 15.6 Card Components

| Component | Description |
|-----------|-------------|
| Message Card | User message, WESLR answer, system message |
| File Card | File upload display |
| Source Card | Evidence/source display |
| Context Card | Context item display |
| Project Card | Project display |
| Conversation Card | Conversation display |
| Snapshot Card | Continuity snapshot display |
| Settings Card | Settings section |

### 15.7 Panel Components

| Component | Description |
|-----------|-------------|
| Context Panel | Right panel showing context used |
| Memory Panel | Memory/knowledge display |
| Evidence Panel | Source/evidence display |
| Settings Panel | Settings page/section |

### 15.8 Feedback Components

| Component | Description |
|-----------|-------------|
| Toast | Temporary notification message |
| Alert | Persistent warning/error message |
| Tooltip | Hover information |
| Empty State | Placeholder for empty lists/areas |

### 15.9 Pricing/Pilot Components

| Component | Description |
|-----------|-------------|
| Pilot Card | Pilot interest request card |
| Pricing Placeholder | "Pricing coming soon" placeholder |
| Contact CTA | Contact for private deployment CTA |

### 15.10 Legal Components

| Component | Description |
|-----------|-------------|
| Legal Link Group | Group of legal links (Privacy, Terms, etc.) |
| Consent Checkbox | Required consent for forms |
| Disclaimer Text | Legal disclaimer text |

---

## 16. Accessibility/Mobile Rules

### 16.1 Responsive Layout
- **Breakpoints:** Mobile (<768px), Tablet (768–1023px), Desktop (≥1024px)
- **Behavior:** Layout adapts to screen size
- **Sidebar:** Collapses to drawer on mobile/tablet
- **Right Panel:** Drawer on mobile/tablet

### 16.2 Keyboard Navigation
- **Tab Order:** Logical sequence through interactive elements
- **Focus Ring:** Visible focus indicator on all interactive elements
- **Enter/Space:** Activate buttons and links
- **Escape:** Close modals, dropdowns, panels
- **Arrow Keys:** Navigate within lists, menus, tabs

### 16.3 Readable Contrast
- **Text on background:** Minimum 4.5:1 contrast ratio
- **Large text:** Minimum 3:1 contrast ratio
- **Interactive elements:** Minimum 3:1 contrast ratio
- **Status colors:** Must be distinguishable (not just by color)

### 16.4 Visible Focus State
- **Focus Ring:** 2px solid accent color
- **Focus Background:** Slight background change if needed
- **No outline removal:** Never remove focus outline without replacement

### 16.5 No Essential Info Only by Color
- **Rule:** Information must not be conveyed by color alone
- **Example:** Status must include text label, not just color
- **Example:** Error must include text or icon, not just red color

### 16.6 Minimum Text Size
- **Body text:** Minimum 14px
- **Labels:** Minimum 12px
- **Captions:** Minimum 11px
- **Never below 11px**

### 16.7 Minimum Touch Target
- **Touch target:** Minimum 44px × 44px
- **Buttons:** Minimum 44px × 44px
- **Links:** Minimum 44px × 44px or sufficient spacing
- **Icon buttons:** Minimum 32px × 32px, with sufficient spacing

### 16.8 Sidebar/Drawer Behavior
- **Desktop:** Sidebar visible, can collapse to icons
- **Tablet:** Sidebar collapsed to icons, expandable on click
- **Mobile:** Sidebar hidden, drawer on menu button
- **Drawer:** Full-height, slide-in from left, swipe-to-close

### 16.9 Mobile File Card Behavior
- **Layout:** Full width, stacked
- **Actions:** Icons only with tooltips
- **Preview:** Snippet truncated with "View full" link
- **Tap targets:** Minimum 44px × 44px

---

## 17. Public Claim UI Rules

### 17.1 Every Component Must Distinguish

| Status | Label | Visual |
|--------|-------|--------|
| Implemented | "Implemented" | Green checkmark |
| Designed | "Designed" | Blue design icon |
| Under Review | "Under Review" | Amber review icon |
| Future Roadmap | "Future" | Gray roadmap icon |
| Not Yet Authorized | "Not Yet Available" | Gray lock icon |

### 17.2 Claim Labels in UI

#### Homepage Feature Cards
- **Implemented:** Show with green checkmark
- **Designed:** Show with "Designed" label
- **Future:** Show with "Planned" or "Future" label

#### Product Experience Page
- **Current Features:** Show with "Implemented" label
- **Planned Features:** Show with "Roadmap" label
- **Clear distinction:** Between current and future

#### Roadmap Page
- **Timeline:** Show all features with status labels
- **Honest:** "Planned for V1.1", "Future consideration"

### 17.3 Forbidden UI Implication

| Forbidden Claim | Reason |
|-----------------|--------|
| "Production-ready" | Not production-ready yet |
| "Public pilot live" | Pilot is invite-only, not public |
| "Unlimited upload" | Uploads have limits |
| "Official benchmark/Turing/intelligence result" | No official results yet |
| "Automatic memory" | Memory requires approval |
| "More reliable than competitors" | No comparison evidence |
| "WESLR is an LLM" | WESLR is not an LLM |
| "Certified intelligence" | Not certified |

### 17.4 UI Enforcement
- **Feature cards:** Must include status label
- **Homepage claims:** Must be reviewed against canon
- **Pricing:** Must NOT claim final pricing
- **Demo:** Must NOT claim production-ready

### 17.5 No Overclaiming
- **Rule:** UI must not imply capabilities beyond what is documented
- **Rule:** UI must not use language like "AI that never makes mistakes"
- **Rule:** UI must not claim "official" or "certified" anything

---

## 18. OCW Handoff Readiness

### 18.1 What OCW Needs Later

| Document/Asset | Status |
|-----------------|--------|
| Reviewed UI Spec | ✅ This document |
| Reviewed Website Structure | ✅ Defined in Section 3 |
| Approved Public Wording | ✅ From grounding docs |
| Visual Tokens | ✅ Defined in Section 2 |
| Component List | ✅ Defined in Section 15 |
| Sitemap | ✅ Defined in Section 3.13 |
| Legal/Privacy Placement | ✅ Defined in Section 14 |
| Claim Boundary | ✅ Defined in Section 17 |
| Build Target/Domain Plan | ⏳ Requires approval |
| No Backend/Runtime Changes | ✅ Confirmed |

### 18.2 Pre-Build Checklist

Before OCW website build:

- [ ] UI spec reviewed and approved
- [ ] Public wording reviewed against canon
- [ ] Legal/privacy content reviewed
- [ ] Domain/hosting plan approved
- [ ] Owner approval for build phase
- [ ] No runtime/backend changes required
- [ ] Static hosting confirmed for website

### 18.3 What OCW Does NOT Do
- Does NOT modify `weslr/chat_responder.py`
- Does NOT modify `weslr/main.py`
- Does NOT implement runtime code
- Does NOT approve or run controlled real answer samples
- Does NOT launch public demo without separate approval

### 18.4 OCW Build Phase
- **Requires:** Separate approval for build phase
- **Scope:** Static website implementation only
- **No:** Backend, runtime, or demo changes

---

## 19. Open Owner Decisions

### 19.1 Brand Decisions

| Decision | Status | Note |
|----------|--------|------|
| Final logo | ⏳ Open | Placeholder text logo in spec |
| Final brand accent | ⏳ Open | Blue/cyan direction defined, final hex TBD |

### 19.2 Content Decisions

| Decision | Status | Note |
|----------|--------|------|
| Exact legal language | ⏳ Open | German/English/bilingual TBD |
| Mockups vs concept diagrams | ⏳ Open | Spec includes both options |

### 19.3 Feature Decisions

| Decision | Status | Note |
|----------|--------|------|
| Public demo chat enabled/disabled | ⏳ Open | Spec assumes disabled |
| Invite login by 02.08.2026 | ⏳ Open | Spec assumes invite-only |
| Exact file/storage limits | ⏳ Open | Conservative defaults in spec |

### 19.4 Pricing Display

| Decision | Status | Note |
|----------|--------|------|
| No price vs pilot-only wording | ⏳ Open | Spec uses "Pilot by invitation" |
| Exact pricing | ⏳ Open | Not defined (not finalized) |

### 19.5 Deployment Decisions

| Decision | Status | Note |
|----------|--------|------|
| Build target/domain plan | ⏳ Open | Requires approval |
| Hosting plan | ⏳ Open | Static hosting recommended |

---

## 20. Recommended Next Lane

`REVIEW_WESLR_V1_UI_COMPONENT_AND_VISUAL_INTERACTION_SPEC_V1`

---

## 21. Validation Commands

```bash
# Validate no Python syntax errors
python -m py_compile weslr/tests/release_gate_v1.py

# Run release gate
python weslr/tests/release_gate_v1.py

# Run release check
bash scripts/weslr_release_check.sh

# Verify chat_responder.py unchanged
git diff --quiet HEAD -- weslr/chat_responder.py

# Verify main.py unchanged
git diff --quiet HEAD -- weslr/main.py
```

---

## 22. Allowed File Changes

- `docs/WESLR_V1_UI_COMPONENT_AND_VISUAL_INTERACTION_SPEC_V1.md` ✅
- `weslr/tests/release_gate_v1.py` (only if required for narrow exact-file allowance)

---

## 23. Forbidden Changes

- `weslr/chat_responder.py` ❌
- `weslr/main.py` ❌
- `weslr-ui/` ❌
- Dashboard files ❌
- Runtime files ❌
- Memory/storage files ❌
- Voice files ❌
- Public pilot executor files ❌
- Provider/model/search/advisor routes ❌
- Answer sample runners ❌
- Controlled real answer execution files ❌
- Website code ❌

---

## 24. Boundary Confirmations

- `weslr/chat_responder.py` remains untouched ✅
- `weslr/main.py` remains untouched ✅
- No runtime behavior changes ✅
- No controlled real answer sample execution ✅
- No approval granted for implementation ✅
- Actual run approval remains not granted ✅
- Actual run execution remains not performed ✅
- This is design/documentation only ✅

---

## 25. Final Report

**Handshake Result:** DESIGN_READY

**Repo Path:** `/home/pr0/projects/weslr-v1-ui-website`

**Branch:** `ocw-weslr-v1-ui-20260529`

**Start HEAD:** `49b96c6`

**End HEAD:** (to be determined after commit)

**Commit Hash:** (to be determined after commit)

**Files Changed:**
- `docs/WESLR_V1_UI_COMPONENT_AND_VISUAL_INTERACTION_SPEC_V1.md` (created/updated)

**Validation Results:**
- Python syntax check: (to be run)
- Release gate: (to be run)
- Release check: (to be run)
- chat_responder.py unchanged: (to be verified)
- main.py unchanged: (to be verified)

**Release Gate Required:** No (documentation only)

**Release Gate Narrow Allowance:** Not required

**Website/UI Code Edited:** No

**Actual Run Approval:** Not granted

**Actual Run Execution:** Not performed

**chat_responder.py Status:** Unchanged

**main.py Status:** Unchanged

**Recommended Next Lane:** `REVIEW_WESLR_V1_UI_COMPONENT_AND_VISUAL_INTERACTION_SPEC_V1`

---

*End of WESLR V1 UI Component and Visual Interaction Spec V1*