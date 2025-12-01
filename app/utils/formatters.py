"""Data formatting utilities."""
from datetime import datetime
import json


def format_datetime_fields(record, date_fields):
    """Format datetime fields in a record to ISO format strings.
    
    Args:
        record (dict): Record containing datetime fields
        date_fields (list): List of field names that should be formatted
    
    Returns:
        dict: Record with formatted datetime fields
    """
    for field in date_fields:
        if record.get(field):
            if isinstance(record[field], datetime):
                record[field] = record[field].isoformat()
    return record


def parse_json_fields(record, json_fields):
    """Parse JSON string fields in a record.
    
    Args:
        record (dict): Record containing JSON string fields
        json_fields (list): List of field names that should be parsed as JSON
    
    Returns:
        dict: Record with parsed JSON fields
    """
    for field in json_fields:
        if record.get(field):
            try:
                record[field] = json.loads(record[field])
            except (json.JSONDecodeError, TypeError):
                record[field] = []
    return record

