"""DateTime parsing utilities for various timestamp formats."""
import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def parse_timestamp(timestamp_str: Optional[str], format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime.datetime]:
    """Parse timestamp string to datetime object.
    
    Args:
        timestamp_str: Timestamp string to parse
        format_str: Format string for parsing (default: "%Y-%m-%d %H:%M:%S")
        
    Returns:
        datetime.datetime: Parsed datetime object, None if parsing fails or input is None/empty
    """
    if not timestamp_str:
        return None
    
    try:
        return datetime.datetime.strptime(timestamp_str, format_str)
    except ValueError:
        logger.warning(f"Failed to parse timestamp: {timestamp_str} with format: {format_str}")
        return None


def parse_iso_timestamp(timestamp_str: Optional[str]) -> Optional[datetime.datetime]:
    """Parse ISO 8601 format timestamp string to datetime object.
    
    Supports formats:
    - "2024-07-30T00:00:00Z"
    - "2024-07-30T00:00:00.000Z"
    
    Args:
        timestamp_str: ISO 8601 timestamp string
        
    Returns:
        datetime.datetime: Parsed datetime object, None if parsing fails or input is None/empty
    """
    if not timestamp_str:
        return None
    
    # Remove 'Z' suffix if present
    clean_str = timestamp_str.replace('Z', '')
    
    # Try format without microseconds first
    try:
        return datetime.datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        # Try format with microseconds
        try:
            return datetime.datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            logger.warning(f"Failed to parse ISO timestamp: {timestamp_str}")
            return None


def parse_device_vulnerability_timestamps(vuln: dict) -> tuple:
    """Parse timestamps from device vulnerability record.
    
    Args:
        vuln: Vulnerability record dictionary
        
    Returns:
        tuple: (last_seen, first_seen, event_timestamp) - all Optional[datetime.datetime]
    """
    last_seen = parse_timestamp(
        vuln.get('lastSeenTimestamp'),
        format_str="%Y-%m-%d %H:%M:%S"
    ) if 'lastSeenTimestamp' in vuln and vuln['lastSeenTimestamp'] else None
    
    first_seen = parse_timestamp(
        vuln.get('firstSeenTimestamp'),
        format_str="%Y-%m-%d %H:%M:%S"
    ) if 'firstSeenTimestamp' in vuln and vuln['firstSeenTimestamp'] else None
    
    event_timestamp = parse_timestamp(
        vuln.get('eventTimestamp'),
        format_str="%Y-%m-%d %H:%M:%S.%f"
    ) if 'eventTimestamp' in vuln and vuln['eventTimestamp'] else None
    
    return last_seen, first_seen, event_timestamp


def parse_vulnerability_list_timestamps(vuln: dict) -> tuple:
    """Parse timestamps from vulnerability list record.
    
    Args:
        vuln: Vulnerability list record dictionary
        
    Returns:
        tuple: (published_on, updated_on, first_detected) - all Optional[datetime.datetime]
    """
    published_on = parse_iso_timestamp(vuln.get('publishedOn')) if 'publishedOn' in vuln and vuln['publishedOn'] else None
    updated_on = parse_iso_timestamp(vuln.get('updatedOn')) if 'updatedOn' in vuln and vuln['updatedOn'] else None
    first_detected = parse_iso_timestamp(vuln.get('firstDetected')) if 'firstDetected' in vuln and vuln['firstDetected'] else None
    
    return published_on, updated_on, first_detected

