# Frontend Architecture: Document-First Evidence-Based Medical RAG UI

This document describes the frontend architecture for the redesigned document-first, evidence-based medical RAG application.

## Overview

The frontend is built with **Next.js 14** (App Router), **TypeScript**, **Tailwind CSS**, and **React Query** for state management. The UI is designed to enforce document-scoped queries and evidence visibility as core principles.

---

## Architecture Principles

1. **Document-First Entry**: No queries can be initiated without document selection
2. **Evidence Visibility**: All answers must display visible citations
3. **Refusal as Valid State**: Insufficient evidence is displayed neutrally, not as errors
4. **Scope Enforcement**: UI locks document context and makes scope explicit
5. **Trust Signals**: Document cards expose authority, year, type at a glance

---

## Route Structure

### Current Routes
```
/                    → Redirects to /documents (STEP 1)
/documents           → Document library (default entry point)
/documents/[id]      → Document workspace with Q&A (NEW)
```

### Route Behavior
- `/` automatically redirects to `/documents`
- `/documents` is the landing page (no global query input)
- `/documents/[id]` opens the workspace for a specific document

---

## Component Architecture

### Core Layout Components

#### `Layout.tsx`
- Root layout wrapper
- Providers setup (React Query, theme)
- Title bar component

#### `TitleBar` (NEW)
- Application title and branding
- Navigation menu
- User settings (if applicable)

### Document Library Page (`/documents`)

#### `DocumentsPage.tsx`
- Main page component (replaces current `/` home page)
- Three-column layout:
  - **Left Sidebar**: Filters
  - **Center**: Document cards grid
  - **Right Sidebar**: Document preview

#### `DocumentFilters` (NEW - Left Sidebar)
**Purpose**: Filter documents by metadata

**Filters**:
- Document Type (Guideline, RCT, Systematic Review, Observational Study)
- Year Range (slider or min/max inputs)
- Authority/Source (multi-select: WHO, NEJM, FDA, etc.)
- Jurisdiction (if applicable)

**Implementation**:
- Uses React Query to filter documents client-side or fetch filtered list
- Maintains filter state in URL query params for shareability
- Clear visual indication of active filters

#### `DocumentCardGrid` (NEW - Center)
**Purpose**: Display documents in an evidence-signaling grid

**Card Design** (STEP 2):
```
┌─────────────────────────────────┐
│ Title (2 lines max, truncated)  │
│ ─────────────────────────────── │
│ WHO • 2023                      │
│ [Guideline] [Evidence Tier Badge]│
│ Jurisdiction: USA               │
└─────────────────────────────────┘
```

**Required Metadata on Card**:
- Title (max 2 lines)
- Authority/Source (prominent)
- Publication Year (large, distinct)
- Document Type (badge)
- Jurisdiction (if applicable)

**Optional Metadata**:
- Evidence Tier (color-coded badge)
- Version number
- Superseded/Outdated warning

**Interactions**:
- Click: Navigate to `/documents/[id]`
- Hover: Show preview in right sidebar

#### `DocumentPreview` (NEW - Right Sidebar)
**Purpose**: Show document details on hover/selection

**Displays**:
- Abstract / Executive Summary (truncated)
- Key metadata (publication date, authority, scope)
- Warning banners (e.g., "Outdated guideline")
- Document stats (page count, sections)

**Implementation**:
- Shows on hover or selection
- Sticky when document is selected
- Clicking "Open Document" navigates to workspace

### Document Workspace Page (`/documents/[id]`)

#### `DocumentWorkspace.tsx` (NEW)
**Purpose**: Document-scoped Q&A interface

**Layout** (STEP 4):
```
┌─────────────────────────────────────────┐
│ [ Document Metadata Header ]            │
│ Active: "WHO Guidelines 2023"           │
│ ─────────────────────────────────────── │
│ [ Query Input - Document Scoped ]       │
│ "Ask this document" placeholder         │
│ ─────────────────────────────────────── │
│ [ Answer Panel - Evidence First ]       │
│ • Bullet 1 [Section 3.2]                │
│ • Bullet 2 [Table 4]                    │
│ ─────────────────────────────────────── │
│ [ Evidence Panel - Citations ]          │
│ Section snippets with quotes            │
└─────────────────────────────────────────┘
```

**Components**:
- `DocumentHeader`: Shows active document name, metadata
- `ScopedQueryInput`: Query input with document context locked
- `EvidenceAnswer`: Structured answer with citations
- `EvidenceNavigator`: Interactive citations with snippets

#### `DocumentHeader` (NEW)
**Displays**:
- Document title and key metadata
- Scope indicator: "Answers limited to this document unless scope is expanded"
- Change document link

#### `ScopedQueryInput` (MODIFIED from QueryInput)
**Changes from Current**:
- Placeholder: "Ask this document..." (not "Ask a question...")
- Disabled state until document is selected
- Shows active document name above input
- Visual indicator of document scope lock

**API Call**:
- Sends `document_id` in query request
- Backend filters to single document

#### `EvidenceAnswer` (MODIFIED from QueryResults)
**Structure** (STEP 7):
- Short bullets (3-6 max)
- Each bullet has at least one citation `[Section X]`
- No narrative paragraphs by default
- Evidence count: "3 sections referenced"

**Refusal State** (STEP 8):
```
┌─────────────────────────────────┐
│ ⚠️ No supporting evidence found │
│    in this document.            │
└─────────────────────────────────┘
```
- Neutral, non-apologetic
- Not an error state
- Actionable: "Try expanding scope?"

#### `EvidenceNavigator` (MODIFIED from CitationCard) - STEP 9
**Purpose**: Interactive evidence inspection

**Features**:
- Section-level snippets (not just metadata)
- Highlighted quoted text from document
- Click-to-scroll to source location
- Visual connection between citation and answer bullet

**Implementation**:
- Stores document chunk text with citations
- Displays snippet preview
- Supports scrolling to chunk in full document view (future)

### Supporting Components

#### `DocumentCard` (ENHANCED)
**Current State**: Basic filename and date display
**New State**: Rich metadata card (STEP 2)

**Props**:
```typescript
interface DocumentCardProps {
  document: Document;
  onSelect: (id: string) => void;
  onHover?: (id: string) => void;
}

interface Document {
  id: string;
  title: string;
  authority: string;        // NEW
  publicationYear: number;  // NEW
  documentType: string;     // NEW: 'Guideline' | 'RCT' | ...
  jurisdiction?: string;    // NEW
  evidenceTier?: string;    // NEW
  isSuperseded?: boolean;   // NEW
  // ... existing fields
}
```

#### `LoadingSpinner`
- Unchanged, used throughout

#### `DocumentUpload`
- May move to settings/admin section
- Not primary entry point

---

## State Management

### React Query Keys

```typescript
// Document list with filters
['documents', { filters }]

// Single document
['document', documentId]

// Document-scoped query
['query', documentId, queryText]

// Filtered documents
['documents', filterParams]
```

### Local State (useState)

**DocumentsPage**:
- `selectedDocumentId: string | null`
- `hoveredDocumentId: string | null`
- `activeFilters: FilterState`

**DocumentWorkspace**:
- `currentQuery: string`
- `scopeExpanded: boolean`

### URL State (Next.js Router)

- Document selection: `/documents/[id]`
- Filters: `/documents?type=Guideline&year=2023`

---

## API Integration

### Modified API Client (`lib/api.ts`)

**New Methods**:
```typescript
// Document-scoped query
queryDocument(documentId: string, query: string): Promise<QueryResponse>

// Enhanced document with metadata
getDocument(id: string): Promise<EnhancedDocument>

// Filtered document list
listDocuments(filters?: FilterParams): Promise<DocumentListResponse>
```

**Modified Types**:
```typescript
interface QueryRequest {
  query: string;
  document_id?: string;  // NEW: for scoped queries
  top_k?: number;
}

interface Document {
  // ... existing fields
  metadata: {
    title?: string;
    authority?: string;      // NEW
    publicationYear?: number; // NEW
    documentType?: string;    // NEW
    jurisdiction?: string;    // NEW
    evidenceTier?: string;    // NEW
    abstract?: string;        // NEW
  };
}
```

---

## UI/UX Patterns

### Evidence Signals (STEP 10)

**Display Format**:
- "3 sections referenced" (not confidence percentage)
- "Evidence conflict detected" (when multiple sources differ)
- "Single-source evidence" (one section only)

### Scope Expansion (STEP 6)

**Trigger**: When query cannot be answered from current document

**UI**:
```
┌─────────────────────────────────────────┐
│ This question requires evidence from    │
│ additional documents. Expand scope?     │
│                                         │
│ [Cancel] [Expand to Guidelines] [All]  │
└─────────────────────────────────────────┘
```

**Implementation**:
- Backend detects insufficient evidence
- UI shows modal/panel for user choice
- Logs scope expansion event (STEP 11)

### Visual Hierarchy

**Colors**:
- Evidence panels: Subtle background (gray-50)
- Citations: Blue accent for links
- Warnings: Yellow-100 background (not red)
- Refusal: Neutral gray (not error red)

**Typography**:
- Document titles: Large, bold
- Authority/Year: Prominent, distinct size
- Evidence snippets: Monospace for code/quotes
- Citations: Smaller, linked

---

## Acceptance Criteria

### Entry Point (STEP 1)
- [ ] `/` redirects to `/documents`
- [ ] No query input on `/documents` page
- [ ] Message: "Select a document to explore its evidence"

### Document Cards (STEP 2)
- [ ] Authority, year, type visible without hover
- [ ] Low-quality evidence visually distinct from guidelines
- [ ] Truncated titles (max 2 lines)

### Sidebars (STEP 3)
- [ ] Left: Filters (type, year, authority, jurisdiction)
- [ ] Right: Preview on hover/selection
- [ ] No chat history or conversational elements

### Document Workspace (STEP 4-5)
- [ ] "Ask this document" placeholder
- [ ] Active document name prominently displayed
- [ ] Scope indicator: "Answers limited to this document..."
- [ ] Document context locked

### Evidence Display (STEP 7-9)
- [ ] Bulleted answers (3-6 max)
- [ ] Each bullet has citation `[Section X]`
- [ ] Evidence navigator with snippets
- [ ] Clickable citations

### Refusal State (STEP 8)
- [ ] Neutral refusal block (not error)
- [ ] "No supporting evidence found in this document"
- [ ] Actionable options (expand scope?)

### Confidence Signals (STEP 10)
- [ ] "X sections referenced" (non-numeric)
- [ ] "Evidence conflict detected" when applicable
- [ ] No model self-assessment percentages

---

## Future Enhancements

- Comparison mode (two documents side-by-side)
- Evidence strength indicators (visual)
- SME annotation overlays
- Read-only patient-safe summaries
- Full document viewer with scroll-to-citation
- Evidence conflict resolution UI

---

## Migration Notes

### Current → New

1. **`page.tsx` (home)**: Move to admin/settings, redirect `/` → `/documents`
2. **`QueryInput`**: Rename props, add document_id requirement
3. **`QueryResults`**: Restructure as `EvidenceAnswer` with bullets
4. **`CitationCard`**: Enhance to `EvidenceNavigator` with snippets
5. **`DocumentList`**: Transform to `DocumentCardGrid` with rich metadata

### Breaking Changes

- Query API now requires `document_id` for most queries
- Document model includes new metadata fields
- Answer format changed from paragraphs to bullets
- Routing: `/` no longer shows query interface

---

## Implementation Order

Follow the steps in `app_design2.md` sequentially:

1. **STEP 1**: Route changes, remove query from landing
2. **STEP 2**: Enhanced document cards
3. **STEP 3**: Sidebar components (filters + preview)
4. **STEP 4-5**: Document workspace with scoped queries
5. **STEP 6**: Scope expansion UI (optional)
6. **STEP 7-9**: Evidence-first answer format
7. **STEP 10-11**: Signals and logging

Each step is independently testable and reviewable.
