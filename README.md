# Medical Research Knowledge Assistant (MR-KA)

An AI-powered assistant for navigating medical literature, helping researchers and clinicians find relevant evidence from research papers, clinical trials, and medical reports using RAG (Retrieval-Augmented Generation).

## Quick Start

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Documentation

All documentation is available in the [`docs/`](./docs/) folder:

- **[📚 Main Documentation](./docs/README-main.md)** - Complete project overview and setup guide
- **[📐 Architecture](./docs/architecture.md)** - System architecture and diagrams
- **[🔧 Services](./docs/services.md)** - Backend services documentation
- **[🌐 API Endpoints](./docs/api-endpoints.md)** - API reference
- **[🚀 Deployment](./docs/DEPLOYMENT.md)** - Deployment guide
- **[📋 Project Overview](./docs/project.md)** - Project definition and design
- **[🔧 Backend Architecture](./docs/BACKEND.md)** - Backend architecture details
- **[📝 Implementation Plan](./docs/IMPLEMENTATION_PLAN.md)** - Step-by-step implementation guide

## Features

- 📄 **PDF Document Processing**: Upload and process medical research PDFs
- 🔍 **Semantic Search**: Advanced vector-based search across documents
- 🤖 **AI-Powered Q&A**: Get answers with citations from source documents
- 📊 **Metadata Extraction**: Automatic extraction of document metadata
- 📝 **Query History**: Track and revisit previous queries
- 📤 **Export Results**: Export answers and citations in Markdown or JSON

## Technology Stack

- **Backend**: FastAPI, ChromaDB, sentence-transformers, Ollama/HuggingFace
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Deployment**: Render/Vercel (free tier) or Railway

## License

MIT License - see LICENSE file for details
