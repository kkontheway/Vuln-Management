"""Microsoft Defender API integration - backward compatibility wrapper.

This module re-exports functions from the refactored modules to maintain backward compatibility.
All functions are now organized in app/integrations/defender/ modules.
"""
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("defender_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Re-export all functions from refactored modules for backward compatibility
from app.integrations.defender.auth import get_access_token
from app.integrations.defender.database import (
    create_db_connection,
    migrate_database,
    initialize_database,
    drop_all_tables
)
from app.integrations.defender.api_client import (
    fetch_device_vulnerabilities,
    run_advanced_query
)
from app.integrations.defender.transformers import transform_severity
from app.integrations.defender.repository import (
    get_last_sync_time,
    update_sync_time,
    save_vulnerabilities,
    get_last_snapshot,
    record_snapshot
)
from app.integrations.defender.sync import (
    sync_device_vulnerabilities_full,
    perform_full_sync,
    main
)

# Re-export config for backward compatibility
from app.integrations.defender.config import (
    TENANT_ID,
    APP_ID,
    APP_SECRET,
    REGION_ENDPOINT,
    API_BASE_URL,
    DB_CONFIG
)

__all__ = [
    'get_access_token',
    'create_db_connection',
    'migrate_database',
    'initialize_database',
    'drop_all_tables',
    'get_last_sync_time',
    'update_sync_time',
    'fetch_device_vulnerabilities',
    'run_advanced_query',
    'transform_severity',
    'save_vulnerabilities',
    'get_last_snapshot',
    'record_snapshot',
    'sync_device_vulnerabilities_full',
    'perform_full_sync',
    'main',
    'TENANT_ID',
    'APP_ID',
    'APP_SECRET',
    'REGION_ENDPOINT',
    'API_BASE_URL',
    'DB_CONFIG',
]

if __name__ == "__main__":
    main()
