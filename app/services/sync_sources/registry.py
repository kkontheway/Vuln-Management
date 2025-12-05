"""Registry of available sync sources."""
from __future__ import annotations

from typing import Dict, List

from .base import SyncSource
from .defender_vulnerabilities import run as run_defender_vulnerabilities
from .threat_feeds import run as run_threat_feeds
from .recordfuture_flags import run as run_recordfuture_flags


SYNC_SOURCES: List[SyncSource] = [
    SyncSource(
        order=10,
        key="defender_vulnerabilities",
        name="Microsoft Defender Vulnerabilities",
        description="Full ingestion from Microsoft Defender SoftwareVulnerabilitiesByMachine (includes snapshot).",
        default_enabled=True,
        runner=run_defender_vulnerabilities,
    ),
    SyncSource(
        order=20,
        key="threat_feeds",
        name="Rapid7/Nuclei Threat Feeds",
        description="Download Rapid7 Metasploit & ProjectDiscovery Nuclei feeds and refresh detection flags.",
        default_enabled=True,
        runner=run_threat_feeds,
    ),
    SyncSource(
        order=30,
        key="recordfuture_flags",
        name="RecordFuture Flags",
        description="Rebuild RecordFuture detection flags from stored indicators.",
        default_enabled=True,
        runner=run_recordfuture_flags,
    ),
]


def get_sync_sources() -> List[SyncSource]:
    """Return sync sources sorted by order."""
    return sorted(SYNC_SOURCES)


def get_sync_source_map() -> Dict[str, SyncSource]:
    """Return a mapping of key -> SyncSource."""
    return {source.key: source for source in get_sync_sources()}


def get_default_source_keys() -> List[str]:
    """Return keys that should be enabled by default."""
    return [source.key for source in get_sync_sources() if source.default_enabled]
