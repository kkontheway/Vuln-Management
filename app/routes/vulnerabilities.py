"""Vulnerability management routes using FastAPI routers."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.services import vulnerability_service as vuln_service
from app.utils.auth import auth_guard

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Vulnerabilities"],
    dependencies=[Depends(auth_guard)],
)


@router.get("/vulnerabilities")
def get_vulnerabilities(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    vuln_id: Optional[str] = Query(default=None, alias="id"),
):
    """Get vulnerability list with pagination and filters."""
    try:
        filters: dict[str, object] = {}
        filter_fields = [
            "cve_id",
            "device_name",
            "os_platform",
            "os_version",
            "software_vendor",
            "software_name",
            "vulnerability_severity_level",
            "status",
            "exploitability_level",
            "rbac_group_name",
            "cve_public_exploit",
        ]

        query = request.query_params
        for field in filter_fields:
            if field == "software_vendor":
                values = query.getlist(field)
                if values:
                    filters[field] = values
            else:
                value = query.get(field)
                if value:
                    filters[field] = value

        threat_intel_values = query.getlist("threat_intel")
        if threat_intel_values:
            filters["threat_intel"] = threat_intel_values

        for name in ("cvss_min", "cvss_max", "epss_min", "epss_max", "date_from", "date_to"):
            value = query.get(name)
            if value:
                filters[name] = value

        result = vuln_service.get_vulnerabilities(
            filters=filters if filters else None,
            page=page,
            per_page=per_page,
            vuln_id=vuln_id,
        )
        return result
    except Exception as exc:  # noqa: BLE001
        logger.error("获取漏洞数据时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/patch-this")
def get_patch_this(
    limit: Optional[int] = Query(default=None, ge=1),
    vendor_scope: Optional[str] = Query(default=None),
):
    """Return high-priority vulnerabilities for PatchThis widget."""
    try:
        data = vuln_service.get_patchthis_vulnerabilities(limit=limit, vendor_scope=vendor_scope)
        return {"data": data}
    except Exception as exc:  # noqa: BLE001
        logger.error("获取PatchThis数据时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/statistics")
def get_statistics():
    """Get vulnerability statistics for charts."""
    try:
        return vuln_service.get_statistics()
    except Exception as exc:  # noqa: BLE001
        logger.error("获取统计信息时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/unique-cve-count")
def get_unique_cve_count():
    """Get count of unique CVE IDs."""
    try:
        return vuln_service.get_unique_cve_count()
    except Exception as exc:  # noqa: BLE001
        logger.error("获取去重CVE数量时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/severity-counts")
def get_severity_counts():
    """Get vulnerability counts by severity level."""
    try:
        return vuln_service.get_severity_counts()
    except Exception as exc:  # noqa: BLE001
        logger.error("获取严重程度统计时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/filter-options")
def get_filter_options():
    """Get filter option lists for dropdowns."""
    try:
        return vuln_service.get_filter_options()
    except Exception as exc:  # noqa: BLE001
        logger.error("获取过滤选项时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/fixed-vulnerabilities")
def get_fixed_vulnerabilities(limit: int = Query(50, ge=1, le=500)):
    """Get list of fixed vulnerabilities."""
    try:
        result = vuln_service.get_fixed_vulnerabilities(limit=limit)
        return {"data": result}
    except Exception as exc:  # noqa: BLE001
        logger.error("获取已修复漏洞列表时出错: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/vulnerability-catalog/{cve_id}")
def get_vulnerability_catalog_entry(cve_id: str):
    """Get catalog metadata for a specific CVE."""
    try:
        result = vuln_service.get_catalog_details(cve_id)
        if not result:
            raise HTTPException(status_code=404, detail="Catalog entry not found")
        return result
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Error fetching catalog entry for %s: %s", cve_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
