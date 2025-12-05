"""Sync source for Rapid7/Nuclei threat feeds."""
import logging

from app.services.threat_source_sync_service import sync_threat_sources
from .base import SyncSourceResult, success_result

logger = logging.getLogger(__name__)


def run() -> SyncSourceResult:
    """Refresh Rapid7/Nuclei metadata tables and detection flags."""
    counts = sync_threat_sources()
    message = f"Threat feeds refreshed (Rapid7={counts.get('rapid', 0)}, Nuclei={counts.get('nuclei', 0)})"
    logger.info(message)
    return success_result(message, details=counts)
