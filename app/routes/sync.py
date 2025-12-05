"""Sync routes."""
import logging
from flask import Blueprint, jsonify, request
from app.services import sync_service as sync_svc

logger = logging.getLogger(__name__)

bp = Blueprint('sync', __name__, url_prefix='/api')


@bp.route('/sync-status', methods=['GET'])
def get_sync_status():
    """Get sync status and last sync time."""
    try:
        result = sync_svc.get_sync_status()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取同步状态时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/sync-progress', methods=['GET'])
def get_sync_progress():
    """Get current sync progress."""
    try:
        result = sync_svc.get_sync_progress()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取同步进度时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/sync-sources', methods=['GET'])
def list_sync_sources():
    """List available sync sources."""
    try:
        return jsonify({'sources': sync_svc.list_sync_sources()})
    except Exception as e:
        logger.error("列出同步源时出错: %s", e)
        return jsonify({'error': str(e)}), 500


@bp.route('/sync', methods=['POST'])
def trigger_sync():
    """Trigger data sync in background (full sync)."""
    try:
        payload = request.get_json(silent=True) or {}
        data_sources = payload.get('data_sources') or None
        if data_sources is not None and not isinstance(data_sources, list):
            return jsonify({'error': 'data_sources must be a list'}), 400
        result = sync_svc.trigger_sync(data_sources)
        return jsonify(result)
    except Exception as e:
        logger.error(f"触发同步时出错: {e}")
        return jsonify({'error': str(e)}), 500
