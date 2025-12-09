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
        report_data = vuln_service.get_cve_vulnerability_report_data(cve_id, device_limit=50)
        if not report_data:
            return jsonify({'error': 'No vulnerability data found'}), 404

        return jsonify(report_data)
    except Exception as e:
        logger.error(f"Error getting CVE vulnerabilities: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/cve/<cve_id>/vulnerabilities', methods=['GET'])
def get_cve_vulnerabilities_by_cve(cve_id: str):
    """Get vulnerability data for a CVE ID directly."""
    try:
        if not cve_id:
            return jsonify({'error': 'CVE ID is required'}), 400
        report_data = vuln_service.get_cve_vulnerability_report_data(cve_id, device_limit=50)
        if not report_data:
            return jsonify({'error': 'Vulnerability data not found'}), 404
        return jsonify(report_data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting CVE vulnerabilities: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
