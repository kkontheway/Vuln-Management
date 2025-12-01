"""Integration settings API routes."""
import logging
from flask import Blueprint, jsonify, request

from app.services.integration_settings_service import (
    PROVIDER_AI,
    PROVIDER_SERVICENOW,
    integration_settings_service,
)

logger = logging.getLogger(__name__)

bp = Blueprint("integrations", __name__, url_prefix="/api/integrations")


@bp.route("/settings", methods=["GET", "POST"])
def integration_settings():
    """Retrieve or update integration settings."""
    if request.method == "GET":
        provider = request.args.get("provider")
        if not provider:
            return jsonify({"error": "Provider query parameter is required"}), 400
        try:
            settings = integration_settings_service.get_setting_summary(provider)
            return jsonify(settings)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load integration settings: %s", exc, exc_info=True)
            return jsonify({"error": str(exc)}), 500

    data = request.json or {}
    provider = data.get("provider")
    metadata = data.get("metadata") or {}
    secrets = data.get("secrets") or {}
    if not provider:
        return jsonify({"error": "Provider is required"}), 400
    try:
        settings = integration_settings_service.save_settings(provider, metadata, secrets)
        return jsonify({"settings": settings})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to save integration settings: %s", exc, exc_info=True)
        return jsonify({"error": "Failed to save settings"}), 500


@bp.route("/settings/<provider>/test", methods=["POST"])
def test_integration(provider: str):
    """Test integration connectivity using stored or temporary credentials."""
    data = request.json or {}
    metadata = data.get("metadata") or {}
    secrets = data.get("secrets") or {}
    try:
        result = integration_settings_service.test_provider(provider, metadata, secrets)
        status = result.pop("status_code", 200)
        return jsonify(result), status
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.error("Integration test failed: %s", exc, exc_info=True)
        return jsonify({"success": False, "error": str(exc)}), 500


@bp.route("/settings/<provider>/rotate", methods=["POST"])
def rotate_integration_secret(provider: str):
    """Rotate integration secret by forcing a new secret payload."""
    data = request.json or {}
    secrets = data.get("secrets") or {}
    if not secrets:
        return jsonify({"error": "Secret payload is required for rotation"}), 400
    try:
        settings = integration_settings_service.save_settings(provider, None, secrets)
        return jsonify({
            "settings": settings,
            "message": "Secret rotated successfully",
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.error("Secret rotation failed: %s", exc, exc_info=True)
        return jsonify({"error": "Failed to rotate secret"}), 500


@bp.route("/providers", methods=["GET"])
def list_supported_providers():
    """Helper endpoint returning providers to drive UI drop-downs."""
    return jsonify({
        "providers": [
            {"id": PROVIDER_SERVICENOW, "label": "ServiceNow"},
            {"id": PROVIDER_AI, "label": "AI"},
        ]
    })
