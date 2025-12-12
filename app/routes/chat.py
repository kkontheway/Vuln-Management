"""AI chat routes for FastAPI."""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from openai import OpenAI

from app.services.integration_settings_service import (
    PROVIDER_AI,
    integration_settings_service,
)
from app.utils.auth import auth_guard

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Chat"],
    dependencies=[Depends(auth_guard)],
)

conversation_history: Dict[str, list[Dict[str, str]]] = {}


def _load_ai_runtime_config(override: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Merge stored AI configuration with optional request override."""
    override = override or {}
    stored = integration_settings_service.get_runtime_credentials(PROVIDER_AI)
    metadata = (stored or {}).get("metadata") or {}
    secrets = (stored or {}).get("secrets") or {}

    api_key = override.get("apiKey") or secrets.get("api_key")
    base_url = override.get("baseUrl") or metadata.get("base_url")
    if not api_key or not base_url:
        return None

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": override.get("model") or metadata.get("model", "deepseek-chat"),
        "temperature": override.get("temperature", metadata.get("temperature", 0.7)),
        "max_tokens": override.get("maxTokens", metadata.get("max_tokens", 1000)),
        "system_prompt": override.get("systemPrompt", metadata.get("system_prompt", "")),
    }


@router.post("/chat")
def chat(
    payload: Dict[str, Any] = Body(...),
    x_session_id: str = Header(default="default", alias="X-Session-Id"),
):
    """AI chat interface using DeepSeek or OpenAI compatible API."""
    try:
        message = payload.get("message", "")
        override_config = payload.get("config", {})

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        runtime_config = _load_ai_runtime_config(override_config)
        if not runtime_config:
            raise HTTPException(status_code=400, detail="AI服务尚未配置，请先在 Chat Config 页面设置。")

        conversation = conversation_history.setdefault(x_session_id, []).copy()

        system_prompt = runtime_config.get("system_prompt", "")
        if system_prompt and not any(msg.get("role") == "system" for msg in conversation):
            conversation.insert(0, {"role": "system", "content": system_prompt})

        conversation.append({"role": "user", "content": message})

        client = OpenAI(api_key=runtime_config["api_key"], base_url=runtime_config["base_url"])

        response = client.chat.completions.create(
            model=runtime_config.get("model", "deepseek-chat"),
            messages=conversation,
            temperature=runtime_config.get("temperature", 0.7),
            max_tokens=runtime_config.get("max_tokens", 1000),
            stream=False,
        )

        ai_response = response.choices[0].message.content
        conversation.append({"role": "assistant", "content": ai_response})
        conversation_history[x_session_id] = conversation[-20:]

        return {"response": ai_response, "message": ai_response}

    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("聊天接口出错: %s", exc, exc_info=True)
        error_message = str(exc)
        lowered = error_message.lower()
        if "api_key" in lowered or "authentication" in lowered:
            error_message = "Invalid API key. Please check your API key in Chat Config."
        elif "base url" in lowered or "url" in lowered:
            error_message = "Invalid Base URL. Please check your Base URL in Chat Config."
        elif "model" in lowered:
            error_message = "Invalid model. Please check your model selection in Chat Config."
        raise HTTPException(status_code=500, detail=error_message) from exc
