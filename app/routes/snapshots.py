"""Snapshot routes using FastAPI."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.services import snapshot_service as snapshot_svc
from app.utils.auth import auth_guard

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Snapshots"],
    dependencies=[Depends(auth_guard)],
)


@router.post("/create-initial-snapshot")
def create_initial_snapshot():
    """Create initial vulnerability snapshot."""
    try:
        return snapshot_svc.create_initial_snapshot()
    except ImportError as exc:
        logger.error("导入defender模块失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"Import error: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("创建初始快照时出错: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating snapshot: {exc}") from exc


@router.get("/snapshots")
def get_snapshots(limit: int = Query(100, ge=1, le=500)):
    """Get list of vulnerability snapshots."""
    try:
        return snapshot_svc.get_snapshots(limit=limit)
    except Exception as exc:  # noqa: BLE001
        logger.error("获取快照列表时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/snapshots/{snapshot_id}/details")
def get_snapshot_details(snapshot_id: int = Path(..., ge=1)):
    """Get detailed information for a specific snapshot."""
    try:
        return snapshot_svc.get_snapshot_details(snapshot_id)
    except Exception as exc:  # noqa: BLE001
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        logger.error("获取快照详情时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/cve-history/{cve_id}")
def get_cve_history(cve_id: str):
    """Get historical changes for a specific CVE."""
    try:
        return snapshot_svc.get_cve_history(cve_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("获取CVE历史时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/snapshots/trend")
def get_snapshots_trend():
    """Get snapshot trend data for line chart."""
    try:
        return snapshot_svc.get_snapshots_trend()
    except Exception as exc:  # noqa: BLE001
        logger.error("获取快照趋势数据时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
