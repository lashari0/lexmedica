```md
# Step-by-Step Instructions: Converting Current App into a Document-First, Evidence-Based Medical RAG System

This guide provides **explicit, sequential, and trackable instructions** to transform the existing chat-oriented UI into a **document-first, evidence-driven medical application**, without reworking the backend RAG pipeline.

Each step is intentionally incremental so changes can be implemented, reviewed, and validated independently.

---

## STEP 0 — Establish Non-Negotiable Design Principles (Baseline)

Before making UI changes, align on the following constraints. These guide every subsequent step.

- The application **must be document-scoped by default**
- The model **may not answer without visible evidence**
- Refusal is a **valid and visible outcome**
- Evidence visibility > conversational fluency
- UI enforces constraints; backend alone is insufficient

> Do not proceed to Step 1 until these are agreed upon.

---

## STEP 1 — Redefine the Application Entry Point (Remove Chat-First UX)

### What to Change
- Remove or hide any global “New Chat” or empty chat input on the landing page
- Make the **Document Cards view the default entry screen**

### How to Implement
- Route `/` → `/documents`
- Disable chat input unless a document is selected
- Replace any “Ask a question” placeholder with:
  > “Select a document to explore its evidence”

### Acceptance Criteria
- Users cannot initiate a query without selecting a document
- No LLM output appears on the landing page

---

## STEP 2 — Redesign Document Cards (Evidence Signaling)

### What to Change
Each document card must expose **trust-relevant metadata** at a glance.

### Required Fields (Visible on Card)
- Title (max 2 lines, truncated)
- Source / Authority (e.g., WHO, NEJM, FDA)
- Publication Year (large, visually distinct)
- Document Type (badge)
  - Guideline
  - Systematic Review
  - RCT
  - Observational Study
- Jurisdiction (if applicable)

### Optional (Recommended)
- Evidence Tier (icon or color-coded badge)
- Version number
- Superseded / Outdated warning badge

### How to Implement
- Add a metadata row beneath title
- Use subtle visual hierarchy (size, spacing), not decorative color
- Do **not** rely on tooltips for critical metadata

### Acceptance Criteria
- A clinician can assess authority without clicking the card
- Low-quality evidence is visually distinct from guidelines

---

## STEP 3 — Define Clear Sidebar Roles

### Left Sidebar → Filtering & Scope Control

#### What to Add
- Filters for:
  - Document Type
  - Year Range
  - Authority / Source
  - Jurisdiction

#### What to Remove
- Chat history
- Free-text input
- Conversational elements

#### Acceptance Criteria
- Sidebar changes only affect document visibility, not model behavior

---

### Right Sidebar → Document Preview & Metadata

#### What to Add
- On hover or selection:
  - Abstract / Executive Summary
  - Key metadata (date, authority, scope)
  - Warning banners (e.g., “Outdated guideline”)

#### Acceptance Criteria
- Users can decide whether to open a document without guessing

---

## STEP 4 — Convert “Chat” into a Document Workspace

### What to Rename
Replace all instances of:
- “Chat”
- “Ask anything”
- “Conversation”

With:
- “Ask this document”
- “Explore evidence”
- “Document Q&A”

### Layout Requirements
```

[ Document Metadata Header ]
[ Answer Panel (bounded, structured) ]
[ Evidence Panel (citations & excerpts) ]

```

### Acceptance Criteria
- The UI communicates that the document—not the model—is authoritative

---

## STEP 5 — Enforce Document-Scoped Queries (UI-Level)

### What to Change
- Lock the active document context once selected
- Display active document name prominently above the input

### How to Implement
- System prompt: “Answer only using the selected document”
- Disable implicit multi-document retrieval

### UI Copy (Required)
> “Answers are limited to this document unless scope is expanded.”

### Acceptance Criteria
- Model does not reference external documents without explicit user action

---

## STEP 6 — Implement Explicit Scope Expansion (Optional, Controlled)

### What to Add
When a query cannot be answered from the current document:

- Display a prompt:
  > “This question requires evidence from additional documents. Expand scope?”

### User Options
- Cancel
- Expand to selected document types only
- Expand to all documents (advanced)

### Acceptance Criteria
- Scope expansion is always explicit and logged

---

## STEP 7 — Constrain Answer Format (Evidence-First Output)

### Required Output Structure
- Short bullets (3–6 max)
- Each bullet has at least one citation
- No narrative paragraphs by default

### Example
```

• Indicated for condition X in adults [Section 3.2]
• Contraindicated in patients with Y [Table 4]

```

### Acceptance Criteria
- Every factual claim is traceable
- Long-form answers require explicit user request

---

## STEP 8 — Make Refusal a First-Class UI State

### What to Add
When evidence is insufficient:

- Display a neutral, visible refusal block:
```

⚠️ No supporting evidence found in this document.

```

### Do NOT
- Show errors
- Apologize
- Attempt speculative answers

### Acceptance Criteria
- Users see refusal as expected system behavior

---

## STEP 9 — Reframe the References Panel as an Evidence Navigator

### What to Change
- Replace generic citation lists with:
  - Section-level snippets
  - Highlighted quoted text
  - Click-to-scroll behavior

### Acceptance Criteria
- Clicking a citation scrolls to the exact source text
- Evidence is inspectable without leaving the app

---

## STEP 10 — Add Confidence & Evidence Signals

### What to Display (Non-Numeric)
- “3 sections referenced”
- “Evidence conflict detected”
- “Single-source evidence”

### Acceptance Criteria
- Users understand confidence without model self-assessment

---

## STEP 11 — Audit & Logging Hooks (UI-Level)

### What to Log
- Document selected
- Scope expansions
- Refusals
- Answer citations used

### Why
- Regulatory defensibility
- Error analysis
- Model improvement feedback

---

## STEP 12 — Final UX Validation Checklist

Before release, confirm:

- [ ] No query without document context
- [ ] No answer without citation
- [ ] Refusal is visible and non-punitive
- [ ] Evidence is visually dominant
- [ ] Scope changes are explicit

---

## Optional Enhancements (Post-V1)

- Comparison mode (two documents, side-by-side)
- Evidence strength indicators
- SME annotation overlays
- Read-only patient-safe summaries

---

## Final Note

This transformation does **not** reduce LLM capability—it **makes it usable in medicine**.

> A document-first UI is not a limitation.  
> It is the only defensible interface for medical RAG.

Implement these steps sequentially. Do not skip ahead.
```
