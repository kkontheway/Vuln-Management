"""ServiceNow integration routes."""
import logging
from flask import Blueprint, request, jsonify

from app.services.integration_settings_service import (
    PROVIDER_SERVICENOW,
    integration_settings_service,
)
from servicenow_client import ServiceNowClient

logger = logging.getLogger(__name__)

bp = Blueprint('servicenow', __name__, url_prefix='/api/servicenow')


def _resolve_servicenow_context():
    """Load runtime ServiceNow client and metadata from settings service."""
    runtime = integration_settings_service.get_runtime_credentials(PROVIDER_SERVICENOW)
    if not runtime:
        return None, None
    metadata = runtime.get('metadata') or {}
    secrets = runtime.get('secrets') or {}
    try:
        client = ServiceNowClient(
            instance_url=metadata.get('instance_url', ''),
            username=metadata.get('username', ''),
            password=secrets.get('password', ''),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to init ServiceNow client: {exc}", exc_info=True)
        return None, metadata
    return client, metadata


@bp.route('/tickets', methods=['GET', 'POST'])
def servicenow_tickets():
    """ServiceNow tickets endpoint - GET list or POST create."""
    try:
        client, metadata = _resolve_servicenow_context()
        if not client:
            return jsonify({'error': 'ServiceNow is not configured. Please configure it in settings.'}), 400
        default_table = metadata.get('default_table', 'incident') if metadata else 'incident'

        if request.method == 'GET':
            # Get tickets list
            table = request.args.get('table', default_table)
            query = request.args.get('query')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            
            tickets = client.get_tickets(
                table=table,
                sysparm_query=query,
                sysparm_limit=limit,
                sysparm_offset=offset
            )
            
            return jsonify({
                'tickets': tickets,
                'total': len(tickets)
            })
        
        elif request.method == 'POST':
            # Create ticket
            data = request.json
            table = data.get('table', default_table)
            
            # Extract ticket fields
            ticket_data = {
                'short_description': data.get('short_description', ''),
                'description': data.get('description', ''),
                'category': data.get('category', ''),
                'priority': data.get('priority', '3'),
                'urgency': data.get('urgency', '3'),
                'impact': data.get('impact', '3'),
            }
            
            # Remove empty fields
            ticket_data = {k: v for k, v in ticket_data.items() if v}
            
            ticket = client.create_ticket(table=table, **ticket_data)
            
            return jsonify({
                'ticket': ticket,
                'ticket_number': ticket.get('number', ticket.get('sys_id')),
                'sys_id': ticket.get('sys_id')
            }), 201
            
    except Exception as e:
        logger.error(f"ServiceNow tickets error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/tickets/<ticket_id>', methods=['GET'])
def servicenow_ticket_detail(ticket_id):
    """Get ServiceNow ticket detail."""
    try:
        client, metadata = _resolve_servicenow_context()
        if not client:
            return jsonify({'error': 'ServiceNow is not configured'}), 400
        default_table = metadata.get('default_table', 'incident') if metadata else 'incident'
        table = request.args.get('table', default_table)
        ticket = client.get_ticket(table=table, sys_id=ticket_id)
        
        return jsonify({'ticket': ticket})
        
    except Exception as e:
        logger.error(f"ServiceNow ticket detail error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/tickets/<ticket_id>/notes', methods=['GET', 'POST'])
def servicenow_ticket_notes(ticket_id):
    """Get or add notes for a ServiceNow ticket."""
    try:
        client, metadata = _resolve_servicenow_context()
        if not client:
            return jsonify({'error': 'ServiceNow is not configured'}), 400
        default_table = metadata.get('default_table', 'incident') if metadata else 'incident'
        table = request.args.get('table', default_table) if request.method == 'GET' else request.json.get('table', default_table)
        
        if request.method == 'GET':
            # Get notes
            notes = client.get_ticket_notes(table=table, sys_id=ticket_id)
            return jsonify({
                'notes': notes,
                'total': len(notes)
            })
        
        elif request.method == 'POST':
            # Add note
            data = request.json
            note_text = data.get('note', '')
            
            if not note_text:
                return jsonify({'error': 'Note text is required'}), 400
            
            note = client.add_ticket_note(table=table, sys_id=ticket_id, note_text=note_text)
            return jsonify({
                'note': note,
                'message': 'Note added successfully'
            }), 201
            
    except Exception as e:
        logger.error(f"ServiceNow notes error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/test-connection', methods=['POST'])
def servicenow_test_connection():
    """Test ServiceNow connection."""
    try:
        data = request.json or {}
        metadata = {
            'instance_url': data.get('instance_url', '').rstrip('/'),
            'username': data.get('username'),
        }
        secrets = {'password': data.get('password')}
        result = integration_settings_service.test_provider(PROVIDER_SERVICENOW, metadata, secrets)
        status = result.pop('status_code', 200)
        return jsonify(result), status
    except Exception as e:
        logger.error(f"ServiceNow connection test error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/health', methods=['GET'])
def servicenow_health_check():
    """Return basic health information for the ServiceNow integration."""
    try:
        client, _ = _resolve_servicenow_context()
        if not client:
            return jsonify({'status': 'unconfigured', 'healthy': False}), 400
        is_healthy = client.test_connection()
        status_payload = integration_settings_service.get_setting_summary(PROVIDER_SERVICENOW).get('status', {})
        return jsonify({
            'healthy': is_healthy,
            'status': status_payload.get('last_test_status'),
            'last_tested_at': status_payload.get('last_tested_at'),
            'message': status_payload.get('last_test_message'),
        }), (200 if is_healthy else 503)
    except Exception as e:
        logger.error(f"ServiceNow health check error: {e}", exc_info=True)
        return jsonify({'healthy': False, 'error': str(e)}), 500
