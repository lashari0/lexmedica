# LexMedica - Document-First Evidence-Based Medical RAG

A **document-first, evidence-driven** medical RAG system designed for clinical use. Unlike generic chat interfaces, LexMedica enforces document-scoped queries and requires visible evidence for every answer, making it suitable for medical decision support.

## Design Philosophy

> **The application must be document-scoped by default.**  
> **The model may not answer without visible evidence.**  
> **Refusal is a valid and visible outcome.**  
> **Evidence visibility > conversational fluency.**

This transformation makes LLM capability **usable in medicine** by prioritizing traceability, authority, and evidence visibility over conversational fluency.

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

- **[📋 Redesign Plan](./docs/app_design2.md)** - Step-by-step redesign instructions (12 steps)
- **[🎨 Frontend Architecture](./docs/frontend.md)** - Frontend components, routing, and UI patterns
- **[⚙️ Backend Architecture](./docs/backend.md)** - API endpoints, services, and data models

## Core Features

### Document-First Interface
- **Document-scoped queries**: Answers limited to selected document by default
- **Evidence signaling**: Document cards show authority, year, type, and jurisdiction at a glance
- **Trust indicators**: Visual distinction between guidelines, RCTs, and observational studies

### Evidence-Based Responses
- **Structured answers**: Bulleted format (3-6 points) with inline citations `[Section X]`
- **Evidence navigator**: Interactive citations with source text snippets
- **Refusal state**: Clear indication when evidence is insufficient (not an error)
- **Non-numeric signals**: "3 sections referenced" instead of confidence percentages

### Enhanced Document Management
- **Rich metadata extraction**: Authority, document type, publication year, jurisdiction
- **Filtering**: By document type, year range, authority, and jurisdiction
- **Document preview**: Abstract and key metadata on hover/selection
- **Scope expansion**: Optional, explicit multi-document queries

### Audit & Compliance
- **Event logging**: Document selection, scope expansion, refusals, citations used
- **Regulatory defensibility**: Full audit trail for medical use cases

## Technology Stack

- **Backend**: FastAPI, ChromaDB, sentence-transformers, Ollama/HuggingFace
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Deployment**: Render/Vercel (free tier) or Railway

## License

MIT License - see LICENSE file for details
