"""Sync routes for FastAPI."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from app.services import sync_service as sync_svc
from app.utils.auth import auth_guard

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Sync"],
    dependencies=[Depends(auth_guard)],
)


@router.get("/sync-status")
def get_sync_status():
    """Get sync status and last sync time."""
    try:
        return sync_svc.get_sync_status()
    except Exception as exc:  # noqa: BLE001
        logger.error("获取同步状态时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sync-progress")
def get_sync_progress():
    """Get current sync progress."""
    try:
        return sync_svc.get_sync_progress()
    except Exception as exc:  # noqa: BLE001
        logger.error("获取同步进度时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sync-sources")
def list_sync_sources():
    """List available sync sources."""
    try:
        return {"sources": sync_svc.list_sync_sources()}
    except Exception as exc:  # noqa: BLE001
        logger.error("列出同步源时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/sync")
def trigger_sync(payload: Optional[dict] = Body(default=None)):
    """Trigger data sync in background (full sync)."""
    try:
        payload = payload or {}
        data_sources = payload.get("data_sources") or None
        if data_sources is not None and not isinstance(data_sources, list):
            raise HTTPException(status_code=400, detail="data_sources must be a list")
        return sync_svc.trigger_sync(data_sources)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("触发同步时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
