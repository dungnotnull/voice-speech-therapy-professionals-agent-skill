"""knowledge_updater.py — Voice & Speech Therapy Knowledge Pipeline.

Async-first crawl pipeline that fetches latest papers + news from ArXiv,
Semantic Scholar, and RSS feeds, scores them, deduplicates, and appends
new entries to SECOND-KNOWLEDGE-BRAIN.md via atomic writes.

Usage:
    python tools/knowledge_updater.py [--dry-run] [--news-only]
                                      [--keywords ...] [--log-level LEVEL]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import math
import os
import re
import sys
import time
import traceback
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import httpx
import portalocker

# Support both direct script execution and package import
try:
    from tools._config import (  # type: ignore[import-not-found]
        DEFAULT_CONFIG,
        KnowledgeConfig,
        PaperEntry,
        load_config,
        validate_config,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools._config import (
        DEFAULT_CONFIG,
        KnowledgeConfig,
        PaperEntry,
        load_config,
        validate_config,
    )

logger = logging.getLogger(__name__)

# --- Rate Limiter --------------------------------------------------------------


class TokenBucket:
    """Async token-bucket rate limiter.

    Tokens refill at `rate` per second up to `burst` capacity.
    """

    def __init__(self, rate: float, burst: int = 5) -> None:
        self.rate = rate
        self.burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Block until at least one token is available."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
            self._last_refill = now
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            wait = (1.0 - self._tokens) / self.rate
        await asyncio.sleep(wait)


# --- Metrics ------------------------------------------------------------------


class ErrorType(str, Enum):
    """Categorized error types for structured tracking."""

    NETWORK_TIMEOUT = "network_timeout"
    HTTP_ERROR = "http_error"
    PARSE_ERROR = "parse_error"
    VALIDATION_ERROR = "validation_error"
    FILE_IO_ERROR = "file_io_error"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


class PipelinePhase(str, Enum):
    """Pipeline execution phases."""

    INIT = "init"
    FETCH_ARXIV = "fetch_arxiv"
    FETCH_SEMANTIC_SCHOLAR = "fetch_semantic_scholar"
    FETCH_RSS = "fetch_rss"
    DEDUP = "dedup"
    SCORE = "score"
    APPEND = "append"
    COMPLETE = "complete"


class Metrics:
    """Production-grade observability counters for a pipeline run.

    Includes structured logging context, categorized errors,
    phase tracking, and performance metrics.
    """

    __slots__ = (
        "run_id",
        "fetched_arxiv",
        "fetched_semantic_scholar",
        "fetched_rss",
        "duplicates_skipped",
        "entries_scored",
        "entries_appended",
        "errors",
        "error_types",
        "start_time",
        "end_time",
        "phase",
        "phases_completed",
        "retry_count",
    )

    def __init__(self) -> None:
        self.run_id = str(uuid.uuid4())[:8]
        self.fetched_arxiv = 0
        self.fetched_semantic_scholar = 0
        self.fetched_rss = 0
        self.duplicates_skipped = 0
        self.entries_scored = 0
        self.entries_appended = 0
        self.errors: dict[str, int] = {}
        self.error_types: dict[ErrorType, int] = {e: 0 for e in ErrorType}
        self.start_time = time.monotonic()
        self.end_time: float = 0.0
        self.phase = PipelinePhase.INIT
        self.phases_completed: list[PipelinePhase] = []
        self.retry_count = 0

    def set_phase(self, phase: PipelinePhase) -> None:
        """Update current pipeline phase."""
        self.phase = phase
        logger.info(
            "Pipeline phase transition",
            extra={
                "run_id": self.run_id,
                "phase": phase.value,
                "duration_seconds": time.monotonic() - self.start_time,
            },
        )

    def complete_phase(self, phase: PipelinePhase) -> None:
        """Mark a phase as completed."""
        self.phases_completed.append(phase)
        logger.debug(
            "Phase completed",
            extra={
                "run_id": self.run_id,
                "phase": phase.value,
                "total_completed": len(self.phases_completed),
            },
        )

    def record_error(self, source: str, error_type: ErrorType = ErrorType.UNKNOWN) -> None:
        """Record an error with type categorization."""
        self.errors[source] = self.errors.get(source, 0) + 1
        self.error_types[error_type] += 1
        logger.warning(
            "Error recorded",
            extra={
                "run_id": self.run_id,
                "source": source,
                "error_type": error_type.value,
                "error_count": self.errors[source],
                "phase": self.phase.value,
            },
        )

    def record_retry(self) -> None:
        """Record a retry operation."""
        self.retry_count += 1
        logger.debug(
            "Retry operation",
            extra={"run_id": self.run_id, "retry_count": self.retry_count},
        )

    def finish(self) -> None:
        """Mark pipeline completion."""
        self.end_time = time.monotonic()
        self.phase = PipelinePhase.COMPLETE
        logger.info(
            "Pipeline completion",
            extra={
                "run_id": self.run_id,
                "duration_seconds": self.duration,
                "phases_completed": [p.value for p in self.phases_completed],
                "total_errors": sum(self.errors.values()),
                "total_retries": self.retry_count,
            },
        )

    @property
    def duration(self) -> float:
        return (self.end_time or time.monotonic()) - self.start_time

    def to_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary for structured logging."""
        return {
            "run_id": self.run_id,
            "duration_seconds": self.duration,
            "fetched": {
                "arxiv": self.fetched_arxiv,
                "semantic_scholar": self.fetched_semantic_scholar,
                "rss": self.fetched_rss,
                "total": self.fetched_arxiv
                + self.fetched_semantic_scholar
                + self.fetched_rss,
            },
            "processing": {
                "duplicates_skipped": self.duplicates_skipped,
                "entries_scored": self.entries_scored,
                "entries_appended": self.entries_appended,
            },
            "errors": {
                "by_source": self.errors,
                "by_type": {e.value: c for e, c in self.error_types.items()},
                "total": sum(self.errors.values()),
            },
            "performance": {
                "retries": self.retry_count,
                "phases_completed": len(self.phases_completed),
                "current_phase": self.phase.value,
            },
        }

    def summary(self) -> str:
        """Human-readable summary string."""
        parts = [
            f"arxiv={self.fetched_arxiv}",
            f"semantic_scholar={self.fetched_semantic_scholar}",
            f"rss={self.fetched_rss}",
            f"duplicates={self.duplicates_skipped}",
            f"scored={self.entries_scored}",
            f"appended={self.entries_appended}",
            f"errors={sum(self.errors.values())}",
            f"retries={self.retry_count}",
            f"duration={self.duration:.1f}s",
        ]
        return ", ".join(parts)


# --- Utility ------------------------------------------------------------------


def normalize_identifier(raw: str) -> str:
    """Normalize DOI/URL for consistent hashing.

    Strips https://doi.org/ and https://www.doi.org/ prefixes,
    lowercases, strips trailing slash.
    """
    result = raw.strip().lower()
    result = re.sub(r"^https?://(www\.)?doi\.org/", "", result)
    result = result.rstrip("/")
    return result


def compute_hash(identifier: str) -> str:
    """SHA-256 hash of a normalized identifier for deduplication."""
    return hashlib.sha256(normalize_identifier(identifier).encode()).hexdigest()


def parse_retry_after(header_value: str | None) -> float:
    """Parse Retry-After header into seconds. Returns 0.0 on failure."""
    if not header_value:
        return 0.0
    try:
        return float(header_value.strip())
    except ValueError:
        try:
            from email.utils import parsedate_to_datetime

            retry_dt = parsedate_to_datetime(header_value.strip())
            return (retry_dt - datetime.now(tz=retry_dt.tzinfo)).total_seconds()
        except Exception:
            return 0.0


# --- Async Knowledge Updater --------------------------------------------------


class AsyncKnowledgeUpdater:
    """Async core of the knowledge crawl pipeline.

    Fetches from ArXiv, Semantic Scholar, and RSS feeds in parallel,
    deduplicates, scores, and atomically appends to the brain file.
    """

    def __init__(
        self,
        config: KnowledgeConfig | None = None,
        client: httpx.AsyncClient | None = None,
        brain_path: Path | None = None,
    ) -> None:
        self.config = config or load_config()
        validate_config(self.config)
        self._own_client = client is None
        self.client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(self.config["request_timeout"]),
            headers={
                "User-Agent": "voice-speech-therapy-professionals/2.0 (academic-crawler)",
            },
        )
        self.brain_path = brain_path or (
            Path(__file__).resolve().parent.parent / "SECOND-KNOWLEDGE-BRAIN.md"
        )
        self.rate_limiter = TokenBucket(rate=self.config["rate_limit_rps"])

    async def close(self) -> None:
        if self._own_client:
            await self.client.aclose()

    # -- Network helpers -------------------------------------------------------

    async def _request_with_retry(
        self, url: str, params: dict[str, Any] | None = None
    ) -> httpx.Response | None:
        """HTTP GET with exponential backoff and Retry-After support.

        Includes comprehensive error categorization and graceful fallbacks.
        All errors are logged with structured context for observability.
        """
        max_retries = self.config["max_retries"]
        base_delay = self.config["retry_base_delay"]
        source = url.split("/")[2] if "/" in url else "unknown"

        for attempt in range(max_retries + 1):
            try:
                await self.rate_limiter.acquire()
                resp = await self.client.get(url, params=params)

                # Handle rate limiting (429)
                if resp.status_code == 429:
                    delay = parse_retry_after(resp.headers.get("Retry-After"))
                    if delay <= 0:
                        delay = base_delay * (2**attempt)

                    self.metrics.record_retry()
                    logger.warning(
                        "Rate limited, waiting before retry",
                        extra={
                            "url": url[:60],
                            "attempt": attempt + 1,
                            "max_retries": max_retries + 1,
                            "delay_seconds": delay,
                            "source": source,
                            "run_id": self.metrics.run_id,
                        },
                    )

                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        continue
                    self.metrics.record_error(source, ErrorType.RATE_LIMIT)
                    return None

                # Handle server errors (5xx)
                if resp.status_code >= 500:
                    logger.warning(
                        "Server error, will retry",
                        extra={
                            "status_code": resp.status_code,
                            "url": url[:60],
                            "attempt": attempt + 1,
                            "source": source,
                            "run_id": self.metrics.run_id,
                        },
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(base_delay * (2**attempt))
                        continue
                    self.metrics.record_error(source, ErrorType.HTTP_ERROR)
                    return None

                resp.raise_for_status()
                logger.debug(
                    "Request successful",
                    extra={"url": url[:60], "status": resp.status_code, "source": source},
                )
                return resp

            except httpx.TimeoutException as exc:
                self.metrics.record_retry()
                logger.warning(
                    "Request timeout, will retry",
                    extra={
                        "url": url[:60],
                        "attempt": attempt + 1,
                        "max_retries": max_retries + 1,
                        "source": source,
                        "run_id": self.metrics.run_id,
                        "error": str(exc),
                    },
                )
                if attempt < max_retries:
                    await asyncio.sleep(base_delay)
                    continue
                self.metrics.record_error(source, ErrorType.NETWORK_TIMEOUT)
                return None

            except httpx.HTTPStatusError as exc:
                # Client errors (4xx) should not be retried
                if 400 <= exc.response.status_code < 500:
                    logger.error(
                        "Client error, not retrying",
                        extra={
                            "status_code": exc.response.status_code,
                            "url": url[:60],
                            "source": source,
                            "run_id": self.metrics.run_id,
                            "error": str(exc),
                        },
                    )
                    self.metrics.record_error(source, ErrorType.HTTP_ERROR)
                    return None

                # Server errors should be retried
                if exc.response.status_code >= 500 and attempt < max_retries:
                    await asyncio.sleep(base_delay)
                    continue
                self.metrics.record_error(source, ErrorType.HTTP_ERROR)
                return None

            except httpx.RequestError as exc:
                self.metrics.record_retry()
                logger.error(
                    "Network request error, will retry",
                    extra={
                        "url": url[:60],
                        "attempt": attempt + 1,
                        "source": source,
                        "run_id": self.metrics.run_id,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                )
                if attempt < max_retries:
                    await asyncio.sleep(base_delay)
                    continue
                self.metrics.record_error(source, ErrorType.NETWORK_TIMEOUT)
                return None

            except Exception as exc:
                # Unexpected errors
                logger.exception(
                    "Unexpected error during request",
                    extra={
                        "url": url[:60],
                        "source": source,
                        "run_id": self.metrics.run_id,
                        "error_type": type(exc).__name__,
                        "traceback": traceback.format_exc(),
                    },
                )
                self.metrics.record_error(source, ErrorType.UNKNOWN)
                return None

        # All retries exhausted
        logger.error(
            "Max retries exhausted",
            extra={"url": url[:60], "source": source, "run_id": self.metrics.run_id},
        )
        return None

    # -- Source fetchers -------------------------------------------------------

    async def fetch_arxiv(self, keywords: list[str]) -> list[PaperEntry]:
        """Fetch papers from ArXiv API."""
        if not self.config["arxiv_categories"]:
            logger.debug("ArXiv: no categories configured, skipping")
            return []

        cats = self.config["arxiv_categories"]
        kws = keywords[:5]
        q = (
            "("
            + " OR ".join(f"cat:{c}" for c in cats)
            + ") AND ("
            + " OR ".join(f'"{k}"' for k in kws)
            + ")"
        )
        resp = await self._request_with_retry(
            self.config["arxiv_base"],
            {
                "search_query": q,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": self.config["max_results_per_source"],
            },
        )
        if resp is None:
            logger.warning("ArXiv: request failed")
            return []

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as exc:
            logger.error("ArXiv: XML parse error: %s", exc)
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries: list[PaperEntry] = []
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            id_el = entry.find("atom:id", ns)
            published_el = entry.find("atom:published", ns)

            title = (
                (title_el.text or "").strip().replace("\n", " ")
                if title_el is not None
                else ""
            )
            url = (id_el.text or "").strip() if id_el is not None else ""
            if not title or not url:
                continue

            published_date = None
            year = datetime.now(timezone.utc).year
            if published_el is not None and published_el.text:
                try:
                    from dateutil import parser as dateutil_parser

                    parsed = dateutil_parser.parse(published_el.text)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    published_date = parsed.isoformat()
                    year = parsed.year
                except (ValueError, OverflowError):
                    pass

            authors: list[str] = []
            for author_el in entry.findall("atom:author", ns):
                name_el = author_el.find("atom:name", ns)
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())
            authors = authors[:3]

            abstract = (
                (summary_el.text or "")[:300].strip() if summary_el is not None else ""
            )
            entries.append(
                PaperEntry(
                    title=title,
                    authors=authors,
                    year=year,
                    venue="ArXiv",
                    doi_or_url=url,
                    abstract=abstract,
                    published_date=published_date,
                    citation_count=0,
                    source="arxiv",
                )
            )

        logger.info("ArXiv: fetched %d papers", len(entries))
        return entries

    async def fetch_semantic_scholar(self, keywords: list[str]) -> list[PaperEntry]:
        """Fetch papers from Semantic Scholar API."""
        headers: dict[str, str] = {}
        api_key = self.config.get("semantic_scholar_api_key", "")
        if api_key:
            headers["x-api-key"] = api_key

        params: dict[str, Any] = {
            "query": " ".join(keywords[:4]),
            "fields": "title,authors,year,venue,externalIds,abstract,citationCount",
            "limit": self.config["max_results_per_source"],
        }
        resp = await self._request_with_retry(
            self.config["semantic_scholar_base"], params
        )
        if resp is None:
            logger.warning("Semantic Scholar: request failed")
            return []

        try:
            data = resp.json()
        except ValueError as exc:
            logger.error("Semantic Scholar: JSON decode error: %s", exc)
            return []

        entries: list[PaperEntry] = []
        for paper in data.get("data", []):
            title = paper.get("title", "")
            if not title:
                continue
            year = paper.get("year") or datetime.now(timezone.utc).year
            ext = paper.get("externalIds") or {}
            doi = ext.get("DOI")
            if not doi:
                arxiv_id = ext.get("ArXiv")
                doi = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
            if not doi:
                paper_id = paper.get("paperId", "")
                doi = f"https://www.semanticscholar.org/paper/{paper_id}"

            authors_list: list[str] = [
                a.get("name", "") for a in paper.get("authors", [])[:3]
            ]
            published_date = (
                datetime(year, 1, 1, tzinfo=timezone.utc).isoformat()
            )
            entries.append(
                PaperEntry(
                    title=title,
                    authors=authors_list,
                    year=year,
                    venue=paper.get("venue") or "Unknown",
                    doi_or_url=doi,
                    abstract=(paper.get("abstract") or "")[:300],
                    published_date=published_date,
                    citation_count=paper.get("citationCount", 0),
                    source="semantic_scholar",
                )
            )

        logger.info("Semantic Scholar: fetched %d papers", len(entries))
        return entries

    async def fetch_rss(self) -> list[PaperEntry]:
        """Fetch news items from RSS feeds."""
        try:
            import feedparser  # noqa: PLC0415
        except ImportError:
            logger.debug("feedparser not installed, skipping RSS")
            return []

        feeds = self.config["rss_feeds"]
        if not feeds:
            logger.debug("No RSS feeds configured, skipping")
            return []

        entries: list[PaperEntry] = []
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
            except Exception as exc:
                logger.warning("RSS parse error for %s: %s", feed_url, exc)
                continue

            for item in feed.entries[:10]:
                title = item.get("title", "")
                link = item.get("link", "")
                if not title or not link:
                    continue
                pp = item.get("published_parsed")
                if pp:
                    pub_dt = datetime(*pp[:6], tzinfo=timezone.utc)
                else:
                    pub_dt = datetime.now(timezone.utc)

                entries.append(
                    PaperEntry(
                        title=title,
                        authors=["Editorial"],
                        year=pub_dt.year,
                        venue="RSS",
                        doi_or_url=link,
                        abstract=(item.get("summary", ""))[:200],
                        published_date=pub_dt.isoformat(),
                        citation_count=0,
                        source="rss",
                    )
                )

        logger.info("RSS: fetched %d items", len(entries))
        return entries

    # -- Orchestration ---------------------------------------------------------

    async def fetch_all(self, news_only: bool = False) -> list[PaperEntry]:
        """Fetch from all sources in parallel."""
        tasks: list[asyncio.Task[list[PaperEntry]]] = []
        task_labels: list[str] = []

        if not news_only:
            tasks.append(asyncio.create_task(self.fetch_arxiv(self.config["keywords"])))
            task_labels.append("arxiv")
            await asyncio.sleep(0.5)
            tasks.append(
                asyncio.create_task(self.fetch_semantic_scholar(self.config["keywords"]))
            )
            task_labels.append("semantic_scholar")

        tasks.append(asyncio.create_task(self.fetch_rss()))
        task_labels.append("rss")

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_entries: list[PaperEntry] = []

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Source %s raised: %s", task_labels[idx], result)
                continue
            all_entries.extend(result)

        logger.info("Total candidates from all sources: %d", len(all_entries))
        return all_entries

    # -- Scoring & dedup -------------------------------------------------------

    def load_existing_hashes(self) -> set[str]:
        """Extract existing hashes from the brain file for dedup."""
        if not self.brain_path.exists():
            return set()
        try:
            content = self.brain_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.error("Cannot read brain file: %s", exc)
            return set()

        hashes: set[str] = set()
        for match in re.finditer(r"\*\*DOI/URL:\*\*\s*(\S+)", content):
            hashes.add(compute_hash(match.group(1)))
        return hashes

    def score_entry(self, entry: PaperEntry, now: datetime) -> float:
        """Compute composite relevance score (0-10).

        Score = recency * Wr + keyword_relevance * Wk + citations * Wc,
        scaled to 0-10.
        """
        weights = self.config["scoring_weights"]
        pub_date_str = entry.get("published_date")

        # Recency
        recency = 0.0
        if pub_date_str:
            try:
                pub_dt = datetime.fromisoformat(pub_date_str)
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                days_old = (now - pub_dt).days
                recency = max(0.0, 1.0 - days_old / self.config["recency_window_days"])
            except (ValueError, TypeError, OverflowError):
                recency = 0.0

        # Keyword relevance
        text = f"{entry.get('title', '')} {entry.get('abstract', '')}".lower()
        keywords = self.config["keywords"]
        if keywords:
            hits = sum(1 for kw in keywords if kw.lower() in text)
            relevance = min(hits / len(keywords), 1.0)
        else:
            relevance = 0.5

        # Citation count
        citations = entry.get("citation_count", 0) or 0
        ceiling = max(self.config["citation_ceiling"], 1)
        cit_score = min(math.log1p(citations) / math.log1p(ceiling), 1.0)

        raw = (
            recency * weights["recency"]
            + relevance * weights["keyword_relevance"]
            + cit_score * weights["citation_count"]
        )
        return round(raw * 10.0, 2)

    def dedup_and_score(self, entries: list[PaperEntry]) -> list[PaperEntry]:
        """Deduplicate by DOI/URL hash, score, sort, and cap."""
        existing = self.load_existing_hashes()
        now = datetime.now(timezone.utc)
        new: list[PaperEntry] = []
        seen: set[str] = set()

        for entry in entries:
            doi = entry.get("doi_or_url", "")
            if not doi:
                continue
            h = compute_hash(doi)
            if h in existing or h in seen:
                self.metrics.duplicates_skipped += 1
                continue
            seen.add(h)
            existing.add(h)
            entry["_score"] = self.score_entry(entry, now)  # type: ignore[typeddict-unknown-key]
            self.metrics.entries_scored += 1
            new.append(entry)

        new.sort(key=lambda e: e.get("_score", 0.0), reverse=True)  # type: ignore[typeddict-item]
        new = new[: self.config["max_new_entries_per_run"]]
        logger.info(
            "Dedup: %d entries remaining after filtering (scored=%d, skipped=%d)",
            len(new),
            self.metrics.entries_scored,
            self.metrics.duplicates_skipped,
        )
        return new

    # -- Persistence -----------------------------------------------------------

    def _format_entry(self, entry: PaperEntry, score: float) -> str:  # noqa: PLR6301
        """Format a paper entry as markdown for the brain file."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        authors = ", ".join(entry.get("authors", [])) or "Unknown"
        return (
            f"\n### {date_str} — {entry.get('title', 'Untitled')}\n"
            f"- **Authors:** {authors}\n"
            f"- **Year:** {entry.get('year', '')}\n"
            f"- **Venue:** {entry.get('venue', 'Unknown')}\n"
            f"- **DOI/URL:** {entry.get('doi_or_url', '')}\n"
            f"- **Relevance Score:** {score}/10\n"
            f"- **Key Finding:** {entry.get('abstract', 'No abstract available.')}\n"
        )

    async def append_to_brain(
        self, entries: list[PaperEntry], dry_run: bool = False
    ) -> int:
        """Append scored entries to brain file. Uses atomic write + locking.

        Returns the number of entries appended.
        """
        if not entries:
            return 0

        if dry_run:
            logger.info(
                "DRY RUN: would append %d entries (not writing)", len(entries)
            )
            return len(entries)

        # Build new content
        new_text = "".join(
            self._format_entry(e, e.get("_score", 0.0)) for e in entries  # type: ignore[typeddict-item]
        )

        try:
            brain_dir = self.brain_path.parent
            brain_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("Cannot create brain directory: %s", exc)
            return 0

        try:
            with portalocker.Lock(
                str(self.brain_path), mode="a+", timeout=30, encoding="utf-8"
            ) as fh:
                fh.seek(0)
                content = fh.read()
                if "## 7. Knowledge Update Log" in content:
                    fh.write(new_text)
                else:
                    fh.write("\n## 7. Knowledge Update Log\n" + new_text)
                fh.flush()
                os.fsync(fh.fileno())

            self.metrics.entries_appended = len(entries)
            logger.info("Appended %d entries to brain file", len(entries))
            return len(entries)

        except (portalocker.LockException, OSError, IOError) as exc:
            logger.error("Failed to write brain file: %s", exc)
            return 0

    # -- Main run --------------------------------------------------------------

    async def run(
        self, news_only: bool = False, dry_run: bool = False
    ) -> Metrics:
        """Execute the full pipeline with phase tracking and structured logging.

        Args:
            news_only: If True, skip academic sources (ArXiv, Semantic Scholar)
            dry_run: If True, fetch and score but don't write to brain file

        Returns:
            Metrics object with pipeline execution statistics
        """
        self.metrics = Metrics()
        self.metrics.set_phase(PipelinePhase.FETCH_ARXIV)

        logger.info(
            "Pipeline start",
            extra={
                "run_id": self.metrics.run_id,
                "news_only": news_only,
                "dry_run": dry_run,
            },
        )

        try:
            # Fetch phase
            entries = await self.fetch_all(news_only=news_only)

            # Update fetch counts
            self.metrics.fetched_arxiv = max(
                sum(1 for e in entries if e.get("source") == "arxiv"),
                self.metrics.fetched_arxiv,
            )
            self.metrics.fetched_semantic_scholar = max(
                sum(1 for e in entries if e.get("source") == "semantic_scholar"),
                self.metrics.fetched_semantic_scholar,
            )
            self.metrics.fetched_rss = max(
                sum(1 for e in entries if e.get("source") == "rss"),
                self.metrics.fetched_rss,
            )

            logger.info(
                "Fetch complete",
                extra={
                    "run_id": self.metrics.run_id,
                    "total_entries": len(entries),
                    "arxiv": self.metrics.fetched_arxiv,
                    "semantic_scholar": self.metrics.fetched_semantic_scholar,
                    "rss": self.metrics.fetched_rss,
                },
            )

            # Dedup and score phase
            self.metrics.set_phase(PipelinePhase.DEDUP)
            scored = self.dedup_and_score(entries)
            self.metrics.complete_phase(PipelinePhase.DEDUP)

            # Append phase
            self.metrics.set_phase(PipelinePhase.APPEND)
            appended = await self.append_to_brain(scored, dry_run=dry_run)
            self.metrics.entries_appended = appended
            self.metrics.complete_phase(PipelinePhase.APPEND)

        except Exception as exc:
            logger.exception(
                "Pipeline error",
                extra={
                    "run_id": self.metrics.run_id,
                    "phase": self.metrics.phase.value,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            self.metrics.record_error("pipeline", ErrorType.UNKNOWN)
            raise

        finally:
            self.metrics.finish()

        logger.info(
            "Pipeline complete",
            extra={
                "run_id": self.metrics.run_id,
                "metrics": self.metrics.to_dict(),
            },
        )

        return self.metrics


# --- Sync Wrapper -------------------------------------------------------------


class KnowledgeUpdater:
    """Synchronous wrapper around AsyncKnowledgeUpdater for cron/CLI use."""

    def __init__(
        self,
        config: KnowledgeConfig | None = None,
        brain_path: Path | None = None,
    ) -> None:
        self._config = config
        self._brain_path = brain_path

    def run(self, news_only: bool = False, dry_run: bool = False) -> Metrics:
        """Execute pipeline synchronously."""

        async def _run() -> Metrics:
            updater = AsyncKnowledgeUpdater(
                config=self._config, brain_path=self._brain_path
            )
            try:
                return await updater.run(news_only=news_only, dry_run=dry_run)
            finally:
                await updater.close()

        return asyncio.run(_run())


# --- CLI ----------------------------------------------------------------------


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: str | None = None,
) -> logging.Logger:
    """Configure production-grade structured logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, emit JSON logs for machine parsing
        log_file: Optional file path for log output

    Returns:
        The configured logger instance
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    handlers: list[logging.Handler] = []

    # Console handler
    if json_format:
        console_handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s",'
            '"message":"%(message)s","context":"%(context)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        console_handler.setFormatter(formatter)
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

    handlers.append(console_handler)

    # File handler (optional)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            if json_format:
                file_handler.setFormatter(formatter)
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                    )
                )
            handlers.append(file_handler)
        except (OSError, IOError) as exc:
            sys.stderr.write(f"Warning: Could not open log file {log_file}: {exc}\n")

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(log_level)

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Add new handlers
    for handler in handlers:
        root.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger.info(
        "Logging configured",
        extra={"level": level, "json_format": json_format, "log_file": log_file or "stderr"},
    )

    return logger


def main() -> None:
    """CLI entry point with production-grade argument parsing and logging."""
    parser = argparse.ArgumentParser(
        description="Voice & Speech Therapy Knowledge Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Weekly academic update
  python tools/knowledge_updater.py

  # Daily news only
  python tools/knowledge_updater.py --news-only

  # Dry run with custom keywords
  python tools/knowledge_updater.py --dry-run --keywords vocal fatigue therapy

  # JSON logging to file
  python tools/knowledge_updater.py --log-json --log-file logs/update.log
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to brain file (fetch and score only)",
    )
    parser.add_argument(
        "--news-only",
        action="store_true",
        help="Fetch RSS/news only, skip academic sources (ArXiv, Semantic Scholar)",
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        help="Override search keywords (space-separated)",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: INFO from env or INFO)",
    )
    parser.add_argument(
        "--log-json",
        action="store_true",
        default=os.environ.get("LOG_FORMAT", "text") == "json",
        help="Emit structured JSON logs for machine parsing",
    )
    parser.add_argument(
        "--log-file",
        default=os.environ.get("LOG_FILE"),
        help="Write logs to specified file (append mode)",
    )
    parser.add_argument(
        "--brain-path",
        default=None,
        help="Path to SECOND-KNOWLEDGE-BRAIN.md (default: project root)",
    )
    parser.add_argument(
        "--output-metrics",
        action="store_true",
        help="Output final metrics as JSON to stdout",
    )
    args = parser.parse_args()

    # Configure logging
    setup_logging(
        level=args.log_level,
        json_format=args.log_json,
        log_file=args.log_file,
    )

    # Load and validate configuration
    config = load_config()
    if args.keywords:
        config["keywords"] = list(args.keywords)
        logger.info(f"Using custom keywords: {config['keywords']}")

    try:
        validate_config(config)
    except ValueError as exc:
        logger.error(f"Invalid configuration: {exc}")
        sys.exit(1)

    brain_path = Path(args.brain_path) if args.brain_path else None

    # Execute pipeline
    updater = KnowledgeUpdater(config=config, brain_path=brain_path)
    try:
        metrics = updater.run(news_only=args.news_only, dry_run=args.dry_run)

        # Output metrics
        if args.output_metrics:
            import json

            print(json.dumps(metrics.to_dict(), indent=2))
        else:
            logger.info(f"Final metrics: {metrics.summary()}")

        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception:
        logger.exception("Pipeline failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
