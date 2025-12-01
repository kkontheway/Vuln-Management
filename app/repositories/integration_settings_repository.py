"""Repository helpers for integration integration settings and secrets."""
import json
import logging
from typing import Any, Dict, Optional

from app.constants.database import (
    TABLE_INTEGRATION_SECRET_VERSIONS,
    TABLE_INTEGRATION_SETTINGS,
)

logger = logging.getLogger(__name__)


def initialize_integration_settings_tables(connection) -> None:
    """Create tables required for integration settings if they do not exist."""
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_INTEGRATION_SETTINGS} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                provider VARCHAR(64) NOT NULL UNIQUE,
                metadata JSON NULL,
                active_secret_version INT DEFAULT NULL,
                last_test_status VARCHAR(20),
                last_tested_at DATETIME,
                last_test_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """
        )
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_INTEGRATION_SECRET_VERSIONS} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                setting_id INT NOT NULL,
                version INT NOT NULL,
                ciphertext LONGBLOB NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_setting_version (setting_id, version),
                INDEX idx_setting_id (setting_id),
                CONSTRAINT fk_integration_setting
                    FOREIGN KEY (setting_id)
                    REFERENCES {TABLE_INTEGRATION_SETTINGS}(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB
            """
        )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        logger.error("Failed to initialize integration settings tables: %s", exc)
        raise
    finally:
        cursor.close()


def _parse_metadata(raw_value: Any) -> Dict[str, Any]:
    if not raw_value:
        return {}
    if isinstance(raw_value, dict):
        return raw_value
    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        logger.warning("Failed to parse integration metadata, returning empty dict")
        return {}


def get_setting_by_provider(connection, provider: str) -> Optional[Dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT id, provider, metadata, active_secret_version, last_test_status,
                   last_tested_at, last_test_message, created_at, updated_at
            FROM {TABLE_INTEGRATION_SETTINGS}
            WHERE provider = %s
            """,
            (provider,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        row["metadata"] = _parse_metadata(row.get("metadata"))
        return row
    finally:
        cursor.close()


def upsert_setting(connection, provider: str, metadata: Dict[str, Any]) -> int:
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"""
            INSERT INTO {TABLE_INTEGRATION_SETTINGS} (provider, metadata)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE metadata = VALUES(metadata), updated_at = CURRENT_TIMESTAMP
            """,
            (provider, json.dumps(metadata or {})),
        )
        if cursor.lastrowid:
            return cursor.lastrowid
        cursor.execute(
            f"SELECT id FROM {TABLE_INTEGRATION_SETTINGS} WHERE provider = %s",
            (provider,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("Integration setting row missing after upsert")
        return row[0]
    finally:
        cursor.close()


def create_secret_version(connection, setting_id: int, ciphertext: bytes) -> int:
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"SELECT COALESCE(MAX(version), 0) FROM {TABLE_INTEGRATION_SECRET_VERSIONS} WHERE setting_id = %s",
            (setting_id,),
        )
        current_max = cursor.fetchone()[0] or 0
        next_version = int(current_max) + 1
        cursor.execute(
            f"""
            INSERT INTO {TABLE_INTEGRATION_SECRET_VERSIONS} (setting_id, version, ciphertext)
            VALUES (%s, %s, %s)
            """,
            (setting_id, next_version, ciphertext),
        )
        return next_version
    finally:
        cursor.close()


def update_active_secret_version(connection, setting_id: int, version: int) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"""
            UPDATE {TABLE_INTEGRATION_SETTINGS}
            SET active_secret_version = %s
            WHERE id = %s
            """,
            (version, setting_id),
        )
    finally:
        cursor.close()


def get_secret_version(connection, setting_id: int, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    try:
        params = (setting_id,)
        if version is None:
            cursor.execute(
                f"""
                SELECT id, setting_id, version, ciphertext, created_at
                FROM {TABLE_INTEGRATION_SECRET_VERSIONS}
                WHERE setting_id = %s
                ORDER BY version DESC
                LIMIT 1
                """,
                params,
            )
        else:
            cursor.execute(
                f"""
                SELECT id, setting_id, version, ciphertext, created_at
                FROM {TABLE_INTEGRATION_SECRET_VERSIONS}
                WHERE setting_id = %s AND version = %s
                """,
                (setting_id, version),
            )
        return cursor.fetchone()
    finally:
        cursor.close()


def update_test_result(connection, setting_id: int, status: str, message: str) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"""
            UPDATE {TABLE_INTEGRATION_SETTINGS}
            SET last_test_status = %s,
                last_test_message = %s,
                last_tested_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (status, message, setting_id),
        )
    finally:
        cursor.close()
