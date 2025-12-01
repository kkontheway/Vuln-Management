"""Helper functions for repository operations.

This module contains utility functions to reduce complexity in repository.py.
"""
import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)


def parse_severity_counts(severity_results: list) -> Dict[str, int]:
    """Parse severity counts from query results.
    
    Args:
        severity_results: List of severity query results
        
    Returns:
        dict: Dictionary with critical_count, high_count, medium_count, low_count
    """
    counts = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0
    }
    
    for row in severity_results:
        severity_lower = row['vulnerability_severity_level'].lower()
        count = row['count']
        
        # Handle transformed format: "1 - Critical", "2 - High", etc.
        if '1 - critical' in severity_lower or ('critical' in severity_lower and '1 -' in severity_lower):
            counts['critical'] = count
        elif '2 - high' in severity_lower or ('high' in severity_lower and '2 -' in severity_lower and 'critical' not in severity_lower):
            counts['high'] = count
        elif '3 - medium' in severity_lower or ('medium' in severity_lower and '3 -' in severity_lower):
            counts['medium'] = count
        elif '4 - low' in severity_lower or ('low' in severity_lower and '4 -' in severity_lower):
            counts['low'] = count
        # Fallback for old format (without transformation)
        elif 'critical' in severity_lower and '1 -' not in severity_lower:
            counts['critical'] = count
        elif 'high' in severity_lower and '2 -' not in severity_lower and 'critical' not in severity_lower:
            counts['high'] = count
        elif 'medium' in severity_lower and '3 -' not in severity_lower:
            counts['medium'] = count
        elif 'low' in severity_lower and '4 -' not in severity_lower:
            counts['low'] = count
    
    return counts


def parse_status_counts(status_results: list) -> Dict[str, int]:
    """Parse status counts from query results.
    
    Args:
        status_results: List of status query results
        
    Returns:
        dict: Dictionary with fixed_count and active_count
    """
    counts = {
        'fixed': 0,
        'active': 0
    }
    
    for row in status_results:
        status_lower = row['status'].lower()
        count = row['count']
        
        if 'fixed' in status_lower or 'resolved' in status_lower:
            counts['fixed'] = count
        elif 'active' in status_lower or 'open' in status_lower:
            counts['active'] = count
    
    return counts


def build_device_map(devices: list) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Build device map from device list.
    
    Args:
        devices: List of device records
        
    Returns:
        dict: Dictionary mapping (cve_id, device_id) to device info
    """
    device_map = {}
    for device in devices:
        key = (device['cve_id'], device['device_id'])
        device_map[key] = {
            'device_name': device['device_name'],
            'status': device['status']
        }
    return device_map


def record_initial_snapshot_devices(cursor, snapshot_id: int, device_table: str, changes_table: str) -> None:
    """Record initial snapshot devices.
    
    Args:
        cursor: Database cursor
        snapshot_id: Snapshot ID
        device_table: Device vulnerability details table name
        changes_table: CVE device changes table name
    """
    device_changes_query = f"""
    INSERT INTO {changes_table} (
        snapshot_id, cve_id, device_id, device_name,
        change_type, current_status, change_time
    )
    SELECT 
        %s, cve_id, device_id, device_name,
        'initial', status, NOW()
    FROM {device_table}
    WHERE cve_id IS NOT NULL AND cve_id != ''
      AND device_id IS NOT NULL AND device_id != ''
    """
    cursor.execute(device_changes_query, (snapshot_id,))


def get_last_snapshot_devices(cursor, last_snapshot_id: int, changes_table: str) -> Dict[Tuple[str, str], str]:
    """Get device statuses from last snapshot.
    
    Args:
        cursor: Database cursor
        last_snapshot_id: Last snapshot ID
        changes_table: CVE device changes table name
        
    Returns:
        dict: Dictionary mapping (cve_id, device_id) to status
    """
    last_snapshot_query = f"""
    SELECT 
        cdc1.cve_id, 
        cdc1.device_id,
        COALESCE(cdc1.current_status, cdc1.previous_status) as status
    FROM {changes_table} cdc1
    INNER JOIN (
        SELECT cve_id, device_id, MAX(id) as max_id
        FROM {changes_table}
        WHERE snapshot_id = %s AND change_type != 'removed'
        GROUP BY cve_id, device_id
    ) cdc2 ON cdc1.cve_id = cdc2.cve_id 
        AND cdc1.device_id = cdc2.device_id 
        AND cdc1.id = cdc2.max_id
    WHERE cdc1.snapshot_id = %s
    """
    cursor.execute(last_snapshot_query, (last_snapshot_id, last_snapshot_id))
    last_devices = {}
    for row in cursor.fetchall():
        key = (row['cve_id'], row['device_id'])
        last_devices[key] = row['status']
    return last_devices


def record_device_changes(
    cursor,
    snapshot_id: int,
    current_device_map: Dict[Tuple[str, str], Dict[str, Any]],
    last_devices: Dict[Tuple[str, str], str],
    changes_table: str
) -> None:
    """Record device changes between snapshots.
    
    Args:
        cursor: Database cursor
        snapshot_id: Current snapshot ID
        current_device_map: Current device map
        last_devices: Last snapshot device statuses
        changes_table: CVE device changes table name
    """
    # Find added devices
    for (cve_id, device_id), info in current_device_map.items():
        if (cve_id, device_id) not in last_devices:
            cursor.execute(f"""
                INSERT INTO {changes_table} (
                    snapshot_id, cve_id, device_id, device_name,
                    change_type, current_status, change_time
                ) VALUES (%s, %s, %s, %s, 'added', %s, NOW())
            """, (snapshot_id, cve_id, device_id, info['device_name'], info['status']))
    
    # Find removed devices
    for (cve_id, device_id), prev_status in last_devices.items():
        if (cve_id, device_id) not in current_device_map:
            cursor.execute(f"""
                INSERT INTO {changes_table} (
                    snapshot_id, cve_id, device_id, device_name,
                    change_type, previous_status, change_time
                ) VALUES (%s, %s, %s, '', 'removed', %s, NOW())
            """, (snapshot_id, cve_id, device_id, prev_status))
    
    # Find devices with status changes
    for (cve_id, device_id), info in current_device_map.items():
        if (cve_id, device_id) in last_devices:
            prev_status = last_devices[(cve_id, device_id)]
            if prev_status != info['status']:
                cursor.execute(f"""
                    INSERT INTO {changes_table} (
                        snapshot_id, cve_id, device_id, device_name,
                        change_type, previous_status, current_status, change_time
                    ) VALUES (%s, %s, %s, %s, 'status_changed', %s, %s, NOW())
                """, (snapshot_id, cve_id, device_id, info['device_name'], 
                     prev_status, info['status']))
    
    # Record current status for unchanged devices (for next comparison)
    for (cve_id, device_id), info in current_device_map.items():
        if (cve_id, device_id) in last_devices:
            prev_status = last_devices[(cve_id, device_id)]
            if prev_status == info['status']:
                cursor.execute(f"""
                    INSERT INTO {changes_table} (
                        snapshot_id, cve_id, device_id, device_name,
                        change_type, current_status, change_time
                    ) VALUES (%s, %s, %s, %s, 'unchanged', %s, NOW())
                """, (snapshot_id, cve_id, device_id, info['device_name'], info['status']))


def calculate_snapshot_statistics(cursor, table_name: str) -> Dict[str, Any]:
    """Calculate snapshot statistics from vulnerabilities table.
    
    Args:
        cursor: Database cursor
        table_name: Vulnerabilities table name
        
    Returns:
        dict: Dictionary with statistics (total_vulnerabilities, unique_cve_count, 
              severity_counts, status_counts, total_devices_affected)
    """
    # Total vulnerability records (distinct CVE count to match Defender panel)
    # Changed from COUNT(*) to COUNT(DISTINCT cve_id) to match Defender panel display
    cursor.execute(f"""
        SELECT COUNT(DISTINCT cve_id) as count 
        FROM {table_name} 
        WHERE cve_id IS NOT NULL AND cve_id != ''
    """)
    total_vulnerabilities = cursor.fetchone()['count']
    
    # Distinct CVE count (same as total_vulnerabilities now)
    unique_cve_count = total_vulnerabilities
    
    # Statistics by severity (distinct CVE)
    severity_query = f"""
    SELECT 
        vulnerability_severity_level,
        COUNT(DISTINCT cve_id) as count
    FROM {table_name}
    WHERE vulnerability_severity_level IS NOT NULL 
      AND vulnerability_severity_level != ''
      AND cve_id IS NOT NULL
      AND cve_id != ''
    GROUP BY vulnerability_severity_level
    """
    cursor.execute(severity_query)
    severity_results = cursor.fetchall()
    severity_counts = parse_severity_counts(severity_results)
    
    # Statistics by status (distinct CVE)
    status_query = f"""
    SELECT 
        status,
        COUNT(DISTINCT cve_id) as count
    FROM {table_name}
    WHERE status IS NOT NULL 
      AND status != ''
      AND cve_id IS NOT NULL
      AND cve_id != ''
    GROUP BY status
    """
    cursor.execute(status_query)
    status_results = cursor.fetchall()
    status_counts = parse_status_counts(status_results)
    
    # Total affected devices (distinct)
    cursor.execute(f"""
        SELECT COUNT(DISTINCT device_id) as count 
        FROM {table_name} 
        WHERE device_id IS NOT NULL AND device_id != ''
    """)
    total_devices_affected = cursor.fetchone()['count']
    
    return {
        'total_vulnerabilities': total_vulnerabilities,
        'unique_cve_count': unique_cve_count,
        'severity_counts': severity_counts,
        'status_counts': status_counts,
        'total_devices_affected': total_devices_affected
    }

