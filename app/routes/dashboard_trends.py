"""Dashboard trend API routes."""
from flask import Blueprint, jsonify, request

from app.services import trend_service

bp = Blueprint('dashboard_trends', __name__, url_prefix='/api')


@bp.route('/dashboard/trends', methods=['GET'])
def get_dashboard_trends():
    """Return materialized dashboard trend data."""
    period_param = request.args.get('period')
    periods = None
    if period_param:
        periods = [value.strip().lower() for value in period_param.split(',') if value.strip()]

    try:
        data = trend_service.fetch_trend_payload(periods)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive handler
        return jsonify({'error': str(exc)}), 500

    return jsonify({'periods': data})
