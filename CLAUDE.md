# CLAUDE.md — Skill 179: voice-speech-therapy-professionals

## Skill Identity
- **Skill Name:** `voice-speech-therapy-professionals`
- **Tagline:** Voice & Speech Therapy & Articulation Coach for Voice Professionals (MC, Podcaster, Teacher) — Vocal Health & Speech-Language Pathology for Voice Professionals analysis & decision-support harness.
- **Version:** 3.0.0
- **Current Phase:** Phase 7 — Production-Grade Architectural Upgrade
- **Folder:** `D:\972026\179-voice-speech-therapy-professionals\`

---

## Problem This Skill Solves

This skill provides a structured, evidence-backed analytical workflow for
**Vocal Health & Speech-Language Pathology for Voice Professionals**. It:
1. Administers a structured intake questionnaire and classifies voice professional subtypes
2. Gathers authoritative real-time and reference data with recency thresholds and fallback chains
3. Performs CAPE-V (0-100mm VAS × 6 parameters) and GRBAS (0-3 × 5 parameters) voice assessment
4. Prescribes from a complete exercise library (22 exercises: SOVT, Estill figures, breath, resonance, articulation, cool-down) with dosage, progression, and precautions
5. Applies differential diagnosis for 10 conditions with red-flag triage
6. Queries a self-improving knowledge base (14+ seeded papers) with 6 sub-domain coverage assessment
7. Synthesizes findings via a decision tree into 5 conclusion categories with 5×5 risk matrix
8. Delivers fully risk-disclosed, evidence-traced outputs in bilingual English/Vietnamese

---

## File Inventory (v3.0.0)

### Core Skill Files (7)
| File | Lines | Purpose |
|------|-------|---------|
| `skills/main.md` | 220 | Harness entry point: 6-step protocol, 10 quality gates, architecture diagram |
| `skills/sub-gather-requirements.md` | 200 | Structured intake: 14-field questionnaire, 6-subtype classification, red-flag detection |
| `skills/sub-evidence-collector.md` | 180 | Evidence collection: search strategies, recency thresholds, fallback chains |
| `skills/sub-core-analysis.md` | 350 | Domain engine: CAPE-V, GRBAS, acoustic norms, 22-exercise library, differential dx, triage |
| `skills/sub-knowledge-updater.md` | 160 | Knowledge surfacing: tier-labeled citations, 6 sub-domain coverage, gap detection |
| `skills/sub-advisor.md` | 180 | Synthesis: decision tree, 5×5 risk matrix, evidence chain, remediation, disclosure |
| `skills/_shared-conventions.md` | 120 | Shared: U1-U6 gates, evidence hierarchy (Tier 1-4), degradation protocol, translations |

### Configuration System (3)
| File | Lines | Purpose |
|------|-------|---------|
| `config/__init__.py` | 15 | Configuration module exports |
| `config/settings.py` | 180 | Hierarchical settings with Pydantic validation, env-var overrides, feature flags |
| `config/schemas.py` | 120 | JSON schemas for skill/tool validation, input/output contracts |

### Scripts & Automation (2)
| File | Lines | Purpose |
|------|-------|---------|
| `scripts/__init__.py` | 10 | Scripts module exports |
| `scripts/hooks.py` | 280 | Lifecycle hooks system with priority execution, state synchronization, event emission |
| `scripts/tools.py` | 200 | Tool execution system with timeout, retry, validation, execution statistics |

### References & Templates (3)
| File | Lines | Purpose |
|------|-------|---------|
| `references/__init__.py` | 10 | References module exports |
| `references/domain-knowledge.md` | 100 | Authoritative domain knowledge for RAG/grounding |
| `references/prompt-templates.md` | 180 | Base prompt templates for agents |

### Assets & Diagrams (2)
| File | Lines | Purpose |
|------|-------|---------|
| `assets/__init__.py` | 10 | Assets module exports |
| `assets/diagrams.md` | 200 | System architecture diagrams (high-level, data flow, component interaction, error handling) |

### Skill Registry (1)
| File | Lines | Purpose |
|------|-------|---------|
| `SKILL.md` | 500 | Complete skill specification: registration, resolution, execution, validation, architecture |

### Supporting Documentation (7)
| File | Purpose |
|------|---------|
| `CLAUDE.md` | This file — skill identity and file inventory |
| `PROJECT-detail.md` | Full technical specification |
| `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` | Build roadmap (7 phases, 100% complete) |
| `SECOND-KNOWLEDGE-BRAIN.md` | Living knowledge base (14+ papers, 7 sections) |
| `GLOSSARY-vi.md` | 140+ Vietnamese/English term pairs (7 sections) |
| `README.md` | Project overview with architecture diagram and usage |
| `CONTRIBUTING.md` | Development setup, workflow, code style |

### Python Tools (4)
| File | Lines | Purpose |
|------|-------|---------|
| `tools/_config.py` | 140 | TypedDict configuration with env-var overrides and validation |
| `tools/knowledge_updater.py` | 600 | Async crawl pipeline: structured logging, error categorization, phase tracking, atomic writes |
| `tools/run_test_scenarios.py` | 130 | Structural & content validator for 8-File Contract + new v3 files |
| `tools/test_knowledge_updater.py` | 450 | 42 tests: hashing, scoring, config, rate limiting, retry, API mocks, integration |

### Domain Tests (1)
| File | Lines | Purpose |
|------|-------|---------|
| `tests/test_domain.py` | 300 | 25 tests: CAPE-V, GRBAS, exercise dosage, red-flag triage, profession classification, acoustic norms, conclusion logic |

### Test Artifacts (3)
| File | Purpose |
|------|---------|
| `tests/test-scenarios.md` | 5 end-to-end test scenarios (standard, minimal, comparison, risk, degraded) |
| `tests/TEST_RESULTS.md` | Validation results summary |
| `DEVELOPMENT-TRACKING.md` | Session tracking and completed work log |

### Infrastructure Files (9)
| File | Purpose |
|------|---------|
| `pyproject.toml` | PEP 621 metadata, deps, ruff/pyright/pytest/coverage config |
| `pytest.ini` | Pytest configuration (asyncio auto, markers) |
| `conftest.py` | Shared fixtures (brain, entries, logs, config) |
| `.pre-commit-config.yaml` | Ruff format/lint + pre-commit hooks |
| `.editorconfig` | Consistent formatting across editors |
| `.env.example` | Documented environment variables |
| `Dockerfile` | Containerized runtime (python:3.12-slim) |
| `Makefile` | Task runner (install, lint, test, build, etc.) |
| `.github/workflows/` | CI (lint + typecheck + test + validate) + PyPI publish |

---

## Harness Flow

```
/voice-speech-therapy-professionals invoked
│
├─ Step 1: sub-gather-requirements   → Intake questionnaire, profession classification, red flags
├─ Step 2: sub-evidence-collector    → Search strategies, recency thresholds, fallback chain
├─ Step 3: sub-core-analysis         → CAPE-V, GRBAS, exercise library, differential dx, triage
├─ Step 4: sub-knowledge-updater     → Knowledge base citations, 6-domain coverage, gap detection
├─ Step 5: sub-advisor               → Decision tree, risk matrix, evidence chain, disclosure
└─ Step 6: main (quality gate)       → 10 gates (U1-U6 + G1-G4), enforcement, auto-fix
```

---

## Sub-Skills

| File | Role | Key Deliverables |
|------|------|------------------|
| `sub-gather-requirements.md` | Intake Specialist | 14-field questionnaire, subtype classification, red-flag escalation |
| `sub-evidence-collector.md` | Data Librarian | Evidence bundle with tier + recency + independence annotation |
| `sub-core-analysis.md` | SLP & Voice Pedagogue | CAPE-V + GRBAS scores, 22-exercise prescription, differential dx, triage |
| `sub-knowledge-updater.md` | Research Librarian | 3-5 tier-labeled citations, 6-domain coverage rating, gap queries |
| `sub-advisor.md` | Senior Advisor | Conclusion category, 5×5 risk matrix, evidence chain, remediation |

---

## Knowledge Pipeline

### Crawl Sources
- **ArXiv** — configured categories: cs.CL, eess.AS (speech/audio)
- **Semantic Scholar** — keyword-based paper search
- **RSS feeds** — news from domain sources (configurable)

### Features
- Async-first (httpx.AsyncClient, asyncio.gather for parallel fetching)
- Token bucket rate limiter (configurable RPS)
- Retry-After header parsing for 429 responses
- SHA256 deduplication with DOI/URL normalization
- Atomic writes (temp file + os.replace)
- File locking for concurrent-run safety (portalocker)
- Structured logging (text + JSON formats)
- Metrics: fetched, duplicated, scored, appended, errors, duration

### Schedule
```cron
# Weekly academic update (Mondays 8:00 AM)
0 8 * * 1 python D:/972026/179-voice-speech-therapy-professionals/tools/knowledge_updater.py >> logs/knowledge_update.log 2>&1

# Daily news update (Daily 7:00 AM)
0 7 * * * python D:/972026/179-voice-speech-therapy-professionals/tools/knowledge_updater.py --news-only >> logs/knowledge_news.log 2>&1
```

### Docker Cron
```bash
docker run --rm -v $(pwd):/app vstp
docker run --rm -v $(pwd):/app vstp --news-only
```

### Manual
```bash
python tools/knowledge_updater.py --dry-run
python tools/knowledge_updater.py --keywords "vocal fatigue" "voice therapy exercises"
python tools/knowledge_updater.py --log-json --log-level DEBUG
```

---

## Tools Required

- **Read** — SECOND-KNOWLEDGE-BRAIN.md, GLOSSARY-vi.md, _shared-conventions.md
- **WebSearch / WebFetch** — ASHA, VASTA, Voice Foundation, PubMed, Cochrane, Semantic Scholar
- **Skill** — invoke sub-skills sequentially through harness
- **Bash** — run tools/knowledge_updater.py for periodic crawl

---

## Quality Gates

See `skills/_shared-conventions.md` for full definitions.

| Gate | Check |
|------|-------|
| U1-U6 | Universal: sources, disclosure, evidence hierarchy, language, template, traceability |
| G1 | Voice production with measurable dimensions (CAPE-V 0-100 VAS + GRBAS 0-3) |
| G2 | Evidence-based exercise protocol with dosage and progression |
| G3 | Pathology red-flags trigger medical referral with urgency level |
| G4 | Articulation drills with measurable targets |

---

## Development Tasks (All Complete)

- [x] Phase 0: Architecture & source map
- [x] Phase 1: Core sub-skills (5) — production-grade with domain depth
- [x] Phase 2: Main harness + 10 quality gates + degradation
- [x] Phase 3: Knowledge pipeline — async, rate-limited, atomic writes
- [x] Phase 4: Testing — 42 tests (unit + domain + integration)
- [x] Phase 5: Integration & polish — 10+ infrastructure files
- [x] Phase 6: Open-Source Production Release — v2.0.0
- [x] Phase 7: Production-Grade Architectural Upgrade — v3.0.0

---

## References

- `PROJECT-detail.md` — full technical specification
- `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` — build roadmap
- `SECOND-KNOWLEDGE-BRAIN.md` — self-improving knowledge base
- `GLOSSARY-vi.md` — 140+ Vietnamese/English term pairs
- `skills/_shared-conventions.md` — universal gates, evidence hierarchy, degradation
- External: `D:\972026\SKILL-STANDARD.md` — library-wide standard
