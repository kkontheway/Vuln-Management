"""Simple query builder for reducing SQL string duplication."""
from typing import Dict, List, Tuple, Any, Optional


# Field mapping from API response keys to database column names
DEVICE_VULNERABILITY_FIELD_MAP = {
    'cveId': 'cve_id',
    'diskPaths': 'disk_paths',  # JSON field
    'registryPaths': 'registry_paths',  # JSON field
    'deviceId': 'device_id',
    'rbacGroupName': 'rbac_group_name',
    'deviceName': 'device_name',
    'osPlatform': 'os_platform',
    'osVersion': 'os_version',
    'osArchitecture': 'os_architecture',
    'softwareVendor': 'software_vendor',
    'softwareName': 'software_name',
    'softwareVersion': 'software_version',
    'vulnerabilitySeverityLevel': 'vulnerability_severity_level',  # Transformed
    'recommendedSecurityUpdate': 'recommended_security_update',
    'recommendedSecurityUpdateId': 'recommended_security_update_id',
    'recommendedSecurityUpdateUrl': 'recommended_security_update_url',
    'lastSeenTimestamp': 'last_seen_timestamp',  # Parsed datetime
    'firstSeenTimestamp': 'first_seen_timestamp',  # Parsed datetime
    'exploitabilityLevel': 'exploitability_level',
    'recommendationReference': 'recommendation_reference',
    'securityUpdateAvailable': 'security_update_available',
    'eventTimestamp': 'event_timestamp',  # Parsed datetime
    'status': 'status',
    'cvssScore': 'cvss_score',
}

# All fields for INSERT (includes id)
DEVICE_VULNERABILITY_INSERT_FIELDS = [
    'id', 'cve_id', 'disk_paths', 'registry_paths', 'device_id', 'rbac_group_name', 
    'device_name', 'os_platform', 'os_version', 'os_architecture', 'software_vendor', 
    'software_name', 'software_version', 'vulnerability_severity_level', 
    'recommended_security_update', 'recommended_security_update_id', 
    'recommended_security_update_url', 'last_seen_timestamp', 'first_seen_timestamp', 
    'exploitability_level', 'recommendation_reference', 'security_update_available', 
    'event_timestamp', 'status', 'cvss_score', 'last_updated'
]

# Fields for UPDATE (excludes id and last_updated)
DEVICE_VULNERABILITY_UPDATE_FIELDS = [
    'cve_id', 'disk_paths', 'registry_paths', 'device_id', 'rbac_group_name', 
    'device_name', 'os_platform', 'os_version', 'os_architecture', 'software_vendor', 
    'software_name', 'software_version', 'vulnerability_severity_level', 
    'recommended_security_update', 'recommended_security_update_id', 
    'recommended_security_update_url', 'last_seen_timestamp', 'first_seen_timestamp', 
    'exploitability_level', 'recommendation_reference', 'security_update_available', 
    'event_timestamp', 'status', 'cvss_score'
]


def build_insert_query(table_name: str, fields: List[str]) -> str:
    """Build INSERT query string.
    
    Args:
        table_name: Table name
        fields: List of field names
        
    Returns:
        str: INSERT query string
    """
    fields_str = ', '.join(fields)
    placeholders = ', '.join(['%s'] * len(fields))
    return f"INSERT INTO {table_name} ({fields_str}) VALUES ({placeholders})"


def build_update_query(table_name: str, fields: List[str], where_clause: str = "WHERE id = %s") -> str:
    """Build UPDATE query string.
    
    Args:
        table_name: Table name
        fields: List of field names to update
        where_clause: WHERE clause (default: "WHERE id = %s")
        
    Returns:
        str: UPDATE query string
    """
    set_clause = ', '.join([f"{field} = %s" for field in fields])
    return f"UPDATE {table_name} SET {set_clause} {where_clause}"


def build_upsert_query(table_name: str, insert_fields: List[str], update_fields: Optional[List[str]] = None) -> str:
    """Build INSERT ... ON DUPLICATE KEY UPDATE query string.
    
    Args:
        table_name: Table name
        insert_fields: List of fields for INSERT
        update_fields: List of fields for UPDATE (defaults to insert_fields excluding id)
        
    Returns:
        str: UPSERT query string
    """
    if update_fields is None:
        # Exclude id and last_updated from update fields
        update_fields = [f for f in insert_fields if f not in ('id', 'last_updated')]
    
    fields_str = ', '.join(insert_fields)
    placeholders = ', '.join(['%s'] * len(insert_fields))
    update_clause = ', '.join([f"{field} = VALUES({field})" for field in update_fields])
    
    return f"""
    INSERT INTO {table_name} ({fields_str}) VALUES ({placeholders})
    ON DUPLICATE KEY UPDATE {update_clause}
    """


def extract_device_vulnerability_values(vuln: Dict[str, Any], field_mapping: Dict[str, str]) -> Dict[str, Any]:
    """Extract and map values from vulnerability record.
    
    Args:
        vuln: Vulnerability record dictionary
        field_mapping: Field mapping from API keys to DB columns
        
    Returns:
        dict: Mapped values dictionary
    """
    # This is a placeholder - actual value extraction is done in repository
    # This function can be extended to handle value transformation
    return {}


def build_vulnerability_filters(
    filters: Optional[Dict[str, Any]] = None,
    vuln_id: Optional[str] = None,
    table_alias: str = ""
) -> Tuple[str, List[Any]]:
    """Build WHERE clause and parameters for vulnerability queries."""
    where_clauses: List[str] = []
    params: List[Any] = []
    threat_intel_filter: Optional[Any] = None

    def qualify(column: str) -> str:
        return f"{table_alias}.{column}" if table_alias else column

    if vuln_id:
        where_clauses.append(f"{qualify('id')} = %s")
        params.append(vuln_id)

    if filters:
        threat_intel_filter = filters.get('threat_intel')
        for field, value in filters.items():
            if field in ['cvss_min', 'cvss_max', 'epss_min', 'epss_max', 'date_from', 'date_to', 'threat_intel']:
                continue
            if isinstance(value, list) and value:
                placeholders = ','.join(['%s'] * len(value))
                where_clauses.append(f"{qualify(field)} IN ({placeholders})")
                params.extend(value)
            elif value:
                where_clauses.append(f"{qualify(field)} LIKE %s")
                params.append(f"%{value}%")

    if threat_intel_filter:
        threat_values = (
            threat_intel_filter
            if isinstance(threat_intel_filter, list)
            else [threat_intel_filter]
        )
        mapping = {
            'metasploit': 'metasploit_detected',
            'nuclei': 'nuclei_detected',
            'recordfuture': 'recordfuture_detected',
        }
        conditions = []
        for raw_value in threat_values:
            if not raw_value:
                continue
            column = mapping.get(str(raw_value).lower())
            if column:
                conditions.append(f"{qualify(column)} = TRUE")
        if conditions:
            where_clauses.append("(" + " OR ".join(conditions) + ")")

    if filters:
        cvss_min = filters.get('cvss_min')
        cvss_max = filters.get('cvss_max')
        if cvss_min:
            where_clauses.append(f"{qualify('cvss_score')} >= %s")
            params.append(float(cvss_min))
        if cvss_max:
            where_clauses.append(f"{qualify('cvss_score')} <= %s")
            params.append(float(cvss_max))
        epss_min = filters.get('epss_min')
        epss_max = filters.get('epss_max')
        if epss_min:
            where_clauses.append(f"{qualify('cve_epss')} >= %s")
            params.append(float(epss_min))
        if epss_max:
            where_clauses.append(f"{qualify('cve_epss')} <= %s")
            params.append(float(epss_max))
        date_from = filters.get('date_from')
        date_to = filters.get('date_to')
        if date_from:
            where_clauses.append(f"{qualify('last_seen_timestamp')} >= %s")
            params.append(date_from)
        if date_to:
            where_clauses.append(f"{qualify('last_seen_timestamp')} <= %s")
            params.append(date_to)
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    return where_sql, params
