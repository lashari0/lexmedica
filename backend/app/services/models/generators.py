"""LLM generation methods for different providers."""

import logging
from typing import Optional

import requests

from app.utils.config import settings

logger = logging.getLogger(__name__)


def generate_with_ollama(
    prompt: str,
    max_tokens: int,
    model: str,
    ollama_base_url: str,
    temperature: float = 0.1,
) -> str:
    """
    Generate answer using Ollama /api/generate endpoint.

    Args:
        prompt: Full prompt with context
        max_tokens: Maximum tokens in response
        model: Model name
        ollama_base_url: Base URL for Ollama API
        temperature: Sampling temperature (0.3 for document questions, 0.7 for factual)

    Returns:
        Generated answer

    Raises:
        RuntimeError: If generation fails
    """
    try:
        # Use Ollama /api/generate endpoint directly
        generate_url = f"{ollama_base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "num_predict": 4096,  # Max tokens to generate
                "temperature": temperature,
                "stop": ["<|im_end|>"],  # CRITICAL: stops at end of assistant turn
                "repeat_penalty": 1.0,  # No extra repetition penalty
                "repeat_last_n": 64,  # Look back 64 tokens for repeats
                "top_k": 40,  # Consider top 40 tokens
                "top_p": 0.9,  # Nucleus sampling
                "min_p": 0.05,  # Optional: ignore very low-prob tokens
                "num_ctx": 8192,  # Use full context window (if model supports it)
            },
            "stream": False,
        }

        logger.debug(f"Calling Ollama /api/generate with model: {model}")
        response = requests.post(generate_url, json=payload, timeout=120)  # 2 minute timeout
        response.raise_for_status()

        result = response.json()

        # Extract answer from response
        # Ollama /api/generate returns: {"response": "text...", "done": true, ...}
        answer = result.get("response", "").strip()
        done_reason = result.get("done_reason", "")
        is_qwen = "qwen" in model.lower()

        # Handle thinking mode for Qwen models
        if not answer and is_qwen:
            thinking = result.get("thinking", "")
            if thinking and done_reason == "length":
                # Model hit token limit during thinking phase
                logger.error(
                    f"Qwen model {model} hit token limit ({max_tokens} tokens) "
                    f"during reasoning phase. Thinking length: {len(thinking)} chars. "
                    f"Recommended: increase max_tokens to at least {max_tokens * 2}"
                )
                raise RuntimeError(
                    f"Model {model} hit token limit ({max_tokens} tokens) during reasoning. "
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
                    f"Done reason: {done_reason}, Model: {model}. "
                    f"Full response keys: {list(result.keys())}"
                )
                raise RuntimeError("Ollama returned empty response")

        logger.info(f"Generated answer using Ollama ({model}): {len(answer)} characters")
        return answer

    except requests.exceptions.HTTPError as http_error:
        # Handle HTTP errors (like 500 for memory issues)
        error_msg = str(http_error)
        status_code = http_error.response.status_code if http_error.response else None

        # Try to extract error message from response
        try:
            error_data = http_error.response.json()
            error_detail = error_data.get("error", error_msg)
        except Exception:
            error_detail = error_msg

        # Check for memory-related errors
        if "memory" in error_detail.lower() or "system memory" in error_detail.lower():
            logger.error(
                f"Ollama memory error (HTTP {status_code}): {error_detail}. "
                f"Model {model} requires more memory than available."
            )
            raise RuntimeError(
                f"Model {model} requires more system memory than available. "
                f"Please use a smaller model (e.g., qwen2.5:3b, llama3.2:3b) or a quantized version. "
                f"Original error: {error_detail}"
            )
        else:
            logger.error(f"Ollama HTTP error ({status_code}): {error_detail}")
            raise RuntimeError(f"Ollama API request failed: {error_detail}")

    except requests.exceptions.RequestException as req_error:
        logger.error(f"Ollama connection error: {str(req_error)}")
        raise RuntimeError(
            f"Could not connect to Ollama at {ollama_base_url}. "
            f"Please ensure Ollama is running. Error: {str(req_error)}"
        )
    except RuntimeError:
        # Re-raise RuntimeError as-is (already formatted)
        raise
    except Exception as e:
        logger.error(f"Ollama generation error: {str(e)}", exc_info=True)
        raise RuntimeError(f"Ollama generation failed: {str(e)}")


def generate_with_huggingface(
    prompt: str,
    max_tokens: int,
    model: str,
) -> str:
    """
    Generate answer using Hugging Face API (fallback).

    Args:
        prompt: Full prompt with context
        max_tokens: Maximum tokens in response
        model: Model name

    Returns:
        Generated answer

    Raises:
        RuntimeError: If generation fails or API key not configured
    """
    if not settings.huggingface_api_key:
        raise RuntimeError("Hugging Face API key not configured")

    try:
        api_url = f"{settings.huggingface_api_url}/{model}"
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

        logger.info(f"Generated answer using Hugging Face ({model})")
        return answer

    except Exception as e:
        logger.error(f"Hugging Face generation error: {str(e)}")
        raise RuntimeError(f"Hugging Face generation failed: {str(e)}")
