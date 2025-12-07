"""Sync source runner for CISA Known Exploited Vulnerabilities feed."""
from __future__ import annotations

import gzip
import json
import logging
import os
import shutil
import tempfile
from typing import Set, Tuple

import requests

from database import get_db_connection
from app.services.sync_sources.base import SyncSourceResult, success_result

logger = logging.getLogger(__name__)

KEV_FEED_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def _download_kev_feed(dest_path: str) -> str:
    """Stream KEV JSON (supports gzip) to disk."""
    logger.info("Downloading KEV feed from %s", KEV_FEED_URL)
    with requests.get(KEV_FEED_URL, stream=True, timeout=600) as response:
        response.raise_for_status()
        with open(dest_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 512):
                if not chunk:
                    continue
                handle.write(chunk)
    logger.info("KEV feed stored at %s", dest_path)
    return dest_path


def _load_cve_ids(feed_path: str) -> Set[str]:
    """Load KEV JSON (plain or gz) and return normalized CVE IDs."""
    def _load_json(path: str) -> dict:
        try:
            with gzip.open(path, "rt", encoding="utf-8") as gz_file:
                return json.load(gz_file)
        except OSError:
            with open(path, "r", encoding="utf-8") as json_file:
                return json.load(json_file)

    payload = _load_json(feed_path)
    entries = payload.get("vulnerabilities", []) if isinstance(payload, dict) else []
    cve_ids: Set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        raw_id = entry.get("cveID") or entry.get("cve_id")
        if not raw_id:
            continue
        normalized = str(raw_id).strip().upper()
        if normalized:
            cve_ids.add(normalized)
    logger.info("Parsed %s CVEs from KEV feed", len(cve_ids))
    return cve_ids


def _apply_flags(cve_ids: Set[str]) -> Tuple[int, int]:
    """Sync cve_public_exploit flags using a temporary table."""
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            CREATE TEMPORARY TABLE IF NOT EXISTS kev_enrichment_tmp (
                cve_id VARCHAR(50) PRIMARY KEY
            ) ENGINE=InnoDB
            """
        )
        cursor.execute("TRUNCATE TABLE kev_enrichment_tmp")
        insert_sql = "INSERT INTO kev_enrichment_tmp (cve_id) VALUES (%s) ON DUPLICATE KEY UPDATE cve_id = VALUES(cve_id)"
        batch = []
        inserted = 0
        for cve_id in cve_ids:
            batch.append((cve_id,))
            if len(batch) >= 1000:
                cursor.executemany(insert_sql, batch)
                inserted += cursor.rowcount
                batch.clear()
        if batch:
            cursor.executemany(insert_sql, batch)
            inserted += cursor.rowcount
        logger.info("Inserted %s CVEs into KEV temp table", inserted)

        cursor.execute(
            """
            UPDATE vulnerabilities v
            LEFT JOIN kev_enrichment_tmp k ON v.cve_id = k.cve_id
            SET v.cve_public_exploit = FALSE
            WHERE k.cve_id IS NULL AND v.cve_public_exploit = TRUE
            """
        )
        cleared = cursor.rowcount

        cursor.execute(
            """
            UPDATE vulnerabilities v
            JOIN kev_enrichment_tmp k ON v.cve_id = k.cve_id
            SET v.cve_public_exploit = TRUE
            WHERE v.cve_public_exploit IS NULL OR v.cve_public_exploit = FALSE
            """
        )
        activated = cursor.rowcount

        connection.commit()
        logger.info("KEV flags updated. Cleared: %s, Activated: %s", cleared, activated)
        return cleared, activated
    finally:
        try:
            cursor.execute("DROP TEMPORARY TABLE IF EXISTS kev_enrichment_tmp")
        except Exception:
            logger.warning("Failed to drop KEV temp table", exc_info=True)
        cursor.close()
        connection.close()


def run() -> SyncSourceResult:
    """Runner entrypoint for KEV enrichment."""
    tmp_dir = tempfile.mkdtemp(prefix="kev_sync_")
    try:
        feed_path = os.path.join(tmp_dir, "known_exploited_vulnerabilities.json")
        _download_kev_feed(feed_path)
        cve_ids = _load_cve_ids(feed_path)
        cleared, activated = _apply_flags(cve_ids)
        message = f"KEV flags refreshed (activated={activated}, cleared={cleared}, source={len(cve_ids)})"
        return success_result(message, details={
            'source_cves': len(cve_ids),
            'activated': activated,
            'cleared': cleared,
        })
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
