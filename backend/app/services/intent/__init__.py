"""Query intent classification — types and classifier."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.services.intent.classifier import classify_intent


class QueryIntent(str, Enum):
    """Classified intent for a user query. Single source of truth for intent values."""

    DOCUMENT_SUMMARY = "DOCUMENT_SUMMARY"
    MAIN_FINDINGS = "MAIN_FINDINGS"
    FACTUAL = "FACTUAL"


class ClassificationResult(BaseModel):
    """Result of intent classification; carries intent and optional raw classifier output."""

    intent: QueryIntent
    raw: Optional[str] = None


__all__ = ["QueryIntent", "ClassificationResult", "classify_intent"]
