---
name: MR-KA Implementation Plan
overview: A phased implementation plan for the Medical Research Knowledge Assistant with comprehensive testing, Next.js frontend, local LLM support, and free deployment strategy using Render/Railway for backend and Vercel for frontend.
todos:
  - id: phase1_setup
    content: Set up project structure (backend FastAPI, frontend Next.js), initialize repositories, configure development environment
    status: completed
  - id: phase1_pdf
    content: Implement PDF processing service (text extraction, OCR handling), document chunking, and embedding generation
    status: completed
    dependencies:
      - phase1_setup
  - id: phase1_vector
    content: Integrate Chroma vector database, implement vector storage and retrieval, create FastAPI health check endpoint
    status: completed
    dependencies:
      - phase1_pdf
  - id: phase1_tests
    content: Write unit tests for PDF processing, chunking, and vector store operations
    status: completed
    dependencies:
      - phase1_vector
  - id: phase2_retrieval
    content: Implement semantic search retrieval system with top-k results and similarity thresholds
    status: completed
    dependencies:
      - phase1_tests
  - id: phase2_llm
    content: Integrate Ollama for local LLM and Hugging Face API as fallback, implement prompt engineering for medical domain
    status: completed
    dependencies:
      - phase2_retrieval
  - id: phase2_query_api
    content: Create query API endpoint that returns answers with citations and confidence scores
    status: completed
    dependencies:
      - phase2_llm
  - id: phase2_integration_tests
    content: Write integration tests for complete RAG pipeline (upload → query → verify citations)
    status: completed
    dependencies:
      - phase2_query_api
  - id: phase3_frontend_setup
    content: Set up Next.js 14 with TypeScript, Tailwind CSS, and API client configuration
    status: completed
    dependencies:
      - phase2_integration_tests
  - id: phase3_components
    content: "Build core UI components: DocumentUpload, QueryInput, QueryResults, CitationCard, DocumentList"
    status: completed
    dependencies:
      - phase3_frontend_setup
  - id: phase3_pages
    content: Create main pages (home/query page, document library) with routing and state management
    status: completed
    dependencies:
      - phase3_components
  - id: phase3_e2e
    content: Write E2E tests with Playwright for complete user flows (upload → query → results)
    status: completed
    dependencies:
      - phase3_pages
  - id: phase4_metadata
    content: Implement document metadata extraction (title, authors, journal, DOI) and storage
    status: completed
    dependencies:
      - phase3_e2e
  - id: phase4_features
    content: Add query history persistence, export functionality (Markdown/JSON), and improved error handling
    status: completed
    dependencies:
      - phase4_metadata
  - id: phase4_performance
    content: Implement caching (query results, embeddings), optimize API responses, add loading states
    status: completed
    dependencies:
      - phase4_features
  - id: phase5_medical_nlp
    content: Integrate scispacy for medical entity recognition, implement paper categorization by specialty
    status: completed
    dependencies:
      - phase4_performance
  - id: phase5_chunking
    content: Implement section-aware chunking (Abstract, Methods, Results, Discussion) with prioritization
    status: completed
    dependencies:
      - phase5_medical_nlp
  - id: phase5_trial_extraction
    content: Extract clinical trial metadata (phase, endpoints, sample size, outcomes) from documents
    status: completed
    dependencies:
      - phase5_chunking
  - id: phase6_testing
    content: Achieve >80% test coverage, write comprehensive unit/integration/E2E tests, performance benchmarks
    status: completed
    dependencies:
      - phase5_trial_extraction
  - id: phase7_docker
    content: Create Dockerfile and docker-compose.yml, optimize image size, set up environment configuration
    status: completed
    dependencies:
      - phase6_testing
  - id: phase7_cicd
    content: Set up GitHub Actions CI/CD pipeline (tests, build, deploy to staging)
    status: completed
    dependencies:
      - phase7_docker
  - id: phase8_backend_deploy
    content: Deploy backend to Render/Railway, configure environment variables, set up health checks
    status: completed
    dependencies:
      - phase7_cicd
  - id: phase8_frontend_deploy
    content: Deploy frontend to Vercel, configure API endpoints, verify CORS and connectivity
    status: completed
    dependencies:
      - phase8_backend_deploy
  - id: phase8_documentation
    content: Write comprehensive README, API documentation (OpenAPI), user guide, and deployment guide
    status: completed
    dependencies:
      - phase8_frontend_deploy
---

# MR-KA Implementation Plan

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Next.js    │────▶│   FastAPI    │────▶│  Vector DB  │
│  Frontend   │◀────│   Backend    │◀────│  (Chroma)   │
│  (Vercel)   │     │   (Render)   │     │  (Embedded) │
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

- FastAPI (Python) - REST API
- Chroma (vector database) - embedded, no separate service needed
- Ollama (local LLM) - Llama 2/3 or Mistral
- Hugging Face API (fallback for production)
- PyPDF2/pdfplumber - PDF processing
- sentence-transformers - embeddings

**Frontend:**

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React Query - data fetching

**Deployment:**

- Backend: Render (free tier) or Railway
- Frontend: Vercel (free tier)
- Vector DB: Embedded in backend (Chroma)
- LLM: Ollama locally, Hugging Face API in production

**Testing:**

- pytest - backend tests
- Jest + React Testing Library - frontend tests
- Playwright - E2E tests

## Phase 1: Foundation & Core Backend (Week 1-2)

### Deliverables

- Project structure setup
- Basic PDF ingestion and text extraction
- Document chunking
- Embedding generation
- Vector database integration
- FastAPI skeleton with health check

### Implementation Tasks

**1.1 Project Structure**

```
lexmedica/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Configuration
│   │   ├── models/              # Pydantic models
│   │   ├── services/
│   │   │   ├── pdf_processor.py
│   │   │   ├── chunker.py
│   │   │   ├── embeddings.py
│   │   │   ├── vector_store.py
│   │   │   └── llm_service.py
│   │   └── api/
│   │       ├── documents.py
│   │       └── queries.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   ├── tests/
│   └── package.json
└── README.md
```

**1.2 Core Services**

- `pdf_processor.py`: Extract text from PDFs, handle OCR if needed
- `chunker.py`: Split documents into semantic chunks (paragraph/section level)
- `embeddings.py`: Generate embeddings using sentence-transformers
- `vector_store.py`: Chroma integration for storing/retrieving embeddings
- `llm_service.py`: Ollama client for local LLM, HF API fallback

**1.3 API Endpoints**

- `POST /api/documents/upload` - Upload PDF
- `GET /api/documents` - List documents
- `GET /api/health` - Health check

### Testing

- Unit tests for PDF extraction
- Unit tests for chunking logic
- Unit tests for embedding generation
- Integration test for vector store

### Success Criteria

- Can upload a PDF and extract text
- Documents are chunked correctly
- Embeddings are generated and stored
- Health check endpoint works

---

## Phase 2: RAG Pipeline & Query System (Week 3-4)

### Deliverables

- Retrieval system (semantic search)
- LLM integration for answer generation
- Query endpoint with citations
- Basic prompt engineering

### Implementation Tasks

**2.1 Retrieval System**

- Implement semantic search in `vector_store.py`
- Top-k retrieval with similarity threshold
- Return chunks with metadata (document ID, page number, chunk index)

**2.2 LLM Service**

- Ollama integration for local development
- Hugging Face API integration for production
- Prompt template with context injection
- Response parsing with citation extraction

**2.3 Query API**

- `POST /api/queries` - Submit query, return answer with citations
- Request: `{ "query": "string", "top_k": 5 }`
- Response: `{ "answer": "string", "citations": [...], "confidence": float }`

**2.4 Prompt Engineering**

- Medical domain-specific prompts
- Context formatting (study type, patient population, etc.)
- Citation instruction in prompts

### Testing

- Unit tests for retrieval (mock vector store)
- Unit tests for LLM service (mock responses)
- Integration test: upload doc → query → verify citations
- Test with sample medical PDFs

### Success Criteria

- Can query uploaded documents
- Returns relevant answers with citations
- Citations link back to source chunks
- Handles queries with no relevant results

---

## Phase 3: Frontend Development (Week 5-6)

### Deliverables

- Next.js application setup
- Document upload interface
- Query interface
- Results display with citations
- Basic UI/UX

### Implementation Tasks

**3.1 Next.js Setup**

- Next.js 14 with App Router
- TypeScript configuration
- Tailwind CSS setup
- API client (fetch wrapper)

**3.2 Core Pages**

- `/` - Home/Query page
- `/documents` - Document library
- `/query/[id]` - Query result page (optional)

**3.3 Components**

- `DocumentUpload` - Drag-and-drop PDF upload
- `QueryInput` - Query form with suggestions
- `QueryResults` - Display answer with citations
- `CitationCard` - Individual citation display
- `DocumentList` - List of uploaded documents
- `LoadingSpinner` - Loading states

**3.4 Features**

- Real-time upload progress
- Query history (localStorage initially)
- Copy answer/citations
- Responsive design

### Testing

- Component unit tests (React Testing Library)
- API integration tests (mock API)
- E2E test: upload → query → verify results (Playwright)

### Success Criteria

- Can upload PDFs via UI
- Can submit queries and see results
- Citations are clickable/viewable
- UI is responsive and usable

---

## Phase 4: Enhanced Features (Week 7-8)

### Deliverables

- Document metadata extraction
- Query history persistence
- Export functionality
- Error handling improvements
- Performance optimizations

### Implementation Tasks

**4.1 Document Metadata**

- Extract title, authors, journal, year, DOI from PDFs
- Store metadata in database (SQLite for MVP, PostgreSQL for production)
- Display metadata in document list

**4.2 Query History**

- Backend: Store queries in database
- Frontend: Query history sidebar/panel
- Re-run previous queries

**4.3 Export Features**

- Export answers as Markdown
- Export citations as JSON
- Copy to clipboard functionality

**4.4 Error Handling**

- Graceful error messages
- Retry logic for failed requests
- Validation for file uploads
- OCR quality warnings

**4.5 Performance**

- Query result caching (Redis or in-memory)
- Embedding caching
- Lazy loading for document list
- Optimistic UI updates

### Testing

- Test metadata extraction accuracy
- Test export functionality
- Test error scenarios
- Performance tests (load testing)

### Success Criteria

- Documents show proper metadata
- Query history works
- Export functions correctly
- Errors are handled gracefully
- App feels responsive

---

## Phase 5: Medical Domain Features (Week 9-10)

### Deliverables

- Medical entity recognition
- Paper categorization
- Enhanced chunking (section-aware)
- Clinical trial metadata extraction

### Implementation Tasks

**5.1 Medical NLP**

- Integrate scispacy for medical NER
- Extract drugs, diseases, conditions
- Link entities to medical ontologies (optional)

**5.2 Paper Categorization**

- Classify papers by specialty (oncology, cardiology, etc.)
- Classify by study type (RCT, review, case study)
- Store categories in metadata

**5.3 Section-Aware Chunking**

- Identify paper sections (Abstract, Methods, Results, Discussion)
- Chunk within sections
- Prioritize Results/Discussion sections in retrieval

**5.4 Clinical Trial Extraction**

- Extract trial phase, endpoints, sample size
- Extract outcomes and adverse events
- Structure trial data for queries

### Testing

- Test NER accuracy on medical texts
- Test categorization accuracy
- Test section-aware chunking
- Test trial metadata extraction

### Success Criteria

- Medical entities are identified
- Papers are categorized correctly
- Section-aware retrieval improves relevance
- Trial metadata is extracted accurately

---

## Phase 6: Testing & Quality Assurance (Week 11)

### Deliverables

- Comprehensive test suite
- Test coverage >80%
- E2E test scenarios
- Performance benchmarks

### Testing Tasks

**6.1 Backend Tests**

- Unit tests for all services
- Integration tests for API endpoints
- Test edge cases (empty PDFs, malformed queries, etc.)
- Test error handling

**6.2 Frontend Tests**

- Component tests
- API integration tests
- User interaction tests
- Accessibility tests

**6.3 E2E Tests**

- Complete user flows:
  - Upload → Query → View results
  - Query history → Re-run query
  - Export functionality
- Cross-browser testing

**6.4 Performance Tests**

- Load testing (multiple concurrent queries)
- Large document handling
- Response time benchmarks

### Success Criteria

- Test coverage >80%
- All critical paths tested
- Performance meets targets (<3s query response)
- No critical bugs

---

## Phase 7: Deployment Preparation (Week 12)

### Deliverables

- Docker containerization
- Environment configuration
- CI/CD pipeline
- Deployment documentation

### Implementation Tasks

**7.1 Docker Setup**

- Multi-stage Dockerfile for backend
- Docker Compose for local development
- Optimize image size

**7.2 Environment Configuration**

- `.env.example` with all required variables
- Environment-specific configs (dev, prod)
- Secrets management

**7.3 CI/CD**

- GitHub Actions workflow:
  - Run tests on PR
  - Build Docker image
  - Deploy to staging
- Automated testing before deployment

**7.4 Deployment Setup**

**Backend (Render/Railway):**

- Connect GitHub repo
- Set environment variables
- Configure build command
- Set up health checks

**Frontend (Vercel):**

- Connect GitHub repo
- Set API endpoint environment variable
- Configure build settings

**7.5 Monitoring**

- Health check endpoints
- Basic logging (query logs, errors)
- Error tracking (Sentry free tier)

### Success Criteria

- Docker builds successfully
- CI/CD pipeline works
- Can deploy to staging
- Health checks pass

---

## Phase 8: Production Deployment (Week 13)

### Deliverables

- Live application
- Documentation
- User guide
- Performance monitoring

### Deployment Tasks

**8.1 Backend Deployment (Render)**

- Create Render account
- Create new Web Service
- Connect repository
- Set environment variables:
  - `HUGGINGFACE_API_KEY` (for production LLM)
  - `CHROMA_PERSIST_DIR` (for vector storage)
  - `ALLOWED_ORIGINS` (frontend URL)
- Deploy and verify

**8.2 Frontend Deployment (Vercel)**

- Create Vercel account
- Import GitHub repository
- Set environment variables:
  - `NEXT_PUBLIC_API_URL` (backend URL)
- Deploy and verify

**8.3 Post-Deployment**

- Test all functionality
- Verify CORS settings
- Check performance
- Monitor error logs

**8.4 Documentation**

- README with setup instructions
- API documentation (OpenAPI/Swagger)
- User guide
- Deployment guide

### Success Criteria

- Application is live and accessible
- All features work in production
- Documentation is complete
- Performance is acceptable

---

## Free Deployment Strategy

### Backend Options

**Option 1: Render (Recommended)**

- Free tier: 750 hours/month
- 512MB RAM (sufficient for Chroma + FastAPI)
- Persistent disk for vector storage
- Auto-deploy from GitHub
- Sleeps after 15min inactivity (wake on request)

**Option 2: Railway**

- Free tier: $5 credit/month
- Better performance than Render
- Persistent storage
- No sleep (always on)

**Option 3: Fly.io**

- Generous free tier
- Global deployment
- Persistent volumes

### Frontend: Vercel

- Free tier: Unlimited
- Excellent Next.js support
- Global CDN
- Auto-deploy from GitHub

### Vector Database: Chroma (Embedded)

- No separate service needed
- Stores vectors in backend's file system
- Works with Render's persistent disk

### LLM Strategy

- **Development**: Ollama (local)
- **Production**: Hugging Face Inference API (free tier: 1000 requests/month)
- **Alternative**: Use OpenAI API with pay-as-you-go (small cost)

---

## Testing Strategy

### Test Types

1. **Unit Tests** (pytest, Jest)

   - Test individual functions/components
   - Mock external dependencies
   - Fast execution

2. **Integration Tests** (pytest)

   - Test API endpoints
   - Test service interactions
   - Use test database

3. **E2E Tests** (Playwright)

   - Test complete user flows
   - Run in CI/CD
   - Cross-browser testing

4. **Performance Tests**

   - Load testing with multiple concurrent requests
   - Response time benchmarks
   - Memory usage monitoring

### Test Coverage Goals

- Backend: >85% coverage
- Frontend: >80% coverage
- Critical paths: 100% coverage

---

## Risk Mitigation

### Technical Risks

1. **LLM Cost/Performance**

   - Mitigation: Use Hugging Face free tier, implement caching
   - Fallback: Switch to cheaper models if needed

2. **Vector DB Storage**

   - Mitigation: Chroma embedded (no separate service)
   - Monitor storage usage on Render

3. **PDF Processing Failures**

   - Mitigation: Robust error handling, OCR fallback
   - User feedback for failed uploads

4. **Deployment Limitations**

   - Mitigation: Optimize Docker image, use efficient libraries
   - Consider paid tier if free tier insufficient

### Deployment Risks

1. **Render Sleep**

   - Mitigation: Use Railway or Fly.io if needed
   - Implement keep-alive ping (if allowed)

2. **Storage Limits**

   - Mitigation: Implement document cleanup
   - Limit document size/quantity

---

## Success Metrics

### Functional

- Can upload and process PDFs successfully
- Queries return relevant answers with citations
- UI is intuitive and responsive
- All features work in production

### Performance

- Query response time < 3 seconds
- PDF processing < 10 seconds per document
- Frontend load time < 2 seconds

### Quality

- Test coverage > 80%
- Zero critical bugs
- Error rate < 1%

---

## Timeline Summary

- **Week 1-2**: Phase 1 - Foundation
- **Week 3-4**: Phase 2 - RAG Pipeline
- **Week 5-6**: Phase 3 - Frontend
- **Week 7-8**: Phase 4 - Enhanced Features
- **Week 9-10**: Phase 5 - Medical Domain
- **Week 11**: Phase 6 - Testing
- **Week 12**: Phase 7 - Deployment Prep
- **Week 13**: Phase 8 - Production Deployment

**Total: ~13 weeks (3 months)**

---

## Next Steps After Plan Approval

1. Set up GitHub repository
2. Initialize backend and frontend projects
3. Set up development environment
4. Begin Phase 1 implementation