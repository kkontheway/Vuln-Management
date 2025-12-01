"""Download and synchronize Rapid7/Nuclei threat source data."""
import json
import logging
from typing import Dict, Iterable, List, Optional, Sequence, Set

import requests

from database import get_db_connection
from app.constants.database import (
    TABLE_VULNERABILITIES,
    TABLE_RAPID_VULNERABILITIES,
    TABLE_NUCLEI_VULNERABILITIES,
)

logger = logging.getLogger(__name__)

METASPLOIT_URL = "https://raw.githubusercontent.com/rapid7/metasploit-framework/master/db/modules_metadata_base.json"
NUCLEI_URL = "https://raw.githubusercontent.com/projectdiscovery/nuclei-templates/main/cves.json"

SEVERITY_ORDER = ["critical", "high", "medium", "low"]
SEVERITY_SCORE_MAP = {
    4: "Critical",
    3: "High",
    2: "Medium",
    1: "Low",
}


def _safe_float(value: Optional[str]) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _chunk(values: Sequence[str], size: int = 500) -> Iterable[Sequence[str]]:
    for idx in range(0, len(values), size):
        yield values[idx:idx + size]


def _download(url: str) -> Optional[requests.Response]:
    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        return response
    except Exception as exc:
        logger.error("Failed to download %s: %s", url, exc)
        return None


def _extract_metasploit_metadata() -> Dict[str, Dict[str, Optional[str]]]:
    response = _download(METASPLOIT_URL)
    if not response:
        return {}

    try:
        data = response.json()
    except Exception as exc:
        logger.error("Failed to parse Metasploit metadata: %s", exc)
        return {}

    if not isinstance(data, dict):
        logger.warning("Unexpected Metasploit metadata format")
        return {}

    result: Dict[str, Dict[str, Optional[str]]] = {}
    for module in data.values():
        if not isinstance(module, dict):
            continue
        refs = module.get("references")
        if not isinstance(refs, list):
            continue
        meta = {
            "title": module.get("name"),
            "description": module.get("description"),
            "severity": None,
            "cvss": _safe_float(module.get("cvss")) if module.get("cvss") else None,
        }
        for ref in refs:
            if isinstance(ref, str) and ref.upper().startswith("CVE-"):
                cve = ref.upper()
                # Only keep first occurrence; duplicates overwrite with same data
                result.setdefault(cve, meta)
    logger.info("Collected %d CVEs from Metasploit dataset", len(result))
    return result


def _extract_nuclei_metadata() -> Dict[str, Dict[str, Optional[str]]]:
    response = _download(NUCLEI_URL)
    if not response:
        return {}

    result: Dict[str, Dict[str, Optional[str]]] = {}
    for line in response.text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            logger.debug("Skipping malformed nuclei line")
            continue
        if not isinstance(entry, dict):
            continue
        cve = entry.get("ID") or entry.get("Id") or entry.get("id")
        if not isinstance(cve, str) or not cve.upper().startswith("CVE-"):
            continue
        info = entry.get("Info", {}) if isinstance(entry.get("Info"), dict) else {}
        classification = info.get("Classification", {}) if isinstance(info.get("Classification"), dict) else {}
        result.setdefault(
            cve.upper(),
            {
                "title": info.get("Name"),
                "description": info.get("Description"),
                "severity": info.get("Severity"),
                "cvss": _safe_float(classification.get("CVSSScore") or classification.get("cvssScore")),
            },
        )
    logger.info("Collected %d CVEs from Nuclei dataset", len(result))
    return result


def _normalize_severity(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    lowered = value.lower()
    for sev in SEVERITY_ORDER:
        if sev in lowered:
            return sev.capitalize()
    return value


def _fetch_local_stats(cursor, cves: Set[str]) -> List[Dict]:
    if not cves:
        return []

    stats: List[Dict] = []
    cve_list = [cve.upper() for cve in cves if cve]
    for batch in _chunk(cve_list):
        placeholders = ",".join(["%s"] * len(batch))
        query = f"""
            SELECT 
                cve_id,
                UPPER(cve_id) AS cve_upper,
                COUNT(DISTINCT device_id) AS device_count,
                MAX(last_seen_timestamp) AS last_seen,
                MAX(cvss_score) AS max_cvss,
                MAX(vulnerability_severity_level) AS sample_severity,
                MAX(
                    CASE 
                        WHEN LOWER(COALESCE(vulnerability_severity_level, '')) LIKE '%critical%' THEN 4
                        WHEN LOWER(COALESCE(vulnerability_severity_level, '')) LIKE '%high%' THEN 3
                        WHEN LOWER(COALESCE(vulnerability_severity_level, '')) LIKE '%medium%' THEN 2
                        WHEN LOWER(COALESCE(vulnerability_severity_level, '')) LIKE '%low%' THEN 1
                        ELSE 0
                    END
                ) AS severity_score
            FROM {TABLE_VULNERABILITIES}
            WHERE UPPER(cve_id) IN ({placeholders})
            GROUP BY cve_id
        """
        cursor.execute(query, batch)
        stats.extend(cursor.fetchall())
    return stats


def _truncate_table(cursor, table_name: str):
    cursor.execute(f"TRUNCATE TABLE {table_name}")


def _bulk_insert(cursor, table_name: str, rows: List[Dict], metadata: Dict[str, Dict]):
    if not rows:
        return
    payload = []
    for row in rows:
        meta_key = (row.get("cve_upper") or row.get("cve_id") or "").upper()
        meta = metadata.get(meta_key, {})
        payload.append(
            (
                row["cve_id"],
                row.get("device_count") or 0,
                SEVERITY_SCORE_MAP.get(row.get("severity_score"))
                or _normalize_severity(row.get("sample_severity")),
                row.get("max_cvss"),
                row.get("last_seen"),
                meta.get("title"),
                meta.get("description"),
                _normalize_severity(meta.get("severity")),
                meta.get("cvss"),
            )
        )
    cursor.executemany(
        f"""
        INSERT INTO {table_name} (
            cve_id, device_count, max_severity, max_cvss, last_seen,
            source_title, source_description, source_severity, source_cvss
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        payload,
    )


def _reset_detection_flag(cursor, column: str):
    cursor.execute(f"UPDATE {TABLE_VULNERABILITIES} SET {column} = FALSE")


def _apply_detection_flag(cursor, column: str, cves: Sequence[str]):
    if not cves:
        return
    for batch in _chunk(list(cves)):
        placeholders = ",".join(["%s"] * len(batch))
        cursor.execute(
            f"UPDATE {TABLE_VULNERABILITIES} SET {column} = TRUE WHERE cve_id IN ({placeholders})",
            batch,
        )


def _sync_source(
    cursor,
    cve_metadata: Dict[str, Dict[str, Optional[str]]],
    table_name: str,
    detection_column: Optional[str] = None,
) -> int:
    stats = _fetch_local_stats(cursor, set(cve_metadata.keys()))
    _truncate_table(cursor, table_name)
    if stats:
        _bulk_insert(cursor, table_name, stats, cve_metadata)
        matched_cves = [row["cve_id"] for row in stats if row.get("cve_id")]
    else:
        matched_cves = []

    if detection_column:
        _reset_detection_flag(cursor, detection_column)
        _apply_detection_flag(cursor, detection_column, matched_cves)

    return len(matched_cves)


def sync_threat_sources() -> Dict[str, int]:
    """Download external CVE feeds and refresh Rapid/Nuclei tables."""
    metasploit_metadata = _extract_metasploit_metadata()
    nuclei_metadata = _extract_nuclei_metadata()

    connection = get_db_connection()
    if not connection:
        raise Exception("Database connection failed")

    cursor = connection.cursor(dictionary=True)
    try:
        counts = {"rapid": 0, "nuclei": 0}

        if metasploit_metadata:
            counts["rapid"] = _sync_source(
                cursor,
                metasploit_metadata,
                TABLE_RAPID_VULNERABILITIES,
                detection_column="metasploit_detected",
            )
        else:
            _truncate_table(cursor, TABLE_RAPID_VULNERABILITIES)
            _reset_detection_flag(cursor, "metasploit_detected")

        if nuclei_metadata:
            counts["nuclei"] = _sync_source(
                cursor,
                nuclei_metadata,
                TABLE_NUCLEI_VULNERABILITIES,
                detection_column="nuclei_detected",
            )
        else:
            _truncate_table(cursor, TABLE_NUCLEI_VULNERABILITIES)
            _reset_detection_flag(cursor, "nuclei_detected")

        connection.commit()
        logger.info("Threat source sync complete (Rapid=%s, Nuclei=%s)", counts["rapid"], counts["nuclei"])
        return counts
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
