# voice-speech-therapy-professionals

**Voice & Speech Therapy & Articulation Coach for Voice Professionals (MC, Podcaster, Teacher)** — Production-grade, evidence-backed analysis harness

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.0.0-blue)](CHANGELOG.md)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://github.com/astral-sh/ruff)

A professional-grade Claude Code harness for **Vocal Health & Speech-Language Pathology for Voice Professionals** — gathers real-time authoritative data, applies CAPE-V and GRBAS assessment protocols, prescribes from a complete evidence-based exercise library (SOVT, Estill figures, breath support, resonance, articulation drills), integrates academic research, performs differential diagnosis, and delivers risk-disclosed outputs with full evidence-chain traceability.

---

## Architecture

```
USER INPUT
    │
    ▼
[main.md — voice-speech-therapy-professionals]
    │
    ├─► 1. sub-gather-requirements  → Structured intake: profession, symptoms, history
    ├─► 2. sub-evidence-collector    → Authoritative data: ASHA, VASTA, PubMed, Cochrane
    ├─► 3. sub-core-analysis         → CAPE-V + GRBAS + exercise library + differential dx
    ├─► 4. sub-knowledge-updater     → Knowledge base citations + coverage assessment
    └─► 5. sub-advisor               → Decision tree → conclusion + risk matrix + disclosure
         │
         ▼
    [QUALITY GATE — 10 gates (U1-U6 + G1-G4)]
         │
         ▼
    FINAL REPORT (bilingual English/Vietnamese)
```

---

## Features

- **CAPE-V & GRBAS Assessment** — perceptual voice evaluation with 0-100mm VAS and 0-3 severity scales
- **Complete Exercise Library** — 22 evidence-based exercises across SOVT, Estill figures, breath support, resonance, articulation, and cool-down — all with dosage, progression, and precautions
- **Profession-Specific Protocols** — differentiated bundles for Teachers, Podcasters, and MCs/Hosts
- **Differential Diagnosis** — framework for 10 conditions (MTD, nodules, polyps, cysts, LPR, presbyphonia, spasmodic dysphonia, and more)
- **Red-Flag Triage** — algorithmic urgency-based referral to ENT or SLP
- **Bilingual Support** — full Vietnamese/English with 140+ term glossary (`GLOSSARY-vi.md`)
- **Self-Improving Knowledge Pipeline** — async crawl from ArXiv + Semantic Scholar + RSS, SHA256 dedup, atomic writes, structured logging

---

## Installation

### From PyPI (recommended)
```bash
pip install voice-speech-therapy-professionals
```

### From source
```bash
git clone https://github.com/your-org/voice-speech-therapy-professionals.git
cd voice-speech-therapy-professionals
pip install -e .
```

### Docker
```bash
docker build -t vstp .
docker run --rm vstp --dry-run
```

---

## Usage

### Claude Code Skill
```bash
/voice-speech-therapy-professionals [your query]
```

Example queries:
```
/voice-speech-therapy-professionals I'm a teacher, voice gets hoarse after 4 hours of class daily for 2 months
/voice-speech-therapy-professionals I'm a podcaster, voice cracks mid-recording after 30 minutes
/voice-speech-therapy-professionals Tôi là MC, giọng khàn sau mỗi sự kiện dài 3 tiếng
```

### Knowledge Pipeline (standalone)
```bash
# Dry run (preview what would be added)
python tools/knowledge_updater.py --dry-run --log-level DEBUG

# Full update (appends to SECOND-KNOWLEDGE-BRAIN.md)
python tools/knowledge_updater.py

# News only
python tools/knowledge_updater.py --news-only

# With custom keywords
python tools/knowledge_updater.py --keywords "vocal nodules prevention" "voice therapy SOVT"

# Docker
docker run --rm -v $(pwd):/app vstp --dry-run

# JSON structured logging
python tools/knowledge_updater.py --log-json --log-level DEBUG
```

---

## Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests (42 tests)
pytest tools/ tests/ -v --cov=tools

# Run project validator
python tools/run_test_scenarios.py

# Or via Makefile
make test-cov validate
```

---

## Data Sources

### Domain Authoritative
- American Speech-Language-Hearing Association (ASHA) — asha.org
- Voice & Speech Trainers Association (VASTA) — vasta.org
- The Voice Foundation — voicefoundation.org
- Estill Voice Training — estillvoice.com
- NIH NIDCD — nidcd.nih.gov (voice disorders)
- Royal College of Speech & Language Therapists (RCSLT)
- British Voice Association

### Academic & Research
- Journal of Voice — Elsevier
- Logopedics Phoniatrics Vocology — Taylor & Francis
- Journal of Speech, Language, and Hearing Research — ASHA
- Laryngoscope — Wiley
- International Journal of Speech-Language Pathology — Taylor & Francis
- Seminars in Speech and Language — Thieme

---

## Quality Gates

10 gates enforced before every output: 6 universal (U1-U6) + 4 domain (G1-G4).

| Gate | Domain Check |
|------|-------------|
| G1 | Voice production assessed with measurable dimensions (CAPE-V 0-100mm VAS + GRBAS 0-3) |
| G2 | Vocal hygiene + exercise protocol evidence-based with dosage and progression |
| G3 | Pathology red-flags trigger medical referral with urgency level |
| G4 | Articulation drills for intelligibility specified with measurable targets |

Full gate definitions and enforcement logic in `skills/_shared-conventions.md`.

---

## Development

```bash
make install-dev    # Install with dev deps + pre-commit hooks
make lint           # Ruff check + format
make typecheck      # Pyright strict mode
make test           # Pytest
make all            # Lint + typecheck + test + validate
```

See `CONTRIBUTING.md` for full development workflow.

---

## Roadmap

- [x] Phase 0: Architecture & Research
- [x] Phase 1: Core sub-skills (5)
- [x] Phase 2: Main harness + quality gates
- [x] Phase 3: Knowledge pipeline (async, rate-limited, atomic writes)
- [x] Phase 4: Testing & validation (42 tests)
- [x] Phase 5: Integration & polish (10+ infrastructure files)
- [x] Phase 6: Open-Source Production Release (v2.0.0)

---

## License

MIT — see [LICENSE](LICENSE).

## Citation

```bibtex
@software{voice-speech-therapy-professionals,
  title = {voice-speech-therapy-professionals: Voice & Speech Therapy &
           Articulation Coach for Voice Professionals},
  year = {2026},
  version = {2.0.0},
  url = {https://github.com/your-org/voice-speech-therapy-professionals}
}
```
