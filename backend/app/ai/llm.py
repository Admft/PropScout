"""Provider-agnostic chat client over Anthropic and OpenAI.

Neutral formats used by the orchestrator:
- tools:    [{"name", "description", "input_schema"}]  (JSON Schema inputs)
- messages: [{"role": "user"|"assistant", "content": str}]
            [{"role": "assistant", "tool_calls": [{"id","name","arguments"}]}]
            [{"role": "tool", "tool_call_id", "name", "content": str}]
Response:   LLMResponse(text, tool_calls)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.config import get_settings


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


def chat(system: str, messages: list[dict], tools: list[dict]) -> LLMResponse:
    provider = get_settings().resolved_provider()
    if provider == "anthropic":
        return _chat_anthropic(system, messages, tools)
    if provider == "openai":
        return _chat_openai(system, messages, tools)
    raise RuntimeError("No LLM configured: set ANTHROPIC_API_KEY or OPENAI_API_KEY")


def _chat_anthropic(system: str, messages: list[dict], tools: list[dict]) -> LLMResponse:
    import anthropic

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    converted: list[dict] = []
    for m in messages:
        if m["role"] == "tool":
            converted.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": m["tool_call_id"],
                            "content": m["content"],
                        }
                    ],
                }
            )
        elif m["role"] == "assistant" and m.get("tool_calls"):
            converted.append(
                {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": tc["arguments"]}
                        for tc in m["tool_calls"]
                    ],
                }
            )
        else:
            converted.append({"role": m["role"], "content": m["content"]})

    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=system,
        messages=converted,
        tools=tools,
    )
    out = LLMResponse()
    for block in resp.content:
        if block.type == "text":
            out.text += block.text
        elif block.type == "tool_use":
            out.tool_calls.append(ToolCall(id=block.id, name=block.name, arguments=block.input))
    return out


def _chat_openai(system: str, messages: list[dict], tools: list[dict]) -> LLMResponse:
    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    converted: list[dict] = [{"role": "system", "content": system}]
    for m in messages:
        if m["role"] == "tool":
            converted.append(
                {"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]}
            )
        elif m["role"] == "assistant" and m.get("tool_calls"):
            converted.append(
                {
                    "role": "assistant",
                    "content": m.get("content") or None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["arguments"]),
                            },
                        }
                        for tc in m["tool_calls"]
                    ],
                }
            )
        else:
            converted.append({"role": m["role"], "content": m["content"]})

    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=converted,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ],
    )
    choice = resp.choices[0].message
    out = LLMResponse(text=choice.content or "")
    for tc in choice.tool_calls or []:
        try:
            args = json.loads(tc.function.arguments)
        except json.JSONDecodeError:
            args = {}
        out.tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))
    return out
