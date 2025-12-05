"""Synchronization logic for Microsoft Defender vulnerability data."""
import datetime
import logging
from typing import Optional
from app.integrations.defender.database import create_db_connection, initialize_database
from app.integrations.defender.service import get_defender_service
from app.integrations.defender.repository import (
    save_vulnerabilities,
    record_snapshot,
    update_sync_time,
    save_vulnerability_catalog
)
from app.constants.database import SYNC_TYPE_FULL, TABLE_VULNERABILITIES

logger = logging.getLogger(__name__)


def sync_device_vulnerabilities_full(connection, access_token: Optional[str] = None):
    """Sync device vulnerability details (full sync).
    
    Uses SoftwareVulnerabilitiesByMachine API to fetch all vulnerability data
    and saves it using table switching method.
    
    Args:
        connection: Database connection
        access_token: Microsoft Defender API access token (optional, will be obtained via service if not provided)
    """
    logger.info("Starting device vulnerability details full sync...")
    
    try:
        service = get_defender_service()
        logger.info("Fetching vulnerabilities from Microsoft Defender API...")
        vulnerabilities = service.fetch_device_vulnerabilities()
        
        logger.info(f"API returned {len(vulnerabilities) if vulnerabilities else 0} vulnerability records")
        
        if vulnerabilities and len(vulnerabilities) > 0:
            logger.info(f"Saving {len(vulnerabilities)} vulnerability records to database...")
            save_vulnerabilities(connection, vulnerabilities, is_delta=False)
            
            # Verify data was saved
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SELECT COUNT(*) as count FROM {TABLE_VULNERABILITIES}")
            saved_count = cursor.fetchone()['count']
            cursor.close()
            
            logger.info(f"Database verification: {saved_count} records in database after save")
            
            if saved_count == 0:
                raise Exception(f"CRITICAL: No records found in database after save operation! Expected {len(vulnerabilities)} records.")
            
            logger.info(f"Device vulnerability details full sync completed, fetched {len(vulnerabilities)} records, saved {saved_count} records")
            
            # Record sync time with record count
            current_time = datetime.datetime.now()
            update_sync_time(connection, current_time, sync_type=SYNC_TYPE_FULL, records_count=saved_count)
            logger.info(f"Sync time recorded: {current_time}, records: {saved_count}")
        else:
            logger.warning("No device vulnerability details data to sync (API returned empty or None)")
            # Still record sync time even if no data
            current_time = datetime.datetime.now()
            update_sync_time(connection, current_time, sync_type=SYNC_TYPE_FULL, records_count=0)
            logger.info(f"Sync time recorded with 0 records: {current_time}")
    except Exception as e:
        logger.error(f"Error syncing device vulnerability details: {e}", exc_info=True)
        raise


def perform_full_sync(connection, access_token: Optional[str] = None):
    """Perform full sync.
    
    Syncs all vulnerability data from SoftwareVulnerabilitiesByMachine API
    and creates a snapshot after sync completes.
    
    Args:
        connection: Database connection
        access_token: Microsoft Defender API access token
    """
    logger.info("Starting full sync...")
    
    try:
        # Sync device vulnerability details (full)
        sync_device_vulnerabilities_full(connection, access_token)
        
        # Sync vulnerability catalog (separate table)
        sync_vulnerability_catalog(connection)
        
        # Record snapshot after sync completes
        logger.info("Creating snapshot after sync...")
        snapshot_id = record_snapshot(connection)
        if snapshot_id:
            logger.info(f"Snapshot created successfully with ID: {snapshot_id}")
        else:
            logger.error("Failed to create snapshot after sync!")
            raise Exception("Snapshot creation failed after sync")
        logger.info("Full sync completed successfully")
    except Exception as e:
        logger.error(f"Error during full sync: {e}")
        raise


def main():
    """Main function for command-line execution."""
    logger.info("Starting Defender vulnerability data sync...")
    
    # Create database connection
    connection = create_db_connection()
    if not connection:
        logger.error("Failed to connect to database, exiting")
        return
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        initialize_database(connection)
        logger.info("Database initialization completed")
        
        # Perform full sync
        logger.info("Starting full sync process...")
        perform_full_sync(connection, None)
        logger.info("Full sync process completed successfully")
    
    except Exception as e:
        logger.error(f"CRITICAL ERROR occurred during sync: {e}", exc_info=True)
        # Re-raise exception to ensure sync_service knows it failed
        raise
    
    finally:
        if connection and connection.is_connected():
            connection.close()
            logger.info("Database connection closed")
    
    logger.info("Vulnerability data sync completed successfully")


def sync_vulnerability_catalog(connection) -> None:
    """Sync CVE catalog data into dedicated table."""
    logger.info("Starting vulnerability catalog sync...")
    service = get_defender_service()
    catalog_records = service.fetch_vulnerability_catalog()
    logger.info("Catalog API returned %s records", len(catalog_records) if catalog_records else 0)
    if not catalog_records:
        logger.warning("No catalog data to sync")
        return
    saved = save_vulnerability_catalog(connection, catalog_records)
    logger.info("Catalog sync completed, %s records saved", saved)


if __name__ == "__main__":
    main()
