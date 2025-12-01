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


@bp.route('/sync', methods=['POST'])
def trigger_sync():
    """Trigger data sync in background (full sync)."""
    try:
        # No data source selection needed - always performs full sync
        result = sync_svc.trigger_sync()
        return jsonify(result)
    except Exception as e:
        logger.error(f"触发同步时出错: {e}")
        return jsonify({'error': str(e)}), 500

