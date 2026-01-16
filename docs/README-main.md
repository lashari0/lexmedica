# Medical Research Knowledge Assistant (MR-KA)

An AI-powered assistant for navigating medical literature, helping researchers and clinicians find relevant evidence from research papers, clinical trials, and medical reports using RAG (Retrieval-Augmented Generation).

## Features

- 📄 **PDF Document Processing**: Upload and process medical research PDFs with automatic text extraction
- 🔍 **Semantic Search**: Advanced vector-based search across uploaded documents
- 🤖 **AI-Powered Q&A**: Get answers to questions with citations from source documents
- 📊 **Metadata Extraction**: Automatic extraction of title, authors, journal, DOI, and publication year
- 📝 **Query History**: Track and revisit previous queries
- 📤 **Export Results**: Export answers and citations in Markdown or JSON format

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Next.js    │────▶│   FastAPI    │────▶│  ChromaDB   │
│  Frontend   │◀────│   Backend    │◀────│  (Vector)   │
│  (Vercel)   │     │   (Render)   │     │  (Embedded)  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Local LLM    │
                    │ (Ollama)     │
                    │ or HF API    │
                    └──────────────┘
```

## Technology Stack

**Backend:**
- FastAPI (Python 3.11+) - REST API
- ChromaDB - Vector database for embeddings
- Ollama / Hugging Face API - LLM for answer generation
- PyPDF2/pdfplumber - PDF processing
- sentence-transformers - Text embeddings

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React Query - Data fetching
- TanStack Query - State management

**Deployment:**
- Backend: Render (free tier) or Railway
- Frontend: Vercel (free tier)
- Docker support for local development

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose (optional, for containerized setup)
- Ollama (for local LLM) - [Install Ollama](https://ollama.ai)

### Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run the server
uvicorn app.main:app --reload
```

The backend will be available at `http://localhost:8000`

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

#### Using Docker Compose

```bash
# Start all services
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Ollama: http://localhost:11434
```

### Configuration

#### Backend Environment Variables

Create a `.env` file in the `backend` directory:

```env
# LLM Configuration
LLM_PROVIDER=ollama  # or "huggingface"
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
# HUGGINGFACE_API_KEY=your_key_here

# Vector Database
CHROMA_PERSIST_DIR=./chroma_db

# Retrieval
TOP_K=5
SIMILARITY_THRESHOLD=0.7

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```

#### Frontend Environment Variables

Create a `.env.local` file in the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

- `POST /api/documents/upload` - Upload a PDF document
- `GET /api/documents` - List all documents
- `GET /api/documents/{id}` - Get document details
- `POST /api/queries` - Query documents
- `GET /api/queries/history` - Get query history
- `GET /api/health` - Health check

## Usage

1. **Upload Documents**: Use the web interface to upload PDF files of medical research papers
2. **Wait for Processing**: Documents are automatically processed, chunked, and indexed
3. **Ask Questions**: Enter natural language questions about the uploaded documents
4. **View Results**: Get AI-generated answers with citations to source documents
5. **Review Citations**: Click on citations to see the exact source text

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

### E2E Tests

```bash
cd frontend
npm run test:e2e
```

## Deployment

### Backend Deployment (Render)

1. Create a Render account
2. Create a new Web Service
3. Connect your GitHub repository
4. Set build command: `cd backend && pip install -r requirements.txt`
5. Set start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables from `.env.example`

### Frontend Deployment (Vercel)

1. Create a Vercel account
2. Import your GitHub repository
3. Set framework preset to Next.js
4. Add environment variable: `NEXT_PUBLIC_API_URL` (your backend URL)
5. Deploy

## Project Structure

```
lexmedica/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── models/        # Pydantic models
│   │   ├── services/     # Core services
│   │   ├── main.py        # FastAPI app
│   │   └── config.py      # Configuration
│   ├── tests/             # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   └── lib/           # Utilities
│   ├── tests/             # Frontend tests
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Development Status

✅ **Phase 1**: Foundation & Core Backend - Complete
✅ **Phase 2**: RAG Pipeline & Query System - Complete
✅ **Phase 3**: Frontend Development - Complete
✅ **Phase 4**: Enhanced Features - Complete
✅ **Phase 5**: Medical Domain Features - Complete
✅ **Phase 6**: Testing & QA - Complete
✅ **Phase 7**: Deployment Preparation - Complete
✅ **Phase 8**: Production Deployment - Ready

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with FastAPI, Next.js, and ChromaDB
- Uses sentence-transformers for embeddings
- LLM support via Ollama and Hugging Face

## Support

For issues and questions, please open an issue on GitHub.
