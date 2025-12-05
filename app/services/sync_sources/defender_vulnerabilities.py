"""Sync source runner for Microsoft Defender vulnerabilities."""
import logging

from app.integrations.defender.database import create_db_connection, initialize_database
from app.integrations.defender.sync import perform_full_sync
from .base import SyncSourceResult, success_result

logger = logging.getLogger(__name__)


def run() -> SyncSourceResult:
    """Execute the main Microsoft Defender vulnerability sync."""
    connection = create_db_connection()
    if not connection:
        raise Exception("Failed to connect to database for Defender sync")
    try:
        logger.info("Initializing database before Defender sync")
        initialize_database(connection)
        perform_full_sync(connection, None)
        return success_result("Defender vulnerability sync completed")
    finally:
        if connection and connection.is_connected():
            connection.close()
