# Backend Architecture Documentation

This document provides a comprehensive overview of the LexMedica backend architecture, including all services, APIs, and data flows.

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Document Upload Workflow](#document-upload-workflow)
3. [Query Workflow (RAG Pipeline)](#query-workflow-rag-pipeline)
4. [Component Interaction Diagram](#component-interaction-diagram)
5. [Service Dependencies](#service-dependencies)
6. [API Endpoints Overview](#api-endpoints-overview)
7. [Data Flow Summary](#data-flow-summary)

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        Frontend[Next.js Frontend]
    end

    subgraph "API Layer (FastAPI)"
        Main[main.py<br/>FastAPI App]
        DocsAPI[documents.py<br/>Document API]
        QueryAPI[queries.py<br/>Query API]
        Config[config.py<br/>Settings]
    end

    subgraph "Service Layer"
        PDFProc[PDFProcessor<br/>pdf_processor.py]
        Chunker[Chunker<br/>chunker.py]
        EmbedSvc[EmbeddingService<br/>embeddings.py]
        VectorStore[VectorStore<br/>vector_store.py]
        LLMService[LLMService<br/>llm_service.py]
    end

    subgraph "Data Storage"
        FileSystem[File System<br/>uploads/]
        ChromaDB[(ChromaDB<br/>Vector Database)]
        InMemoryStore[In-Memory Store<br/>documents_store]
    end

    subgraph "External Services"
        Ollama[Ollama<br/>Local LLM]
        HuggingFace[Hugging Face API<br/>Cloud LLM]
    end

    Frontend -->|HTTP Requests| Main
    Main -->|Routes| DocsAPI
    Main -->|Routes| QueryAPI
    Main -->|Config| Config

    DocsAPI -->|Uses| PDFProc
    DocsAPI -->|Uses| Chunker
    DocsAPI -->|Uses| EmbedSvc
    DocsAPI -->|Uses| VectorStore
    DocsAPI -->|Stores| FileSystem
    DocsAPI -->|Stores| InMemoryStore

    QueryAPI -->|Uses| EmbedSvc
    QueryAPI -->|Uses| VectorStore
    QueryAPI -->|Uses| LLMService

    PDFProc -->|Reads| FileSystem
    Chunker -->|Processes| PDFProc
    EmbedSvc -->|Generates| Chunker
    VectorStore -->|Stores| ChromaDB
    LLMService -->|Calls| Ollama
    LLMService -->|Calls| HuggingFace

    style Main fill:#4A90E2
    style DocsAPI fill:#7ED321
    style QueryAPI fill:#7ED321
    style PDFProc fill:#F5A623
    style Chunker fill:#F5A623
    style EmbedSvc fill:#F5A623
    style VectorStore fill:#F5A623
    style LLMService fill:#F5A623
    style ChromaDB fill:#BD10E0
    style Ollama fill:#50E3C2
    style HuggingFace fill:#50E3C2
```

---

## Document Upload Workflow

```mermaid
sequenceDiagram
    participant Client
    participant DocsAPI
    participant PDFProc
    participant Chunker
    participant EmbedSvc
    participant VectorStore
    participant FileSystem
    participant ChromaDB
    participant InMemoryStore

    Client->>DocsAPI: POST /api/documents/upload (PDF file)
    DocsAPI->>DocsAPI: Validate file (extension, size)
    DocsAPI->>FileSystem: Save file with UUID
    DocsAPI->>PDFProc: extract_text(file_path)
    PDFProc->>PDFProc: Try pdfplumber
    alt pdfplumber succeeds
        PDFProc-->>DocsAPI: {text, needs_ocr, method}
    else pdfplumber fails
        PDFProc->>PDFProc: Try PyPDF2
        PDFProc-->>DocsAPI: {text, needs_ocr, method}
    end
    
    alt Text extracted successfully
        DocsAPI->>Chunker: chunk_text(text, doc_id, filename)
        Chunker->>Chunker: Split by paragraphs/sentences
        Chunker-->>DocsAPI: List of chunks with metadata
        
        DocsAPI->>EmbedSvc: generate_embeddings_batch(chunk_texts)
        EmbedSvc->>EmbedSvc: Load sentence-transformers model
        EmbedSvc->>EmbedSvc: Encode chunks to vectors
        EmbedSvc-->>DocsAPI: List of embeddings
        
        DocsAPI->>VectorStore: add_document_chunks(doc_id, chunks)
        VectorStore->>ChromaDB: Store chunks with embeddings
        ChromaDB-->>VectorStore: Chunk IDs
        VectorStore-->>DocsAPI: Chunk IDs
    end
    
    DocsAPI->>InMemoryStore: Store document metadata
    DocsAPI-->>Client: DocumentUploadResponse
```

### Upload Flow Steps

1. **File Validation**: Check file extension (.pdf), size (max 10MB), and non-empty
2. **File Storage**: Save PDF to `uploads/` directory with UUID filename
3. **Text Extraction**: Use PDFProcessor (pdfplumber → PyPDF2 fallback)
4. **Chunking**: Split text into semantic chunks (500 chars, 50 overlap)
5. **Embedding Generation**: Generate vector embeddings for each chunk
6. **Vector Storage**: Store chunks with embeddings in ChromaDB
7. **Metadata Storage**: Store document metadata in in-memory store
8. **Response**: Return document ID and processing statistics

---

## Query Workflow (RAG Pipeline)

```mermaid
sequenceDiagram
    participant Client
    participant QueryAPI
    participant EmbedSvc
    participant VectorStore
    participant ChromaDB
    participant LLMService
    participant Ollama

    Client->>QueryAPI: POST /api/queries {query, top_k}
    QueryAPI->>QueryAPI: Validate query text
    
    QueryAPI->>EmbedSvc: generate_embedding(query)
    EmbedSvc->>EmbedSvc: Encode query to vector
    EmbedSvc-->>QueryAPI: Query embedding vector
    
    QueryAPI->>VectorStore: search(query_embedding, top_k)
    VectorStore->>ChromaDB: Query similar chunks
    ChromaDB-->>VectorStore: Top-k results with scores
    VectorStore->>VectorStore: Filter by similarity threshold
    VectorStore-->>QueryAPI: Search results with citations
    
    QueryAPI->>QueryAPI: Limit context chunks (max_context_chunks)
    QueryAPI->>QueryAPI: Truncate chunks (max_chunk_length)
    
    QueryAPI->>LLMService: generate_answer(query, context_chunks)
    LLMService->>LLMService: Build RAG prompt
    alt Provider is Ollama
        LLMService->>Ollama: POST /api/generate
        Ollama-->>LLMService: Generated answer
    else Provider is HuggingFace
        LLMService->>HuggingFace: POST /models/{model}
        HuggingFace-->>LLMService: Generated answer
    end
    LLMService-->>QueryAPI: Answer text
    
    QueryAPI->>QueryAPI: Calculate confidence (top similarity score)
    QueryAPI-->>Client: QueryResponse {answer, citations, confidence}
```

### Query Flow Steps

1. **Query Validation**: Ensure query text is not empty
2. **Query Embedding**: Generate vector embedding for the query
3. **Vector Search**: Search ChromaDB for similar chunks (top-k)
4. **Similarity Filtering**: Filter results by similarity threshold (default: 0.3)
5. **Context Preparation**: Limit and truncate chunks for LLM (max 3 chunks, 300 chars each)
6. **LLM Generation**: Build RAG prompt and generate answer using Ollama/HuggingFace
7. **Response Formatting**: Calculate confidence score and format response with citations

---

## Component Interaction Diagram

```mermaid
graph LR
    subgraph "Document Upload Flow"
        A1[PDF File] --> A2[Validation]
        A2 --> A3[Save to Disk]
        A3 --> A4[Extract Text]
        A4 --> A5[Chunk Text]
        A5 --> A6[Generate Embeddings]
        A6 --> A7[Store in ChromaDB]
        A7 --> A8[Store Metadata]
    end

    subgraph "Query Flow"
        B1[User Query] --> B2[Generate Query Embedding]
        B2 --> B3[Vector Search]
        B3 --> B4[Retrieve Top-K Chunks]
        B4 --> B5[Build Context]
        B5 --> B6[LLM Generation]
        B6 --> B7[Format Response]
    end

    style A1 fill:#E8F4F8
    style B1 fill:#E8F4F8
    style A7 fill:#BD10E0
    style B3 fill:#BD10E0
    style B6 fill:#50E3C2
```

---

## Service Dependencies

```mermaid
graph TD
    subgraph "Core Services"
        S1[PDFProcessor<br/>- extract_text<br/>- detect_ocr_needed]
        S2[Chunker<br/>- chunk_text<br/>- split_into_paragraphs]
        S3[EmbeddingService<br/>- generate_embedding<br/>- generate_embeddings_batch]
        S4[VectorStore<br/>- add_document_chunks<br/>- search<br/>- delete_document]
        S5[LLMService<br/>- generate_answer<br/>- build_rag_prompt]
    end

    subgraph "Dependencies"
        D1[sentence-transformers<br/>all-MiniLM-L6-v2]
        D2[ChromaDB<br/>Persistent Client]
        D3[Ollama API<br/>or HuggingFace API]
        D4[pdfplumber/PyPDF2]
    end

    S1 --> D4
    S3 --> D1
    S4 --> D2
    S5 --> D3

    style S1 fill:#F5A623
    style S2 fill:#F5A623
    style S3 fill:#F5A623
    style S4 fill:#F5A623
    style S5 fill:#F5A623
    style D1 fill:#50E3C2
    style D2 fill:#BD10E0
    style D3 fill:#50E3C2
    style D4 fill:#50E3C2
```

### Service Details

#### PDFProcessor (`pdf_processor.py`)
- **Purpose**: Extract text from PDF files
- **Methods**: 
  - `extract_text(file_path)` - Main extraction method
  - `_extract_with_pdfplumber()` - Primary extraction method
  - `_extract_with_pypdf2()` - Fallback extraction method
  - `_detect_ocr_needed()` - Detect scanned PDFs
- **Dependencies**: pdfplumber, PyPDF2

#### Chunker (`chunker.py`)
- **Purpose**: Split documents into semantic chunks
- **Methods**:
  - `chunk_text(text, document_id, filename)` - Main chunking method
  - `_split_into_paragraphs()` - Split by paragraphs
  - `_split_large_paragraph()` - Split large paragraphs by sentences
  - `_split_by_words()` - Last resort word-based splitting
- **Configuration**: chunk_size (500), chunk_overlap (50)

#### EmbeddingService (`embeddings.py`)
- **Purpose**: Generate vector embeddings for text
- **Methods**:
  - `generate_embedding(text)` - Single text embedding
  - `generate_embeddings_batch(texts)` - Batch embeddings
  - `get_embedding_dimension()` - Get embedding dimension
- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Dependencies**: sentence-transformers

#### VectorStore (`vector_store.py`)
- **Purpose**: Manage document chunks in ChromaDB
- **Methods**:
  - `add_document_chunks(document_id, chunks)` - Store chunks
  - `search(query_embedding, top_k)` - Search similar chunks
  - `delete_document(document_id)` - Delete document chunks
  - `get_document_chunks(document_id)` - Retrieve chunks
- **Dependencies**: ChromaDB

#### LLMService (`llm_service.py`)
- **Purpose**: Generate answers using LLM with RAG context
- **Methods**:
  - `generate_answer(query, context_chunks)` - Main generation method
  - `_build_rag_prompt()` - Build prompt with context
  - `_generate_with_ollama()` - Ollama generation
  - `_generate_with_huggingface()` - HuggingFace generation
- **Providers**: Ollama (local) or HuggingFace (cloud)
- **Dependencies**: requests, ollama API

---

## API Endpoints Overview

```mermaid
graph TB
    subgraph "FastAPI Application"
        Root["/ (Root)"]
        Health["/api/health"]
        
        subgraph "Documents API (/api/documents)"
            Upload["POST /upload<br/>- Upload PDF<br/>- Process & Index"]
            List["GET /<br/>- List all documents"]
            Get["GET /{id}<br/>- Get document details"]
            Delete["DELETE /{id}<br/>- Delete document"]
        end
        
        subgraph "Queries API (/api/queries)"
            Query["POST /<br/>- Query documents<br/>- RAG pipeline"]
            History["GET /history<br/>- Query history"]
            Export["POST /export<br/>- Export results"]
        end
    end

    Root --> Health
    Root --> Upload
    Root --> List
    Root --> Get
    Root --> Delete
    Root --> Query
    Root --> History
    Root --> Export

    style Upload fill:#7ED321
    style Query fill:#7ED321
    style List fill:#4A90E2
    style Get fill:#4A90E2
    style Delete fill:#D0021B
```

### Endpoint Details

#### Root Endpoints
- `GET /` - Root endpoint, returns API info
- `GET /api/health` - Health check endpoint

#### Documents API (`/api/documents`)
- `POST /upload` - Upload and process PDF document
  - **Request**: Multipart file upload
  - **Response**: DocumentUploadResponse with document_id, stats
- `GET /` - List all uploaded documents
  - **Response**: DocumentListResponse with document metadata
- `GET /{id}` - Get document details (including chunks)
  - **Response**: Document with full details
- `DELETE /{id}` - Delete document and all its chunks
  - **Response**: Success message

#### Queries API (`/api/queries`)
- `POST /` - Query documents using RAG pipeline
  - **Request**: QueryRequest {query, top_k}
  - **Response**: QueryResponse {answer, citations, confidence}
- `GET /history` - Get query history
  - **Response**: List of QueryHistoryEntry
- `POST /export` - Export query results
  - **Request**: Export format (markdown/json)
  - **Response**: Exported data

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────┘

INPUT: PDF Document
  │
  ├─► [API Layer] documents.py
  │     │
  │     ├─► [Service] PDFProcessor
  │     │     └─► Extract text (pdfplumber → PyPDF2 fallback)
  │     │
  │     ├─► [Service] Chunker
  │     │     └─► Split into semantic chunks (500 chars, 50 overlap)
  │     │
  │     ├─► [Service] EmbeddingService
  │     │     └─► Generate vectors (sentence-transformers)
  │     │
  │     └─► [Service] VectorStore
  │           └─► Store in ChromaDB with metadata
  │
  └─► OUTPUT: Document indexed in vector database

──────────────────────────────────────────────────────────────────

INPUT: User Query
  │
  ├─► [API Layer] queries.py
  │     │
  │     ├─► [Service] EmbeddingService
  │     │     └─► Generate query embedding
  │     │
  │     ├─► [Service] VectorStore
  │     │     └─► Search similar chunks (top-k, threshold)
  │     │
  │     └─► [Service] LLMService
  │           ├─► Build RAG prompt with context
  │           └─► Generate answer (Ollama/HuggingFace)
  │
  └─► OUTPUT: Answer + Citations + Confidence Score
```

---

## Configuration

All configuration is managed through `app/config.py` using Pydantic Settings:

- **API**: Title, version, debug mode, CORS origins
- **Vector DB**: ChromaDB path, collection name
- **Embeddings**: Model name (all-MiniLM-L6-v2), dimension (384)
- **LLM**: Provider (ollama/huggingface), model, API URLs/keys
- **Retrieval**: Top-k (5), similarity threshold (0.3)
- **Chunking**: Chunk size (500), overlap (50)
- **File Upload**: Max size (10MB), allowed extensions, upload directory
- **LLM Context**: Max context chunks (3), max chunk length (300)

---

## Key Design Decisions

1. **Lazy Service Initialization**: Services are initialized on-demand to avoid startup failures
2. **Singleton Pattern**: Services are reused across requests for efficiency
3. **In-Memory Document Store**: Currently uses dictionary (will be replaced with database in production)
4. **ChromaDB**: Embedded vector database for simplicity and portability
5. **Modular Services**: Each service is independent and testable
6. **Error Handling**: Comprehensive error handling with helpful messages
7. **Memory Optimization**: Limits context chunks and truncates text for LLM to reduce memory usage

---

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Vector Database**: ChromaDB (embedded, persistent)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **PDF Processing**: pdfplumber, PyPDF2
- **LLM**: Ollama (local) or HuggingFace API (cloud)
- **Validation**: Pydantic models
- **Configuration**: Pydantic Settings with .env support

---

## Future Enhancements

- Database integration for persistent document storage
- OCR support for scanned PDFs
- Multi-collection support for document organization
- Authentication and authorization
- Rate limiting and request throttling
- Advanced retrieval strategies (reranking, hybrid search)
- Caching for frequently accessed documents
- Streaming responses for large queries
- Batch document processing
- Document versioning
