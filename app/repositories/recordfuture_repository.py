"""Repository helpers for RecordFuture indicator storage."""
import json
import logging
from typing import Dict, List

from app.constants.database import TABLE_RECORDFUTURE_INDICATORS

logger = logging.getLogger(__name__)


def initialize_recordfuture_table(connection) -> None:
    """Ensure the RecordFuture table exists before writes."""
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_RECORDFUTURE_INDICATORS} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                indicator_type ENUM('ip', 'cve') NOT NULL,
                indicator_value VARCHAR(255) NOT NULL,
                source_text TEXT,
                metadata JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_indicator (indicator_type, indicator_value)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        logger.error("Failed to initialize RecordFuture table: %s", exc)
        raise
    finally:
        cursor.close()


def bulk_upsert_indicators(connection, indicators: List[Dict]) -> int:
    """Insert or update a list of indicators."""
    if not indicators:
        return 0

    cursor = connection.cursor()
    try:
        payload = [
            (
                indicator["indicator_type"],
                indicator["indicator_value"],
                indicator.get("source_text"),
                json.dumps(indicator.get("metadata") or {}),
            )
            for indicator in indicators
        ]

        cursor.executemany(
            f"""
            INSERT INTO {TABLE_RECORDFUTURE_INDICATORS}
                (indicator_type, indicator_value, source_text, metadata)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                source_text = VALUES(source_text),
                metadata = VALUES(metadata),
                updated_at = CURRENT_TIMESTAMP
            """,
            payload,
        )
        connection.commit()
        return cursor.rowcount
    except Exception as exc:
        connection.rollback()
        logger.error("Failed to upsert RecordFuture indicators: %s", exc)
        raise
    finally:
        cursor.close()
