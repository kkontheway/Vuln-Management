"""Recommendation report routes for FastAPI."""
import logging
from typing import Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query

from app.services import recommendation_service as rec_service
from app.services import vulnerability_service as vuln_service
from app.utils.auth import auth_guard

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/recommendations",
    tags=["Recommendations"],
    dependencies=[Depends(auth_guard)],
)


@router.get("/check/{cve_id}")
def check_existing_report(cve_id: str):
    """Check if a report exists for the given CVE within the last 7 days."""
    try:
        result = rec_service.check_existing_report(cve_id)
        if result:
            return {"exists": True, "report": result}
        return {"exists": False}
    except Exception as exc:  # noqa: BLE001
        logger.error("Error checking existing report: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/generate")
def generate_report(payload: Dict = Body(...)):
    """Generate a recommendation report for a CVE using existing vulnerability data."""
    try:
        cve_id = payload.get("cve_id", "").strip()
        force_generate = payload.get("force", False)

        if not cve_id:
            raise HTTPException(status_code=400, detail="CVE ID is required")

        if not force_generate:
            existing = rec_service.check_existing_report(cve_id)
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "Report already exists",
                        "exists": True,
                        "report": existing,
                    },
                )

        report_content = rec_service.build_report_from_data(cve_id)
        report_id = rec_service.save_report(cve_id, report_content, "")

        return {
            "success": True,
            "report_id": report_id,
            "cve_id": cve_id,
            "message": "Report generated successfully",
        }

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Error generating report: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/history")
def get_report_history(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    """Get report history."""
    try:
        reports = rec_service.get_report_history(limit=limit, offset=offset)
        return {"reports": reports, "total": len(reports)}
    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting report history: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{report_id}")
def get_report(report_id: int = Path(..., ge=1)):
    """Get a specific report by ID."""
    try:
        report = rec_service.get_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"report": report}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting report: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/cve/{cve_id}")
def get_report_by_cve(cve_id: str):
    """Get the latest report for a CVE ID."""
    try:
        report = rec_service.get_report_by_cve_id(cve_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"report": report}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting report by CVE: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{report_id}/vulnerabilities")
def get_cve_vulnerabilities_by_report(report_id: int = Path(..., ge=1)):
    """Get vulnerability data for a CVE ID from a report."""
    try:
        report = rec_service.get_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        cve_id = report.get("cve_id")
        if not cve_id:
            raise HTTPException(status_code=400, detail="CVE ID not found in report")

        report_data = vuln_service.get_cve_vulnerability_report_data(cve_id, device_limit=50)
        if not report_data:
            raise HTTPException(status_code=404, detail="No vulnerability data found")
        return report_data
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting CVE vulnerabilities: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/cve/{cve_id}/vulnerabilities")
def get_cve_vulnerabilities_by_cve(cve_id: str):
    """Get vulnerability data for a CVE ID directly."""
    try:
        if not cve_id:
            raise HTTPException(status_code=400, detail="CVE ID is required")
        report_data = vuln_service.get_cve_vulnerability_report_data(cve_id, device_limit=50)
        if not report_data:
            raise HTTPException(status_code=404, detail="Vulnerability data not found")
        return report_data
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting CVE vulnerabilities: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
