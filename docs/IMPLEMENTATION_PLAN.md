# Backend Implementation Plan

This document outlines a step-by-step plan to implement the backend from scratch, building incrementally from basic functionality to a fully functional RAG system.

## Implementation Strategy

**Approach**: Build incrementally, testing each step before moving to the next. Each step should be functional and testable on its own.

**Testing**: After each step, verify the functionality works before proceeding.

---

## Step 1: Project Foundation & Configuration

**Goal**: Set up the basic project structure and configuration system.

### Tasks:
1. Create `app/` directory structure:
   - `app/__init__.py`
   - `app/config.py`
   - `app/main.py`
   - `app/api/__init__.py`
   - `app/services/__init__.py`
   - `app/models/__init__.py`

2. Implement `app/config.py`:
   - Create `Settings` class using Pydantic Settings
   - Add all configuration fields (API, Vector DB, LLM, etc.)
   - Support `.env` file loading
   - Set sensible defaults

3. Implement `app/main.py`:
   - Create FastAPI app instance
   - Add CORS middleware
   - Add root endpoint (`/`)
   - Add health check endpoint (`/api/health`)
   - Basic error handling

4. Create `requirements.txt` with minimal dependencies:
   - `fastapi`
   - `uvicorn[standard]`
   - `pydantic`
   - `pydantic-settings`
   - `python-multipart`
   - `python-dotenv`

### Verification:
- ✅ Server starts without errors
- ✅ Root endpoint returns response
- ✅ Health check works
- ✅ Configuration loads from `.env` file

### Files Created:
- `app/__init__.py`
- `app/config.py`
- `app/main.py`
- `app/api/__init__.py`
- `app/services/__init__.py`
- `app/models/__init__.py`

---

## Step 2: Basic File Upload (No Processing)

**Goal**: Implement basic file upload endpoint without any processing.

### Tasks:
1. Create `app/api/documents.py`:
   - Implement `POST /api/documents/upload` endpoint
   - Accept file upload (PDF only)
   - Validate file extension
   - Validate file size
   - Save file to `uploads/` directory
   - Return document ID and filename

2. Create `app/models/__init__.py`:
   - Basic response models (if needed)

3. Register router in `app/main.py`

### Verification:
- ✅ Can upload PDF file via API
- ✅ File is saved to `uploads/` directory
- ✅ Invalid files are rejected
- ✅ Returns document ID

### Files Created:
- `app/api/documents.py`
- `app/models/__init__.py` (basic models)

---

## Step 3: PDF Text Extraction

**Goal**: Extract text from uploaded PDFs.

### Tasks:
1. Create `app/services/pdf_processor.py`:
   - Implement `PDFProcessor` class
   - Add `extract_text()` method using `pdfplumber`
   - Add fallback to `PyPDF2` if `pdfplumber` fails
   - Return extracted text and `needs_ocr` flag
   - Handle errors gracefully

2. Update `app/api/documents.py`:
   - Integrate `PDFProcessor` into upload endpoint
   - Extract text after file upload
   - Return text length in response

3. Update `requirements.txt`:
   - Add `pdfplumber`
   - Add `PyPDF2`

### Verification:
- ✅ Text is extracted from PDF
- ✅ Returns text content
- ✅ Handles text-based PDFs
- ✅ Detects scanned PDFs (needs_ocr flag)

### Files Modified:
- `app/api/documents.py`
- `app/services/pdf_processor.py` (new)

---

## Step 4: Document Chunking

**Goal**: Split documents into semantic chunks.

### Tasks:
1. Create `app/services/chunker.py`:
   - Implement `Chunker` class
   - Add `chunk_text()` method
   - Implement paragraph-based chunking
   - Implement sentence-based chunking for large paragraphs
   - Add chunk size and overlap configuration
   - Preserve metadata (document_id, filename, etc.)

2. Update `app/api/documents.py`:
   - Integrate `Chunker` into upload endpoint
   - Chunk extracted text
   - Return number of chunks created

### Verification:
- ✅ Documents are split into chunks
- ✅ Chunks have appropriate size
- ✅ Chunks have overlap
- ✅ Metadata is preserved in chunks

### Files Created:
- `app/services/chunker.py`

### Files Modified:
- `app/api/documents.py`

---

## Step 5: Embedding Generation

**Goal**: Generate vector embeddings for document chunks.

### Tasks:
1. Create `app/services/embeddings.py`:
   - Implement `EmbeddingService` class
   - Load sentence-transformers model (`all-MiniLM-L6-v2`)
   - Add `generate_embedding()` for single text
   - Add `generate_embeddings_batch()` for multiple texts
   - Handle model loading errors

2. Update `app/api/documents.py`:
   - Integrate `EmbeddingService` into upload endpoint
   - Generate embeddings for all chunks
   - Return embedding count

3. Update `requirements.txt`:
   - Add `sentence-transformers`
   - Add `torch` (for sentence-transformers)

### Verification:
- ✅ Embeddings are generated for chunks
- ✅ Embeddings have correct dimensions
- ✅ Batch processing works
- ✅ Model loads successfully

### Files Created:
- `app/services/embeddings.py`

### Files Modified:
- `app/api/documents.py`

---

## Step 6: Vector Database Setup

**Goal**: Set up ChromaDB and store document chunks with embeddings.

### Tasks:
1. Create `app/services/vector_store.py`:
   - Implement `VectorStore` class
   - Initialize ChromaDB client (persistent)
   - Create/get collection
   - Add `add_document_chunks()` method
   - Store chunks with embeddings and metadata
   - Handle ChromaDB errors

2. Update `app/api/documents.py`:
   - Integrate `VectorStore` into upload endpoint
   - Store chunks in ChromaDB after embedding generation
   - Return chunk IDs

3. Create in-memory document store:
   - Add `documents_store` dictionary in `documents.py`
   - Store document metadata (id, filename, uploaded_at, num_chunks)

4. Update `requirements.txt`:
   - Add `chromadb`

5. Create `GET /api/documents` endpoint:
   - List all documents from in-memory store

### Verification:
- ✅ ChromaDB collection is created
- ✅ Chunks are stored with embeddings
- ✅ Document metadata is stored
- ✅ Can list all documents

### Files Created:
- `app/services/vector_store.py`

### Files Modified:
- `app/api/documents.py`

---

## Step 7: Basic Query Endpoint (No LLM)

**Goal**: Implement query endpoint that returns relevant chunks without LLM.

### Tasks:
1. Create `app/api/queries.py`:
   - Implement `POST /api/queries` endpoint
   - Accept query text
   - Generate query embedding
   - Search vector store for similar chunks
   - Return top-k chunks with similarity scores

2. Create `app/models/__init__.py`:
   - Add `QueryRequest` model
   - Add `QueryResponse` model (simplified, no LLM answer yet)
   - Add `Citation` model

3. Update `app/services/vector_store.py`:
   - Add `search()` method
   - Implement similarity search
   - Return results with similarity scores
   - Apply similarity threshold

4. Register router in `app/main.py`

### Verification:
- ✅ Can query documents
- ✅ Returns relevant chunks
- ✅ Similarity scores are calculated
- ✅ Top-k results are returned

### Files Created:
- `app/api/queries.py`

### Files Modified:
- `app/models/__init__.py`
- `app/services/vector_store.py`
- `app/main.py`

---

## Step 8: LLM Integration

**Goal**: Add LLM to generate answers from retrieved chunks.

### Tasks:
1. Create `app/services/llm_service.py`:
   - Implement `LLMService` class
   - Support Ollama provider (local LLM)
   - Support Hugging Face API (fallback)
   - Add `generate_answer()` method
   - Build prompts with context chunks
   - Handle LLM errors gracefully

2. Update `app/api/queries.py`:
   - Integrate `LLMService` into query endpoint
   - Generate answer using retrieved chunks
   - Update `QueryResponse` to include answer
   - Add fallback if LLM fails

3. Update `requirements.txt`:
   - Add `ollama`
   - Add `huggingface-hub`
   - Add `requests`

4. Update `app/config.py`:
   - Add LLM configuration (provider, model, API keys)

### Verification:
- ✅ LLM generates answers
- ✅ Answers include context from chunks
- ✅ Handles LLM errors gracefully
- ✅ Works with both Ollama and Hugging Face

### Files Created:
- `app/services/llm_service.py`

### Files Modified:
- `app/api/queries.py`
- `app/config.py`

---

## Step 9: Metadata Extraction

**Goal**: Extract metadata (title, authors, journal, etc.) from documents.

### Tasks:
1. Create `app/services/metadata_extractor.py`:
   - Implement `MetadataExtractor` class
   - Add `extract_metadata()` method
   - Extract title, authors, journal, year, DOI
   - Use regex patterns and heuristics

2. Update `app/api/documents.py`:
   - Integrate `MetadataExtractor` into upload endpoint
   - Extract metadata after text extraction
   - Store metadata in document store

3. Update document response models:
   - Include metadata in document responses

### Verification:
- ✅ Metadata is extracted from documents
- ✅ Title, authors, journal are detected
- ✅ Year and DOI are extracted
- ✅ Metadata is stored with documents

### Files Created:
- `app/services/metadata_extractor.py`

### Files Modified:
- `app/api/documents.py`
- `app/models/__init__.py`

---

## Step 10: Document Management Endpoints

**Goal**: Complete document management (get, delete).

### Tasks:
1. Update `app/api/documents.py`:
   - Implement `GET /api/documents/{id}` endpoint
   - Return document details with chunks
   - Implement `DELETE /api/documents/{id}` endpoint
   - Delete from vector store
   - Delete from in-memory store
   - Delete uploaded file

2. Update `app/services/vector_store.py`:
   - Add `delete_document()` method
   - Add `get_document_chunks()` method

### Verification:
- ✅ Can get document by ID
- ✅ Can delete document
- ✅ Chunks are removed from vector store
- ✅ File is deleted from disk

### Files Modified:
- `app/api/documents.py`
- `app/services/vector_store.py`

---

## Step 11: Query History & Export

**Goal**: Add query history tracking and export functionality.

### Tasks:
1. Create `app/models/query_history.py`:
   - Implement `QueryHistoryEntry` model
   - Create in-memory query history store

2. Update `app/api/queries.py`:
   - Store queries in history after processing
   - Implement `GET /api/queries/history` endpoint
   - Implement `POST /api/queries/export` endpoint
   - Support markdown and JSON export formats

### Verification:
- ✅ Queries are stored in history
- ✅ Can retrieve query history
- ✅ Can export queries in different formats

### Files Created:
- `app/models/query_history.py`

### Files Modified:
- `app/api/queries.py`

---

## Step 12: Error Handling & Polish

**Goal**: Improve error handling, logging, and code quality.

### Tasks:
1. Add comprehensive error handling:
   - HTTP exceptions with helpful messages
   - Service initialization error handling
   - File processing error handling
   - LLM error handling

2. Add logging:
   - Configure Python logging
   - Add log statements throughout services
   - Log errors with context

3. Improve code quality:
   - Add docstrings to all classes and methods
   - Add type hints where missing
   - Refactor duplicate code
   - Add input validation

4. Update configuration:
   - Make all paths configurable (no hardcoded paths)
   - Add environment variable examples
   - Create `.env.example` file

### Verification:
- ✅ Errors are handled gracefully
- ✅ Error messages are helpful
- ✅ Logging works correctly
- ✅ Code is well-documented

### Files Modified:
- All service files
- All API files
- `app/config.py`

---

## Step 13: Testing Setup

**Goal**: Add unit and integration tests.

### Tasks:
1. Create `tests/` directory structure:
   - `tests/__init__.py`
   - `tests/conftest.py`
   - Test fixtures and mocks

2. Create service tests:
   - `test_pdf_processor.py`
   - `test_chunker.py`
   - `test_embeddings.py`
   - `test_vector_store.py`
   - `test_llm_service.py`
   - `test_metadata_extractor.py`

3. Create API tests:
   - `test_integration.py` (end-to-end tests)

4. Update `requirements.txt`:
   - Add `pytest`
   - Add `pytest-asyncio`
   - Add `pytest-cov`
   - Add `httpx`

5. Create `pytest.ini` configuration

### Verification:
- ✅ All tests pass
- ✅ Test coverage is reasonable (>70%)
- ✅ Integration tests work

### Files Created:
- `tests/` directory with all test files
- `pytest.ini`

---

## Step 14: Docker & Deployment Prep

**Goal**: Prepare for deployment with Docker.

### Tasks:
1. Create `Dockerfile`:
   - Multi-stage build
   - Install dependencies
   - Copy application code
   - Set up working directory
   - Expose port 8000

2. Create `docker-compose.yml` (if needed):
   - Backend service
   - Volume mounts for data persistence

3. Create `.dockerignore`:
   - Exclude unnecessary files

4. Update documentation:
   - Add deployment instructions
   - Add Docker usage examples

### Verification:
- ✅ Docker image builds successfully
- ✅ Container runs without errors
- ✅ API is accessible in container

### Files Created:
- `Dockerfile`
- `.dockerignore`
- `docker-compose.yml` (optional)

---

## Implementation Order Summary

1. ✅ **Step 1**: Project Foundation & Configuration
2. ✅ **Step 2**: Basic File Upload (No Processing)
3. ✅ **Step 3**: PDF Text Extraction
4. ✅ **Step 4**: Document Chunking
5. ✅ **Step 5**: Embedding Generation
6. ✅ **Step 6**: Vector Database Setup
7. ✅ **Step 7**: Basic Query Endpoint (No LLM)
8. ✅ **Step 8**: LLM Integration
9. ✅ **Step 9**: Metadata Extraction
10. ✅ **Step 10**: Document Management Endpoints
11. ✅ **Step 11**: Query History & Export
12. ✅ **Step 12**: Error Handling & Polish
13. ✅ **Step 13**: Testing Setup
14. ✅ **Step 14**: Docker & Deployment Prep

---

## Quick Start Checklist

For each step:
- [ ] Complete all tasks
- [ ] Verify functionality works
- [ ] Test with sample data
- [ ] Commit changes
- [ ] Move to next step

---

## Notes

- **Start Simple**: Each step builds on the previous one. Don't skip ahead.
- **Test Incrementally**: Verify each step works before moving forward.
- **Error Handling**: Add basic error handling from the start, refine in Step 12.
- **Configuration**: Keep configuration flexible from Step 1.
- **Dependencies**: Add dependencies as needed in each step.

---

## Estimated Timeline

- **Steps 1-3**: Foundation (2-3 hours)
- **Steps 4-6**: Core RAG pipeline (3-4 hours)
- **Steps 7-8**: Query & LLM (2-3 hours)
- **Steps 9-11**: Features (2-3 hours)
- **Steps 12-14**: Polish & deployment (3-4 hours)

**Total**: ~12-17 hours for complete implementation
