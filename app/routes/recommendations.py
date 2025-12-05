"""Recommendation report routes."""
import logging
from flask import Blueprint, jsonify, request

from app.services import recommendation_service as rec_service
from app.services import vulnerability_service as vuln_service

logger = logging.getLogger(__name__)

bp = Blueprint('recommendations', __name__, url_prefix='/api/recommendations')


@bp.route('/check/<cve_id>', methods=['GET'])
def check_existing_report(cve_id: str):
    """Check if a report exists for the given CVE within the last 7 days."""
    try:
        result = rec_service.check_existing_report(cve_id)
        if result:
            return jsonify({
                'exists': True,
                'report': result
            })
        else:
            return jsonify({
                'exists': False
            })
    except Exception as e:
        logger.error(f"Error checking existing report: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate a recommendation report for a CVE using existing vulnerability data."""
    try:
        data = request.json
        cve_id = data.get('cve_id', '').strip()
        force_generate = data.get('force', False)

        if not cve_id:
            return jsonify({'error': 'CVE ID is required'}), 400

        if not force_generate:
            existing = rec_service.check_existing_report(cve_id)
            if existing:
                return jsonify({
                    'error': 'Report already exists',
                    'exists': True,
                    'report': existing
                }), 409

        report_content = rec_service.build_report_from_data(cve_id)
        report_id = rec_service.save_report(cve_id, report_content, '')

        return jsonify({
            'success': True,
            'report_id': report_id,
            'cve_id': cve_id,
            'message': 'Report generated successfully'
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/history', methods=['GET'])
def get_report_history():
    """Get report history."""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        reports = rec_service.get_report_history(limit=limit, offset=offset)
        
        return jsonify({
            'reports': reports,
            'total': len(reports)
        })
    except Exception as e:
        logger.error(f"Error getting report history: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:report_id>', methods=['GET'])
def get_report(report_id: int):
    """Get a specific report by ID."""
    try:
        report = rec_service.get_report_by_id(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify({'report': report})
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/cve/<cve_id>', methods=['GET'])
def get_report_by_cve(cve_id: str):
    """Get the latest report for a CVE ID."""
    try:
        report = rec_service.get_report_by_cve_id(cve_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify({'report': report})
    except Exception as e:
        logger.error(f"Error getting report by CVE: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:report_id>/vulnerabilities', methods=['GET'])
def get_cve_vulnerabilities_by_report(report_id: int):
    """Get vulnerability data for a CVE ID from a report."""
    try:
        # Get CVE from report first
        report = rec_service.get_report_by_id(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        cve_id = report.get('cve_id')
        
        if not cve_id:
            return jsonify({'error': 'CVE ID not found in report'}), 400
        
        # Get all vulnerabilities for this CVE
        filters = {'cve_id': cve_id}
        result = vuln_service.get_vulnerabilities(filters=filters, page=1, per_page=1000)
        
        vulnerabilities = result.get('data', [])
        
        # Calculate statistics
        total_devices = len(set(v.get('device_id') for v in vulnerabilities if v.get('device_id')))
        
        # OS distribution
        os_distribution = {}
        for v in vulnerabilities:
            os_platform = v.get('os_platform', 'Unknown')
            if os_platform:
                os_distribution[os_platform] = os_distribution.get(os_platform, 0) + 1
        
        # Department distribution
        dept_distribution = {}
        for v in vulnerabilities:
            dept = v.get('rbac_group_name', 'Unknown')
            if dept:
                dept_distribution[dept] = dept_distribution.get(dept, 0) + 1
        
        # Get unique software info (should be same for all)
        software_info = {}
        if vulnerabilities:
            first_vuln = vulnerabilities[0]
            software_info = {
                'vendor': first_vuln.get('software_vendor', ''),
                'name': first_vuln.get('software_name', ''),
                'version': first_vuln.get('software_version', '')
            }
        
        # Get CVSS score and severity (should be same for all)
        cvss_score = None
        severity = None
        if vulnerabilities:
            first_vuln = vulnerabilities[0]
            cvss_score = first_vuln.get('cvss_score')
            severity = first_vuln.get('vulnerability_severity_level') or first_vuln.get('severity')
        
        # Get affected devices list (unique devices)
        affected_devices = []
        seen_devices = set()
        for v in vulnerabilities:
            device_id = v.get('device_id')
            if device_id and device_id not in seen_devices:
                seen_devices.add(device_id)
                affected_devices.append({
                    'device_id': device_id,
                    'device_name': v.get('device_name', ''),
                    'os_platform': v.get('os_platform', ''),
                    'os_version': v.get('os_version', ''),
                    'rbac_group_name': v.get('rbac_group_name', ''),
                    'status': v.get('status', 'Vulnerable')
                })
        
        # Get evidence paths (from first vulnerability as sample)
        evidence = {
            'disk_paths': [],
            'registry_paths': []
        }
        if vulnerabilities:
            first_vuln = vulnerabilities[0]
            disk_paths = first_vuln.get('disk_paths', [])
            registry_paths = first_vuln.get('registry_paths', [])
            
            if isinstance(disk_paths, list):
                evidence['disk_paths'] = disk_paths
            elif isinstance(disk_paths, str):
                try:
                    import json
                    evidence['disk_paths'] = json.loads(disk_paths)
                except:
                    evidence['disk_paths'] = [disk_paths] if disk_paths else []
            
            if isinstance(registry_paths, list):
                evidence['registry_paths'] = registry_paths
            elif isinstance(registry_paths, str):
                try:
                    import json
                    evidence['registry_paths'] = json.loads(registry_paths)
                except:
                    evidence['registry_paths'] = [registry_paths] if registry_paths else []
        
        # Get remediation info
        remediation = {}
        if vulnerabilities:
            first_vuln = vulnerabilities[0]
            remediation = {
                'security_update_available': first_vuln.get('security_update_available', False),
                'recommended_security_update': first_vuln.get('recommended_security_update', ''),
                'recommended_security_update_id': first_vuln.get('recommended_security_update_id', ''),
                'recommended_security_update_url': first_vuln.get('recommended_security_update_url', ''),
                'recommendation_reference': first_vuln.get('recommendation_reference', '')
            }
        
        return _build_vulnerability_response(
            cve_id, vulnerabilities, total_devices, os_distribution, 
            dept_distribution, cvss_score, severity, software_info, 
            affected_devices, evidence, remediation
        )
        
    except Exception as e:
        logger.error(f"Error getting CVE vulnerabilities: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def _build_vulnerability_response(cve_id, vulnerabilities, total_devices, os_distribution, 
                                  dept_distribution, cvss_score, severity, software_info, 
                                  affected_devices, evidence, remediation):
    """Helper function to build vulnerability response."""
    return jsonify({
        'cve_id': cve_id,
        'summary': {
            'total_affected_hosts': total_devices,
            'os_distribution': os_distribution,
            'department_distribution': dept_distribution,
            'cvss_score': cvss_score,
            'severity': severity
        },
        'software': software_info,
        'affected_devices': affected_devices[:50],  # Limit to top 50 for display
        'evidence': evidence,
        'remediation': remediation,
        'total_vulnerabilities': len(vulnerabilities)
    })


@bp.route('/cve/<cve_id>/vulnerabilities', methods=['GET'])
def get_cve_vulnerabilities_by_cve(cve_id: str):
    """Get vulnerability data for a CVE ID directly."""
    try:
        if not cve_id:
            return jsonify({'error': 'CVE ID is required'}), 400
        
        # Get all vulnerabilities for this CVE
        filters = {'cve_id': cve_id}
        result = vuln_service.get_vulnerabilities(filters=filters, page=1, per_page=1000)
        
        vulnerabilities = result.get('data', [])
        
        # Calculate statistics
        total_devices = len(set(v.get('device_id') for v in vulnerabilities if v.get('device_id')))
        
        # OS distribution
        os_distribution = {}
        for v in vulnerabilities:
            os_platform = v.get('os_platform', 'Unknown')
            if os_platform:
                os_distribution[os_platform] = os_distribution.get(os_platform, 0) + 1
        
        # Department distribution
        dept_distribution = {}
        for v in vulnerabilities:
            dept = v.get('rbac_group_name', 'Unknown')
            if dept:
                dept_distribution[dept] = dept_distribution.get(dept, 0) + 1
        
        # Get unique software info (should be same for all)
        software_info = {}
        if vulnerabilities:
            first_vuln = vulnerabilities[0]
            software_info = {
                'vendor': first_vuln.get('software_vendor', ''),
                'name': first_vuln.get('software_name', ''),
                'version': first_vuln.get('software_version', '')
            }
        
        # Get CVSS score and severity (should be same for all)
        cvss_score = None
        severity = None
        if vulnerabilities:
            first_vuln = vulnerabilities[0]
            cvss_score = first_vuln.get('cvss_score')
            severity = first_vuln.get('vulnerability_severity_level') or first_vuln.get('severity')
        
        # Get affected devices list (unique devices)
        affected_devices = []
        seen_devices = set()
        for v in vulnerabilities:
            device_id = v.get('device_id')
            if device_id and device_id not in seen_devices:
                seen_devices.add(device_id)
                affected_devices.append({
                    'device_id': device_id,
                    'device_name': v.get('device_name', ''),
                    'os_platform': v.get('os_platform', ''),
                    'os_version': v.get('os_version', ''),
                    'rbac_group_name': v.get('rbac_group_name', ''),
                    'status': v.get('status', 'Vulnerable')
                })
        
        # Get evidence paths (from first vulnerability as sample)
        evidence = {
            'disk_paths': [],
            'registry_paths': []
        }
        if vulnerabilities:
            first_vuln = vulnerabilities[0]
            disk_paths = first_vuln.get('disk_paths', [])
            registry_paths = first_vuln.get('registry_paths', [])
            
            if isinstance(disk_paths, list):
                evidence['disk_paths'] = disk_paths
            elif isinstance(disk_paths, str):
                try:
                    import json
                    evidence['disk_paths'] = json.loads(disk_paths)
                except:
                    evidence['disk_paths'] = [disk_paths] if disk_paths else []
            
            if isinstance(registry_paths, list):
                evidence['registry_paths'] = registry_paths
            elif isinstance(registry_paths, str):
                try:
                    import json
                    evidence['registry_paths'] = json.loads(registry_paths)
                except:
                    evidence['registry_paths'] = [registry_paths] if registry_paths else []
        
        # Get remediation info
        remediation = {}
        if vulnerabilities:
            first_vuln = vulnerabilities[0]
            remediation = {
                'security_update_available': first_vuln.get('security_update_available', False),
                'recommended_security_update': first_vuln.get('recommended_security_update', ''),
                'recommended_security_update_id': first_vuln.get('recommended_security_update_id', ''),
                'recommended_security_update_url': first_vuln.get('recommended_security_update_url', ''),
                'recommendation_reference': first_vuln.get('recommendation_reference', '')
            }
        
        return _build_vulnerability_response(
            cve_id, vulnerabilities, total_devices, os_distribution, 
            dept_distribution, cvss_score, severity, software_info, 
            affected_devices, evidence, remediation
        )
        
    except Exception as e:
        logger.error(f"Error getting CVE vulnerabilities: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
