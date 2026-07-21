"""tools/_config.py — Typed configuration for the knowledge updater pipeline.

All configuration defaults live in DEFAULT_CONFIG. Environment variables
override specific fields. validate_config() ensures sanity before pipeline start.
"""

from __future__ import annotations

import os
from typing import TypedDict

# --- TypedDicts ----------------------------------------------------------------


class ScoringWeights(TypedDict):
    recency: float
    keyword_relevance: float
    citation_count: float


class KnowledgeConfig(TypedDict):
    domain: str
    keywords: list[str]
    arxiv_categories: list[str]
    arxiv_base: str
    semantic_scholar_base: str
    semantic_scholar_api_key: str
    rss_feeds: list[str]
    authoritative_docs: list[str]
    scoring_weights: ScoringWeights
    max_results_per_source: int
    max_new_entries_per_run: int
    recency_window_days: int
    citation_ceiling: int
    request_timeout: int
    max_retries: int
    retry_base_delay: float
    rate_limit_rps: float


class PaperEntry(TypedDict, total=False):
    title: str
    authors: list[str]
    year: int
    venue: str
    doi_or_url: str
    abstract: str
    published_date: str | None
    citation_count: int
    source: str


# --- Default configuration -----------------------------------------------------

DEFAULT_CONFIG: KnowledgeConfig = {
    "domain": "Vocal Health & Speech-Language Pathology for Voice Professionals",
    "keywords": [
        "voice therapy vocal hygiene",
        "vocal fold physiology",
        "speech articulation coaching",
        "vocal fatigue prevention",
        "Estill voice training",
        "muscle tension dysphonia",
    ],
    "arxiv_categories": [],
    "arxiv_base": "https://export.arxiv.org/api/query",
    "semantic_scholar_base": "https://api.semanticscholar.org/graph/v1/paper/search",
    "semantic_scholar_api_key": "",
    "rss_feeds": [],
    "authoritative_docs": [
        "Journal of Voice — Elsevier",
        "Logopedics Phoniatrics Vocology — Taylor & Francis",
        "Journal of Speech, Language, and Hearing Research — ASHA",
        "Laryngoscope — Wiley",
        "International Journal of Speech-Language Pathology — Taylor & Francis",
        "Seminars in Speech and Language — Thieme",
    ],
    "scoring_weights": {
        "recency": 0.4,
        "keyword_relevance": 0.4,
        "citation_count": 0.2,
    },
    "max_results_per_source": 10,
    "max_new_entries_per_run": 20,
    "recency_window_days": 730,
    "citation_ceiling": 1000,
    "request_timeout": 30,
    "max_retries": 3,
    "retry_base_delay": 2.0,
    "rate_limit_rps": 3.0,
}

# --- Environment-variable mapping ----------------------------------------------

_ENV_MAP: dict[str, tuple[str, type]] = {
    "SEMANTIC_SCHOLAR_API_KEY": ("semantic_scholar_api_key", str),
    "ARXIV_BASE_URL": ("arxiv_base", str),
    "SEMANTIC_SCHOLAR_BASE_URL": ("semantic_scholar_base", str),
    "MAX_RETRIES": ("max_retries", int),
    "RETRY_BASE_DELAY": ("retry_base_delay", float),
    "REQUEST_TIMEOUT": ("request_timeout", int),
    "RATE_LIMIT_RPS": ("rate_limit_rps", float),
    "RECENCY_WINDOW_DAYS": ("recency_window_days", int),
    "CITATION_CEILING": ("citation_ceiling", int),
    "MAX_RESULTS_PER_SOURCE": ("max_results_per_source", int),
    "MAX_NEW_ENTRIES_PER_RUN": ("max_new_entries_per_run", int),
}


def load_config() -> KnowledgeConfig:
    """Load configuration with environment-variable overrides."""
    config = KnowledgeConfig(
        domain=DEFAULT_CONFIG["domain"],
        keywords=list(DEFAULT_CONFIG["keywords"]),
        arxiv_categories=list(DEFAULT_CONFIG["arxiv_categories"]),
        arxiv_base=DEFAULT_CONFIG["arxiv_base"],
        semantic_scholar_base=DEFAULT_CONFIG["semantic_scholar_base"],
        semantic_scholar_api_key=DEFAULT_CONFIG["semantic_scholar_api_key"],
        rss_feeds=list(DEFAULT_CONFIG["rss_feeds"]),
        authoritative_docs=list(DEFAULT_CONFIG["authoritative_docs"]),
        scoring_weights=ScoringWeights(
            recency=DEFAULT_CONFIG["scoring_weights"]["recency"],
            keyword_relevance=DEFAULT_CONFIG["scoring_weights"]["keyword_relevance"],
            citation_count=DEFAULT_CONFIG["scoring_weights"]["citation_count"],
        ),
        max_results_per_source=DEFAULT_CONFIG["max_results_per_source"],
        max_new_entries_per_run=DEFAULT_CONFIG["max_new_entries_per_run"],
        recency_window_days=DEFAULT_CONFIG["recency_window_days"],
        citation_ceiling=DEFAULT_CONFIG["citation_ceiling"],
        request_timeout=DEFAULT_CONFIG["request_timeout"],
        max_retries=DEFAULT_CONFIG["max_retries"],
        retry_base_delay=DEFAULT_CONFIG["retry_base_delay"],
        rate_limit_rps=DEFAULT_CONFIG["rate_limit_rps"],
    )

    for env_var, (config_key, converter) in _ENV_MAP.items():
        value = os.environ.get(env_var)
        if value is not None:
            try:
                config[config_key] = converter(value)  # type: ignore[literal-required]
            except (ValueError, TypeError):
                pass

    return config


def validate_config(config: KnowledgeConfig) -> None:
    """Validate configuration; raises ValueError on invalid state."""
    w = config["scoring_weights"]
    total = w["recency"] + w["keyword_relevance"] + w["citation_count"]
    if abs(total - 1.0) > 0.01:
        raise ValueError(
            f"Scoring weights must sum to ~1.0 (got {total:.3f})"
        )

    if len(config["keywords"]) < 1:
        raise ValueError("At least one keyword is required")

    if config["max_results_per_source"] < 1:
        raise ValueError("max_results_per_source must be >= 1")

    if config["rate_limit_rps"] <= 0:
        raise ValueError("rate_limit_rps must be > 0")

    if config["max_retries"] < 0:
        raise ValueError("max_retries must be >= 0")

    if config["request_timeout"] < 1:
        raise ValueError("request_timeout must be >= 1")
