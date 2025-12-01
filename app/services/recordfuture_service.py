"""Service layer for RecordFuture indicator persistence."""
import logging
from typing import Dict, List

from database import get_db_connection
from app.repositories.recordfuture_repository import (
    bulk_upsert_indicators,
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
        return {
            "processed": len(payload),
            "saved": affected,
            "message": "Indicators persisted to RecordFuture",
        }
    finally:
        if connection and connection.is_connected():
            connection.close()
