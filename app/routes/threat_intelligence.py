"""Threat intelligence routes."""
import logging
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException

from app.services import recordfuture_service
from app.services import threat_intelligence_service as threat_svc
from app.utils.auth import auth_guard

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/threat-intelligence",
    tags=["Threat Intelligence"],
    dependencies=[Depends(auth_guard)],
)


@router.post("/extract-ip")
def extract_ip_addresses(payload: dict = Body(...)):
    """Extract IP addresses from text and generate CSV file."""
    try:
        text = payload.get("text", "")
        return threat_svc.extract_ip_addresses(text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Error extracting IP addresses: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/recordfuture/save")
def save_recordfuture_indicators(payload: dict = Body(...)):
    """Persist extracted indicators upon user confirmation."""
    try:
        ips: List[str] = payload.get("ips", [])
        cves: List[str] = payload.get("cves", [])
        source_text = payload.get("sourceText", "")
        return recordfuture_service.save_indicators(ips, cves, source_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Error saving RecordFuture indicators: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save indicators") from exc
