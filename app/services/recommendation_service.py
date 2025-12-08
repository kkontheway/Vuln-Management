"""Recommendation report service for business logic."""
import logging
from datetime import datetime, timedelta
from textwrap import dedent
from typing import Dict, List

from database import get_db_connection
from app.constants.database import TABLE_RECOMMENDATION_REPORTS
from app.services import vulnerability_service as vuln_service

logger = logging.getLogger(__name__)


def check_existing_report(cve_id: str):
    """Check if a report exists for the given CVE within the last 7 days.
    
    Args:
        cve_id: CVE ID to check
        
    Returns:
        dict: Report info if exists (id, cve_id, created_at), None otherwise
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Check for reports created within last 7 days
        query = f"""
        SELECT id, cve_id, created_at
        FROM {TABLE_RECOMMENDATION_REPORTS}
        WHERE cve_id = %s 
          AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY created_at DESC
        LIMIT 1
        """
        cursor.execute(query, (cve_id,))
        result = cursor.fetchone()
        
        if result:
            # Format datetime
            if result.get('created_at'):
                if isinstance(result['created_at'], datetime):
                    result['created_at'] = result['created_at'].isoformat()
                elif isinstance(result['created_at'], str):
                    pass  # Already a string
            return result
        return None
    finally:
        cursor.close()
        connection.close()


def build_report_from_data(cve_id: str) -> str:
    """Create a recommendation report purely from stored vulnerability data."""
    result = vuln_service.get_vulnerabilities(filters={'cve_id': cve_id}, page=1, per_page=1000)
    vulnerabilities = result.get('data', [])
    if not vulnerabilities:
        raise ValueError('未找到该CVE的漏洞数据，无法生成报告')

    summary = _summarize_vulnerabilities(vulnerabilities)
    return _render_report_template(cve_id, summary)


def _summarize_vulnerabilities(vulnerabilities: List[Dict]) -> Dict:
    """Aggregate vulnerability data for reporting."""
    seen_devices = set()
    affected_devices: List[Dict] = []
    os_distribution: Dict[str, int] = {}
    dept_distribution: Dict[str, int] = {}

    for vuln in vulnerabilities:
        os_platform = vuln.get('os_platform') or 'Unknown'
        dept = vuln.get('rbac_group_name') or 'Unknown'
        os_distribution[os_platform] = os_distribution.get(os_platform, 0) + 1
        dept_distribution[dept] = dept_distribution.get(dept, 0) + 1

        device_key = vuln.get('device_id') or vuln.get('device_name')
        if device_key and device_key not in seen_devices:
            seen_devices.add(device_key)
            affected_devices.append({
                'device_id': vuln.get('device_id'),
                'device_name': vuln.get('device_name'),
                'os_platform': vuln.get('os_platform'),
                'os_version': vuln.get('os_version'),
                'status': vuln.get('status') or 'Vulnerable',
                'rbac_group_name': vuln.get('rbac_group_name') or 'Unknown'
            })

    first_vuln = vulnerabilities[0]
    evidence = {
        'disk_paths': first_vuln.get('disk_paths') or [],
        'registry_paths': first_vuln.get('registry_paths') or []
    }
    remediation = {
        'security_update_available': first_vuln.get('security_update_available', False),
        'recommended_security_update': first_vuln.get('recommended_security_update') or '',
        'recommended_security_update_id': first_vuln.get('recommended_security_update_id') or '',
        'recommended_security_update_url': first_vuln.get('recommended_security_update_url') or '',
        'recommendation_reference': first_vuln.get('recommendation_reference') or ''
    }

    return {
        'total_devices': len(seen_devices),
        'os_distribution': os_distribution,
        'dept_distribution': dept_distribution,
        'severity': first_vuln.get('vulnerability_severity_level') or first_vuln.get('severity'),
        'cvss_score': first_vuln.get('cvss_score'),
        'software': {
            'vendor': first_vuln.get('software_vendor') or '',
            'name': first_vuln.get('software_name') or '',
            'version': first_vuln.get('software_version') or ''
        },
        'remediation': remediation,
        'evidence': evidence,
        'affected_devices': affected_devices
    }


def _render_report_template(cve_id: str, summary: Dict) -> str:
    """Render a plain-text report from aggregated data."""
    os_top = _format_top_entries(summary['os_distribution'])
    dept_top = _format_top_entries(summary['dept_distribution'])
    cvss_text = f"{summary['cvss_score']:.1f}" if summary['cvss_score'] is not None else "N/A"

    remediation = summary['remediation']
    remediation_lines = []
    if remediation['recommended_security_update']:
        remediation_lines.append(f"- Recommended Update: {remediation['recommended_security_update']}")
    if remediation['recommended_security_update_id']:
        remediation_lines.append(f"- Update ID: {remediation['recommended_security_update_id']}")
    if remediation['recommended_security_update_url']:
        remediation_lines.append(f"- Vendor URL: {remediation['recommended_security_update_url']}")
    if remediation['recommendation_reference']:
        remediation_lines.append(f"- Reference: {remediation['recommendation_reference']}")
    if not remediation_lines:
        remediation_lines.append("- No vendor remediation guidance provided.")

    device_lines = []
    for idx, device in enumerate(summary['affected_devices'][:5], start=1):
        name = device.get('device_name') or device.get('device_id') or 'Unknown Device'
        platform = device.get('os_platform') or 'Unknown OS'
        version = device.get('os_version') or ''
        status = device.get('status') or 'Vulnerable'
        dept = device.get('rbac_group_name') or 'Unknown'
        device_lines.append(
            f"  {idx}. {name} | {platform} {version} | {status} | Department: {dept}"
        )
    if not device_lines:
        device_lines.append("  (No device details available.)")

    evidence_lines = []
    for path in summary['evidence']['disk_paths'][:3]:
        evidence_lines.append(f"  - File Path: {path}")
    for path in summary['evidence']['registry_paths'][:3]:
        evidence_lines.append(f"  - Registry Path: {path}")
    if not evidence_lines:
        evidence_lines.append("  - No specific evidence paths recorded.")

    device_block = "\n".join(device_lines)
    evidence_block = "\n".join(evidence_lines)
    remediation_block = "\n".join(remediation_lines)

    template = dedent(f"""
        Vulnerability Recommendation Report - {cve_id}

        Impact Summary
        --------------
        - Severity: {summary['severity'] or 'Unknown'}
        - CVSS Score: {cvss_text}
        - Total Affected Devices: {summary['total_devices']}
        - Primary Operating Systems: {os_top}
        - Top Impacted Departments: {dept_top}

        Vulnerable Software
        -------------------
        - Vendor: {summary['software']['vendor'] or 'N/A'}
        - Product: {summary['software']['name'] or 'N/A'}
        - Version: {summary['software']['version'] or 'N/A'}

        Sample Affected Devices
        -----------------------
        {device_block}

        Evidence Highlights
        -------------------
        {evidence_block}

        Recommended Actions
        -------------------
        {remediation_block}
    """).strip()

    return template


def _format_top_entries(distribution: Dict[str, int], limit: int = 3) -> str:
    """Format top distribution entries as text."""
    if not distribution:
        return 'N/A'
    sorted_items = sorted(distribution.items(), key=lambda item: item[1], reverse=True)[:limit]
    return ', '.join(f"{name} ({count})" for name, count in sorted_items)


def save_report(cve_id: str, report_content: str, ai_prompt: str = ''):
    """Save recommendation report to database.
    
    Args:
        cve_id: CVE ID
        report_content: Generated report content
        ai_prompt: AI prompt used (optional, can be empty)
        
    Returns:
        int: Report ID
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    
    try:
        cursor = connection.cursor()
        
        query = f"""
        INSERT INTO {TABLE_RECOMMENDATION_REPORTS} (cve_id, report_content, ai_prompt)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (cve_id, report_content, ai_prompt))
        connection.commit()
        
        report_id = cursor.lastrowid
        logger.info(f"Saved report for CVE {cve_id} with ID {report_id}")
        
        return report_id
    except Exception as e:
        logger.error(f"Error saving report: {e}", exc_info=True)
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_report_history(limit: int = 50, offset: int = 0):
    """Get report history.
    
    Args:
        limit: Maximum number of reports to return
        offset: Offset for pagination
        
    Returns:
        list: List of reports
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = f"""
        SELECT id, cve_id, report_content, ai_prompt, created_at, updated_at
        FROM {TABLE_RECOMMENDATION_REPORTS}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, offset))
        results = cursor.fetchall()
        
        # Format datetime fields
        for row in results:
            if row.get('created_at') and isinstance(row['created_at'], datetime):
                row['created_at'] = row['created_at'].isoformat()
            if row.get('updated_at') and isinstance(row['updated_at'], datetime):
                row['updated_at'] = row['updated_at'].isoformat()
        
        return results
    finally:
        cursor.close()
        connection.close()


def get_report_by_id(report_id: int):
    """Get a specific report by ID.
    
    Args:
        report_id: Report ID
        
    Returns:
        dict: Report data or None if not found
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = f"""
        SELECT id, cve_id, report_content, ai_prompt, created_at, updated_at
        FROM {TABLE_RECOMMENDATION_REPORTS}
        WHERE id = %s
        """
        cursor.execute(query, (report_id,))
        result = cursor.fetchone()
        
        if result:
            # Format datetime fields
            if result.get('created_at') and isinstance(result['created_at'], datetime):
                result['created_at'] = result['created_at'].isoformat()
            if result.get('updated_at') and isinstance(result['updated_at'], datetime):
                result['updated_at'] = result['updated_at'].isoformat()
        
        return result
    finally:
        cursor.close()
        connection.close()


def get_report_by_cve_id(cve_id: str):
    """Get the latest report for a CVE ID.
    
    Args:
        cve_id: CVE ID
        
    Returns:
        dict: Report data or None if not found
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = f"""
        SELECT id, cve_id, report_content, ai_prompt, created_at, updated_at
        FROM {TABLE_RECOMMENDATION_REPORTS}
        WHERE cve_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """
        cursor.execute(query, (cve_id,))
        result = cursor.fetchone()
        
        if result:
            # Format datetime fields
            if result.get('created_at') and isinstance(result['created_at'], datetime):
                result['created_at'] = result['created_at'].isoformat()
            if result.get('updated_at') and isinstance(result['updated_at'], datetime):
                result['updated_at'] = result['updated_at'].isoformat()
        
        return result
    finally:
        cursor.close()
        connection.close()
