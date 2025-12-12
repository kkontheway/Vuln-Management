"""Device tagging utility functions."""
from __future__ import annotations

import logging
from typing import Dict, List

from mysql.connector import Error

from app.constants.database import (
    TABLE_DEVICE_TAG_RULES,
    TABLE_DEVICE_TAGS,
    TABLE_VULNERABILITIES,
)

logger = logging.getLogger(__name__)

DEFAULT_DEVICE_TAG_RULES: List[Dict] = [
    {
        "tag": "panjin",
        "pattern": "%.victrex-panjin.com",
        "priority": 10,
        "enabled": True,
        "notes": "Panjin endpoint naming convention",
    },
    {
        "tag": "victrex",
        "pattern": "%.victrex.com",
        "priority": 20,
        "enabled": True,
        "notes": "Victrex PLC corporate devices",
    },
    {
        "tag": "txv",
        "pattern": "%txv%",
        "priority": 30,
        "enabled": False,
        "notes": "Reserved placeholder for TXV pattern",
    },
]


def seed_default_rules(connection) -> None:
    """Insert built-in rules when table is empty."""
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT COUNT(*) AS count FROM {TABLE_DEVICE_TAG_RULES}")
        count = cursor.fetchone()["count"]
        if count:
            return
        logger.info("Seeding default device tag rules...")
        insert_query = f"""
            INSERT INTO {TABLE_DEVICE_TAG_RULES} (tag, pattern, priority, enabled, notes)
            VALUES (%s, %s, %s, %s, %s)
        """
        for rule in DEFAULT_DEVICE_TAG_RULES:
            cursor.execute(
                insert_query,
                (
                    rule["tag"],
                    rule["pattern"],
                    rule.get("priority", 100),
                    1 if rule.get("enabled", True) else 0,
                    rule.get("notes"),
                ),
            )
        connection.commit()
    finally:
        cursor.close()


def apply_device_tag_rules(connection) -> int:
    """Apply device tag rules to the vulnerabilities table."""
    seed_default_rules(connection)
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT id, tag, pattern, priority
            FROM {TABLE_DEVICE_TAG_RULES}
            WHERE enabled = TRUE
            ORDER BY priority ASC, id ASC
            """
        )
        rules = cursor.fetchall()
        if not rules:
            logger.info("No device tag rules enabled; skipping tagging step")
            return 0

        logger.info("Clearing previous device_tag assignments...")
        cursor.execute(
            f"UPDATE {TABLE_VULNERABILITIES} SET device_tag = NULL WHERE device_tag IS NOT NULL"
        )

        applied = 0
        for rule in rules:
            cursor.execute(
                f"""
                UPDATE {TABLE_VULNERABILITIES}
                SET device_tag = %s
                WHERE device_tag IS NULL
                  AND device_name IS NOT NULL
                  AND device_name LIKE %s
                """,
                (rule["tag"], rule["pattern"]),
            )
            affected = cursor.rowcount or 0
            applied += affected
            if affected:
                logger.info(
                    "Rule #%s (%s) matched %s records",
                    rule["id"],
                    rule["tag"],
                    affected,
                )

        logger.info("Rebuilding device_tags materialized table...")
        cursor.execute(f"DELETE FROM {TABLE_DEVICE_TAGS}")
        cursor.execute(
            f"""
            INSERT INTO {TABLE_DEVICE_TAGS} (device_id, device_name, tag, source)
            SELECT DISTINCT device_id, device_name, device_tag, 'rule'
            FROM {TABLE_VULNERABILITIES}
            WHERE device_tag IS NOT NULL AND device_tag != ''
        """
        )

        connection.commit()
        logger.info("Device tagging completed; %s rows updated.", applied)
        return applied
    except Error as exc:
        connection.rollback()
        logger.error("Failed to apply device tag rules: %s", exc)
        raise
    finally:
        cursor.close()


def get_device_tag_distribution(connection) -> List[Dict]:
    """Return per-tag device counts."""
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT device_tag AS tag, COUNT(DISTINCT device_id) AS device_count
            FROM {TABLE_VULNERABILITIES}
            WHERE device_tag IS NOT NULL AND device_tag != ''
            GROUP BY device_tag
            ORDER BY device_count DESC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()


def get_distinct_device_tags(connection) -> List[str]:
    """Return sorted list of existing device tags."""
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            f"""
            SELECT DISTINCT device_tag AS tag
            FROM {TABLE_VULNERABILITIES}
            WHERE device_tag IS NOT NULL AND device_tag != ''
            ORDER BY device_tag
            """
        )
        return [row["tag"] for row in cursor.fetchall()]
    finally:
        cursor.close()
