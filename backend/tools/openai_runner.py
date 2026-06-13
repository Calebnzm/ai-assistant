import json
import os
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI


DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"


def _json_safe(value: Any) -> Any:
    """Convert tool results into JSON-compatible data for logs and model input."""
    try:
        return json.loads(json.dumps(value, default=str))
    except Exception:
        return str(value)


def _tool_result_to_content(value: Any) -> str:
    safe_value = _json_safe(value)
    if isinstance(safe_value, str):
        return safe_value
    return json.dumps(safe_value, default=str)


def to_openai_tools(tool_schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tools = []
    for schema in tool_schemas:
        parameters = schema.get("parameters") or {
            "type": "object",
            "properties": {},
        }
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema.get("description", ""),
                    "parameters": parameters,
                },
            }
        )
    return tools


def conversation_to_openai_messages(messages) -> List[Dict[str, str]]:
    openai_messages = []
    for message in messages:
        role = "assistant" if message.role == "model" else message.role
        openai_messages.append({"role": role, "content": message.content})
    return openai_messages


def _assistant_message_to_dict(message) -> Dict[str, Any]:
    output = {
        "role": "assistant",
        "content": message.content or "",
    }

    if message.tool_calls:
        output["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments or "{}",
                },
            }
            for tool_call in message.tool_calls
        ]

    return output


def _parse_tool_arguments(arguments: Optional[str]) -> Dict[str, Any]:
    if not arguments:
        return {}

    try:
        parsed = json.loads(arguments)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON arguments from model: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Tool arguments must decode to an object.")

    return parsed


def run_openai_tool_agent(
    *,
    messages: List[Dict[str, Any]],
    system_prompt: str,
    tool_schemas: List[Dict[str, Any]],
    tool_registry: Dict[str, Callable],
    user_id: int,
    model: Optional[str] = None,
    max_iterations: int = 20,
    on_tool_result: Optional[Callable[[str, Dict[str, Any], Dict[str, Any], int], None]] = None,
) -> Dict[str, Any]:
    client = OpenAI()
    openai_tools = to_openai_tools(tool_schemas)

    conversation = [{"role": "system", "content": system_prompt}]
    conversation.extend(messages)

    tool_results = []
    response_text = ""
    iterations = 0

    for iterations in range(1, max_iterations + 1):
        request_kwargs = {
            "model": model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            "messages": conversation,
        }
        if openai_tools:
            request_kwargs["tools"] = openai_tools
            request_kwargs["tool_choice"] = "auto"

        completion = client.chat.completions.create(**request_kwargs)
        assistant_message = completion.choices[0].message
        tool_calls = assistant_message.tool_calls or []

        if not tool_calls:
            response_text = assistant_message.content or ""
            break

        conversation.append(_assistant_message_to_dict(assistant_message))

        for tool_call in tool_calls:
            tool_name = tool_call.function.name

            try:
                tool_args = _parse_tool_arguments(tool_call.function.arguments)
                tool_args["user_id"] = user_id
            except ValueError as exc:
                tool_args = {"user_id": user_id}
                tool_result = {
                    "status": "error",
                    "error_type": "ARGUMENT_ERROR",
                    "message": str(exc),
                }
            else:
                tool_function = tool_registry.get(tool_name)
                if not tool_function:
                    tool_result = {
                        "status": "error",
                        "message": f"Tool '{tool_name}' not found.",
                    }
                else:
                    try:
                        raw_tool_result = tool_function(**tool_args)
                        if isinstance(raw_tool_result, dict):
                            tool_result = raw_tool_result
                        else:
                            try:
                                parsed = json.loads(raw_tool_result)
                                tool_result = (
                                    parsed
                                    if isinstance(parsed, dict)
                                    else {"raw": raw_tool_result}
                                )
                            except Exception:
                                tool_result = {"raw": str(raw_tool_result)}
                    except ValueError as exc:
                        tool_result = {
                            "status": "error",
                            "error_type": "VALIDATION_ERROR",
                            "message": "One of the provided arguments has an invalid format.",
                            "details": str(exc),
                        }
                    except TypeError as exc:
                        tool_result = {
                            "status": "error",
                            "error_type": "ARGUMENT_ERROR",
                            "message": "Missing or incorrect arguments for the tool.",
                            "details": str(exc),
                        }
                    except Exception as exc:
                        tool_result = {
                            "status": "error",
                            "message": f"Tool execution error: {exc}",
                        }

            tool_result = _json_safe(tool_result)
            step_index = len(tool_results)
            tool_results.append(tool_result)

            if on_tool_result:
                on_tool_result(tool_name, tool_args, tool_result, step_index)

            conversation.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": _tool_result_to_content(tool_result),
                }
            )

    return {
        "content": response_text,
        "tool_results": tool_results,
        "iterations": iterations,
    }
