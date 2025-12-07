"""Sync source runner for DuckDB-based EPSS enrichment."""
from __future__ import annotations

import csv
import logging
import os
import shutil
import tempfile
from typing import Tuple

import duckdb
import requests

from database import get_db_connection
from app.services.sync_sources.base import SyncSourceResult, success_result

logger = logging.getLogger(__name__)

EPSS_SOURCE_URL = "https://epss.empiricalsecurity.com/epss_scores-current.csv.gz"


def _download_epss_snapshot(dest_path: str) -> Tuple[int, str]:
    """Stream EPSS gz file to disk to avoid large memory usage."""
    logger.info("Downloading EPSS snapshot from %s", EPSS_SOURCE_URL)
    with requests.get(EPSS_SOURCE_URL, stream=True, timeout=600) as response:
        response.raise_for_status()
        with open(dest_path, "wb") as handle:
            total_bytes = 0
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                handle.write(chunk)
                total_bytes += len(chunk)
    logger.info("EPSS snapshot downloaded: %.2f MB", total_bytes / (1024 * 1024))
    return total_bytes, dest_path


def _transform_with_duckdb(source_path: str, output_path: str) -> int:
    """Use DuckDB to filter/clean EPSS CSV and export to a sanitized CSV file."""
    logger.info("Transforming EPSS data with DuckDB")
    con = duckdb.connect(database=":memory:")
    try:
        con.execute(
            f"""
            CREATE OR REPLACE TABLE epss_clean AS
            SELECT
                upper(trim(cve)) AS cve_id,
                TRY_CAST(epss AS DOUBLE) AS epss
            FROM read_csv_auto('{source_path}', header=True)
            WHERE cve IS NOT NULL
              AND epss IS NOT NULL
              AND TRY_CAST(epss AS DOUBLE) BETWEEN 0 AND 1
            """
        )
        total_rows = con.execute("SELECT COUNT(*) FROM epss_clean").fetchone()[0]
        logger.info("DuckDB cleaned rows: %s", total_rows)
        con.execute(
            f"""
            COPY (
                SELECT cve_id, epss
                FROM epss_clean
                WHERE cve_id IS NOT NULL AND epss IS NOT NULL
            ) TO '{output_path}' WITH (HEADER, DELIMITER ',')
            """
        )
        return total_rows
    finally:
        con.close()


def _load_into_mysql(clean_csv_path: str) -> Tuple[int, int]:
    """Load cleaned EPSS values into temp table then update vulnerabilities."""
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    cursor = connection.cursor()
    inserted = 0
    updated = 0
    try:
        cursor.execute(
            """
            CREATE TEMPORARY TABLE IF NOT EXISTS epss_enrichment_tmp (
                cve_id VARCHAR(50) PRIMARY KEY,
                epss FLOAT
            ) ENGINE=InnoDB
            """
        )
        insert_sql = """
            INSERT INTO epss_enrichment_tmp (cve_id, epss)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE epss = VALUES(epss)
        """
        batch = []
        batch_size = 2000
        with open(clean_csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                cve_id = row.get('cve_id')
                epss_val = row.get('epss')
                if not cve_id or epss_val in (None, ''):
                    continue
                try:
                    epss_float = float(epss_val)
                except ValueError:
                    continue
                batch.append((cve_id, epss_float))
                if len(batch) >= batch_size:
                    cursor.executemany(insert_sql, batch)
                    inserted += cursor.rowcount
                    batch.clear()
            if batch:
                cursor.executemany(insert_sql, batch)
                inserted += cursor.rowcount
        logger.info("Inserted %s rows into temporary EPSS table", inserted)
        cursor.execute(
            """
            UPDATE vulnerabilities v
            JOIN epss_enrichment_tmp e ON v.cve_id = e.cve_id
            SET v.cve_epss = e.epss
            """
        )
        updated = cursor.rowcount
        logger.info("Updated EPSS values for %s vulnerabilities", updated)
        connection.commit()
        return inserted, updated
    finally:
        try:
            cursor.execute("DROP TEMPORARY TABLE IF EXISTS epss_enrichment_tmp")
        except Exception:
            logger.warning("Failed to drop temporary EPSS table", exc_info=True)
        cursor.close()
        connection.close()


def run() -> SyncSourceResult:
    """Runner entrypoint for EPSS enrichment."""
    tmp_dir = tempfile.mkdtemp(prefix="epss_sync_")
    download_path = os.path.join(tmp_dir, "epss_scores-current.csv.gz")
    clean_csv_path = os.path.join(tmp_dir, "epss_clean.csv")
    try:
        _download_epss_snapshot(download_path)
        total_rows = _transform_with_duckdb(download_path, clean_csv_path)
        inserted, updated = _load_into_mysql(clean_csv_path)
        message = f"EPSS enriched for {updated} vulnerabilities (source rows: {total_rows})"
        return success_result(message, details={
            'source_rows': total_rows,
            'temp_inserted': inserted,
            'updated': updated
        })
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
