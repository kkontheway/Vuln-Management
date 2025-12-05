"""Service layer for RecordFuture indicator persistence."""
import logging
from typing import Dict, List

from database import get_db_connection
from app.constants.database import TABLE_VULNERABILITIES
from app.repositories.recordfuture_repository import (
    bulk_upsert_indicators,
    fetch_indicator_values_by_type,
    initialize_recordfuture_table,
)

logger = logging.getLogger(__name__)


def _normalize_indicators(values: List[str]) -> List[str]:
    """Normalize indicator values by stripping whitespace."""
    normalized = []
    seen = set()
    for item in values or []:
        candidate = (item or "").strip()
        if not candidate:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return normalized


def _apply_recordfuture_detection_flags(connection, cves: List[str]) -> None:
    """Mark vulnerabilities that have RecordFuture intelligence."""
    normalized = [cve.upper() for cve in cves if cve]
    if not normalized:
        return

    cursor = connection.cursor()
    try:
        batch_size = 500
        for index in range(0, len(normalized), batch_size):
            batch = normalized[index:index + batch_size]
            placeholders = ','.join(['%s'] * len(batch))
            cursor.execute(
                f"""
                UPDATE {TABLE_VULNERABILITIES}
                SET recordfuture_detected = TRUE
                WHERE UPPER(cve_id) IN ({placeholders})
                """,
                batch,
            )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        logger.error("Failed to update RecordFuture detection flags: %s", exc)
        raise
    finally:
        cursor.close()


def _reset_recordfuture_detection_flags(connection) -> int:
    """Clear existing RecordFuture flags before rebuild."""
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"""
            UPDATE {TABLE_VULNERABILITIES}
            SET recordfuture_detected = FALSE
            WHERE recordfuture_detected = TRUE
            """
        )
        affected = cursor.rowcount or 0
        connection.commit()
        return affected
    except Exception as exc:
        connection.rollback()
        logger.error("Failed to reset RecordFuture detection flags: %s", exc)
        raise
    finally:
        cursor.close()


def save_indicators(ips: List[str], cves: List[str], source_text: str = "") -> Dict:
    """Persist indicators into the RecordFuture table."""
    normalized_ips = _normalize_indicators(ips)
    normalized_cves = _normalize_indicators(cves)

    if not normalized_ips and not normalized_cves:
        raise ValueError("No indicators provided for persistence")

    connection = get_db_connection()
    if not connection:
        raise Exception("Database connection failed")

    try:
        initialize_recordfuture_table(connection)
        payload = []
        metadata = {
            "source": "recordfuture_tool",
            "ip_count": len(normalized_ips),
            "cve_count": len(normalized_cves),
        }

        for ip in normalized_ips:
            payload.append(
                {
                    "indicator_type": "ip",
                    "indicator_value": ip,
                    "source_text": source_text,
                    "metadata": metadata,
                }
            )

        for cve in normalized_cves:
            payload.append(
                {
                    "indicator_type": "cve",
                    "indicator_value": cve,
                    "source_text": source_text,
                    "metadata": metadata,
                }
            )

        affected = bulk_upsert_indicators(connection, payload)
        if normalized_cves:
            _apply_recordfuture_detection_flags(connection, normalized_cves)
        return {
            "processed": len(payload),
            "saved": affected,
            "message": "Indicators persisted to RecordFuture",
        }
    finally:
        if connection and connection.is_connected():
            connection.close()


def rebuild_detection_flags() -> Dict[str, int]:
    """Recalculate RecordFuture flags from stored indicators."""
    connection = get_db_connection()
    if not connection:
        raise Exception("Database connection failed")

    try:
        initialize_recordfuture_table(connection)
        cve_indicators = fetch_indicator_values_by_type(connection, "cve")
        cleared = _reset_recordfuture_detection_flags(connection)

        if not cve_indicators:
            logger.info("RecordFuture rebuild skipped; no stored CVE indicators")
            return {
                "cleared": cleared,
                "reapplied": 0,
                "total_indicators": 0,
            }

        _apply_recordfuture_detection_flags(connection, cve_indicators)

        return {
            "cleared": cleared,
            "reapplied": len(cve_indicators),
            "total_indicators": len(cve_indicators),
        }
    finally:
        if connection and connection.is_connected():
            connection.close()
