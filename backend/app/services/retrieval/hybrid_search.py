"""Hybrid search service combining semantic, lexical, and reranking."""

import logging
from typing import List, Dict, Any, Optional

from app.services.retrieval.vector_store import VectorStore
from app.services.retrieval.reranker import Reranker
from app.utils.config import settings

logger = logging.getLogger(__name__)


class HybridSearch:
    """Service for hybrid search combining semantic, lexical, and reranking."""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        reranker: Optional[Reranker] = None,
    ):
        """
        Initialize hybrid search service.

        Args:
            vector_store: Vector store instance (defaults to new instance)
            reranker: Reranker instance (defaults to new instance)
        """
        self.vector_store = vector_store or VectorStore()
        self.reranker = reranker or Reranker()

    def search(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int = None,
        document_id: Optional[str] = None,
        use_reranker: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic search with reranking.

        Args:
            query: Query text (for lexical/reranking)
            query_embedding: Query embedding vector (for semantic search)
            top_k: Number of results to return
            document_id: Optional filter by document ID
            use_reranker: Whether to use reranker (default: True)

        Returns:
            List of search results with scores
        """
        top_k = top_k or settings.top_k
        
        # Step 1: Semantic search
        semantic_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more results for reranking
            document_id=document_id,
        )
        
        if not semantic_results:
            logger.info("No semantic search results found")
            return []
        
        logger.debug(f"Semantic search returned {len(semantic_results)} results")
        
        # Step 2: Rerank results if enabled
        if use_reranker and self.reranker:
            reranked_results = self.reranker.rerank(
                query=query,
                results=semantic_results,
                top_k=top_k,
            )
            logger.debug(f"Reranking returned {len(reranked_results)} results")
            return reranked_results
        
        # Return top_k semantic results if reranking disabled
        return semantic_results[:top_k]
