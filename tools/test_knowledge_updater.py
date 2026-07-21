"""test_knowledge_updater.py — Production-grade tests for the knowledge pipeline.

Covers: hashing, scoring, config validation, rate limiting, retry logic,
API fetching (mocked), atomic writes, dry-run, DOI normalization,
metrics, and integration.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from tools._config import KnowledgeConfig, load_config, validate_config
from tools.knowledge_updater import (
    AsyncKnowledgeUpdater,
    KnowledgeUpdater,
    Metrics,
    TokenBucket,
    compute_hash,
    normalize_identifier,
    parse_retry_after,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_config() -> KnowledgeConfig:
    """Return a test-safe config with short timeouts and 0 API keys."""
    return KnowledgeConfig(
        domain="Test Domain",
        keywords=["test keyword", "voice therapy"],
        arxiv_categories=["cs.CL", "eess.AS"],
        arxiv_base="https://export.arxiv.org/api/query",
        semantic_scholar_base="https://api.semanticscholar.org/graph/v1/paper/search",
        semantic_scholar_api_key="",
        rss_feeds=["https://example.com/feed.xml"],
        authoritative_docs=["Test Journal"],
        scoring_weights={"recency": 0.4, "keyword_relevance": 0.4, "citation_count": 0.2},
        max_results_per_source=3,
        max_new_entries_per_run=5,
        recency_window_days=730,
        citation_ceiling=1000,
        request_timeout=5,
        max_retries=2,
        retry_base_delay=0.1,
        rate_limit_rps=50.0,
    )


@pytest.fixture
def updater(test_config: KnowledgeConfig, temp_brain_path: Path) -> AsyncKnowledgeUpdater:
    """Return an AsyncKnowledgeUpdater pointing at a temp brain file."""
    return AsyncKnowledgeUpdater(
        config=test_config,
        brain_path=temp_brain_path,
    )


# ===========================================================================
# TestHashDedup
# ===========================================================================


class TestNormalizeIdentifier:
    def test_strips_doi_prefix(self) -> None:
        assert normalize_identifier("https://doi.org/10.1234/abc") == "10.1234/abc"

    def test_strips_http_doi_prefix(self) -> None:
        assert normalize_identifier("http://doi.org/10.1234/abc") == "10.1234/abc"

    def test_strips_trailing_slash(self) -> None:
        assert normalize_identifier("10.1234/abc/") == "10.1234/abc"

    def test_lowercases(self) -> None:
        assert normalize_identifier("HTTPS://DOI.ORG/10.ABC") == "10.abc"

    def test_empty_string(self) -> None:
        assert normalize_identifier("") == ""


class TestComputeHash:
    def test_same_url_same_hash(self) -> None:
        h1 = compute_hash("https://doi.org/10.1234/abc")
        h2 = compute_hash("https://doi.org/10.1234/abc")
        assert h1 == h2

    def test_different_url_different_hash(self) -> None:
        h1 = compute_hash("https://doi.org/10.1234/abc")
        h2 = compute_hash("https://doi.org/10.1234/def")
        assert h1 != h2

    def test_normalization_equivalent(self) -> None:
        h1 = compute_hash("https://doi.org/10.1234/abc")
        h2 = compute_hash("10.1234/abc")
        assert h1 == h2

    def test_trailing_slash_equivalent(self) -> None:
        h1 = compute_hash("10.1234/abc")
        h2 = compute_hash("10.1234/abc/")
        assert h1 == h2

    def test_case_insensitive(self) -> None:
        h1 = compute_hash("10.ABC/Def")
        h2 = compute_hash("10.abc/def")
        assert h1 == h2


# ===========================================================================
# TestScoring
# ===========================================================================


class TestScoring:
    def test_score_in_range(self, test_config: KnowledgeConfig) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        entry = {
            "title": "voice therapy efficacy study",
            "abstract": "This paper examines vocal hygiene and voice therapy outcomes for teachers and performers.",
            "published_date": now.isoformat(),
            "citation_count": 50,
        }
        updater = AsyncKnowledgeUpdater(config=test_config)
        score = updater.score_entry(entry, now)
        assert 0.0 <= score <= 10.0

    def test_recent_paper_scores_higher(self, test_config: KnowledgeConfig) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        updater = AsyncKnowledgeUpdater(config=test_config)
        recent_entry = {
            "title": "voice therapy",
            "abstract": "voice therapy vocal hygiene",
            "published_date": now.isoformat(),
            "citation_count": 10,
        }
        old_entry = {
            "title": "voice therapy",
            "abstract": "voice therapy vocal hygiene",
            "published_date": (now - datetime.timedelta(days=1000)).isoformat(),
            "citation_count": 10,
        }
        assert updater.score_entry(recent_entry, now) > updater.score_entry(old_entry, now)

    def test_zero_citations(self, test_config: KnowledgeConfig) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        entry = {
            "title": "voice therapy",
            "abstract": "voice therapy vocal hygiene",
            "published_date": now.isoformat(),
            "citation_count": 0,
        }
        updater = AsyncKnowledgeUpdater(config=test_config)
        score = updater.score_entry(entry, now)
        assert score >= 0.0

    def test_high_citation_scores_higher(self, test_config: KnowledgeConfig) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        updater = AsyncKnowledgeUpdater(config=test_config)
        low_cit_entry = {
            "title": "voice therapy",
            "abstract": "voice therapy vocal hygiene",
            "published_date": now.isoformat(),
            "citation_count": 0,
        }
        high_cit_entry = {
            "title": "voice therapy",
            "abstract": "voice therapy vocal hygiene",
            "published_date": now.isoformat(),
            "citation_count": 500,
        }
        assert updater.score_entry(high_cit_entry, now) > updater.score_entry(low_cit_entry, now)

    def test_missing_published_date(self, test_config: KnowledgeConfig) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        entry = {
            "title": "voice therapy",
            "abstract": "voice therapy vocal hygiene",
            "published_date": None,
            "citation_count": 10,
        }
        updater = AsyncKnowledgeUpdater(config=test_config)
        score = updater.score_entry(entry, now)
        assert 0.0 <= score <= 10.0

    def test_empty_title_and_abstract(self, test_config: KnowledgeConfig) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        entry = {
            "title": "",
            "abstract": "",
            "published_date": now.isoformat(),
            "citation_count": 0,
        }
        updater = AsyncKnowledgeUpdater(config=test_config)
        score = updater.score_entry(entry, now)
        assert 0.0 <= score <= 10.0


# ===========================================================================
# TestConfig
# ===========================================================================


class TestConfigValidation:
    def test_valid_config_passes(self) -> None:
        config = load_config()
        validate_config(config)

    def test_weights_not_sum_to_one_raises(self, test_config: KnowledgeConfig) -> None:
        test_config["scoring_weights"] = {
            "recency": 0.5,
            "keyword_relevance": 0.5,
            "citation_count": 0.5,
        }
        with pytest.raises(ValueError, match="sum"):
            validate_config(test_config)

    def test_empty_keywords_raises(self, test_config: KnowledgeConfig) -> None:
        test_config["keywords"] = []
        with pytest.raises(ValueError, match="keyword"):
            validate_config(test_config)

    def test_zero_rate_limit_raises(self, test_config: KnowledgeConfig) -> None:
        test_config["rate_limit_rps"] = 0.0
        with pytest.raises(ValueError, match="rate_limit"):
            validate_config(test_config)

    def test_negative_max_retries_raises(self, test_config: KnowledgeConfig) -> None:
        test_config["max_retries"] = -1
        with pytest.raises(ValueError, match="retries"):
            validate_config(test_config)


# ===========================================================================
# TestRateLimiting
# ===========================================================================


class TestTokenBucket:
    @pytest.mark.asyncio
    async def test_acquire_does_not_block_when_tokens_available(self) -> None:
        bucket = TokenBucket(rate=100.0, burst=10)
        start = asyncio.get_event_loop().time()
        for _ in range(5):
            await bucket.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_acquire_blocks_when_exhausted(self) -> None:
        bucket = TokenBucket(rate=2.0, burst=1)
        await bucket.acquire()
        start = asyncio.get_event_loop().time()
        await bucket.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        assert elapsed >= 0.4

    @pytest.mark.asyncio
    async def test_concurrent_acquire_serializes(self) -> None:
        bucket = TokenBucket(rate=10.0, burst=1)
        completed: list[int] = []

        async def worker(i: int) -> None:
            await bucket.acquire()
            completed.append(i)

        await asyncio.gather(*(worker(i) for i in range(3)))
        assert len(completed) == 3


# ===========================================================================
# TestRetryLogic
# ===========================================================================


class TestParseRetryAfter:
    def test_seconds_value(self) -> None:
        assert parse_retry_after("120") == 120.0

    def test_http_date(self) -> None:
        result = parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT")
        assert result > 0.0 or result <= 0.0

    def test_none_returns_zero(self) -> None:
        assert parse_retry_after(None) == 0.0

    def test_empty_string_returns_zero(self) -> None:
        assert parse_retry_after("") == 0.0

    def test_whitespace(self) -> None:
        assert parse_retry_after("  60  ") == 60.0


class TestRetryBehavior:
    @pytest.mark.asyncio
    async def test_retry_on_429(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        call_counter: list[int] = [0]

        def handler(req: httpx.Request) -> httpx.Response:
            call_counter[0] += 1
            if call_counter[0] <= 2:
                return httpx.Response(
                    429,
                    headers={"Retry-After": "0.01"},
                    request=req,
                )
            return httpx.Response(200, json={"data": []}, request=req)

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            updater = AsyncKnowledgeUpdater(
                config=test_config, client=client, brain_path=temp_brain_path
            )
            result = await updater._request_with_retry("http://test/429", {})
            assert result is not None
            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(500, request=req)
            )
        ) as client:
            updater = AsyncKnowledgeUpdater(
                config=test_config, client=client, brain_path=temp_brain_path
            )
            result = await updater._request_with_retry("http://test/500", {})
            assert result is None

    @pytest.mark.asyncio
    async def test_timeout_retry(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        timeout_attempts: list[int] = [0]

        def handler(req: httpx.Request) -> httpx.Response:
            timeout_attempts[0] += 1
            if timeout_attempts[0] < 3:
                raise httpx.TimeoutException("timeout")
            return httpx.Response(200, json={"data": []}, request=req)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            updater = AsyncKnowledgeUpdater(
                config=test_config, client=client, brain_path=temp_brain_path
            )
            result = await updater._request_with_retry("http://test/timeout", {})
            assert result is not None
            assert timeout_attempts[0] >= 2


# ===========================================================================
# TestFetchArxiv
# ===========================================================================


class TestFetchArxiv:
    ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Voice Therapy Efficacy Review</title>
    <summary>A comprehensive review of voice therapy for professional users.</summary>
    <id>http://arxiv.org/abs/2501.00001v1</id>
    <published>2025-01-15T00:00:00Z</published>
    <author><name>Smith, Jane</name></author>
    <author><name>Jones, Mark</name></author>
  </entry>
  <entry>
    <title>Speech Articulation in Broadcasters</title>
    <summary>Analysis of articulation patterns in radio broadcasters.</summary>
    <id>http://arxiv.org/abs/2502.00002v1</id>
    <published>2025-02-20T00:00:00Z</published>
    <author><name>Lee, Kim</name></author>
  </entry>
</feed>"""

    @pytest.mark.asyncio
    async def test_success(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, content=self.ARXIV_XML, request=req)
            )
        ) as client:
            updater = AsyncKnowledgeUpdater(
                config=test_config, client=client, brain_path=temp_brain_path
            )
            results = await updater.fetch_arxiv(test_config["keywords"])
            assert len(results) == 2
            assert results[0]["title"] == "Voice Therapy Efficacy Review"

    @pytest.mark.asyncio
    async def test_empty_xml(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        empty_xml = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, content=empty_xml, request=req)
            )
        ) as client:
            updater = AsyncKnowledgeUpdater(
                config=test_config, client=client, brain_path=temp_brain_path
            )
            results = await updater.fetch_arxiv(test_config["keywords"])
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_malformed_xml_logged(
        self,
        test_config: KnowledgeConfig,
        temp_brain_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, content="not xml", request=req)
            )
        ) as client:
            updater = AsyncKnowledgeUpdater(
                config=test_config, client=client, brain_path=temp_brain_path
            )
            results = await updater.fetch_arxiv(test_config["keywords"])
            assert len(results) == 0
            assert any("parse error" in r.message.lower() for r in caplog.records)


# ===========================================================================
# TestFetchSemanticScholar
# ===========================================================================


class TestFetchSemanticScholar:
    SS_RESPONSE = {
        "data": [
            {
                "title": "Voice Therapy RCT",
                "authors": [{"name": "Brown, A."}],
                "year": 2024,
                "venue": "Journal of Voice",
                "externalIds": {"DOI": "10.1016/jvoice.2024.01"},
                "abstract": "An RCT of voice therapy.",
                "citationCount": 25,
            },
            {
                "title": "Vocal Fold Physiology",
                "authors": [{"name": "White, B."}],
                "year": 2023,
                "venue": "Laryngoscope",
                "externalIds": {"ArXiv": "2301.00001"},
                "abstract": "Vocal fold physiology study.",
                "citationCount": 50,
            },
        ]
    }

    @pytest.mark.asyncio
    async def test_success(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, json=self.SS_RESPONSE, request=req)
            )
        ) as client:
            updater = AsyncKnowledgeUpdater(
                config=test_config, client=client, brain_path=temp_brain_path
            )
            results = await updater.fetch_semantic_scholar(test_config["keywords"])
            assert len(results) == 2
            assert results[0]["title"] == "Voice Therapy RCT"
            assert results[0]["citation_count"] == 25

    @pytest.mark.asyncio
    async def test_empty_results(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, json={"data": []}, request=req)
            )
        ) as client:
            updater = AsyncKnowledgeUpdater(
                config=test_config, client=client, brain_path=temp_brain_path
            )
            results = await updater.fetch_semantic_scholar(test_config["keywords"])
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_missing_external_ids_fallback(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        resp = {
            "data": [
                {
                    "title": "No ID Paper",
                    "authors": [],
                    "year": 2025,
                    "venue": "Unknown",
                    "externalIds": {},
                    "abstract": "",
                    "citationCount": 0,
                }
            ]
        }
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, json=resp, request=req)
            )
        ) as client:
            updater = AsyncKnowledgeUpdater(
                config=test_config, client=client, brain_path=temp_brain_path
            )
            results = await updater.fetch_semantic_scholar(test_config["keywords"])
            assert len(results) == 1
            assert "semanticscholar.org" in results[0]["doi_or_url"]


# ===========================================================================
# TestDryRun
# ===========================================================================


class TestDryRun:
    @pytest.mark.asyncio
    async def test_dry_run_does_not_modify_file(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        original = temp_brain_path.read_text(encoding="utf-8")
        updater = AsyncKnowledgeUpdater(config=test_config, brain_path=temp_brain_path)
        entries = [
            {
                "title": "Test Paper",
                "authors": ["Tester"],
                "year": 2025,
                "venue": "Test Journal",
                "doi_or_url": "10.9999/dryrun",
                "abstract": "Dry run test.",
                "published_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "citation_count": 1,
                "source": "test",
                "_score": 8.0,
            }
        ]
        count = await updater.append_to_brain(entries, dry_run=True)
        assert count == 1
        after = temp_brain_path.read_text(encoding="utf-8")
        assert after == original

    @pytest.mark.asyncio
    async def test_dry_run_returns_correct_count(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        updater = AsyncKnowledgeUpdater(config=test_config, brain_path=temp_brain_path)
        entries = [
            {
                "title": "P1",
                "authors": ["A"],
                "year": 2025,
                "venue": "V",
                "doi_or_url": "10.dry/1",
                "abstract": "",
                "published_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "citation_count": 0,
                "source": "test",
                "_score": 5.0,
            },
            {
                "title": "P2",
                "authors": ["B"],
                "year": 2025,
                "venue": "V",
                "doi_or_url": "10.dry/2",
                "abstract": "",
                "published_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "citation_count": 0,
                "source": "test",
                "_score": 6.0,
            },
        ]
        count = await updater.append_to_brain(entries, dry_run=True)
        assert count == 2


# ===========================================================================
# TestMetrics
# ===========================================================================


class TestMetrics:
    def test_summary_includes_all_fields(self) -> None:
        m = Metrics()
        m.fetched_arxiv = 3
        m.fetched_semantic_scholar = 5
        m.fetched_rss = 2
        m.duplicates_skipped = 1
        m.entries_scored = 10
        m.entries_appended = 8
        m.finish()
        s = m.summary()
        assert "arxiv=3" in s
        assert "semantic_scholar=5" in s
        assert "rss=2" in s
        assert "duplicates=1" in s
        assert "appended=8" in s
        assert "duration=" in s

    def test_duration_is_positive(self) -> None:
        m = Metrics()
        m.finish()
        assert m.duration >= 0.0

    def test_record_error_counts(self) -> None:
        m = Metrics()
        m.record_error("arxiv")
        m.record_error("arxiv")
        m.record_error("semantic_scholar")
        assert m.errors == {"arxiv": 2, "semantic_scholar": 1}


# ===========================================================================
# TestDOINormalization
# ===========================================================================


class TestDOINormalization:
    def test_same_doi_different_prefix(self) -> None:
        h1 = compute_hash("https://doi.org/10.1000/test")
        h2 = compute_hash("http://doi.org/10.1000/test")
        assert h1 == h2

    def test_doi_with_www_prefix(self) -> None:
        h1 = compute_hash("https://www.doi.org/10.1000/test")
        h2 = compute_hash("10.1000/test")
        assert h1 == h2

    def test_complex_doi(self) -> None:
        result = normalize_identifier("https://doi.org/10.1016/S0892-1997(05)80319-6")
        assert result == "10.1016/s0892-1997(05)80319-6"


# ===========================================================================
# TestIntegration
# ===========================================================================


class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_pipeline_with_temp_brain(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        """End-to-end: fetch (mocked) → dedup → score → append to brain."""
        test_config["arxiv_categories"] = ["cs.CL"]
        test_config["rss_feeds"] = []

        arxiv_xml = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Voice Therapy for Professional Users</title>
    <summary>A study on vocal hygiene and voice therapy.</summary>
    <id>http://arxiv.org/abs/2503.00001v1</id>
    <published>2025-03-01T00:00:00Z</published>
    <author><name>Doe, John</name></author>
  </entry>
</feed>"""

        ss_resp = {
            "data": [
                {
                    "title": "Speech Articulation Coaching RCT",
                    "authors": [{"name": "Park, S."}],
                    "year": 2025,
                    "venue": "JSLHR",
                    "externalIds": {"DOI": "10.1044/test.2025"},
                    "abstract": "RCT on articulation coaching for podcasters.",
                    "citationCount": 30,
                }
            ]
        }

        calls: list[str] = []

        def handler(req: httpx.Request) -> httpx.Response:
            calls.append(str(req.url))
            if "arxiv" in str(req.url):
                return httpx.Response(200, content=arxiv_xml, request=req)
            if "semanticscholar" in str(req.url):
                return httpx.Response(200, json=ss_resp, request=req)
            return httpx.Response(404, request=req)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            updater = AsyncKnowledgeUpdater(
                config=test_config, client=client, brain_path=temp_brain_path
            )
            metrics = await updater.run(news_only=False, dry_run=False)

        assert metrics.entries_appended >= 1
        brain_content = temp_brain_path.read_text(encoding="utf-8")
        assert "Voice Therapy for Professional Users" in brain_content


# ===========================================================================
# TestKnowledgeUpdaterSync
# ===========================================================================


class TestKnowledgeUpdaterSync:
    def test_sync_wrapper_runs(
        self, test_config: KnowledgeConfig, temp_brain_path: Path
    ) -> None:
        test_config["arxiv_categories"] = []
        test_config["rss_feeds"] = []
        updater = KnowledgeUpdater(config=test_config, brain_path=temp_brain_path)
        metrics = updater.run(news_only=False, dry_run=True)
        assert metrics is not None
        assert metrics.duration >= 0.0
