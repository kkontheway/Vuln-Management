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
    vulnerability_data = vuln_service.get_cve_vulnerability_report_data(cve_id, device_limit=None)
    if not vulnerability_data:
        raise ValueError('未找到该CVE的漏洞数据，无法生成报告')

    summary = _build_report_summary_from_payload(vulnerability_data)
    return _render_report_template(cve_id, summary)


def _build_report_summary_from_payload(vulnerability_data: Dict) -> Dict:
    """Convert API payload into template-friendly summary."""
    summary = vulnerability_data.get('summary') or {}
    return {
        'total_devices': summary.get('total_affected_hosts', 0),
        'os_distribution': summary.get('os_distribution') or {},
        'dept_distribution': summary.get('department_distribution') or {},
        'severity': summary.get('severity'),
        'cvss_score': summary.get('cvss_score'),
        'software': vulnerability_data.get('software') or {},
        'remediation': vulnerability_data.get('remediation') or {},
        'evidence': vulnerability_data.get('evidence') or {'disk_paths': [], 'registry_paths': []},
        'affected_devices': vulnerability_data.get('affected_devices') or [],
        'description': vulnerability_data.get('description')
    }


def _render_report_template(cve_id: str, summary: Dict) -> str:
    """Render a plain-text report from aggregated data."""
    os_top = _format_top_entries(summary['os_distribution'])
    dept_top = _format_top_entries(summary['dept_distribution'])
    cvss_text = f"{summary['cvss_score']:.1f}" if summary['cvss_score'] is not None else "N/A"
    description_block = summary.get('description') or 'No description available.'
    remediation = summary.get('remediation') or {}
    software_info = summary.get('software') or {}
    evidence = summary.get('evidence') or {'disk_paths': [], 'registry_paths': []}
    affected_devices = summary.get('affected_devices') or []

    remediation_lines = []
    if remediation.get('recommended_security_update'):
        remediation_lines.append(f"- Recommended Update: {remediation['recommended_security_update']}")
    if remediation.get('recommended_security_update_id'):
        remediation_lines.append(f"- Update ID: {remediation['recommended_security_update_id']}")
    if remediation.get('recommended_security_update_url'):
        remediation_lines.append(f"- Vendor URL: {remediation['recommended_security_update_url']}")
    if remediation.get('recommendation_reference'):
        remediation_lines.append(f"- Reference: {remediation['recommendation_reference']}")
    if not remediation_lines:
        remediation_lines.append("- No vendor remediation guidance provided.")

    device_lines = []
    for idx, device in enumerate(affected_devices[:5], start=1):
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
    for path in evidence.get('disk_paths', [])[:3]:
        evidence_lines.append(f"  - File Path: {path}")
    for path in evidence.get('registry_paths', [])[:3]:
        evidence_lines.append(f"  - Registry Path: {path}")
    if not evidence_lines:
        evidence_lines.append("  - No specific evidence paths recorded.")

    device_block = "\n".join(device_lines)
    evidence_block = "\n".join(evidence_lines)
    remediation_block = "\n".join(remediation_lines)

    template = dedent(f"""
        Vulnerability Recommendation Report - {cve_id}

        Vulnerability Description
        ------------------------
        {description_block}

        Impact Summary
        --------------
        - Severity: {summary['severity'] or 'Unknown'}
        - CVSS Score: {cvss_text}
        - Total Affected Devices: {summary['total_devices']}
        - Primary Operating Systems: {os_top}
        - Top Impacted Departments: {dept_top}

        Vulnerable Software
        -------------------
        - Vendor: {software_info.get('vendor') or 'N/A'}
        - Product: {software_info.get('name') or 'N/A'}
        - Version: {software_info.get('version') or 'N/A'}

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
