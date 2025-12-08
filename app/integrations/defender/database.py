"""Database operations for Microsoft Defender integration."""
import logging
import mysql.connector
from mysql.connector import Error
from app.integrations.defender.config import DB_CONFIG
from app.constants.database import (
    TABLE_VULNERABILITIES,
    TABLE_SYNC_STATE,
    TABLE_VULNERABILITY_SNAPSHOTS,
    TABLE_CVE_DEVICE_SNAPSHOTS,
    TABLE_VULNERABILITY_TREND_PERIODS,
    TABLE_RECOMMENDATION_REPORTS,
    TABLE_RAPID_VULNERABILITIES,
    TABLE_NUCLEI_VULNERABILITIES,
)

logger = logging.getLogger(__name__)


def _ensure_table_columns(cursor, table_name, columns):
    for column_name, ddl in columns:
        try:
            cursor.execute(f"SELECT {column_name} FROM {table_name} LIMIT 1")
            cursor.fetchone()
        except Error:
            logger.info("Adding %s column to %s table...", column_name, table_name)
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")
            except Error as exc:
                error_msg = str(exc).lower()
                if 'duplicate' in error_msg or 'exists' in error_msg:
                    logger.info("%s column already exists in %s", column_name, table_name)
                else:
                    logger.warning("Error adding %s column to %s: %s", column_name, table_name, exc)


def create_db_connection():
    """Create database connection.
    
    Returns:
        mysql.connector.connection.MySQLConnection: Database connection if successful, None otherwise
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            logger.info("Successfully connected to MySQL database")
            return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return None


def migrate_database(connection):
    """Migrate database schema from old structure to new structure.
    
    This function handles migration from old table structure to new single-table structure.
    - Migrates sync_state table: removes data_source column, adds records_count column
    - Other tables will be created fresh if they don't exist
    
    Args:
        connection: Database connection
    """
    try:
        cursor = connection.cursor()
        
        # Migrate sync_state table structure
        try:
            # Check if sync_state table exists
            cursor.execute(f"SELECT 1 FROM {TABLE_SYNC_STATE} LIMIT 1")
            logger.info(f"{TABLE_SYNC_STATE} table exists, checking structure...")
            
            # Check if records_count column exists
            try:
                cursor.execute(f"SELECT records_count FROM {TABLE_SYNC_STATE} LIMIT 1")
                # Consume the result to avoid "Unread result found" error
                cursor.fetchone()
                logger.info(f"{TABLE_SYNC_STATE} table already has records_count column")
            except Error:
                # Column doesn't exist, need to add it
                logger.info(f"Adding records_count column to {TABLE_SYNC_STATE} table...")
                try:
                    cursor.execute(f"ALTER TABLE {TABLE_SYNC_STATE} ADD COLUMN records_count INT DEFAULT 0 AFTER sync_type")
                    connection.commit()
                    logger.info("Successfully added records_count column")
                except Error as e:
                    error_msg = str(e).lower()
                    if 'duplicate column' in error_msg or 'already exists' in error_msg:
                        logger.info("records_count column already exists, skipping")
                    else:
                        logger.warning(f"Error adding records_count column: {e}")
                        connection.rollback()
            
            # Check if data_source column exists and remove it if present
            try:
                cursor.execute(f"SELECT data_source FROM {TABLE_SYNC_STATE} LIMIT 1")
                # Consume the result to avoid "Unread result found" error
                cursor.fetchone()
                # Column exists, need to remove it
                logger.info(f"Removing data_source column from {TABLE_SYNC_STATE} table...")
                try:
                    cursor.execute(f"ALTER TABLE {TABLE_SYNC_STATE} DROP COLUMN data_source")
                    connection.commit()
                    logger.info("Successfully removed data_source column")
                except Error as e:
                    error_msg = str(e).lower()
                    if 'doesn\'t exist' in error_msg or 'unknown column' in error_msg:
                        logger.info("data_source column doesn't exist, skipping")
                    else:
                        logger.warning(f"Error removing data_source column: {e}")
                        connection.rollback()
            except Error:
                # Column doesn't exist, that's fine
                logger.info("data_source column doesn't exist, no need to remove")
                
        except Error:
            # Table doesn't exist, will be created by initialize_database
            logger.info(f"{TABLE_SYNC_STATE} table doesn't exist, will be created")
        
        # Migrate vulnerabilities table - add autopatch_covered field
        try:
            # Check if vulnerabilities table exists
            cursor.execute(f"SELECT 1 FROM {TABLE_VULNERABILITIES} LIMIT 1")
            # Consume the result to avoid "Unread result found" error
            cursor.fetchone()
            logger.info(f"{TABLE_VULNERABILITIES} table exists, checking for autopatch_covered column...")
            
            # Check if autopatch_covered column exists
            try:
                cursor.execute(f"SELECT autopatch_covered FROM {TABLE_VULNERABILITIES} LIMIT 1")
                # Consume the result to avoid "Unread result found" error
                cursor.fetchone()
                logger.info(f"{TABLE_VULNERABILITIES} table already has autopatch_covered column")
            except Error:
                # Column doesn't exist, need to add it
                logger.info(f"Adding autopatch_covered column to {TABLE_VULNERABILITIES} table...")
                try:
                    cursor.execute(f"ALTER TABLE {TABLE_VULNERABILITIES} ADD COLUMN autopatch_covered BOOLEAN DEFAULT FALSE AFTER recommendation_reference")
                    # Add index for better query performance
                    cursor.execute(f"CREATE INDEX idx_autopatch_covered ON {TABLE_VULNERABILITIES}(autopatch_covered)")
                    connection.commit()
                    logger.info("Successfully added autopatch_covered column and index")
                except Error as e:
                    error_msg = str(e).lower()
                    if 'duplicate column' in error_msg or 'already exists' in error_msg or 'duplicate key' in error_msg:
                        logger.info("autopatch_covered column or index already exists, skipping")
                    else:
                        logger.warning(f"Error adding autopatch_covered column: {e}")
                        connection.rollback()

            # Ensure cve_description column exists for caching NVD text
            try:
                cursor.execute(f"SELECT cve_description FROM {TABLE_VULNERABILITIES} LIMIT 1")
                cursor.fetchone()
                logger.info("%s table already has cve_description column", TABLE_VULNERABILITIES)
            except Error:
                logger.info("Adding cve_description column to %s table...", TABLE_VULNERABILITIES)
                try:
                    cursor.execute(
                        f"ALTER TABLE {TABLE_VULNERABILITIES} "
                        f"ADD COLUMN cve_description TEXT AFTER recommendation_reference"
                    )
                    connection.commit()
                    logger.info("Successfully added cve_description column")
                except Error as e:
                    error_msg = str(e).lower()
                    if 'duplicate column' in error_msg or 'already exists' in error_msg:
                        logger.info("cve_description column already exists, skipping")
                    else:
                        logger.warning("Error adding cve_description column: %s", e)
                        connection.rollback()

            # Ensure threat source indicator columns exist
            threat_source_columns = [
                ("metasploit_detected", "idx_metasploit_detected"),
                ("nuclei_detected", "idx_nuclei_detected"),
                ("recordfuture_detected", "idx_recordfuture_detected"),
            ]
            for column_name, index_name in threat_source_columns:
                try:
                    cursor.execute(f"SELECT {column_name} FROM {TABLE_VULNERABILITIES} LIMIT 1")
                    cursor.fetchone()
                    logger.info(f"{TABLE_VULNERABILITIES} already has {column_name} column")
                except Error:
                    logger.info(f"Adding {column_name} column to {TABLE_VULNERABILITIES} table...")
                    try:
                        cursor.execute(
                            f"ALTER TABLE {TABLE_VULNERABILITIES} "
                            f"ADD COLUMN {column_name} BOOLEAN DEFAULT FALSE"
                        )
                        cursor.execute(
                            f"CREATE INDEX {index_name} ON {TABLE_VULNERABILITIES}({column_name})"
                        )
                        connection.commit()
                        logger.info("Successfully added %s column and index", column_name)
                    except Error as e:
                        error_msg = str(e).lower()
                        if 'duplicate column' in error_msg or 'already exists' in error_msg or 'duplicate key' in error_msg:
                            logger.info("%s column or index already exists, skipping", column_name)
                        else:
                            logger.warning("Error adding %s column: %s", column_name, e)
                            connection.rollback()

        except Error:
            # Table doesn't exist, will be created by initialize_database
            logger.info(f"{TABLE_VULNERABILITIES} table doesn't exist, will be created")

        # Ensure rapid/nuclei tables exist before checking columns
        threat_tables = {
            TABLE_RAPID_VULNERABILITIES: [
                ("source_title", "source_title VARCHAR(255)"),
                ("source_description", "source_description TEXT"),
                ("source_severity", "source_severity VARCHAR(50)"),
                ("source_cvss", "source_cvss FLOAT"),
            ],
            TABLE_NUCLEI_VULNERABILITIES: [
                ("source_title", "source_title VARCHAR(255)"),
                ("source_description", "source_description TEXT"),
                ("source_severity", "source_severity VARCHAR(50)"),
                ("source_cvss", "source_cvss FLOAT"),
            ],
        }

        for table_name, columns in threat_tables.items():
            try:
                cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                cursor.fetchone()
                _ensure_table_columns(cursor, table_name, columns)
                connection.commit()
            except Error:
                logger.info(f"{table_name} table doesn't exist yet, will be created during initialization")
        
        cursor.close()
        
    except Error as e:
        logger.error(f"Database migration error: {e}")
        if connection:
            connection.rollback()
    except Exception as e:
        logger.error(f"Unknown error during database migration: {e}")
        if connection:
            connection.rollback()


def initialize_database(connection):
    """Initialize database table structure with new single-table architecture.
    
    Creates:
    - vulnerabilities: Main table for SoftwareVulnerabilitiesByMachine API data
    - sync_state: Sync operation history
    - vulnerability_snapshots: Snapshot statistics
    - cve_device_snapshots: CVE-Device combination snapshots for fixed status tracking
    
    Args:
        connection: Database connection
    """
    try:
        # Execute migration first
        migrate_database(connection)
        
        cursor = connection.cursor()
        
        # Create main vulnerabilities table (from SoftwareVulnerabilitiesByMachine API)
        vulnerabilities_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_VULNERABILITIES} (
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
            cve_description TEXT,
            autopatch_covered BOOLEAN DEFAULT FALSE,
            metasploit_detected BOOLEAN DEFAULT FALSE,
            nuclei_detected BOOLEAN DEFAULT FALSE,
            recordfuture_detected BOOLEAN DEFAULT FALSE,
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
            INDEX idx_metasploit_detected (metasploit_detected),
            INDEX idx_nuclei_detected (nuclei_detected),
            INDEX idx_recordfuture_detected (recordfuture_detected),
            INDEX idx_last_seen (last_seen_timestamp),
            INDEX idx_first_seen (first_seen_timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        # Create sync state table
        sync_state_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_SYNC_STATE} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            last_sync_time DATETIME NOT NULL,
            sync_type VARCHAR(20) DEFAULT 'full',
            records_count INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_sync_time (last_sync_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        # Create vulnerability snapshots table
        vulnerability_snapshots_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_VULNERABILITY_SNAPSHOTS} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            snapshot_time DATETIME NOT NULL,
            total_vulnerabilities INT DEFAULT 0,
            unique_cve_count INT DEFAULT 0,
            critical_count INT DEFAULT 0,
            high_count INT DEFAULT 0,
            medium_count INT DEFAULT 0,
            low_count INT DEFAULT 0,
            fixed_count INT DEFAULT 0,
            active_count INT DEFAULT 0,
            total_devices_affected INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_snapshot_time (snapshot_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        # Create CVE-Device snapshots table (for fixed status tracking)
        cve_device_snapshots_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_CVE_DEVICE_SNAPSHOTS} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            snapshot_id INT NOT NULL,
            cve_id VARCHAR(50) NOT NULL,
            device_id VARCHAR(100) NOT NULL,
            device_name VARCHAR(255),
            status VARCHAR(20) NOT NULL,
            severity VARCHAR(50),
            cvss_score FLOAT,
            first_seen DATETIME,
            last_seen DATETIME,
            FOREIGN KEY (snapshot_id) REFERENCES {TABLE_VULNERABILITY_SNAPSHOTS}(id) ON DELETE CASCADE,
            UNIQUE KEY uk_snapshot_cve_device (snapshot_id, cve_id, device_id),
            INDEX idx_snapshot_id (snapshot_id),
            INDEX idx_cve_id (cve_id),
            INDEX idx_device_id (device_id),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        # Create vulnerability trend periods table (materialized rollups)
        vulnerability_trend_periods_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_VULNERABILITY_TREND_PERIODS} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            period_type ENUM('week','month','year') NOT NULL,
            period_label VARCHAR(32) NOT NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            critical_active INT DEFAULT 0,
            high_active INT DEFAULT 0,
            medium_active INT DEFAULT 0,
            data_points JSON NOT NULL,
            source_snapshot_ids JSON,
            is_carry_forward BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_period_type_start (period_type, period_start),
            INDEX idx_period_type (period_type),
            INDEX idx_period_range (period_start, period_end)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        # Create recommendation reports table
        recommendation_reports_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_RECOMMENDATION_REPORTS} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cve_id VARCHAR(50) NOT NULL,
            report_content TEXT,
            ai_prompt TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_cve_id (cve_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        rapid_vulnerabilities_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_RAPID_VULNERABILITIES} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cve_id VARCHAR(50) NOT NULL UNIQUE,
            device_count INT DEFAULT 0,
            max_severity VARCHAR(50),
            max_cvss FLOAT,
            last_seen DATETIME,
            source_title VARCHAR(255),
            source_description TEXT,
            source_severity VARCHAR(50),
            source_cvss FLOAT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_rapid_cve_id (cve_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        nuclei_vulnerabilities_table = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NUCLEI_VULNERABILITIES} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cve_id VARCHAR(50) NOT NULL UNIQUE,
            device_count INT DEFAULT 0,
            max_severity VARCHAR(50),
            max_cvss FLOAT,
            last_seen DATETIME,
            source_title VARCHAR(255),
            source_description TEXT,
            source_severity VARCHAR(50),
            source_cvss FLOAT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_nuclei_cve_id (cve_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        cursor.execute(vulnerabilities_table)
        cursor.execute(sync_state_table)
        cursor.execute(vulnerability_snapshots_table)
        cursor.execute(cve_device_snapshots_table)
        cursor.execute(vulnerability_trend_periods_table)
        cursor.execute(recommendation_reports_table)
        cursor.execute(rapid_vulnerabilities_table)
        cursor.execute(nuclei_vulnerabilities_table)
        
        connection.commit()
        logger.info("Database table structure initialized successfully")
        
    except Error as e:
        logger.error(f"Error initializing database: {e}")
        if connection:
            connection.rollback()


def drop_all_tables(connection):
    """Drop all related tables in the database.
    
    This will drop all old tables including:
    - device_vulnerability_details
    - vulnerability_list
    - vulnerability_snapshots (old structure)
    - cve_snapshots
    - cve_device_changes
    - vulnerability_list_snapshots
    - sync_state (will be recreated)
    
    Args:
        connection: Database connection
    """
    try:
        cursor = connection.cursor()
        
        # Disable foreign key checks to avoid constraint issues when dropping tables
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # List all old tables that may exist
        old_tables_to_drop = [
            "disk_paths",
            "registry_paths",
            "software_vulnerabilities",
            "vulnerability_info",  # Old table name
            "device_vulnerability_details",
            "vulnerability_list",
            "vulnerability_snapshots",
            "cve_snapshots",
            "cve_device_changes",
            "vulnerability_list_snapshots",
            "sync_state",  # Will be recreated with new structure
            "vulnerabilities",  # New table, will be recreated
            "vulnerabilities_temp",  # Temporary table from previous sync
            "vulnerabilities_old",  # Old table from previous sync
            "defender_vulnerability_catalog"
        ]
        
        # Drop tables one by one
        for table in old_tables_to_drop:
            try:
                logger.info(f"Attempting to drop table: {table}")
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                logger.info(f"Successfully dropped table: {table}")
            except Error as e:
                logger.warning(f"Error dropping table {table}: {e}")
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        connection.commit()
        logger.info("All old tables dropped successfully")
        
    except Error as e:
        logger.error(f"Error occurred while dropping tables: {e}")
        if connection:
            connection.rollback()
        
    except Exception as e:
        logger.error(f"Unknown error occurred while dropping tables: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
