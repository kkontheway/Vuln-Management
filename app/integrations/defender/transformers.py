"""Data transformation utilities for Microsoft Defender API."""
from typing import Optional


def transform_severity(severity: Optional[str]) -> str:
    """Transform severity level according to Power BI conversion rules.
    
    Critical -> "1 - Critical"
    High -> "2 - High"
    Medium -> "3 - Medium"
    Low -> "4 - Low"
    
    Args:
        severity: Original severity string
        
    Returns:
        str: Transformed severity string
    """
    if not severity:
        return severity
    
    severity_str = str(severity).strip()
    severity_lower = severity_str.lower()
    
    if 'critical' in severity_lower:
        return "1 - Critical"
    elif 'high' in severity_lower:
        return "2 - High"
    elif 'medium' in severity_lower:
        return "3 - Medium"
    elif 'low' in severity_lower:
        return "4 - Low"
    else:
        # If already in transformed format, return as is
        if severity_str.startswith(('1 -', '2 -', '3 -', '4 -')):
            return severity_str
        # Otherwise return original value
        return severity_str

