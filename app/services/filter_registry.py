"""Filter configuration for vulnerability queries."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Field-level filter strategies
# strategy options: contains, equals, boolean, in
FILTER_FIELD_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "cve_id": {"column": "cve_id", "strategy": "contains"},
    "device_name": {"column": "device_name", "strategy": "contains"},
    "software_name": {"column": "software_name", "strategy": "contains"},
    "os_platform": {"column": "os_platform", "strategy": "equals"},
    "os_version": {"column": "os_version", "strategy": "equals"},
    "vulnerability_severity_level": {"column": "vulnerability_severity_level", "strategy": "equals"},
    "status": {"column": "status", "strategy": "equals"},
    "exploitability_level": {"column": "exploitability_level", "strategy": "equals"},
    "rbac_group_name": {"column": "rbac_group_name", "strategy": "equals"},
    "software_vendor": {"column": "software_vendor", "strategy": "in"},
    "cve_public_exploit": {"column": "cve_public_exploit", "strategy": "boolean"},
    "device_tag": {"column": "device_tag", "strategy": "in"},
}

# Numeric range filters
RANGE_FILTER_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "cvss_min": {"column": "cvss_score", "operator": ">=", "cast": float},
    "cvss_max": {"column": "cvss_score", "operator": "<=", "cast": float},
    "epss_min": {"column": "cve_epss", "operator": ">=", "cast": float},
    "epss_max": {"column": "cve_epss", "operator": "<=", "cast": float},
}

# Date filters (ISO strings)
DATE_FILTER_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "date_from": {"column": "last_seen_timestamp", "operator": ">="},
    "date_to": {"column": "last_seen_timestamp", "operator": "<="},
}


def normalize_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def parse_boolean(value: Any) -> Optional[bool]:
    if value in (None, "", "all"):
        return None
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return None
