"""Copilot SDK Agent Runtime.

This module provides the core agent loop that drives the Enterprise DevEx
Orchestrator. It uses the GitHub Copilot SDK / OpenAI-compatible API to
perform multi-turn, tool-calling agent workflows.

Architecture:
    User Intent (string)
        -> Intent Parser Agent   -> IntentSpec
        -> Architecture Planner  -> PlanOutput
        -> Governance Reviewer   -> GovernanceReport (with feedback loop)
        -> Infrastructure Gen    -> Bicep files, CI/CD, app code, docs

Reliability:
    - Transient errors (rate limits, timeouts, 5xx) are retried with
      exponential backoff before falling back to template mode.
    - Permanent errors (auth, invalid model) fall back immediately.
    - run_sync timeout is configurable via max_iterations parameter.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from openai import AzureOpenAI, OpenAI

from src.orchestrator.config import AppConfig, get_config
from src.orchestrator.llm_client import AnthropicAdapter, create_llm_client
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)

# Maximum retries for transient API errors
_MAX_RETRIES = 1
_BASE_BACKOFF_SECONDS = 0.5


class LLMErrorCategory(Enum):
    """Classification of LLM API errors for retry decisions."""

    TRANSIENT = "transient"  # Rate limit, timeout, 5xx -- retryable
    PERMANENT = "permanent"  # Auth failure, invalid model, bad request -- not retryable
    UNKNOWN = "unknown"  # Unrecognized -- retry once then give up


def _classify_error(error: Exception) -> LLMErrorCategory:
    """Classify an LLM API error as transient or permanent."""
    error_str = str(error).lower()

    # Transient: rate limits, timeouts, server errors
    transient_signals = [
        "rate limit", "rate_limit", "429",
        "timeout", "timed out",
        "500", "502", "503", "504",
        "server error", "internal error",
        "connection", "temporarily unavailable",
        "overloaded",
    ]
    if any(signal in error_str for signal in transient_signals):
        return LLMErrorCategory.TRANSIENT

    # Permanent: auth, invalid model, bad request
    permanent_signals = [
        "401", "403", "authentication", "unauthorized",
        "invalid api key", "invalid_api_key",
        "model not found", "model_not_found",
        "invalid model", "does not exist",
        "400", "bad request",
        "permission", "forbidden",
    ]
    if any(signal in error_str for signal in permanent_signals):
        return LLMErrorCategory.PERMANENT

    return LLMErrorCategory.UNKNOWN

# Type alias for tool functions
ToolFunction = Callable[..., str]


@dataclass
class Tool:
    """Definition of a tool the agent can call."""

    name: str
    description: str
    parameters: dict[str, Any]
    function: ToolFunction

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function-calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class AgentContext:
    """Mutable context passed through the agent chain."""

    config: AppConfig
    messages: list[dict[str, Any]] = field(default_factory=list)
    tools: list[Tool] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    iteration: int = 0
    max_iterations: int = 10


class AgentRuntime:
    """Core agent runtime powered by GitHub Copilot SDK / OpenAI API.

    Manages the agent loop: send messages -> receive tool calls -> execute
    tools -> append results -> repeat until the agent produces a final response.
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or get_config()
        self._client = create_llm_client(self.config)
        self._tool_registry: dict[str, Tool] = {}

    def _create_client(self) -> OpenAI | AzureOpenAI | AnthropicAdapter:
        """Create the appropriate LLM client based on configuration."""
        return create_llm_client(self.config)

    def register_tool(self, tool: Tool) -> None:
        """Register a tool that the agent can call."""
        self._tool_registry[tool.name] = tool
        logger.info("agent.tool_registered", tool=tool.name)

    def register_tools(self, tools: list[Tool]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self.register_tool(tool)

    async def run(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Tool] | None = None,
        max_iterations: int = 10,
    ) -> str:
        """Execute the agent loop with retry logic for transient errors.

        Args:
            system_prompt: System instructions for the agent role.
            user_message: The user's input message.
            tools: Optional tools specific to this run (merged with registry).
            max_iterations: Maximum tool-calling iterations to prevent runaway loops.

        Returns:
            The agent's final text response.
        """
        # Short-circuit in template-only mode to avoid HTTP timeouts
        if self.config.llm.provider == "template-only":
            return self._fallback_response(user_message)

        # Pre-flight token count guard: ~4 chars per token; 128k context window
        # 80,000 chars ≈ 20,000 tokens — conservative guard that leaves room for
        # system prompt and tool schemas while avoiding silent truncation.
        _TOKEN_CHAR_LIMIT = 80_000
        if len(user_message) > _TOKEN_CHAR_LIMIT:
            logger.warning(
                "agent.large_input",
                chars=len(user_message),
                limit=_TOKEN_CHAR_LIMIT,
                msg="Input may exceed context window; falling back to template mode",
            )
            return self._fallback_response(
                user_message,
                reason=f"Input too large ({len(user_message):,} chars > {_TOKEN_CHAR_LIMIT:,} limit)",
            )

        # Merge run-specific tools with registered tools
        all_tools = dict(self._tool_registry)
        if tools:
            for t in tools:
                all_tools[t.name] = t

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        openai_tools = [t.to_openai_schema() for t in all_tools.values()] if all_tools else None

        for iteration in range(max_iterations):
            logger.info("agent.iteration", iteration=iteration, message_count=len(messages))

            response = await self._call_llm_with_retry(messages, openai_tools)
            if response is None:
                return self._fallback_response(user_message)

            choice = response.choices[0]
            message = choice.message

            # If no tool calls, we have the final response
            if not message.tool_calls:
                logger.info("agent.complete", iteration=iteration)
                return message.content or ""

            # Process tool calls
            messages.append(message.model_dump())  # type: ignore[arg-type]

            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args_str = tool_call.function.arguments

                logger.info("agent.tool_call", tool=fn_name, args=fn_args_str)

                if fn_name in all_tools:
                    try:
                        fn_args = json.loads(fn_args_str) if fn_args_str else {}
                        result = all_tools[fn_name].function(**fn_args)
                    except Exception as e:
                        result = f"Error executing tool {fn_name}: {e}"
                        logger.error("agent.tool_error", tool=fn_name, error=str(e))
                else:
                    result = f"Unknown tool: {fn_name}"
                    logger.warning("agent.unknown_tool", tool=fn_name)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    }
                )

        logger.warning("agent.max_iterations", max_iterations=max_iterations)
        return messages[-1].get("content", "Agent reached maximum iterations without a final response.")

    async def _call_llm_with_retry(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
    ) -> Any | None:
        """Call the LLM API with retry logic for transient errors.

        Returns the API response, or None if all retries are exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=messages,
                    tools=tools if tools else None,  # type: ignore[arg-type]
                    temperature=self.config.llm.temperature,
                )
                if attempt > 0:
                    logger.info("agent.retry_succeeded", attempt=attempt)
                return response
            except Exception as e:
                last_error = e
                category = _classify_error(e)
                logger.debug(
                    "agent.api_error",
                    error=str(e),
                    category=category.value,
                    attempt=attempt,
                )

                if category == LLMErrorCategory.PERMANENT:
                    logger.warning("agent.permanent_error", error=str(e))
                    return None

                if attempt < _MAX_RETRIES:
                    backoff = _BASE_BACKOFF_SECONDS * (2 ** attempt)
                    logger.info("agent.retrying", backoff=backoff, attempt=attempt + 1)
                    time.sleep(backoff)
                elif category == LLMErrorCategory.UNKNOWN:
                    # Unknown errors get one retry, then give up
                    logger.warning("agent.unknown_error_exhausted", error=str(e))
                    return None

        logger.warning("agent.retries_exhausted", last_error=str(last_error))
        return None

    def _fallback_response(self, user_message: str, reason: str = "API unavailable") -> str:
        """Provide a template-based fallback when API is unavailable."""
        logger.info("agent.fallback", msg=f"Using template-only mode: {reason}")
        return json.dumps(
            {
                "mode": "template-fallback",
                "message": f"{reason} -- using secure defaults",
                "input": user_message[:200],
            }
        )

    def run_sync(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Tool] | None = None,
        max_iterations: int = 10,
        timeout_seconds: int = 90,
    ) -> str:
        """Synchronous wrapper for the agent loop.

        Args:
            system_prompt: System instructions for the agent role.
            user_message: The user's input message.
            tools: Optional tools specific to this run.
            max_iterations: Maximum tool-calling iterations.
            timeout_seconds: Max seconds to wait for LLM response.
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self.run(system_prompt, user_message, tools, max_iterations),
                )
                try:
                    return future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    logger.warning(
                        "agent.run_sync_timeout",
                        msg=f"LLM call timed out after {timeout_seconds}s",
                    )
                    return self._fallback_response(
                        user_message, reason=f"LLM call timed out after {timeout_seconds}s"
                    )
        else:
            return asyncio.run(self.run(system_prompt, user_message, tools, max_iterations))
