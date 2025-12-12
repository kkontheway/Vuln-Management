"""FastAPI auth utilities with Entra ID extension hooks."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from fastapi import Depends, HTTPException, Request, status

from config import config

logger = logging.getLogger(__name__)


class AuthProvider(Protocol):
    """Authentication provider interface."""

    def validate_request(self, request: Request) -> None:
        """Validate incoming request or raise HTTPException."""
        raise NotImplementedError


@dataclass
class NullAuthProvider:
    """Default auth provider that allows all requests."""

    name: str = "none"

    def validate_request(self, request: Request) -> None:  # noqa: ARG002
        return None


class MicrosoftEntraAuthProvider:
    """Placeholder for future Entra ID integration."""

    def __init__(self) -> None:
        self.tenant_id = config.ENTRA_TENANT_ID
        self.client_id = config.ENTRA_CLIENT_ID
        self.authority = config.ENTRA_AUTHORITY

    def validate_request(self, request: Request) -> None:
        auth_header = request.headers.get("Authorization") or ""
        if not auth_header.startswith("Bearer "):
            logger.debug("Missing bearer token for Entra provider")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
        logger.debug("Received Entra token placeholder validation")


def get_auth_provider() -> AuthProvider:
    provider_name = config.AUTH_PROVIDER.lower()
    if provider_name == "entra":
        return MicrosoftEntraAuthProvider()
    return NullAuthProvider()


def auth_guard(request: Request, provider: AuthProvider = Depends(get_auth_provider)) -> None:
    provider.validate_request(request)
