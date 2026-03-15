"""AI Client -- auto-detecting provider with enterprise auth.

Supports:
1. Azure OpenAI with Managed Identity (AZURE_OPENAI_ENDPOINT set)
2. Azure OpenAI with API key (AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY)
3. OpenAI API (OPENAI_API_KEY set)

No mocks — real AI processing for: Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, AuditLog
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

CHAT_MODEL = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
EMBEDDINGS_MODEL = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "text-embedding-ada-002")


def _create_azure_openai_client():
    """Create Azure OpenAI client with Managed Identity or API key."""
    from openai import AzureOpenAI

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if api_key:
        return AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-06-01",
        )

    # Managed Identity (production path)
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    credential = DefaultAzureCredential(
        managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
    )
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-06-01",
    )


def _create_openai_client():
    """Create standard OpenAI client."""
    from openai import OpenAI

    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_ai_client():
    """Auto-detect and return the best available AI client.

    Returns a tuple of (client, provider_name).
    Raises RuntimeError if no provider is configured.
    """
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        logger.info("ai_client.provider", extra={"provider": "azure_openai"})
        return _create_azure_openai_client(), "azure_openai"

    if os.getenv("OPENAI_API_KEY"):
        logger.info("ai_client.provider", extra={"provider": "openai"})
        return _create_openai_client(), "openai"

    raise RuntimeError(
        "No AI provider configured. Set one of: "
        "AZURE_OPENAI_ENDPOINT (+ optional AZURE_OPENAI_API_KEY), "
        "or OPENAI_API_KEY"
    )


def get_embeddings(text: str) -> list[float]:
    """Generate embeddings for the given text."""
    client, _ = get_ai_client()
    response = client.embeddings.create(model=EMBEDDINGS_MODEL, input=text)
    return response.data[0].embedding


def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> dict[str, Any]:
    """Run a chat completion and return structured result."""
    client, provider = get_ai_client()
    use_model = model or CHAT_MODEL

    response = client.chat.completions.create(
        model=use_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    choice = response.choices[0]
    return {
        "reply": choice.message.content or "",
        "model": use_model,
        "provider": provider,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        },
    }
