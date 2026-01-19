"""Query endpoints for searching documents."""

import logging
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.utils.config import settings
from app.models import QueryRequest, QueryResponse, Citation
from app.services.ingestion import Embedder
from app.services.retrieval import VectorStore
from app.services.models.llm import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/queries", tags=["queries"])


def replace_context_refs(text: str, citations: List[Citation]) -> str:
    """
    STEP 7: Replace [Context N] references with [Citation N] in answer text.
    
    Maps context indices (1-based) to citation indices (1-based) for display.
    
    Args:
        text: Answer text containing [Context N] references
        citations: List of citations to map context numbers to
        
    Returns:
        Text with [Context N] replaced by [Citation N]
    """
    # Pattern to match [Context N] or [ContextN]
    pattern = r'\[Context\s*(\d+)\]'
    
    def replace_match(match):
        context_num = int(match.group(1))
        # Context numbers are 1-based, convert to 0-based index
        context_idx = context_num - 1
        if 0 <= context_idx < len(citations):
            # Use 1-based citation number for display
            citation_num = context_idx + 1
            return f"[Citation {citation_num}]"
        else:
            # Invalid context reference, keep original
            return match.group(0)
    
    return re.sub(pattern, replace_match, text)


@router.post("", response_model=QueryResponse)
async def query_documents(request: QueryRequest) -> QueryResponse:
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
        embedder = Embedder()
        query_embedding = embedder.generate_embedding(request.query)

        # Search vector store
        vector_store = VectorStore()
        top_k = request.top_k or settings.top_k

        # STEP 5: Pass document_id to enforce document-scoped queries
        search_results = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_id=request.document_id,  # Filter to specific document if provided
        )

        # Convert search results to citations (metadata only)
        citations = []
        citation_text_map = {}  # Map citation index to text for LLM context
        
        for idx, result in enumerate(search_results):
            metadata = result.get("metadata", {})
            document_id = metadata.get("document_id", "")
            chunk_index = int(metadata.get("chunk_index", 0)) if metadata.get("chunk_index") else 0
            filename = metadata.get("filename", f"{document_id}.pdf")
            text = result.get("text", "")
            score = result.get("score", 0.0)

            citation = Citation(
                document_id=document_id,
                filename=filename,
                chunk_index=chunk_index,
                similarity_score=score,
            )
            citations.append(citation)
            
            # Store text for LLM context using the index in citations list
            citation_text_map[idx] = text

        # Calculate confidence from top similarity score
        # Confidence is the highest similarity score (0.0 to 1.0)
        confidence = citations[0].similarity_score if citations else 0.0

        # Fallback for document-scoped queries with no semantic matches
        # If querying a specific document and got 0 citations, retrieve chunks directly
        if not citations and request.document_id:
            logger.info(
                f"Semantic search returned 0 results for document-scoped query. "
                f"Falling back to direct document chunk retrieval for document {request.document_id}"
            )
            fallback_chunks = vector_store.get_document_chunks(
                document_id=request.document_id,
                limit=top_k,
            )
            
            # Convert fallback chunks to citations (same format as search results)
            for idx, chunk in enumerate(fallback_chunks):
                metadata = chunk.get("metadata", {})
                doc_id = metadata.get("document_id", request.document_id)
                chunk_index = int(metadata.get("chunk_index", 0)) if metadata.get("chunk_index") else 0
                filename = metadata.get("filename", f"{doc_id}.pdf")
                text = chunk.get("text", "")
                score = chunk.get("score", 1.0)  # Full score for direct retrieval
                
                citation = Citation(
                    document_id=doc_id,
                    filename=filename,
                    chunk_index=chunk_index,
                    similarity_score=score,
                )
                citations.append(citation)
                citation_text_map[idx] = text
            
            confidence = 1.0 if fallback_chunks else 0.0
            logger.info(
                f"Fallback retrieval found {len(citations)} chunks from document {request.document_id}"
            )

        # STEP 6: Log scope information
        scope_info = f"document_id={request.document_id}" if request.document_id else "all documents"
        logger.info(
            f"Query '{request.query[:50]}...' returned {len(citations)} results "
            f"with confidence {confidence:.3f} (scope: {scope_info})"
        )

        # Generate answer using LLM with retrieved context
        answer = ""
        max_chunks = settings.max_context_chunks  # Define outside try block
        
        if citations:
            try:
                llm_service = LLMService()
                # Limit context chunks to reduce memory usage
                # Take top N chunks (most relevant) and truncate if too long
                limited_citations = citations[:max_chunks]
                
                # Extract and truncate text from citations for context
                context_chunks = []
                for idx, citation in enumerate(limited_citations):
                    chunk_text = citation_text_map.get(idx, "")
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
                    max_tokens=settings.max_tokens,
                )
                logger.info(f"Generated answer using LLM ({len(answer)} characters)")
                
                # STEP 7: Process answer to map [Context N] references to citation indices
                # Replace [Context N] with [Citation N] where N maps to the citation index
                answer = replace_context_refs(answer, limited_citations)
                
                # Remove any "Sources:" section that might have been added by old code
                # The citations are already in the citations array, no need to duplicate
                answer = re.sub(r'\n\n\*\*Sources:\*\*\n.*', '', answer, flags=re.DOTALL)
                
            except Exception as e:
                # If LLM fails, log error but don't fail the request
                logger.error(f"LLM generation failed: {str(e)}")
                answer = (
                    "I found relevant information in the documents, but couldn't generate "
                    "a summary. The relevant sources are listed below."
                )
                
                # Still append sources even if LLM failed
                if citations:
                    answer += "\n\n**Sources:**\n"
                    seen_docs = set()
                    citation_num = 1
                    for citation in citations[:max_chunks]:
                        if citation.document_id not in seen_docs:
                            answer += f"[{citation_num}] {citation.filename} (similarity: {citation.similarity_score:.2f})\n"
                            seen_docs.add(citation.document_id)
                            citation_num += 1
        else:
            # No citations found
            answer = "I couldn't find any relevant information in the documents to answer your question."
            confidence = 0.0

        # Prepare metadata
        unique_documents = set(citation.document_id for citation in citations)
        metadata = {
            "total_results": len(citations),
            "sources_count": len(unique_documents) if citations else 0,
            "query": request.query,
            "top_k_used": top_k,
        }
        
        return QueryResponse(
            answer=answer,
            confidence=confidence,
            citations=citations,
            metadata=metadata,
        )

    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}",
        )
