"""Threat intelligence routes."""
import logging
from flask import Blueprint, request, jsonify
from app.services import threat_intelligence_service as threat_svc
from app.services import recordfuture_service

logger = logging.getLogger(__name__)

bp = Blueprint('threat_intelligence', __name__, url_prefix='/api/threat-intelligence')


@bp.route('/extract-ip', methods=['POST'])
def extract_ip_addresses():
    """Extract IP addresses from text and generate CSV file."""
    try:
        data = request.get_json(silent=True) or {}
        text = data.get('text', '')
        
        result = threat_svc.extract_ip_addresses(text)
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error extracting IP addresses: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/recordfuture/save', methods=['POST'])
def save_recordfuture_indicators():
    """Persist extracted indicators upon user confirmation."""
    try:
        data = request.get_json(silent=True) or {}
        ips = data.get('ips', [])
        cves = data.get('cves', [])
        source_text = data.get('sourceText', '')

        result = recordfuture_service.save_indicators(ips, cves, source_text)
        return jsonify(result)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error saving RecordFuture indicators: {e}")
        return jsonify({'error': 'Failed to save indicators'}), 500
