# Service Layer Documentation

Detailed documentation of all backend services.

## Table of Contents

1. [PDFProcessor](#pdfprocessor)
2. [Chunker](#chunker)
3. [EmbeddingService](#embeddingservice)
4. [VectorStore](#vectorstore)
5. [LLMService](#llmservice)

---

## PDFProcessor

**File**: `backend/app/services/pdf_processor.py`

### Purpose
Extract text from PDF files with support for multiple extraction methods and OCR detection.

### Methods

#### `extract_text(file_path: Path) -> Dict[str, Any]`
Main method for extracting text from PDF files.

**Parameters**:
- `file_path`: Path to the PDF file

**Returns**:
- Dictionary with:
  - `text`: Extracted text content
  - `needs_ocr`: Boolean indicating if PDF appears to be scanned
  - `method`: Extraction method used ("pdfplumber" or "pypdf2")
  - `error`: Error message if extraction failed (optional)

**Process**:
1. Try pdfplumber first (better text extraction)
2. Fallback to PyPDF2 if pdfplumber fails
3. Detect if OCR is needed based on extracted text length
4. Return extraction results

#### `_extract_with_pdfplumber(file_path: Path) -> Tuple[str, str]`
Extract text using pdfplumber library.

**Returns**: Tuple of (extracted_text, method_name)

#### `_extract_with_pypdf2(file_path: Path) -> Tuple[str, str]`
Extract text using PyPDF2 library (fallback method).

**Returns**: Tuple of (extracted_text, method_name)

#### `_detect_ocr_needed(text: str) -> bool`
Detect if PDF likely needs OCR (scanned image PDF).

**Heuristics**:
- If extracted text is very short (< 100 chars), likely scanned
- If text is mostly whitespace (< 30% actual text), likely scanned

**Returns**: True if OCR is likely needed, False otherwise

### Dependencies
- `pdfplumber` - Primary PDF extraction library
- `PyPDF2` - Fallback PDF extraction library

### Error Handling
- Handles encrypted PDFs
- Handles corrupted PDFs
- Returns error information in result dictionary
- Logs warnings for extraction failures

---

## Chunker

**File**: `backend/app/services/chunker.py`

### Purpose
Split documents into semantic chunks with configurable size and overlap.

### Methods

#### `chunk_text(text: str, document_id: str, filename: str) -> List[Dict[str, Any]]`
Split text into semantic chunks with metadata.

**Parameters**:
- `text`: Text content to chunk
- `document_id`: Document identifier
- `filename`: Original filename

**Returns**: List of chunk dictionaries with text and metadata

**Chunking Strategy**:
1. Split by paragraphs (double newline separator)
2. For large paragraphs, split by sentences
3. For very long sentences, split by words (last resort)
4. Apply overlap between chunks (default: 50 chars)
5. Preserve metadata for each chunk

**Chunk Metadata**:
- `text`: Chunk text content
- `document_id`: Document identifier
- `filename`: Original filename
- `chunk_index`: Chunk index (0-based)
- `start_char`: Starting character position in original text
- `end_char`: Ending character position in original text

#### `_split_into_paragraphs(text: str) -> List[str]`
Split text into paragraphs using double newline separator.

#### `_split_large_paragraph(paragraph: str, ...) -> List[Dict[str, Any]]`
Split a large paragraph into sentence-based chunks.

**Process**:
- Split by sentences (period, exclamation, question mark)
- Apply chunk size limits
- Apply overlap between chunks

#### `_split_by_words(text: str, ...) -> List[Dict[str, Any]]`
Split text by words as last resort for very long sentences.

#### `_get_overlap_text(text: str, overlap_size: int) -> str`
Get overlap text from the end of a chunk, trying to start at word boundary.

#### `_create_chunk_metadata(...) -> Dict[str, Any]`
Create chunk dictionary with text and metadata.

### Configuration
- `chunk_size`: Maximum chunk size in characters (default: 500)
- `chunk_overlap`: Overlap between chunks in characters (default: 50)

### Features
- Preserves document structure
- Maintains context through overlap
- Handles edge cases (empty text, very long paragraphs)
- Word-boundary aware overlap

---

## EmbeddingService

**File**: `backend/app/services/embeddings.py`

### Purpose
Generate vector embeddings for text using sentence-transformers models.

### Methods

#### `__init__(model_name: Optional[str] = None)`
Initialize embedding service with model.

**Parameters**:
- `model_name`: Name of the sentence-transformers model (defaults to settings)

**Process**:
- Loads the sentence-transformers model on initialization
- Model is cached for reuse across requests

#### `generate_embedding(text: str) -> List[float]`
Generate embedding for a single text.

**Parameters**:
- `text`: Text to generate embedding for

**Returns**: List of floats representing the embedding vector (384 dimensions for all-MiniLM-L6-v2)

**Process**:
- Encodes text using sentence-transformers model
- Normalizes embeddings
- Converts numpy array to list

#### `generate_embeddings_batch(texts: List[str]) -> List[List[float]]`
Generate embeddings for multiple texts (batch processing).

**Parameters**:
- `texts`: List of texts to generate embeddings for

**Returns**: List of embedding vectors

**Process**:
- Filters out empty texts
- Processes in batches of 32 for efficiency
- Normalizes embeddings
- Returns list of lists

#### `get_embedding_dimension() -> int`
Get the dimension of embeddings generated by this model.

**Returns**: Embedding dimension (e.g., 384 for all-MiniLM-L6-v2)

### Model
- **Default**: `all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Type**: Sentence transformer (semantic embeddings)

### Dependencies
- `sentence-transformers` - Embedding generation library
- `torch` - PyTorch (required by sentence-transformers)

### Features
- Batch processing for efficiency
- Normalized embeddings for better similarity search
- Lazy model loading
- Error handling for empty texts

---

## VectorStore

**File**: `backend/app/services/vector_store.py`

### Purpose
Manage document chunks in ChromaDB vector database with similarity search capabilities.

### Methods

#### `__init__()`
Initialize ChromaDB client and collection.

**Process**:
- Creates persistent ChromaDB client
- Gets or creates collection with cosine distance metric
- Collection name: "documents" (configurable)

#### `add_document_chunks(document_id: str, chunks: List[Dict[str, Any]]) -> List[str]`
Add document chunks with embeddings to ChromaDB.

**Parameters**:
- `document_id`: Document identifier
- `chunks`: List of chunk dictionaries with:
  - `text`: Chunk text content
  - `embedding`: Embedding vector (list of floats)
  - `chunk_index`: Chunk index within document
  - `filename`: Original filename
  - `start_char`: Starting character position
  - `end_char`: Ending character position

**Returns**: List of chunk IDs (generated by ChromaDB)

**Process**:
- Validates required fields in chunks
- Generates unique chunk IDs
- Prepares metadata (ChromaDB requires string values)
- Adds to ChromaDB collection

#### `search(query_embedding: List[float], top_k: int = None, similarity_threshold: float = None, document_id: Optional[str] = None) -> List[Dict[str, Any]]`
Search for similar chunks using query embedding.

**Parameters**:
- `query_embedding`: Query embedding vector
- `top_k`: Number of top results to return (defaults to settings.top_k)
- `similarity_threshold`: Minimum similarity score (defaults to settings.similarity_threshold)
- `document_id`: Optional filter by document ID

**Returns**: List of result dictionaries with:
- `id`: Chunk ID
- `text`: Chunk text
- `metadata`: Chunk metadata
- `distance`: Similarity distance (lower is more similar)
- `score`: Similarity score (higher is more similar, 1 - distance)

**Process**:
- Queries ChromaDB with query embedding
- Converts distance to similarity score
- Filters results by similarity threshold
- Returns top-k results

**Similarity Score Calculation**:
- For L2 distance > 1.0: `score = 1.0 - (distance² / 2.0)`
- For cosine distance ≤ 1.0: `score = 1.0 - distance`

#### `delete_document(document_id: str) -> int`
Delete all chunks for a document from ChromaDB.

**Parameters**:
- `document_id`: Document identifier

**Returns**: Number of chunks deleted

**Process**:
- Gets all chunks for document using where clause
- Deletes chunks by IDs
- Returns count of deleted chunks

#### `get_document_chunks(document_id: str) -> List[Dict[str, Any]]`
Get all chunks for a document from ChromaDB.

**Parameters**:
- `document_id`: Document identifier

**Returns**: List of chunk dictionaries with text and metadata

**Process**:
- Queries ChromaDB with document_id filter
- Returns all chunks for the document

### Dependencies
- `chromadb` - Vector database library

### Configuration
- `chroma_db_path`: Path to ChromaDB persistence directory (default: "./chroma_db")
- `chroma_collection_name`: Collection name (default: "documents")
- `top_k`: Default number of results (default: 5)
- `similarity_threshold`: Minimum similarity score (default: 0.3)

### Features
- Persistent storage (data survives restarts)
- Cosine similarity search
- Document filtering
- Metadata preservation
- Error handling and logging

---

## LLMService

**File**: `backend/app/services/llm_service.py`

### Purpose
Generate answers using LLM with RAG (Retrieval-Augmented Generation) context.

### Methods

#### `__init__(provider: Optional[str] = None, model: Optional[str] = None)`
Initialize LLM service.

**Parameters**:
- `provider`: LLM provider ('ollama' or 'huggingface'), defaults to settings
- `model`: Model name, defaults to settings

**Process**:
- Sets provider and model from parameters or settings
- Initializes Ollama connection if provider is 'ollama'
- Verifies model availability

#### `generate_answer(query: str, context_chunks: List[str], max_tokens: int = 500) -> str`
Generate answer from query and context chunks using LLM.

**Parameters**:
- `query`: User query/question
- `context_chunks`: List of text chunks retrieved from documents (already limited and truncated)
- `max_tokens`: Maximum tokens in response (default: 500)

**Returns**: Generated answer string

**Process**:
1. Validates query is not empty
2. Returns default message if no context chunks
3. Builds RAG prompt with context
4. Calls appropriate LLM provider
5. Returns generated answer

#### `_build_rag_prompt(query: str, context_chunks: List[str]) -> str`
Build RAG prompt with context chunks.

**Format**:
```
Answer the question based ONLY on the provided context.

Context:
[Context 1]
{chunk 1}

[Context 2]
{chunk 2}

...

Question: {query}

Answer:
```

#### `_generate_with_ollama(prompt: str, max_tokens: int) -> str`
Generate answer using Ollama /api/generate endpoint.

**Parameters**:
- `prompt`: Full prompt with context
- `max_tokens`: Maximum tokens in response

**Returns**: Generated answer

**Process**:
- Calls Ollama API at `/api/generate`
- Uses model from settings
- Sets temperature to 0.7
- Handles memory errors gracefully
- Returns complete response (stream: false)

**Error Handling**:
- Detects memory-related errors
- Provides helpful error messages
- Handles connection errors

#### `_generate_with_huggingface(prompt: str, max_tokens: int) -> str`
Generate answer using Hugging Face API (fallback).

**Parameters**:
- `prompt`: Full prompt with context
- `max_tokens`: Maximum tokens in response

**Returns**: Generated answer

**Process**:
- Calls HuggingFace Inference API
- Uses API key from settings
- Handles different response formats
- Returns generated text

### Providers

#### Ollama (Local)
- **Base URL**: `http://localhost:11434` (configurable)
- **Endpoint**: `/api/generate`
- **Default Model**: `deepseek-r1:latest` (configurable)
- **Advantages**: Local, no API costs, privacy
- **Requirements**: Ollama must be running locally

#### HuggingFace (Cloud)
- **API URL**: `https://api-inference.huggingface.co/models` (configurable)
- **Endpoint**: `/models/{model_name}`
- **Requirements**: API key required
- **Advantages**: No local setup, various models available

### Configuration
- `llm_provider`: Provider name ("ollama" or "huggingface")
- `llm_model`: Model name
- `ollama_base_url`: Ollama API base URL
- `huggingface_api_key`: HuggingFace API key
- `huggingface_api_url`: HuggingFace API URL

### Features
- Multiple LLM provider support
- RAG prompt building
- Error handling for memory issues
- Connection error handling
- Configurable model and parameters
- Context truncation to reduce memory usage

### Memory Optimization
- Limits context chunks sent to LLM (max_context_chunks: 3)
- Truncates chunk text (max_chunk_length: 300 chars)
- Reduces token usage and memory requirements

---

## Service Interaction Patterns

### Document Upload Flow
```
PDFProcessor → Chunker → EmbeddingService → VectorStore
```

### Query Flow
```
EmbeddingService → VectorStore → LLMService
```

### Error Handling
- All services use try-except blocks
- Errors are logged with context
- Services return error information rather than crashing
- Graceful degradation when possible

### Initialization
- Services use lazy initialization
- Models are loaded on first use
- Singleton pattern for service instances
- Configuration loaded from settings
