# API Endpoints Documentation

Complete documentation of all FastAPI endpoints.

## Table of Contents

1. [Root Endpoints](#root-endpoints)
2. [Documents API](#documents-api)
3. [Queries API](#queries-api)
4. [Data Models](#data-models)

---

## Root Endpoints

### GET /

Root endpoint that returns API information.

**Response**:
```json
{
  "message": "Welcome to LexMedica API",
  "version": "1.0.0",
  "status": "running"
}
```

### GET /api/health

Health check endpoint for monitoring and load balancers.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## Documents API

Base path: `/api/documents`

### POST /api/documents/upload

Upload and process a PDF document.

**Request**:
- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Body**: File upload (PDF only)

**Request Parameters**:
- `file` (required): PDF file to upload

**Validation**:
- File extension must be `.pdf`
- File size must be ≤ 10MB (configurable)
- File must not be empty

**Response**: `DocumentUploadResponse`
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "research_paper.pdf",
  "message": "File uploaded successfully",
  "text_length": 1234,
  "needs_ocr": false,
  "extraction_method": "pdfplumber",
  "num_chunks": 5,
  "num_embeddings": 5
}
```

**Process Flow**:
1. Validate file (extension, size, non-empty)
2. Save file to `uploads/` directory with UUID filename
3. Extract text using PDFProcessor
4. Chunk text using Chunker
5. Generate embeddings using EmbeddingService
6. Store chunks in ChromaDB using VectorStore
7. Store document metadata in in-memory store
8. Return response with document ID and statistics

**Error Responses**:
- `400 Bad Request`: Invalid file type, empty file, or validation error
- `413 Payload Too Large`: File exceeds maximum size
- `500 Internal Server Error`: Processing failure

**Example**:
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@research_paper.pdf"
```

---

### GET /api/documents

List all uploaded documents.

**Request**:
- **Method**: GET
- **Parameters**: None

**Response**: `DocumentListResponse`
```json
{
  "documents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "research_paper.pdf",
      "uploaded_at": "2024-01-15T10:30:00",
      "text_length": 1234,
      "needs_ocr": false,
      "extraction_method": "pdfplumber",
      "num_chunks": 5,
      "num_embeddings": 5,
      "metadata": null
    }
  ]
}
```

**Example**:
```bash
curl "http://localhost:8000/api/documents"
```

---

### GET /api/documents/{id}

Get document details including chunks.

**Request**:
- **Method**: GET
- **Path Parameters**:
  - `id` (required): Document ID (UUID)

**Response**: `Document`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "research_paper.pdf",
  "uploaded_at": "2024-01-15T10:30:00",
  "text_length": 1234,
  "needs_ocr": false,
  "extraction_method": "pdfplumber",
  "num_chunks": 5,
  "num_embeddings": 5,
  "metadata": null
}
```

**Error Responses**:
- `404 Not Found`: Document not found

**Example**:
```bash
curl "http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000"
```

---

### DELETE /api/documents/{id}

Delete a document and all its chunks.

**Request**:
- **Method**: DELETE
- **Path Parameters**:
  - `id` (required): Document ID (UUID)

**Response**:
```json
{
  "message": "Document deleted successfully",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunks_deleted": 5
}
```

**Process**:
1. Delete chunks from ChromaDB
2. Delete file from uploads directory
3. Remove from in-memory store
4. Return success message

**Error Responses**:
- `404 Not Found`: Document not found
- `500 Internal Server Error`: Deletion failure

**Example**:
```bash
curl -X DELETE "http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000"
```

---

## Queries API

Base path: `/api/queries`

### POST /api/queries

Query documents using semantic search and LLM.

**Request**:
- **Method**: POST
- **Content-Type**: `application/json`
- **Body**: `QueryRequest`

**Request Body**:
```json
{
  "query": "What are the side effects of this medication?",
  "top_k": 5
}
```

**Request Parameters**:
- `query` (required): Query text (string, non-empty)
- `top_k` (optional): Number of top results to retrieve (default: 5)

**Response**: `QueryResponse`
```json
{
  "answer": "Based on the documents, the medication shows the following side effects...",
  "citations": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "chunk_index": 0,
      "text": "The medication showed significant improvement...",
      "page_number": null,
      "similarity_score": 0.85
    }
  ],
  "confidence": 0.85
}
```

**Process Flow**:
1. Validate query text (non-empty)
2. Generate query embedding using EmbeddingService
3. Search vector store for similar chunks (top-k)
4. Filter results by similarity threshold (default: 0.3)
5. Limit context chunks (max 3) and truncate (max 300 chars each)
6. Build RAG prompt with context
7. Generate answer using LLMService
8. Calculate confidence from top similarity score
9. Return answer with citations

**Error Responses**:
- `400 Bad Request`: Empty query text
- `500 Internal Server Error`: Query processing failure

**Example**:
```bash
curl -X POST "http://localhost:8000/api/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the side effects of this medication?",
    "top_k": 5
  }'
```

---

### GET /api/queries/history

Get query history.

**Request**:
- **Method**: GET
- **Parameters**: None (or pagination parameters in future)

**Response**:
```json
{
  "queries": [
    {
      "query": "What are the side effects?",
      "timestamp": "2024-01-15T10:30:00",
      "answer": "...",
      "confidence": 0.85
    }
  ]
}
```

**Note**: Currently returns in-memory query history. Will be replaced with persistent storage.

**Example**:
```bash
curl "http://localhost:8000/api/queries/history"
```

---

### POST /api/queries/export

Export query results in different formats.

**Request**:
- **Method**: POST
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "query_id": "query-uuid",
  "format": "markdown"  // or "json"
}
```

**Response**: Exported data in requested format

**Formats**:
- `markdown`: Markdown formatted export
- `json`: JSON formatted export

**Example**:
```bash
curl -X POST "http://localhost:8000/api/queries/export" \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "query-uuid",
    "format": "markdown"
  }'
```

---

## Data Models

### DocumentUploadResponse

Response model for document upload endpoint.

```python
{
  "document_id": str,
  "filename": str,
  "message": str,  # default: "File uploaded successfully"
  "text_length": int,
  "needs_ocr": bool,
  "extraction_method": Optional[str],
  "num_chunks": int,
  "num_embeddings": int
}
```

### Document

Document model for listing and details.

```python
{
  "id": str,
  "filename": str,
  "uploaded_at": str,  # ISO format
  "text_length": Optional[int],
  "needs_ocr": Optional[bool],
  "extraction_method": Optional[str],
  "num_chunks": Optional[int],
  "num_embeddings": Optional[int],
  "metadata": Optional[dict]
}
```

### DocumentListResponse

Response model for document list endpoint.

```python
{
  "documents": List[Document]
}
```

### QueryRequest

Request model for query endpoint.

```python
{
  "query": str,  # required, non-empty
  "top_k": Optional[int]  # defaults to settings.top_k (5)
}
```

### Citation

Citation model for query results.

```python
{
  "document_id": str,
  "chunk_index": int,
  "text": str,
  "page_number": Optional[int],
  "similarity_score": float  # 0.0 to 1.0
}
```

### QueryResponse

Response model for query endpoint.

```python
{
  "answer": str,
  "citations": List[Citation],
  "confidence": float  # 0.0 to 1.0 (top similarity score)
}
```

---

## Error Responses

All endpoints may return standard HTTP error responses:

### 400 Bad Request
```json
{
  "detail": "Error message describing the validation error"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 413 Payload Too Large
```json
{
  "detail": "File too large. Maximum size: 10.0MB. Got: 15.0MB"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

---

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These are automatically generated from the FastAPI application and include:
- All endpoints with descriptions
- Request/response schemas
- Try-it-out functionality
- Example requests and responses

---

## CORS Configuration

The API supports CORS (Cross-Origin Resource Sharing) for frontend integration.

**Default Allowed Origins**:
- `http://localhost:3000` (Next.js default)
- `http://localhost:5173` (Vite default)

**Configuration**: Set `CORS_ORIGINS` environment variable or in `.env` file.

---

## Rate Limiting

Currently, there is no rate limiting implemented. This should be added for production use.

**Future Enhancement**: Add rate limiting middleware to prevent abuse.

---

## Authentication

Currently, there is no authentication implemented. The API is open.

**Future Enhancement**: Add JWT authentication or API key authentication for production use.
