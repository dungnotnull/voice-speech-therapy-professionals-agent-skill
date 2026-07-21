"""
JSON schemas for skill validation and execution.

This module defines the schema contracts for:
- Skill registration and invocation
- Input/output validation
- Tool execution schemas
- Hook event payloads
"""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class SkillInputSchema(BaseModel):
    """Schema for skill input validation."""

    type: Literal["string", "number", "boolean", "object", "array"] = Field(
        description="Input data type"
    )

    required: bool = Field(
        default=True,
        description="Whether this input is required"
    )

    description: str = Field(
        description="Human-readable description of the input"
    )

    default: Optional[Any] = Field(
        default=None,
        description="Default value if not provided"
    )

    constraints: Optional[dict] = Field(
        default=None,
        description="Additional constraints (e.g., min/max for numbers)"
    )


class SkillOutputSchema(BaseModel):
    """Schema for skill output validation."""

    type: Literal["string", "number", "boolean", "object", "array"] = Field(
        description="Output data type"
    )

    description: str = Field(
        description="Human-readable description of the output"
    )

    format: Optional[str] = Field(
        default=None,
        description="Expected format (e.g., 'markdown', 'json')"
    )


class ToolDefinition(BaseModel):
    """Definition of a tool that can be invoked by skills."""

    name: str = Field(description="Unique tool identifier")

    description: str = Field(description="Tool description")

    input_schema: dict = Field(
        description="JSON Schema for tool input validation"
    )

    output_schema: dict = Field(
        description="JSON Schema for tool output validation"
    )

    handler: str = Field(
        description="Python handler path (e.g., 'tools.knowledge_updater.main')"
    )

    timeout_seconds: int = Field(
        default=30,
        ge=1,
        description="Tool execution timeout"
    )

    retry_on_failure: bool = Field(
        default=False,
        description="Whether to retry on transient failures"
    )


class SkillRegistry(BaseModel):
    """
    Schema for skill registration in SKILL.md.

    This defines the contract between skill definitions and the execution harness.
    """

    name: str = Field(description="Unique skill identifier (kebab-case)")

    version: str = Field(
        default="1.0.0",
        description="Skill version following semver"
    )

    description: str = Field(
        description="One-line description for skill triggering"
    )

    long_description: Optional[str] = Field(
        default=None,
        description="Extended description for documentation"
    )

    author: Optional[str] = Field(
        default=None,
        description="Skill author or maintainer"
    )

    inputs: dict[str, SkillInputSchema] = Field(
        default_factory=dict,
        description="Named inputs with schemas"
    )

    outputs: dict[str, SkillOutputSchema] = Field(
        default_factory=dict,
        description="Named outputs with schemas"
    )

    tools: list[ToolDefinition] = Field(
        default_factory=list,
        description="Tools available to this skill"
    )

    dependencies: list[str] = Field(
        default_factory=list,
        description="Other skills this depends on"
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization and discovery"
    )

    quality_gates: list[str] = Field(
        default_factory=list,
        description="Quality gate identifiers this skill must pass"
    )


class HookEvent(BaseModel):
    """Schema for hook events."""

    event_type: Literal[
        "skill.pre_invoke",
        "skill.post_invoke",
        "tool.pre_execute",
        "tool.post_execute",
        "quality_gate.pre_check",
        "quality_gate.post_check",
        "error.on_failure",
    ] = Field(description="Type of hook event")

    skill_name: str = Field(description="Name of the skill invoking the hook")

    timestamp: str = Field(description="ISO 8601 timestamp of the event")

    payload: dict = Field(
        default_factory=dict,
        description="Event-specific data payload"
    )

    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (correlation IDs, etc.)"
    )


class QualityGateResult(BaseModel):
    """Schema for quality gate execution results."""

    gate_id: str = Field(description="Gate identifier (e.g., 'U1', 'G1')")

    passed: bool = Field(description="Whether the gate passed")

    message: str = Field(description="Human-readable result message")

    auto_fix_attempted: bool = Field(
        default=False,
        description="Whether auto-fix was attempted"
    )

    auto_fix_successful: Optional[bool] = Field(
        default=None,
        description="Whether auto-fix succeeded (if attempted)"
    )

    retry_count: int = Field(
        default=0,
        description="Number of retries performed"
    )

    max_retries: int = Field(
        default=2,
        description="Maximum retries allowed"
    )


class SkillExecutionContext(BaseModel):
    """Schema for skill execution context passed to all skills."""

    skill_name: str = Field(description="Current skill being executed")

    session_id: str = Field(description="Unique session identifier")

    user_id: Optional[str] = Field(
        default=None,
        description="User identifier (if available)"
    )

    language: Literal["en", "vi"] = Field(
        default="en",
        description="User's preferred language"
    )

    inputs: dict = Field(
        default_factory=dict,
        description="User-provided inputs"
    )

    state: dict = Field(
        default_factory=dict,
        description="Shared state between skills"
    )

    metadata: dict = Field(
        default_factory=dict,
        description="Execution metadata (timestamps, tokens, etc.)"
    )


# JSON Schema exports for validation
SKILL_REGISTRY_JSON_SCHEMA = SkillRegistry.model_json_schema()
HOOK_EVENT_JSON_SCHEMA = HookEvent.model_json_schema()
QUALITY_GATE_RESULT_JSON_SCHEMA = QualityGateResult.model_json_schema()
SKILL_EXECUTION_CONTEXT_JSON_SCHEMA = SkillExecutionContext.model_json_schema()
