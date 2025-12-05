"""Sync service for business logic."""
import json
import logging
import threading
from typing import List, Optional
from mysql.connector import Error
from database import get_db_connection
from app.utils.cache import get_cache_client
from app.services.sync_sources import (
    get_default_source_keys,
    get_sync_source_map,
    get_sync_sources,
)
from app.services.sync_sources.base import SyncSource, SyncSourceResult

logger = logging.getLogger(__name__)

# Global sync status
sync_in_progress = False

# Global sync progress tracking
sync_progress = {
    'stage': '',
    'progress': 0,
    'message': '',
    'is_complete': False,
    'is_syncing': False,
    'sources': []
}

SYNC_PROGRESS_CACHE_KEY = "sync:progress"


def list_sync_sources():
    """Return available sync sources for UI consumption."""
    return [
        {
            'key': source.key,
            'name': source.name,
            'description': source.description,
            'default_enabled': source.default_enabled,
            'order': source.order,
        }
        for source in get_sync_sources()
    ]


def _persist_progress():
    """Persist current progress state to Redis if available."""
    client = get_cache_client()
    if not client:
        return
    try:
        client.set(SYNC_PROGRESS_CACHE_KEY, json.dumps(sync_progress))
    except Exception as exc:
        logger.warning("Failed to persist sync progress: %s", exc)


def _load_progress_from_cache():
    """Load progress state from Redis."""
    client = get_cache_client()
    if not client:
        return None
    try:
        value = client.get(SYNC_PROGRESS_CACHE_KEY)
        if value:
            return json.loads(value)
    except Exception as exc:
        logger.warning("Failed to load sync progress from cache: %s", exc)
    return None


def _initialize_source_states(selected_sources: List[SyncSource]):
    """Prepare per-source status tracking."""
    sync_progress['sources'] = [
        {
            'key': source.key,
            'name': source.name,
            'status': 'pending',
            'message': ''
        }
        for source in selected_sources
    ]


def _update_source_state(source_key: str, status: str, message: str = ''):
    """Update the status dictionary for a single source."""
    sources = sync_progress.get('sources', [])
    for entry in sources:
        if entry.get('key') == source_key:
            entry.update({'status': status, 'message': message})
            break
    sync_progress['sources'] = sources
    _persist_progress()


def _set_progress(stage: str, progress_value: int, message: str, *, is_complete: bool = False, is_syncing: Optional[bool] = None):
    """Update in-memory progress and persist."""
    global sync_progress
    if is_syncing is None:
        is_syncing = sync_in_progress
    sync_progress.update({
        'stage': stage,
        'progress': progress_value,
        'message': message,
        'is_complete': is_complete,
        'is_syncing': is_syncing
    })
    _persist_progress()


def get_sync_status():
    """Get sync status and last sync time.
    
    Returns:
        dict: {
            device_vulnerabilities: { last_sync_time: ..., sync_type: ..., records_count: ... }
        }
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Check if records_count column exists (for backward compatibility)
        try:
            cursor.execute("SELECT records_count FROM sync_state LIMIT 1")
            # Consume the result to avoid "Unread result found" error
            cursor.fetchone()
            has_records_count = True
        except Error:
            has_records_count = False
        
        # Build query based on available columns
        if has_records_count:
            query = """
            SELECT last_sync_time, sync_type, records_count
            FROM sync_state
            ORDER BY id DESC
            LIMIT 1
            """
        else:
            # Fallback for old table structure
            query = """
            SELECT last_sync_time, sync_type
            FROM sync_state
            ORDER BY id DESC
            LIMIT 1
            """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        # 返回结构（保持向后兼容）
        status = {
            'device_vulnerabilities': {
                'last_sync_time': result['last_sync_time'].isoformat() if result and result['last_sync_time'] else None,
                'sync_type': result['sync_type'] if result else None,
                'records_count': result.get('records_count', 0) if result else 0
            }
        }
        source_status = {}
        for src in get_sync_sources():
            if src.key == 'defender_vulnerabilities':
                last_sync = status['device_vulnerabilities']['last_sync_time']
                sync_type = status['device_vulnerabilities']['sync_type']
            else:
                last_sync = None
                sync_type = None
            source_status[src.key] = {
                'name': src.name,
                'last_sync_time': last_sync,
                'sync_type': sync_type
            }
        status['sources'] = source_status
        return status
    finally:
        cursor.close()
        connection.close()


def get_sync_progress():
    """Get current sync progress.
    
    Returns:
        dict: {
            'stage': str - Current stage name,
            'progress': int - Progress percentage (0-100),
            'message': str - Progress message,
            'is_complete': bool - Whether sync is complete,
            'is_syncing': bool - Whether sync is in progress
        }
    """
    global sync_progress, sync_in_progress
    cached = _load_progress_from_cache()
    source = cached or sync_progress
    return {
        'stage': source.get('stage', ''),
        'progress': source.get('progress', 0),
        'message': source.get('message', ''),
        'is_complete': source.get('is_complete', False),
        'is_syncing': source.get('is_syncing', sync_in_progress),
        'sources': source.get('sources', [])
    }


def _resolve_selected_sources(data_sources: Optional[List[str]]) -> List[SyncSource]:
    """Validate and resolve requested sources."""
    source_map = get_sync_source_map()
    if data_sources:
        selected = []
        for key in data_sources:
            source = source_map.get(key)
            if not source:
                raise Exception(f"Unknown data source: {key}")
            selected.append(source)
    else:
        selected = [source_map[key] for key in get_default_source_keys() if key in source_map]
    if not selected:
        raise Exception("No valid data sources selected for sync")
    return sorted(selected)


def trigger_sync(data_sources: Optional[List[str]] = None):
    """Trigger modular data sync in background thread."""
    global sync_in_progress
    if sync_in_progress:
        raise Exception('Sync is already in progress. Please wait for it to complete.')

    selected_sources = _resolve_selected_sources(data_sources)
    sync_in_progress = True
    _initialize_source_states(selected_sources)
    _set_progress('initializing', 0, 'Starting sync...', is_complete=False, is_syncing=True)

    def run_sync():
        _run_sync_job(selected_sources)

    thread = threading.Thread(target=run_sync, daemon=True)
    thread.start()
    return {
        'message': 'Sync started',
        'data_sources': [source.key for source in selected_sources]
    }


def _run_sync_job(selected_sources: List[SyncSource]):
    """Execute sync sources sequentially."""
    global sync_in_progress
    total = len(selected_sources)
    try:
        for index, source in enumerate(selected_sources):
            start_progress = int((index / total) * 100)
            _update_source_state(source.key, 'running', 'In progress...')
            _set_progress(source.key, start_progress, f'Running {source.name}...', is_syncing=True)
            try:
                result: Optional[SyncSourceResult] = source.runner()
                if result and not result.success:
                    raise Exception(result.message or 'Sync source reported failure')
                success_message = (result.message if result else '') or 'Completed successfully'
                _update_source_state(source.key, 'success', success_message)
                end_progress = int(((index + 1) / total) * 100)
                _set_progress(source.key, end_progress, success_message, is_syncing=True)
            except Exception as exc:
                logger.error("Sync source %s failed: %s", source.key, exc, exc_info=True)
                _update_source_state(source.key, 'error', str(exc))
                _set_progress('error', start_progress, f'{source.name} failed: {exc}', is_complete=True, is_syncing=False)
                return

        _set_progress('complete', 100, 'Sync completed successfully', is_complete=True, is_syncing=False)
    finally:
        sync_in_progress = False
