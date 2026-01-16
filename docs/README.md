# LexMedica Backend Documentation

Welcome to the LexMedica backend documentation. This directory contains comprehensive documentation of the backend architecture, services, and APIs.

## Documentation Files

### 📐 [Architecture Overview](./architecture.md)
Complete system architecture with diagrams showing:
- System architecture overview
- Document upload workflow
- Query workflow (RAG pipeline)
- Component interactions
- Service dependencies
- API endpoints overview
- Data flow summary

### 🔧 [Services Documentation](./services.md)
Detailed documentation of all backend services:
- **PDFProcessor**: PDF text extraction
- **Chunker**: Document chunking service
- **EmbeddingService**: Vector embedding generation
- **VectorStore**: ChromaDB vector database management
- **LLMService**: LLM answer generation with RAG

### 🌐 [API Endpoints](./api-endpoints.md)
Complete API reference including:
- Root endpoints
- Documents API (upload, list, get, delete)
- Queries API (query, history, export)
- Request/response models
- Error handling
- Example requests

## Project Documentation

### 📚 [Main Project README](./README-main.md)
Complete project overview, features, setup instructions, and usage guide.

### 🚀 [Deployment Guide](./DEPLOYMENT.md)
Step-by-step deployment instructions for Render, Vercel, and Railway.

### 📋 [Project Overview](./project.md)
Project definition, problem statement, solution approach, and architecture design.

### 🔧 [Backend Architecture](./BACKEND.md)
Backend architecture and workflow documentation.

### 📝 [Implementation Plan](./IMPLEMENTATION_PLAN.md)
Step-by-step implementation guide for building the backend from scratch.

## Architecture Summary

The LexMedica backend is a **FastAPI-based RAG (Retrieval-Augmented Generation) system** that:

1. **Processes PDF Documents**:
   - Extracts text from PDFs
   - Chunks text into semantic units
   - Generates vector embeddings
   - Stores in ChromaDB vector database

2. **Answers Questions**:
   - Generates query embeddings
   - Searches for similar document chunks
   - Uses LLM to generate answers with context
   - Returns answers with citations

## Key Components

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                            │
│  documents.py  │  queries.py  │  main.py               │
└─────────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────────┐
│                  Service Layer                           │
│  PDFProcessor │ Chunker │ EmbeddingService              │
│  VectorStore   │ LLMService                             │
└─────────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────────┐
│                  Data Layer                              │
│  File System │ ChromaDB │ In-Memory Store               │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Vector Database**: ChromaDB
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **PDF Processing**: pdfplumber, PyPDF2
- **LLM**: Ollama (local) or HuggingFace API (cloud)

## Getting Started

1. Read the [Main Project README](./README-main.md) for project overview and setup
2. Review the [Architecture Overview](./architecture.md) to understand the system
3. Check [Services Documentation](./services.md) for implementation details
4. See [API Endpoints](./api-endpoints.md) for API usage
5. Follow the [Deployment Guide](./DEPLOYMENT.md) for production deployment

## Diagrams

All diagrams in this documentation use **Mermaid** syntax and can be rendered in:
- GitHub/GitLab markdown viewers
- VS Code with Mermaid extension
- Online Mermaid editors (mermaid.live)
- Documentation tools (MkDocs, Docusaurus, etc.)

## Contributing

When adding new features or services:
1. Update the relevant documentation file
2. Add diagrams if architecture changes
3. Update API documentation for new endpoints
4. Keep diagrams synchronized with code

## Questions?

For questions about the backend:
- Check the [Backend Architecture](./BACKEND.md)
- Review the [Implementation Plan](./IMPLEMENTATION_PLAN.md)
- See the [Main Project README](./README-main.md) for general information
- Open an issue on GitHub
