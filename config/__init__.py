"""
Voice Speech Therapy Professionals - Configuration Module

Production-grade configuration management with:
- Type-safe settings with Pydantic validation
- Environment variable overrides
- Feature flag management
- LLM parameter configuration
"""

from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
