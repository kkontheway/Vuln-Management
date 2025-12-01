"""Snapshot routes."""
import logging
from flask import Blueprint, request, jsonify
from app.services import snapshot_service as snapshot_svc

logger = logging.getLogger(__name__)

bp = Blueprint('snapshots', __name__, url_prefix='/api')


@bp.route('/create-initial-snapshot', methods=['POST'])
def create_initial_snapshot():
    """Create initial vulnerability snapshot."""
    try:
        result = snapshot_svc.create_initial_snapshot()
        return jsonify(result)
    except ImportError as e:
        logger.error(f"导入defender模块失败: {e}")
        return jsonify({'error': f'Import error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"创建初始快照时出错: {e}", exc_info=True)
        return jsonify({'error': f'Error creating snapshot: {str(e)}'}), 500


@bp.route('/snapshots', methods=['GET'])
def get_snapshots():
    """Get list of vulnerability snapshots."""
    try:
        limit = int(request.args.get('limit', 100))
        result = snapshot_svc.get_snapshots(limit=limit)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取快照列表时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/snapshots/<int:snapshot_id>/details', methods=['GET'])
def get_snapshot_details(snapshot_id):
    """Get detailed information for a specific snapshot."""
    try:
        result = snapshot_svc.get_snapshot_details(snapshot_id)
        return jsonify(result)
    except Exception as e:
        if 'not found' in str(e).lower():
            return jsonify({'error': str(e)}), 404
        logger.error(f"获取快照详情时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/cve-history/<cve_id>', methods=['GET'])
def get_cve_history(cve_id):
    """Get historical changes for a specific CVE."""
    try:
        result = snapshot_svc.get_cve_history(cve_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取CVE历史时出错: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/snapshots/trend', methods=['GET'])
def get_snapshots_trend():
    """Get snapshot trend data for line chart."""
    try:
        result = snapshot_svc.get_snapshots_trend()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取快照趋势数据时出错: {e}")
        return jsonify({'error': str(e)}), 500

