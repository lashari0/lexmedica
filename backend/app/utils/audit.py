"""
STEP 11: Structured audit logging for regulatory defensibility and analysis.

Events: document_selected, query (with scope_expanded, refusal, citation_count, etc.).
One JSON object per line for easy parsing.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


AUDIT_LOGGER_NAME = "audit"


def log_audit_event(event: str, **kwargs: Any) -> None:
    """
    Log a structured audit event as one JSON line.

    Args:
        event: Event type (e.g. "document_selected", "query").
        **kwargs: Event-specific fields (e.g. document_id, scope_expanded, refusal).
    """
    payload = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }
    logger = logging.getLogger(AUDIT_LOGGER_NAME)
    # Ensure we don't log None values that might break JSON; drop them
    payload = {k: v for k, v in payload.items() if v is not None}
    message = json.dumps(payload)
    logger.info(message)


def setup_audit_logging(audit_log_file: Optional[Path] = None) -> None:
    """
    Configure the audit logger. If audit_log_file is set, add a file handler
    that writes one JSON line per log record. Otherwise audit uses root handlers (stdout).

    Args:
        audit_log_file: Optional path for audit log file.
    """
    logger = logging.getLogger(AUDIT_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Clear existing handlers so we don't duplicate if called again
    logger.handlers.clear()

    if audit_log_file:
        audit_log_file = Path(audit_log_file)
        audit_log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(audit_log_file, encoding="utf-8")
        handler.setLevel(logging.INFO)
        # Log message is already JSON from log_audit_event; no extra formatting
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    else:
        # Console: same, message is already JSON
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
