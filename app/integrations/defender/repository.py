"""Repository layer for Microsoft Defender vulnerability data access."""
import json
import datetime
import logging
from typing import Optional, List, Dict, Any, Tuple
from mysql.connector import Error
from app.integrations.defender.transformers import transform_severity
from app.utils.datetime_parser import (
    parse_device_vulnerability_timestamps,
    parse_vulnerability_list_timestamps
)
from app.constants.database import (
    TABLE_VULNERABILITIES,
    TABLE_SYNC_STATE,
    TABLE_VULNERABILITY_SNAPSHOTS,
    TABLE_CVE_DEVICE_SNAPSHOTS,
    TABLE_VULNERABILITY_CATALOG,
    SYNC_TYPE_FULL
)
from app.integrations.defender.repository_helpers import (
    parse_severity_counts,
    parse_status_counts,
    build_device_map,
    record_initial_snapshot_devices,
    get_last_snapshot_devices,
    record_device_changes,
    calculate_snapshot_statistics
)

logger = logging.getLogger(__name__)


def _safe_float(value) -> Optional[float]:
    """Safely convert numeric-like input to float."""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> Optional[int]:
    """Safely convert numeric-like input to int."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def get_sync_state_count(connection, sync_type: str) -> int:
    """Get count of sync state records by sync type.
    
    Args:
        connection: Database connection
        sync_type: Sync type ('full' or 'delta')
        
    Returns:
        int: Count of sync state records
    """
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT COUNT(*) as count FROM {TABLE_SYNC_STATE} WHERE sync_type = %s"
        cursor.execute(query, (sync_type,))
        result = cursor.fetchone()
        cursor.close()
        return result['count'] if result else 0
    except Error as e:
        logger.error(f"Error getting sync state count: {e}")
        return 0


def get_last_sync_time_by_type(connection, sync_type: str) -> Optional[datetime.datetime]:
    """Get last sync time by sync type.
    
    Args:
        connection: Database connection
        sync_type: Sync type ('full' or 'delta')
        
    Returns:
        datetime.datetime: Last sync time, None if no record exists
    """
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT MAX(last_sync_time) as last_time FROM {TABLE_SYNC_STATE} WHERE sync_type = %s"
        cursor.execute(query, (sync_type,))
        result = cursor.fetchone()
        cursor.close()
        return result['last_time'] if result and result['last_time'] else None
    except Error as e:
        logger.error(f"Error getting last sync time by type: {e}")
        return None


def get_last_sync_time(connection, sync_type: str = SYNC_TYPE_FULL) -> Optional[datetime.datetime]:
    """Get last sync time.
    
    Args:
        connection: Database connection
        sync_type: Sync type ('full')
        
    Returns:
        datetime.datetime: Last sync time, or None if no record exists
    """
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT last_sync_time FROM {TABLE_SYNC_STATE} WHERE sync_type = %s ORDER BY id DESC LIMIT 1"
        cursor.execute(query, (sync_type,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if result and result['last_sync_time']:
            return result['last_sync_time']
        else:
            return None
            
    except Error as e:
        logger.error(f"Error getting last sync time: {e}")
        return None


def update_sync_time(connection, sync_time: datetime.datetime, sync_type: str = SYNC_TYPE_FULL, records_count: int = 0):
    """Update sync time and record count.
    
    Args:
        connection: Database connection
        sync_time: Sync time
        sync_type: Sync type ('full')
        records_count: Number of records synced
    """
    try:
        cursor = connection.cursor()
        query = f"INSERT INTO {TABLE_SYNC_STATE} (last_sync_time, sync_type, records_count) VALUES (%s, %s, %s)"
        cursor.execute(query, (sync_time, sync_type, records_count))
        connection.commit()
        logger.info(f"Sync time updated successfully: {sync_time}, type: {sync_type}, records: {records_count}")
    except Error as e:
        logger.error(f"Error updating sync time: {e}")
        connection.rollback()


def save_vulnerabilities(connection, vulnerabilities: List[Dict[str, Any]], is_delta: bool = True):
    """Save vulnerability data to database using table switching method for full sync.
    
    Uses double-table switching method:
    1. Create temporary table vulnerabilities_temp
    2. Batch insert all data into temp table
    3. Atomically switch tables using RENAME TABLE
    4. Drop old table
    
    Args:
        connection: Database connection
        vulnerabilities: List of vulnerability records
        is_delta: Whether this is a delta update (deprecated, always full sync now)
    """
    if not vulnerabilities:
        logger.warning("No vulnerabilities to save")
        return
    
    logger.info(f"Starting to save {len(vulnerabilities)} vulnerability records...")
    
    cursor = None
    temp_table_name = f"{TABLE_VULNERABILITIES}_temp"
    old_table_name = f"{TABLE_VULNERABILITIES}_old"
    
    try:
        cursor = connection.cursor()
        
        # Step 0: Ensure vulnerabilities table exists before creating temp table
        logger.info("Checking if vulnerabilities table exists...")
        try:
            cursor.execute(f"SELECT 1 FROM {TABLE_VULNERABILITIES} LIMIT 1")
            # Consume the result to avoid "Unread result found" error
            cursor.fetchone()
            logger.info(f"{TABLE_VULNERABILITIES} table exists")
        except Error:
            # Table doesn't exist, need to create it first
            logger.warning(f"{TABLE_VULNERABILITIES} table does not exist, creating it...")
            from app.integrations.defender.database import initialize_database
            initialize_database(connection)
            logger.info(f"{TABLE_VULNERABILITIES} table created successfully")
        
        # Step 1: Create temporary table with same structure as vulnerabilities
        logger.info("Creating temporary table for data insertion...")
        try:
            create_temp_table_query = f"""
            CREATE TABLE IF NOT EXISTS {temp_table_name} LIKE {TABLE_VULNERABILITIES}
            """
            cursor.execute(create_temp_table_query)
            logger.info(f"Temporary table {temp_table_name} created successfully")
        except Error as e:
            logger.error(f"Failed to create temporary table using LIKE: {e}")
            # Fallback: Create table with explicit structure
            logger.info("Attempting to create temporary table with explicit structure...")
            create_temp_table_query = f"""
            CREATE TABLE IF NOT EXISTS {temp_table_name} (
                id VARCHAR(255) PRIMARY KEY,
                cve_id VARCHAR(50),
                device_id VARCHAR(100),
                device_name VARCHAR(255),
                rbac_group_name VARCHAR(100),
                os_platform VARCHAR(50),
                os_version VARCHAR(50),
                os_architecture VARCHAR(20),
                software_vendor VARCHAR(100),
                software_name VARCHAR(100),
                software_version VARCHAR(100),
                vulnerability_severity_level VARCHAR(50),
                cvss_score FLOAT,
                status VARCHAR(20),
                exploitability_level VARCHAR(50),
                security_update_available BOOLEAN,
                recommended_security_update TEXT,
                recommended_security_update_id VARCHAR(100),
                recommended_security_update_url TEXT,
                recommendation_reference VARCHAR(255),
                autopatch_covered BOOLEAN DEFAULT FALSE,
                disk_paths JSON,
                registry_paths JSON,
                last_seen_timestamp DATETIME,
                first_seen_timestamp DATETIME,
                event_timestamp DATETIME,
                last_synced DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_cve_id (cve_id),
                INDEX idx_device_id (device_id),
                INDEX idx_cve_device (cve_id, device_id),
                INDEX idx_status (status),
                INDEX idx_severity (vulnerability_severity_level),
                INDEX idx_autopatch_covered (autopatch_covered),
                INDEX idx_last_seen (last_seen_timestamp),
                INDEX idx_first_seen (first_seen_timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
            cursor.execute(create_temp_table_query)
            logger.info(f"Temporary table {temp_table_name} created with explicit structure")
        
        # Step 2: Validate and prepare data for batch insert
        logger.info(f"Validating and preparing {len(vulnerabilities)} records for batch insert...")
        if len(vulnerabilities) == 0:
            logger.warning("No vulnerabilities to process after validation")
            return
        
        # Validate data structure
        valid_count = 0
        for vuln in vulnerabilities:
            if not isinstance(vuln, dict):
                logger.warning(f"Invalid vulnerability record (not a dict): {vuln}")
                continue
            if 'id' not in vuln:
                logger.warning(f"Vulnerability record missing 'id' field: {vuln}")
                continue
            valid_count += 1
        
        logger.info(f"Validated {valid_count} out of {len(vulnerabilities)} records")
        if valid_count == 0:
            logger.error("No valid vulnerability records to save")
            return
        
        batch_size = 2000  # Optimize batch size for performance
        insert_query = f"""
        INSERT INTO {temp_table_name} (
            id, cve_id, device_id, device_name, rbac_group_name,
            os_platform, os_version, os_architecture,
            software_vendor, software_name, software_version,
            vulnerability_severity_level, cvss_score, status,
            exploitability_level, security_update_available,
            recommended_security_update, recommended_security_update_id,
            recommended_security_update_url, recommendation_reference,
            autopatch_covered, disk_paths, registry_paths,
            last_seen_timestamp, first_seen_timestamp, event_timestamp,
            last_synced
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            NOW()
        )
        """
        
        # Prepare batch data
        batch_data = []
        for vuln in vulnerabilities:
            # Parse timestamps
            last_seen, first_seen, event_timestamp = parse_device_vulnerability_timestamps(vuln)
            
            # Convert disk paths and registry paths to JSON
            disk_paths_json = json.dumps(vuln.get('diskPaths', [])) if 'diskPaths' in vuln else '[]'
            registry_paths_json = json.dumps(vuln.get('registryPaths', [])) if 'registryPaths' in vuln else '[]'
            
            # Apply severity transformation
            transformed_severity = transform_severity(vuln.get('vulnerabilitySeverityLevel'))
            
            # Calculate autopatch_covered: check if recommendation_reference contains "microsoft" (case-insensitive)
            recommendation_ref = vuln.get('recommendationReference') or ''
            autopatch_covered = 'microsoft' in recommendation_ref.lower()

            batch_data.append((
                vuln['id'],
                vuln.get('cveId'),
                vuln.get('deviceId'),
                vuln.get('deviceName'),
                vuln.get('rbacGroupName'),
                vuln.get('osPlatform'),
                vuln.get('osVersion'),
                vuln.get('osArchitecture'),
                vuln.get('softwareVendor'),
                vuln.get('softwareName'),
                vuln.get('softwareVersion'),
                transformed_severity,
                vuln.get('cvssScore'),
                vuln.get('status'),
                vuln.get('exploitabilityLevel'),
                vuln.get('securityUpdateAvailable', False),
                vuln.get('recommendedSecurityUpdate'),
                vuln.get('recommendedSecurityUpdateId'),
                vuln.get('recommendedSecurityUpdateUrl'),
                vuln.get('recommendationReference'),
                autopatch_covered,
                disk_paths_json,
                registry_paths_json,
                last_seen,
                first_seen,
                event_timestamp
            ))
        
        # Step 3: Batch insert data
        logger.info(f"Inserting {len(batch_data)} records in batches of {batch_size}...")
        for i in range(0, len(batch_data), batch_size):
            batch = batch_data[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            logger.info(f"Inserted batch {i // batch_size + 1} ({len(batch)} records)")
        
        connection.commit()
        logger.info(f"Successfully inserted {len(batch_data)} records into temporary table")
        
        # Step 4: Atomically switch tables
        logger.info("Switching tables atomically...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Check if main table exists, if so rename it to old
        try:
            cursor.execute(f"SELECT 1 FROM {TABLE_VULNERABILITIES} LIMIT 1")
            # Consume the result to avoid "Unread result found" error
            cursor.fetchone()
            # Table exists, rename it
            cursor.execute(f"RENAME TABLE {TABLE_VULNERABILITIES} TO {old_table_name}")
            logger.info(f"Renamed {TABLE_VULNERABILITIES} to {old_table_name}")
        except Error:
            # Table doesn't exist, that's fine for first sync
            logger.info(f"{TABLE_VULNERABILITIES} table doesn't exist, skipping rename")
        
        # Rename temp table to main table
        cursor.execute(f"RENAME TABLE {temp_table_name} TO {TABLE_VULNERABILITIES}")
        logger.info(f"Renamed {temp_table_name} to {TABLE_VULNERABILITIES}")
        
        # Drop old table if it exists
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {old_table_name}")
            logger.info(f"Dropped old table {old_table_name}")
        except Error as e:
            logger.warning(f"Error dropping old table: {e}")
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        connection.commit()
        
        # Step 5: Verify data was saved correctly
        logger.info("Verifying data was saved correctly...")
        verify_cursor = connection.cursor(dictionary=True)
        verify_cursor.execute(f"SELECT COUNT(*) as count FROM {TABLE_VULNERABILITIES}")
        saved_count = verify_cursor.fetchone()['count']
        verify_cursor.close()
        logger.info(f"Verification: {saved_count} records found in {TABLE_VULNERABILITIES} table")
        
        if saved_count == 0:
            logger.error(f"CRITICAL: No records found in {TABLE_VULNERABILITIES} after save operation!")
            raise Exception(f"Data save verification failed: expected records but found 0")
        
        if saved_count != len(batch_data):
            logger.warning(f"Record count mismatch: expected {len(batch_data)}, found {saved_count}")
        else:
            logger.info(f"Data verification successful: {saved_count} records match expected count")
        
        logger.info(f"Successfully saved {len(vulnerabilities)} vulnerability records using table switching method")
        
    except Error as e:
        logger.error(f"Error saving vulnerability data: {e}", exc_info=True)
        connection.rollback()
        
        # Clean up temp table on error
        try:
            if cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
                logger.info(f"Cleaned up temporary table {temp_table_name}")
        except Error as cleanup_error:
            logger.warning(f"Error cleaning up temp table: {cleanup_error}")
        
        raise
    except Exception as e:
        logger.error(f"Unknown error saving vulnerability data: {e}", exc_info=True)
        connection.rollback()
        
        # Clean up temp table on error
        try:
            if cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
                logger.info(f"Cleaned up temporary table {temp_table_name}")
        except Error as cleanup_error:
            logger.warning(f"Error cleaning up temp table: {cleanup_error}")
        
        raise
    finally:
        if cursor:
            cursor.close()


def save_vulnerability_catalog(connection, catalog_records: List[Dict[str, Any]]) -> int:
    """Save CVE catalog records into dedicated catalog table."""
    if not catalog_records:
        logger.info("No catalog records to save")
        return 0
    cursor = connection.cursor()
    insert_query = f"""
    INSERT INTO {TABLE_VULNERABILITY_CATALOG} (
        cve_id, name, description, severity, cvss_v3, cvss_vector,
        exposed_machines, published_on, updated_on, first_detected,
        public_exploit, exploit_verified, exploit_in_kit,
        exploit_types, exploit_uris, supportability, tags, epss
    ) VALUES (
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s, %s
    )
    ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        description = VALUES(description),
        severity = VALUES(severity),
        cvss_v3 = VALUES(cvss_v3),
        cvss_vector = VALUES(cvss_vector),
        exposed_machines = VALUES(exposed_machines),
        published_on = VALUES(published_on),
        updated_on = VALUES(updated_on),
        first_detected = VALUES(first_detected),
        public_exploit = VALUES(public_exploit),
        exploit_verified = VALUES(exploit_verified),
        exploit_in_kit = VALUES(exploit_in_kit),
        exploit_types = VALUES(exploit_types),
        exploit_uris = VALUES(exploit_uris),
        supportability = VALUES(supportability),
        tags = VALUES(tags),
        epss = VALUES(epss)
    """
    batch = []
    for record in catalog_records:
        cve_identifier = record.get('cveId') or record.get('id') or record.get('name')
        if not cve_identifier:
            continue
        published_on, updated_on, first_detected = parse_vulnerability_list_timestamps(record)
        batch.append((
            str(cve_identifier),
            record.get('name') or record.get('id'),
            record.get('description'),
            record.get('severity'),
            _safe_float(record.get('cvssV3')),
            record.get('cvssVector'),
            _safe_int(record.get('exposedMachines')),
            published_on,
            updated_on,
            first_detected,
            bool(record.get('publicExploit')) if record.get('publicExploit') is not None else None,
            bool(record.get('exploitVerified')) if record.get('exploitVerified') is not None else None,
            bool(record.get('exploitInKit')) if record.get('exploitInKit') is not None else None,
            json.dumps(record.get('exploitTypes') or []),
            json.dumps(record.get('exploitUris') or []),
            record.get('cveSupportability'),
            json.dumps(record.get('tags') or []),
            _safe_float(record.get('epss'))
        ))
    if not batch:
        logger.warning("No valid catalog records after validation")
        cursor.close()
        return 0
    cursor.executemany(insert_query, batch)
    connection.commit()
    cursor.close()
    logger.info("Saved/updated %s catalog records", len(batch))
    return len(batch)


def get_last_snapshot(connection) -> Optional[int]:
    """Get last snapshot ID.
    
    Args:
        connection: Database connection
        
    Returns:
        int: Last snapshot ID, None if no snapshot exists
    """
    try:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT id FROM {TABLE_VULNERABILITY_SNAPSHOTS} ORDER BY snapshot_time DESC LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        return result['id'] if result else None
    except Error as e:
        logger.error(f"Error getting last snapshot: {e}")
        return None


def record_snapshot(connection, snapshot_time: Optional[datetime.datetime] = None, is_initial: bool = False) -> Optional[int]:
    """Record data snapshot based on vulnerabilities table.
    
    Creates snapshot statistics and records each CVE-Device combination for fixed status tracking.
    
    Args:
        connection: Database connection
        snapshot_time: Snapshot time, defaults to current time
        is_initial: Whether this is an initial snapshot
        
    Returns:
        int: Snapshot ID if successful, None otherwise
    """
    try:
        if snapshot_time is None:
            snapshot_time = datetime.datetime.now()
        
        cursor = connection.cursor(dictionary=True)
        
        # 1. Calculate overall statistics from vulnerabilities table
        stats = calculate_snapshot_statistics(cursor, TABLE_VULNERABILITIES)
        total_vulnerabilities = stats['total_vulnerabilities']
        unique_cve_count = stats['unique_cve_count']
        severity_counts = stats['severity_counts']
        status_counts = stats['status_counts']
        total_devices_affected = stats['total_devices_affected']
        
        critical_count = severity_counts['critical']
        high_count = severity_counts['high']
        medium_count = severity_counts['medium']
        low_count = severity_counts['low']
        fixed_count = status_counts['fixed']
        active_count = status_counts['active']
        
        # 2. Insert overall snapshot
        snapshot_query = f"""
        INSERT INTO {TABLE_VULNERABILITY_SNAPSHOTS} (
            snapshot_time, total_vulnerabilities, unique_cve_count,
            critical_count, high_count, medium_count, low_count,
            fixed_count, active_count, total_devices_affected
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(snapshot_query, (
            snapshot_time, total_vulnerabilities, unique_cve_count,
            critical_count, high_count, medium_count, low_count,
            fixed_count, active_count, total_devices_affected
        ))
        snapshot_id = cursor.lastrowid
        
        # 3. Record each CVE-Device combination for fixed status tracking
        # Use GROUP BY to deduplicate: same CVE-Device may have multiple records (different software versions)
        # For each CVE-Device combination, we keep the record with the latest last_seen_timestamp
        logger.info("Recording CVE-Device combinations for snapshot (deduplicating by CVE-Device)...")
        cve_device_query = f"""
        SELECT 
            cve_id,
            device_id,
            MAX(device_name) as device_name,
            COALESCE(MAX(CASE WHEN status IS NOT NULL AND status != '' THEN status END), 'Active') as status,
            MAX(vulnerability_severity_level) as severity,
            MAX(cvss_score) as cvss_score,
            MIN(first_seen_timestamp) as first_seen,
            MAX(last_seen_timestamp) as last_seen
        FROM {TABLE_VULNERABILITIES}
        WHERE cve_id IS NOT NULL AND cve_id != ''
          AND device_id IS NOT NULL AND device_id != ''
        GROUP BY cve_id, device_id
        """
        cursor.execute(cve_device_query)
        cve_device_records = cursor.fetchall()
        
        logger.info(f"Found {len(cve_device_records)} unique CVE-Device combinations after deduplication")
        
        # Batch insert CVE-Device snapshots using INSERT IGNORE to handle any remaining duplicates
        cve_device_snapshot_query = f"""
        INSERT IGNORE INTO {TABLE_CVE_DEVICE_SNAPSHOTS} (
            snapshot_id, cve_id, device_id, device_name, status,
            severity, cvss_score, first_seen, last_seen
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        batch_size = 2000
        batch_data = []
        for record in cve_device_records:
            # Ensure status is not None (use 'Active' as default if NULL)
            status_value = record['status'] if record['status'] is not None and record['status'] != '' else 'Active'
            batch_data.append((
                snapshot_id,
                record['cve_id'],
                record['device_id'],
                record['device_name'],
                status_value,
                record['severity'],
                record['cvss_score'],
                record['first_seen'],
                record['last_seen']
            ))
        
        # Insert in batches
        for i in range(0, len(batch_data), batch_size):
            batch = batch_data[i:i + batch_size]
            cursor.executemany(cve_device_snapshot_query, batch)
            logger.info(f"Inserted CVE-Device snapshot batch {i // batch_size + 1} ({len(batch)} records)")
        
        connection.commit()
        cursor.close()
        logger.info(f"Snapshot recorded successfully, snapshot ID: {snapshot_id}, CVE-Device records: {len(batch_data)}")
        
        return snapshot_id
        
    except Error as e:
        logger.error(f"Database error recording snapshot: {e}", exc_info=True)
        if connection:
            connection.rollback()
        return None
    except Exception as e:
        logger.error(f"Unknown error recording snapshot: {e}", exc_info=True)
        if connection:
            connection.rollback()
        return None


def create_initial_snapshot(connection) -> Optional[int]:
    """Create initial snapshot for existing data.
    
    Args:
        connection: Database connection
        
    Returns:
        int: Snapshot ID if successful, None otherwise
    """
    try:
        logger.info("Starting to create initial snapshot...")
        
        # Ensure database tables are initialized
        from app.integrations.defender.database import initialize_database
        initialize_database(connection)
        
        snapshot_id = record_snapshot(connection, is_initial=True)
        if snapshot_id:
            logger.info(f"Initial snapshot created successfully, snapshot ID: {snapshot_id}")
        else:
            logger.error("Initial snapshot creation failed: record_snapshot returned None")
        return snapshot_id
    except Exception as e:
        logger.error(f"Exception occurred while creating initial snapshot: {e}", exc_info=True)
        if connection:
            connection.rollback()
        return None
