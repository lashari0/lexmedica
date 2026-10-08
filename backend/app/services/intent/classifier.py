"""LLM-based intent classifier for user queries."""

import logging
import re

from app.services.intent import QueryIntent
from app.services.models.generators import (
    generate_with_huggingface,
    generate_with_ollama,
)
from app.utils.config import settings

logger = logging.getLogger(__name__)

CLASSIFY_SYSTEM = (
    "You classify medical document queries. "
    "Reply with exactly one word: DOCUMENT_SUMMARY, MAIN_FINDINGS, or FACTUAL."
)
CLASSIFY_USER_TEMPLATE = (
    "DOCUMENT_SUMMARY = what the document is about / purpose / scope. "
    "MAIN_FINDINGS = key conclusions / takeaways / main points. "
    "FACTUAL = specific fact lookup.\n\nQuery: {query}"
)
CLASSIFY_MAX_TOKENS = 10
CLASSIFY_TEMPERATURE = 0.0

# Map normalized classifier output to enum
_INTENT_MAP = {
    "DOCUMENT_SUMMARY": QueryIntent.DOCUMENT_SUMMARY,
    "MAIN_FINDINGS": QueryIntent.MAIN_FINDINGS,
    "FACTUAL": QueryIntent.FACTUAL,
}


def _build_classify_prompt(query: str) -> str:
    """Build a single prompt for the generate API (system + user combined)."""
    user_part = CLASSIFY_USER_TEMPLATE.format(query=query)
    return f"{CLASSIFY_SYSTEM}\n\n{user_part}"


def _parse_classifier_response(raw: str) -> QueryIntent:
    """Parse LLM reply to QueryIntent; return FACTUAL if unparseable."""
    if not raw or not raw.strip():
        return QueryIntent.FACTUAL
    text = raw.strip().upper()
    # First line or first token (split on whitespace/punctuation)
    first_line = text.split("\n")[0].strip()
    first_token = re.split(r"[\s,.;:]+", first_line)[0] if first_line else ""
    return _INTENT_MAP.get(first_token, QueryIntent.FACTUAL)


def classify_intent(query: str) -> QueryIntent:
    """
    Classify user query into one of DOCUMENT_SUMMARY, MAIN_FINDINGS, FACTUAL.

    Uses a single LLM call with a fixed prompt. On exception or invalid output,
    returns FACTUAL.

    Args:
        query: User query string.

    Returns:
        QueryIntent enum value.
    """
    if not query or not query.strip():
        return QueryIntent.FACTUAL

    prompt = _build_classify_prompt(query)

    try:
        provider = settings.llm_provider
        model = settings.llm_model
        ollama_base_url = settings.ollama_base_url.rstrip("/")

        if provider == "ollama":
            raw = generate_with_ollama(
                prompt,
                CLASSIFY_MAX_TOKENS,
                model,
                ollama_base_url,
                temperature=CLASSIFY_TEMPERATURE,
            )
        elif provider == "huggingface":
            raw = generate_with_huggingface(prompt, CLASSIFY_MAX_TOKENS, model)
        else:
            logger.warning(f"Unknown LLM provider {provider}, defaulting to FACTUAL")
            return QueryIntent.FACTUAL

        intent = _parse_classifier_response(raw)
        logger.debug(f"Classified query intent: {intent.value} (raw: {raw!r})")
        return intent

    except Exception as e:
        logger.warning(f"Intent classification failed, defaulting to FACTUAL: {e}")
        return QueryIntent.FACTUAL
