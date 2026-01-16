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
        For Qwen models, use proper chat template format.

        Args:
            query: User query
            context_chunks: Retrieved context chunks (already limited and truncated)

        Returns:
            Formatted prompt string
        """
        # Check if this is a Qwen model
        is_qwen = "qwen" in self.model.lower()
        
        if is_qwen:
            # Qwen-specific chat template format
            context_text = "\n".join([
                f"### Context {i+1}:\n{chunk}" 
                for i, chunk in enumerate(context_chunks)
            ])
            
            prompt = f"""<|im_start|>system
You are a helpful AI assistant. Answer the question based on the provided context sections. Extract and use any relevant information from the context to answer the question. Be thorough and use all available information from the context. Only indicate lack of information if the context truly contains nothing relevant.<|im_end|>
<|im_start|>user
Context sections:
{context_text}

Question: {query}<|im_end|>
<|im_start|>assistant
"""
        else:
            # Standard format for other models
            context_parts = []
            for i, chunk in enumerate(context_chunks, 1):
                context_parts.append(f"[Context {i}]\n{chunk}")
            context_text = "\n\n".join(context_parts)
            
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
                    "num_predict": 800,          # Max tokens to generate (was 500 → too short)
                    "temperature": 0.7,          # Balanced creativity (0.5–0.8 is safe)
                    "stop": ["<|im_end|>"],      # CRITICAL: stops at end of assistant turn
                    "repeat_penalty": 1.0,       # No extra repetition penalty (Qwen handles well)
                    "repeat_last_n": 64,         # Look back 64 tokens for repeats (default)
                    "top_k": 40,                 # Consider top 40 tokens (standard)
                    "top_p": 0.9,                # Nucleus sampling (good balance)
                    "min_p": 0.05,               # Optional: ignore very low-prob tokens
                    "num_ctx": 8192,             # Use full context window (if model supports it)
                },
                "stream": False,
            }

            logger.debug(f"Calling Ollama /api/generate with model: {self.model}")
            response = requests.post(generate_url, json=payload, timeout=120)  # 2 minute timeout
            response.raise_for_status()
            
            result = response.json()
            
            # Extract answer from response
            # Ollama /api/generate returns: {"response": "text...", "done": true, ...}
            answer = result.get("response", "").strip()
            done_reason = result.get("done_reason", "")
            is_qwen = "qwen" in self.model.lower()
            
            # Handle thinking mode for Qwen models
            if not answer and is_qwen:
                thinking = result.get("thinking", "")
                if thinking and done_reason == "length":
                    # Model hit token limit during thinking phase
                    logger.error(
                        f"Qwen model {self.model} hit token limit ({max_tokens} tokens) "
                        f"during reasoning phase. Thinking length: {len(thinking)} chars. "
                        f"Recommended: increase max_tokens to at least {max_tokens * 2}"
                    )
                    raise RuntimeError(
                        f"Model {self.model} hit token limit ({max_tokens} tokens) during reasoning. "
                        f"Increase max_tokens in config (current: {max_tokens}). "
                        f"Recommended: {max_tokens * 2} tokens for reasoning models."
                    )
                elif thinking:
                    logger.warning(
                        f"Qwen model returned thinking but no response. "
                        f"Done reason: {done_reason}. Thinking length: {len(thinking)} chars. "
                        f"This may indicate a configuration issue."
                    )
            
            # Handle truncated responses
            if answer and done_reason == "length":
                answer += "\n\n[Note: Response may be truncated due to length limits.]"
                logger.warning(
                    f"LLM response was truncated (done_reason: length, "
                    f"response length: {len(answer)} chars, max_tokens: {max_tokens})"
                )
            
            if not answer:
                # Check if there's an error in the response
                error_msg = result.get("error", "")
                if error_msg:
                    raise RuntimeError(f"Ollama API error: {error_msg}")
                else:
                    logger.error(
                        f"Ollama returned empty response. "
                        f"Done reason: {done_reason}, Model: {self.model}. "
                        f"Full response keys: {list(result.keys())}"
                    )
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
