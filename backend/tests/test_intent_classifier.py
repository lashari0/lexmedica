"""Unit tests for intent classifier (Step 2)."""

import pytest
from unittest.mock import patch

from app.services.intent import QueryIntent, classify_intent


@patch("app.services.intent.classifier.settings")
@patch("app.services.intent.classifier.generate_with_ollama")
def test_classify_intent_document_summary(mock_ollama, mock_settings):
    mock_settings.llm_provider = "ollama"
    mock_settings.llm_model = "test"
    mock_settings.ollama_base_url = "http://localhost:11434"
    mock_ollama.return_value = "DOCUMENT_SUMMARY"
    assert classify_intent("What is this document about?") == QueryIntent.DOCUMENT_SUMMARY
    mock_ollama.assert_called_once()


@patch("app.services.intent.classifier.settings")
@patch("app.services.intent.classifier.generate_with_ollama")
def test_classify_intent_main_findings(mock_ollama, mock_settings):
    mock_settings.llm_provider = "ollama"
    mock_settings.llm_model = "test"
    mock_settings.ollama_base_url = "http://localhost:11434"
    mock_ollama.return_value = "MAIN_FINDINGS"
    assert classify_intent("What are the main findings?") == QueryIntent.MAIN_FINDINGS
    mock_ollama.assert_called_once()


@patch("app.services.intent.classifier.settings")
@patch("app.services.intent.classifier.generate_with_ollama")
def test_classify_intent_factual(mock_ollama, mock_settings):
    mock_settings.llm_provider = "ollama"
    mock_settings.llm_model = "test"
    mock_settings.ollama_base_url = "http://localhost:11434"
    mock_ollama.return_value = "FACTUAL"
    assert classify_intent("What does it say about aspirin?") == QueryIntent.FACTUAL
    mock_ollama.assert_called_once()


@patch("app.services.intent.classifier.settings")
@patch("app.services.intent.classifier.generate_with_ollama")
def test_classify_intent_invalid_response_defaults_to_factual(mock_ollama, mock_settings):
    mock_settings.llm_provider = "ollama"
    mock_settings.llm_model = "test"
    mock_settings.ollama_base_url = "http://localhost:11434"
    mock_ollama.return_value = "GARBAGE"
    assert classify_intent("Anything") == QueryIntent.FACTUAL


@patch("app.services.intent.classifier.settings")
@patch("app.services.intent.classifier.generate_with_ollama")
def test_classify_intent_empty_response_defaults_to_factual(mock_ollama, mock_settings):
    mock_settings.llm_provider = "ollama"
    mock_settings.llm_model = "test"
    mock_settings.ollama_base_url = "http://localhost:11434"
    mock_ollama.return_value = ""
    assert classify_intent("Anything") == QueryIntent.FACTUAL


@patch("app.services.intent.classifier.settings")
@patch("app.services.intent.classifier.generate_with_ollama")
def test_classify_intent_exception_defaults_to_factual(mock_ollama, mock_settings):
    mock_settings.llm_provider = "ollama"
    mock_settings.llm_model = "test"
    mock_settings.ollama_base_url = "http://localhost:11434"
    mock_ollama.side_effect = RuntimeError("LLM unavailable")
    assert classify_intent("What are the main findings?") == QueryIntent.FACTUAL


def test_classify_intent_empty_query_returns_factual():
    assert classify_intent("") == QueryIntent.FACTUAL
    assert classify_intent("   ") == QueryIntent.FACTUAL
