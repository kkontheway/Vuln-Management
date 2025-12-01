"""Microsoft Defender API integration module."""
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
    get_sync_state_count,
    get_last_sync_time_by_type,
    update_sync_time,
    save_vulnerabilities,
    get_last_snapshot,
    record_snapshot,
    create_initial_snapshot
)
from app.integrations.defender.service import (
    DefenderService,
    get_defender_service
)
from app.integrations.defender.sync import (
    sync_device_vulnerabilities_full,
    perform_full_sync,
    main
)

__all__ = [
    'get_access_token',
    'create_db_connection',
    'migrate_database',
    'initialize_database',
    'drop_all_tables',
    'get_last_sync_time',
    'get_sync_state_count',
    'get_last_sync_time_by_type',
    'update_sync_time',
    'fetch_device_vulnerabilities',
    'run_advanced_query',
    'transform_severity',
    'save_vulnerabilities',
    'get_last_snapshot',
    'record_snapshot',
    'create_initial_snapshot',
    'sync_device_vulnerabilities_full',
    'perform_full_sync',
    'DefenderService',
    'get_defender_service',
    'main',
]
