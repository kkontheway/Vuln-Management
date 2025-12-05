"""Vulnerability management routes."""
import logging
from flask import Blueprint, request, jsonify
from app.services import vulnerability_service as vuln_service

logger = logging.getLogger(__name__)

bp = Blueprint('vulnerabilities', __name__, url_prefix='/api')


@bp.route('/vulnerabilities', methods=['GET'])
def get_vulnerabilities():
    """Get vulnerability list with pagination and filters."""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        vuln_id = request.args.get('id')
        
        # Get filter conditions
        filters = {}
        filter_fields = [
            'cve_id', 'device_name', 'os_platform', 'os_version',
            'software_vendor', 'software_name', 'vulnerability_severity_level',
            'status', 'exploitability_level', 'rbac_group_name'
        ]
        
        for field in filter_fields:
            # Handle array parameters (for multi-select like software_vendor)
            if field == 'software_vendor':
                values = request.args.getlist(field)
                if values:
                    filters[field] = values  # Store as list for IN query
            else:
                value = request.args.get(field)
                if value:
                    filters[field] = value
        
        threat_intel_values = request.args.getlist('threat_intel')
        if threat_intel_values:
            filters['threat_intel'] = threat_intel_values

        # Add CVSS and date filters
        cvss_min = request.args.get('cvss_min')
        cvss_max = request.args.get('cvss_max')
        if cvss_min:
            filters['cvss_min'] = cvss_min
        if cvss_max:
            filters['cvss_max'] = cvss_max
        
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        result = vuln_service.get_vulnerabilities(
            filters=filters if filters else None,
            page=page,
            per_page=per_page,
            vuln_id=vuln_id if vuln_id else None
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取漏洞数据时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get vulnerability statistics for charts."""
    try:
        result = vuln_service.get_statistics()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取统计信息时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/unique-cve-count', methods=['GET'])
def get_unique_cve_count():
    """Get count of unique CVE IDs."""
    try:
        result = vuln_service.get_unique_cve_count()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取去重CVE数量时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/severity-counts', methods=['GET'])
def get_severity_counts():
    """Get vulnerability counts by severity level."""
    try:
        result = vuln_service.get_severity_counts()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取严重程度统计时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/filter-options', methods=['GET'])
def get_filter_options():
    """Get filter option lists for dropdowns."""
    try:
        result = vuln_service.get_filter_options()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取过滤选项时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/fixed-vulnerabilities', methods=['GET'])
def get_fixed_vulnerabilities():
    """Get list of fixed vulnerabilities (exist in snapshot but not in current vulnerabilities)."""
    try:
        limit = int(request.args.get('limit', 50))
        result = vuln_service.get_fixed_vulnerabilities(limit=limit)
        return jsonify({'data': result})
    except Exception as e:
        logger.error(f"获取已修复漏洞列表时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/vulnerability-catalog/<cve_id>', methods=['GET'])
def get_vulnerability_catalog_entry(cve_id: str):
    """Get catalog metadata for a specific CVE."""
    try:
        result = vuln_service.get_catalog_details(cve_id)
        if not result:
            return jsonify({'error': 'Catalog entry not found'}), 404
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching catalog entry for {cve_id}: {e}")
        return jsonify({'error': str(e)}), 500
