"""conftest.py — Shared pytest fixtures for voice-speech-therapy-professionals."""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_brain_path(tmp_path: Path) -> Path:
    """Create a temporary SECOND-KNOWLEDGE-BRAIN.md file.

    Returns a path to a brain file pre-populated with the standard 7 sections
    and a sample entry. Tests can write to it safely without touching the real file.
    """
    brain = tmp_path / "SECOND-KNOWLEDGE-BRAIN.md"
    brain.write_text(
        """# SECOND-KNOWLEDGE-BRAIN.md

> Living Knowledge Base - auto-updated.

## 1. Core Concepts & Frameworks
Sample framework content.

## 2. Key Research Papers & Standards
| Title | Authors | Year | Venue | DOI/URL | Tier |
|------|---------|------|-------|---------|------|
| Sample Paper | Author | 2024 | Journal | 10.1234/sample | 2 |

## 3. State-of-the-Art Methods & Tools
Sample SOTA.

## 4. Authoritative Data Sources
- Sample Source (sample.org)

## 5. Analytical Frameworks
Sample frameworks.

## 6. Self-Update Protocol
Sample protocol.

## 7. Knowledge Update Log
"""
    )
    return brain


@pytest.fixture
def sample_paper_entry() -> dict[str, Any]:
    """Return a well-formed sample paper entry dict."""
    return {
        "title": "Voice Therapy Efficacy in Professional Voice Users",
        "authors": ["Smith, J.", "Jones, M.", "Lee, K."],
        "year": 2025,
        "venue": "Journal of Voice",
        "doi_or_url": "https://doi.org/10.1016/j.jvoice.2025.01.001",
        "abstract": (
            "A systematic review of voice therapy outcomes for professional voice users "
            "including teachers, broadcasters, and performers. Results show significant "
            "improvement in VHI scores and acoustic measures."
        ),
        "published_date": datetime.datetime(2025, 3, 15, tzinfo=datetime.timezone.utc),
        "citation_count": 42,
        "source": "semantic_scholar",
    }


@pytest.fixture
def sample_paper_entry_minimal() -> dict[str, Any]:
    """Return a minimal paper entry with only required fields."""
    return {
        "title": "Minimal Paper",
        "authors": [],
        "year": 2025,
        "venue": "Unknown",
        "doi_or_url": "https://example.com/minimal",
        "abstract": "",
        "published_date": None,
        "citation_count": 0,
        "source": "arxiv",
    }


@pytest.fixture(autouse=True)
def capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture all log output at DEBUG level for assertions."""
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def config_override(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Set test-safe environment variables and return the overrides."""
    overrides = {
        "LOG_LEVEL": "DEBUG",
        "LOG_FORMAT": "text",
        "MAX_RETRIES": "2",
        "REQUEST_TIMEOUT": "5",
        "RATE_LIMIT_RPS": "10.0",
        "RECENCY_WINDOW_DAYS": "730",
        "CITATION_CEILING": "1000",
    }
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)
    return overrides
