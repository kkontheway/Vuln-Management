"""Service logic for integration settings management."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI

from database import get_db_connection
from servicenow_client import ServiceNowClient
from app.repositories import integration_settings_repository as repo
from app.services.secret_manager import SecretManager

logger = logging.getLogger(__name__)

PROVIDER_SERVICENOW = "servicenow"
PROVIDER_AI = "ai"
SUPPORTED_PROVIDERS = {PROVIDER_SERVICENOW, PROVIDER_AI}


class IntegrationSettingsService:
    """Provides CRUD, encryption, and runtime helpers for integrations."""

    def __init__(self) -> None:
        self._secret_manager: Optional[SecretManager] = None

    @property
    def secret_manager(self) -> SecretManager:
        if not self._secret_manager:
            self._secret_manager = SecretManager()
        return self._secret_manager

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_setting_summary(self, provider: str) -> Dict[str, Any]:
        provider = self._normalize_provider(provider)
        connection = get_db_connection()
        if not connection:
            raise RuntimeError("数据库连接失败")
        try:
            setting = repo.get_setting_by_provider(connection, provider)
            metadata = self._default_metadata(provider)
            secret_info: Dict[str, Dict[str, Any]] = {}
            status = {
                "last_test_status": None,
                "last_tested_at": None,
                "last_test_message": None,
            }
            if setting:
                metadata.update(setting.get("metadata") or {})
                status = {
                    "last_test_status": setting.get("last_test_status"),
                    "last_tested_at": self._format_datetime(setting.get("last_tested_at")),
                    "last_test_message": setting.get("last_test_message"),
                }
                secret_info = self._build_secret_descriptor(connection, setting)
            else:
                expected = self._expected_secret_fields(provider)
                secret_info = {field: {"configured": False} for field in expected}
            return {
                "provider": provider,
                "metadata": metadata,
                "secrets": secret_info,
                "status": status,
            }
        finally:
            if connection:
                connection.close()

    def save_settings(
        self,
        provider: str,
        metadata: Optional[Dict[str, Any]] = None,
        secrets: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        provider = self._normalize_provider(provider)
        metadata = metadata or {}
        secrets = secrets or {}
        connection = get_db_connection()
        if not connection:
            raise RuntimeError("数据库连接失败")
        try:
            connection.start_transaction()
            existing = repo.get_setting_by_provider(connection, provider)
            merged_metadata = self._merge_metadata(
                (existing or {}).get("metadata"),
                metadata,
                provider,
            )
            setting_id = repo.upsert_setting(connection, provider, merged_metadata)
            cleaned_secrets = self._clean_secret_values(secrets)
            if cleaned_secrets:
                ciphertext = self.secret_manager.encrypt_dict(cleaned_secrets)
                version = repo.create_secret_version(connection, setting_id, ciphertext)
                repo.update_active_secret_version(connection, setting_id, version)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.get_setting_summary(provider)

    def test_provider(
        self,
        provider: str,
        metadata: Optional[Dict[str, Any]] = None,
        secrets: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        provider = self._normalize_provider(provider)
        metadata = metadata or {}
        secrets = secrets or {}
        runtime = self._compose_runtime_config(provider, metadata, secrets)
        persist_result = not metadata and not secrets and runtime.get("setting_id")
        if provider == PROVIDER_SERVICENOW:
            success, message = self._test_servicenow(runtime)
        elif provider == PROVIDER_AI:
            success, message = self._test_ai(runtime)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        if persist_result:
            self._persist_test_result(runtime["setting_id"], success, message)
        status_code = 200 if success else 400
        return {
            "success": success,
            "message": message if success else None,
            "error": None if success else message,
            "status_code": status_code,
        }

    def get_runtime_credentials(self, provider: str) -> Optional[Dict[str, Any]]:
        provider = self._normalize_provider(provider)
        runtime = self._load_setting_with_secret(provider)
        if not runtime:
            return None
        metadata = self._default_metadata(provider)
        metadata.update(runtime.get("metadata") or {})
        secrets = runtime.get("secrets") or {}
        if not secrets:
            return None
        return {
            "provider": provider,
            "metadata": metadata,
            "secrets": secrets,
            "setting_id": runtime.get("id"),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalize_provider(self, provider: str) -> str:
        if not provider:
            raise ValueError("Provider is required")
        provider = provider.lower()
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        return provider

    def _default_metadata(self, provider: str) -> Dict[str, Any]:
        if provider == PROVIDER_SERVICENOW:
            return {
                "instance_url": "",
                "username": "",
                "default_table": "incident",
            }
        if provider == PROVIDER_AI:
            return {
                "api_provider": "openai",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 1000,
                "system_prompt": "",
            }
        return {}

    def _expected_secret_fields(self, provider: str) -> Tuple[str, ...]:
        if provider == PROVIDER_SERVICENOW:
            return ("password",)
        if provider == PROVIDER_AI:
            return ("api_key",)
        return ()

    def _merge_metadata(
        self,
        existing: Optional[Dict[str, Any]],
        updates: Dict[str, Any],
        provider: str,
    ) -> Dict[str, Any]:
        merged = self._default_metadata(provider)
        if existing:
            merged.update(existing)
        for key, value in (updates or {}).items():
            if value is None:
                merged.pop(key, None)
            else:
                merged[key] = value
        return merged

    def _clean_secret_values(self, secrets: Dict[str, Any]) -> Dict[str, Any]:
        cleaned: Dict[str, Any] = {}
        for key, value in (secrets or {}).items():
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            cleaned[key] = value
        return cleaned

    def _build_secret_descriptor(
        self,
        connection,
        setting: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        descriptor: Dict[str, Dict[str, Any]] = {
            field: {"configured": False}
            for field in self._expected_secret_fields(setting["provider"])
        }
        version = setting.get("active_secret_version")
        if not version:
            return descriptor
        secret_row = repo.get_secret_version(connection, setting["id"], version)
        if not secret_row:
            return descriptor
        try:
            decrypted = self.secret_manager.decrypt_dict(secret_row["ciphertext"])
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to decrypt secrets for provider %s: %s", setting["provider"], exc)
            return descriptor
        ts = self._format_datetime(secret_row.get("created_at"))
        for key in set(list(descriptor.keys()) + list(decrypted.keys())):
            descriptor[key] = {
                "configured": key in decrypted,
                "last_rotated_at": ts,
                "version": secret_row.get("version"),
            }
        return descriptor

    def _format_datetime(self, value: Any) -> Optional[str]:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            return value
        return None

    def _load_setting_with_secret(self, provider: str) -> Optional[Dict[str, Any]]:
        connection = get_db_connection()
        if not connection:
            raise RuntimeError("数据库连接失败")
        try:
            setting = repo.get_setting_by_provider(connection, provider)
            if not setting:
                return None
            version = setting.get("active_secret_version")
            if version:
                secret_row = repo.get_secret_version(connection, setting["id"], version)
                if secret_row:
                    setting["secrets"] = self.secret_manager.decrypt_dict(secret_row["ciphertext"])
            return setting
        finally:
            connection.close()

    def _compose_runtime_config(
        self,
        provider: str,
        metadata_overrides: Dict[str, Any],
        secrets_overrides: Dict[str, Any],
    ) -> Dict[str, Any]:
        stored = self._load_setting_with_secret(provider)
        metadata = self._default_metadata(provider)
        secrets: Dict[str, Any] = {}
        if stored:
            metadata.update(stored.get("metadata") or {})
            secrets.update(stored.get("secrets") or {})
        for key, value in metadata_overrides.items():
            if value is not None:
                metadata[key] = value
        cleaned_secrets = self._clean_secret_values(secrets_overrides)
        secrets.update(cleaned_secrets)
        return {
            "provider": provider,
            "metadata": metadata,
            "secrets": secrets,
            "setting_id": stored.get("id") if stored else None,
        }

    def _persist_test_result(self, setting_id: int, success: bool, message: str) -> None:
        connection = get_db_connection()
        if not connection:
            logger.warning("Skipping test result persistence due to missing DB connection")
            return
        try:
            repo.update_test_result(connection, setting_id, "success" if success else "failed", message)
            connection.commit()
        except Exception:
            connection.rollback()
            logger.exception("Failed to persist integration test result")
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # Provider specific tests
    # ------------------------------------------------------------------
    def _test_servicenow(self, runtime: Dict[str, Any]) -> Tuple[bool, str]:
        metadata = runtime.get("metadata") or {}
        secrets = runtime.get("secrets") or {}
        instance_url = (metadata.get("instance_url") or "").rstrip("/")
        username = metadata.get("username")
        password = secrets.get("password")
        if not instance_url or not username or not password:
            return False, "ServiceNow实例、用户名与密码均为必填项"
        client = ServiceNowClient(instance_url=instance_url, username=username, password=password)
        return (True, "连接成功") if client.test_connection() else (False, "连接测试失败")

    def _test_ai(self, runtime: Dict[str, Any]) -> Tuple[bool, str]:
        metadata = runtime.get("metadata") or {}
        secrets = runtime.get("secrets") or {}
        base_url = metadata.get("base_url")
        api_key = secrets.get("api_key")
        if not base_url or not api_key:
            return False, "AI配置缺少Base URL或API Key"
        model = metadata.get("model", "gpt-3.5-turbo")
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            client.models.list()
            logger.info("AI provider test succeeded for model %s", model)
            return True, "AI配置测试成功"
        except Exception as exc:  # noqa: BLE001
            logger.error("AI configuration test failed: %s", exc)
            return False, str(exc)


integration_settings_service = IntegrationSettingsService()
