"""LiteLLM provider implementation for multi-provider support."""

import os
import secrets
import string
import json
from typing import Any, AsyncGenerator, Dict, List

import json_repair
import litellm
from litellm import acompletion

from nanobot.providers.base import LLMProvider, LLMResponse, ToolCallRequest, StreamChunk
from nanobot.providers.registry import find_by_model, find_gateway

# Standard chat-completion message keys.
_ALLOWED_MSG_KEYS = frozenset({"role", "content", "tool_calls", "tool_call_id", "name", "reasoning_content"})
_ANTHROPIC_EXTRA_KEYS = frozenset({"thinking_blocks"})
_ALNUM = string.ascii_letters + string.digits

def _short_tool_id() -> str:
    """Generate a 9-char alphanumeric ID compatible with all providers (incl. Mistral)."""
    return "".join(secrets.choice(_ALNUM) for _ in range(9))


class LiteLLMProvider(LLMProvider):
    """
    LLM provider using LiteLLM for multi-provider support.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        default_model: str = "anthropic/claude-opus-4-5",
        extra_headers: dict[str, str] | None = None,
        provider_name: str | None = None,
    ):
        super().__init__(api_key, api_base)
        self.default_model = default_model
        self.extra_headers = extra_headers or {}
        self._gateway = find_gateway(provider_name, api_key, api_base)

        if api_key:
            self._setup_env(api_key, api_base, default_model)
        if api_base:
            litellm.api_base = api_base

        litellm.suppress_debug_info = True
        litellm.drop_params = True

    def _setup_env(self, api_key: str, api_base: str | None, model: str) -> None:
        spec = self._gateway or find_by_model(model)
        if not spec or not spec.env_key: return
        
        if self._gateway: os.environ[spec.env_key] = api_key
        else: os.environ.setdefault(spec.env_key, api_key)

        effective_base = api_base or spec.default_api_base
        for env_name, env_val in spec.env_extras:
            resolved = env_val.replace("{api_key}", api_key).replace("{api_base}", effective_base)
            os.environ.setdefault(env_name, resolved)

    def _resolve_model(self, model: str) -> str:
        if self._gateway:
            prefix = self._gateway.litellm_prefix
            if self._gateway.strip_model_prefix: model = model.split("/")[-1]
            if prefix and not model.startswith(f"{prefix}/"): model = f"{prefix}/{model}"
            return model
        spec = find_by_model(model)
        if spec and spec.litellm_prefix:
            if not any(model.startswith(s) for s in spec.skip_prefixes):
                model = f"{spec.litellm_prefix}/{model}"
        return model

    def _prepare_kwargs(self, messages, tools, model, max_tokens, temperature, reasoning_effort) -> dict:
        original_model = model or self.default_model
        resolved_model = self._resolve_model(original_model)
        
        # CoT Injection
        cot_instruction = "\n\n[ Reasoning Mode ]\nThink step-by-step in <think> tags."
        enhanced_messages = []
        for m in messages:
            if m.get("role") == "system":
                enhanced_messages.append({**m, "content": str(m["content"]) + cot_instruction})
            else: enhanced_messages.append(m)

        kwargs = {
            "model": resolved_model,
            "messages": self._sanitize_messages(self._sanitize_empty_content(enhanced_messages)),
            "max_tokens": max(1, max_tokens),
            "temperature": temperature,
            "drop_params": True,
        }

        if self.api_base:
            kwargs["api_base"] = self.api_base
            kwargs["custom_llm_provider"] = "openai"
        if self.api_key: kwargs["api_key"] = self.api_key
        if self.extra_headers: kwargs["extra_headers"] = self.extra_headers
        if reasoning_effort: kwargs["reasoning_effort"] = reasoning_effort
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        return kwargs

    async def chat(self, **kwargs) -> LLMResponse:
        # Standard implementation redirects to a parsed result
        full_kwargs = self._prepare_kwargs(
            kwargs.get("messages"), kwargs.get("tools"), kwargs.get("model"), 
            kwargs.get("max_tokens", 4096), kwargs.get("temperature", 0.7), 
            kwargs.get("reasoning_effort")
        )
        try:
            response = await acompletion(**full_kwargs)
            return self._parse_response(response)
        except Exception as e:
            return LLMResponse(content=f"LLM Error: {e}", finish_reason="error")

    async def chat_stream(self, messages, tools=None, model=None, max_tokens=4096, temperature=0.7, reasoning_effort=None) -> AsyncGenerator[StreamChunk, None]:
        full_kwargs = self._prepare_kwargs(messages, tools, model, max_tokens, temperature, reasoning_effort)
        full_kwargs["stream"] = True
        
        try:
            async for chunk in await acompletion(**full_kwargs):
                if not chunk.choices: continue
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason
                
                # Extract parts
                content = getattr(delta, "content", None)
                reasoning = getattr(delta, "reasoning_content", None)
                
                tool_call_delta = None
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    tc = delta.tool_calls[0]
                    tool_call_delta = {
                        "index": getattr(tc, "index", 0),
                        "id": getattr(tc, "id", None),
                        "name": getattr(tc.function, "name", None),
                        "arguments": getattr(tc.function, "arguments", None)
                    }

                yield StreamChunk(
                    content=content,
                    reasoning_content=reasoning,
                    tool_call_delta=tool_call_delta,
                    finish_reason=finish_reason
                )
        except Exception as e:
            yield StreamChunk(content=f"\n[Stream Error: {e}]", finish_reason="error")

    def _parse_response(self, response: Any) -> LLMResponse:
        choice = response.choices[0]
        message = choice.message
        tool_calls = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                args = tc.function.arguments
                if isinstance(args, str): args = json_repair.loads(args)
                tool_calls.append(ToolCallRequest(id=getattr(tc, "id", None) or _short_tool_id(), name=tc.function.name, arguments=args))

        usage = {"total_tokens": getattr(response.usage, "total_tokens", 0)} if hasattr(response, "usage") else {}
        return LLMResponse(
            content=message.content, 
            tool_calls=tool_calls, 
            finish_reason=choice.finish_reason or "stop", 
            usage=usage,
            reasoning_content=getattr(message, "reasoning_content", None),
            thinking_blocks=getattr(message, "thinking_blocks", None)
        )

    def _sanitize_messages(self, messages: list[dict]) -> list[dict]:
        sanitized = []
        for msg in messages:
            clean = {k: v for k, v in msg.items() if k in _ALLOWED_MSG_KEYS}
            if clean.get("role") == "assistant" and "content" not in clean: clean["content"] = None
            sanitized.append(clean)
        return sanitized

    def get_default_model(self) -> str: return self.default_model
