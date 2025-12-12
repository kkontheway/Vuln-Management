"""Integration settings API routes."""
import logging
from typing import Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from app.services.integration_settings_service import (
    PROVIDER_AI,
    PROVIDER_SERVICENOW,
    integration_settings_service,
)
from app.utils.auth import auth_guard

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/integrations",
    tags=["Integrations"],
    dependencies=[Depends(auth_guard)],
)


@router.get("/settings")
def integration_settings_get(provider: str = Query(...)):
    """Retrieve integration settings."""
    try:
        return integration_settings_service.get_setting_summary(provider)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load integration settings: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/settings")
def integration_settings_post(payload: Dict = Body(...)):
    """Update integration settings."""
    provider = payload.get("provider")
    metadata = payload.get("metadata") or {}
    secrets = payload.get("secrets") or {}
    if not provider:
        raise HTTPException(status_code=400, detail="Provider is required")
    try:
        settings = integration_settings_service.save_settings(provider, metadata, secrets)
        return {"settings": settings}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to save integration settings: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save settings") from exc


@router.post("/settings/{provider}/test")
def test_integration(provider: str, payload: Optional[Dict] = Body(default=None)):
    """Test integration connectivity using stored or temporary credentials."""
    payload = payload or {}
    metadata = payload.get("metadata") or {}
    secrets = payload.get("secrets") or {}
    try:
        result = integration_settings_service.test_provider(provider, metadata, secrets)
        status_code = result.pop("status_code", 200)
        return JSONResponse(result, status_code=status_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Integration test failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/settings/{provider}/rotate")
def rotate_integration_secret(provider: str, payload: Dict = Body(...)):
    """Rotate integration secret by forcing a new secret payload."""
    secrets = payload.get("secrets") or {}
    if not secrets:
        raise HTTPException(status_code=400, detail="Secret payload is required for rotation")
    try:
        settings = integration_settings_service.save_settings(provider, None, secrets)
        return {
            "settings": settings,
            "message": "Secret rotated successfully",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Secret rotation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to rotate secret") from exc


@router.get("/providers")
def list_supported_providers():
    """Helper endpoint returning providers to drive UI drop-downs."""
    return {
        "providers": [
            {"id": PROVIDER_SERVICENOW, "label": "ServiceNow"},
            {"id": PROVIDER_AI, "label": "AI"},
        ]
    }
