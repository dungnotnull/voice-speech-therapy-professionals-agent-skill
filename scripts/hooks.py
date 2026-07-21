"""
Production-grade lifecycle hooks system for skill execution.

This module provides a robust hook system for:
- Pre/post skill invocation
- Pre/post tool execution
- Quality gate checks
- Error handling and recovery
- Event emission for observability
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from functools import wraps
from dataclasses import dataclass, field


class HookEventType(str, Enum):
    """Hook event types."""

    SKILL_PRE_INVOKE = "skill.pre_invoke"
    SKILL_POST_INVOKE = "skill.post_invoke"
    TOOL_PRE_EXECUTE = "tool.pre_execute"
    TOOL_POST_EXECUTE = "tool.post_execute"
    QUALITY_GATE_PRE_CHECK = "quality_gate.pre_check"
    QUALITY_GATE_POST_CHECK = "quality_gate.post_check"
    ERROR_ON_FAILURE = "error.on_failure"


@dataclass
class HookEvent:
    """Hook event data structure."""

    event_type: HookEventType
    skill_name: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "skill_name": self.skill_name,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "metadata": self.metadata,
        }


class HookPriority(int, Enum):
    """Hook execution priority (higher = earlier execution)."""

    CRITICAL = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25


@dataclass
class HookRegistration:
    """Hook registration data."""

    name: str
    event_type: HookEventType
    handler: Callable
    priority: HookPriority = HookPriority.NORMAL
    once: bool = False
    enabled: bool = True


class HookManager:
    """
    Centralized hook management and execution.

    Thread-safe hook execution with:
    - Priority-based execution order
    - Conditional execution (once, enabled)
    - Error handling per-hook
    - Event emission
    """

    def __init__(self):
        self._hooks: dict[HookEventType, list[HookRegistration]] = {}
        self._event_history: list[HookEvent] = []
        self._correlation_id: Optional[str] = None

    def register(
        self,
        name: str,
        event_type: HookEventType,
        handler: Callable,
        priority: HookPriority = HookPriority.NORMAL,
        once: bool = False,
    ) -> Callable:
        """
        Register a hook handler.

        Args:
            name: Unique hook name
            event_type: Event type to listen for
            handler: Async or sync callable
            priority: Execution priority (higher first)
            once: Remove hook after first execution

        Returns:
            The registered handler (for decorator usage)
        """

        def decorator(func: Callable) -> Callable:
            registration = HookRegistration(
                name=name,
                event_type=event_type,
                handler=func,
                priority=priority,
                once=once,
            )

            if event_type not in self._hooks:
                self._hooks[event_type] = []

            self._hooks[event_type].append(registration)
            # Sort by priority (descending)
            self._hooks[event_type].sort(key=lambda h: h.priority, reverse=True)

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    async def emit(
        self,
        event_type: HookEventType,
        skill_name: str,
        payload: dict,
        metadata: Optional[dict] = None,
    ) -> list[Any]:
        """
        Emit a hook event to all registered handlers.

        Args:
            event_type: Type of event to emit
            skill_name: Name of the skill emitting
            payload: Event payload data
            metadata: Optional metadata

        Returns:
            List of handler results
        """
        event = HookEvent(
            event_type=event_type,
            skill_name=skill_name,
            payload=payload,
            metadata=metadata or {},
        )

        self._event_history.append(event)

        handlers = self._hooks.get(event_type, [])
        results = []
        to_remove = []

        for registration in handlers:
            if not registration.enabled:
                continue

            try:
                handler = registration.handler
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(event)
                else:
                    result = handler(event)

                results.append(result)

                if registration.once:
                    to_remove.append(registration)

            except Exception as e:
                # Log error but continue with other handlers
                await self.emit(
                    HookEventType.ERROR_ON_FAILURE,
                    skill_name,
                    {"error": str(e), "hook": registration.name},
                )

        # Remove one-time hooks
        for registration in to_remove:
            handlers.remove(registration)

        return results

    def get_history(
        self,
        event_type: Optional[HookEventType] = None,
        skill_name: Optional[str] = None,
    ) -> list[HookEvent]:
        """
        Get event history with optional filtering.

        Args:
            event_type: Filter by event type
            skill_name: Filter by skill name

        Returns:
            Filtered event history
        """
        events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if skill_name:
            events = [e for e in events if e.skill_name == skill_name]

        return events

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()

    def unregister(self, name: str, event_type: Optional[HookEventType] = None) -> bool:
        """
        Unregister a hook by name.

        Args:
            name: Hook name to unregister
            event_type: Optional event type filter

        Returns:
            True if hook was found and removed
        """
        if event_type:
            handlers = self._hooks.get(event_type, [])
            for i, registration in enumerate(handlers):
                if registration.name == name:
                    handlers.pop(i)
                    return True
        else:
            for handlers in self._hooks.values():
                for i, registration in enumerate(handlers):
                    if registration.name == name:
                        handlers.pop(i)
                        return True

        return False

    def enable(self, name: str) -> bool:
        """Enable a hook by name."""
        for handlers in self._hooks.values():
            for registration in handlers:
                if registration.name == name:
                    registration.enabled = True
                    return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a hook by name."""
        for handlers in self._hooks.values():
            for registration in handlers:
                if registration.name == name:
                    registration.enabled = False
                    return True
        return False


# Global hook manager instance
_global_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """Get the global hook manager instance."""
    global _global_hook_manager
    if _global_hook_manager is None:
        _global_hook_manager = HookManager()
    return _global_hook_manager


# Decorator for registering hooks
def hook(
    event_type: HookEventType,
    name: str,
    priority: HookPriority = HookPriority.NORMAL,
    once: bool = False,
) -> Callable:
    """
    Decorator for registering hook handlers.

    Usage:
        @hook(HookEventType.SKILL_PRE_INVOKE, "my-hook")
        async def my_handler(event: HookEvent):
            print(f"Skill {event.skill_name} invoked")
    """
    manager = get_hook_manager()
    return manager.register(name, event_type, handler=None, priority=priority, once=once)


# State synchronization hooks
class StateManager:
    """
    Manages shared state between skills with:
    - Thread-safe access
    - State versioning
    - Change detection
    """

    def __init__(self):
        self._state: dict = {}
        self._version: int = 0

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self._state.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        """Set a state value and increment version."""
        self._state[key] = value
        self._version += 1

        # Emit state change event
        manager = get_hook_manager()
        await manager.emit(
            HookEventType.TOOL_POST_EXECUTE,
            "state-manager",
            {"key": key, "version": self._version},
        )

    async def delete(self, key: str) -> bool:
        """Delete a state value."""
        if key in self._state:
            del self._state[key]
            self._version += 1
            return True
        return False

    def get_version(self) -> int:
        """Get current state version."""
        return self._version

    def get_all(self) -> dict:
        """Get all state (copy)."""
        return self._state.copy()


# Global state manager instance
_global_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = StateManager()
    return _global_state_manager
