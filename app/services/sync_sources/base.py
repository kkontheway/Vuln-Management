"""Base definitions for modular sync sources."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Any


@dataclass
class SyncSourceResult:
    """Standard result returned by each sync source runner."""
    success: bool = True
    message: str = ""
    details: Optional[Dict[str, Any]] = None


SyncRunner = Callable[[], SyncSourceResult]


@dataclass(order=True)
class SyncSource:
    """Declarative configuration for an individual sync source."""
    order: int
    key: str = field(compare=False)
    name: str = field(compare=False)
    description: str = field(compare=False)
    default_enabled: bool = field(default=True, compare=False)
    runner: SyncRunner = field(default=lambda: SyncSourceResult(), compare=False)


def success_result(message: str = "", details: Optional[Dict[str, Any]] = None) -> SyncSourceResult:
    """Helper to create a success response."""
    return SyncSourceResult(success=True, message=message, details=details)
