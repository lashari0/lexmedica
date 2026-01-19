"""LLM service for generating answers from retrieved context."""

import logging
from typing import List, Optional

import requests

from app.services.models.generators import (
    generate_with_huggingface,
    generate_with_ollama,
)
from app.services.models.prompt_builder import (
    build_rag_prompt,
    violates_summary_contract,
)
from app.utils.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating answers using LLM with RAG context."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM service.

        Args:
            provider: LLM provider ('ollama' or 'huggingface'), defaults to settings
            model: Model name, defaults to settings
        """
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.ollama_base_url = settings.ollama_base_url.rstrip('/')

        if self.provider == "ollama":
            self._initialize_ollama()

    def _initialize_ollama(self):
        """Initialize Ollama and verify model availability."""
        tags_url = f"{self.ollama_base_url}/api/tags"
        
        try:
            response = requests.get(tags_url, timeout=5)
            response.raise_for_status()
            tags_data = response.json()
            
            # Extract model names from response
            models_list = tags_data.get("models", [])
            model_names = []
            for m in models_list:
                if isinstance(m, dict):
                    # Model name can be in "name" or "model" field
                    name = m.get("name") or m.get("model", "")
                    if name:
                        model_names.append(name)
                elif isinstance(m, str):
                    model_names.append(m)
            
            if self.model not in model_names:
                logger.warning(
                    f"Model {self.model} not found in Ollama. Available models: {model_names}. "
                    f"Will attempt to use it anyway (Ollama may pull it automatically)."
                )
            else:
                logger.info(
                    f"Ollama initialized with model: {self.model} "
                    f"(available models: {len(model_names)})"
                )
        except requests.exceptions.RequestException as req_error:
            logger.warning(
                f"Could not connect to Ollama at {tags_url}: {str(req_error)}. "
                f"Will attempt to use {self.model} anyway."
            )
        except Exception as e:
            logger.warning(
                f"Could not list Ollama models: {str(e)}. "
                f"Will attempt to use {self.model} anyway."
            )

    def generate_answer(
        self,
        query: str,
        context_chunks: List[str],
        max_tokens: int = 500,
    ) -> str:
        """
        Generate answer from query and context chunks using LLM.

        Args:
            query: User query/question
            context_chunks: List of text chunks retrieved from documents
            max_tokens: Maximum tokens in response

        Returns:
            Generated answer string

        Raises:
            RuntimeError: If LLM generation fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not context_chunks:
            return "I couldn't find any relevant information in the documents to answer your question."

        # Build RAG prompt with context
        prompt, is_document_question = build_rag_prompt(
            query, context_chunks, self.model
        )

        try:
            if self.provider == "ollama":
                # Use lower temperature for document questions (more constrained)
                temperature = 0.3 if is_document_question else 0.7
                answer = generate_with_ollama(
                    prompt, max_tokens, self.model, self.ollama_base_url, temperature
                )

                # Post-generation validation for document questions
                if is_document_question and violates_summary_contract(answer):
                    logger.warning(
                        f"Answer violates summary contract, regenerating. "
                        f"Original answer length: {len(answer)}"
                    )
                    # Regenerate with reminder
                    reminder = "\n\nREMINDER: Follow DOCUMENT CHARACTERIZATION RULES strictly. Use neutral verbs (examines, discusses, analyzes). Do NOT use 'focuses on', 'emphasizes', 'highlights', or scope-generalizing terms."
                    answer = generate_with_ollama(
                        prompt + reminder,
                        max_tokens,
                        self.model,
                        self.ollama_base_url,
                        temperature,
                    )
                return answer
            elif self.provider == "huggingface":
                return generate_with_huggingface(prompt, max_tokens, self.model)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate answer: {str(e)}")

