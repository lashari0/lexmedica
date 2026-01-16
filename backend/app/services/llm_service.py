"""LLM service for generating answers from retrieved context."""

import logging
from typing import List, Optional

import requests

from app.config import settings

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
        try:
            # Test connection using /api/tags endpoint
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
                    logger.info(f"Ollama initialized with model: {self.model} (available models: {len(model_names)})")
            except requests.exceptions.RequestException as req_error:
                logger.warning(
                    f"Could not connect to Ollama at {tags_url}: {str(req_error)}. "
                    f"Will attempt to use {self.model} anyway."
                )
            except Exception as list_error:
                logger.warning(f"Could not list Ollama models: {str(list_error)}. Will attempt to use {self.model} anyway.")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {str(e)}")
            raise RuntimeError(
                f"Could not connect to Ollama at {self.ollama_base_url}. "
                f"Please ensure Ollama is running. Error: {str(e)}"
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
        prompt = self._build_rag_prompt(query, context_chunks)

        try:
            if self.provider == "ollama":
                return self._generate_with_ollama(prompt, max_tokens)
            elif self.provider == "huggingface":
                return self._generate_with_huggingface(prompt, max_tokens)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate answer: {str(e)}")

    def _build_rag_prompt(self, query: str, context_chunks: List[str]) -> str:
        """
        Build RAG prompt with context chunks.

        Args:
            query: User query
            context_chunks: Retrieved context chunks (already limited and truncated)

        Returns:
            Formatted prompt string
        """
        # Build context text with numbered chunks
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            context_parts.append(f"[Context {i}]\n{chunk}")
        context_text = "\n\n".join(context_parts)

        # Build concise prompt to reduce token usage
        prompt = f"""Answer the question based ONLY on the provided context.

Context:
{context_text}

Question: {query}

Answer:"""

        return prompt

    def _generate_with_ollama(self, prompt: str, max_tokens: int) -> str:
        """
        Generate answer using Ollama /api/generate endpoint.

        Args:
            prompt: Full prompt with context
            max_tokens: Maximum tokens in response

        Returns:
            Generated answer
        """
        try:
            # Use Ollama /api/generate endpoint directly
            generate_url = f"{self.ollama_base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                },
                "stream": False,  # Get complete response
            }

            logger.debug(f"Calling Ollama /api/generate with model: {self.model}")
            response = requests.post(generate_url, json=payload, timeout=120)  # 2 minute timeout
            response.raise_for_status()
            
            result = response.json()
            
            # Extract answer from response
            # Ollama /api/generate returns: {"response": "text...", "done": true, ...}
            answer = result.get("response", "").strip()
            
            if not answer:
                # Check if there's an error in the response
                error_msg = result.get("error", "")
                if error_msg:
                    raise RuntimeError(f"Ollama API error: {error_msg}")
                else:
                    logger.error(f"Ollama returned empty response. Full response: {result}")
                    raise RuntimeError("Ollama returned empty response")

            logger.info(f"Generated answer using Ollama ({self.model}): {len(answer)} characters")
            return answer

        except requests.exceptions.HTTPError as http_error:
            # Handle HTTP errors (like 500 for memory issues)
            error_msg = str(http_error)
            status_code = http_error.response.status_code if http_error.response else None
            
            # Try to extract error message from response
            try:
                error_data = http_error.response.json()
                error_detail = error_data.get("error", error_msg)
            except:
                error_detail = error_msg
            
            # Check for memory-related errors
            if "memory" in error_detail.lower() or "system memory" in error_detail.lower():
                logger.error(
                    f"Ollama memory error (HTTP {status_code}): {error_detail}. "
                    f"Model {self.model} requires more memory than available."
                )
                raise RuntimeError(
                    f"Model {self.model} requires more system memory than available. "
                    f"Please use a smaller model (e.g., qwen2.5:3b, llama3.2:3b) or a quantized version. "
                    f"Original error: {error_detail}"
                )
            else:
                logger.error(f"Ollama HTTP error ({status_code}): {error_detail}")
                raise RuntimeError(f"Ollama API request failed: {error_detail}")
                
        except requests.exceptions.RequestException as req_error:
            logger.error(f"Ollama connection error: {str(req_error)}")
            raise RuntimeError(
                f"Could not connect to Ollama at {self.ollama_base_url}. "
                f"Please ensure Ollama is running. Error: {str(req_error)}"
            )
        except RuntimeError:
            # Re-raise RuntimeError as-is (already formatted)
            raise
        except Exception as e:
            logger.error(f"Ollama generation error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Ollama generation failed: {str(e)}")

    def _generate_with_huggingface(self, prompt: str, max_tokens: int) -> str:
        """
        Generate answer using Hugging Face API (fallback).

        Args:
            prompt: Full prompt with context
            max_tokens: Maximum tokens in response

        Returns:
            Generated answer
        """
        if not settings.huggingface_api_key:
            raise RuntimeError("Hugging Face API key not configured")

        try:
            api_url = f"{settings.huggingface_api_url}/{self.model}"
            headers = {
                "Authorization": f"Bearer {settings.huggingface_api_key}",
            }
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.7,
                    "return_full_text": False,
                },
            }

            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            # Handle different response formats from Hugging Face
            if isinstance(result, list) and len(result) > 0:
                answer = result[0].get("generated_text", "").strip()
            elif isinstance(result, dict):
                answer = result.get("generated_text", "").strip()
            else:
                answer = str(result).strip()

            if not answer:
                raise RuntimeError("Hugging Face returned empty response")

            logger.info(f"Generated answer using Hugging Face ({self.model})")
            return answer

        except Exception as e:
            logger.error(f"Hugging Face generation error: {str(e)}")
            raise RuntimeError(f"Hugging Face generation failed: {str(e)}")
