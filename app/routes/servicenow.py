"""ServiceNow integration routes for FastAPI."""
import logging
from typing import Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.services.integration_settings_service import (
    PROVIDER_SERVICENOW,
    integration_settings_service,
)
from app.utils.auth import auth_guard
from servicenow_client import ServiceNowClient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/servicenow",
    tags=["ServiceNow"],
    dependencies=[Depends(auth_guard)],
)


def _resolve_servicenow_context():
    """Load runtime ServiceNow client and metadata from settings service."""
    runtime = integration_settings_service.get_runtime_credentials(PROVIDER_SERVICENOW)
    if not runtime:
        return None, None
    metadata = runtime.get("metadata") or {}
    secrets = runtime.get("secrets") or {}
    try:
        client = ServiceNowClient(
            instance_url=metadata.get("instance_url", ""),
            username=metadata.get("username", ""),
            password=secrets.get("password", ""),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to init ServiceNow client: %s", exc, exc_info=True)
        return None, metadata
    return client, metadata


@router.get("/tickets")
def list_servicenow_tickets(
    table: Optional[str] = Query(default=None),
    query: Optional[str] = Query(default=None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """ServiceNow tickets list endpoint."""
    try:
        client, metadata = _resolve_servicenow_context()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ServiceNow is not configured. Please configure it in settings.",
            )
        default_table = metadata.get("default_table", "incident") if metadata else "incident"
        target_table = table or default_table
        tickets = client.get_tickets(
            table=target_table,
            sysparm_query=query,
            sysparm_limit=limit,
            sysparm_offset=offset,
        )
        return {"tickets": tickets, "total": len(tickets)}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("ServiceNow tickets error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/tickets")
def create_servicenow_ticket(payload: Dict = Body(...)):
    """Create ServiceNow ticket."""
    try:
        client, metadata = _resolve_servicenow_context()
        if not client:
            raise HTTPException(status_code=400, detail="ServiceNow is not configured. Please configure it in settings.")
        default_table = metadata.get("default_table", "incident") if metadata else "incident"
        target_table = payload.get("table", default_table)
        ticket_data = {
            "short_description": payload.get("short_description", ""),
            "description": payload.get("description", ""),
            "category": payload.get("category", ""),
            "priority": payload.get("priority", "3"),
            "urgency": payload.get("urgency", "3"),
            "impact": payload.get("impact", "3"),
        }
        ticket_data = {k: v for k, v in ticket_data.items() if v}
        ticket = client.create_ticket(table=target_table, **ticket_data)
        return JSONResponse(
            {
                "ticket": ticket,
                "ticket_number": ticket.get("number", ticket.get("sys_id")),
                "sys_id": ticket.get("sys_id"),
            },
            status_code=status.HTTP_201_CREATED,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("ServiceNow tickets error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tickets/{ticket_id}")
def servicenow_ticket_detail(ticket_id: str, table: Optional[str] = Query(default=None)):
    """Get ServiceNow ticket detail."""
    try:
        client, metadata = _resolve_servicenow_context()
        if not client:
            raise HTTPException(status_code=400, detail="ServiceNow is not configured")
        default_table = metadata.get("default_table", "incident") if metadata else "incident"
        target_table = table or default_table
        ticket = client.get_ticket(table=target_table, sys_id=ticket_id)
        return {"ticket": ticket}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("ServiceNow ticket detail error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tickets/{ticket_id}/notes")
def get_servicenow_ticket_notes(ticket_id: str, table: Optional[str] = Query(default=None)):
    """Get notes for a ServiceNow ticket."""
    try:
        client, metadata = _resolve_servicenow_context()
        if not client:
            raise HTTPException(status_code=400, detail="ServiceNow is not configured")
        default_table = metadata.get("default_table", "incident") if metadata else "incident"
        target_table = table or default_table
        notes = client.get_ticket_notes(table=target_table, sys_id=ticket_id)
        return {"notes": notes, "total": len(notes)}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("ServiceNow notes error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/tickets/{ticket_id}/notes")
def add_servicenow_ticket_note(
    ticket_id: str,
    payload: Dict = Body(...),
    table: Optional[str] = Query(default=None),
):
    """Add note for a ServiceNow ticket."""
    try:
        client, metadata = _resolve_servicenow_context()
        if not client:
            raise HTTPException(status_code=400, detail="ServiceNow is not configured")
        default_table = metadata.get("default_table", "incident") if metadata else "incident"
        target_table = table or default_table
        note_text = payload.get("note", "")
        if not note_text:
            raise HTTPException(status_code=400, detail="Note text is required")
        note = client.add_ticket_note(table=target_table, sys_id=ticket_id, note_text=note_text)
        return JSONResponse({"note": note, "message": "Note added successfully"}, status_code=status.HTTP_201_CREATED)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("ServiceNow notes error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/test-connection")
def servicenow_test_connection(payload: Dict = Body(...)):
    """Test ServiceNow connection."""
    try:
        metadata = {
            "instance_url": payload.get("instance_url", "").rstrip("/"),
            "username": payload.get("username"),
        }
        secrets = {"password": payload.get("password")}
        result = integration_settings_service.test_provider(PROVIDER_SERVICENOW, metadata, secrets)
        status_code = result.pop("status_code", 200)
        return JSONResponse(result, status_code=status_code)
    except Exception as exc:  # noqa: BLE001
        logger.error("ServiceNow connection test error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/health")
def servicenow_health_check():
    """Return basic health information for the ServiceNow integration."""
    try:
        client, _ = _resolve_servicenow_context()
        if not client:
            raise HTTPException(status_code=400, detail="ServiceNow is not configured")
        is_healthy = client.test_connection()
        status_payload = integration_settings_service.get_setting_summary(PROVIDER_SERVICENOW).get("status", {})
        return {
            "healthy": is_healthy,
            "status": status_payload.get("last_test_status"),
            "last_tested_at": status_payload.get("last_tested_at"),
            "message": status_payload.get("last_test_message"),
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("ServiceNow health check error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
