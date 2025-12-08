"""NVD API client for fetching CVE metadata."""
from __future__ import annotations

import logging
from typing import Optional

import requests

from app.integrations.nvd.config import (
    NVD_API_BASE_URL,
    NVD_API_KEY,
    NVD_API_TIMEOUT,
)

logger = logging.getLogger(__name__)


def _extract_english_description(payload: dict) -> Optional[str]:
    """Return the English description string from NVD response payload."""
    vulnerabilities = payload.get("vulnerabilities") or []
    for item in vulnerabilities:
        cve_block = item.get("cve") or {}
        descriptions = cve_block.get("descriptions") or []
        for description in descriptions:
            if description.get("lang") == "en" and description.get("value"):
                return description["value"].strip()
    return None


def fetch_cve_description(cve_id: str) -> Optional[str]:
    """Fetch CVE description text from NVD.

    Args:
        cve_id: CVE identifier, e.g. "CVE-2023-12345".

    Returns:
        The English description string if available, otherwise None.
    """
    if not cve_id:
        return None

    headers = {
        "User-Agent": "VulnManagement/1.0",
    }
    if NVD_API_KEY:
        headers["apiKey"] = NVD_API_KEY

    params = {"cveId": cve_id}
    response = None
    try:
        response = requests.get(
            NVD_API_BASE_URL,
            params=params,
            headers=headers,
            timeout=NVD_API_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        status = response.status_code if response is not None else "unknown"
        if status == 404:
            logger.info("CVE %s not found in NVD", cve_id)
        elif status == 429:
            logger.warning("NVD API rate limit hit while requesting %s", cve_id)
        else:
            logger.error(
                "HTTP error from NVD for %s (status=%s): %s",
                cve_id,
                status,
                exc,
            )
        return None
    except requests.exceptions.RequestException as exc:
        logger.error("Error calling NVD API for %s: %s", cve_id, exc)
        return None

    try:
        payload = response.json()
    except ValueError:
        logger.warning("Failed to decode NVD response JSON for %s", cve_id)
        return None

    description = _extract_english_description(payload)
    if not description:
        logger.info("NVD response for %s did not contain an English description", cve_id)
    return description
