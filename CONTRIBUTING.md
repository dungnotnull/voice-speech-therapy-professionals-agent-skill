# Contributing to voice-speech-therapy-professionals

Thank you for your interest in contributing! This project provides a professional-grade
AI-assisted harness for Vocal Health & Speech-Language Pathology for Voice Professionals.
Contributions that improve clinical accuracy, evidence quality, exercise protocols, or
code reliability are welcome.

## Development Setup

```bash
# Clone and enter the repository
git clone https://github.com/your-org/voice-speech-therapy-professionals.git
cd voice-speech-therapy-professionals

# Create a virtual environment (Python 3.11+)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Copy environment config
cp .env.example .env
```

## Development Workflow

1. **Fork** the repository and create a feature branch from `main`.
2. **Write code** following the conventions below.
3. **Run checks** before committing:
   ```bash
   make lint        # ruff check + format
   make typecheck   # pyright strict
   make test        # pytest with coverage
   ```
4. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat(skills): add CAPE-V protocol to sub-core-analysis
   fix(updater): handle Retry-After header on 429 responses
   docs(readme): update architecture diagram
   test(updater): add integration test for full pipeline
   ```
5. **Push** and open a Pull Request against `main`.

## Code Style

- **Formatter:** ruff format (line length 100, double quotes, 4-space indent)
- **Linter:** ruff (ALL rules, see `pyproject.toml` for ignores)
- **Type checker:** pyright (strict mode)
- **Docstrings:** Google style for public functions; concise inline comments where logic is non-obvious
- **Imports:** `from __future__ import annotations` at top of every `.py` file

## Testing Requirements

- **New features:** must include tests covering success, error, and edge-case paths
- **Bug fixes:** must include a regression test demonstrating the bug and the fix
- **Coverage:** should not decrease below 85% line coverage for `tools/`
- **Run tests:** `pytest tools/ tests/ -v --cov=tools`
- **Async tests:** use `pytest-asyncio` (`asyncio_mode = auto` in `pytest.ini`)

## Skill Files

When modifying skill files under `skills/`:

- Maintain YAML frontmatter (`name` + `description`) at the top
- Follow the standard sections: Role & Persona → Workflow → Tools → Output Format → Quality Gates
- Reference `_shared-conventions.md` for universal gates, evidence hierarchy, and translation tables
- Reference `GLOSSARY-vi.md` for Vietnamese domain terminology
- All clinical claims must cite a Tier 1-4 source or be flagged as `[analyst judgment]`

## Domain Contribution Guidelines

When adding exercises, protocols, or clinical content:

- **Evidence required:** every exercise protocol must reference at least one peer-reviewed source
- **Dosage:** specify reps × sets × frequency; provide progression criteria
- **Contraindications:** list when an exercise should NOT be used
- **Vietnamese terminology:** add new terms to `GLOSSARY-vi.md` in the appropriate section
- **Referral thresholds:** clearly define when to escalate from self-management to SLP/ENT

## Knowledge Base Contributions

To seed the `SECOND-KNOWLEDGE-BRAIN.md` with new references:

- Add entries to Section 2 (Key Research Papers) table with DOI/URL, Tier label, and key finding
- Follow the existing table format
- Prefer Tier 1-2 sources (systematic reviews, meta-analyses, RCTs, guidelines)

## Reporting Issues

Use GitHub Issues. For bugs, include:
- Expected behavior vs. actual behavior
- Python version and OS
- Steps to reproduce
- Relevant log output

For clinical content suggestions, include the evidence source and the specific improvement proposed.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
