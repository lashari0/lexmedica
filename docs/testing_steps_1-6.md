# Testing Guide: Steps 1-6 Implementation

This guide provides step-by-step testing procedures for validating Steps 1-6 of the LexMedica redesign.

## Prerequisites

1. **Backend running**: `cd backend && uvicorn app.main:app --reload`
2. **Frontend running**: `cd frontend && npm run dev`
3. **At least 2-3 documents uploaded** (preferably with different metadata: types, years, authorities)

---

## Step 1: Document-First Entry Point

### Test 1.1: Root Route Redirect
- [ ] Navigate to `http://localhost:3000/`
- [ ] **Expected**: Automatically redirects to `http://localhost:3000/documents`
- [ ] URL should show `/documents`

### Test 1.2: No Query Input on Landing
- [ ] On `/documents` page, verify:
  - [ ] No "Ask a Question" section visible
  - [ ] No query input field
  - [ ] Header shows: "Select a document to explore its evidence"

### Test 1.3: Direct Navigation
- [ ] Navigate directly to `http://localhost:3000/documents`
- [ ] **Expected**: Page loads normally (no redirect loop)

---

## Step 2: Document Cards with Evidence Signaling

### Test 2.1: Document Card Metadata
- [ ] View document cards on `/documents` page
- [ ] **Expected** for each card:
  - [ ] Title displayed (max 2 lines, truncated with ellipsis)
  - [ ] Authority/Source visible (if available)
  - [ ] Publication Year displayed prominently (large, bold)
  - [ ] Document Type badge visible (if available)
  - [ ] Jurisdiction shown (if available)

### Test 2.2: Visual Hierarchy
- [ ] Verify metadata uses size/spacing for hierarchy, not just colors
- [ ] Year should be visually distinct (larger font)
- [ ] Document type badge should be subtle (gray background)

### Test 2.3: Superseded Warning
- [ ] If any document has `superseded: true`, verify:
  - [ ] Yellow warning badge: "⚠️ Outdated Guideline"

---

## Step 3: Sidebar Roles

### Test 3.1: Left Sidebar - Filters
- [ ] Verify left sidebar shows:
  - [ ] "Filters" heading
  - [ ] Document Type checkboxes (if document types exist)
  - [ ] Year Range inputs (Min/Max)
  - [ ] Authority/Source checkboxes (if available)
  - [ ] Jurisdiction checkboxes (if available)
  - [ ] "Clear All" button (when filters are active)

### Test 3.2: Filter Functionality
- [ ] Select a document type filter
  - [ ] **Expected**: Document list updates to show only matching documents
- [ ] Set year range (e.g., 2020-2023)
  - [ ] **Expected**: Only documents in that range are shown
- [ ] Select an authority filter
  - [ ] **Expected**: Only documents from that authority are shown
- [ ] Click "Clear All"
  - [ ] **Expected**: All filters reset, all documents shown

### Test 3.3: Right Sidebar - Document Preview
- [ ] Hover over a document card
  - [ ] **Expected**: Right sidebar shows document preview with:
    - [ ] Title
    - [ ] Authority
    - [ ] Year
    - [ ] Document Type
    - [ ] Jurisdiction
    - [ ] Authors (if available)
- [ ] Click on a document card
  - [ ] **Expected**: Preview persists (doesn't disappear on mouse leave)

### Test 3.4: Three-Column Layout
- [ ] Verify layout:
  - [ ] Left sidebar (3 columns width on large screens)
  - [ ] Main content (6 columns width)
  - [ ] Right sidebar (3 columns width)
- [ ] On mobile/tablet: Layout should stack vertically

---

## Step 4: Document Workspace (Converted from Chat)

### Test 4.1: Navigate to Document Workspace
- [ ] Click on a document card
- [ ] **Expected**: Navigate to `/documents/[document-id]`
- [ ] Verify page shows:
  - [ ] "Document Q&A" heading
  - [ ] Document metadata header with title, authority, year
  - [ ] Blue info box: "Answers are limited to this document unless scope is expanded."

### Test 4.2: Query Input
- [ ] Verify QueryInput shows:
  - [ ] Placeholder: "Ask this document..."
  - [ ] Button text: "Explore" (not "Search")
  - [ ] "Explore evidence:" label for example queries

### Test 4.3: Query Results Structure
- [ ] Submit a query
- [ ] **Expected** results structure:
  - [ ] Document Metadata Header (shows document info)
  - [ ] Answer Panel (bounded, structured)
  - [ ] Evidence Panel (citations & excerpts) - labeled "Evidence" not "Sources"

---

## Step 5: Document-Scoped Queries

### Test 5.1: Document Context Locking
- [ ] On document workspace page (`/documents/[id]`)
- [ ] Submit a query
- [ ] **Expected**:
  - [ ] Query is automatically scoped to selected document
  - [ ] Document name displayed prominently above input
  - [ ] UI copy: "Answers are limited to this document unless scope is expanded."

### Test 5.2: Scoped Query Verification
- [ ] Query a document that you know contains specific content
- [ ] **Expected**: Results only reference that document (check citations)
- [ ] Check browser DevTools Network tab:
  - [ ] Request to `/api/queries` includes `document_id` parameter

### Test 5.3: Cannot Query Without Document
- [ ] Verify you cannot access query functionality from `/documents` page
- [ ] Query input only available in document workspace page

---

## Step 6: Explicit Scope Expansion

### Test 6.1: Insufficient Evidence Detection
- [ ] On document workspace page, query something that won't be in that document
  - [ ] Example: Query about "diabetes" in a document about "cardiology"
- [ ] **Expected**: If citations are empty or very few (< 2):
  - [ ] Scope expansion prompt appears

### Test 6.2: Scope Expansion Prompt
- [ ] When prompt appears, verify it shows:
  - [ ] Message: "This question requires evidence from additional documents. Expand scope?"
  - [ ] Current document title displayed
  - [ ] Option: "Expand to Selected Types" with checkboxes
  - [ ] Option: "Expand to All Documents (Advanced)"
  - [ ] Option: "Cancel"

### Test 6.3: Expand to Selected Types
- [ ] In expansion prompt, select one or more document types
- [ ] Click "Expand to Selected Types"
- [ ] **Expected**:
  - [ ] Query re-runs without document_id restriction
  - [ ] Results may include citations from other documents
  - [ ] Document metadata header removed (if expanded)
  - [ ] Console logs scope expansion event

### Test 6.4: Expand to All Documents
- [ ] Click "Expand to All Documents (Advanced)"
- [ ] **Expected**:
  - [ ] Query re-runs across all documents
  - [ ] Results include citations from multiple documents
  - [ ] Document metadata header removed
  - [ ] Console logs scope expansion

### Test 6.5: Cancel Expansion
- [ ] Click "Cancel" in expansion prompt
- [ ] **Expected**: Prompt dismisses, no query re-runs

### Test 6.6: Scope Expansion Logging
- [ ] Check browser console:
  - [ ] Verify `[Scope Expansion]` logs when expanding
  - [ ] Logs should include: original document, query, expansion type
- [ ] Check backend logs:
  - [ ] Verify scope info logged: `scope: document_id=...` or `scope: all documents`

---

## Integration Tests

### Test A: Full Document Workflow
1. [ ] Navigate to `/documents`
2. [ ] Filter documents by type (e.g., "Guideline")
3. [ ] Hover over a document → preview appears in right sidebar
4. [ ] Click document → navigate to workspace
5. [ ] Submit query → get scoped results
6. [ ] If insufficient evidence → expansion prompt appears
7. [ ] Expand scope → get multi-document results

### Test B: Multiple Document Types
- [ ] Upload documents with different types (Guideline, RCT, etc.)
- [ ] Verify document type badges display correctly
- [ ] Filter by document type → only matching documents shown
- [ ] Expand scope to selected types → only those types included

### Test C: Edge Cases
- [ ] Document with no metadata → should still work
- [ ] Query with no results → shows refusal/expansion prompt
- [ ] Cancel expansion → returns to document-scoped view
- [ ] New query after expansion → resets to document-scoped

---

## Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if available)

---

## Performance Checks

- [ ] Filtering is responsive (no lag)
- [ ] Document preview on hover is smooth
- [ ] Query results load within reasonable time (< 5 seconds)
- [ ] No console errors or warnings

---

## Issues to Report

If you find any issues during testing, note:
1. **Step affected**: Which step (1-6)
2. **Test case**: Which test failed
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happened
5. **Browser/OS**: Your environment
6. **Console errors**: Any errors in browser console or backend logs

---

## Success Criteria

All steps 1-6 are working correctly if:
- ✅ Users cannot query without selecting a document
- ✅ Document cards show all required metadata prominently
- ✅ Filters work correctly and only affect document visibility
- ✅ Document workspace enforces document-scoped queries
- ✅ Scope expansion is explicit and logged
- ✅ UI clearly communicates document-first, evidence-based approach
