"""Snapshot service for business logic."""
import logging
from datetime import datetime
from database import get_db_connection
from app.utils.formatters import format_datetime_fields
from app.constants.database import (
    TABLE_VULNERABILITY_SNAPSHOTS,
    TABLE_CVE_DEVICE_SNAPSHOTS,
)

logger = logging.getLogger(__name__)


def create_initial_snapshot():
    """Create initial vulnerability snapshot.
    
    Returns:
        dict: Status and snapshot_id
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("Database connection failed")
    
    try:
        # Import here to avoid circular dependency
        from app.integrations.defender.database import initialize_database
        from app.integrations.defender.repository import create_initial_snapshot
        
        initialize_database(connection)
        snapshot_id = create_initial_snapshot(connection)
        
        if snapshot_id:
            return {
                'status': 'success',
                'message': 'Initial snapshot created successfully',
                'snapshot_id': snapshot_id
            }
        else:
            raise Exception('Failed to create initial snapshot')
    except ImportError as e:
        logger.error(f"导入defender模块失败: {e}")
        raise Exception(f'Import error: {str(e)}')
    finally:
        if connection and connection.is_connected():
            connection.close()


def get_snapshots(limit=100):
    """Get list of vulnerability snapshots.
    
    Args:
        limit (int): Maximum number of snapshots to return
    
    Returns:
        dict: snapshots list and total count
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = f"""
        SELECT 
            id, snapshot_time, total_vulnerabilities, unique_cve_count,
            critical_count, high_count, medium_count, low_count,
            fixed_count, active_count, total_devices_affected,
            created_at
        FROM {TABLE_VULNERABILITY_SNAPSHOTS}
        ORDER BY snapshot_time DESC
        LIMIT %s
        """
        cursor.execute(query, (limit,))
        snapshots = cursor.fetchall()
        
        # Format datetime fields
        for snapshot in snapshots:
            format_datetime_fields(snapshot, ['snapshot_time', 'created_at'])
        
        return {
            'snapshots': snapshots,
            'total': len(snapshots)
        }
    finally:
        cursor.close()
        connection.close()


def get_snapshot_details(snapshot_id):
    """Get detailed information for a specific snapshot.
    
    Args:
        snapshot_id (int): Snapshot ID
    
    Returns:
        dict: Snapshot details, CVE snapshots, and change stats
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get snapshot basic info
        cursor.execute(
            f"SELECT * FROM {TABLE_VULNERABILITY_SNAPSHOTS} WHERE id = %s",
            (snapshot_id,)
        )
        snapshot = cursor.fetchone()
        
        if not snapshot:
            raise Exception('Snapshot not found')
        
        format_datetime_fields(snapshot, ['snapshot_time', 'created_at'])
        
        # Aggregate CVE-level statistics from device snapshot table
        cve_query = f"""
        SELECT 
            cve_id,
            COUNT(*) AS device_count,
            SUM(CASE WHEN LOWER(COALESCE(status, '')) LIKE 'fixed%%' THEN 1 ELSE 0 END) AS fixed_devices,
            SUM(CASE WHEN LOWER(COALESCE(status, '')) LIKE 'active%%' THEN 1 ELSE 0 END) AS active_devices,
            MIN(first_seen) AS first_seen,
            MAX(last_seen) AS last_seen,
            MAX(severity) AS severity,
            MAX(cvss_score) AS max_cvss_score
        FROM {TABLE_CVE_DEVICE_SNAPSHOTS}
        WHERE snapshot_id = %s
        GROUP BY cve_id
        ORDER BY device_count DESC
        LIMIT 1000
        """
        cursor.execute(cve_query, (snapshot_id,))
        cve_snapshots = cursor.fetchall()
        for cve in cve_snapshots:
            format_datetime_fields(cve, ['first_seen', 'last_seen'])
        
        status_query = f"""
        SELECT 
            COALESCE(status, 'Unknown') AS status,
            COUNT(*) AS count
        FROM {TABLE_CVE_DEVICE_SNAPSHOTS}
        WHERE snapshot_id = %s
        GROUP BY COALESCE(status, 'Unknown')
        ORDER BY count DESC
        """
        cursor.execute(status_query, (snapshot_id,))
        status_rows = cursor.fetchall()
        change_stats = [
            {'change_type': row['status'], 'count': row['count']}
            for row in status_rows
        ]
        
        return {
            'snapshot': snapshot,
            'cve_snapshots': cve_snapshots,
            'change_stats': change_stats
        }
    finally:
        cursor.close()
        connection.close()


def get_cve_history(cve_id):
    """Get historical changes for a specific CVE.
    
    Args:
        cve_id (str): CVE ID
    
    Returns:
        dict: CVE history and device changes
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        history_query = f"""
        SELECT 
            stats.snapshot_id,
            vs.snapshot_time,
            stats.device_count,
            stats.active_devices,
            stats.fixed_devices,
            stats.first_seen,
            stats.last_seen
        FROM (
            SELECT 
                snapshot_id,
                COUNT(*) AS device_count,
                SUM(CASE WHEN LOWER(COALESCE(status, '')) LIKE 'active%%' THEN 1 ELSE 0 END) AS active_devices,
                SUM(CASE WHEN LOWER(COALESCE(status, '')) LIKE 'fixed%%' THEN 1 ELSE 0 END) AS fixed_devices,
                MIN(first_seen) AS first_seen,
                MAX(last_seen) AS last_seen
            FROM {TABLE_CVE_DEVICE_SNAPSHOTS}
            WHERE cve_id = %s
            GROUP BY snapshot_id
        ) stats
        JOIN {TABLE_VULNERABILITY_SNAPSHOTS} vs ON vs.id = stats.snapshot_id
        ORDER BY vs.snapshot_time ASC
        """
        cursor.execute(history_query, (cve_id,))
        cve_history = cursor.fetchall()
        
        for record in cve_history:
            format_datetime_fields(record, ['snapshot_time', 'first_seen', 'last_seen'])
        
        device_query = f"""
        SELECT 
            cds.snapshot_id,
            cds.device_id,
            cds.device_name,
            cds.status,
            cds.severity,
            cds.cvss_score,
            cds.first_seen,
            cds.last_seen,
            vs.snapshot_time
        FROM {TABLE_CVE_DEVICE_SNAPSHOTS} cds
        JOIN {TABLE_VULNERABILITY_SNAPSHOTS} vs ON vs.id = cds.snapshot_id
        WHERE cds.cve_id = %s
        ORDER BY vs.snapshot_time DESC, cds.last_seen DESC
        LIMIT 500
        """
        cursor.execute(device_query, (cve_id,))
        device_rows = cursor.fetchall()
        
        device_changes = []
        for row in device_rows:
            format_datetime_fields(row, ['snapshot_time', 'first_seen', 'last_seen'])
            device_changes.append({
                'snapshot_id': row['snapshot_id'],
                'snapshot_time': row['snapshot_time'],
                'device_id': row['device_id'],
                'device_name': row['device_name'],
                'change_type': 'snapshot_record',
                'current_status': row['status'],
                'previous_status': None,
                'severity': row.get('severity'),
                'cvss_score': row.get('cvss_score'),
                'first_seen': row.get('first_seen'),
                'last_seen': row.get('last_seen'),
            })
        
        return {
            'cve_id': cve_id,
            'history': cve_history,
            'device_changes': device_changes
        }
    finally:
        cursor.close()
        connection.close()


def get_snapshots_trend():
    """Get snapshot trend data for line chart.
    
    Returns:
        dict: Trend data with date, critical, high, medium counts
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = f"""
        SELECT 
            DATE(snapshot_time) as snapshot_date,
            snapshot_time,
            critical_count,
            high_count,
            medium_count
        FROM {TABLE_VULNERABILITY_SNAPSHOTS}
        ORDER BY snapshot_time ASC
        """
        cursor.execute(query)
        all_snapshots = cursor.fetchall()
        
        # Aggregate by day: if multiple snapshots on same day, take the latest
        daily_data = {}
        for snapshot in all_snapshots:
            date_key = snapshot['snapshot_date']
            if hasattr(date_key, 'isoformat'):
                date_key = date_key.isoformat()
            else:
                date_key = str(date_key)
            
            # If day already has data, compare time and keep the latest
            if date_key not in daily_data:
                daily_data[date_key] = snapshot
            else:
                current_time = snapshot['snapshot_time']
                existing_time = daily_data[date_key]['snapshot_time']
                
                # Ensure both are datetime objects for comparison
                if isinstance(current_time, str):
                    try:
                        current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
                    except:
                        current_time = datetime.strptime(current_time.split('.')[0], '%Y-%m-%d %H:%M:%S')
                if isinstance(existing_time, str):
                    try:
                        existing_time = datetime.fromisoformat(existing_time.replace('Z', '+00:00'))
                    except:
                        existing_time = datetime.strptime(existing_time.split('.')[0], '%Y-%m-%d %H:%M:%S')
                
                if current_time > existing_time:
                    daily_data[date_key] = snapshot
        
        # Convert to list and sort by date
        trend_data = []
        for date_key in sorted(daily_data.keys()):
            snapshot = daily_data[date_key]
            # Format datetime fields
            if snapshot['snapshot_time']:
                if isinstance(snapshot['snapshot_time'], datetime):
                    snapshot['snapshot_time'] = snapshot['snapshot_time'].isoformat()
                snapshot['snapshot_date'] = snapshot['snapshot_date'].isoformat() if hasattr(snapshot['snapshot_date'], 'isoformat') else str(snapshot['snapshot_date'])
            trend_data.append({
                'date': snapshot['snapshot_date'],
                'snapshot_time': snapshot['snapshot_time'],
                'critical': snapshot['critical_count'] or 0,
                'high': snapshot['high_count'] or 0,
                'medium': snapshot['medium_count'] or 0
            })
        
        return {
            'trend': trend_data,
            'total': len(trend_data)
        }
    finally:
        cursor.close()
        connection.close()
