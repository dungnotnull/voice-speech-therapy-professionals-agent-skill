"""
Production-grade settings management with type safety and validation.

This module provides a hierarchical configuration system:
1. Default values defined here
2. Environment variable overrides (prefixed with VSTP_)
3. Runtime validation via Pydantic
4. Feature flags for conditional behavior
"""

import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class SourceConfig(BaseModel):
    """Configuration for external data sources."""

    arxiv_categories: list[str] = Field(
        default=["cs.CL", "eess.AS"],
        description="ArXiv categories for speech and language processing"
    )

    semantic_scholar_api_key: Optional[str] = Field(
        default=None,
        description="API key for Semantic Scholar (optional, higher rate limits)"
    )

    ash_base_url: str = Field(
        default="https://www.asha.org",
        description="American Speech-Language-Hearing Association base URL"
    )

    vasta_base_url: str = Field(
        default="https://www.vastastandard.org",
        description="Voice and Speech Trainers Association base URL"
    )

    voice_foundation_base_url: str = Field(
        default="https://voicefoundation.org",
        description="The Voice Foundation base URL"
    )

    pubmed_base_url: str = Field(
        default="https://pubmed.ncbi.nlm.nih.gov",
        description="PubMed base URL"
    )

    cochrane_base_url: str = Field(
        default="https://www.cochranelibrary.com",
        description="Cochrane Library base URL"
    )


class CrawlConfig(BaseModel):
    """Configuration for knowledge pipeline crawling."""

    rate_limit_rps: float = Field(
        default=2.0,
        ge=0.1,
        le=10.0,
        description="Requests per second rate limit"
    )

    retry_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for failed requests"
    )

    retry_backoff_seconds: float = Field(
        default=1.0,
        ge=0.1,
        description="Base backoff time for retries (exponential)"
    )

    request_timeout_seconds: float = Field(
        default=30.0,
        ge=5.0,
        le=120.0,
        description="Timeout for HTTP requests"
    )

    dedup_enabled: bool = Field(
        default=True,
        description="Enable SHA256 deduplication"
    )

    atomic_writes: bool = Field(
        default=True,
        description="Enable atomic file writes (temp + rename)"
    )

    file_lock_timeout: int = Field(
        default=30,
        ge=1,
        description="File lock timeout in seconds"
    )


class LLMConfig(BaseModel):
    """Configuration for LLM parameters."""

    model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Primary model for skill execution"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Sampling temperature for generation"
    )

    max_tokens: int = Field(
        default=4096,
        ge=256,
        le=8192,
        description="Maximum tokens per response"
    )

    timeout_seconds: int = Field(
        default=120,
        ge=30,
        description="LLM request timeout"
    )

    enable_caching: bool = Field(
        default=True,
        description="Enable prompt caching for repeated contexts"
    )


class LoggingConfig(BaseModel):
    """Configuration for structured logging."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Minimum log level"
    )

    format: Literal["text", "json"] = Field(
        default="json",
        description="Log output format"
    )

    log_file: Optional[Path] = Field(
        default=None,
        description="Path to log file (None = stdout only)"
    )

    rotation_size_mb: int = Field(
        default=10,
        ge=1,
        description="Log file rotation size in MB"
    )

    backup_count: int = Field(
        default=5,
        ge=1,
        description="Number of backup log files to retain"
    )


class FeatureFlags(BaseModel):
    """Feature flags for conditional behavior."""

    enable_async_crawl: bool = Field(
        default=True,
        description="Enable async crawling (requires httpx)"
    )

    enable_docker_mode: bool = Field(
        default=False,
        description="Enable Docker-specific optimizations"
    )

    enable_test_mode: bool = Field(
        default=False,
        description="Enable test-specific behavior (mocks, fixtures)"
    )

    enable_verbose_metrics: bool = Field(
        default=False,
        description="Enable detailed performance metrics"
    )

    enable_multilingual_support: bool = Field(
        default=True,
        description="Enable Vietnamese language support"
    )


class Settings(BaseModel):
    """
    Root configuration object.

    Hierarchical loading:
    1. Default values from Pydantic Field defaults
    2. Environment variables (prefix VSTP_)
    3. Runtime overrides via get_settings(overrides={})
    """

    # Version
    version: str = Field(default="2.0.0", description="Application version")

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment"
    )

    # Paths
    project_root: Path = Field(
        default=Path(__file__).parent.parent,
        description="Root directory of the project"
    )

    skills_dir: Path = Field(
        default=Path(__file__).parent.parent / "skills",
        description="Directory containing skill definitions"
    )

    knowledge_base_path: Path = Field(
        default=Path(__file__).parent.parent / "SECOND-KNOWLEDGE-BRAIN.md",
        description="Path to knowledge base file"
    )

    glossary_path: Path = Field(
        default=Path(__file__).parent.parent / "GLOSSARY-vi.md",
        description="Path to bilingual glossary"
    )

    logs_dir: Path = Field(
        default=Path(__file__).parent.parent / "logs",
        description="Directory for log files"
    )

    # Sub-configurations
    sources: SourceConfig = Field(default_factory=SourceConfig)
    crawl: CrawlConfig = Field(default_factory=CrawlConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    @field_validator("environment", mode="before")
    @classmethod
    def parse_environment(cls, v: str) -> str:
        """Parse environment from string or env var."""
        if isinstance(v, str):
            return v.lower()
        return v

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Create Settings from environment variables.

        Environment variables should be prefixed with VSTP_:
        - VSTP_ENVIRONMENT=production
        - VSTP_CRAWL_RATE_LIMIT_RPS=5.0
        - VSTP_LLM_MODEL=claude-opus-4-20250514
        """
        env_vars = {}

        for key, value in os.environ.items():
            if key.startswith("VSTP_"):
                config_key = key[5:].lower()  # Remove VSTP_ prefix
                # Convert to nested structure (e.g., crawl_rate_limit_rps)
                # This is simplified; full implementation would use dot notation
                env_vars[config_key] = value

        return cls(**env_vars)

    def to_dict(self) -> dict:
        """Convert settings to dictionary for serialization."""
        return self.model_dump()


# Singleton instance
_settings: Optional[Settings] = None


def get_settings(overrides: Optional[dict] = None) -> Settings:
    """
    Get the singleton Settings instance.

    Args:
        overrides: Optional dictionary of setting overrides

    Returns:
        Settings instance
    """
    global _settings

    if _settings is None:
        _settings = Settings.from_env()

    if overrides:
        _settings = Settings(**{**_settings.to_dict(), **overrides})

    return _settings


def reset_settings() -> None:
    """Reset the singleton Settings instance (mainly for testing)."""
    global _settings
    _settings = None
