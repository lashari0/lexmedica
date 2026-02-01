"""STEP 11: Audit event endpoint for document_selected and other client-driven events."""

from fastapi import APIRouter, HTTPException

from app.models import AuditEventRequest
from app.utils.audit import log_audit_event

router = APIRouter(prefix="/api/audit", tags=["audit"])


ALLOWED_EVENTS = {"document_selected"}


@router.post("", status_code=204)
async def post_audit_event(request: AuditEventRequest) -> None:
    """
    Log an audit event from the client (e.g. document_selected).
    Returns 204 No Content on success.
    """
    if request.event not in ALLOWED_EVENTS:
        raise HTTPException(status_code=400, detail=f"Unknown event: {request.event}")
    if request.event == "document_selected" and not request.document_id:
        raise HTTPException(
            status_code=400,
            detail="document_id required for document_selected event",
        )
    log_audit_event(request.event, document_id=request.document_id)
    return None
