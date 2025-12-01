"""AI chat routes."""
import logging
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request
from openai import OpenAI

from app.services.integration_settings_service import (
    PROVIDER_AI,
    integration_settings_service,
)

logger = logging.getLogger(__name__)

bp = Blueprint('chat', __name__, url_prefix='/api')

# Store conversation history per session (in production, use Redis or database)
conversation_history = {}


def _load_ai_runtime_config(override: Optional[Dict]) -> Optional[Dict[str, Any]]:
    """Merge stored AI configuration with optional request override."""
    override = override or {}
    stored = integration_settings_service.get_runtime_credentials(PROVIDER_AI)
    metadata = (stored or {}).get('metadata') or {}
    secrets = (stored or {}).get('secrets') or {}

    api_key = override.get('apiKey') or secrets.get('api_key')
    base_url = override.get('baseUrl') or metadata.get('base_url')
    if not api_key or not base_url:
        return None

    return {
        'api_key': api_key,
        'base_url': base_url,
        'model': override.get('model') or metadata.get('model', 'deepseek-chat'),
        'temperature': override.get('temperature', metadata.get('temperature', 0.7)),
        'max_tokens': override.get('maxTokens', metadata.get('max_tokens', 1000)),
        'system_prompt': override.get('systemPrompt', metadata.get('system_prompt', '')),
    }


@bp.route('/chat', methods=['POST'])
def chat():
    """AI chat interface using DeepSeek or OpenAI compatible API."""
    try:
        data = request.json
        message = data.get('message', '')
        override_config = data.get('config', {})

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        runtime_config = _load_ai_runtime_config(override_config)
        if not runtime_config:
            return jsonify({'error': 'AI服务尚未配置，请先在 Chat Config 页面设置。'}), 400

        # Get or create conversation history for this session
        session_id = request.headers.get('X-Session-Id', 'default')
        if session_id not in conversation_history:
            conversation_history[session_id] = []

        messages = conversation_history[session_id].copy()

        # Add system prompt if provided
        system_prompt = runtime_config.get('system_prompt', '')
        if system_prompt and not any(msg.get('role') == 'system' for msg in messages):
            messages.insert(0, {'role': 'system', 'content': system_prompt})

        # Add user message
        messages.append({'role': 'user', 'content': message})

        client = OpenAI(
            api_key=runtime_config['api_key'],
            base_url=runtime_config['base_url']
        )

        temperature = runtime_config.get('temperature', 0.7)
        max_tokens = runtime_config.get('max_tokens', 1000)
        model = runtime_config.get('model', 'deepseek-chat')

        logger.info(f"Calling AI API with model: {model}, base_url: {runtime_config['base_url']}")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )

        ai_response = response.choices[0].message.content

        messages.append({'role': 'assistant', 'content': ai_response})
        conversation_history[session_id] = messages[-20:]

        return jsonify({
            'response': ai_response,
            'message': ai_response
        })

    except Exception as e:  # noqa: BLE001
        logger.error(f"聊天接口出错: {e}", exc_info=True)
        error_message = str(e)

        if 'api_key' in error_message.lower() or 'authentication' in error_message.lower():
            error_message = 'Invalid API key. Please check your API key in Chat Config.'
        elif 'base_url' in error_message.lower() or 'url' in error_message.lower():
            error_message = 'Invalid Base URL. Please check your Base URL in Chat Config.'
        elif 'model' in error_message.lower():
            error_message = 'Invalid model. Please check your model selection in Chat Config.'

        return jsonify({'error': error_message}), 500
