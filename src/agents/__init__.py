"""Stub implementations for Agent system interfaces.

This repository expects an external `agents` library providing
`Agent`, `Runner`, and various tool classes. To allow the codebase to
run in environments without that dependency, minimal placeholder
implementations are provided here. These stubs do not perform any real
model calls or tool operations; they simply satisfy imports and return
basic placeholder data.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable


class Agent:
    """Minimal representation of an agent used for testing."""

    def __init__(self, name: str, instructions: str, model: str, tools: Iterable[Any] | None = None):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools: list[Any] = list(tools or [])


class RunResult:
    """Simple container mimicking the structure of a real run result."""

    def __init__(self, output: str = "") -> None:
        self.final_output = output


class Runner:
    """Async runner that returns a stubbed result."""

    @staticmethod
    async def run(agent: Agent, prompt: str) -> RunResult:
        # In a real implementation, this would execute the agent.
        # Here we just return the prompt for visibility.
        return RunResult(f"Stub response from {agent.name} for: {prompt[:50]}")


class WebSearchTool:
    """Placeholder for a web search tool."""

    def __call__(self, *args: Any, **kwargs: Any) -> str:  # pragma: no cover - simple stub
        return ""


class FileSearchTool:
    """Placeholder for a file search tool."""

    def __call__(self, *args: Any, **kwargs: Any) -> str:  # pragma: no cover - simple stub
        return ""


def function_tool(func: Callable | None = None, *, name: str | None = None, description: str | None = None):
    """Decorator used to declare a function as a tool.

    This stub simply returns the function unchanged.
    """

    def decorator(f: Callable) -> Callable:
        return f

    if func is None:
        return decorator
    return decorator(func)
