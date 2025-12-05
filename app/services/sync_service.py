"""Sync service for business logic."""
import json
import logging
import subprocess
import threading
from typing import Optional
from mysql.connector import Error
from database import get_db_connection
from app.utils.cache import get_cache_client
from app.services.threat_source_sync_service import sync_threat_sources
from app.services.recordfuture_service import rebuild_detection_flags

logger = logging.getLogger(__name__)

# Global sync status
sync_in_progress = False

# Global sync progress tracking
sync_progress = {
    'stage': '',
    'progress': 0,
    'message': '',
    'is_complete': False,
    'is_syncing': False
}

SYNC_PROGRESS_CACHE_KEY = "sync:progress"


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
        'is_syncing': source.get('is_syncing', sync_in_progress)
    }


def trigger_sync(data_sources=None):
    """Trigger data sync in background thread.
    
    Args:
        data_sources (list): Deprecated, kept for backward compatibility. Ignored.
    
    Returns:
        dict: Status message
    
    Raises:
        Exception: If sync is already in progress
    """
    global sync_in_progress, sync_progress
    
    global sync_in_progress
    if sync_in_progress:
        raise Exception('Sync is already in progress. Please wait for it to complete.')
    
    sync_in_progress = True
    _set_progress('initializing', 0, 'Starting sync...', is_complete=False, is_syncing=True)
    
    def run_sync():
        global sync_in_progress
        try:
            logger.info("Starting data sync in background thread (full sync)")
            
            # Update progress: Getting access token
            _set_progress('authenticating', 10, 'Getting access token...', is_syncing=True)
            
            # Call defender.py main function directly (no data source arguments needed)
            cmd = ['python3', 'defender.py']
            
            # Update progress: Starting data fetch
            _set_progress('fetching', 30, 'Fetching data from Microsoft Defender API...', is_syncing=True)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            # Update progress: Processing data
            _set_progress('processing', 60, 'Processing and saving data...', is_syncing=True)
            
            if result.returncode == 0:
                try:
                    _set_progress('threat_sources', 80, 'Refreshing Rapid7/Nuclei intelligence...', is_syncing=True)
                    sync_threat_sources()
                except Exception as exc:
                    logger.error("Threat source enrichment failed: %s", exc)
                try:
                    _set_progress('recordfuture', 85, 'Rebuilding RecordFuture intelligence flags...', is_syncing=True)
                    rebuild_detection_flags()
                except Exception as exc:
                    logger.error("RecordFuture flag rebuild failed: %s", exc)

                # Update progress: Creating snapshot
                _set_progress('snapshot', 90, 'Creating snapshot...', is_syncing=True)
                
                logger.info("Data sync completed successfully")
                
                # Update progress: Complete
                _set_progress('complete', 100, 'Sync completed successfully', is_complete=True, is_syncing=False)
            else:
                logger.error(f"Data sync failed: {result.stderr}")
                _set_progress('error', 0, f'Sync failed: {result.stderr[:100]}', is_complete=True, is_syncing=False)
                
        except subprocess.TimeoutExpired:
            logger.error("Data sync timed out")
            _set_progress('error', 0, 'Sync timed out', is_complete=True, is_syncing=False)
        except Exception as e:
            logger.error(f"同步执行失败: {e}")
            _set_progress('error', 0, f'Sync failed: {str(e)[:100]}', is_complete=True, is_syncing=False)
        finally:
            sync_in_progress = False
            if not sync_progress.get('is_complete'):
                _set_progress(sync_progress.get('stage', ''), sync_progress.get('progress', 0), sync_progress.get('message', ''), is_complete=sync_progress.get('is_complete', False), is_syncing=False)
    
    # Start background thread
    sync_thread = threading.Thread(target=run_sync, daemon=True)
    sync_thread.start()
    
    return {
        'status': 'started',
        'message': 'Data sync started in background'
    }
