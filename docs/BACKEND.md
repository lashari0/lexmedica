# Backend Architecture & Workflow

## Overview

The backend is a **FastAPI-based RAG (Retrieval-Augmented Generation) system** designed to process medical research PDFs and answer natural language queries using AI. It implements a complete document ingestion and query pipeline with vector search capabilities.

## Core Purpose

The backend serves as the **Medical Research Knowledge Assistant API**, enabling:

1. **Document Ingestion**: Upload, process, and index medical research PDFs
2. **Semantic Search**: Find relevant content using vector similarity search
3. **AI-Powered Q&A**: Generate answers to questions using retrieved context and LLMs
4. **Metadata Management**: Extract and store document metadata (title, authors, journal, DOI, etc.)

## Architecture Components

### 1. API Layer (`app/api/`)

**Documents API** (`documents.py`):
- `POST /api/documents/upload` - Upload and process PDF documents
- `GET /api/documents` - List all uploaded documents
- `GET /api/documents/{id}` - Get document details with chunks
- `DELETE /api/documents/{id}` - Delete document and all its chunks

**Queries API** (`queries.py`):
- `POST /api/queries` - Query documents using RAG pipeline
- `GET /api/queries/history` - Get query history
- `POST /api/queries/export` - Export query results

### 2. Service Layer (`app/services/`)

**PDFProcessor** (`pdf_processor.py`):
- Extracts text from PDF files using `pdfplumber` and `PyPDF2`
- Detects if OCR is needed for scanned documents
- Saves uploaded files to disk

**Chunker** (`chunker.py`):
- Splits documents into semantic chunks (paragraphs, sentences)
- Configurable chunk size (default: 500 chars) and overlap (default: 50 chars)
- Preserves document structure and context

**EmbeddingService** (`embeddings.py`):
- Generates text embeddings using `sentence-transformers`
- Default model: `all-MiniLM-L6-v2`
- Supports batch processing for efficiency

**VectorStore** (`vector_store.py`):
- Manages ChromaDB vector database
- Stores document chunks with embeddings
- Performs similarity search for retrieval
- Handles document deletion and chunk retrieval

**LLMService** (`llm_service.py`):
- Generates answers using LLMs (Ollama or Hugging Face API)
- Builds prompts with retrieved context
- Handles different LLM providers and response formats

**MetadataExtractor** (`metadata_extractor.py`):
- Extracts title, authors, journal, year, and DOI from document text
- Uses regex patterns and heuristics for medical literature

### 3. Data Models (`app/models/`)

- `QueryRequest` - Query input with optional top_k parameter
- `QueryResponse` - Answer with citations and confidence score
- `Citation` - Source citation with document ID, chunk index, and similarity score
- `QueryHistoryEntry` - Historical query record

## Workflow

### Document Upload Workflow

```
1. File Upload
   ↓
2. Validation (PDF format, size, non-empty)
   ↓
3. PDF Processing (text extraction)
   ↓
4. Chunking (split into semantic units)
   ↓
5. Embedding Generation (vectorize chunks)
   ↓
6. Metadata Extraction (title, authors, etc.)
   ↓
7. Vector Storage (store in ChromaDB)
   ↓
8. Document Metadata Storage (in-memory store)
   ↓
9. Return Document ID
```

### Query Workflow (RAG Pipeline)

```
1. Query Input
   ↓
2. Query Embedding (generate vector for query)
   ↓
3. Vector Search (find similar chunks in ChromaDB)
   ↓
4. Context Preparation (format top-k chunks)
   ↓
5. LLM Generation (generate answer with context)
   ↓
6. Citation Building (create citations from results)
   ↓
7. Response (return answer + citations + confidence)
```

## Configuration

All settings are managed through `app/config.py` using Pydantic Settings:

- **API**: Title, version, debug mode
- **Vector DB**: ChromaDB persistence directory
- **Embeddings**: Model name (sentence-transformers)
- **LLM**: Provider (ollama/huggingface), model (qwen3:4b), API keys
- **Retrieval**: Top-k results, similarity threshold
- **File Upload**: Max size, allowed extensions, upload directory
- **CORS**: Allowed origins

## Key Design Decisions

1. **Lazy Service Initialization**: Services in `documents.py` are initialized on-demand to avoid startup failures
2. **Singleton Pattern**: Services are reused across requests for efficiency
3. **In-Memory Document Store**: Currently uses dictionary (will be replaced with database in production)
4. **ChromaDB**: Embedded vector database for simplicity and portability
5. **Modular Services**: Each service is independent and testable
6. **Error Handling**: Comprehensive error handling with helpful messages

## Dependencies

- **FastAPI**: Web framework
- **ChromaDB**: Vector database
- **sentence-transformers**: Embedding generation
- **pdfplumber/PyPDF2**: PDF processing
- **ollama/requests**: LLM integration
- **pydantic**: Data validation

## Current Limitations

1. **In-Memory Storage**: Document metadata stored in memory (not persistent)
2. **No OCR**: Scanned PDFs are detected but not processed
3. **Single Collection**: All documents stored in one ChromaDB collection
4. **No Authentication**: API is open (needs auth for production)
5. **Hardcoded Paths**: Some debug paths are hardcoded (should be configurable)

## Future Enhancements

- Database integration for persistent document storage
- OCR support for scanned PDFs
- Multi-collection support for document organization
- Authentication and authorization
- Rate limiting and request throttling
- Advanced retrieval strategies (reranking, hybrid search)
- Caching for frequently accessed documents

## Testing

Tests are located in `backend/tests/`:
- Unit tests for each service
- Integration tests for API endpoints
- Mock services for isolated testing

## Deployment

The backend is containerized with Docker and can be deployed to:
- Render (recommended for free tier)
- Railway
- AWS/GCP/Azure
- Any platform supporting Docker

Default port: `8000`
