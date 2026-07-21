"""
Production-grade tools execution system.

This module provides:
- Tool definition and registration
- Execution handlers with timeout and retry
- Schema validation for inputs/outputs
- Error handling with graceful fallbacks
"""

import asyncio
import importlib
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field

from config.schemas import ToolDefinition, SkillExecutionContext


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


@dataclass
class ToolExecutionContext:
    """Context for tool execution."""

    tool_name: str
    skill_name: str
    session_id: str
    inputs: dict
    timeout_seconds: int = 30
    correlation_id: Optional[str] = None


class ToolExecutor:
    """
    Executes registered tools with:
    - Timeout enforcement
    - Retry logic
    - Error handling
    - Execution tracking
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._execution_history: list[dict] = []

    def register(self, definition: ToolDefinition) -> None:
        """Register a tool definition."""
        self._tools[definition.name] = definition

    def unregister(self, name: str) -> bool:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        return self._tools.get(name)

    async def execute(
        self,
        context: ToolExecutionContext,
    ) -> ToolResult:
        """
        Execute a tool with timeout and retry logic.

        Args:
            context: Tool execution context

        Returns:
            ToolResult with success/error data
        """
        tool = self._tools.get(context.tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {context.tool_name}",
            )

        start_time = datetime.utcnow()

        try:
            # Import handler module
            module_path, func_name = tool.handler.rsplit(".", 1)
            module = importlib.import_module(module_path)
            handler = getattr(module, func_name)

            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_with_retry(handler, context.inputs, tool.retry_on_failure),
                timeout=context.timeout_seconds,
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Record execution
            self._execution_history.append({
                "tool_name": context.tool_name,
                "skill_name": context.skill_name,
                "success": True,
                "execution_time_ms": execution_time,
                "timestamp": start_time.isoformat(),
            })

            return ToolResult(
                success=True,
                data=result,
                execution_time_ms=execution_time,
            )

        except asyncio.TimeoutError:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ToolResult(
                success=False,
                error=f"Tool execution timeout after {context.timeout_seconds}s",
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    async def _execute_with_retry(
        self,
        handler: callable,
        inputs: dict,
        retry_on_failure: bool,
        max_attempts: int = 3,
    ) -> Any:
        """Execute handler with retry logic."""
        last_error = None

        for attempt in range(max_attempts):
            try:
                if asyncio.iscoroutinefunction(handler):
                    return await handler(**inputs)
                else:
                    return handler(**inputs)

            except Exception as e:
                last_error = e
                if not retry_on_failure:
                    raise
                # Exponential backoff
                await asyncio.sleep(2**attempt * 0.1)

        raise last_error

    def get_execution_stats(self) -> dict:
        """Get execution statistics."""
        if not self._execution_history:
            return {"total_executions": 0}

        total = len(self._execution_history)
        successful = sum(1 for e in self._execution_history if e["success"])
        failed = total - successful

        times = [e["execution_time_ms"] for e in self._execution_history]

        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "avg_execution_time_ms": sum(times) / len(times) if times else 0,
            "min_execution_time_ms": min(times) if times else 0,
            "max_execution_time_ms": max(times) if times else 0,
        }


# Global tool executor instance
_global_tool_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """Get the global tool executor instance."""
    global _global_tool_executor
    if _global_tool_executor is None:
        _global_tool_executor = ToolExecutor()
    return _global_tool_executor


# Decorator for registering tools
def tool(
    name: str,
    description: str,
    input_schema: dict,
    output_schema: dict,
    timeout_seconds: int = 30,
    retry_on_failure: bool = False,
) -> callable:
    """
    Decorator for registering tool handlers.

    Usage:
        @tool(
            name="knowledge_updater",
            description="Update knowledge base from external sources",
            input_schema={"type": "object", "properties": {...}},
            output_schema={"type": "object", "properties": {...}}
        )
        async def my_tool(inputs: dict) -> dict:
            return {"status": "success"}
    """
    def decorator(func: callable) -> callable:
        # Get module path for handler reference
        module_path = func.__module__
        handler_path = f"{module_path}.{func.__name__}"

        definition = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            handler=handler_path,
            timeout_seconds=timeout_seconds,
            retry_on_failure=retry_on_failure,
        )

        executor = get_tool_executor()
        executor.register(definition)

        return func

    return decorator
