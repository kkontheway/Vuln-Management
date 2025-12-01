"""Threat intelligence service for business logic."""
import logging
import re
import csv
import io

logger = logging.getLogger(__name__)


def extract_ip_addresses(text):
    """Extract RecordFuture indicators from text and generate CSV file.
    
    Args:
        text (str): Text containing indicators
    
    Returns:
        dict: Extracted IPs, CSV content, and count
    
    Raises:
        ValueError: If text is empty
    """
    if not text:
        raise ValueError('Text is required')
    
    # Extract IP addresses using regex (IPv4)
    # Pattern 1: Normal IP format (192.168.1.1)
    normal_ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    # Pattern 2: Obfuscated IP format with brackets (192[.]168[.]1[.]1)
    obfuscated_ip_pattern = r'\b(?:\d{1,3})\[\.\](?:\d{1,3})\[\.\](?:\d{1,3})\[\.\](?:\d{1,3})\b'
    
    # Find all matches
    normal_ips = re.findall(normal_ip_pattern, text)
    obfuscated_ips = re.findall(obfuscated_ip_pattern, text)
    
    # Clean obfuscated IPs by removing brackets
    cleaned_obfuscated_ips = []
    for ip in obfuscated_ips:
        cleaned_ip = ip.replace('[.]', '.')
        cleaned_obfuscated_ips.append(cleaned_ip)
    
    # Extract CVE identifiers
    cve_pattern = r'\bCVE-\d{4}-\d{4,7}\b'
    raw_cves = re.findall(cve_pattern, text, flags=re.IGNORECASE)
    normalized_cves = []
    seen_cves = set()
    for cve in raw_cves:
        normalized = cve.upper()
        if normalized in seen_cves:
            continue
        seen_cves.add(normalized)
        normalized_cves.append(normalized)

    # Combine all IPs
    all_ips = normal_ips + cleaned_obfuscated_ips
    
    # Validate and filter IP addresses
    valid_ips = []
    for ip in all_ips:
        parts = ip.split('.')
        if len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts):
            # Remove duplicates while preserving order
            if ip not in valid_ips:
                valid_ips.append(ip)
    
    if not valid_ips and not normalized_cves:
        return {
            'ips': [],
            'cves': [],
            'csv': None,
            'message': 'No valid IP addresses found'
        }
    
    csv_content = generate_csv(valid_ips) if valid_ips else None
    
    return {
        'ips': valid_ips,
        'cves': normalized_cves,
        'csv': csv_content,
        'count': len(valid_ips)
    }


def generate_csv(ips):
    """Generate CSV file content for IP addresses.
    
    Args:
        ips (list): List of IP addresses
    
    Returns:
        str: CSV file content
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'IndicatorType',
        'IndicatorValue',
        'ExpirationTime',
        'Action',
        'Severity',
        'Title',
        'description',
        'recommendedActions',
        'RbacGroups',
        'Category',
        'MitreTechniques',
        'GenerateAlert'
    ])
    
    # Write data rows
    for ip in ips:
        writer.writerow([
            'IPAddress',  # IndicatorType
            ip,  # IndicatorValue
            '',  # ExpirationTime
            'Block',  # Action
            'Low',  # Severity
            'RecordFuture MaliciousIPAddress',  # Title
            'RecordFuture MaliciousIPAddress',  # description
            '',  # recommendedActions
            '',  # RbacGroups
            'SuspiciousActivity',  # Category
            '',  # MitreTechniques
            'True'  # GenerateAlert
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return csv_content
