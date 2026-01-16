"""Query endpoints for searching documents."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import QueryRequest, QueryResponse, Citation
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/queries", tags=["queries"])


@router.post("", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query documents using semantic search and LLM.

    - Generates embedding for the query text
    - Searches vector store for similar chunks
    - Generates answer using LLM with retrieved context
    - Returns answer, citations, and confidence score

    Args:
        request: Query request with query text and optional top_k

    Returns:
        QueryResponse with answer, citations, and confidence score
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty")

    try:
        # Generate embedding for query
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.generate_embedding(request.query)

        # Search vector store
        vector_store = VectorStore()
        top_k = request.top_k or settings.top_k

        search_results = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        # Convert search results to citations
        citations = []
        for result in search_results:
            metadata = result.get("metadata", {})
            chunk_index = int(metadata.get("chunk_index", 0)) if metadata.get("chunk_index") else 0

            citation = Citation(
                document_id=metadata.get("document_id", ""),
                chunk_index=chunk_index,
                text=result.get("text", ""),
                similarity_score=result.get("score", 0.0),
            )
            citations.append(citation)

        # Calculate confidence from top similarity score
        # Confidence is the highest similarity score (0.0 to 1.0)
        confidence = citations[0].similarity_score if citations else 0.0

        logger.info(
            f"Query '{request.query[:50]}...' returned {len(citations)} results "
            f"with confidence {confidence:.3f}"
        )

        # Generate answer using LLM with retrieved context
        answer = ""
        if citations:
            try:
                llm_service = LLMService()
                # Limit context chunks to reduce memory usage
                # Take top N chunks (most relevant) and truncate if too long
                max_chunks = settings.max_context_chunks
                limited_citations = citations[:max_chunks]
                
                # Extract and truncate text from citations for context
                context_chunks = []
                for citation in limited_citations:
                    chunk_text = citation.text
                    # Truncate chunk if it's too long
                    if len(chunk_text) > settings.max_chunk_length:
                        chunk_text = chunk_text[:settings.max_chunk_length] + "..."
                    context_chunks.append(chunk_text)
                
                logger.info(
                    f"Sending {len(context_chunks)} context chunks to LLM "
                    f"(limited from {len(citations)} total citations, "
                    f"max {settings.max_chunk_length} chars each)"
                )
                
                answer = llm_service.generate_answer(
                    query=request.query,
                    context_chunks=context_chunks,
                )
                logger.info(f"Generated answer using LLM ({len(answer)} characters)")
            except Exception as e:
                # If LLM fails, log error but don't fail the request
                # Return citations only with empty answer
                logger.error(f"LLM generation failed: {str(e)}")
                answer = (
                    "I found relevant information in the documents, but couldn't generate "
                    "a summary. Please review the citations below."
                )

        return QueryResponse(
            answer=answer,
            citations=citations,
            confidence=confidence,
        )

    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}",
        )
