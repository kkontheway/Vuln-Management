"""Sync source runner for RecordFuture detection flags."""
import logging

from app.services.recordfuture_service import rebuild_detection_flags
from .base import SyncSourceResult, success_result

logger = logging.getLogger(__name__)


def run() -> SyncSourceResult:
    """Rebuild RecordFuture detection flags based on stored indicators."""
    stats = rebuild_detection_flags()
    message = (
        f"RecordFuture flags rebuilt (cleared={stats.get('cleared', 0)}, "
        f"reapplied={stats.get('reapplied', 0)})"
    )
    logger.info(message)
    return success_result(message, details=stats)
