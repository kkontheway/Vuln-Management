"""Secret manager for encrypting and decrypting integration credentials."""
import base64
import json
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

from config import config


class SecretManager:
    """Handles symmetric encryption for integration secrets."""

    def __init__(self, key: Optional[str] = None) -> None:
        raw_key = key or config.INTEGRATIONS_SECRET_KEY
        if not raw_key:
            raise ValueError("INTEGRATIONS_SECRET_KEY is not configured.")
        self._key = self._normalize_key(raw_key)
        self._fernet = Fernet(self._key)

    @staticmethod
    def _normalize_key(raw_key: str) -> bytes:
        """Validate and normalize the provided key to Fernet format."""
        key_bytes = raw_key.strip().encode()
        try:
            decoded = base64.urlsafe_b64decode(key_bytes)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("INTEGRATIONS_SECRET_KEY must be urlsafe base64 encoded.") from exc
        if len(decoded) != 32:
            raise ValueError("INTEGRATIONS_SECRET_KEY must decode to 32 bytes.")
        return key_bytes

    def encrypt_dict(self, payload: Dict[str, Any]) -> bytes:
        """Encrypt a dictionary payload."""
        if not payload:
            raise ValueError("Secret payload cannot be empty.")
        serialized = json.dumps(payload).encode()
        return self._fernet.encrypt(serialized)

    def decrypt_dict(self, ciphertext: bytes) -> Dict[str, Any]:
        """Decrypt ciphertext back into a dictionary."""
        if not ciphertext:
            raise ValueError("Ciphertext payload is required.")
        try:
            decrypted = self._fernet.decrypt(ciphertext)
        except InvalidToken as exc:
            raise ValueError("Failed to decrypt stored secret payload.") from exc
        return json.loads(decrypted.decode())
